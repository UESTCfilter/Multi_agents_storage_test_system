from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.database import engine, get_db
from backend.models import Base, Project, Deliverable, AgentLog, WorkflowState, Template
from backend.agents.coordinator import AgentCoordinator
from backend.template_data import init_default_templates

# 全局任务管理器
class TaskManager:
    def __init__(self):
        self.running_tasks = {}  # project_id -> {task, cancel_event}
    
    def start_task(self, project_id: int, task_func, *args, **kwargs):
        """启动一个可取消的任务"""
        cancel_event = asyncio.Event()
        
        async def wrapped_task():
            try:
                print(f"[Task {project_id}] Starting task: {kwargs.get('stage', 'unknown')}")
                result = await task_func(*args, cancel_event=cancel_event)
                print(f"[Task {project_id}] Task completed")
                return result
            except asyncio.CancelledError:
                print(f"[Task {project_id}] Task cancelled")
                return {"cancelled": True}
            except Exception as e:
                print(f"[Task {project_id}] Task error: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        def on_done(t):
            try:
                t.result()
            except Exception as e:
                print(f"[Task {project_id}] Task failed in callback: {e}")
                import traceback
                traceback.print_exc()
            finally:
                if project_id in self.running_tasks:
                    del self.running_tasks[project_id]
                    print(f"[Task {project_id}] Cleaned up from running_tasks")
        
        task = asyncio.create_task(wrapped_task())
        task.add_done_callback(on_done)
        self.running_tasks[project_id] = {
            "task": task,
            "cancel_event": cancel_event,
            "stage": kwargs.get("stage", "unknown")
        }
        return task
    
    async def stop_task(self, project_id: int) -> bool:
        """停止任务"""
        if project_id not in self.running_tasks:
            return False
        
        task_info = self.running_tasks[project_id]
        task = task_info["task"]
        cancel_event = task_info["cancel_event"]
        
        # 设置取消标志
        cancel_event.set()
        
        # 取消任务
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        del self.running_tasks[project_id]
        return True
    
    def get_task_info(self, project_id: int):
        return self.running_tasks.get(project_id)

task_manager = TaskManager()

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 启动时清理残留的 running 状态（防止后端重启后状态不一致）
try:
    from backend.database import SessionLocal
    _cleanup_db = SessionLocal()
    _stale_workflows = _cleanup_db.query(WorkflowState).filter(WorkflowState.status == "running").all()
    for _wf in _stale_workflows:
        _wf.status = "failed"
        _wf.message = "后端重启，任务中断"
        _wf.progress = 0
    if _stale_workflows:
        print(f"[Startup] Cleaned up {len(_stale_workflows)} stale running workflows")
        _cleanup_db.commit()
    _cleanup_db.close()
except Exception as _e:
    print(f"[Startup] Cleanup warning: {_e}")

# SQLite 兼容性：为已有表添加缺失列
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('lecroy_scripts')]
    with engine.connect() as conn:
        if 'generation_mode' not in columns:
            conn.execute(text("ALTER TABLE lecroy_scripts ADD COLUMN generation_mode VARCHAR(20) DEFAULT 'template'"))
            conn.commit()
            print("[Startup] Added column generation_mode to lecroy_scripts")
        if 'feedback_history' not in columns:
            conn.execute(text("ALTER TABLE lecroy_scripts ADD COLUMN feedback_history TEXT DEFAULT '[]'"))
            conn.commit()
            print("[Startup] Added column feedback_history to lecroy_scripts")
        if 'optimized_from' not in columns:
            conn.execute(text("ALTER TABLE lecroy_scripts ADD COLUMN optimized_from INTEGER"))
            conn.commit()
            print("[Startup] Added column optimized_from to lecroy_scripts")
except Exception as _e:
    print(f"[Startup] Schema migration warning: {_e}")

app = FastAPI(title="AI Storage Test System", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Pydantic Models ==========
class ProjectCreate(BaseModel):
    name: str
    device_type: str = "SSD"
    requirements: Optional[str] = None
    test_objective: Optional[str] = None
    target_market: Optional[str] = None
    current_stage: Optional[str] = None

class GenerateRequest(BaseModel):
    template: Optional[str] = None
    use_template: bool = True

class ProjectResponse(BaseModel):
    id: int
    name: str
    device_type: str
    requirements: Optional[str]
    test_objective: Optional[str]
    target_market: Optional[str]
    current_stage: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    total: int
    items: List[ProjectResponse]

class DeliverableResponse(BaseModel):
    id: int
    project_id: int
    type: str
    content: Optional[str]
    status: str
    version: int
    created_at: datetime
    class Config:
        from_attributes = True

class WorkflowStatus(BaseModel):
    status: str
    current_stage: Optional[str]
    progress: int
    message: Optional[str]
    task_id: Optional[str] = None
    can_stop: bool = False

# ========== Projects API ==========
@app.get("/api/projects", response_model=ProjectListResponse)
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    total = db.query(Project).count()
    items = db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}

@app.post("/api/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(**project.dict(), status="created")
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_update: ProjectCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project_update.dict().items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}

# ========== PRD Upload API ==========
@app.post("/api/projects/{project_id}/upload-prd")
async def upload_prd(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传 PRD 需求文档（支持 txt, md, docx）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 检查文件类型
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    allowed = {".txt", ".md", ".docx", ".doc"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，仅支持 {', '.join(allowed)}")

    content = ""
    try:
        if ext in (".txt", ".md"):
            raw = await file.read()
            # Try utf-8 first, fallback to gbk
            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                content = raw.decode("gbk", errors="ignore")
        elif ext in (".docx", ".doc"):
            try:
                from docx import Document
            except ImportError:
                raise HTTPException(status_code=500, detail="python-docx 未安装，无法解析 docx 文件")
            # Save to temp file for docx parser
            import tempfile
            suffix = ext if ext.startswith(".") else ".docx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name
            try:
                doc = Document(tmp_path)
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                content = "\n".join(paragraphs)
            finally:
                os.unlink(tmp_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")

    # Save to project
    project.requirements = content
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)

    return {
        "message": "PRD 上传成功",
        "project_id": project_id,
        "filename": filename,
        "size": len(content),
        "preview": content[:300] + ("..." if len(content) > 300 else "")
    }

# ========== Background Task Runners ==========
async def run_strategy_generation(project_id: int, template: Optional[str], use_template: bool, cancel_event):
    """后台执行策略生成（使用独立的 db session）"""
    print(f"[StrategyGen] Started for project {project_id}, template={template}")
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        coordinator = AgentCoordinator(db)
        
        workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
        if not workflow:
            workflow = WorkflowState(project_id=project_id)
            db.add(workflow)
        workflow.status = "running"
        workflow.current_stage = "strategy"
        workflow.progress = 0
        workflow.message = f"使用模板: {template}" if template else "不使用模板"
        db.commit()
        
        def update_progress(progress: int, message: str):
            try:
                wf = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
                if wf:
                    wf.progress = progress
                    wf.message = message
                    db.commit()
            except Exception as e:
                print(f"[ProgressUpdate] Error: {e}")
        
        context = {
            "requirements": project.requirements or "",
            "test_objective": project.test_objective or "",
            "device_type": project.device_type or "SSD",
            "template": template,
            "use_template": use_template,
            "_progress_callback": update_progress,
            "_cancel_event": cancel_event
        }
        
        result = await coordinator.generate_strategy(context)
        
        if cancel_event.is_set():
            workflow.status = "cancelled"
            workflow.message = "任务已终止"
            db.commit()
            return
        
        if result.get("success"):
            deliverable = db.query(Deliverable).filter(
                Deliverable.project_id == project_id,
                Deliverable.type == "strategy"
            ).first()
            if not deliverable:
                deliverable = Deliverable(project_id=project_id, type="strategy", status="completed")
                db.add(deliverable)
            
            content_parts = []
            content_parts.append(f"# 测试策略\n\n")
            content_parts.append(f"## 需求分析\n")
            content_parts.append(f"- 识别设备类型: {result.get('device_type', 'Unknown')}\n")
            content_parts.append(f"- 自动检测: {'是' if result.get('auto_detected') else '否'}\n\n")
            
            req_analysis = result.get('requirement_analysis', {})
            if req_analysis.get('analysis_summary'):
                content_parts.append(f"### 分析摘要\n{req_analysis['analysis_summary']}\n\n")
            
            content_parts.append(f"## 调度模式\n{result.get('scheduling_mode', 'pipeline')}\n\n")
            content_parts.append(f"## 选中专家\n")
            for agent in result.get('selected_agents', []):
                content_parts.append(f"- {agent}\n")
            content_parts.append(f"\n")
            
            results = result.get('results', [])
            success_count = 0
            fail_count = 0
            failed_agents = []
            if isinstance(results, list):
                for r in results:
                    if r.get('success') and r.get('output'):
                        content_parts.append(f"---\n\n## {r.get('agent', '专家')} 贡献\n\n{r['output']}\n\n")
                        success_count += 1
                    else:
                        fail_count += 1
                        failed_agents.append(r.get('agent', '未知专家'))
            
            # 添加执行统计
            content_parts.append(f"\n---\n\n## 执行统计\n\n")
            content_parts.append(f"- 成功: {success_count} 位专家\n")
            if fail_count > 0:
                content_parts.append(f"- 失败: {fail_count} 位专家 ({', '.join(failed_agents)})\n")
            
            deliverable.content = "".join(content_parts)
            deliverable.status = "completed"
            db.commit()
        
        workflow.status = "completed"
        workflow.progress = 100
        workflow.message = "策略生成完成"
        db.commit()
        
        # 更新项目状态
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "completed"
            db.commit()
    except Exception as e:
        workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
        if workflow:
            workflow.status = "failed"
            workflow.message = str(e)
            db.commit()
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def run_design_generation(project_id: int, template: Optional[str], use_template: bool, cancel_event):
    """后台执行设计生成（使用独立的 db session）"""
    print(f"[DesignGen] Started for project {project_id}, template={template}")
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        
        strategy = db.query(Deliverable).filter(
            Deliverable.project_id == project_id,
            Deliverable.type == "strategy",
            Deliverable.status == "completed"
        ).first()
        
        coordinator = AgentCoordinator(db)
        
        workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
        if not workflow:
            workflow = WorkflowState(project_id=project_id)
            db.add(workflow)
        workflow.status = "running"
        workflow.current_stage = "design"
        workflow.progress = 0
        workflow.message = f"使用模板: {template}" if template else "不使用模板"
        db.commit()
        
        def update_progress(progress: int, message: str):
            try:
                wf = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
                if wf:
                    wf.progress = progress
                    wf.message = message
                    db.commit()
            except Exception as e:
                print(f"[ProgressUpdate] Error: {e}")
        
        context = {
            "requirements": project.requirements or "",
            "test_objective": project.test_objective or "",
            "device_type": project.device_type or "SSD",
            "strategy": strategy.content if strategy else "",
            "template": template,
            "use_template": use_template,
            "_progress_callback": update_progress,
            "_cancel_event": cancel_event
        }
        
        result = await coordinator.generate_design(context)
        
        if cancel_event.is_set():
            workflow.status = "cancelled"
            workflow.message = "任务已终止"
            db.commit()
            return
        
        if result.get("success"):
            deliverable = db.query(Deliverable).filter(
                Deliverable.project_id == project_id,
                Deliverable.type == "design"
            ).first()
            if not deliverable:
                deliverable = Deliverable(project_id=project_id, type="design", status="completed")
                db.add(deliverable)
            
            content_parts = []
            content_parts.append(f"# 测试设计\n\n")
            content_parts.append(f"## 基于策略\n{strategy.content[:500] if strategy else 'N/A'}...\n\n")
            
            results = result.get('results', [])
            success_count = 0
            fail_count = 0
            failed_agents = []
            if isinstance(results, list):
                for r in results:
                    if r.get('success') and r.get('output'):
                        content_parts.append(f"---\n\n## {r.get('agent', '专家')} 贡献\n\n{r['output']}\n\n")
                        success_count += 1
                    else:
                        fail_count += 1
                        failed_agents.append(r.get('agent', '未知专家'))
            
            content_parts.append(f"\n---\n\n## 执行统计\n\n")
            content_parts.append(f"- 成功: {success_count} 位专家\n")
            if fail_count > 0:
                content_parts.append(f"- 失败: {fail_count} 位专家 ({', '.join(failed_agents)})\n")
            
            deliverable.content = "".join(content_parts)
            deliverable.status = "completed"
            db.commit()
        
        workflow.status = "completed"
        workflow.progress = 100
        workflow.message = "设计生成完成"
        db.commit()
        
        # 更新项目状态
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "completed"
            db.commit()
    except Exception as e:
        workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
        if workflow:
            workflow.status = "failed"
            workflow.message = str(e)
            db.commit()
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def run_case_generation(project_id: int, template: Optional[str], use_template: bool, cancel_event):
    """后台执行用例生成（使用独立的 db session）"""
    print(f"[CaseGen] Started for project {project_id}, template={template}")
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return
        
        design = db.query(Deliverable).filter(
            Deliverable.project_id == project_id,
            Deliverable.type == "design",
            Deliverable.status == "completed"
        ).first()
        
        coordinator = AgentCoordinator(db)
        
        workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
        if not workflow:
            workflow = WorkflowState(project_id=project_id)
            db.add(workflow)
        workflow.status = "running"
        workflow.current_stage = "cases"
        workflow.progress = 0
        workflow.message = f"使用模板: {template}" if template else "不使用模板"
        db.commit()
        
        def update_progress(progress: int, message: str):
            try:
                wf = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
                if wf:
                    wf.progress = progress
                    wf.message = message
                    db.commit()
            except Exception as e:
                print(f"[ProgressUpdate] Error: {e}")
        
        context = {
            "requirements": project.requirements or "",
            "test_objective": project.test_objective or "",
            "device_type": project.device_type or "SSD",
            "design": design.content if design else "",
            "template": template,
            "use_template": use_template,
            "_progress_callback": update_progress,
            "_cancel_event": cancel_event
        }
        
        result = await coordinator.generate_cases(context)
        
        if cancel_event.is_set():
            workflow.status = "cancelled"
            workflow.message = "任务已终止"
            db.commit()
            return
        
        if result.get("success"):
            deliverable = db.query(Deliverable).filter(
                Deliverable.project_id == project_id,
                Deliverable.type == "case"
            ).first()
            if not deliverable:
                deliverable = Deliverable(project_id=project_id, type="case", status="completed")
                db.add(deliverable)
            
            content_parts = []
            content_parts.append(f"# 测试用例\n\n")
            content_parts.append(f"## 基于设计\n{design.content[:500] if design else 'N/A'}...\n\n")
            
            results = result.get('results', [])
            success_count = 0
            fail_count = 0
            failed_agents = []
            if isinstance(results, list):
                for r in results:
                    if r.get('success') and r.get('output'):
                        content_parts.append(f"---\n\n## {r.get('agent', '专家')} 贡献\n\n{r['output']}\n\n")
                        success_count += 1
                    else:
                        fail_count += 1
                        failed_agents.append(r.get('agent', '未知专家'))
            
            content_parts.append(f"\n---\n\n## 执行统计\n\n")
            content_parts.append(f"- 成功: {success_count} 位专家\n")
            if fail_count > 0:
                content_parts.append(f"- 失败: {fail_count} 位专家 ({', '.join(failed_agents)})\n")
            
            deliverable.content = "".join(content_parts)
            deliverable.status = "completed"
            db.commit()
        
        workflow.status = "completed"
        workflow.progress = 100
        workflow.message = "用例生成完成"
        db.commit()
        
        # 更新项目状态
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "completed"
            db.commit()
    except Exception as e:
        workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
        if workflow:
            workflow.status = "failed"
            workflow.message = str(e)
            db.commit()
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ========== Workflow API ==========
@app.post("/api/projects/{project_id}/generate-strategy")
async def generate_strategy(
    project_id: int,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 检查是否有运行中的任务
    if project_id in task_manager.running_tasks:
        raise HTTPException(status_code=400, detail="有任务正在运行中")
    
    task = task_manager.start_task(
        project_id,
        run_strategy_generation,
        project_id,
        request.template if request.use_template else None,
        request.use_template,
        stage="strategy"
    )
    
    project.status = "strategy_generating"
    db.commit()
    
    return {
        "message": "Strategy generation started",
        "project_id": project_id,
        "template": request.template if request.use_template else None
    }

@app.post("/api/projects/{project_id}/generate-design")
async def generate_design(
    project_id: int,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 验证依赖：必须先有策略
    strategy = db.query(Deliverable).filter(
        Deliverable.project_id == project_id,
        Deliverable.type == "strategy",
        Deliverable.status == "completed"
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=400, detail="请先生成测试策略")
    
    # 检查是否有运行中的任务
    if project_id in task_manager.running_tasks:
        raise HTTPException(status_code=400, detail="有任务正在运行中")
    
    task = task_manager.start_task(
        project_id,
        run_design_generation,
        project_id,
        request.template if request.use_template else None,
        request.use_template,
        stage="design"
    )
    
    project.status = "design_generating"
    db.commit()
    
    return {
        "message": "Design generation started",
        "project_id": project_id,
        "template": request.template if request.use_template else None
    }

@app.post("/api/projects/{project_id}/generate-cases")
async def generate_cases(
    project_id: int,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 验证依赖：必须先有设计
    design = db.query(Deliverable).filter(
        Deliverable.project_id == project_id,
        Deliverable.type == "design",
        Deliverable.status == "completed"
    ).first()
    
    if not design:
        raise HTTPException(status_code=400, detail="请先生成测试设计")
    
    # 检查是否有运行中的任务
    if project_id in task_manager.running_tasks:
        raise HTTPException(status_code=400, detail="有任务正在运行中")
    
    task = task_manager.start_task(
        project_id,
        run_case_generation,
        project_id,
        request.template if request.use_template else None,
        request.use_template,
        stage="cases"
    )
    
    project.status = "cases_generating"
    db.commit()
    
    return {
        "message": "Test cases generation started",
        "project_id": project_id,
        "template": request.template if request.use_template else None
    }

@app.get("/api/workflow/status/{project_id}", response_model=WorkflowStatus)
def get_workflow_status(project_id: int, db: Session = Depends(get_db)):
    workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
    task_info = task_manager.get_task_info(project_id)
    
    if not workflow:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return WorkflowStatus(
            status="idle",
            current_stage=None,
            progress=0,
            message="",
            task_id=None,
            can_stop=False
        )
    
    return WorkflowStatus(
        status=workflow.status,
        current_stage=workflow.current_stage,
        progress=workflow.progress,
        message=workflow.message,
        task_id=str(project_id) if task_info else None,
        can_stop=workflow.status == "running" and task_info is not None
    )

@app.post("/api/workflow/stop/{project_id}")
async def stop_workflow(project_id: int, db: Session = Depends(get_db)):
    """终止运行中的任务"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 停止任务
    success = await task_manager.stop_task(project_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="没有运行中的任务")
    
    # 更新工作状态
    workflow = db.query(WorkflowState).filter(WorkflowState.project_id == project_id).first()
    if workflow:
        workflow.status = "cancelled"
        workflow.message = "用户手动终止"
        db.commit()
    
    # 更新项目状态
    project.status = "cancelled"
    db.commit()
    
    return {"message": "任务已终止", "project_id": project_id}

# ========== Deliverables API ==========
@app.get("/api/projects/{project_id}/deliverables", response_model=List[DeliverableResponse])
def list_deliverables(project_id: int, db: Session = Depends(get_db)):
    return db.query(Deliverable).filter(Deliverable.project_id == project_id).all()

@app.get("/api/deliverables/{deliverable_id}", response_model=DeliverableResponse)
def get_deliverable(deliverable_id: int, db: Session = Depends(get_db)):
    deliverable = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    return deliverable

# ========== Agents API ==========
@app.get("/api/agents")
def list_agents():
    return {
        "agents": [
            {"name": "nand_expert", "display_name": "NAND Stack Expert", "category": "存储核心"},
            {"name": "data_integrity_expert", "display_name": "Data Integrity Expert", "category": "存储核心"},
            {"name": "firmware_expert", "display_name": "Firmware Testing Expert", "category": "存储核心"},
            {"name": "protocol_expert", "display_name": "Protocol Expert", "category": "接口协议"},
            {"name": "cxl_expert", "display_name": "CXL Expert", "category": "接口协议"},
            {"name": "performance_expert", "display_name": "Performance Expert", "category": "质量属性"},
            {"name": "reliability_expert", "display_name": "Reliability Expert", "category": "质量属性"},
            {"name": "stability_expert", "display_name": "Stability Expert", "category": "质量属性"},
            {"name": "security_expert", "display_name": "Security Expert", "category": "质量属性"},
            {"name": "dfx_expert", "display_name": "DFX Testing Expert", "category": "DFX"},
            {"name": "physical_layer_expert", "display_name": "Physical Layer Expert", "category": "其他"},
            {"name": "thermal_expert", "display_name": "Thermal Expert", "category": "其他"},
            {"name": "power_expert", "display_name": "Power Expert", "category": "其他"},
            {"name": "compatibility_expert", "display_name": "Compatibility Expert", "category": "其他"},
        ]
    }

# ========== Quality & Routing Debug API ==========
from backend.agents.quality_gate import QualityGate
from backend.agents.smart_router import SmartRouter
from pydantic import BaseModel

class QualityCheckRequest(BaseModel):
    content: str
    task_type: str = "strategy"
    requirements: str = ""

@app.post("/api/quality/check")
def quality_check(request: QualityCheckRequest):
    """质量验证 API - 测试内容质量"""
    gate = QualityGate(min_score=70.0)
    report = gate.validate(
        content=request.content,
        task_type=request.task_type,
        requirements=request.requirements
    )
    return {
        "passed": report.passed,
        "score": report.score,
        "checks": report.checks,
        "feedback": report.feedback,
        "suggestions": report.suggestions
    }

class AgentSelectionRequest(BaseModel):
    device_type: str = "SSD"
    requirements: str = ""
    test_objective: str = ""

@app.post("/api/agents/select")
def agent_selection(request: AgentSelectionRequest):
    """智能路由 API - 查看系统选择了哪些 Agent"""
    from backend.agents.coordinator import AgentCoordinator
    coordinator = AgentCoordinator()
    
    context = {
        "device_type": request.device_type,
        "requirements": request.requirements,
        "test_objective": request.test_objective
    }
    
    report = coordinator.smart_router.get_agent_selection_report(context)
    return report


# ========== Template Management API ==========
class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    type: str
    content: str
    is_default: bool
    is_editable: bool
    parent_id: Optional[int]
    created_by: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # strategy, design, case
    content: str
    parent_id: Optional[int] = None

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None

@app.get("/api/templates", response_model=List[TemplateResponse])
def list_templates(
    type: Optional[str] = None,
    include_default: bool = True,
    db: Session = Depends(get_db)
):
    """获取模板列表"""
    query = db.query(Template)
    
    if type:
        query = query.filter(Template.type == type)
    
    if not include_default:
        query = query.filter(Template.is_default == False)
    
    templates = query.order_by(Template.type, Template.is_default.desc(), Template.name).all()
    return templates

@app.get("/api/templates/{template_id}", response_model=TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """获取单个模板详情"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@app.post("/api/templates", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """创建新模板（用户自定义）"""
    db_template = Template(
        name=template.name,
        description=template.description,
        type=template.type,
        content=template.content,
        is_default=False,
        is_editable=True,
        parent_id=template.parent_id,
        created_by="user"
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@app.put("/api/templates/{template_id}", response_model=TemplateResponse)
def update_template(template_id: int, update: TemplateUpdate, db: Session = Depends(get_db)):
    """更新模板内容"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 默认模板不能直接修改，需要创建副本
    if template.is_default and not template.is_editable:
        raise HTTPException(status_code=400, detail="默认模板不能直接修改，请先创建副本")
    
    if update.name is not None:
        template.name = update.name
    if update.description is not None:
        template.description = update.description
    if update.content is not None:
        template.content = update.content
    
    db.commit()
    db.refresh(template)
    return template

@app.post("/api/templates/{template_id}/clone", response_model=TemplateResponse)
def clone_template(template_id: int, db: Session = Depends(get_db)):
    """克隆模板（用于基于默认模板创建自定义版本）"""
    original = db.query(Template).filter(Template.id == template_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Template not found")
    
    new_template = Template(
        name=f"{original.name} (副本)",
        description=original.description,
        type=original.type,
        content=original.content,
        is_default=False,
        is_editable=True,
        parent_id=original.id,
        created_by="user"
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """删除模板（只能删除用户创建的模板）"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.is_default:
        raise HTTPException(status_code=400, detail="默认模板不能删除")
    
    db.delete(template)
    db.commit()
    return {"message": "Template deleted", "template_id": template_id}


# ========== Health Check ==========
@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0", "features": ["quality_gate", "smart_router", "template_management"]}

# ========== LeCroy Script Agent API ==========

class LeCroyScriptGenerateRequest(BaseModel):
    description: str  # 自然语言描述的测试用例步骤
    test_name: Optional[str] = None  # 测试名称（可选）
    mode: Optional[str] = "hybrid"  # template / llm / hybrid
    protocol: Optional[str] = None  # 强制指定协议（可选）
    scenario: Optional[str] = None  # 强制指定场景（可选）

class LeCroyScriptOptimizeRequest(BaseModel):
    script_id: int
    feedback: str  # 用户的优化反馈/要求

class LeCroyScriptResponse(BaseModel):
    success: bool
    id: Optional[int] = None
    test_name: Optional[str] = None
    protocol: Optional[str] = None
    scenario: Optional[str] = None
    peg_content: Optional[str] = None
    pevs_content: Optional[str] = None
    generation_mode: Optional[str] = None
    reasoning: Optional[str] = None
    optimized_from: Optional[int] = None
    error: Optional[str] = None

@app.post("/api/projects/{project_id}/generate-lecroy-script", response_model=LeCroyScriptResponse)
async def generate_lecroy_script(
    project_id: int,
    request: LeCroyScriptGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    从自然语言描述生成 LeCroy 脚本 (PEG + PEVS)
    
    请求体:
    {
        "description": "测试步骤的自然语言描述",
        "test_name": "测试名称（可选）",
        "mode": "hybrid"  // template | llm | hybrid
    }
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not request.description or not request.description.strip():
        raise HTTPException(status_code=400, detail="请提供测试步骤描述")
    
    mode = request.mode or "hybrid"
    if mode not in ("template", "llm", "hybrid"):
        raise HTTPException(status_code=400, detail="mode 必须是 template、llm 或 hybrid")
    
    from backend.services.lecrory_integration import LeCroyIntegrationService
    
    service = LeCroyIntegrationService()
    result = await service.generate_scripts(
        project_id=project_id,
        description=request.description,
        test_name=request.test_name,
        mode=mode,
        protocol=request.protocol,
        scenario=request.scenario
    )
    
    if result and result.get("success"):
        return LeCroyScriptResponse(
            success=True,
            id=result["id"],
            test_name=result["test_name"],
            protocol=result["protocol"],
            scenario=result["scenario"],
            peg_content=result["peg_content"],
            pevs_content=result["pevs_content"],
            generation_mode=result.get("generation_mode"),
            reasoning=result.get("reasoning")
        )
    else:
        error_msg = result.get("error", "脚本生成失败") if result else "未知错误"
        return LeCroyScriptResponse(success=False, error=error_msg)

@app.post("/api/projects/{project_id}/optimize-lecroy-script", response_model=LeCroyScriptResponse)
async def optimize_lecroy_script(
    project_id: int,
    request: LeCroyScriptOptimizeRequest,
    db: Session = Depends(get_db)
):
    """
    基于用户反馈优化已有 LeCroy 脚本
    
    请求体:
    {
        "script_id": 1,
        "feedback": "请在PEVS中添加链路宽度变化的验证步骤"
    }
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not request.feedback or not request.feedback.strip():
        raise HTTPException(status_code=400, detail="请提供优化反馈")
    
    from backend.services.lecrory_integration import LeCroyIntegrationService
    
    service = LeCroyIntegrationService()
    result = await service.optimize_script(
        project_id=project_id,
        script_id=request.script_id,
        feedback=request.feedback
    )
    
    if result and result.get("success"):
        return LeCroyScriptResponse(
            success=True,
            id=result["id"],
            test_name=result["test_name"],
            protocol=result["protocol"],
            scenario=result["scenario"],
            peg_content=result["peg_content"],
            pevs_content=result["pevs_content"],
            generation_mode="llm_optimized",
            reasoning=result.get("reasoning"),
            optimized_from=result.get("optimized_from")
        )
    else:
        error_msg = result.get("error", "优化失败") if result else "未知错误"
        return LeCroyScriptResponse(success=False, error=error_msg)

@app.get("/api/projects/{project_id}/lecroy-scripts")
def list_lecroy_scripts(project_id: int, db: Session = Depends(get_db)):
    """获取项目下所有生成的 LeCroy 脚本（从数据库）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    from backend.services.lecrory_integration import LeCroyIntegrationService
    service = LeCroyIntegrationService()
    scripts = service.list_scripts(project_id, db)
    
    return {"scripts": scripts, "total": len(scripts)}

@app.get("/api/projects/{project_id}/lecroy-scripts/{script_id}")
def get_lecroy_script(project_id: int, script_id: int, db: Session = Depends(get_db)):
    """获取指定 LeCroy 脚本的完整内容"""
    from backend.services.lecrory_integration import LeCroyIntegrationService
    
    service = LeCroyIntegrationService()
    script = service.get_script(project_id, script_id, db)
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script

@app.delete("/api/projects/{project_id}/lecroy-scripts/{script_id}")
def delete_lecroy_script(project_id: int, script_id: int, db: Session = Depends(get_db)):
    """删除指定 LeCroy 脚本"""
    from backend.services.lecrory_integration import LeCroyIntegrationService
    
    service = LeCroyIntegrationService()
    success = service.delete_script(project_id, script_id, db)
    
    if not success:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return {"message": "脚本已删除", "script_id": script_id}


# ========== Main Entry ==========

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8001))
    
    # 初始化默认模板
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        init_default_templates(db)
    finally:
        db.close()
    
    uvicorn.run(app, host="0.0.0.0", port=port)
"""智能体协调器 V2 - 30专家集群 + 智能调度

集成：
- 30个专业测试专家
- 智能路由（需求驱动的Agent选择）
- 质量验证（4维检查+自动重写）
- 智能调度（分层协作、流水线、主从模式）
"""
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

# 导入所有17个原有专家
from backend.agents.specialized.nand_expert import NANDStackExpert
from backend.agents.specialized.data_integrity_expert import DataIntegrityExpert
from backend.agents.specialized.firmware_expert import FirmwareTestingExpert
from backend.agents.specialized.protocol_expert import ProtocolExpert
from backend.agents.specialized.cxl_expert import CXLExpert
from backend.agents.specialized.performance_expert import PerformanceExpert
from backend.agents.specialized.reliability_expert import ReliabilityExpert
from backend.agents.specialized.stability_expert import StabilityExpert
from backend.agents.specialized.security_expert import SecurityExpert
from backend.agents.specialized.dfx_expert import DFXTestingExpert
from backend.agents.specialized.physical_layer_expert import PhysicalLayerExpert
from backend.agents.specialized.thermal_expert import ThermalExpert
from backend.agents.specialized.power_expert import PowerExpert
from backend.agents.specialized.compatibility_expert import CompatibilityExpert
from backend.agents.specialized.stress_expert import StressTestingExpert
from backend.agents.specialized.regression_expert import RegressionTestingExpert
from backend.agents.specialized.automation_expert import AutomationExpert

# 导入13个新增专家
from backend.agents.specialized.cxl_protocol_expert import CXLProtocolExpert
from backend.agents.specialized.cxl_switch_expert import CXLSwitchExpert
from backend.agents.specialized.type2_expert import Type2DeviceExpert
from backend.agents.specialized.type3_expert import Type3DeviceExpert
from backend.agents.specialized.cxl_coherency_expert import CXLCoherencyExpert
from backend.agents.specialized.cxl_ras_expert import CXL_RAS_Expert
from backend.agents.specialized.pcm_media_expert import PCMMediaExpert
from backend.agents.specialized.pcm_endurance_expert import PCMEnduranceExpert
from backend.agents.specialized.pcm_temperature_expert import PCMTemperatureExpert
from backend.agents.specialized.ftl_expert import FTLExpert
from backend.agents.specialized.nvme_expert import NVMeExpert
from backend.agents.specialized.qos_expert import QoSExpert
from backend.agents.specialized.workload_expert import WorkloadExpert

# 导入需求分析专家
from backend.agents.specialized.requirement_analysis_expert import RequirementAnalysisExpert

# 导入质量验证和智能路由
from backend.agents.quality_gate import QualityGate, QualityReport
from backend.agents.smart_router import SmartRouter, AgentMatch


class SchedulingMode(Enum):
    """调度模式"""
    PARALLEL = "parallel"           # 并行执行
    PIPELINE = "pipeline"           # 流水线
    MASTER_SLAVE = "master_slave"   # 主从协作


class AgentCoordinator:
    """中央协调器 - 30专家集群 + 智能调度"""
    
    def __init__(self, db_session=None):
        self.agents: Dict[str, Any] = {}
        self.db_session = db_session
        self.quality_gate = QualityGate(min_score=50.0)
        self.smart_router = None  # 延迟初始化
        self._init_agents()
        self.smart_router = SmartRouter(self.agents)
    
    def _init_agents(self):
        """初始化所有30个智能体"""
        agent_classes = [
            # 原有17个
            NANDStackExpert,
            DataIntegrityExpert,
            FirmwareTestingExpert,
            ProtocolExpert,
            CXLExpert,
            PerformanceExpert,
            ReliabilityExpert,
            StabilityExpert,
            SecurityExpert,
            DFXTestingExpert,
            PhysicalLayerExpert,
            ThermalExpert,
            PowerExpert,
            CompatibilityExpert,
            StressTestingExpert,
            RegressionTestingExpert,
            AutomationExpert,
            # 新增13个
            CXLProtocolExpert,
            CXLSwitchExpert,
            Type2DeviceExpert,
            Type3DeviceExpert,
            CXLCoherencyExpert,
            CXL_RAS_Expert,
            PCMMediaExpert,
            PCMEnduranceExpert,
            PCMTemperatureExpert,
            FTLExpert,
            NVMeExpert,
            QoSExpert,
            WorkloadExpert,
            # 需求分析专家（系统入口）
            RequirementAnalysisExpert,
        ]
        
        for agent_class in agent_classes:
            try:
                agent = agent_class()
                self.agents[agent.name] = agent
            except Exception as e:
                print(f"Warning: Failed to init {agent_class.__name__}: {e}")
    
    def get_agent(self, name: str) -> Optional[Any]:
        """获取指定智能体"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        return [agent.get_info() for agent in self.agents.values()]
    
    # ========== 质量验证 ==========
    
    async def execute_agent_with_quality(self, agent_name: str, 
                                          context: Dict[str, Any],
                                          max_retries: int = 1) -> Dict[str, Any]:
        """执行智能体并带质量验证（含限流重试）"""
        import asyncio
        cancel_event = context.get("_cancel_event")
        if cancel_event and cancel_event.is_set():
            return {
                "success": False,
                "error": "Task cancelled",
                "output": None,
                "cancelled": True
            }
        
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                "success": False,
                "error": f"Agent not found: {agent_name}",
                "output": None
            }
        
        task_type = context.get("task_type", "strategy")
        requirements = context.get("requirements", "")
        
        # 带指数退避重试（处理 429 限流）
        api_retry = 0
        max_api_retries = 3
        result = None
        while api_retry <= max_api_retries:
            try:
                result = await asyncio.wait_for(self._execute_single(agent, context), timeout=360.0)
            except asyncio.TimeoutError:
                result = {
                    "success": False,
                    "agent": agent_name,
                    "error": "Agent execution timeout (300s)",
                    "output": None
                }
            if result["success"]:
                break
            error = result.get("error", "")
            # 429 限流或连接错误时重试
            if "429" in error or "rate limit" in error.lower() or "connect" in error.lower() or "timeout" in error.lower():
                api_retry += 1
                if api_retry <= max_api_retries:
                    wait = 2 ** api_retry  # 2, 4, 8 秒
                    print(f"[Agent {agent_name}] Rate limit/Error, retrying in {wait}s... ({api_retry}/{max_api_retries})")
                    await asyncio.sleep(wait)
                continue
            break
        
        if not result["success"]:
            return result
        
        quality_report = self.quality_gate.validate(
            content=result["output"],
            task_type=task_type,
            requirements=requirements
        )
        
        retry_count = 0
        while not quality_report.passed and retry_count < max_retries:
            if cancel_event and cancel_event.is_set():
                return {
                    **result,
                    "cancelled": True,
                    "quality_report": {
                        "score": quality_report.score,
                        "passed": quality_report.passed,
                        "checks": quality_report.checks,
                        "retries": retry_count
                    }
                }
            
            retry_count += 1
            enhanced_prompt = self.quality_gate.generate_enhanced_prompt(
                original_output=result["output"],
                report=quality_report,
                task_type=task_type
            )
            
            retry_context = {
                **context,
                "enhanced_prompt": enhanced_prompt,
                "previous_attempt": result["output"]
            }
            
            result = await self._execute_single(agent, retry_context)
            
            if not result["success"]:
                break
            
            quality_report = self.quality_gate.validate(
                content=result["output"],
                task_type=task_type,
                requirements=requirements
            )
        
        return {
            **result,
            "quality_report": {
                "score": quality_report.score,
                "passed": quality_report.passed,
                "checks": quality_report.checks,
                "retries": retry_count
            }
        }
    
    async def _execute_single(self, agent: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个 Agent"""
        try:
            result = await agent.execute(context)
            # Agent 可能返回 dict（含 output/error）或纯字符串
            if isinstance(result, dict):
                if result.get("success"):
                    return {
                        "success": True,
                        "agent": agent.name,
                        "output": result.get("output", ""),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    err = result.get("error", "")
                    if not err:
                        err = f"{agent.name} 执行失败（无详细错误）"
                    return {
                        "success": False,
                        "agent": agent.name,
                        "error": err,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            else:
                # 纯字符串输出
                return {
                    "success": True,
                    "agent": agent.name,
                    "output": str(result),
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            err_msg = str(e) or f"{type(e).__name__}"
            return {
                "success": False,
                "agent": agent.name,
                "error": err_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # ========== 智能调度 ==========
    
    def _select_master_agent(self, device_type: str, agents: List[str]) -> str:
        """选择主 Agent（领域最相关的）"""
        # 根据设备类型选择最合适的Master
        master_candidates = {
            "CXL": ["CXL Protocol Expert", "CXL Expert", "Type3 Device Expert"],
            "PCM": ["PCM Media Expert", "PCM Endurance Expert"],
            "SSD": ["NAND Stack Expert", "FTL Expert", "NVMe Expert"],
        }
        
        candidates = master_candidates.get(device_type, ["Protocol Expert"])
        for candidate in candidates:
            if candidate in agents:
                return candidate
        return agents[0] if agents else None
    
    def _determine_dependencies(self, agent_names: List[str], device_type: str) -> List[List[str]]:
        """确定 Agent 执行依赖关系，返回分层列表"""
        # 定义层级
        layers = {
            "physical": ["NAND Stack Expert", "PCM Media Expert", "Physical Layer Expert"],
            "controller": ["FTL Expert", "Firmware Testing Expert", "NVMe Expert"],
            "protocol": ["CXL Protocol Expert", "CXL Expert", "Type2 Device Expert", "Type3 Device Expert"],
            "system": ["CXL Switch Expert", "CXL Coherency Expert", "Data Integrity Expert"],
            "application": ["QoS Expert", "Workload Expert", "Performance Expert", "Security Expert"],
        }
        
        # 按层级分组
        execution_layers = []
        for layer_name, layer_agents in layers.items():
            layer = [a for a in agent_names if a in layer_agents]
            if layer:
                execution_layers.append(layer)
        
        # 未分层的放最后并行执行
        remaining = [a for a in agent_names if not any(a in layer for layer in execution_layers)]
        if remaining:
            execution_layers.append(remaining)
        
        return execution_layers
    
    async def execute_pipeline(self, agent_matches: List[AgentMatch], 
                               context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """流水线模式执行 - 分层依赖（限制并发防限流）"""
        device_type = context.get("device_type", "SSD")
        agent_names = [m.agent_name for m in agent_matches]
        progress_callback = context.get("_progress_callback")
        cancel_event = context.get("_cancel_event")
        
        # 确定依赖层级
        layers = self._determine_dependencies(agent_names, device_type)
        total_layers = len(layers)
        
        all_results = []
        accumulated_context = context.copy()
        
        # 信号量限制并发数（防止 API 限流）
        semaphore = asyncio.Semaphore(2)
        
        async def run_with_limit(agent_name: str, ctx: Dict):
            async with semaphore:
                return await self.execute_agent_with_quality(agent_name, ctx)
        
        for i, layer in enumerate(layers):
            # 检查是否已取消
            if cancel_event and cancel_event.is_set():
                print(f"[Pipeline] Cancelled at layer {i+1}")
                if progress_callback:
                    progress_callback(0, "任务已终止")
                return all_results
            
            print(f"Pipeline Layer {i+1}/{total_layers}: {layer}")
            
            # 更新进度：每层开始前推进进度
            if progress_callback:
                progress = int(((i) / total_layers) * 80 + 10)  # 10%~90%
                progress_callback(progress, f"执行流水线第 {i+1}/{total_layers} 层: {', '.join(layer)}")
            
            # 并行执行当前层（限制并发数为3）
            tasks = [
                run_with_limit(agent_name, accumulated_context)
                for agent_name in layer
            ]
            try:
                layer_results = await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                print(f"[Pipeline] CancelledError at layer {i+1}")
                if progress_callback:
                    progress_callback(0, "任务已终止")
                raise  # 继续向上传播
            
            all_results.extend(layer_results)
            
            # 将当前层结果加入上下文（供下一层参考）
            layer_outputs = [r["output"] for r in layer_results if r["success"]]
            accumulated_context[f"layer_{i}_outputs"] = layer_outputs
        
        # 流水线完成
        if progress_callback:
            progress_callback(90, "流水线执行完成，正在汇总结果...")
        
        return all_results
    
    async def execute_master_slave(self, agent_matches: List[AgentMatch],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """主从模式执行 - Master制定框架，Slaves填充"""
        device_type = context.get("device_type", "SSD")
        agent_names = [m.agent_name for m in agent_matches]
        
        # 选择 Master
        master_name = self._select_master_agent(device_type, agent_names)
        slave_names = [a for a in agent_names if a != master_name]
        
        print(f"Master: {master_name}, Slaves: {slave_names}")
        
        # Master 制定框架
        master_result = await self.execute_agent_with_quality(master_name, {
            **context,
            "role": "master",
            "task": "generate_framework"
        })
        
        if not master_result["success"]:
            return {"error": "Master agent failed", "results": [master_result]}
        
        framework = master_result["output"]
        
        # Slaves 填充各章节
        slave_results = []
        if slave_names:
            slave_tasks = [
                self.execute_agent_with_quality(slave_name, {
                    **context,
                    "role": "slave",
                    "framework": framework,
                    "section": slave_name  # 每个slave负责自己的专长部分
                })
                for slave_name in slave_names
            ]
            slave_results = await asyncio.gather(*slave_tasks)
        
        # Master 统一润色
        combined = {
            "framework": framework,
            "slave_contributions": [r["output"] for r in slave_results if r["success"]]
        }
        
        polish_result = await self.execute_agent_with_quality(master_name, {
            **context,
            "role": "master",
            "task": "polish",
            "combined_content": combined
        })
        
        return {
            "master": master_result,
            "slaves": slave_results,
            "final": polish_result
        }
    
    # ========== 工作流接口 ==========
    
    async def analyze_requirements(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """第一步：需求分析 - 自动识别设备类型和测试目标"""
        # 检查是否已提供设备类型（如果没有则需要分析）
        requirements = project_context.get("requirements", "")
        test_objective = project_context.get("test_objective", "")
        
        # 如果用户明确指定了设备类型，跳过分析
        if project_context.get("device_type") and project_context["device_type"] != "SSD":
            return {
                "success": True,
                "device_type": project_context["device_type"],
                "analysis": "用户使用指定设备类型",
                "auto_detected": False
            }
        
        # 调用需求分析专家
        analysis_result = await self.execute_agent_with_quality(
            "Requirement Analysis Expert",
            {
                **project_context,
                "task_type": "strategy"
            }
        )
        
        if not analysis_result["success"]:
            return {
                "success": False,
                "error": "需求分析失败",
                "fallback_device_type": "SSD"
            }
        
        # 从分析结果中提取设备类型（简单解析）
        output = analysis_result.get("output", "")
        detected_device = "SSD"  # 默认
        
        if "CXL_Switch" in output or ("CXL" in output and "Switch" in output):
            detected_device = "CXL"
        elif "CXL_Type2" in output or ("Type2" in output and "device cache" in output.lower()):
            detected_device = "CXL"
        elif "CXL" in output and "内存扩展" in output:
            detected_device = "CXL"
        elif "PCM" in output or "相变" in output:
            detected_device = "PCM"
        
        return {
            "success": True,
            "device_type": detected_device,
            "analysis_output": output,
            "analysis_quality": analysis_result.get("quality_report", {}),
            "auto_detected": True
        }
    
    async def generate_strategy(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试策略 - 需求分析 → 智能路由 → 流水线调度"""
        progress_callback = project_context.get("_progress_callback")
        
        if progress_callback:
            progress_callback(5, "正在进行需求分析...")
        
        # ===== 第一步：需求分析（自动识别） =====
        analysis = await self.analyze_requirements(project_context)
        
        if not analysis["success"]:
            # 分析失败，使用默认值继续
            device_type = "SSD"
        else:
            device_type = analysis["device_type"]
            # 更新项目上下文
            project_context["device_type"] = device_type
            project_context["_analysis"] = analysis
        
        if progress_callback:
            progress_callback(10, f"需求分析完成，识别设备类型: {device_type}，正在选择专家...")
        
        # ===== 第二步：智能路由选择 Agent =====
        agent_matches = self.smart_router.select_agents(project_context, max_agents=8)
        
        if not agent_matches:
            return {"success": False, "error": "No suitable agents found", "analysis": analysis}
        
        if progress_callback:
            progress_callback(12, f"已选择 {len(agent_matches)} 位专家，开始协作生成...")
        
        # 2. 根据场景选择调度模式
        scheduling_mode = project_context.get("scheduling_mode", "pipeline")
        
        if scheduling_mode == "master_slave":
            results = await self.execute_master_slave(agent_matches, {
                **project_context,
                "task_type": "strategy"
            })
        else:  # 默认 pipeline
            results = await self.execute_pipeline(agent_matches, {
                **project_context,
                "task_type": "strategy"
            })
        
        # 3. 汇总质量报告
        quality_scores = []
        passed_count = 0
        
        if isinstance(results, list):
            for r in results:
                if r.get("success"):
                    q_report = r.get("quality_report", {})
                    quality_scores.append(q_report.get("score", 0))
                    if q_report.get("passed"):
                        passed_count += 1
            avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        else:
            avg_score = 0
        
        return {
            "success": True,
            "stage": "strategy",
            "device_type": device_type,
            "auto_detected": analysis.get("auto_detected", False),
            "requirement_analysis": {
                "detected_device": device_type,
                "analysis_summary": analysis.get("analysis_output", "")[:500] if analysis.get("auto_detected") else "使用用户指定类型",
                "analysis_quality": analysis.get("analysis_quality", {})
            },
            "scheduling_mode": scheduling_mode,
            "selected_agents": [m.agent_name for m in agent_matches],
            "selection_report": self.smart_router.get_agent_selection_report(project_context),
            "results": results,
            "summary": f"策略生成完成，需求分析→{len(agent_matches)}个专家协作",
            "quality_summary": {
                "average_score": avg_score,
                "passed_agents": passed_count,
                "total_agents": len(agent_matches)
            }
        }
    
    async def generate_design(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试设计"""
        progress_callback = project_context.get("_progress_callback")
        if progress_callback:
            progress_callback(5, "正在准备测试设计...")
        
        design_context = {
            **project_context,
            "test_objective": f"{project_context.get('test_objective', '')} 详细设计"
        }
        
        agent_matches = self.smart_router.select_agents(design_context, max_agents=6)
        
        if progress_callback:
            progress_callback(10, f"已选择 {len(agent_matches)} 位专家，开始生成测试设计...")
        
        results = await self.execute_pipeline(agent_matches, {
            **project_context,
            "task_type": "design"
        })
        
        return {
            "success": True,
            "stage": "design",
            "results": results,
            "summary": f"设计阶段完成，涉及{len(results)}个专家"
        }
    
    async def generate_cases(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试用例"""
        progress_callback = project_context.get("_progress_callback")
        if progress_callback:
            progress_callback(5, "正在准备测试用例生成...")
        
        agent_matches = self.smart_router.select_agents(project_context, max_agents=10)
        
        if progress_callback:
            progress_callback(10, f"已选择 {len(agent_matches)} 位专家，开始生成测试用例...")
        
        results = await self.execute_pipeline(agent_matches, {
            **project_context,
            "task_type": "case"
        })
        
        return {
            "success": True,
            "stage": "case",
            "results": results,
            "summary": f"生成阶段完成，{len(results)}个专家参与"
        }


# 全局协调器实例
coordinator = AgentCoordinator()
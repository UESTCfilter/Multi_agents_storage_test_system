"""
LeCroy Script Agent 集成模块（LLM 强化版）

架构变更：
- LLM 成为核心生成器，模板库退化为参考示例源
- template 模式保留旧规则引擎作为兜底
- llm / hybrid 模式走新的 LeCroyLLMAgent
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, Dict, List

# 添加 lecroy_script_agent 到路径（保留兼容性）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from lecroy_script_agent.agent import LeCroyScriptAgent
except ImportError as e:
    print(f"[LeCroyIntegration] Warning: lecroy_script_agent not found: {e}")
    LeCroyScriptAgent = None

from backend.database import SessionLocal
from backend.models import Project, AgentLog, LeCroyScript


class LeCroyIntegrationService:
    """LeCroy Script Agent 集成服务（LLM 为核心）"""

    def __init__(self):
        # 旧规则引擎仅作为 template 模式兜底使用
        self.agent = LeCroyScriptAgent() if LeCroyScriptAgent else None
        self._llm_agent = None

    def _get_llm_agent(self):
        """延迟初始化 LLM Agent"""
        if self._llm_agent is None:
            from backend.agents.lecroy_llm_agent import LeCroyLLMAgent
            from backend.agents.peg_validator import validate_peg, format_validation_report
            self._llm_agent = LeCroyLLMAgent()
            self._validate_peg = validate_peg
            self._format_validation = format_validation_report
        return self._llm_agent

    async def generate_scripts(
        self,
        project_id: int,
        description: str,
        test_name: str = None,
        mode: str = "hybrid",
        protocol: Optional[str] = None,
        scenario: Optional[str] = None
    ) -> Optional[Dict]:
        """
        从自然语言描述生成 LeCroy 脚本并保存到数据库

        Args:
            project_id: 项目ID
            description: 自然语言描述的测试步骤
            test_name: 测试名称
            mode: 生成模式
                - template: 仅使用旧规则引擎（无 API 消耗，场景有限）
                - llm: 仅使用 LLM 动态生成（智能灵活）
                - hybrid: LLM 生成 + 旧模板作为参考上下文（推荐）

        Returns:
            {
                "success": bool,
                "id": int,
                "test_name": str,
                "protocol": str,
                "scenario": str,
                "peg_content": str,
                "pevs_content": str,
                "generation_mode": str,
                "reasoning": str
            }
        """
        test_name = test_name or f"Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            reference_template = None

            # ── template 模式：旧规则引擎兜底 ──
            if mode == "template":
                if not self.agent:
                    return {
                        "success": False,
                        "error": "LeCroy Script Agent 未初始化，无法使用 template 模式"
                    }
                try:
                    result = self.agent.generate_from_text(description, test_name)
                    final_peg = result.peg_content
                    final_pevs = result.pevs_content
                    final_protocol = result.protocol
                    final_scenario = result.scenario
                    final_reasoning = "基于规则引擎模板生成（兜底模式）"
                    final_mode = "template"
                except Exception as te:
                    return {"success": False, "error": f"规则引擎生成失败: {te}"}

            # ── llm / hybrid 模式：LLM 为核心 ──
            else:
                llm_agent = self._get_llm_agent()

                # hybrid 模式下，先尝试获取旧模板作为参考
                if mode == "hybrid" and self.agent:
                    try:
                        template_result = self.agent.generate_from_text(description, test_name)
                        reference_template = {
                            "peg_template": template_result.peg_content,
                            "pevs_template": template_result.pevs_content,
                            "protocol": template_result.protocol,
                            "scenario": template_result.scenario
                        }
                    except Exception:
                        reference_template = None

                llm_result = await llm_agent.generate(
                    description=description,
                    test_name=test_name,
                    protocol=protocol,
                    scenario=scenario,
                    reference_template=reference_template if mode == "hybrid" else None
                )

                final_peg = llm_result.peg_content
                final_pevs = llm_result.pevs_content
                final_protocol = llm_result.protocol
                final_scenario = llm_result.scenario
                final_reasoning = llm_result.reasoning
                final_mode = "hybrid" if mode == "hybrid" else "llm"

            # ── 保存到数据库 ──
            db = SessionLocal()
            try:
                script_record = LeCroyScript(
                    project_id=project_id,
                    test_name=test_name,
                    protocol=final_protocol,
                    scenario=final_scenario,
                    description=description,
                    peg_content=final_peg,
                    pevs_content=final_pevs,
                    generation_mode=final_mode
                )
                db.add(script_record)
                db.commit()
                db.refresh(script_record)

                # 记录 Agent 日志
                log = AgentLog(
                    project_id=project_id,
                    agent_name="LeCroyScriptAgent",
                    task_type="lecroy_script",
                    status="completed",
                    output=f"Generated script ({final_mode}): {test_name} ({final_protocol} - {final_scenario})"
                )
                db.add(log)
                db.commit()

                # PEG 语法校验
                validation_errors = self._validate_peg(final_peg) if hasattr(self, '_validate_peg') else []
                validation_report = self._format_validation(validation_errors) if hasattr(self, '_format_validation') else ""
                
                return {
                    "success": True,
                    "id": script_record.id,
                    "test_name": test_name,
                    "protocol": final_protocol,
                    "scenario": final_scenario,
                    "peg_content": final_peg,
                    "pevs_content": final_pevs,
                    "generation_mode": final_mode,
                    "reasoning": final_reasoning,
                    "validation_errors": validation_errors,
                    "validation_report": validation_report,
                }
            except Exception as db_err:
                db.rollback()
                raise db_err
            finally:
                db.close()

        except Exception as e:
            # 记录错误日志
            db = SessionLocal()
            try:
                log = AgentLog(
                    project_id=project_id,
                    agent_name="LeCroyScriptAgent",
                    task_type="lecroy_script",
                    status="error",
                    error_message=str(e) or f"{type(e).__name__}"
                )
                db.add(log)
                db.commit()
            finally:
                db.close()

            return {
                "success": False,
                "error": str(e) or f"{type(e).__name__}"
            }

    async def optimize_script(
        self,
        project_id: int,
        script_id: int,
        feedback: str
    ) -> Optional[Dict]:
        """
        基于用户反馈优化已有脚本（纯 LLM，不走规则引擎）
        """
        db = SessionLocal()
        try:
            script = db.query(LeCroyScript).filter(
                LeCroyScript.id == script_id,
                LeCroyScript.project_id == project_id
            ).first()

            if not script:
                return {"success": False, "error": "脚本不存在"}

            # 调用 LLM 优化
            llm_agent = self._get_llm_agent()
            llm_result = await llm_agent.optimize(
                test_name=script.test_name,
                current_peg=script.peg_content,
                current_pevs=script.pevs_content,
                protocol=script.protocol or "pcie_pl",
                scenario=script.scenario or "link_up",
                feedback=feedback,
                description=script.description or ""
            )

            # 更新 feedback_history
            history = script.feedback_history or []
            if isinstance(history, str):
                history = json.loads(history) if history else []
            history.append({
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat(),
                "reasoning": llm_result.reasoning
            })

            # 保存优化后的脚本为新记录（保留历史）
            optimized_record = LeCroyScript(
                project_id=project_id,
                test_name=f"{script.test_name}_v{len(history)+1}",
                protocol=llm_result.protocol,
                scenario=llm_result.scenario,
                description=script.description,
                peg_content=llm_result.peg_content,
                pevs_content=llm_result.pevs_content,
                generation_mode="llm_optimized",
                feedback_history=history,
                optimized_from=script.id
            )
            db.add(optimized_record)
            db.commit()
            db.refresh(optimized_record)

            # 记录日志
            log = AgentLog(
                project_id=project_id,
                agent_name="LeCroyScriptAgent",
                task_type="lecroy_script_optimize",
                status="completed",
                output=f"Optimized script {script_id} -> {optimized_record.id}: {feedback[:100]}"
            )
            db.add(log)
            db.commit()

            return {
                "success": True,
                "id": optimized_record.id,
                "test_name": optimized_record.test_name,
                "protocol": llm_result.protocol,
                "scenario": llm_result.scenario,
                "peg_content": llm_result.peg_content,
                "pevs_content": llm_result.pevs_content,
                "reasoning": llm_result.reasoning,
                "optimized_from": script.id
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def list_scripts(self, project_id: int, db_session) -> List[Dict]:
        """从数据库获取项目的所有 LeCroy 脚本"""
        scripts = db_session.query(LeCroyScript).filter(
            LeCroyScript.project_id == project_id
        ).order_by(LeCroyScript.created_at.desc()).all()

        return [
            {
                "id": s.id,
                "test_name": s.test_name,
                "protocol": s.protocol,
                "scenario": s.scenario,
                "generation_mode": getattr(s, "generation_mode", "template"),
                "peg_preview": s.peg_content[:200] + "..." if len(s.peg_content) > 200 else s.peg_content,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in scripts
        ]

    def get_script(self, project_id: int, script_id: int, db_session) -> Optional[Dict]:
        """从数据库获取指定脚本内容"""
        script = db_session.query(LeCroyScript).filter(
            LeCroyScript.id == script_id,
            LeCroyScript.project_id == project_id
        ).first()

        if not script:
            return None

        feedback_history = script.feedback_history
        if isinstance(feedback_history, str):
            try:
                feedback_history = json.loads(feedback_history)
            except Exception:
                feedback_history = []

        return {
            "id": script.id,
            "test_name": script.test_name,
            "protocol": script.protocol,
            "scenario": script.scenario,
            "description": script.description,
            "peg_content": script.peg_content,
            "pevs_content": script.pevs_content,
            "generation_mode": getattr(script, "generation_mode", "template"),
            "feedback_history": feedback_history or [],
            "optimized_from": getattr(script, "optimized_from", None),
            "created_at": script.created_at.isoformat() if script.created_at else None
        }

    def delete_script(self, project_id: int, script_id: int, db_session) -> bool:
        """删除指定脚本"""
        script = db_session.query(LeCroyScript).filter(
            LeCroyScript.id == script_id,
            LeCroyScript.project_id == project_id
        ).first()

        if not script:
            return False

        db_session.delete(script)
        db_session.commit()
        return True


# ── 便捷函数 ──

def generate_lecroy_scripts(
    project_id: int,
    description: str,
    test_name: str = None,
    mode: str = "hybrid"
) -> Optional[Dict]:
    """便捷函数：生成 LeCroy 脚本（同步包装）"""
    import asyncio
    service = LeCroyIntegrationService()
    return asyncio.run(service.generate_scripts(project_id, description, test_name, mode))

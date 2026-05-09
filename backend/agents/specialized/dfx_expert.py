from typing import Dict, Any
from backend.agents import TestingExpertAgent


class DFXTestingExpert(TestingExpertAgent):
    """DFX Testing Expert"""
    
    def __init__(self):
        super().__init__(
            name="DFX Testing Expert",
            expertise="DFX测试",
            description="专注于可制造性(DFM)、可服务性(DFS)、可测试性(DFT)测试"
        )
        self.capabilities.extend([
"可制造性测试(DFM)",
            "可服务性测试(DFS)",
            "可测试性测试(DFT)",
            "诊断功能测试",
            "调试接口测试",
            "生产测试支持"
        ])
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        task_type = context.get("task_type", "strategy")
        device_type = context.get("device_type", "SSD")
        requirements = context.get("requirements", "")
        
        # 优先调用 LLM 生成精准内容
        try:
            from backend.agents import call_llm
            system_msg = f"""你是{self.name}，{self.description}。
请根据设备类型和用户需求，生成专业的测试{task_type}文档。

输出要求：
1. 使用 Markdown 格式
2. 内容针对 {device_type} 设备特点定制
3. 包含具体的测试项、判定标准、推荐工具
4. 不要泛泛而谈
5. 你的输出必须直接以 Markdown 标题（# 或 ##）开头，不要有任何前言、背景说明、自我对话、计划、分析过程或思考过程。"""
            
            user_msg = f"""设备类型: {device_type}
测试需求: {requirements}
任务: 生成测试{task_type}

请直接输出 Markdown 文档。"""
            
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
            output = await call_llm(messages, temperature=1.0, max_tokens=2000)
            output = self._strip_thinking(output)
            if output and output.strip():
                return {"success": True, "agent": self.name, "output": output, "task_type": task_type}
        except Exception as e:
            print(f"[{self.name}] LLM failed: {e}, using fallback template")
        
        # LLM 失败回退到参数化模板
        return self._fallback(context)
    
    def _fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        task_type = context.get("task_type", "strategy")
        if task_type == "strategy":
            output = """# DFX测试策略


## DFM (Design for Manufacturing)
- 生产测试模式
- 良率提升验证
- 工艺窗口验证

## DFS (Design for Serviceability)
- 故障诊断功能
- 远程维护能力
- 现场升级支持

## DFT (Design for Testability)
- JTAG/BIST测试
- 边界扫描
- 内建自测试
"""
        elif task_type == "design":
            output = """# DFX测试设计

## 测试接口
- UART诊断接口
- I2C/SMBus接口
- JTAG接口
- 厂商特定接口
"""
        else:
            output = """# DFX测试用例

## TC-DFX-001: 生产测试模式
**步骤**: 1.进入测试模式 2.执行自测试 3.获取测试结果
**通过准则**: 所有自测试通过

## TC-DFX-002: 故障诊断
**步骤**: 1.注入故障 2.触发诊断 3.验证诊断结果
**通过准则**: 正确识别故障类型和位置
"""

            return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

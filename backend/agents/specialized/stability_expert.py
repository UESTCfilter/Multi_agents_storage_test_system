from typing import Dict, Any
from backend.agents import TestingExpertAgent


class StabilityExpert(TestingExpertAgent):
    """Stability Expert"""
    
    def __init__(self):
        super().__init__(
            name="Stability Expert",
            expertise="稳定性测试",
            description="专注于长时间稳定性测试、压力测试、老化测试等"
        )
        self.capabilities.extend([
"长时间运行测试",
            "压力测试",
            "老化测试",
            "温度循环测试",
            "电源循环测试",
            "振动测试"
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
            output = """# 稳定性测试策略


## 测试类型
1. 长时间运行测试 (7x24小时)
2. 压力测试 (满负载)
3. 老化测试 (高温)
4. 环境应力测试

## 监控指标
- 性能衰减
- 错误计数
- 温度变化
- 功耗变化
"""
        elif task_type == "design":
            output = """# 稳定性测试设计

## 测试环境
- 持续IO负载
- 温度循环箱
- 电源循环设备
- 振动台
"""
        else:
            output = """# 稳定性测试用例

## TC-STB-001: 72小时压力测试
**步骤**: 持续满负载运行72小时
**通过准则**: 无错误，性能衰减<5%

## TC-STB-002: 电源循环测试
**步骤**: 执行1000次电源循环
**通过准则**: 每次上电正常，无数据丢失
"""

            return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

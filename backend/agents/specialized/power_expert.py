from typing import Dict, Any
from backend.agents import TestingExpertAgent


class PowerExpert(TestingExpertAgent):
    """Power Expert"""
    
    def __init__(self):
        super().__init__(
            name="Power Expert",
            expertise="电源测试",
            description="专注于功耗测试、电源管理、电源状态转换等"
        )
        self.capabilities.extend([
"功耗测试",
            "电源管理测试",
            "电源状态转换测试",
            "电源抑制比测试",
            "上电/下电序列测试",
            "功耗优化验证"
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
            output = """# 电源测试策略


## 测试范围
1. 功耗特性
2. 电源管理状态
3. 上电/下电序列
4. 电源故障处理

## 关键指标
-  active功耗
- idle功耗
- L1.x功耗
- 峰值功耗
"""
        elif task_type == "design":
            output = """# 电源测试设计

## 测试设备
- 功率分析仪
- 电源时序分析仪
- 电子负载
- 可编程电源
"""
        else:
            output = """# 电源测试用例

## TC-PWR-001: 功耗状态测试
**步骤**: 测试各电源状态功耗
**通过准则**: 满足规范要求

## TC-PWR-002: 上电序列
**步骤**: 测量各电源轨上电时序
**通过准则**: 符合设计规范
"""

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

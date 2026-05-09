from typing import Dict, Any
from backend.agents import TestingExpertAgent


class ReliabilityExpert(TestingExpertAgent):
    """Reliability Expert"""
    
    def __init__(self):
        super().__init__(
            name="Reliability Expert",
            expertise="可靠性测试",
            description="专注于存储设备可靠性测试，包括寿命预测、错误恢复、容错等"
        )
        self.capabilities.extend([
"寿命预测测试",
            "错误恢复测试",
            "容错测试",
            "数据保持测试",
            "读干扰测试",
            "写放大测试"
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
            output = """# 可靠性测试策略


## 测试范围
1. 使用寿命验证
2. 错误处理能力
3. 数据保持特性
4. 环境应力测试

## 关键测试
- TBW (Total Bytes Written) 验证
- DWPD (Drive Writes Per Day) 验证
- 数据保持时间测试
- 温度循环测试
"""
        elif task_type == "design":
            output = """# 可靠性测试设计

## 测试方法
1. 加速寿命测试
2. 错误注入与恢复
3. 边界条件测试
4. 统计分析方法
"""
        else:
            output = """# 可靠性测试用例

## TC-REL-001: 写寿命测试
**步骤**: 持续写入直至寿命终止
**通过准则**: 达到标称TBW值

## TC-REL-002: 数据保持
**步骤**: 写入数据→高温老化→读取验证
**通过准则**: 数据保持率≥99.99%
"""

            return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

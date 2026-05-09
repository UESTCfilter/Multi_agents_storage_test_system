from typing import Dict, Any
from backend.agents import TestingExpertAgent


class StressTestingExpert(TestingExpertAgent):
    """Stress Testing Expert"""
    
    def __init__(self):
        super().__init__(
            name="Stress Testing Expert",
            expertise="压力测试与极限测试",
            description="专注于高负载压力测试、长时间运行测试、极限边界条件测试"
        )
        self.capabilities.extend([
"长时间压力测试",
            "高并发IO测试",
            "极限温度测试",
            "电源波动测试",
            "满盘状态测试",
            "碎片化测试"
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
                    return f"""# {device_type} 压力测试策略


## 长时间压力测试
- 连续7x24小时读写测试
- 周期性高低温循环测试
- 电源循环与掉电测试

## 高负载测试
- 100% IO负载持续运行
- 队列深度饱和测试
- 满盘数据完整性测试
"""
        elif task_type == "design":
            return """# 压力测试设计

## 测试矩阵
| 测试项 | 时长 | 判定标准 |
|--------|------|----------|
| 持续读写 | 168h | 无错误 |
| 温度循环 | 72h | 性能稳定 |
| 满盘测试 | 48h | 无丢数据 |
"""
        else:
            return """## 压力测试用例示例

### TC-STRESS-001: 168小时持续读写
- **目的**: 验证长期稳定性
- **步骤**: 连续随机读写168小时
- **预期**: 无UECC、无掉盘
"""

from typing import Dict, Any
from backend.agents import TestingExpertAgent


class AutomationExpert(TestingExpertAgent):
    """Automation Expert"""
    
    def __init__(self):
        super().__init__(
            name="Automation Expert",
            expertise="测试自动化框架",
            description="专注于测试自动化框架设计、脚本开发、CI/CD集成"
        )
        self.capabilities.extend([
"自动化框架设计",
            "测试脚本开发",
            "CI/CD集成",
            "报告自动生成",
            "并行执行优化"
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
                    return f"""# {device_type} 自动化测试策略


## 自动化框架
- Python + pytest 框架
- 设备抽象层封装
- 日志与报告集成

## CI/CD 集成
- Jenkins/GitLab CI
-  nightly 自动化运行
- 自动邮件通知
"""
        elif task_type == "design":
            return """# 自动化测试设计

## 框架架构
```
test_framework/
├── drivers/      # 设备驱动
├── tests/        # 测试用例
├── utils/        # 工具函数
└── reports/      # 报告输出
```

## 关键特性
- 并发执行支持
- 失败自动重试
- 截图/日志收集
"""
        else:
            return """## 自动化测试用例示例

```python
def test_power_on_self_check():
    device = get_device()
    result = device.power_cycle()
    assert result.status == "OK"
    assert device.identify() is not None
```
"""

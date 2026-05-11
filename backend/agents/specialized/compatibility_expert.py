from typing import Dict, Any
from backend.agents import TestingExpertAgent


class CompatibilityExpert(TestingExpertAgent):
    """Compatibility Expert"""
    
    def __init__(self):
        super().__init__(
            name="Compatibility Expert",
            expertise="兼容性测试",
            description="专注于硬件兼容性、软件兼容性、操作系统兼容性测试"
        )
        self.capabilities.extend([
"硬件兼容性测试",
            "软件兼容性测试",
            "操作系统兼容性测试",
            "驱动兼容性测试",
            "平台兼容性测试",
            "互操作性测试"
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
            output = """# 兼容性测试策略


## 硬件兼容
- 不同主板/平台
- 不同CPU架构
- 不同扩展卡

## 软件兼容
- 不同OS版本
- 不同驱动版本
- 主流应用程序

## 测试矩阵
- 平台 x OS x 驱动组合
"""
        elif task_type == "design":
            output = """# 兼容性测试设计

## 测试环境
- 多平台测试实验室
- 虚拟机环境
- 自动化测试框架
"""
        else:
            output = """# 兼容性测试用例

## TC-CMP-001: 主板兼容性
**步骤**: 在{platform_list}上验证功能
**通过准则**: 所有平台功能正常

## TC-CMP-002: OS兼容性
**步骤**: 在{os_list}上验证功能
**通过准则**: 所有OS识别正常，性能达标
"""

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

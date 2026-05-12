from typing import Dict, Any
from backend.agents import TestingExpertAgent


class DataIntegrityExpert(TestingExpertAgent):
    """Data Integrity Expert"""

    def __init__(self):
        super().__init__(
            name="Data Integrity Expert",
            expertise="数据完整性测试",
            description="专注于数据完整性验证，包括端到端数据保护、CRC校验、数据一致性等"
        )
        self.capabilities.extend([
            "端到端数据保护",
            "CRC校验验证",
            "数据一致性检查",
            "静默错误检测",
            "掉电保护测试",
            "元数据完整性"
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
            output = await call_llm(messages, temperature=1.0, max_tokens=4000)
            output = self._strip_thinking(output)
            if output and output.strip():
                return {"success": True, "agent": self.name, "output": output, "task_type": task_type}
        except Exception as e:
            print(f"[{self.name}] LLM failed: {e}, using fallback template")

        # LLM 失败回退到参数化模板
        return self._fallback(context)

    def _fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        task_type = context.get("task_type", "strategy")
        device_type = context.get("device_type", "SSD")

        if task_type == "strategy":
            output = self._generate_strategy(device_type)
        elif task_type == "design":
            output = self._generate_design(device_type)
        else:
            output = self._generate_cases(device_type)

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

    def _generate_strategy(self, device_type: str) -> str:
        return f"""# {device_type} 数据完整性测试策略

## 测试范围
1. 写读一致性验证
2. 多路径数据保护
3. 异常场景数据保护
4. 长时间运行数据一致性

## 关键测试点
- 端到端CRC校验
- 元数据完整性
- 静默错误检测(PI)
- 掉电数据保护
"""

    def _generate_design(self, device_type: str) -> str:
        return f"""# {device_type} 数据完整性测试设计

## 测试方法
1. 数据模式生成
2. 写入并验证CRC
3. 读取并重新计算CRC
4. 对比验证一致性
"""

    def _generate_cases(self, device_type: str) -> str:
        return f"""# {device_type} 数据完整性测试用例

## TC-DI-001: 端到端数据保护
**步骤**:
1. 生成带PI的数据
2. 写入设备
3. 读取并验证PI
**通过准则**: PI校验100%通过

## TC-DI-002: 掉电数据保护
**步骤**:
1. 启动持续写入
2. 模拟掉电
3. 上电后数据验证
**通过准则**: 无数据损坏
"""

from typing import Dict, Any
from backend.agents import TestingExpertAgent


class PhysicalLayerExpert(TestingExpertAgent):
    """Physical Layer Expert"""
    
    def __init__(self):
        super().__init__(
            name="Physical Layer Expert",
            expertise="物理层测试",
            description="专注于信号完整性、电源完整性、时序测试等物理层验证"
        )
        self.capabilities.extend([
"信号完整性测试",
            "电源完整性测试",
            "时序测试",
            "眼图分析",
            "抖动测试",
            "阻抗测试"
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
        if task_type == "strategy":
            output = """# 物理层测试策略


## 信号完整性
- 眼图测试
- 抖动分析
- 插入损耗
- 回波损耗

## 电源完整性
- 电源噪声
- 去耦验证
- 电压波动

## 时序测试
- 建立/保持时间
- 传播延迟
- 时钟抖动
"""
        elif task_type == "design":
            output = """# 物理层测试设计

## 测试设备
- 示波器
- 矢量网络分析仪
- 误码率测试仪
- 电源分析仪
"""
        else:
            output = """# 物理层测试用例

## TC-PHY-001: PCIe眼图测试
**步骤**: 测量发送端眼图
**通过准则**: 眼图满足PCIe规范模板

## TC-PHY-002: 电源噪声测试
**步骤**: 测量各电源轨噪声
**通过准则**: 噪声<规范要求
"""

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

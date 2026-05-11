from typing import Dict, Any
from backend.agents import TestingExpertAgent


class ProtocolExpert(TestingExpertAgent):
    """Protocol Expert"""
    
    def __init__(self):
        super().__init__(
            name="Protocol Expert",
            expertise="PCIe/NVMe协议测试",
            description="专注于PCIe和NVMe协议一致性测试，包括TLP/DLLP、NVMe命令集、错误处理等"
        )
        self.capabilities.extend([
"PCIe链路测试",
            "NVMe命令集测试",
            "TLP/DLLP验证",
            "MSI/MSI-X测试",
            "SR-IOV测试",
            "热插拔测试"
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
            output = f"""# {device_type} 协议测试策略


## PCIe协议测试
1. 链路训练与状态机
2. 电源管理状态转换
3. 流量控制验证
4. 错误处理机制

## NVMe协议测试
1. Admin命令集
2. IO命令集
3. 队列管理
4. 命名空间操作
"""
        elif task_type == "design":
            output = """# 协议测试设计

## 测试工具
- 协议分析仪
- PCIe exerciser
- NVMe compliance suite

## 测试场景
1. 正常操作流程
2. 错误注入测试
3. 边界条件测试
4. 时序测试
"""
        else:
            output = """# 协议测试用例

## TC-PROT-001: PCIe Link Training
**步骤**: 1.设备上电 2.监测LTSSM 3.验证链路状态
**通过准则**: 链路宽度/速率协商正确

## TC-PROT-002: NVMe Reset流程
**步骤**: 1.发送Controller Reset 2.验证CC.EN 3.等待就绪
**通过准则**: Reset流程符合规范
"""

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

from typing import Dict, Any
from backend.agents import TestingExpertAgent


class SecurityExpert(TestingExpertAgent):
    """Security Expert"""
    
    def __init__(self):
        super().__init__(
            name="Security Expert",
            expertise="安全测试",
            description="专注于存储设备安全功能测试，包括加密、擦除、认证等"
        )
        self.capabilities.extend([
"数据加密测试",
            "安全擦除测试",
            "TCG Opal测试",
            "安全启动测试",
            "固件完整性验证",
            "访问控制测试"
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
            output = """# 安全测试策略


## 测试范围
1. 数据加密功能
2. 密钥管理
3. 安全擦除
4. 访问控制
5. 固件安全

## 合规标准
- TCG Opal 2.0
- IEEE 1667
- FIPS 140-2
"""
        elif task_type == "design":
            output = """# 安全测试设计

## 测试方法
1. 加密算法验证
2. 密钥生命周期测试
3. 安全擦除验证
4. 渗透测试
"""
        else:
            output = """# 安全测试用例

## TC-SEC-001: AES加密验证
**步骤**: 1.启用加密 2.写入数据 3.物理读取验证加密
**通过准则**: 数据已加密，无法直接读取

## TC-SEC-002: 安全擦除
**步骤**: 1.写入数据 2.执行安全擦除 3.尝试恢复数据
**通过准则**: 数据无法恢复
"""

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

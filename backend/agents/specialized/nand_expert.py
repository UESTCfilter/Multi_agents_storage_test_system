from typing import Dict, Any
from backend.agents import TestingExpertAgent


class NANDStackExpert(TestingExpertAgent):
    """NAND Stack Expert"""
    
    def __init__(self):
        super().__init__(
            name="NAND Stack Expert",
            expertise="NAND闪存测试",
            description="NAND闪存测试专家，精通NAND特性、FTL算法、坏块管理、磨损均衡等测试"
        )
        self.capabilities.extend([
            "NAND特性测试",
            "FTL算法验证",
            "坏块管理测试",
            "磨损均衡验证",
            "ECC纠错测试",
            "读取干扰测试",
            "编程干扰测试"
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
        device_name = context.get("device_name", "SSD设备")
        
        if task_type == "strategy":
            output = self._generate_strategy(device_name, context)
        elif task_type == "design":
            output = self._generate_design(device_name, context)
        elif task_type == "case":
            output = self._generate_cases(device_name, context)
        else:
            output = "# NAND Stack 测试分析\n\n## 分析要点\n1. NAND特性验证\n2. FTL算法评估\n3. 可靠性测试\n"
        
        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}
    
    def _generate_strategy(self, device_name: str, context: Dict) -> str:
        return f"""# NAND Stack 测试策略


## 测试范围
1. **NAND特性测试**
   - 块擦除特性验证
   - 页编程特性
   - 读取特性分析

2. **FTL算法测试**
   - 地址映射验证
   - 垃圾回收策略
   - 预取算法验证

3. **可靠性测试**
   - 坏块管理
   - 磨损均衡
   - 数据保持

## 测试重点
针对{device_name}的NAND特性，重点测试：
- 不同温度下的编程/擦除性能
- ECC纠错能力边界
- 长时间数据保持特性
"""

    def _generate_design(self, device_name: str, context: Dict) -> str:
        return f"""# NAND Stack 测试设计

## 测试模块

### 1. 块管理测试
- 坏块识别与标记
- 备用块切换
- 块状态管理

### 2. 页操作测试
- 页编程验证
- 页读取验证
- 多页并行操作

### 3. ECC测试
- 纠错能力测试
- 错误注入测试
- 纠错延迟测量
"""

    def _generate_cases(self, device_name: str, context: Dict) -> str:
        ecc = context.get("ecc_capability", "72")
        return f"""# NAND Stack 测试用例

## TC-NAND-001: 块擦除验证
**目的**: 验证块擦除功能正常
**步骤**:
1. 选择测试块
2. 执行擦除操作
3. 验证块状态为已擦除
4. 检查擦除时间

**通过准则**: 擦除时间≤3ms，块状态正确

## TC-NAND-002: ECC纠错能力
**目的**: 验证ECC纠错边界
**步骤**:
1. 注入可控位错误
2. 执行读取操作
3. 验证纠错结果

**通过准则**: 可纠正{ecc}位错误
"""

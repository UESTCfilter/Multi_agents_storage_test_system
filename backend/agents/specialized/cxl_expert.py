from typing import Dict, Any
from backend.agents import TestingExpertAgent


class CXLExpert(TestingExpertAgent):
    """CXL Expert"""
    
    def __init__(self):
        super().__init__(
            name="CXL Expert",
            expertise="CXL协议测试",
            description="专注于CXL (Compute Express Link) 协议测试，包括CXL.io、CXL.cache、CXL.mem"
        )
        self.capabilities.extend([
"CXL.io协议测试",
            "CXL.mem协议测试",
            "CXL.cache协议测试",
            "内存池化测试",
            "内存扩展测试",
            "CXL 2.0/3.0特性测试"
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
            output = """# CXL协议测试策略


## CXL.io 测试
- PCIe 5.0/6.0兼容性
- CXL事务层验证
- CXL链路训练

## CXL.mem 测试
- 内存池化功能
- 内存扩展功能
- HDM (Host-managed Device Memory) 测试
- 一致性验证

## CXL.cache 测试
- 缓存一致性协议
- 监听过滤器验证

## 关键测试点
- 256B Flit模式
- 68B Flit模式
- 链路完整性
- 内存事务排序
"""
        elif task_type == "design":
            output = """# CXL测试设计

## 测试模块
1. CXL链路初始化
2. CXL DVSEC验证
3. CXL RAS功能
4. CXL PMU (性能监控)

## 测试方法
- 协议分析仪捕获
- 错误注入
- 压力测试
"""
        else:
            output = """# CXL测试用例

## TC-CXL-001: CXL Link Initialization
**步骤**: 1.设备上电 2.检测CXL DVSEC 3.验证链路协商
**通过准则**: CXL模式激活，链路稳定

## TC-CXL-002: Memory Pooling
**步骤**: 1.配置内存池 2.分配设备内存 3.执行读写
**通过准则**: 内存访问正常，数据一致

## TC-CXL-003: CXL RAS Error Injection
**步骤**: 1.注入可纠正错误 2.验证错误日志 3.验证恢复
**通过准则**: 错误正确记录，系统继续运行
"""

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

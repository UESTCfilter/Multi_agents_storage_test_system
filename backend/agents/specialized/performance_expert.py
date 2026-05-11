from typing import Dict, Any
from backend.agents import TestingExpertAgent


class PerformanceExpert(TestingExpertAgent):
    """Performance Expert"""
    
    def __init__(self):
        super().__init__(
            name="Performance Expert",
            expertise="性能测试",
            description="专注于存储设备性能测试，包括带宽、IOPS、延迟、QoS等"
        )
        self.capabilities.extend([
"带宽测试",
            "IOPS测试",
            "延迟测试",
            "QoS测试",
            "混合负载测试",
            "性能一致性测试"
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
            output = """# 性能测试策略


## 测试维度
1. 带宽 (Sequential Read/Write)
2. IOPS (Random Read/Write)
3. 延迟 (Read/Write Latency)
4. QoS (Quality of Service)

## 测试条件
- 不同队列深度 (QD1, QD4, QD16, QD32)
- 不同块大小 (4K, 8K, 64K, 128K, 1M)
- 不同写入比例 (100/0, 70/30, 50/50, 0/100)
- 不同并发度

## 关键指标
- 顺序读带宽 ≥ 7GB/s
- 顺序写带宽 ≥ 3GB/s
- 随机读IOPS ≥ 1000K
- 随机写IOPS ≥ 400K
- 读延迟 ≤ 100μs (P99)
- 写延迟 ≤ 50μs (P99)
"""
        elif task_type == "design":
            output = """# 性能测试设计

## 测试工具
- FIO (Flexible I/O Tester)
- Iometer
- VDBench

## 测试方法
1. 预处理(写入全盘2遍)
2. 稳态测试(持续30分钟)
3. 峰值测试(短时间爆发)
4. 一致性测试(长时间稳定性)
"""
        else:
            output = """# 性能测试用例

## TC-PERF-001: 顺序读带宽
**配置**: 128KB, QD32, 8线程
**通过准则**: ≥ 7GB/s

## TC-PERF-002: 随机读IOPS
**配置**: 4KB, QD128, 4线程, 随机
**通过准则**: ≥ 1000K IOPS

## TC-PERF-003: 读延迟P99
**配置**: 4KB, QD1, 随机读
**通过准则**: P99 ≤ 100μs
"""

        return {"success": True, "agent": self.name, "output": output, "task_type": task_type}

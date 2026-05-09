"""PCM Media Expert - PCM介质专家

专注于相变存储器物理特性
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class PCMMediaExpert(TestingExpertAgent):
    """PCM介质专家"""
    
    def __init__(self):
        super().__init__(
            name="PCM Media Expert",
            expertise="PCM介质特性测试",
            description="专注于相变存储器物理特性、相变机制、读写原理、GST材料特性"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# PCM介质特性测试策略

## 测试目标
验证PCM（Phase Change Memory）介质的物理特性和可靠性

## PCM工作原理
- **RESET状态**: 非晶态，高电阻（逻辑0）
- **SET状态**: 晶态，低电阻（逻辑1）
- **相变材料**: GST（Ge-Sb-Te）合金
- **写入机制**: 加热相变（SET熔化结晶，RESET快速冷却）

## 关键测试项

### 材料特性
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 电阻分布 | RESET/SET分离清晰 | 参数分析仪 |
| 阈值电压 | 符合规格 | IV测试 |
| 相变温度 | SET~150°C, RESET~600°C | 热分析 |

### 读写特性
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 写电流 | SET 0.2-0.4mA, RESET 0.6-1.0mA | 参数分析仪 |
| 写脉冲宽度 | SET 100-500ns, RESET 10-50ns | 脉冲测试 |
| 读电流 | 不影响状态 | 验证测试 |

### 可靠性特性
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 保持时间 | >10年@85°C | 高温保持 |
| 循环耐久 | >10^8次 | 耐久测试 |
| 抗干扰 | 读不扰动 | 读干扰测试 |

## PCM vs NAND对比
| 特性 | PCM | NAND |
|------|-----|------|
| 读写粒度 | Byte | Page |
| 写入前擦除 | No | Yes |
| 耐久性 | 10^8 | 10^3-10^5 |
| 读取延迟 | ~100ns | ~50μs |
| 写入延迟 | ~100ns-10μs | ~500μs-1ms |
| 保持时间 | 10年 | 10年 |
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## PCM介质测试设计

### 测试环境
- PCM测试芯片
- 参数分析仪
- 高低温箱
- 脉冲发生器

### 测试步骤
1. 测量基础IV特性
2. 确定RESET/SET参数
3. 测试电阻分布
4. 高温保持测试
5. 耐久性循环测试
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## PCM介质测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| PCM-001 | 电阻分布 | 测量RESET/SET电阻 | 分布分离良好 |
| PCM-002 | 写电流优化 | 扫描写电流 | 找到最优值 |
| PCM-003 | 写脉冲优化 | 扫描写脉冲宽度 | 确定最短时间 |
| PCM-004 | 保持特性 | 高温存储测试 | 10年等效通过 |
| PCM-005 | 耐久测试 | 10^8次循环 | 性能不衰减 |
| PCM-006 | 读干扰 | 反复读取 | 状态不改变 |
"""
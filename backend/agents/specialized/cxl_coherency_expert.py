"""CXL Coherency Expert - CXL缓存一致性专家

专注于CXL缓存一致性协议验证
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class CXLCoherencyExpert(TestingExpertAgent):
    """CXL缓存一致性专家"""
    
    def __init__(self):
        super().__init__(
            name="CXL Coherency Expert",
            expertise="CXL缓存一致性测试",
            description="专注于缓存一致性协议、Snoop过滤器、一致性域管理、MOESI状态机"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# CXL缓存一致性测试策略

## 测试目标
验证CXL设备与CPU之间的缓存一致性正确性

## CXL一致性协议要点
- **MOESI状态机**: Modified/Owned/Exclusive/Shared/Invalid
- **Snoop过滤器**: 追踪缓存行状态
- **一致性域**: 主机和设备共享一致性域
- **HDM-DB**: Host vs Device Bias控制一致性责任

## 关键测试项

### 一致性状态机
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| M→S转换 | 正确降级 | 协议分析仪 |
| E→I失效 | 正确失效 | 功能测试 |
| O状态处理 | 正确转发 | 一致性验证 |

### Snoop过滤器
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 命中检测 | 正确检测 | 协议分析仪 |
| 过滤器容量 | 不溢出 | 压力测试 |
| 错误处理 | 优雅降级 | 故障注入 |

### 并发一致性
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 多核并发 | 一致性保证 | 并发测试 |
| 原子操作 | 正确互斥 | 功能测试 |
| 内存屏障 | 正确序 | 验证工具 |

## 一致性测试模式
```
测试场景1: 单写多读
[CPU0 Write] → [Device Read] → [CPU1 Read]
                  ↓
            验证最终一致性

测试场景2: 多写竞争
[CPU0 Write A] ─┐
                 ├──→ 验证串行化
[CPU1 Write B] ─┘

测试场景3: 原子操作
[Multiple CPUs] → [Atomic Add] → [验证正确结果]
```
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## CXL一致性测试设计

### 测试环境
- 支持CXL.cache的多CPU系统
- Type2 CXL设备
- 一致性验证工具
- 协议分析仪

### 测试步骤
1. 建立一致性域
2. 执行状态机测试
3. 验证Snoop过滤
4. 并发压力测试
5. 原子操作验证
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## CXL一致性测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| COH-001 | M状态降级 | M状态行被读取 | 正确降为O/S |
| COH-002 | 缓存失效 | 远程写入 | 本地缓存失效 |
| COH-003 | Snoop命中 | 查询缓存行 | 正确返回状态 |
| COH-004 | 多核竞争 | 多核写同一行 | 串行化结果 |
| COH-005 | 原子操作 | CAS/FA操作 | 原子性保证 |
| COH-006 | 内存屏障 | 乱序访问+屏障 | 正确序保证 |
"""
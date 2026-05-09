"""Type2 Device Expert - CXL Type2设备专家

专注于带缓存的CXL内存设备（Type 2）
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class Type2DeviceExpert(TestingExpertAgent):
    """CXL Type2设备专家 - 带缓存的CXL设备"""
    
    def __init__(self):
        super().__init__(
            name="Type2 Device Expert",
            expertise="CXL Type2设备测试",
            description="专注于带缓存的CXL设备、HDM-DB、Back Invalidation、缓存一致性"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# CXL Type2设备测试策略

## 测试目标
验证带缓存的CXL内存设备（Type 2）功能正确性

## Type2设备特性
- **设备缓存**: 设备本地缓存加速访问
- **HDM-DB**: Host-managed Device Memory with Device Bias
- **Back Invalidation**: 缓存一致性回写
- **CXL.cache协议**: 设备与主机缓存一致性

## 关键测试项

### HDM-DB功能
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| Host Bias模式 | 主机管理缓存 | 协议分析仪 |
| Device Bias模式 | 设备管理缓存 | 功能测试 |
| 模式切换 | 平滑切换 | 性能测试 |

### Back Invalidation
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| BI消息处理 | 正确失效缓存行 | 协议分析仪 |
| BI响应时间 | < 1μs | 延迟测试 |
| BI风暴处理 | 不丢消息 | 压力测试 |

### 缓存一致性
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 读写一致性 | 所有缓存一致 | 一致性测试 |
| 原子操作 | 正确执行 | 功能测试 |
| 内存序 | 符合要求 | 验证工具 |

## 测试拓扑
```
[CPU Host]──CXL──[Type2 Device]
     │              │
     └─CXL.cache────┤
                    │(Device Cache)
              [Device Memory]
```
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## Type2设备测试设计

### 测试环境
- Type2 CXL设备
- 支持CXL.cache的主机
- 协议分析仪
- 缓存一致性验证工具

### 测试步骤
1. 初始化Type2设备
2. 配置HDM-DB区域
3. 测试Host/Device Bias切换
4. 验证BI功能
5. 一致性压力测试
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## Type2设备测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| T2-001 | HDM-DB初始化 | 配置HDM-DB区域 | 容量识别正确 |
| T2-002 | Host Bias访问 | Host模式读写 | 数据正确 |
| T2-003 | Device Bias访问 | Device模式读写 | 缓存命中提升 |
| T2-004 | 模式切换 | 切换Bias模式 | 切换成功 |
| T2-005 | Back Invalidation | 触发BI | 缓存行失效 |
| T2-006 | 并发一致性 | 多核并发访问 | 一致性保证 |
"""
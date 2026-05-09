"""Type3 Device Expert - CXL Type3设备专家

专注于纯内存扩展的CXL设备
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class Type3DeviceExpert(TestingExpertAgent):
    """CXL Type3设备专家 - 纯内存扩展"""
    
    def __init__(self):
        super().__init__(
            name="Type3 Device Expert",
            expertise="CXL Type3设备测试",
            description="专注于纯内存扩展CXL设备、内存池化、NUMA节点管理、容量扩展"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# CXL Type3设备测试策略

## 测试目标
验证纯内存扩展CXL设备（Type 3）功能正确性和性能

## Type3设备特性
- **纯内存扩展**: 无设备缓存，纯CXL.mem协议
- **内存池化**: 作为系统内存资源池
- **NUMA节点**: 作为独立的内存-only NUMA节点
- **大容量扩展**: 单设备可达TB级容量

## 关键测试项

### 内存访问
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 基本读写 | 数据正确 | 内存测试工具 |
| 带宽测试 | 接近理论值 | 带宽测试 |
| 延迟测试 | P99 < 500ns | 延迟测试 |
| 地址对齐 | 各种粒度访问 | 功能测试 |

### NUMA集成
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| NUMA识别 | 正确识别为NUMA节点 | OS工具 |
| 内存分配 | 正确分配到CXL内存 | 系统测试 |
| 跨节点访问 | 正确访问 | 性能测试 |

### 容量扩展
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 单设备容量 | 识别全部容量 | OS工具 |
| 多设备聚合 | 总容量正确 | 系统测试 |
| 在线扩容 | 支持热插拔 | 功能测试 |

## 延迟分级
```
Local DRAM:    ~100ns
CXL Memory:    ~300-500ns  ← Type3目标
Remote DRAM:   ~150-300ns
Remote CXL:    ~400-700ns
```

## 性能目标
- **带宽**: 每通道32-64GB/s (PCIe 5.0/6.0)
- **IOPS**: 目标210M IOPS聚合
- **延迟**: P99 < 500ns
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## Type3设备测试设计

### 测试环境
- Type3 CXL设备
- 支持CXL的主机平台
- 内存测试工具
- NUMA分析工具

### 测试步骤
1. 初始化Type3设备
2. 验证容量识别
3. 测试读写带宽
4. 测量访问延迟
5. 验证NUMA集成
6. 多设备扩展测试
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## Type3设备测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| T3-001 | 容量识别 | 启动识别设备 | 容量正确 |
| T3-002 | 读写带宽 | 顺序/随机读写 | 达到规格 |
| T3-003 | 延迟分布 | 测量访问延迟 | P99<500ns |
| T3-004 | NUMA节点 | 检查NUMA拓扑 | 正确显示 |
| T3-005 | 内存分配 | 分配CXL内存 | 分配成功 |
| T3-006 | 多设备聚合 | 测试多设备 | 容量聚合 |
"""
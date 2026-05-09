"""QoS Expert - 服务质量专家

专注于存储系统服务质量测试
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class QoSExpert(TestingExpertAgent):
    """QoS专家"""
    
    def __init__(self):
        super().__init__(
            name="QoS Expert",
            expertise="服务质量测试",
            description="专注于尾延迟P99/P999、延迟分级、SLA保障、性能隔离"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# QoS测试策略

## 测试目标
验证存储系统在不同负载下的服务质量保障能力

## QoS核心指标
- **尾延迟**: P99、P99.9、P99.99延迟
- **延迟分级**: Local/Remote/CXL内存延迟层次
- **性能隔离**: 多租户间互不干扰
- **SLA保障**: 满足预设服务等级协议

## 关键测试项

### 尾延迟
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| P99延迟 | < 目标值 | 延迟测试 |
| P999延迟 | < 2x P99 | 延迟测试 |
| 延迟稳定性 | 无尖峰 | 监控工具 |
| 延迟分布 | CDF平滑 | 统计分析 |

### 延迟分级
| 层级 | 目标延迟 | 应用场景 |
|------|---------|---------|
| Local DRAM | ~100ns | 热数据、元数据 |
| CXL Memory | ~300-500ns | 大容量扩展 |
| Remote CXL | ~400-700ns | 跨节点访问 |
| SSD | ~10-100μs | 持久化存储 |

### 性能隔离
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 多租户隔离 | 干扰<10% | 压力测试 |
| 优先级调度 | 高优先执行 | 调度测试 |
| 资源预留 | 预留生效 | 资源测试 |

### SLA验证
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| IOPS SLA | 达标率>99% | 监控测试 |
| 带宽SLA | 达标率>99% | 监控测试 |
| 延迟SLA | 达标率>99.9% | 监控测试 |

## QoS保障机制
```
1. IO调度: MQ-DEADLINE, BFQ, Kyber
2. 优先级: 高/中/低优先级队列
3. 限流: 基于令牌桶的带宽限制
4. 隔离: Cgroup blkio控制
```
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## QoS测试设计

### 测试环境
- 企业级存储系统
- 多租户模拟环境
- 性能监控工具
- 延迟分析工具

### 测试步骤
1. 基线延迟测试
2. 尾延迟分析
3. 延迟分级验证
4. 性能隔离测试
5. SLA压力测试
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## QoS测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| QoS-001 | P99延迟 | 混合负载测试 | P99<500ns(CXL) |
| QoS-002 | 延迟尖峰 | 长时间监控 | 无异常尖峰 |
| QoS-003 | 多租户隔离 | 干扰负载测试 | 干扰<10% |
| QoS-004 | 优先级调度 | 高低优先IO | 高优响应快 |
| QoS-005 | SLA达标 | 7x24监控 | 达标>99.9% |
| QoS-006 | 延迟分级 | 多层访问 | 延迟符合层级 |
"""
"""Workload Expert - 工作负载专家

专注于企业工作负载模拟
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class WorkloadExpert(TestingExpertAgent):
    """工作负载专家"""
    
    def __init__(self):
        super().__init__(
            name="Workload Expert",
            expertise="工作负载测试",
            description="专注于OLTP/OLAP、SNIA PTS、AI训练负载、VDI/VSI模型"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# 工作负载测试策略

## 测试目标
使用真实企业工作负载验证存储系统性能和可靠性

## 工作负载类型

### 数据库负载
| 类型 | 特征 | 典型应用 |
|------|------|---------|
| OLTP | 随机小IO、高IOPS | 交易系统、ERP |
| OLAP | 顺序大IO、高带宽 | 数据分析、BI |
| HTAP | 混合负载 | 实时分析 |

### 虚拟化负载
| 类型 | 特征 | 典型应用 |
|------|------|---------|
| VDI | 启动风暴、重复数据 | 虚拟桌面 |
| VSI | 混合VDI+服务器 | 混合虚拟化 |

### AI/ML负载
| 类型 | 特征 | 典型应用 |
|------|------|---------|
| 训练 | 大文件、高吞吐 | 模型训练 |
| 推理 | 小延迟敏感 | 在线推理 |
| 检查点 | 周期性大写 | 容错恢复 |

## SNIA PTS规范
| 测试项目 | 描述 |
|----------|------|
| IOPS测试 | 稳态IOPS测量 |
| 吞吐量测试 | 顺序读写带宽 |
| 延迟测试 | 读写延迟分布 |
| 写饱和测试 | 稳态性能确定 |
| 一致性测试 | 长时间稳定性 |

## 关键测试项

### OLTP测试
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| IOPS性能 | >100K IOPS | Sysbench, TPC-C |
| 响应时间 | P95<10ms | 延迟监控 |
| 并发处理 | 支持高并发 | 压力测试 |

### OLAP测试
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 扫描带宽 | 最大化带宽 | TPC-H, TPC-DS |
| 查询延迟 | 分钟级完成 | 查询测试 |
| 并发查询 | 多查询并行 | 压力测试 |

### AI训练测试
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 数据加载 | 不阻塞GPU | MLperf |
| 检查点写 | 快速持久化 | 自定义测试 |
| 大数据集 | 高效访问 | DLIO |

## 工作负载特征参数
```
OLTP: 8KB随机, 读写比70:30, QD32
OLAP: 1MB顺序, 全读取, QD64
AI训练: 大文件顺序, 突发读取, 周期性检查点
VDI: 4KB随机, 70%读, 启动时突发
```
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## 工作负载测试设计

### 测试环境
- 存储系统
- 工作负载生成器 (fio, Sysbench, TPC)
- 性能监控工具
- 业务模拟环境

### 测试步骤
1. 配置工作负载参数
2. 执行预热至稳态
3. 运行测试并收集数据
4. 分析性能指标
5. 验证SLA合规
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## 工作负载测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| WL-001 | OLTP负载 | TPC-C模拟 | TPS达标 |
| WL-002 | OLAP负载 | TPC-H查询 | 查询时间达标 |
| WL-003 | AI训练 | 模拟训练流程 | GPU利用率>90% |
| WL-004 | SNIA PTS | 标准测试套件 | 符合规范 |
| WL-005 | VDI负载 | 启动风暴 | 响应时间达标 |
| WL-006 | 混合负载 | OLTP+OLAP混合 | 性能可预测 |
"""
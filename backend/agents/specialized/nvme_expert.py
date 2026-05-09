"""NVMe Expert - NVMe协议专家

专注于NVMe协议测试
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class NVMeExpert(TestingExpertAgent):
    """NVMe专家"""
    
    def __init__(self):
        super().__init__(
            name="NVMe Expert",
            expertise="NVMe协议测试",
            description="专注于NVMe协议、队列管理、Admin/IO命令、PCIe集成"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# NVMe协议测试策略

## 测试目标
验证NVMe设备符合协议规范，确保功能和性能

## NVMe核心特性
- **队列机制**: 多达64K SQ/CQ对，每队列64K深度
- **命令集**: Admin命令集 + IO命令集
- **多命名空间**: 支持多个逻辑设备
- **SR-IOV**: 单根IO虚拟化支持

## 关键测试项

### 队列管理
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 队列创建 | 支持最大队列数 | 协议测试 |
| 队列深度 | 支持最大深度 | 功能测试 |
| 并发处理 | 无竞争条件 | 压力测试 |
| MSI-X中断 | 正确路由 | 中断测试 |

### Admin命令
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 识别命令 | 返回正确数据 | 功能测试 |
| 特性管理 | Get/Set Feature | 功能测试 |
| 命名空间管理 | 创建/删除NS | 功能测试 |
| 固件管理 | 下载/激活FW | 功能测试 |

### IO命令
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 读写命令 | 数据正确 | 数据测试 |
| Flush命令 | 数据持久化 | 掉电测试 |
| DSM命令 |  discard/TRIM | 功能测试 |
| 原子写 | 保证原子性 | 一致性测试 |

### 协议合规
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| PCIe集成 | 符合规范 | 协议分析仪 |
| 错误处理 | 正确处理 | 故障注入 |
| 电源管理 | 状态转换正确 | 功耗测试 |

## NVMe版本支持
| 版本 | 特性 |
|------|------|
| 1.3 | SR-IOV, Namespace写保护 |
| 1.4 | PMR, I/O determinism |
| 2.0 | ZNS, KV, NVMe/TCP |
| 2.0b| C2C (CXL over PCIe) |

## 性能指标
- **IOPS**: 随机4K QD32 > 100K
- **带宽**: 顺序128K > 7GB/s (PCIe 4.0 x4)
- **延迟**: 4K QD1 < 10μs
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## NVMe协议测试设计

### 测试环境
- NVMe SSD
- NVMe测试平台
- 协议分析仪
- NVMe CTS测试套件

### 测试步骤
1. 基础识别测试
2. 队列功能测试
3. Admin命令测试
4. IO命令测试
5. 协议合规测试
6. 性能基准测试
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## NVMe协议测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| NVMe-001 | 识别命令 | 发送Identify | 返回正确数据 |
| NVMe-002 | 队列创建 | 创建多个队列 | 全部成功 |
| NVMe-003 | 读写测试 | 各种粒度读写 | 数据正确 |
| NVMe-004 | 并发测试 | 多队列并发 | 无数据损坏 |
| NVMe-005 | Flush测试 | 写后Flush掉电 | 数据完整 |
| NVMe-006 | 错误处理 | 注入错误 | 正确处理 |
"""
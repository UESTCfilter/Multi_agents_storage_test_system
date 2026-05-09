"""CXL Switch Expert - CXL交换机专家

专注于CXL Switch多主机连接、内存池化
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class CXLSwitchExpert(TestingExpertAgent):
    """CXL交换机专家"""
    
    def __init__(self):
        super().__init__(
            name="CXL Switch Expert",
            expertise="CXL交换机测试",
            description="专注于CXL Switch、多主机连接、fan-out拓扑、内存池化"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# CXL Switch测试策略

## 测试目标
验证CXL Switch多主机连接能力和内存池化功能

## CXL Switch关键特性
- **多主机连接**: 支持多主机共享内存资源
- **Fan-out拓扑**: 扩展连接端口数量
- **内存池化**: 动态分配内存给不同主机
- **多级Switch**: CXL 3.0支持fabric架构

## 测试拓扑
```
[Host A]──┬──[CXL Switch]──┬──[CXL Memory Device 1]
[Host B]──┤                ├──[CXL Memory Device 2]
[Host C]──┘                └──[CXL Memory Device 3]
```

## 关键测试项

### 多主机访问
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 并发内存访问 | 无冲突、数据一致 | 多主机测试平台 |
| 访问仲裁 | 公平调度 | 性能分析工具 |
| 隔离性 | 主机间不干扰 | 功能测试 |

### 内存池化
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 动态分配 | 容量按需分配 | 系统测试 |
| 热插拔 | 设备增删正常 | 自动化测试 |
| 容量扩展 | 在线扩容成功 | 压力测试 |

### 性能测试
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| Switch延迟 | < 100ns | 延迟测试 |
| 聚合带宽 | 接近理论值 | 带宽测试 |
| 扩展性 | 线性扩展 | 规模测试 |

## 测试环境要求
- 支持CXL Switch的开发平台
- 多台CXL主机
- 多台CXL内存设备
- 协议分析仪
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## CXL Switch测试设计

### 测试环境
- CXL Switch设备
- 3-4台CXL主机
- 多台CXL内存设备
- 协议分析仪

### 测试步骤
1. 搭建Switch拓扑
2. 配置多主机连接
3. 测试并发访问
4. 验证内存池化
5. 性能基准测试
6. 故障注入测试
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## CXL Switch测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| SW-001 | 多主机初始化 | 所有主机初始化Switch | 各主机识别Switch |
| SW-002 | 并发读写 | 多主机同时访问内存 | 数据一致性 |
| SW-003 | 内存池分配 | 动态分配内存给主机 | 分配成功 |
| SW-004 | 设备热插拔 | 在线添加/移除设备 | 系统正常运行 |
| SW-005 | Switch故障 | Switch重启测试 | 主机正确恢复 |
| SW-006 | 带宽扩展 | 测试多设备聚合 | 线性扩展 |
"""
"""CXL Protocol Expert - CXL协议合规专家

专注于CXL 1.1/2.0/3.0协议合规性测试
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class CXLProtocolExpert(TestingExpertAgent):
    """CXL协议合规专家"""
    
    def __init__(self):
        super().__init__(
            name="CXL Protocol Expert",
            expertise="CXL协议合规测试",
            description="专注于CXL 1.1/2.0/3.0协议合规、CV测试、PCIe集成"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        device_name = context.get("device_name", "CXL设备")
        
        return f"""# {device_name} CXL协议合规测试策略

## 测试目标
验证设备符合CXL规范要求，确保PCIe集成和协议兼容性

## 协议版本支持
- **CXL 1.1**: 基础内存扩展、68B Flit
- **CXL 2.0**: 内存池化、Switch支持、256B Flit、IDE安全
- **CXL 3.0**: 多级Switch、fabric架构、增强一致性

## 关键测试项

### CXL.io (I/O协议)
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| PCIe 5.0/6.0兼容性 | 链路训练成功 | 协议分析仪 |
| CXL事务层验证 | 事务正确性 | CV测试套件 |
| 256B Flit模式 | Flit格式正确 | 逻辑分析仪 |
| IDE(完整性+数据加密) | 加密/解密正确 | 安全测试工具 |

### CXL.mem (内存协议)
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| HDM (Host-managed Device Memory) | 地址映射正确 | 内存测试工具 |
| 内存池化功能 | 多主机访问正常 | 系统测试平台 |
| 容量扩展 | 容量识别正确 | OS工具 |

### CXL.cache (缓存协议)
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 缓存一致性 | 一致性域正常 | 一致性验证平台 |
| Back Invalidation | BI消息正确处理 | 协议分析仪 |

## 测试流程
1. 链路训练与初始化
2. CXL能力协商
3. 协议事务测试
4. 错误处理验证
5. 性能基准测试

## 合规认证
- CXL Consortium CV测试套件
- PCIe SIG合规测试
- Integrators List准入测试
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## CXL协议测试设计

### 测试环境
- **硬件**: CXL协议分析仪、被测设备(DUT)、主机平台
- **软件**: CXL CV测试套件、PCIe SIG测试工具
- **拓扑**: 直连/Switch连接两种模式

### 测试步骤
1. 配置CXL链路参数
2. 执行CV测试套件
3. 分析协议trace
4. 验证错误处理
5. 生成合规报告

### 预期结果
- 所有CV测试项通过
- 协议trace无异常
- 符合CXL规范要求
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## CXL协议测试用例

| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|---------|
| CXL-001 | 链路训练 | DUT上电 | 1.复位链路 2.协商速率 | 链路up在最高速率 |
| CXL-002 | CXL.io事务 | 链路up | 发送CXL.io配置读写 | 配置正确完成 |
| CXL-003 | CXL.mem访问 | 内存初始化 | 读写HDM区域 | 数据一致 |
| CXL-004 | 错误注入 | 正常链路 | 注入CRC错误 | 正确检测并重传 |
| CXL-005 | 热复位 | 正常运行 | 触发热复位 | 正确恢复 |
| CXL-006 | IDE功能 | 支持IDE | 启用加密传输 | 数据加密正确 |
"""
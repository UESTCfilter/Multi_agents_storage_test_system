"""PCM Endurance Expert - PCM耐久性专家

专注于PCM耐久性测试和寿命预测
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class PCMEnduranceExpert(TestingExpertAgent):
    """PCM耐久性专家"""
    
    def __init__(self):
        super().__init__(
            name="PCM Endurance Expert",
            expertise="PCM耐久性测试",
            description="专注于PCM耐久性、磨损模型、寿命预测、数据保持"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# PCM耐久性测试策略

## 测试目标
验证PCM设备的耐久性和预测使用寿命

## PCM耐久性机制
- **编程/擦除循环**: 相变材料可重复相变次数
- **材料退化**: 反复加热导致材料迁移
- **电阻漂移**: 长时间保持后电阻变化
- **目标耐久**: 10^8次循环（企业级要求）

## 关键测试项

### 耐久性测试
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 循环耐久 | >10^8次 | 耐久测试平台 |
| 数据保持 | 10年@85°C | 高温加速 |
| 错误率 | RBER < 10^-6 | 错误统计 |

### 磨损模型
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 退化曲线 | 建立模型 | 数据分析 |
| 温度加速 | 阿伦尼乌斯模型 | 高温测试 |
| 寿命预测 | MTTF计算 | 模型预测 |

### 分布演化
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| RESET分布 | 跟踪变化 | 参数分析 |
| SET分布 | 跟踪变化 | 参数分析 |
| 窗口闭合 | 容限监控 | 统计分析 |

## 加速测试方法
```
温度加速因子:
AF = exp[(Ea/k) * (1/T_use - 1/T_stress)]

Ea: 激活能 (~1.5eV for PCM)
k: 玻尔兹曼常数
T_use: 使用温度 (e.g., 358K/85°C)
T_stress: 应力温度 (e.g., 398K/125°C)

示例: 125°C加速85°C约10-20倍
```
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## PCM耐久性测试设计

### 测试环境
- PCM测试芯片/设备
- 高低温箱（-40°C to 150°C）
- 耐久测试平台
- 参数分析仪

### 测试步骤
1. 初始参数测量
2. 高温加速耐久测试
3. 定期参数监测
4. 建立退化模型
5. 预测使用寿命
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## PCM耐久性测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| END-001 | 基础耐久 | 10^8次循环 | 功能正常 |
| END-002 | 高温耐久 | 125°C加速 | 等效10年通过 |
| END-003 | 分布监测 | 每10^6次测量 | 变化可接受 |
| END-004 | 窗口跟踪 | 跟踪读写窗口 | 不闭合 |
| END-005 | 保持验证 | 写后高温存储 | 数据正确 |
| END-006 | 寿命预测 | 模型外推 | MTTF>5年 |
"""
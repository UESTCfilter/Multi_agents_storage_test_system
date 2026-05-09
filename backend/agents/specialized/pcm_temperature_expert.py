"""PCM Temperature Expert - PCM温度专家

专注于PCM温度敏感性和温度管理
"""
from typing import Dict, Any
from backend.agents import TestingExpertAgent


class PCMTemperatureExpert(TestingExpertAgent):
    """PCM温度专家"""
    
    def __init__(self):
        super().__init__(
            name="PCM Temperature Expert",
            expertise="PCM温度特性测试",
            description="专注于PCM温度敏感性、高温保持、热串扰、温度管理"
        )
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        return """# PCM温度特性测试策略

## 测试目标
验证PCM设备在不同温度条件下的性能和可靠性

## PCM温度特性
- **高温敏感**: 保持时间随温度指数下降
- **相变温度**: SET~150°C, RESET~600°C
- **热串扰**: 邻近单元加热影响
- **工作范围**: 工业级-40°C~85°C，企业级0°C~70°C

## 关键测试项

### 温度特性
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 电阻温度系数 | 测量TC | 高低温测试 |
| SET/RESET温度 | 验证相变点 | 热分析 |
| 阈值电压温度 | 温度依赖性 | 参数测试 |

### 高温保持
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 数据保持 | 10年@85°C | 高温加速 |
| 保持时间温度 | 阿伦尼乌斯行为 | 多温点测试 |
| 激活能提取 | Ea~1.5eV | 数据分析 |

### 热串扰
| 测试项 | 判定标准 | 工具 |
|--------|---------|------|
| 邻近效应 | 无数据翻转 | 功能测试 |
| 散热设计 | 温升可控 | 热仿真 |
| 热管理 | 动态调节 | 系统测试 |

## 温度测试矩阵
```
温度点: -40°C, 0°C, 25°C, 55°C, 70°C, 85°C, 105°C, 125°C

每个温度点测试:
- 基础参数（电阻、阈值）
- 读写性能
- 数据保持（短期）
- 功能正确性
```

## 热串扰测试
```
测试模式:
[Target Cell] - [Heater Cell 1] - [Heater Cell 2]
     ↓              ↓                   ↓
  监测状态     反复写入加热       反复写入加热

验证目标单元状态是否受影响
```
"""

    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """## PCM温度测试设计

### 测试环境
- 高低温箱（-40°C to 150°C）
- PCM测试芯片
- 热仿真工具
- 红外热成像仪

### 测试步骤
1. 多温度点参数测试
2. 高温保持加速测试
3. 热串扰测试
4. 热循环测试
5. 热管理验证
"""

    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """## PCM温度测试用例

| 用例ID | 用例名称 | 测试步骤 | 预期结果 |
|--------|---------|---------|---------|
| TEMP-001 | 温度系数 | -40°C到125°C扫描 | 系数符合规格 |
| TEMP-002 | 高温保持 | 150°C加速保持 | 等效10年通过 |
| TEMP-003 | 热串扰 | 邻近单元加热 | 目标单元不受影响 |
| TEMP-004 | 热循环 | -40°C↔85°C循环 | 1000次无失效 |
| TEMP-005 | 工作范围 | 全温区功能测试 | 全范围正常 |
| TEMP-006 | 热管理 | 动态温度调节 | 温度可控 |
"""
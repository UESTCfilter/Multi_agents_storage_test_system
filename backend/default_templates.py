"""默认测试模板"""

DEFAULT_TEMPLATES = [
    # ============ 策略模板 ============
    {
        "template_key": "strategy_comprehensive",
        "template_type": "strategy",
        "scope": "global",
        "name": "综合测试策略模板",
        "description": "适用于SSD/CXL存储设备的综合测试策略",
        "is_default": True,
        "content": """# {{device_name}} 测试策略

## 1. 测试目标
{{test_objective}}

## 2. 测试范围
### 2.1 功能测试
- 基础读写功能验证
- 异常处理机制验证
- 边界条件测试

### 2.2 性能测试
- 吞吐量测试
- 延迟测试
- IOPS测试

### 2.3 可靠性测试
- 数据完整性验证
- 错误恢复测试
- 长时间稳定性测试

## 3. 测试重点
{{#focus_areas}}
- {{.}}
{{/focus_areas}}
{{^focus_areas}}
- 基于{{device_type}}特性的专项测试
- 目标市场({{target_market}})相关场景测试
{{/focus_areas}}

## 4. 测试资源
- 测试设备: {{device_name}}
- 测试环境: {{test_environment}}
- 测试周期: {{test_duration}}

## 5. 风险评估
| 风险项 | 等级 | 缓解措施 |
|--------|------|----------|
| 硬件兼容性 | 中 | 多平台验证 |
| 测试覆盖度 | 低 | 多智能体协作 |
""",
        "structure": {
            "sections": ["objective", "scope", "focus", "resources", "risk"],
            "required_vars": ["device_name", "device_type"]
        },
        "tags": ["strategy", "ssd", "cxl", "comprehensive"]
    },
    {
        "template_key": "strategy_cxl_pcm",
        "template_type": "strategy",
        "scope": "global",
        "name": "CXL PCM测试策略模板",
        "description": "专门针对CXL PCM存储设备的测试策略",
        "is_default": False,
        "content": """# CXL PCM 测试策略

## 1. 设备概述
- 设备类型: CXL Type 3 Memory Device
- 存储介质: PCM (Phase Change Memory)
- 应用场景: {{target_market}}

## 2. CXL特定测试项
### 2.1 CXL.io 协议测试
- PCIe 5.0兼容性
- CXL.io事务层验证

### 2.2 CXL.mem 协议测试
- 内存池化功能
- 内存扩展功能
- 一致性功能

### 2.3 PCM 特性测试
- 写入耐久性
- 数据保持特性
- 温度敏感性

## 3. 测试策略
{{requirements}}

## 4. 关键指标
- 延迟: < 100ns (加载)
- 带宽: > 10GB/s
- 耐久性: > 10^8 次写入
""",
        "structure": {
            "sections": ["overview", "cxl_specific", "strategy", "metrics"],
            "required_vars": ["device_name", "target_market"]
        },
        "tags": ["strategy", "cxl", "pcm"]
    },
    
    # ============ 设计模板 ============
    {
        "template_key": "design_module_cxl",
        "template_type": "design",
        "scope": "global",
        "name": "CXL模块测试设计模板",
        "description": "CXL存储模块的详细测试设计",
        "is_default": True,
        "content": """# {{module_name}} 测试设计

## 1. 测试设计概述
基于策略文档，设计{{module_name}}的详细测试方案。

## 2. 测试策略回顾
{{strategy_summary}}

## 3. 测试模块设计

### 3.1 接口测试模块
```
测试项: CXL Link Initialization
- 输入: 设备上电序列
- 预期输出: 链路正常建立
- 判定标准: 链路状态寄存器 = 0x1
```

### 3.2 功能测试模块
```
测试项: 内存读写
- 输入: 地址=0x1000, 数据=0xAABBCCDD
- 预期输出: 读取数据=0xAABBCCDD
- 判定标准: 数据一致
```

### 3.3 性能测试模块
```
测试项: 顺序读写带宽
- 输入: 4MB数据块, 队列深度=32
- 预期输出: 带宽>10GB/s
- 判定标准: 实际带宽≥目标值
```

### 3.4 异常测试模块
```
测试项: 链路断开恢复
- 输入: 模拟链路故障
- 预期输出: 设备自动恢复
- 判定标准: 恢复时间<5s
```

## 4. 测试用例框架
| 用例ID | 测试项 | 优先级 | 预置条件 | 测试步骤 | 预期结果 |
|--------|--------|--------|----------|----------|----------|
| TC001 | 链路初始化 | P0 | 设备上电 | 1.上电 2.等待 | 链路就绪 |
| TC002 | 内存读写 | P0 | 链路就绪 | 1.写数据 2.读数据 | 数据一致 |
| TC003 | 带宽测试 | P1 | 链路就绪 | 1.发送数据 | 带宽达标 |

## 5. 测试环境需求
- 测试主机: {{test_host}}
- CXL交换机: {{cxl_switch}}
- 测试软件: {{test_software}}

## 6. 通过准则
{{#pass_criteria}}
- {{.}}
{{/pass_criteria}}
{{^pass_criteria}}
- 所有P0用例100%通过
- 所有P1用例≥95%通过
- 无阻塞性缺陷
{{/pass_criteria}}
""",
        "structure": {
            "sections": ["overview", "interface", "function", "performance", "exception"],
            "required_vars": ["module_name", "strategy_summary"]
        },
        "tags": ["design", "cxl", "module"]
    },
    {
        "template_key": "design_comprehensive",
        "template_type": "design",
        "scope": "global",
        "name": "综合测试设计模板",
        "description": "适用于各种存储设备的综合测试设计",
        "is_default": False,
        "content": """# {{device_name}} 综合测试设计

## 1. 测试设计目标
{{design_objective}}

## 2. 测试策略输入
{{strategy}}

## 3. 功能测试设计
### 3.1 基础功能
- 读写功能验证
- 容量验证
- 格式化验证

### 3.2 高级功能
- 加密功能 (如适用)
- 压缩功能 (如适用)
- 缓存功能 (如适用)

## 4. 性能测试设计
### 4.1 基准测试
- 顺序读/写
- 随机读/写
- 混合负载

### 4.2 场景测试
- 数据库场景
- 文件服务器场景
- 流媒体场景

## 5. 可靠性测试设计
### 5.1 数据完整性
- 掉电保护
- 数据校验
- 错误注入

### 5.2 稳定性
- 长时间运行
- 温度循环
- 电源波动

## 6. 兼容性测试设计
- 操作系统兼容
- 平台兼容
- 软件兼容
""",
        "structure": {
            "sections": ["objective", "function", "performance", "reliability", "compatibility"],
            "required_vars": ["device_name", "strategy"]
        },
        "tags": ["design", "comprehensive", "ssd"]
    },
    
    # ============ 用例模板 ============
    {
        "template_key": "case_detailed_storage",
        "template_type": "case",
        "scope": "global",
        "name": "详细存储测试用例模板",
        "description": "详细的可执行测试用例模板",
        "is_default": True,
        "content": """# {{device_name}} 测试用例集

## 用例信息
- 项目: {{project_name}}
- 版本: v{{version}}
- 生成时间: {{generated_at}}

{{#test_cases}}
---

## 用例 {{id}}: {{title}}

### 基本信息
| 属性 | 值 |
|------|-----|
| 用例ID | TC-{{id}} |
| 优先级 | {{priority}} |
| 测试类型 | {{test_type}} |
| 相关模块 | {{module}} |

### 测试目的
{{purpose}}

### 预置条件
{{#preconditions}}
{{n}}. {{.}}
{{/preconditions}}

### 测试步骤
| 步骤 | 操作 | 预期结果 |
|------|------|----------|
{{#steps}}
| {{number}} | {{action}} | {{expected}} |
{{/steps}}

### 测试数据
{{#test_data}}
- {{name}}: {{value}}
{{/test_data}}

### 通过准则
{{pass_criteria}}

### 相关需求
{{related_requirements}}

{{/test_cases}}

---

## 测试执行统计
| 优先级 | 用例数 | 占比 |
|--------|--------|------|
| P0 | {{p0_count}} | {{p0_percent}}% |
| P1 | {{p1_count}} | {{p1_percent}}% |
| P2 | {{p2_count}} | {{p2_percent}}% |
| **总计** | **{{total_count}}** | **100%** |
""",
        "structure": {
            "sections": ["info", "cases", "statistics"],
            "required_vars": ["device_name", "project_name", "test_cases"]
        },
        "tags": ["case", "detailed", "executable"]
    },
    {
        "template_key": "case_cxl_pcm_detailed",
        "template_type": "case",
        "scope": "global",
        "name": "CXL PCM详细测试用例模板",
        "description": "专门针对CXL PCM设备的详细测试用例",
        "is_default": False,
        "content": """# CXL PCM 详细测试用例

## 1. CXL协议测试用例

### TC-CXL-001: CXL Link Training
**优先级**: P0
**目的**: 验证CXL链路训练过程

**步骤**:
1. 设备上电
2. 监测链路训练状态
3. 确认链路宽度协商
4. 确认速率协商

**预期结果**:
- 链路训练完成状态=1
- 协商宽度={{expected_width}}
- 协商速率={{expected_speed}}

### TC-CXL-002: CXL.mem Memory Pooling
**优先级**: P0
**目的**: 验证内存池化功能

**步骤**:
1. 配置内存池
2. 分配内存
3. 执行读写
4. 释放内存

**预期结果**:
- 内存分配成功
- 读写数据一致
- 释放无内存泄漏

## 2. PCM特性测试用例

### TC-PCM-001: Write Endurance
**优先级**: P1
**目的**: 验证PCM写入耐久性

**步骤**:
1. 选择测试单元
2. 执行循环写入
3. 记录错误率
4. 达到目标次数

**预期结果**:
- 错误率<{{max_error_rate}}
- 达到{{endurance_target}}次写入

### TC-PCM-002: Data Retention
**优先级**: P1
**目的**: 验证数据保持特性

**步骤**:
1. 写入测试数据
2. 高温老化{{retention_hours}}小时
3. 读取数据
4. 比较数据一致性

**预期结果**:
- 数据一致率>99.99%

## 3. 性能测试用例

### TC-PERF-001: Sequential Read Bandwidth
**优先级**: P0
**目的**: 验证顺序读带宽

**配置**:
- 块大小: 128KB
- 队列深度: 32
- 线程数: 8

**通过准则**: 带宽≥{{target_read_bw}} GB/s

### TC-PERF-002: Random Read Latency
**优先级**: P0
**目的**: 验证随机读延迟

**配置**:
- 块大小: 4KB
- 队列深度: 1
- 测试时间: 60s

**通过准则**: P99延迟≤{{target_latency_us}} μs
""",
        "structure": {
            "sections": ["cxl_protocol", "pcm_feature", "performance"],
            "required_vars": ["device_name", "expected_width", "expected_speed"]
        },
        "tags": ["case", "cxl", "pcm"]
    }
]
"""SSD/存储测试行业专家补充方案

基于行业最佳实践，建议在当前17个专家基础上补充以下专家：

## SSD/NAND 领域补充

### 物理介质层（当前有基础，需细化）
- ✅ NAND Stack Expert（已有）
- ❌ **建议新增**: **ReadRetry Expert** - 读参考电压优化、Vopt自适应学习
- ❌ **建议新增**: **WearLeveling Expert** - 页面级磨损均衡（PGWL）策略

### 控制器与固件层（当前有 Firmware Expert）
- ❌ **建议新增**: **FTL Expert** - 闪存转换层、垃圾回收、写放大优化
- ❌ **建议新增**: **PLP Expert** - 掉电保护机制（钽电容、数据一致性）
- ❌ **建议新增**: **TemperatureStress Expert** - 跨温度范围性能验证

### 系统协议层（当前有 Protocol Expert）
- ❌ **建议新增**: **NVMe Expert** - NVMe队列管理、SQ/CQ机制、Admin/IO命令
- ❌ **建议新增**: **QoS Expert** - 尾延迟优化（P99/P999）、延迟分布分析
- ❌ **建议新增**: **SATA_SAS Expert** - 传统接口兼容性（AHCI、NCQ）

### 场景化测试（当前较缺）
- ❌ **建议新增**: **Workload Expert** - 企业工作负载模拟（OLTP/OLAP/SNIA PTS）
- ❌ **建议新增**: **AI_Storage Expert** - 大模型存储性能（高并发读、检查点）
- ❌ **建议新增**: **DataIntegrity Expert**（已有，可扩展）- T10 DIF/DIX、CRC

### 质量与合规（当前较缺）
- ❌ **建议新增**: **Compliance Expert** - SNIA、PCI-SIG、TCG认证测试
- ❌ **建议新增**: **ML_Prediction Expert** - 基于机器学习的故障模式预测


## CXL 内存领域补充（当前只有基础 CXL Expert）

### CXL 协议与物理层
- ❌ **建议新增**: **CXL_Protocol Expert** - CXL 1.1/2.0/3.0协议合规、CV测试
- ❌ **建议新增**: **PCIe_Signal Expert** - 8/16/32 GT/s信号完整性、眼图、BER
- ❌ **建议新增**: **CXL_Switch Expert** - CXL Switch多主机连接、内存池化

### CXL 内存设备（Type 2/3）
- ❌ **建议新增**: **Type2_Device Expert** - 带缓存的CXL设备（HDM-DB、BI）
- ❌ **建议新增**: **Type3_Device Expert** - 纯内存扩展设备、NUMA节点管理
- ❌ **建议新增**: **DDR5_Backend Expert** - CXL设备后端DDR5性能验证

### 内存性能与拓扑
- ❌ **建议新增**: **NUMA_Topology Expert** - 内存-only NUMA节点、延迟分级
- ❌ **建议新增**: **Duplex_Performance Expert** - CXL读写双工优化
- ❌ **建议新增**: **Bandwidth_Expansion Expert** - 多CXL设备聚合带宽（210M IOPS目标）

### 系统应用层
- ❌ **建议新增**: **Memory_Tiering Expert** - 内存分层策略（热页识别、页面迁移）
- ❌ **建议新增**: **LLM_Workload Expert** - 大模型推理/训练（KV Cache卸载、Embedding缓存）
- ❌ **建议新增**: **Heterogeneous_Computing Expert** - CPU/GPU/加速器共享CXL

### 质量与自动化
- ❌ **建议新增**: **RAS Expert** - 可靠性、可用性、可服务性（故障注入、热插拔）
- ❌ **建议新增**: **CXL_Interop Expert** - 跨厂商兼容性验证（多主机、多OS）


## 建议优先级

### 高优先级（SSD核心能力）
1. **FTL Expert** - 闪存核心
2. **NVMe Expert** - 协议核心
3. **QoS Expert** - 企业级必需
4. **Workload Expert** - 场景化测试

### 高优先级（CXL核心能力）
5. **CXL_Protocol Expert** - 协议合规
6. **Type3_Device Expert** - 内存扩展
7. **NUMA_Topology Expert** - 系统拓扑
8. **Memory_Tiering Expert** - 分层策略

### 中优先级（增强能力）
9. **PLP Expert** - 可靠性
10. **Compliance Expert** - 认证
11. **AI_Storage/LLM_Workload Expert** - AI场景
12. **RAS Expert** - 故障处理

### 低优先级（专项能力）
13. 其他细分领域专家（ReadRetry、WearLeveling、CXL_Switch等）


## 实施建议

当前17个专家 → 建议扩展至 **25-30个专家**

保留现有：
- NAND Stack、Data Integrity、Firmware
- Protocol、CXL（基础）
- Performance、Reliability、Stability、Security
- DFX、Physical Layer、Thermal、Power

新增重点：
- SSD: FTL、NVMe、QoS、Workload
- CXL: CXL_Protocol、Type3、NUMA、Memory_Tiering
- 通用: Compliance、RAS、AI场景

"""

# 如果要快速实施，建议先实现以下8个核心专家：
PRIORITY_EXPERTS = [
    ("FTL Expert", "闪存转换层专家", ["FTL", "地址映射", "垃圾回收", "写放大"]),
    ("NVMe Expert", "NVMe协议专家", ["NVMe", "队列管理", "SQ/CQ", "命令集"]),
    ("QoS Expert", "服务质量专家", ["QoS", "尾延迟", "P99", "延迟分布"]),
    ("Workload Expert", "工作负载专家", ["工作负载", "OLTP", "OLAP", "SNIA PTS"]),
    ("CXL_Protocol Expert", "CXL协议专家", ["CXL", "协议合规", "CV测试", "PCIe"]),
    ("Type3_Device Expert", "CXL Type3专家", ["Type3", "内存扩展", "NUMA", "内存池化"]),
    ("NUMA_Topology Expert", "NUMA拓扑专家", ["NUMA", "拓扑", "延迟分级", "Local/Remote"]),
    ("Memory_Tiering Expert", "内存分层专家", ["内存分层", "热页识别", "页面迁移", "Tiering"]),
]
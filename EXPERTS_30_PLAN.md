# 专家集群规划 - 企业级CXL协议 + PCM存储

## 现有17个专家
1. NAND Stack Expert
2. Data Integrity Expert
3. Firmware Testing Expert
4. Protocol Expert
5. CXL Expert (基础)
6. Performance Expert
7. Reliability Expert
8. Stability Expert
9. Security Expert
10. DFX Testing Expert
11. Physical Layer Expert
12. Thermal Expert
13. Power Expert
14. Compatibility Expert
15. Stress Testing Expert
16. Regression Testing Expert
17. Automation Expert

## 新增13个专家（达到30个）

### CXL企业级协议专家（6个）
18. **CXL_Protocol Expert** - CXL 1.1/2.0/3.0协议合规、CV测试、Integrators List
19. **CXL_Switch Expert** - CXL交换机、多主机连接、fan-out拓扑、内存池化
20. **Type2_Device Expert** - CXL Type2设备（带缓存）、HDM-DB、Back Invalidation
21. **Type3_Device Expert** - CXL Type3设备（纯内存）、内存扩展、NUMA节点
22. **CXL_Coherency Expert** - 缓存一致性协议、Snoop过滤器、一致性域管理
23. **CXL_RAS Expert** - 可靠性可用性可服务性、错误注入、热插拔、故障恢复

### PCM存储专家（3个）
24. **PCM_Media Expert** - PCM介质物理特性、相变机制、读写原理
25. **PCM_Endurance Expert** - PCM耐久性测试、磨损模型、寿命预测
26. **PCM_Temperature Expert** - PCM温度敏感性、高温保持、热串扰

### 通用存储核心专家（4个）
27. **FTL Expert** - 闪存转换层、地址映射、垃圾回收、写放大优化
28. **NVMe Expert** - NVMe协议、队列管理、SQ/CQ、Admin/IO命令
29. **QoS Expert** - 服务质量、尾延迟P99/P999、延迟分级、SLA保障
30. **Workload Expert** - 工作负载模拟、OLTP/OLAP、SNIA PTS、AI训练负载

## 专家分类矩阵

| 层级 | 专家数量 | 覆盖范围 |
|------|---------|---------|
| 物理介质层 | 4 | NAND, PCM介质, 信号完整性 |
| 控制器层 | 3 | FTL, Firmware, NVMe |
| CXL协议层 | 7 | CXL基础, 协议, Switch, Type2/3, 一致性, RAS |
| 系统层 | 6 | NUMA, 内存分层, QoS, Data Integrity, Reliability |
| 应用层 | 6 | Workload, Performance, Security, DFX, 兼容性, 自动化 |
| 质量保障层 | 4 | Stress, Stability, Regression, 质量门 |

## 智能调度策略

### 路由规则
```
IF device_type == "CXL":
    必选: CXL_Protocol, Type3_Device
    条件触发:
        - 多主机/Switch → +CXL_Switch
        - 缓存一致性需求 → +CXL_Coherency, +Type2_Device
        - 高可靠性需求 → +CXL_RAS
        - NUMA架构 → +NUMA_Topology
        
IF device_type == "PCM":
    必选: PCM_Media, PCM_Endurance
    条件触发:
        - 宽温应用 → +PCM_Temperature
        - 企业级 → +QoS, +Reliability
        
IF device_type == "SSD":
    必选: NAND Stack, FTL, NVMe
    条件触发:
        - 高性能需求 → +QoS, +Performance
        - 企业级 → +Workload, +Data Integrity
```

### 协作模式
1. **主-从模式**: 领域主专家制定框架，其他专家填充章节
2. **并行模式**: 无依赖的专家并行执行
3. **流水线模式**: 物理层→控制器→协议→系统→应用层顺序执行

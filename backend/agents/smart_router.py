"""智能路由 V2 - 30专家集群

基于需求动态选择Agent，支持企业级CXL协议和PCM存储
"""
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import re


@dataclass
class AgentMatch:
    """Agent 匹配结果"""
    agent_name: str
    relevance_score: float
    reason: str


class SmartRouter:
    """智能路由 - 根据需求选择相关 Agent"""
    
    def __init__(self, agent_registry: Dict[str, Any]):
        self.agent_registry = agent_registry
        
        # 30个专家的专长关键词映射
        self.agent_keywords = {
            # ========== 物理介质层 (4个) ==========
            "NAND Stack Expert": [
                "nand", "闪存", "flash", "ftl", "磨损均衡", "坏块", "ecc", "纠错",
                "page", "block", "erase", "program", "read", "tlc", "qlc", "slc"
            ],
            "Physical Layer Expert": [
                "物理层", "信号", "眼图", "误码率", "ber", "信号完整性", "si",
                "pcie", "电气", "链路", "training", "均衡"
            ],
            "PCM Media Expert": [
                "pcm", "相变", "phase change", "gst", "ge-sb-te", "reset", "set",
                "amorphous", "crystalline", "阈值电压", "vth"
            ],
            "PCM Endurance Expert": [
                "pcm耐久", "耐久性", "endurance", "循环", "cycle", "保持", "retention",
                "寿命", "lifetime", "退化", "degradation"
            ],
            
            # ========== 控制器层 (3个) ==========
            "Firmware Testing Expert": [
                "固件", "firmware", "fw", "升级", "刷机", "bootloader", "fw update"
            ],
            "FTL Expert": [
                "ftl", "闪存转换层", "地址映射", "mapping", "垃圾回收", "gc",
                "写放大", "write amplification", "wear leveling", "wl"
            ],
            
            # ========== 协议层 (7个) ==========
            "Protocol Expert": [
                "pcie", "nvme", "协议", "链路", "transaction", "tlp", "dllp",
                "mps", "mrrs", "aspm", "l0s", "l1"
            ],
            "NVMe Expert": [
                "nvme", "命名空间", "namespace", "队列", "sq", "cq", "admin",
                "io", "命令", "command", "prp", "sgl", "msi-x"
            ],
            "CXL Expert": [
                "cxl", "cache", "memory", "内存扩展", "一致性", "cxl.io", "cxl.mem", "cxl.cache"
            ],
            "CXL Protocol Expert": [
                "cxl协议", "协议合规", "cv测试", "compliance", "integrators list",
                "flit", "68b", "256b", "ide"
            ],
            "CXL Switch Expert": [
                "cxl switch", "交换机", "多主机", "multi-host", "内存池化", "pooling",
                "fan-out", "fabric"
            ],
            "Type2 Device Expert": [
                "type2", "cxl type 2", "设备缓存", "device cache", "hdm-db",
                "back invalidation", "bi"
            ],
            "Type3 Device Expert": [
                "type3", "cxl type 3", "内存扩展", "memory expansion", "容量扩展"
            ],
            
            # ========== 系统层 (6个) ==========
            "Data Integrity Expert": [
                "数据完整性", "数据一致性", "断电保护", "plp", "掉电", "corruption",
                "end-to-end", "e2e", "crc", "checksum"
            ],
            "CXL Coherency Expert": [
                "缓存一致性", "cache coherency", "snoop", "监听", "moesi", "mesi",
                "一致性域", "coherency domain", "bias"
            ],
            "CXL RAS Expert": [
                "ras", "可靠性", "可用性", "可服务性", "故障注入", "热插拔",
                "hot plug", "错误恢复", "error recovery"
            ],
            "Thermal Expert": [
                "温度", "thermal", "散热", "过热", "throttle", "功耗温度", "temp"
            ],
            "PCM Temperature Expert": [
                "pcm温度", "温度敏感", "thermal sensitivity", "高温保持", "热串扰",
                "thermal crosstalk", "激活能", "activation energy"
            ],
            "Power Expert": [
                "电源", "功耗", "power", "电压", "电流", "节能", "power state",
                "aspm", "l1ss"
            ],
            
            # ========== 质量属性 (4个) ==========
            "Performance Expert": [
                "性能", "吞吐", "带宽", "iops", "延迟", "latency", "throughput",
                "benchmark", "tpm", "gbps"
            ],
            "QoS Expert": [
                "qos", "服务质量", "尾延迟", "tail latency", "p99", "p999", "p9999",
                "sla", "分级", "latency tier"
            ],
            "Reliability Expert": [
                "可靠性", "寿命", "耐久", "寿命预测", "rber", "uberk", "mtbf", "mttd"
            ],
            "Stability Expert": [
                "稳定性", "长时间", "老化", "高温", "压力测试", "stress", "稳定性"
            ],
            
            # ========== 安全与DFX (3个) ==========
            "Security Expert": [
                "安全", "加密", "安全启动", "secure boot", "aes", "hash", "签名",
                "ide", "完整性", "数据加密"
            ],
            "DFX Testing Expert": [
                "dfx", "可制造", "可测试", "可维护", "诊断", "debug", "scan", "bist"
            ],
            "Stress Testing Expert": [
                "压力测试", "压力", "满负荷", "边界", "极限", "burn-in", "烤机"
            ],
            
            # ========== 应用层 (3个) ==========
            "Workload Expert": [
                "工作负载", "workload", "oltp", "olap", "snia pts", "pts", "vdi", "vsi",
                "数据库", "虚拟化"
            ],
            "Compatibility Expert": [
                "兼容性", "兼容", "interoperability", "互操作性", "生态", "interop"
            ],
            "Regression Testing Expert": [
                "回归", "regression", "版本", "迭代", "基线", "baseline"
            ],
            
            # ========== 自动化 (1个) ==========
            "Automation Expert": [
                "自动化", "auto", "脚本", "framework", "ci/cd", "jenkins", "gitlab"
            ],
        }
        
        # 设备类型默认 Agent 配置
        self.device_defaults = {
            "SSD": [
                "NAND Stack Expert", "FTL Expert", "NVMe Expert",
                "Protocol Expert", "Performance Expert", "Data Integrity Expert"
            ],
            "CXL": [
                "CXL Protocol Expert", "Type3 Device Expert", "CXL Expert",
                "Protocol Expert", "Performance Expert", "Data Integrity Expert",
                "CXL RAS Expert", "QoS Expert"
            ],
            "PCM": [
                "PCM Media Expert", "PCM Endurance Expert", "PCM Temperature Expert",
                "Reliability Expert", "Data Integrity Expert", "QoS Expert"
            ],
            "CXL_PCM": [
                "CXL Protocol Expert", "Type3 Device Expert", "PCM Media Expert",
                "PCM Endurance Expert", "CXL RAS Expert", "QoS Expert"
            ]
        }
    
    def select_agents(self, context: Dict[str, Any], max_agents: int = 8) -> List[AgentMatch]:
        """智能选择相关 Agent"""
        device_type = context.get("device_type", "SSD")
        requirements = context.get("requirements", "")
        test_objective = context.get("test_objective", "")
        
        # 合并所有文本用于关键词匹配
        query_text = f"{requirements} {test_objective}".lower()
        
        # 计算每个 Agent 的相关度
        matches = []
        
        for agent_name, keywords in self.agent_keywords.items():
            if agent_name not in self.agent_registry:
                continue
            
            score, matched_keywords = self._calculate_relevance(query_text, keywords)
            
            if score > 0.1:  # 降低阈值，提高覆盖率
                reason = f"匹配: {', '.join(matched_keywords[:3])}"
                matches.append(AgentMatch(
                    agent_name=agent_name,
                    relevance_score=score,
                    reason=reason
                ))
        
        # 按相关度排序
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # 如果需求匹配不足，补充设备类型默认 Agent
        if len(matches) < 4:
            defaults = self.device_defaults.get(device_type, self.device_defaults["SSD"])
            existing_names = {m.agent_name for m in matches}
            
            for default_agent in defaults:
                if default_agent not in existing_names and default_agent in self.agent_registry:
                    matches.append(AgentMatch(
                        agent_name=default_agent,
                        relevance_score=0.3,
                        reason=f"{device_type}默认"
                    ))
        
        # 返回 Top N，确保多样性（各领域至少一个）
        selected = matches[:max_agents]
        
        return selected
    
    def _calculate_relevance(self, query: str, keywords: List[str]) -> Tuple[float, List[str]]:
        """计算相关度分数"""
        matched = []
        for kw in keywords:
            if kw.lower() in query:
                matched.append(kw)
        
        if not matched:
            return 0.0, []
        
        # 基础分
        base_score = 0.2
        
        # 匹配词加分（考虑同义词）
        match_bonus = min(len(matched) * 0.15, 0.5)
        
        # 精确匹配加分
        exact_matches = sum(1 for m in matched if f" {m} " in f" {query} " or query.startswith(m) or query.endswith(m))
        exact_bonus = exact_matches * 0.1
        
        # 关键词长度加权（长词更具体）
        length_bonus = sum(len(m) * 0.01 for m in matched[:3])
        
        score = min(base_score + match_bonus + exact_bonus + length_bonus, 1.0)
        return score, matched
    
    def get_agent_selection_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成 Agent 选择报告"""
        matches = self.select_agents(context)
        
        # 按层级分组
        layer_groups = {
            "物理介质层": [],
            "协议层": [],
            "系统层": [],
            "质量属性": [],
            "应用层": []
        }
        
        layer_keywords = {
            "物理介质层": ["NAND", "PCM", "Physical"],
            "协议层": ["Protocol", "NVMe", "CXL"],
            "系统层": ["Data Integrity", "Coherency", "RAS", "Thermal", "Power"],
            "质量属性": ["Performance", "QoS", "Reliability", "Stability"],
            "应用层": ["Workload", "Security", "Compatibility"]
        }
        
        for m in matches:
            assigned = False
            for layer, keywords in layer_keywords.items():
                if any(kw in m.agent_name for kw in keywords):
                    layer_groups[layer].append({
                        "name": m.agent_name,
                        "relevance": f"{m.relevance_score:.2f}",
                        "reason": m.reason
                    })
                    assigned = True
                    break
            if not assigned:
                layer_groups["应用层"].append({
                    "name": m.agent_name,
                    "relevance": f"{m.relevance_score:.2f}",
                    "reason": m.reason
                })
        
        return {
            "device_type": context.get("device_type"),
            "query": f"{context.get('requirements', '')} {context.get('test_objective', '')}"[:200],
            "selected_agents_by_layer": {k: v for k, v in layer_groups.items() if v},
            "total_available": len(self.agent_registry),
            "total_selected": len(matches)
        }
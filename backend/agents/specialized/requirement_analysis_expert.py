"""Requirement Analysis Expert - 需求分析专家

作为系统入口，负责解析用户需求文档，提取关键测试信息
"""
from typing import Dict, Any, List
from backend.agents import TestingExpertAgent
import re


class RequirementAnalysisExpert(TestingExpertAgent):
    """需求分析专家 - 系统入口Agent"""
    
    def __init__(self):
        super().__init__(
            name="Requirement Analysis Expert",
            expertise="需求文档分析",
            description="解析用户需求文档，自动识别设备类型、测试目标、关键技术指标"
        )
        
        # 设备类型识别关键词
        self.device_patterns = {
            "SSD": ["ssd", "固态硬盘", "solid state", "nand", "闪存", "sata", "sas", "nvme ssd"],
            "CXL": ["cxl", "compute express link", "内存扩展", "memory expansion", "type3", "type 3"],
            "CXL_Switch": ["cxl switch", "交换机", "内存池化", "memory pooling", "多主机", "multi-host"],
            "CXL_Type2": ["type2", "type 2", "设备缓存", "device cache", "hdm-db"],
            "PCM": ["pcm", "相变存储", "phase change", "gst", "3d xpoint", "optane", "持久内存"],
            "ZNS": ["zns", "zoned namespace", "分区命名空间", "smr", "叠瓦"],
            "KV": ["kv", "key-value", "键值存储", "kv store"],
        }
        
        # 测试目标识别
        self.objective_patterns = {
            "compliance": ["合规", "认证", "compliance", "cv test", "integrators list", "pcie sig"],
            "performance": ["性能", "带宽", "iops", "延迟", "throughput", "bandwidth", "latency"],
            "reliability": ["可靠性", "寿命", "耐久", "endurance", "lifetime", "rber", "uberk"],
            "function": ["功能", "特性", "function", "feature", "验证"],
            "interop": ["兼容性", "互操作", "interop", "compatibility", "认证"],
        }
        
        # 关键指标提取模式
        self.metric_patterns = {
            "capacity": r'(\d+)\s*(TB|GB|PB)',
            "iops": r'(\d+)\s*[Kk]?\s*IOPS',
            "bandwidth": r'(\d+)\s*(GB/s|Gbps)',
            "latency": r'(\d+)\s*(μs|us|ns|ms)',
            "temperature": r'(-?\d+)\s*°?C',
            "cycles": r'(10\^\d+|\d+e\d+)\s*次?',
        }
    
    def _build_strategy_prompt(self, context: Dict[str, Any]) -> list:
        """构建需求分析Prompt"""
        requirements = context.get("requirements", "")
        test_objective = context.get("test_objective", "")
        
        system_msg = """你是需求分析专家，专注于解析存储测试需求文档。
你的任务是自动识别设备类型、测试目标、关键指标，无需用户指定设备类型。

输出要求：
1. 使用 Markdown 格式
2. 明确给出识别的设备类型（SSD/CXL/PCM等）
3. 列出匹配的置信度和关键词
4. 提取所有技术指标（容量、性能、温度等）
5. 你的输出必须直接以 Markdown 标题（# 或 ##）开头，不要有任何前言、背景说明、自我对话、计划、分析过程或思考过程。"""

        user_msg = f"""请分析以下测试需求：

## 原始需求
{requirements}

## 测试目标
{test_objective}

请生成需求分析报告，包含：
### 识别的设备类型
- 设备类型: [SSD/CXL/PCM等]
- 置信度: [高/中/低]
- 匹配关键词: [列出关键词]

### 测试目标
- 主要目标: [功能/性能/可靠性/合规等]
- 次要目标: [其他目标]

### 关键技术指标
- [指标名]: [数值]

### 特殊需求
- [是否有企业级要求、安全需求、RAS需求等]

### 推荐的测试重点
1. [重点1]
2. [重点2]

### 建议调用的专家
- [专家1]
- [专家2]"""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    
    async def generate_strategy(self, context: Dict[str, Any]) -> str:
        """生成需求分析报告（作为策略的一部分）"""
        requirements = context.get("requirements", "")
        test_objective = context.get("test_objective", "")
        
        analysis = self._analyze_requirements(requirements + " " + test_objective)
        
        return f"""# 需求分析报告

## 原始需求
{requirements[:500]}{"..." if len(requirements) > 500 else ""}

## 自动识别结果

### 设备类型
- **识别结果**: {analysis['device_type']}
- **置信度**: {analysis['confidence']}
- **匹配关键词**: {', '.join(analysis['matched_keywords'])}

### 测试目标
- **主要目标**: {analysis['primary_objective']}
- **次要目标**: {', '.join(analysis['secondary_objectives']) if analysis['secondary_objectives'] else '无'}

### 关键技术指标
{self._format_metrics(analysis['metrics'])}

### 特殊需求
{self._format_special_requirements(analysis)}

## 推荐的测试重点
{self._generate_recommendations(analysis)}

## 建议调用的专家
{self._recommend_experts(analysis)}
"""
    
    async def generate_design(self, context: Dict[str, Any]) -> str:
        return """需求分析阶段已完成，无需设计文档。"""
    
    async def generate_cases(self, context: Dict[str, Any]) -> str:
        return """需求分析阶段已完成，无需测试用例。"""
    
    def _analyze_requirements(self, text: str) -> Dict[str, Any]:
        """分析需求文本，提取关键信息"""
        text_lower = text.lower()
        
        # 1. 识别设备类型
        device_scores = {}
        for device_type, keywords in self.device_patterns.items():
            score = sum(2 if kw in text_lower else 0 for kw in keywords)
            if score > 0:
                device_scores[device_type] = score
        
        # 选择得分最高的设备类型
        if device_scores:
            detected_device = max(device_scores, key=device_scores.get)
            confidence = "高" if device_scores[detected_device] >= 4 else "中"
            matched_keywords = [kw for kw in self.device_patterns[detected_device] 
                              if kw in text_lower][:5]
        else:
            detected_device = "SSD"  # 默认
            confidence = "低（默认）"
            matched_keywords = []
        
        # 2. 识别测试目标
        objective_scores = {}
        for obj_type, keywords in self.objective_patterns.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                objective_scores[obj_type] = score
        
        sorted_objectives = sorted(objective_scores.items(), key=lambda x: x[1], reverse=True)
        primary_objective = sorted_objectives[0][0] if sorted_objectives else "function"
        secondary_objectives = [obj for obj, _ in sorted_objectives[1:3]]
        
        # 3. 提取技术指标
        metrics = {}
        for metric_name, pattern in self.metric_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                metrics[metric_name] = matches[:3]  # 最多取3个
        
        # 4. 特殊需求检测
        special = {
            "needs_security": any(kw in text_lower for kw in ["安全", "加密", "secure", "ide", "加密"]),
            "needs_ras": any(kw in text_lower for kw in ["可靠性", "可用性", "ras", "热插拔", "故障"]),
            "needs_qos": any(kw in text_lower for kw in ["qos", "sla", "p99", "尾延迟", "服务质量"]),
            "needs_power": any(kw in text_lower for kw in ["功耗", "电源", "power", "节能", "thermal"]),
            "enterprise_grade": any(kw in text_lower for kw in ["企业级", "enterprise", "数据中心", "dc"]),
        }
        
        return {
            "device_type": detected_device,
            "confidence": confidence,
            "matched_keywords": matched_keywords,
            "primary_objective": primary_objective,
            "secondary_objectives": secondary_objectives,
            "metrics": metrics,
            "special_requirements": special,
            "raw_analysis": {
                "device_scores": device_scores,
                "objective_scores": dict(sorted_objectives)
            }
        }
    
    def _format_metrics(self, metrics: Dict) -> str:
        """格式化指标输出"""
        if not metrics:
            return "- 未检测到明确指标"
        
        lines = []
        metric_names = {
            "capacity": "存储容量",
            "iops": "IOPS性能",
            "bandwidth": "带宽",
            "latency": "延迟",
            "temperature": "温度范围",
            "cycles": "耐久次数"
        }
        
        for key, values in metrics.items():
            name = metric_names.get(key, key)
            lines.append(f"- **{name}**: {', '.join(str(v) for v in values)}")
        
        return '\n'.join(lines)
    
    def _format_special_requirements(self, analysis: Dict) -> str:
        """格式化特殊需求"""
        special = analysis['special_requirements']
        items = []
        
        if special['enterprise_grade']:
            items.append("- ✅ 企业级要求（高可靠性、QoS保障）")
        if special['needs_security']:
            items.append("- ✅ 安全需求（加密、安全启动）")
        if special['needs_ras']:
            items.append("- ✅ RAS需求（可靠性、可用性、可服务性）")
        if special['needs_qos']:
            items.append("- ✅ QoS需求（延迟SLA、性能隔离）")
        if special['needs_power']:
            items.append("- ✅ 功耗/热管理需求")
        
        return '\n'.join(items) if items else "- 无特殊要求"
    
    def _generate_recommendations(self, analysis: Dict) -> str:
        """生成测试建议"""
        recommendations = []
        
        device = analysis['device_type']
        obj = analysis['primary_objective']
        
        # 基于设备类型的建议
        if device in ['CXL', 'CXL_Switch', 'CXL_Type2']:
            recommendations.append("1. **CXL协议合规测试** - 确保符合CXL规范")
            recommendations.append("2. **内存一致性测试** - 验证缓存一致性正确性")
            if device == 'CXL_Switch':
                recommendations.append("3. **多主机并发测试** - 验证内存池化功能")
        elif device == 'PCM':
            recommendations.append("1. **耐久性测试** - 验证相变材料循环寿命")
            recommendations.append("2. **温度特性测试** - 验证高温保持能力")
        elif device == 'SSD':
            recommendations.append("1. **FTL功能测试** - 验证地址映射和垃圾回收")
            recommendations.append("2. **NAND特性测试** - 验证坏块管理和磨损均衡")
        
        # 基于测试目标的建议
        if obj == 'performance':
            recommendations.append(f"{len(recommendations)+1}. **性能基准测试** - 测量IOPS、带宽、延迟")
            recommendations.append(f"{len(recommendations)+1}. **QoS测试** - 验证P99/P999尾延迟")
        elif obj == 'reliability':
            recommendations.append(f"{len(recommendations)+1}. **长期耐久测试** - 验证寿命预测模型")
            recommendations.append(f"{len(recommendations)+1}. **数据保持测试** - 验证高温保持能力")
        elif obj == 'compliance':
            recommendations.append(f"{len(recommendations)+1}. **协议合规测试** - CV测试套件")
            recommendations.append(f"{len(recommendations)+1}. **认证测试** - 行业认证要求")
        
        return '\n'.join(recommendations)
    
    def _recommend_experts(self, analysis: Dict) -> str:
        """推荐专家"""
        device = analysis['device_type']
        special = analysis['special_requirements']
        
        experts = []
        
        # 基础专家
        if device in ['CXL', 'CXL_Switch', 'CXL_Type2']:
            experts.extend(["CXL Protocol Expert", "Type3 Device Expert"])
            if device == 'CXL_Switch':
                experts.append("CXL Switch Expert")
            if device == 'CXL_Type2':
                experts.extend(["Type2 Device Expert", "CXL Coherency Expert"])
        elif device == 'PCM':
            experts.extend(["PCM Media Expert", "PCM Endurance Expert"])
        elif device == 'SSD':
            experts.extend(["NAND Stack Expert", "FTL Expert", "NVMe Expert"])
        
        # 特殊需求专家
        if special['needs_qos']:
            experts.append("QoS Expert")
        if special['needs_ras']:
            experts.append("CXL RAS Expert")
        if special['needs_security']:
            experts.append("Security Expert")
        if special['enterprise_grade']:
            experts.extend(["Reliability Expert", "Workload Expert"])
        
        return '\n'.join(f"- {exp}" for exp in experts)
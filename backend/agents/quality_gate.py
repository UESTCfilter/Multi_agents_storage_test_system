"""质量验证层 - 确保 Agent 输出质量"""
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class QualityReport:
    """质量报告"""
    passed: bool
    score: float  # 0-100
    checks: Dict[str, bool]
    feedback: List[str]
    suggestions: List[str]


class QualityGate:
    """质量把关层"""
    
    # 质量标准权重
    WEIGHTS = {
        "completeness": 0.3,
        "specificity": 0.3,
        "consistency": 0.2,
        "traceability": 0.2
    }
    
    def __init__(self, min_score: float = 75.0):
        self.min_score = min_score
        self.section_patterns = {
            "strategy": ["测试目标", "测试项", "判定标准", "工具"],
            "design": ["环境", "步骤", "预期结果"],
            "case": ["用例ID", "前置条件", "测试步骤", "预期结果"]
        }
    
    def validate(self, content: str, task_type: str, requirements: str = "") -> QualityReport:
        """
        验证输出质量
        
        Args:
            content: Agent 生成的内容
            task_type: strategy/design/case
            requirements: 原始需求，用于可追溯性检查
            
        Returns:
            QualityReport: 质量报告
        """
        checks = {}
        feedback = []
        suggestions = []
        
        # 1. 完整性检查
        checks["completeness"] = self._check_completeness(content, task_type)
        if not checks["completeness"]:
            feedback.append("内容不完整，缺少必要章节")
            suggestions.append(f"请确保包含以下章节：{self.section_patterns[task_type]}")
        
        # 2. 具体性检查（是否有数值）
        checks["specificity"] = self._check_specificity(content)
        if not checks["specificity"]:
            feedback.append("内容不够具体，缺少量化指标")
            suggestions.append("请添加具体的数值：温度范围、时间、吞吐量、队列深度等")
        
        # 3. 一致性检查
        checks["consistency"] = self._check_consistency(content)
        if not checks["consistency"]:
            feedback.append("内容存在矛盾或重复")
            suggestions.append("请检查各章节之间的逻辑一致性，删除重复内容")
        
        # 4. 可追溯性检查
        checks["traceability"] = self._check_traceability(content, requirements)
        if not checks["traceability"]:
            feedback.append("内容与需求关联不强")
            suggestions.append("请明确标注每条测试项对应的需求点")
        
        # 计算总分
        score = sum(
            self.WEIGHTS[key] * (100 if checks[key] else 0)
            for key in checks
        )
        
        passed = score >= self.min_score
        
        return QualityReport(
            passed=passed,
            score=score,
            checks=checks,
            feedback=feedback,
            suggestions=suggestions
        )
    
    def _check_completeness(self, content: str, task_type: str) -> bool:
        """检查是否包含必要章节"""
        required_sections = self.section_patterns.get(task_type, [])
        if not required_sections:
            return True
        
        # 检查至少包含 70% 的必要章节
        found_count = sum(
            1 for section in required_sections
            if section in content
        )
        return found_count >= len(required_sections) * 0.7
    
    def _check_specificity(self, content: str) -> bool:
        """检查是否包含具体数值"""
        # 查找数值模式：数字 + 单位
        patterns = [
            r'\d+\s*[°℃℉]',  # 温度
            r'\d+\s*[hms小时分钟秒]',  # 时间
            r'\d+\s*[GBMBTBgbmb]',  # 容量
            r'\d+\s*[GTM]bps',  # 带宽
            r'\d+\s*%',  # 百分比
            r'\d+\s*个',  # 数量
            r'\d+\s*次',  # 次数
            r'QD\s*\d+',  # 队列深度
            r'\d+\s*IO/s',  # IOPS
            r'\d+\s*μs',  # 微秒延迟
        ]
        
        found_count = sum(
            1 for pattern in patterns
            if re.search(pattern, content, re.IGNORECASE)
        )
        
        # 至少找到 3 个数值指标
        return found_count >= 3
    
    def _check_consistency(self, content: str) -> bool:
        """检查内容一致性"""
        lines = content.split('\n')
        
        # 检查重复行（非空行且长度>10）
        seen = set()
        duplicates = 0
        for line in lines:
            line = line.strip()
            if len(line) > 10:
                if line in seen:
                    duplicates += 1
                seen.add(line)
        
        # 重复率 < 5% 视为通过
        return duplicates < len(lines) * 0.05
    
    def _check_traceability(self, content: str, requirements: str) -> bool:
        """检查是否可追溯至需求"""
        if not requirements or len(requirements) < 10:
            # 无明确需求时跳过
            return True
        
        # 提取需求关键词
        req_keywords = self._extract_keywords(requirements)
        
        # 检查内容中是否包含需求关键词
        found_keywords = [
            kw for kw in req_keywords
            if kw.lower() in content.lower()
        ]
        
        # 至少包含 30% 的需求关键词
        return len(found_keywords) >= len(req_keywords) * 0.3 if req_keywords else True
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现）"""
        # 过滤停用词，保留名词性词汇
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', 
                     '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                     '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)  # 中文词汇
        words += re.findall(r'[A-Z]{2,}', text)  # 英文缩写（CXL, PCIe）
        
        keywords = [w for w in words if w not in stopwords and len(w) >= 2]
        return list(set(keywords))[:20]  # 去重，取前20个
    
    def generate_enhanced_prompt(self, original_output: str, report: QualityReport, 
                                 task_type: str) -> str:
        """
        生成用于重写的增强 Prompt
        
        Args:
            original_output: 原始输出
            report: 质量报告
            task_type: 任务类型
            
        Returns:
            增强后的 Prompt
        """
        prompt = f"""请基于以下反馈改进内容：

原始内容：
{original_output[:1000]}...

质量检查结果：
- 总分：{report.score:.1f}/100
- 通过项：{[k for k, v in report.checks.items() if v]}
- 未通过项：{[k for k, v in report.checks.items() if not v]}

问题反馈：
"""
        for fb in report.feedback:
            prompt += f"- {fb}\n"
        
        prompt += "\n改进建议：\n"
        for sg in report.suggestions:
            prompt += f"- {sg}\n"
        
        prompt += f"""
请重写 {task_type} 文档，确保：
1. 解决上述所有问题
2. 保持原有结构和深度
3. 输出 Markdown 格式
"""
        return prompt


# 全局质量门实例
quality_gate = QualityGate(min_score=70.0)
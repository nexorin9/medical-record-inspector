"""
质控规则混合模式 - Medical Record Inspector
支持规则检查和样本对比的混合模式，提高检测全面性
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class RuleDefect:
    """规则检查发现的缺陷"""
    rule_id: str
    rule_name: str
    defect_type: str
    severity: str  # high, medium, low
    description: str
    suggested_fix: str
    position: Optional[str] = None


@dataclass
class HybridResult:
    """混合模式检测结果"""
    overall_score: float
    rule_defects: List[RuleDefect]
    sample_defects: List[Dict]
    combined_defects: List[Dict]
    quality_level: str
    risk_factors: List[str]


class HybridChecker:
    """混合模式质控检查器"""

    def __init__(self, sample_weight: float = 0.6, rule_weight: float = 0.4):
        """
        初始化混合检查器

        Args:
            sample_weight: 样本对比得分权重
            rule_weight: 规则检查得分权重
        """
        self.sample_weight = sample_weight
        self.rule_weight = rule_weight

        # 内置质控规则
        self.rules = self._init_rules()

    def _init_rules(self) -> List[Dict]:
        """初始化质控规则"""
        return [
            {
                'id': 'R001',
                'name': '患者基本信息完整',
                'type': 'required_fields',
                'fields': ['姓名', '性别', '年龄', '联系方式'],
                'severity': 'high',
                'description': '患者基本信息缺失',
                'suggested_fix': '补充患者基本信息'
            },
            {
                'id': 'R002',
                'name': '主诉格式正确',
                'type': 'pattern_match',
                'pattern': r'(^\w{2,5}性\w+|\w{2,5}余\w+)',
                'severity': 'medium',
                'description': '主诉格式不规范',
                'suggested_fix': '主诉应为"症状+持续时间"格式'
            },
            {
                'id': 'R003',
                'name': '现病史完整',
                'type': 'required_sections',
                'sections': ['起病缓急', '主要症状', '病情演变', '伴随症状'],
                'severity': 'high',
                'description': '现病史内容不完整',
                'suggested_fix': '补充现病史相关内容'
            },
            {
                'id': 'R004',
                'name': '诊疗经过充分',
                'type': 'required_sections',
                'sections': ['检查项目', '治疗方案', '用药情况'],
                'severity': 'medium',
                'description': '诊疗经过描述不充分',
                'suggested_fix': '补充详细的诊疗经过'
            },
            {
                'id': 'R005',
                'name': '诊断依据充分',
                'type': 'required_sections',
                'sections': ['诊断名称', '诊断依据', '鉴别诊断'],
                'severity': 'high',
                'description': '诊断依据不充分',
                'suggested_fix': '补充诊断依据'
            },
            {
                'id': 'R006',
                'name': '出院诊断明确',
                'type': 'required_sections',
                'sections': ['出院诊断', '出院情况', '出院医嘱'],
                'severity': 'medium',
                'description': '出院诊断不完整',
                'suggested_fix': '补充完整的出院诊断信息'
            }
        ]

    def check_rules(self, text: str) -> List[RuleDefect]:
        """
        按规则检查病历文本

        Args:
            text: 病历文本

        Returns:
            缺陷列表
        """
        defects = []

        for rule in self.rules:
            rule_id = rule['id']
            rule_name = rule['name']
            rule_type = rule['type']
            severity = rule['severity']

            if rule_type == 'required_fields':
                # 检查必需字段
                missing_fields = self._check_missing_fields(text, rule['fields'])
                if missing_fields:
                    defects.append(RuleDefect(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        defect_type='missing_fields',
                        severity=severity,
                        description=f"{rule_name}：缺失字段 [{', '.join(missing_fields)}]",
                        suggested_fix=rule['suggested_fix']
                    ))

            elif rule_type == 'required_sections':
                # 检查必需section
                missing_sections = self._check_missing_sections(text, rule['sections'])
                if missing_sections:
                    defects.append(RuleDefect(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        defect_type='missing_sections',
                        severity=severity,
                        description=f"{rule_name}：缺失section [{', '.join(missing_sections)}]",
                        suggested_fix=rule['suggested_fix']
                    ))

            elif rule_type == 'pattern_match':
                # 正则表达式匹配检查
                import re
                text_preview = text[:500]
                if not re.search(rule['pattern'], text_preview):
                    defects.append(RuleDefect(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        defect_type='pattern_mismatch',
                        severity=severity,
                        description=f"{rule_name}：文本格式不符合要求",
                        suggested_fix=rule['suggested_fix']
                    ))

        return defects

    def _check_missing_fields(self, text: str, fields: List[str]) -> List[str]:
        """检查缺失的字段"""
        missing = []
        for field in fields:
            if field not in text:
                missing.append(field)
        return missing

    def _check_missing_sections(self, text: str, sections: List[str]) -> List[str]:
        """检查缺失的section"""
        missing = []
        for section in sections:
            # 检查section是否在文本中出现
            if section not in text:
                missing.append(section)
        return missing

    def calculate_rule_score(self, defects: List[RuleDefect]) -> float:
        """
        根据规则缺陷计算分数

        Args:
            defects: 缺陷列表

        Returns:
            规则检查分数 (0-1)
        """
        if not defects:
            return 1.0

        # 计算扣分
        total_penalty = 0
        for defect in defects:
            if defect.severity == 'high':
                total_penalty += 0.15
            elif defect.severity == 'medium':
                total_penalty += 0.10
            else:
                total_penalty += 0.05

        return max(0.0, 1.0 - total_penalty)

    def combine_results(self, sample_score: float, rule_score: float,
                        sample_defects: List[Dict],
                        rule_defects: List[RuleDefect]) -> HybridResult:
        """
        结合样本对比和规则检查的结果

        Args:
            sample_score: 样本对比得分
            rule_score: 规则检查得分
            sample_defects: 样本对比缺陷
            rule_defects: 规则检查缺陷

        Returns:
            混合结果
        """
        # 计算综合得分
        overall_score = sample_score * self.sample_weight + rule_score * self.rule_weight

        # 合并缺陷
        combined_defects = []

        # 添加规则缺陷
        for defect in rule_defects:
            combined_defects.append({
                'type': 'rule',
                'rule_id': defect.rule_id,
                'rule_name': defect.rule_name,
                'severity': defect.severity,
                'description': defect.description,
                'suggested_fix': defect.suggested_fix
            })

        # 添加样本缺陷
        for defect in sample_defects:
            combined_defects.append({
                'type': 'sample',
                'index': defect.get('index', 0),
                'similarity': defect.get('similarity', 0),
                'text': defect.get('text', '')
            })

        # 确定质量等级
        if overall_score >= 0.8:
            quality_level = "优秀"
        elif overall_score >= 0.6:
            quality_level = "合格"
        else:
            quality_level = "需要改进"

        # 识别风险因素
        risk_factors = []
        high_rule_defects = [d for d in rule_defects if d.severity == 'high']
        if high_rule_defects:
            risk_factors.append(f"存在{len(high_rule_defects)}个严重规则缺陷")

        low_sample_defects = [d for d in sample_defects if d.get('similarity', 1) < 0.5]
        if low_sample_defects:
            risk_factors.append(f"存在{len(low_sample_defects)}个与模板差异较大的段落")

        severity_ratio = len([d for d in combined_defects if d.get('severity') == 'high']) / max(len(combined_defects), 1)
        if severity_ratio > 0.3:
            risk_factors.append("高严重性缺陷比例较高")

        return HybridResult(
            overall_score=overall_score,
            rule_defects=rule_defects,
            sample_defects=sample_defects,
            combined_defects=combined_defects,
            quality_level=quality_level,
            risk_factors=risk_factors
        )

    def check_hybrid(self, text: str, sample_score: float,
                     sample_defects: List[Dict]) -> HybridResult:
        """
        执行混合模式检查

        Args:
            text: 病历文本
            sample_score: 样本对比得分
            sample_defects: 样本对比缺陷

        Returns:
            混合检测结果
        """
        # 规则检查
        rule_defects = self.check_rules(text)
        rule_score = self.calculate_rule_score(rule_defects)

        # 结合结果
        result = self.combine_results(sample_score, rule_score,
                                      sample_defects, rule_defects)

        return result


def create_hybrid_checker(sample_weight: float = 0.6,
                          rule_weight: float = 0.4) -> HybridChecker:
    """创建混合检查器"""
    return HybridChecker(sample_weight=sample_weight, rule_weight=rule_weight)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=== Hybrid Checker 测试 ===\n")

    # 测试病历
    test_text = """患者基本信息
姓名：张三
性别：男

主诉
发热咳嗽3天。

现病史
患者3天前受凉后出现发热。

诊疗经过
给予头孢曲松静滴。

诊断
社区获得性肺炎。"""

    # 样本对比结果
    sample_result = {
        'overall_score': 0.65,
        'defects': [
            {'index': 0, 'similarity': 0.45, 'text': '患者基本信息不完整'},
            {'index': 3, 'similarity': 0.38, 'text': '诊疗经过不详细'}
        ]
    }

    # 创建检查器
    checker = create_hybrid_checker()

    # 运行规则检查
    print("规则检查结果:")
    rule_defects = checker.check_rules(test_text)
    for defect in rule_defects:
        print(f"  - [{defect.severity}] {defect.rule_name}: {defect.description}")

    rule_score = checker.calculate_rule_score(rule_defects)
    print(f"  规则检查分数: {rule_score:.3f}")

    # 混合模式检查
    print("\n混合模式检查结果:")
    hybrid_result = checker.check_hybrid(test_text, sample_result['overall_score'],
                                         sample_result['defects'])

    print(f"  综合得分: {hybrid_result.overall_score:.3f}")
    print(f"  质量等级: {hybrid_result.quality_level}")
    print(f"  规则缺陷数量: {len(hybrid_result.rule_defects)}")
    print(f"  样本缺陷数量: {len(hybrid_result.sample_defects)}")
    print(f"  总缺陷数量: {len(hybrid_result.combined_defects)}")
    print(f"  风险因素:")
    for factor in hybrid_result.risk_factors:
        print(f"    - {factor}")

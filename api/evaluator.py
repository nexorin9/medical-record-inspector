"""
LLM Quality Evaluator for Medical Record Inspector.

This module implements the core quality assessment logic using LLM
to compare submitted cases against standard templates.
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from api.models import (
    StandardCase, Issue, QualityScore, QualityAssessment,
    AssessRequest, AssessResponse
)

# Load environment variables
load_dotenv()


class QualityEvaluator:
    """病历质量评估器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-3-5-sonnet-20240620"
    ):
        """
        初始化评估器。

        Args:
            api_key: Anthropic API key，从环境变量读取
            model_name: LLM 模型名称
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model_name
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def _load_template(self, template_name: str) -> str:
        """加载 Jinja2 模板文件"""
        template_path = self.templates_dir / template_name
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _generate_assessment_id(self, case_data: Dict) -> str:
        """根据病历数据生成评估ID（使用哈希）"""
        case_str = json.dumps(case_data, sort_keys=True)
        case_hash = hashlib.md5(case_str.encode()).hexdigest()[:16]
        return f"ASSESS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{case_hash}"

    def evaluate_completeness(
        self,
        submitted_case: Dict,
        standard_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历完整性。

        Args:
            submitted_case: 待评估病历
            standard_case: 标准病历模板

        Returns:
            (score, issues): 完整性评分和问题列表
        """
        required_fields = [
            "main_complaint", "present_illness", "past_history",
            "physical_exam", "auxiliary_exams", "diagnosis", "prescription"
        ]

        missing_fields = []
        incomplete_fields = []

        for field in required_fields:
            submitted_value = submitted_case.get(field, "")
            standard_value = standard_case.get(field, "")

            # 检查字段是否存在
            if not submitted_value or len(submitted_value.strip()) < 5:
                missing_fields.append(field)
                continue

            # 检查字段内容是否足够详细
            submitted_len = len(submitted_value)
            standard_len = len(standard_value)

            # 如果提交内容少于标准的50%，视为不完整
            if standard_len > 0 and submitted_len < standard_len * 0.5:
                incomplete_fields.append(field)

        # 计算分数
        total_issues = len(missing_fields) + len(incomplete_fields)
        score = max(0, 10 - total_issues * 1.5)

        issues = []

        for field in missing_fields:
            issues.append({
                "issue_id": f"C{len(issues)+1:03d}",
                "category": "completeness",
                "severity": "high",
                "description": f"字段缺失：{field}",
                "suggestion": f"请补充{field}信息",
                "relevant_fields": [field]
            })

        for field in incomplete_fields:
            issues.append({
                "issue_id": f"C{len(issues)+1:03d}",
                "category": "completeness",
                "severity": "medium",
                "description": f"字段内容不完整：{field}",
                "suggestion": f"请补充{field}的详细信息",
                "relevant_fields": [field]
            })

        return max(0, score), issues

    def evaluate_consistency(
        self,
        submitted_case: Dict,
        standard_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历逻辑一致性。

        Args:
            submitted_case: 待评估病历
            standard_case: 标准病历模板

        Returns:
            (score, issues): 一致性评分和问题列表
        """
        issues = []
        score = 10.0

        diagnosis = submitted_case.get("diagnosis", "")
        prescription = submitted_case.get("prescription", "")
        present_illness = submitted_case.get("present_illness", "")
        past_history = submitted_case.get("past_history", "")

        # 检查诊断是否与现病史匹配
        if diagnosis and present_illness:
            prompt = f"""分析以下现病史描述与诊断是否一致。
现病史：{present_illness}
诊断：{diagnosis}
请回答：一致/不一致。如果不一致，请说明原因。"""

            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                consistency_result = response.content[0].text.lower()

                if "不一致" in consistency_result:
                    score -= 2
                    issues.append({
                        "issue_id": f"CI{len(issues)+1:03d}",
                        "category": "consistency",
                        "severity": "high",
                        "description": "诊断与现病史可能不匹配",
                        "suggestion": "请重新评估诊断是否与症状相符",
                        "relevant_fields": ["diagnosis", "present_illness"]
                    })
            except Exception:
                # 如果 LLM 调用失败，跳过此项检查
                pass

        # 检查治疗方案是否与诊断匹配
        if diagnosis and prescription:
            prompt = f"""分析以下诊断与医嘱/治疗方案是否匹配。
诊断：{diagnosis}
治疗方案：{prescription}
请回答：匹配/不匹配。如果不匹配，请说明原因。"""

            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                match_result = response.content[0].text.lower()

                if "不匹配" in match_result:
                    score -= 2
                    issues.append({
                        "issue_id": f"CI{len(issues)+1:03d}",
                        "category": "consistency",
                        "severity": "high",
                        "description": "治疗方案与诊断可能不匹配",
                        "suggestion": "请检查治疗方案是否针对当前诊断",
                        "relevant_fields": ["diagnosis", "prescription"]
                    })
            except Exception:
                pass

        # 检查既往史是否影响当前诊断
        if past_history and diagnosis:
            prompt = f"""分析以下既往史是否可能影响当前诊断。
既往史：{past_history}
当前诊断：{diagnosis}
请回答：相关/不相关。如果相关，请说明影响。"""

            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                related_result = response.content[0].text.lower()

                if "相关" in related_result:
                    # 这是合理的，可能需要额外说明
                    if "需要" in related_result or "注意" in related_result:
                        score -= 0.5
                        issues.append({
                            "issue_id": f"CI{len(issues)+1:03d}",
                            "category": "consistency",
                            "severity": "low",
                            "description": "既往史可能影响当前诊断评估",
                            "suggestion": "请补充既往史与当前诊断的关系说明",
                            "relevant_fields": ["past_history", "diagnosis"]
                        })
            except Exception:
                pass

        return max(0, score), issues

    def evaluate_timeliness(
        self,
        submitted_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历及时性。

        Args:
            submitted_case: 待评估病历

        Returns:
            (score, issues): 及时性评分和问题列表
        """
        issues = []
        score = 10.0

        # 检查辅助检查是否在诊断之前或同时
        auxiliary_exams = submitted_case.get("auxiliary_exams", "")
        diagnosis = submitted_case.get("diagnosis", "")

        # 提示词分析时间逻辑
        prompt = f"""分析以下病历中的检查和诊断时间逻辑。
辅助检查：{auxiliary_exams}
诊断：{diagnosis}

请判断：
1. 是否先有检查后有诊断（合理）
2. 是否诊断在检查之前（可能不合理）

请回答：合理/需要改进。
如果需要改进，请说明具体原因。"""

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text.lower()

            if "改进" in result or "不合理" in result:
                score -= 1.5
                issues.append({
                    "issue_id": f"T{len(issues)+1:03d}",
                    "category": "timeliness",
                    "severity": "medium",
                    "description": "辅助检查与诊断的时间顺序可能不合理",
                    "suggestion": "请确保辅助检查在诊断之前或同时进行",
                    "relevant_fields": ["auxiliary_exams", "diagnosis"]
                })
        except Exception:
            pass

        # 检查治疗方案是否及时
        prescription = submitted_case.get("prescription", "")
        present_illness = submitted_case.get("present_illness", "")

        prompt = f"""分析以下病历的治疗是否及时。
现病史：{present_illness}
治疗方案：{prescription}

请判断：治疗是否及时（及时/延迟/不合理）。
如果不及时，请说明原因。"""

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text.lower()

            if "延迟" in result or "不及时" in result:
                score -= 1.5
                issues.append({
                    "issue_id": f"T{len(issues)+1:03d}",
                    "category": "timeliness",
                    "severity": "medium",
                    "description": "治疗可能不够及时",
                    "suggestion": "请评估治疗措施的及时性",
                    "relevant_fields": ["prescription", "present_illness"]
                })
        except Exception:
            pass

        return max(0, score), issues

    def evaluate_standardization(
        self,
        submitted_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历规范性。

        Args:
            submitted_case: 待评估病历

        Returns:
            (score, issues): 规范性评分和问题列表
        """
        issues = []
        score = 10.0

        # 检查字段内容长度是否合理
        for field, min_length in [
            ("main_complaint", 5),
            ("present_illness", 30),
            ("diagnosis", 5),
            ("prescription", 10)
        ]:
            value = submitted_case.get(field, "")
            if len(value) < min_length:
                score -= 1
                issues.append({
                    "issue_id": f"S{len(issues)+1:03d}",
                    "category": "standardization",
                    "severity": "low",
                    "description": f"字段内容过短：{field}",
                    "suggestion": f"请补充{field}的详细信息",
                    "relevant_fields": [field]
                })

        # 检查是否使用规范术语
        prompt = f"""分析以下病历文本，检查是否使用规范的医学术语。
主诉：{submitted_case.get('main_complaint', '')}
现病史：{submitted_case.get('present_illness', '')}
诊断：{submitted_case.get('diagnosis', '')}

请指出：
1. 是否使用了不规范的医学术语
2. 是否存在口语化表达
3. 是否存在错别字

请回答：规范/需要改进。如果需要改进，请列出具体问题。"""

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text.lower()

            if "改进" in result or "不规范" in result:
                score -= 1
                issues.append({
                    "issue_id": f"S{len(issues)+1:03d}",
                    "category": "standardization",
                    "severity": "low",
                    "description": "病历可能使用了不规范的术语或表达",
                    "suggestion": "请使用规范的医学术语书写病历",
                    "relevant_fields": ["main_complaint", "present_illness", "diagnosis"]
                })
        except Exception:
            pass

        return max(0, score), issues

    def generate_report(
        self,
        submitted_case: Dict,
        standard_case: Dict,
        assessment: QualityAssessment
    ) -> str:
        """
        生成可读的质量评估报告。

        Args:
            submitted_case: 待评估病历
            standard_case: 标准病历模板
            assessment: 评估结果

        Returns:
            可读的评估报告字符串
        """
        report_lines = [
            "=" * 60,
            "病历质量评估报告",
            "=" * 60,
            f"\n评估时间：{assessment.评估时间.strftime('%Y-%m-%d %H:%M:%S')}",
            f"患者ID：{submitted_case.get('patient_id', 'N/A')}",
            f"就诊ID：{submitted_case.get('visit_id', 'N/A')}",
            f"科室：{submitted_case.get('department', 'N/A')}",
            f"病历类型：{submitted_case.get('case_type', 'N/A')}",
            "",
            "-" * 40,
            "综合评分",
            "-" * 40,
            f"总体评分：{assessment.scores.overall_score:.1f}/10.0",
            "",
            f"  完整性：{assessment.scores.completeness_score:.1f}/10.0",
            f"  一致性：{assessment.scores.consistency_score:.1f}/10.0",
            f"  及时性：{assessment.scores.timeliness_score:.1f}/10.0",
            f"  规范性：{assessment.scores.standardization_score:.1f}/10.0",
            "",
            "-" * 40,
            "发现的问题",
            "-" * 40,
        ]

        if assessment.issues:
            for i, issue in enumerate(assessment.issues, 1):
                report_lines.extend([
                    f"\n[{i}] {issue.category.upper()} - {issue.severity.upper()}",
                    f"  问题：{issue.description}",
                    f"  建议：{issue.suggestion}",
                    f"  相关字段：{', '.join(issue.relevant_fields)}"
                ])
        else:
            report_lines.append("  未发现明显问题。")

        report_lines.extend([
            "",
            "-" * 40,
            "总体评价",
            "-" * 40,
            assessment.report,
            "",
            "=" * 60,
            "报告生成完毕",
            "=" * 60
        ])

        return "\n".join(report_lines)

    def assess(
        self,
        case: Dict,
        standard_template: Optional[Dict] = None,
        standard_template_id: Optional[str] = None
    ) -> QualityAssessment:
        """
        对病历进行全面质量评估。

        Args:
            case: 待评估病历数据
            standard_template: 标准病历模板（可选）
            standard_template_id: 标准模板ID（可选）

        Returns:
            QualityAssessment 评估结果对象
        """
        # 如果没有提供标准模板，使用默认模板
        if standard_template is None:
            # 这里可以根据科室和类型选择合适的默认模板
            standard_template = {
                "main_complaint": "不变",
                "present_illness": "已描述",
                "past_history": "已记录",
                "physical_exam": "已检查",
                "auxiliary_exams": "已完成",
                "diagnosis": "已诊断",
                "prescription": "已开具"
            }

        # 执行各项评估
        completeness_score, completeness_issues = self.evaluate_completeness(
            case, standard_template
        )
        consistency_score, consistency_issues = self.evaluate_consistency(
            case, standard_template
        )
        timeliness_score, timeliness_issues = self.evaluate_timeliness(case)
        standardization_score, standardization_issues = self.evaluate_standardization(
            case
        )

        # 计算综合评分
        overall_score = (
            completeness_score * 0.25 +
            consistency_score * 0.25 +
            timeliness_score * 0.25 +
            standardization_score * 0.25
        )

        # 合并所有问题
        all_issues = (
            completeness_issues +
            consistency_issues +
            timeliness_issues +
            standardization_issues
        )

        # 生成总体报告
        overall_comment = self._generate_overall_comment(
            completeness_score, consistency_score,
            timeliness_score, standardization_score,
            all_issues
        )

        # 创建评估对象
        assessment = QualityAssessment(
            assessment_id=self._generate_assessment_id(case),
            patient_id=case.get("patient_id"),
            visit_id=case.get("visit_id"),
            scores=QualityScore(
                completeness_score=round(completeness_score, 1),
                consistency_score=round(consistency_score, 1),
                timeliness_score=round(timeliness_score, 1),
                standardization_score=round(standardization_score, 1),
                overall_score=round(overall_score, 1)
            ),
            issues=[Issue(**issue) for issue in all_issues],
            report=overall_comment,
            标注时间=datetime.now(),
            standard_template_id=standard_template_id
        )

        return assessment

    def _generate_overall_comment(
        self,
        completeness: float,
        consistency: float,
        timeliness: float,
        standardization: float,
        issues: List[Dict]
    ) -> str:
        """生成总体评论"""
        score = (completeness + consistency + timeliness + standardization) / 4

        if score >= 9:
            comment = "病历质量优秀，书写规范，内容完整。"
        elif score >= 7:
            comment = "病历质量良好，基本符合规范要求。"
        elif score >= 5:
            comment = "病历质量一般，存在需要改进的地方。"
        else:
            comment = "病历质量较差，存在较多问题需要整改。"

        if issues:
            high_count = sum(1 for i in issues if i.get("severity") == "high")
            medium_count = sum(1 for i in issues if i.get("severity") == "medium")
            low_count = sum(1 for i in issues if i.get("severity") == "low")

            comment += f"\n\n主要问题统计："
            comment += f"\n- 严重问题：{high_count}项"
            comment += f"\n- 中等问题：{medium_count}项"
            comment += f"\n- 轻微问题：{low_count}项"

            if high_count > 0:
                comment += "\n\n建议优先处理严重问题，确保病历质量和诊疗安全。"
        else:
            comment += "\n\n继续保持良好的病历书写质量。"

        return comment


# 便捷函数
def assess_case(
    case: Dict,
    api_key: Optional[str] = None,
    model_name: str = "claude-3-5-sonnet-20240620"
) -> QualityAssessment:
    """
    便捷的病历评估函数。

    Args:
        case: 待评估病历
        api_key: API密钥
        model_name: 模型名称

    Returns:
        评估结果对象
    """
    evaluator = QualityEvaluator(api_key=api_key, model_name=model_name)
    return evaluator.assess(case)


if __name__ == "__main__":
    # 简单测试
    test_case = {
        "patient_id": "PAT001",
        "visit_id": "VIS001",
        "department": "内科",
        "case_type": "门诊",
        "main_complaint": "咳嗽3天",
        "present_illness": "患者3天前受凉后出现咳嗽",
        "past_history": "无特殊",
        "physical_exam": "双肺呼吸音清",
        "auxiliary_exams": "血常规正常",
        "diagnosis": "急性支气管炎",
        "prescription": "阿莫西林 0.5g tid"
    }

    # 评估
    evaluator = QualityEvaluator()
    result = evaluator.assess(test_case)

    print(f"评估ID：{result.assessment_id}")
    print(f"总体评分：{result.scores.overall_score}")
    print(f"发现问题：{len(result.issues)}项")
    for issue in result.issues:
        print(f"  - {issue.category}: {issue.description}")

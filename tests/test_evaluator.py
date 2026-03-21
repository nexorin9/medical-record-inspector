"""
Unit tests for the QualityEvaluator.

Note: These tests may require mocking the LLM API calls.
"""

import pytest
from unittest.mock import patch, MagicMock
import json

from api.models import QualityAssessment, QualityScore
from api.evaluator import QualityEvaluator


class TestQualityEvaluator:
    """QualityEvaluator 类测试"""

    def test_init(self):
        """测试初始化"""
        evaluator = QualityEvaluator()
        assert evaluator is not None

    @patch('api.evaluator.anthropic.Anthropic')
    def test_evaluate_completeness_full(self, mock_anthropic):
        """测试完整性评估（完整字段）"""
        evaluator = QualityEvaluator()

        submitted_case = {
            "main_complaint": "咳嗽3天",
            "present_illness": "患者3天前出现咳嗽、咳痰...",
            "past_history": "否认高血压...",
            "physical_exam": "双肺呼吸音清...",
            "auxiliary_exams": "血常规正常...",
            "diagnosis": "急性支气管炎",
            "prescription": "阿莫西林 0.5g tid"
        }

        standard_case = {
            "main_complaint": "咳嗽",
            "present_illness": "患者...",
            "past_history": "无特殊...",
            "physical_exam": "正常...",
            "auxiliary_exams": "无...",
            "diagnosis": "诊断",
            "prescription": "治疗"
        }

        score, issues = evaluator.evaluate_completeness(submitted_case, standard_case)

        assert isinstance(score, float)
        assert score > 0
        assert isinstance(issues, list)

    @patch('api.evaluator.anthropic.Anthropic')
    def test_evaluate_completeness_missing(self, mock_anthropic):
        """测试完整性评估（缺失字段）"""
        evaluator = QualityEvaluator()

        submitted_case = {
            "main_complaint": "咳嗽",
            # 缺少其他字段
        }

        standard_case = {
            "main_complaint": "咳嗽",
            "present_illness": "描述",
            "past_history": "无",
            "physical_exam": "正常",
            "auxiliary_exams": "无",
            "diagnosis": "诊断",
            "prescription": "治疗"
        }

        score, issues = evaluator.evaluate_completeness(submitted_case, standard_case)

        # 应该发现缺失字段
        assert len(issues) > 0
        # 分数应该较低
        assert score < 8

    @patch('api.evaluator.anthropic.Anthropic')
    def test_evaluate_consistency(self, mock_anthropic):
        """测试一致性评估"""
        evaluator = QualityEvaluator()

        submitted_case = {
            "diagnosis": "急性支气管炎",
            "prescription": "阿莫西林 0.5g tid",
            "present_illness": "咳嗽、咳痰3天",
            "past_history": "无特殊"
        }

        standard_case = {}

        score, issues = evaluator.evaluate_consistency(submitted_case, standard_case)

        assert isinstance(score, float)
        assert score >= 0

    @patch('api.evaluator.anthropic.Anthropic')
    def test_evaluate_timeliness(self, mock_anthropic):
        """测试及时性评估"""
        evaluator = QualityEvaluator()

        submitted_case = {
            "auxiliary_exams": "血常规正常",
            "diagnosis": "急性支气管炎",
            "prescription": "阿莫西林 0.5g tid"
        }

        score, issues = evaluator.evaluate_timeliness(submitted_case)

        assert isinstance(score, float)
        assert score >= 0

    @patch('api.evaluator.anthropic.Anthropic')
    def test_evaluate_standardization(self, mock_anthropic):
        """测试规范性评估"""
        evaluator = QualityEvaluator()

        submitted_case = {
            "main_complaint": "咳嗽3天",
            "present_illness": "患者3天前出现咳嗽...",
            "diagnosis": "急性支气管炎",
            "prescription": "阿莫西林 0.5g tid"
        }

        score, issues = evaluator.evaluate_standardization(submitted_case)

        assert isinstance(score, float)
        assert score >= 0

    @patch('api.evaluator.anthropic.Anthropic')
    def test_assess_full(self, mock_anthropic):
        """测试完整评估流程"""
        evaluator = QualityEvaluator()

        submitted_case = {
            "patient_id": "PAT001",
            "visit_id": "VIS001",
            "department": "内科",
            "case_type": "门诊",
            "main_complaint": "咳嗽3天",
            "present_illness": "患者3天前出现咳嗽、咳痰...",
            "past_history": "否认高血压...",
            "physical_exam": "双肺呼吸音清...",
            "auxiliary_exams": "血常规正常...",
            "diagnosis": "急性支气管炎",
            "prescription": "阿莫西林 0.5g tid"
        }

        standard_case = {
            "main_complaint": "咳嗽",
            "present_illness": "患者...",
            "past_history": "无特殊...",
            "physical_exam": "正常...",
            "auxiliary_exams": "无...",
            "diagnosis": "诊断",
            "prescription": "治疗"
        }

        result = evaluator.assess(submitted_case, standard_case)

        assert isinstance(result, QualityAssessment)
        assert result.patient_id == "PAT001"
        assert result.scores.overall_score >= 0

    def test_generate_report(self):
        """测试报告生成"""
        evaluator = QualityEvaluator()

        submitted_case = {"department": "内科"}
        standard_case = {}
        assessment = QualityAssessment(
            assessment_id="ASSESS-001",
            scores=QualityScore(
                completeness_score=8.0,
                consistency_score=9.0,
                timeliness_score=7.5,
                standardization_score=8.5,
                overall_score=8.25
            ),
            issues=[],
            report="测试报告",
            标注时间=None
        )

        report = evaluator.generate_report(submitted_case, standard_case, assessment)

        assert isinstance(report, str)
        assert "病历质量评估报告" in report
        assert "综合评分" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

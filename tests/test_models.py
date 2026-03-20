"""
Unit tests for data models.
"""

import pytest
from pydantic import ValidationError

from api.models import (
    StandardCase, Issue, QualityScore, QualityAssessment,
    AssessRequest, AssessResponse, ListStandardsResponse,
    HealthResponse, CaseData
)


class TestStandardCase:
    """StandardCase 模型测试"""

    def test_valid_standard_case(self):
        """测试有效的标准病历"""
        case = StandardCase(
            template_id="TEST-001",
            department="内科",
            case_type="门诊",
            main_complaint="咳嗽3天",
            present_illness="患者3天前受凉后出现咳嗽",
            past_history="无特殊",
            physical_exam="双肺呼吸音清",
            auxiliary_exams="血常规正常",
            diagnosis="急性支气管炎",
            prescription="阿莫西林 0.5g tid"
        )
        assert case.template_id == "TEST-001"
        assert case.department == "内科"

    def test_standard_case_missing_required_field(self):
        """测试缺少必填字段"""
        with pytest.raises(ValidationError):
            StandardCase(
                template_id="TEST-001",
                department="内科",
                case_type="门诊"
                # 缺少其他必填字段
            )


class TestIssue:
    """Issue 模型测试"""

    def test_valid_issue(self):
        """测试有效的Issue"""
        issue = Issue(
            issue_id="I001",
            category="completeness",
            severity="high",
            description="字段缺失",
            suggestion="请补充信息",
            relevant_fields=["field1"]
        )
        assert issue.issue_id == "I001"
        assert issue.category == "completeness"
        assert issue.severity == "high"

    def test_issue_default_values(self):
        """测试Issue默认值"""
        issue = Issue(
            issue_id="I001",
            category="completeness",
            severity="high",
            description="测试问题",
            suggestion="建议"
        )
        assert issue.relevant_fields == []


class TestQualityScore:
    """QualityScore 模型测试"""

    def test_valid_quality_score(self):
        """测试有效的评分"""
        score = QualityScore(
            completeness_score=8.5,
            consistency_score=9.0,
            timeliness_score=7.5,
            standardization_score=8.0,
            overall_score=8.25
        )
        assert score.completeness_score == 8.5
        assert score.overall_score == 8.25

    def test_score_range(self):
        """测试评分范围"""
        with pytest.raises(ValidationError):
            QualityScore(
                completeness_score=11,  # 超过最大值
                consistency_score=9.0,
                timeliness_score=7.5,
                standardization_score=8.0,
                overall_score=8.25
            )

    def test_score_min_value(self):
        """测试评分最小值"""
        with pytest.raises(ValidationError):
            QualityScore(
                completeness_score=-1,  # 低于最小值
                consistency_score=9.0,
                timeliness_score=7.5,
                standardization_score=8.0,
                overall_score=8.25
            )


class TestQualityAssessment:
    """QualityAssessment 模型测试"""

    def test_valid_assessment(self):
        """测试有效的评估结果"""
        assessment = QualityAssessment(
            assessment_id="ASSESS-001",
            patient_id="PAT001",
            visit_id="VIS001",
            scores=QualityScore(
                completeness_score=8.0,
                consistency_score=9.0,
                timeliness_score=7.5,
                standardization_score=8.5,
                overall_score=8.25
            ),
            issues=[],
            report="病历质量良好",
            标注时间=None
        )
        assert assessment.assessment_id == "ASSESS-001"
        assert assessment.scores.overall_score == 8.25

    def test_assessment_with_issues(self):
        """测试包含问题的评估结果"""
        assessment = QualityAssessment(
            assessment_id="ASSESS-002",
            scores=QualityScore(
                completeness_score=6.0,
                consistency_score=9.0,
                timeliness_score=9.0,
                standardization_score=9.0,
                overall_score=8.25
            ),
            issues=[
                Issue(
                    issue_id="C001",
                    category="completeness",
                    severity="medium",
                    description="字段不完整",
                    suggestion="请补充",
                    relevant_fields=["field1"]
                )
            ],
            report="病历质量一般",
            标注时间=None
        )
        assert len(assessment.issues) == 1


class testCaseData:
    """CaseData 模型测试"""

    def test_valid_case_data(self):
        """测试有效的case数据"""
        case = CaseData(
            department="内科",
            case_type="门诊",
            main_complaint="咳嗽",
            present_illness="描述",
            past_history="无",
            physical_exam="正常",
            auxiliary_exams="无",
            diagnosis="诊断",
            prescription="治疗"
        )
        assert case.department == "内科"
        assert case.patient_id is None

    def test_case_data_optional_fields(self):
        """测试case数据可选字段"""
        case = CaseData(
            patient_id="PAT001",
            visit_id="VIS001",
            department="外科",
            case_type="住院",
            main_complaint="腹痛",
            present_illness="描述",
            past_history="无",
            physical_exam="无",
            auxiliary_exams="无",
            diagnosis="诊断",
            prescription="治疗",
            standard_template_id="STD001"
        )
        assert case.patient_id == "PAT001"
        assert case.standard_template_id == "STD001"


class TestResponses:
    """响应模型测试"""

    def test_assess_response(self):
        """测试AssessResponse"""
        response = AssessResponse(
            success=True,
            result=QualityAssessment(
                assessment_id="A001",
                scores=QualityScore(
                    completeness_score=8.0,
                    consistency_score=8.0,
                    timeliness_score=8.0,
                    standardization_score=8.0,
                    overall_score=8.0
                ),
                issues=[],
                report="测试",
                标注时间=None
            ),
            message="测试消息"
        )
        assert response.success is True

    def test_list_standards_response(self):
        """测试ListStandardsResponse"""
        response = ListStandardsResponse(
            success=True,
            standards=[],
            total=0
        )
        assert response.total == 0

    def test_health_response(self):
        """测试HealthResponse"""
        response = HealthResponse(status="healthy")
        assert response.status == "healthy"
        assert response.version == "1.0.0"

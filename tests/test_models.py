"""
测试数据模型序列化
tests/test_models.py
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from models.evaluator import EvaluationRequest
from models.response import EvaluationResponse, DimensionScores, Issue


def test_evaluation_request_serialization():
    """测试评估请求序列化"""
    request = EvaluationRequest(
        content="病历内容",
        template_id="template-001",
        evaluation_dims=["completeness", "logicality"]
    )

    # 序列化为 dict
    data = request.dict()
    assert data["content"] == "病历内容"
    assert data["template_id"] == "template-001"
    assert data["evaluation_dims"] == ["completeness", "logicality"]

    # 反序列化
    request2 = EvaluationRequest(**data)
    assert request2.content == "病历内容"

    print("test_evaluation_request_serialization passed!")


def test_dimension_scores_serialization():
    """测试维度分数序列化"""
    scores = DimensionScores(
        completeness=85.5,
        logicality=90.0,
        timeliness=75.0,
        normativity=88.5
    )

    data = scores.dict()
    assert data["completeness"] == 85.5
    assert data["logicality"] == 90.0

    scores2 = DimensionScores(**data)
    assert scores2.completeness == 85.5

    print("test_dimension_scores_serialization passed!")


def test_issue_serialization():
    """测试问题序列化"""
    issue = Issue(
        dimension="completeness",
        severity="high",
        description="缺少主诉信息",
        recommendation="请补充主诉内容"
    )

    data = issue.dict()
    assert data["dimension"] == "completeness"
    assert data["severity"] == "high"
    assert data["recommendation"] == "请补充主诉内容"

    issue2 = Issue(**data)
    assert issue2.dimension == "completeness"

    print("test_issue_serialization passed!")


def test_evaluation_response_serialization():
    """测试评估响应序列化"""
    response = EvaluationResponse(
        overall_score=85.0,
        dimension_scores=DimensionScores(
            completeness=85.5,
            logicality=90.0,
            timeliness=75.0,
            normativity=88.5
        ),
        issues=[
            Issue(
                dimension="completeness",
                severity="high",
                description="缺少主诉信息",
                recommendation="请补充主诉内容"
            )
        ],
        recommendations=["建议完善病历内容"]
    )

    data = response.dict()
    assert data["overall_score"] == 85.0
    assert len(data["issues"]) == 1

    response2 = EvaluationResponse(**data)
    assert response2.overall_score == 85.0

    print("test_evaluation_response_serialization passed!")


def test_chinese_content():
    """测试中文内容处理"""
    request = EvaluationRequest(
        content="患者主诉：头痛三天，伴有恶心呕吐。",
        template_id="template-001",
        evaluation_dims=["completeness"]
    )

    data = request.dict()
    assert "头痛" in data["content"]
    assert "恶心呕吐" in data["content"]

    print("test_chinese_content passed!")


def test_empty_fields():
    """测试空字段处理"""
    request = EvaluationRequest(
        content="病历内容",
        template_id=None,
        evaluation_dims=None
    )

    data = request.dict()
    assert data["template_id"] is None
    assert data["evaluation_dims"] is None

    print("test_empty_fields passed!")


if __name__ == "__main__":
    test_evaluation_request_serialization()
    test_dimension_scores_serialization()
    test_issue_serialization()
    test_evaluation_response_serialization()
    test_chinese_content()
    test_empty_fields()
    print("\nAll model tests passed!")

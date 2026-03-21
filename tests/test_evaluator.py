"""
测试评估器核心逻辑
tests/test_evaluator.py
"""

import sys
import os
import asyncio

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Add parent directory to path for importing test utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evaluator import MedicalRecordEvaluator, get_default_evaluator, evaluate_medical_record, get_evaluator_with_model
from src.models.evaluator import EvaluationRequest
from src.models.response import EvaluationResponse, DimensionScores, Issue
from src.llm.llm_client import LLMClient


def test_evaluator_initialization():
    """测试评估器初始化"""
    evaluator = MedicalRecordEvaluator()

    # 检查默认权重
    assert evaluator.weight_map["completeness"] == 0.25
    assert evaluator.weight_map["logicality"] == 0.25
    assert evaluator.weight_map["timeliness"] == 0.25
    assert evaluator.weight_map["normativity"] == 0.25

    # 检查严重程度映射
    assert evaluator.severity_score_map["critical"] == 0.0
    assert evaluator.severity_score_map["high"] == 40.0
    assert evaluator.severity_score_map["medium"] == 70.0
    assert evaluator.severity_score_map["low"] == 90.0

    print("test_evaluator_initialization passed!")


def test_evaluator_with_custom_weights():
    """测试自定义权重"""
    weight_map = {
        "completeness": 0.4,
        "logicality": 0.3,
        "timeliness": 0.2,
        "normativity": 0.1,
    }
    evaluator = MedicalRecordEvaluator(weight_map=weight_map)

    # 检查权重归一化
    assert abs(sum(evaluator.weight_map.values()) - 1.0) < 0.01

    print("test_evaluator_with_custom_weights passed!")


def test_normalize_severity():
    """测试严重程度标准化"""
    evaluator = MedicalRecordEvaluator()

    # 标准级别
    assert evaluator._normalize_severity("critical") == "critical"
    assert evaluator._normalize_severity("high") == "high"
    assert evaluator._normalize_severity("medium") == "medium"
    assert evaluator._normalize_severity("low") == "low"

    # 中文映射（注意：轻微映射到medium，低单独映射到low）
    assert evaluator._normalize_severity("严重") == "critical"
    assert evaluator._normalize_severity("中度") == "high"
    assert evaluator._normalize_severity("轻微") == "medium"  # 中文的"轻微"对应medium
    assert evaluator._normalize_severity("低") == "low"  # 单独的"低"对应low

    # 大小写
    assert evaluator._normalize_severity("CRITICAL") == "critical"
    assert evaluator._normalize_severity("  HIGH  ") == "high"

    print("test_normalize_severity passed!")


def test_calculate_dimension_score():
    """测试维度分数计算"""
    evaluator = MedicalRecordEvaluator()

    # 无问题，满分
    issues = []
    assert evaluator._calculate_dimension_score(issues) == 100.0

    # 一个低严重度问题（-5分）
    issues = [{"severity": "low"}]
    assert evaluator._calculate_dimension_score(issues) == 95.0

    # 一个中严重度问题（-10分）
    issues = [{"severity": "medium"}]
    assert evaluator._calculate_dimension_score(issues) == 90.0

    # 一个高严重度问题（-20分）
    issues = [{"severity": "high"}]
    assert evaluator._calculate_dimension_score(issues) == 80.0

    # 一个严重问题（-30分）
    issues = [{"severity": "critical"}]
    assert evaluator._calculate_dimension_score(issues) == 70.0

    # 多个问题累加
    issues = [
        {"severity": "low"},
        {"severity": "medium"},
        {"severity": "high"},
    ]
    assert evaluator._calculate_dimension_score(issues) == 65.0  # 100 - 5 - 10 - 20

    # 分数不低于 0
    issues = [{"severity": "critical"} for _ in range(10)]
    assert evaluator._calculate_dimension_score(issues) == 0.0

    print("test_calculate_dimension_score passed!")


def test_evaluation_request():
    """测试评估请求模型"""
    request = EvaluationRequest(
        content="患者主诉：头痛三天，伴有恶心呕吐。",
        template_id="template-001",
        evaluation_dims=["completeness", "logicality"]
    )

    assert request.content == "患者主诉：头痛三天，伴有恶心呕吐。"
    assert request.template_id == "template-001"
    assert request.evaluation_dims == ["completeness", "logicality"]

    # 测试可选字段默认值
    request2 = EvaluationRequest(content="病历内容")
    assert request2.template_id is None
    assert request2.evaluation_dims is None

    print("test_evaluation_request passed!")


def test_dimension_scores_model():
    """测试维度分数模型"""
    scores = DimensionScores(
        completeness=85.5,
        logicality=90.0,
        timeliness=75.0,
        normativity=88.5
    )

    assert scores.completeness == 85.5
    assert scores.logicality == 90.0
    assert scores.timeliness == 75.0
    assert scores.normativity == 88.5

    print("test_dimension_scores_model passed!")


def test_issue_model():
    """测试问题模型"""
    issue = Issue(
        dimension="completeness",
        severity="high",
        description="缺少主诉信息",
        recommendation="请补充主诉内容"
    )

    assert issue.dimension == "completeness"
    assert issue.severity == "high"
    assert issue.description == "缺少主诉信息"
    assert issue.recommendation == "请补充主诉内容"

    print("test_issue_model passed!")


def test_evaluation_response_model():
    """测试评估响应模型"""
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

    assert response.overall_score == 85.0
    assert len(response.issues) == 1
    assert response.recommendations == ["建议完善病历内容"]

    print("test_evaluation_response_model passed!")


def test_aggregate_issues():
    """测试问题聚合和去重"""
    evaluator = MedicalRecordEvaluator()

    issues = [
        {"dimension": "completeness", "description": "问题1", "severity": "high"},
        {"dimension": "completeness", "description": "问题1", "severity": "high"},  # 重复
        {"dimension": "logicality", "description": "问题2", "severity": "medium"},
    ]

    aggregated = evaluator._aggregate_issues(issues)

    # 检查去重
    assert len(aggregated) == 2

    # 检查按严重程度排序
    assert aggregated[0].severity == "high"
    assert aggregated[1].severity == "medium"

    print("test_aggregate_issues passed!")


def test_get_default_evaluator():
    """测试获取默认评估器"""
    evaluator1 = get_default_evaluator()
    evaluator2 = get_default_evaluator()

    # 应该返回同一个实例（单例模式）
    assert evaluator1 is evaluator2

    print("test_get_default_evaluator passed!")


def test_parse_issue():
    """测试问题解析"""
    evaluator = MedicalRecordEvaluator()

    # 完整问题数据
    issue_data = {
        "dimension": "completeness",
        "severity": "high",
        "description": "缺少主诉信息",
        "suggestion": "请补充主诉内容"
    }

    issue = evaluator._parse_issue(issue_data, "completeness")
    assert issue is not None
    assert issue.dimension == "completeness"
    assert issue.severity == "high"
    assert issue.description == "缺少主诉信息"
    assert issue.recommendation == "请补充主诉内容"

    # 缺少推荐字段（应使用 suggestion）
    issue_data2 = {
        "dimension": "completeness",
        "severity": "medium",
        "description": "缺少体格检查"
    }
    issue2 = evaluator._parse_issue(issue_data2, "completeness")
    assert issue2 is not None
    assert issue2.recommendation == ""

    print("test_parse_issue passed!")


def test_empty_content_handling():
    """测试空内容处理"""
    evaluator = MedicalRecordEvaluator()

    # 异步调用 evaluate 方法
    async def run_test():
        # 空字符串
        request = EvaluationRequest(content="")
        response = await evaluator.evaluate(request)

        # 应该返回空响应（overall_score = 0）
        assert response.overall_score == 0.0
        assert len(response.issues) == 0

        # 只有空格
        request2 = EvaluationRequest(content="   ")
        response2 = await evaluator.evaluate(request2)

        assert response2.overall_score == 0.0

    asyncio.run(run_test())

    print("test_empty_content_handling passed!")


def test_extract_json_from_response():
    """测试 JSON 提取"""
    evaluator = MedicalRecordEvaluator()

    # 纯 JSON
    response = '{"dimension_score": 85, "issues": []}'
    result = evaluator._extract_json_from_response(response)
    assert result["dimension_score"] == 85

    # 包含代码块标记
    response2 = '```json\n{"dimension_score": 90}\n```'
    result2 = evaluator._extract_json_from_response(response2)
    assert result2["dimension_score"] == 90

    print("test_extract_json_from_response passed!")


if __name__ == "__main__":
    test_evaluator_initialization()
    test_evaluator_with_custom_weights()
    test_normalize_severity()
    test_calculate_dimension_score()
    test_evaluation_request()
    test_dimension_scores_model()
    test_issue_model()
    test_evaluation_response_model()
    test_aggregate_issues()
    test_get_default_evaluator()
    test_parse_issue()
    test_empty_content_handling()
    test_extract_json_from_response()
    print("\nAll evaluator tests passed!")

"""
评估响应模型 - Evaluation Response Models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class Issue(BaseModel):
    """
    评估问题模型

    Attributes:
        dimension (str): 问题所属评估维度（completeness, logicality, timeliness, normativity）
        severity (str): 问题严重程度
            - critical: 严重问题，影响诊断或医疗安全
            - high: 较严重问题，需要重点关注
            - medium: 一般问题，建议修正
            - low: 轻微问题，可优化
        description (str): 问题描述
        recommendation (Optional[str]): 改进建议
    """
    dimension: str = Field(..., description="问题所属评估维度")
    severity: str = Field(
        ...,
        description="问题严重程度: critical, high, medium, low",
        pattern="^(critical|high|medium|low)$"
    )
    description: str = Field(..., description="问题描述")
    recommendation: Optional[str] = Field(None, description="改进建议")


class DimensionScores(BaseModel):
    """
    评估维度分数模型

    Attributes:
        completeness (float): 完整性分数 (0-100)
        logicality (float): 逻辑性分数 (0-100)
        timeliness (float): 及时性分数 (0-100)
        normativity (float): 规范性分数 (0-100)
    """
    completeness: float = Field(..., ge=0, le=100, description="完整性分数 (0-100)")
    logicality: float = Field(..., ge=0, le=100, description="逻辑性分数 (0-100)")
    timeliness: float = Field(..., ge=0, le=100, description="及时性分数 (0-100)")
    normativity: float = Field(..., ge=0, le=100, description="规范性分数 (0-100)")


class EvaluationResponse(BaseModel):
    """
    病历评估响应模型

    Attributes:
        overall_score (float): 总体评分 (0-100)
        dimension_scores (DimensionScores): 各维度分数
        issues (List[Issue]): 问题列表
        recommendations (List[str]): 综合改进建议
    """
    overall_score: float = Field(..., ge=0, le=100, description="总体评分 (0-100)")
    dimension_scores: DimensionScores = Field(..., description="各维度分数")
    issues: List[Issue] = Field(default_factory=list, description="问题列表")
    recommendations: List[str] = Field(default_factory=list, description="综合改进建议")


# 用于快速创建空响应的辅助函数
def create_empty_response() -> EvaluationResponse:
    """创建一个空的评估响应"""
    return EvaluationResponse(
        overall_score=0.0,
        dimension_scores=DimensionScores(
            completeness=0.0,
            logicality=0.0,
            timeliness=0.0,
            normativity=0.0
        ),
        issues=[],
        recommendations=[]
    )

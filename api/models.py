"""
Pydantic Data Models for Medical Record Inspector.

This module defines all Pydantic models for:
- Standard case templates
- Quality assessment results
- API request/response
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class StandardCase(BaseModel):
    """标准病历模板"""
    template_id: str = Field(..., description="模板唯一标识")
    department: str = Field(..., description="科室名称")
    case_type: str = Field(..., description="病历类型（门诊/住院/急诊）")
    main_complaint: str = Field(..., description="主诉")
    present_illness: str = Field(..., description="现病史")
    past_history: str = Field(..., description="既往史")
    physical_exam: str = Field(..., description="体格检查")
    auxiliary_exams: str = Field(..., description="辅助检查")
    diagnosis: str = Field(..., description="诊断")
    prescription: str = Field(..., description="医嘱/治疗方案")
    notes: Optional[str] = Field(None, description="备注")


class Issue(BaseModel):
    """发现的问题"""
    issue_id: str = Field(..., description="问题唯一标识")
    category: str = Field(..., description="问题分类（完整性/一致性/及时性/规范性）")
    severity: str = Field(..., description="严重程度（高/中/低）")
    description: str = Field(..., description="问题描述")
    suggestion: str = Field(..., description="改进建议")
    relevant_fields: List[str] = Field(default_factory=list, description="相关字段")


class QualityScore(BaseModel):
    """质量评分"""
    completeness_score: float = Field(..., ge=0, le=10, description="完整性评分")
    consistency_score: float = Field(..., ge=0, le=10, description="逻辑一致性评分")
    timeliness_score: float = Field(..., ge=0, le=10, description="及时性评分")
    standardization_score: float = Field(..., ge=0, le=10, description="规范性评分")
    overall_score: float = Field(..., ge=0, le=10, description="总体评分")


class QualityAssessment(BaseModel):
    """质量评估结果"""
    assessment_id: str = Field(..., description="评估唯一标识")
    patient_id: Optional[str] = Field(None, description="患者ID")
    visit_id: Optional[str] = Field(None, description="就诊ID")
    scores: QualityScore = Field(..., description="各项评分")
    issues: List[Issue] = Field(default_factory=list, description="发现的问题列表")
    report: str = Field(..., description="可解释报告文本")
    评估时间: datetime = Field(default_factory=datetime.now, description="评估时间")
    standard_template_id: Optional[str] = Field(None, description="所参考的标准模板ID")


class AssessRequest(BaseModel):
    """质控评估请求"""
    case: Dict[str, Any] = Field(..., description="待评估病历数据")
    standard_template_id: Optional[str] = Field(None, description="标准模板ID（可选）")
    options: Dict[str, Any] = Field(default_factory=dict, description="评估选项")


class AssessResponse(BaseModel):
    """质控评估响应"""
    success: bool = Field(..., description="是否成功")
    result: QualityAssessment = Field(..., description="评估结果")
    message: Optional[str] = Field(None, description="消息")


class ListStandardsResponse(BaseModel):
    """列出标准模板响应"""
    success: bool = Field(..., description="是否成功")
    standards: List[StandardCase] = Field(default_factory=list, description="标准模板列表")
    total: int = Field(..., description="总数")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    version: str = Field("1.0.0", description="版本号")


class BatchRequest(BaseModel):
    """批量评估请求"""
    files: List[str] = Field(default_factory=list, description="文件路径列表")
    directory: Optional[str] = Field(None, description="目录路径")
    options: Dict[str, Any] = Field(default_factory=dict, description="评估选项")


class BatchResponse(BaseModel):
    """批量评估响应"""
    success: bool = Field(..., description="是否成功")
    total: int = Field(..., description="处理总数")
    successful: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="评估结果列表")
    summary: Dict[str, Any] = Field(default_factory=dict, description="汇总统计")

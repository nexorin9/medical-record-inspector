"""
FastAPI API Service for Medical Record Inspector.

This module provides REST API endpoints for:
- Health check
- Quality assessment
- List standard cases
"""

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from api.models import (
    AssessRequest, AssessResponse, ListStandardsResponse,
    HealthResponse, QualityAssessment, QualityScore, Issue
)
from api.evaluator import QualityEvaluator, assess_case
from api.standard_case_generator import StandardCaseGenerator
from api.middleware.validation import validation_middleware

# Create FastAPI app
app = FastAPI(
    title="Medical Record Inspector API",
    description="病历质控评估 API 服务",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data validation middleware
app.middleware("http")(validation_middleware)


#/models model
class CaseData(BaseModel):
    """病历数据模型"""
    patient_id: Optional[str] = None
    visit_id: Optional[str] = None
    department: str
    case_type: str
    main_complaint: str
    present_illness: str
    past_history: str
    physical_exam: str
    auxiliary_exams: str
    diagnosis: str
    prescription: str
    standard_template_id: Optional[str] = None


# Health check endpoint
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(status="healthy")


# Quality assessment endpoint
@app.post("/api/v1/assess", response_model=AssessResponse)
async def assess_quality(
    case_data: CaseData = Body(...)
):
    """
    质量评估接口

    对提交的病历进行质量评估，返回评估结果和问题列表。
    """
    try:
        # 构建病历数据字典
        case_dict = {
            "patient_id": case_data.patient_id,
            "visit_id": case_data.visit_id,
            "department": case_data.department,
            "case_type": case_data.case_type,
            "main_complaint": case_data.main_complaint,
            "present_illness": case_data.present_illness,
            "past_history": case_data.past_history,
            "physical_exam": case_data.physical_exam,
            "auxiliary_exams": case_data.auxiliary_exams,
            "diagnosis": case_data.diagnosis,
            "prescription": case_data.prescription
        }

        # 获取标准模板（如果指定了ID）
        standard_template = None
        if case_data.standard_template_id:
            generator = StandardCaseGenerator()
            standard_cases = generator.load_cases()
            for case in standard_cases:
                if case.get("template_id") == case_data.standard_template_id:
                    standard_template = case
                    break

        # 执行评估
        evaluator = QualityEvaluator()
        result = evaluator.assess(case_dict, standard_template)

        return AssessResponse(
            success=True,
            result=result,
            message="评估完成"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"评估失败：{str(e)}"
        )


# List standard cases endpoint
@app.get("/api/v1/list-standards", response_model=ListStandardsResponse)
async def list_standard_cases():
    """
    获取标准病历列表

    返回所有可用的标准病历模板。
    """
    try:
        generator = StandardCaseGenerator()
        standards = generator.load_cases()

        return ListStandardsResponse(
            success=True,
            standards=standards,
            total=len(standards)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取标准病历列表失败：{str(e)}"
        )


# Alternative assessment endpoint with full request model
@app.post("/api/v1/assess/full")
async def assess_quality_full(
    request: AssessRequest
):
    """
    质量评估接口（完整请求模型）

    接收完整的 AssessRequest 对象，支持更多配置选项。
    """
    try:
        case_dict = request.case

        # 获取标准模板
        standard_template = None
        if request.options.get("standard_template_id"):
            generator = StandardCaseGenerator()
            standard_cases = generator.load_cases()
            for case in standard_cases:
                if case.get("template_id") == request.options["standard_template_id"]:
                    standard_template = case
                    break

        # 执行评估
        evaluator = QualityEvaluator()
        result = evaluator.assess(case_dict, standard_template)

        return AssessResponse(
            success=True,
            result=result,
            message="评估完成"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"评估失败：{str(e)}"
        )


# Batch assessment placeholder
@app.post("/api/v1/assess/batch")
async def assess_batch(
    cases: List[CaseData]
):
    """
    批量评估接口（暂未实现）

    批量处理多个病历文件。
    """
    return {
        "success": True,
        "message": "批量评估功能暂未实现，请使用单评估接口",
        "total": len(cases)
    }


# Custom exception handler
@app.exception_handler(Exception)
async def custom_exception_handler(request, exc: Exception):
    """自定义异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"服务器错误：{str(exc)}",
            "code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)

"""
Evaluator API routes for medical record quality assessment.
"""

import os
import sys

# Add parent directory to path for imports (for standalone testing)
父目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 父目录)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from models.evaluator import EvaluationRequest as ModelEvaluationRequest
from models.response import EvaluationResponse as ModelEvaluationResponse
from evaluator import get_default_evaluator, MedicalRecordEvaluator
from utils.batch_processor import get_batch_processor, BatchProcessor
from utils.file_parser import FileParser
from utils.rate_limiter import get_rate_limiter, check_rate_limit
from utils.cache import get_cache_manager

from fastapi.responses import PlainTextResponse, JSONResponse

router = APIRouter()

# Global evaluator instance
_evaluator: Optional[MedicalRecordEvaluator] = None


def get_evaluator() -> MedicalRecordEvaluator:
    """Get or create evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = get_default_evaluator()
    return _evaluator


# Request models (API layer - mirrors model layer but kept separate for flexibility)
class EvaluationRequest(BaseModel):
    """Request model for medical record evaluation."""
    content: str
    template_id: Optional[str] = None
    evaluation_dims: Optional[List[str]] = Field(
        None,
        description="Evaluation dimensions. Options: completeness, logicality, timeliness, normativity. Default: all dimensions."
    )
    model_name: Optional[str] = Field(
        None,
        description="LLM model name to use for evaluation. Defaults to MODEL_NAME from environment."
    )
    provider: Optional[str] = Field(
        None,
        description="LLM provider (openai, dashscope, ernie, local). Defaults to LLM_PROVIDER from environment."
    )


# Response models (API layer - mirrors model layer but kept separate for flexibility)
class Issue(BaseModel):
    """Evaluation issue."""
    dimension: str
    severity: str  # critical, high, medium, low
    description: str
    recommendation: Optional[str] = None


class DimensionScores(BaseModel):
    """Scores for each evaluation dimension."""
    completeness: float
    logicality: float
    timeliness: float
    normativity: float = Field(description="规范性")


class EvaluationResponse(BaseModel):
    """Response model for evaluation result."""
    overall_score: float
    dimension_scores: DimensionScores
    issues: List[Issue]
    recommendations: List[str]


@router.post("/evaluator", response_model=EvaluationResponse)
async def evaluate_record(request: EvaluationRequest):
    """
    Evaluate medical record quality using LLM.

    This endpoint assesses medical records from four dimensions:
    - Completeness (完整性): Basic elements coverage
    - Logicality (逻辑性): Medical logic and reasoning
    - Timeliness (及时性): Timing and time records
    - Normativity (规范性): Formatting and terminology standards

    Args:
        request: EvaluationRequest containing medical record content and optional parameters

    Returns:
        EvaluationResponse with overall score, dimension scores, issues, and recommendations

    Raises:
        HTTPException: If evaluation fails or rate limit exceeded
    """
    # Rate limiting check
    client_id = request.content[:10]  # Simplified client identification
    if not check_rate_limit(client_id):
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试。Rate limit exceeded. Please try again later."
        )

    try:
        # Get evaluator with model configuration from request (or use default)
        from evaluator import get_evaluator_with_model

        if request.model_name or request.provider:
            evaluator = get_evaluator_with_model(
                model_name=request.model_name,
                provider=request.provider,
            )
        else:
            evaluator = get_evaluator()

        cache_manager = get_cache_manager()

        # Generate cache key (include model_name in cache key for model-specific results)
        cache_key = cache_manager.get_cache_key(request.content, {
            "template_id": request.template_id,
            "evaluation_dims": request.evaluation_dims,
            "model_name": request.model_name,
            "provider": request.provider,
        })

        # Try to get from cache
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return EvaluationResponse(
                overall_score=cached_result["overall_score"],
                dimension_scores=DimensionScores(**cached_result["dimension_scores"]),
                issues=[Issue(**issue) for issue in cached_result["issues"]],
                recommendations=cached_result["recommendations"],
            )

        # Convert API request to model request
        model_request = ModelEvaluationRequest(
            content=request.content,
            template_id=request.template_id,
            evaluation_dims=request.evaluation_dims,
        )

        # Perform evaluation
        result = await evaluator.evaluate(model_request)

        # Cache the result
        cache_manager.set(cache_key, {
            "overall_score": result.overall_score,
            "dimension_scores": result.dimension_scores.dict(),
            "issues": [issue.dict() for issue in result.issues],
            "recommendations": result.recommendations,
        })

        # Convert model response to API response
        return EvaluationResponse(
            overall_score=result.overall_score,
            dimension_scores=DimensionScores(
                completeness=result.dimension_scores.completeness,
                logicality=result.dimension_scores.logicality,
                timeliness=result.dimension_scores.timeliness,
                normativity=result.dimension_scores.normativity,
            ),
            issues=[Issue(
                dimension=i.dimension,
                severity=i.severity,
                description=i.description,
                recommendation=i.recommendation
            ) for i in result.issues],
            recommendations=result.recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger = SysLogAdapter()
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/evaluator/status")
async def get_evaluator_status():
    """Get evaluator service status."""
    return {"status": "ready", "service": "Medical Record Inspector"}


@router.get("/evaluator/health")
async def evaluator_health():
    """Get evaluator health check."""
    try:
        evaluator = get_evaluator()
        return {
            "status": "healthy",
            "service": "Medical Record Inspector Evaluator",
            "provider": evaluator.llm_client.provider if hasattr(evaluator, 'llm_client') else "unknown",
            "model": evaluator.llm_client.model_name if hasattr(evaluator, 'llm_client') else "unknown",
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "Medical Record Inspector Evaluator",
            "error": str(e),
        }


class SysLogAdapter:
    """Simple logging adapter for API routes."""

    def error(self, message: str):
        import logging
        logging.error(message)

    def info(self, message: str):
        import logging
        logging.info(message)

    def warning(self, message: str):
        import logging
        logging.warning(message)


# ==================== 批量评估 API ====================

class BatchFileItem(BaseModel):
    """批量评估文件项"""
    filename: str
    content: str


class BatchEvaluationRequest(BaseModel):
    """批量评估请求"""
    files: List[BatchFileItem]
    evaluation_dims: Optional[List[str]] = Field(
        None,
        description="Evaluation dimensions"
    )


class BatchItemResult(BaseModel):
    """批量评估项结果"""
    filename: str
    status: str  # completed, failed
    overall_score: Optional[float] = None
    issues_count: int = 0
    error: Optional[str] = None


class BatchEvaluationResponse(BaseModel):
    """批量评估响应"""
    batch_id: str
    total: int
    completed: int
    failed: int
    status: str
    results: List[BatchItemResult]
    created_at: str


@router.post("/evaluator/batch", response_model=BatchEvaluationResponse)
async def evaluate_batch(request: BatchEvaluationRequest):
    """
    批量评估病历质量

    Args:
        request: BatchEvaluationRequest 包含多个文件

    Returns:
        BatchEvaluationResponse 批量评估结果
    """
    try:
        processor = get_batch_processor()

        # 创建临时文件
        temp_files = []
        for file_item in request.files:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.txt', delete=False, encoding='utf-8'
            ) as f:
                f.write(file_item.content)
                temp_files.append(f.name)

        try:
            # 创建批量任务
            batch = processor.create_batch(temp_files)

            # 异步处理批量任务
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                processor.process_batch(batch.batch_id, request.evaluation_dims)
            )

            # 转换结果
            batch_results = []
            for item in result.items:
                batch_results.append(BatchItemResult(
                    filename=item.filename,
                    status=item.status,
                    overall_score=item.result.get("overall_score") if item.result else None,
                    issues_count=item.result.get("issues_count", 0) if item.result else 0,
                    error=item.error
                ))

            return BatchEvaluationResponse(
                batch_id=result.batch_id,
                total=result.total,
                completed=result.completed,
                failed=result.failed,
                status=result.status,
                results=batch_results,
                created_at=result.created_at
            )

        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception:
                    pass

    except Exception as e:
        logger = SysLogAdapter()
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch evaluation failed: {str(e)}"
        )


@router.get("/evaluator/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    获取批量评估状态

    Args:
        batch_id: 批次 ID

    Returns:
        批量评估状态和结果
    """
    try:
        processor = get_batch_processor()

        # 先尝试从文件加载
        batch = processor.load_batch_from_file(batch_id)

        if batch is None:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

        return {
            "batch_id": batch.batch_id,
            "total": batch.total,
            "completed": batch.completed,
            "failed": batch.failed,
            "status": batch.status,
            "created_at": batch.created_at,
            "completed_at": batch.completed_at,
            "items": [
                {
                    "id": item.id,
                    "filename": item.filename,
                    "status": item.status,
                    "progress": item.progress,
                    "result": item.result,
                    "error": item.error,
                    "created_at": item.created_at,
                    "completed_at": item.completed_at
                }
                for item in batch.items
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger = SysLogAdapter()
        logger.error(f"Get batch status failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Get batch status failed: {str(e)}"
        )


@router.get("/evaluator/batch")
async def list_batches():
    """
    列出所有批量评估任务

    Returns:
        批量评估任务列表
    """
    try:
        processor = get_batch_processor()
        batches = processor.list_batches()

        return {
            "batches": [
                {
                    "batch_id": batch.batch_id,
                    "total": batch.total,
                    "completed": batch.completed,
                    "failed": batch.failed,
                    "status": batch.status,
                    "created_at": batch.created_at,
                    "completed_at": batch.completed_at
                }
                for batch in batches
            ]
        }

    except Exception as e:
        logger = SysLogAdapter()
        logger.error(f"List batches failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"List batches failed: {str(e)}"
        )


# ==================== 报告导出 API ====================

@router.get("/evaluator/export/json")
async def export_json(evaluation_result: EvaluationResponse):
    """
    导出评估结果为 JSON 格式

    Args:
        evaluation_result: 评估结果对象

    Returns:
        JSONResponse: JSON 格式的评估结果
    """
    return JSONResponse(content=evaluation_result.dict())


@router.get("/evaluator/export/md")
async def export_markdown(evaluation_result: EvaluationResponse):
    """
    导出评估结果为 Markdown 格式

    Args:
        evaluation_result: 评估结果对象

    Returns:
        PlainTextResponse: Markdown 格式的评估结果
    """
    md_lines = [
        f"# 病历质量评估报告",
        "",
        f"## 总体评分",
        "",
        f"**得分：{evaluation_result.overall_score:.1f} / 100**",
        "",
    ]

    # 维度评分
    md_lines.extend([
        "## 维度评分",
        "",
        "| 维度 | 得分 |",
        "|------|------|",
        f"| 完整性 | {evaluation_result.dimension_scores.completeness:.1f} |",
        f"| 逻辑性 | {evaluation_result.dimension_scores.logicality:.1f} |",
        f"| 及时性 | {evaluation_result.dimension_scores.timeliness:.1f} |",
        f"| 规范性 | {evaluation_result.dimension_scores.normativity:.1f} |",
        "",
    ])

    # 问题列表
    md_lines.extend([
        f"## 发现问题 ({len(evaluation_result.issues)} 个)",
        "",
    ])

    if evaluation_result.issues:
        for i, issue in enumerate(evaluation_result.issues, 1):
            md_lines.extend([
                f"### {i}. [{issue.severity.upper()}] {issue.dimension}",
                "",
                f"{issue.description}",
                "",
            ])
            if issue.recommendation:
                md_lines.extend([
                    f"**建议：** {issue.recommendation}",
                    "",
                ])
    else:
        md_lines.append("无问题发现。")
        md_lines.append("")

    # 改进建议
    if evaluation_result.recommendations:
        md_lines.extend([
            "## 改进建议",
            "",
        ])
        for i, rec in enumerate(evaluation_result.recommendations, 1):
            md_lines.append(f"{i}. {rec}")
        md_lines.append("")

    md_lines.extend([
        f"---",
        f"*生成时间：{evaluation_result.created_at if hasattr(evaluation_result, 'created_at') else 'N/A'}*"
    ])

    return PlainTextResponse(content='\n'.join(md_lines))


# PDF 导出依赖（可选）
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    pdfmetrics = None
    colors = None
    A4 = None
    canvas = None
    TTFont = None


@router.get("/evaluator/export/pdf")
async def export_pdf(evaluation_result: EvaluationResponse):
    """
    导出评估结果为 PDF 格式

    Args:
        evaluation_result: 评估结果对象

    Returns:
        PDF 文件下载
    """
    if not PDF_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF 导出需要 reportlab 库。请运行: pip install reportlab"
        )

    try:
        # 创建临时 PDF 文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
            c = canvas.Canvas(tmp_file, pagesize=A4)
            width, height = A4

            # 标题
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, height - 50, "病历质量评估报告")

            # 总体评分
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 100, "总体评分")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 120, f"得分：{evaluation_result.overall_score:.1f} / 100")

            # 维度评分
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 160, "维度评分")
            c.setFont("Helvetica", 10)

            y_pos = height - 180
            dimensions = [
                ("完整性", evaluation_result.dimension_scores.completeness),
                ("逻辑性", evaluation_result.dimension_scores.logicality),
                ("及时性", evaluation_result.dimension_scores.timeliness),
                ("规范性", evaluation_result.dimension_scores.normativity),
            ]

            for dim_name, dim_score in dimensions:
                c.drawString(50, y_pos, f"{dim_name}: {dim_score:.1f}")
                y_pos -= 20

            # 问题列表
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_pos, "发现问题")
            y_pos -= 20

            c.setFont("Helvetica", 9)
            for issue in evaluation_result.issues:
                if y_pos < 50:  # 新页面
                    c.showPage()
                    y_pos = height - 50
                    c.setFont("Helvetica", 9)

                severity_color = {
                    'critical': colors.red,
                    'high': colors.orange,
                    'medium': colors.yellow,
                    'low': colors.green,
                }.get(issue.severity, colors.black)

                c.setFillColor(severity_color)
                c.drawString(50, y_pos, f"[{issue.severity.upper()}] {issue.dimension}")
                y_pos -= 15
                c.setFillColor(colors.black)
                c.drawString(70, y_pos, issue.description[:80])
                y_pos -= 20

                if issue.recommendation:
                    c.setFillColor(colors.blue)
                    c.drawString(70, y_pos, f"建议: {issue.recommendation[:60]}")
                    y_pos -= 20
                    c.setFillColor(colors.black)

            # 改进建议
            if evaluation_result.recommendations:
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y_pos, "改进建议")
                y_pos -= 20

                c.setFont("Helvetica", 9)
                for i, rec in enumerate(evaluation_result.recommendations, 1):
                    if y_pos < 50:
                        c.showPage()
                        y_pos = height - 50
                        c.setFont("Helvetica", 9)
                    c.drawString(50, y_pos, f"{i}. {rec[:90]}")
                    y_pos -= 15

            # 保存 PDF
            c.save()

        # 读取生成的 PDF 文件
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        # 删除临时文件
        os.unlink(pdf_path)

        # 返回 PDF 响应
        from fastapi.responses import Response
        return Response(
            content=pdf_content,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="evaluation_report.pdf"'}
        )

    except Exception as e:
        logger = SysLogAdapter()
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF export failed: {str(e)}"
        )


# 导入必要的模块（放在底部以避免循环引用）
import logging


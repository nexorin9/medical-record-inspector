"""
Web API 服务 - Medical Record Inspector
FastAPI Web 服务，支持病历检测 API 调用
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 添加 src 的父目录到路径，这样可以正确导入 src 模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.inspector import create_inspector, MedicalRecordInspector
from src.logger import get_logger

logger = get_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Medical Record Inspector API",
    description="病历质控 API 服务",
    version="1.0.0"
)

# 全局 Inspector 实例
_inspector: Optional[MedicalRecordInspector] = None


class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    text: str = Field(..., description="病历文本")
    template: Optional[str] = Field(None, description="模板名称")


class AnalyzeResponse(BaseModel):
    """分析响应模型"""
    overall_score: float = Field(description="总体相似度分数")
    template_used: Optional[str] = Field(None, description="使用的模板名称")
    defect_count: int = Field(description="缺陷数量")
    defects: List[Dict] = Field(description="缺陷详情")
    paragraph_analysis: Dict = Field(description="段落分析")
    chunk_analysis: Dict = Field(description="分块分析")
    defect_map: Dict = Field(description="缺陷热力图")


class TemplateInfo(BaseModel):
    """模板信息模型"""
    name: str = Field(description="模板名称")
    type: str = Field(description="模板类型")
    department: str = Field(description="科室")
    year: int = Field(description="年份")
    score: float = Field(description="质量评分")
    length: int = Field(description="文本长度（字符数）")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(default="healthy")


def get_inspector() -> MedicalRecordInspector:
    """获取 Inspector 实例"""
    global _inspector
    if _inspector is None:
        template_dir = os.environ.get('TEMPLATE_DIR', 'templates')
        _inspector = create_inspector(template_dir)
    return _inspector


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


@app.get("/templates", response_model=List[TemplateInfo], tags=["Templates"])
async def list_templates():
    """列出所有可用模板"""
    try:
        inspector = get_inspector()
        templates = inspector.get_template_list()
        return templates
    except Exception as e:
        logger.error(f"获取模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_record(request: AnalyzeRequest):
    """
    分析单个病历
    """
    try:
        inspector = get_inspector()
        result = inspector.analyze(request.text, request.template)
        return result
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-batch", response_model=Dict[str, Any], tags=["Analysis"])
async def analyze_batch(records: List[AnalyzeRequest]):
    """
    批量分析病历
    """
    try:
        inspector = get_inspector()

        # 如果指定了模板，对所有记录使用相同模板
        template_name = None
        if records and records[0].template:
            template_name = records[0].template

        results = []
        for record in records:
            result = inspector.analyze(record.text, template_name or record.template)
            results.append(result)

        return {
            "total": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/single", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_record_query(
    text: str = Query(..., description="病历文本"),
    template: Optional[str] = Query(None, description="模板名称")
):
    """
    分析单个病历（GET 方式，使用查询参数）
    """
    try:
        inspector = get_inspector()
        result = inspector.analyze(text, template)
        return result
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status", tags=["System"])
async def status():
    """系统状态"""
    return {
        "status": "running",
        "templates_loaded": _inspector is not None,
        "template_count": len(_inspector.get_template_list()) if _inspector else 0
    }


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    global _inspector
    _inspector = None


def main():
    """启动服务"""
    import argparse

    parser = argparse.ArgumentParser(description="启动 Medical Record Inspector API 服务")
    parser.add_argument('--host', '-H', default='0.0.0.0', help='绑定的主机地址')
    parser.add_argument('--port', '-p', type=int, default=8000, help='端口号')
    parser.add_argument('--reload', action='store_true', help='开发模式（自动重载）')
    args = parser.parse_args()

    print(f"Starting Medical Record Inspector API on {args.host}:{args.port}")
    print("Available endpoints:")
    print("  GET  /health              - 健康检查")
    print("  GET  /templates           - 列出模板")
    print("  POST /analyze             - 分析病历 (JSON body)")
    print("  GET  /analyze/single      - 分析病历 (query arg)")
    print("  POST /analyze-batch       - 批量分析")

    uvicorn.run("src.api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

"""
评估请求模型 - Evaluation Request Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class EvaluationRequest(BaseModel):
    """
    病历评估请求模型

    Attributes:
        content (str): 病历文本内容
        template_id (Optional[str]): 模板ID，可选用于对比评估
        evaluation_dims (Optional[List[str]]): 评估维度列表，可选
            可选值: ["completeness", "logicality", "timeliness", "normativity"]
    """
    content: str = Field(..., description="病历文本内容")
    template_id: Optional[str] = Field(None, description="高质量模板ID，用于对比评估")
    evaluation_dims: Optional[List[str]] = Field(
        None,
        description="评估维度列表，默认评估所有维度"
    )

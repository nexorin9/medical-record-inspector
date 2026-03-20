"""
模板模型 - Template Models
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class Template(BaseModel):
    """
    病历模板模型

    Attributes:
        id (str): 模板唯一标识符，自动生成
        name (str): 模板名称
        description (str): 模板描述
        content (str): 模板内容（高质量病历文本）
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
        version (int): 模板版本号
        tags (Optional[List[str]]): 模板标签，用于分类
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="模板唯一标识符")
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: str = Field(..., min_length=1, max_length=500, description="模板描述")
    content: str = Field(..., min_length=1, description="模板内容（高质量病历文本）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    version: int = Field(default=1, ge=1, description="模板版本号")
    tags: Optional[list] = Field(default_factory=list, description="模板标签")

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

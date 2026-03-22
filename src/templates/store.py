"""
模板存储 - Template Store
"""
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.template import Template
from models import create_empty_response


class TemplateStore:
    """
    模板存储类，使用 JSON 文件持久化模板数据

    Attributes:
        storage_path (Path): 存储文件路径，默认为 data/templates.json
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化模板存储

        Args:
            storage_path (Optional[str]): 存储文件路径
        """
        if storage_path is None:
            # 默认路径：项目根目录/data/templates.json
            self.storage_path = Path(__file__).parent.parent.parent / "data" / "templates.json"
        else:
            self.storage_path = Path(storage_path)

        # 确保数据目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果文件不存在，初始化空文件
        if not self.storage_path.exists():
            self._save({})

    def _load(self) -> Dict:
        """加载存储数据"""
        with open(self.storage_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict) -> None:
        """保存数据到文件"""

        def json_serializable(obj):
            """Convert datetime to ISO format string for JSON serialization"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializable)

    def save_template(self, template: Template) -> Template:
        """
        保存模板（如果存在则更新版本）

        Args:
            template (Template): 要保存的模板对象

        Returns:
            Template: 保存后的模板对象（包含ID）
        """
        data = self._load()

        # 如果是新模板，生成新ID
        if not template.id:
            template.id = str(uuid.uuid4())[:8]  # 简短ID
            template.created_at = datetime.utcnow()
            template.version = 1
        else:
            # 检查是否是新版本
            if template.id in data:
                old_template = self._parse_template(data[template.id])
                template.version = old_template.version + 1
                template.created_at = old_template.created_at

        template.updated_at = datetime.utcnow()

        # 保存模板数据
        data[template.id] = template.model_dump()

        self._save(data)
        return template

    def get_template(self, template_id: str) -> Optional[Template]:
        """
        获取模板

        Args:
            template_id (str): 模板ID

        Returns:
            Optional[Template]: 模板对象，不存在返回 None
        """
        data = self._load()

        if template_id in data:
            return self._parse_template(data[template_id])

        return None

    def list_templates(self, limit: int = 100, offset: int = 0) -> List[Template]:
        """
        列出模板

        Args:
            limit (int): 返回数量限制
            offset (int): 偏移量

        Returns:
            List[Template]: 模板列表，按更新时间倒序排列
        """
        data = self._load()

        templates = []
        for template_id, template_data in data.items():
            template = self._parse_template(template_data)
            templates.append(template)

        # 按更新时间倒序排序
        templates.sort(key=lambda t: t.updated_at, reverse=True)

        return templates[offset:offset + limit]

    def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id (str): 模板ID

        Returns:
            bool: 删除是否成功
        """
        data = self._load()

        if template_id in data:
            del data[template_id]
            self._save(data)
            return True

        return False

    def template_exists(self, template_id: str) -> bool:
        """
        检查模板是否存在

        Args:
            template_id (str): 模板ID

        Returns:
            bool: 模板是否存在
        """
        data = self._load()
        return template_id in data

    def _parse_template(self, data: Dict) -> Template:
        """
        从字典解析模板对象

        Args:
            data (Dict): 模板数据字典

        Returns:
            Template: 模板对象
        """
        # 处理日期字段
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return Template(**data)

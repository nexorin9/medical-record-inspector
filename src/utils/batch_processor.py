"""
批量评估处理器 - Batch Processor
支持批量文件评估和进度追踪
"""

import asyncio
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Add parent directory to path for imports (to access root-level modules)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluator import get_default_evaluator, MedicalRecordEvaluator
from models.evaluator import EvaluationRequest
from models.response import EvaluationResponse


class BatchStatus(str, Enum):
    """批量评估状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # 部分成功


@dataclass
class BatchItem:
    """批量评估项"""
    id: str
    filename: str
    file_path: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


@dataclass
class BatchResult:
    """批量评估结果"""
    batch_id: str
    total: int
    completed: int
    failed: int
    status: str  # pending, processing, completed, failed, partial
    items: List[BatchItem]
    created_at: str
    completed_at: Optional[str] = None


class BatchProcessor:
    """
    批量评估处理器

    支持：
    - 批量文件评估
    - 进度追踪
    - 异步处理
    - 结果缓存
    """

    def __init__(self, evaluator: Optional[MedicalRecordEvaluator] = None):
        """
        初始化批量处理器

        Args:
            evaluator: 评估器实例，如未提供则使用默认实例
        """
        self.evaluator = evaluator or get_default_evaluator()
        self.batches: Dict[str, BatchResult] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.storage_path = Path(tempfile.gettempdir()) / "medical_record_batch_cache"

        # 创建存储目录
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_batch(self, file_paths: List[str], batch_id: Optional[str] = None) -> BatchResult:
        """
        创建批量评估任务

        Args:
            file_paths: 文件路径列表
            batch_id: 批次 ID，如未提供则自动生成

        Returns:
            BatchResult: 批量评估结果对象
        """
        if batch_id is None:
            batch_id = self._generate_batch_id(file_paths)

        # 创建评估请求
        items = []
        for file_path in file_paths:
            item = BatchItem(
                id=self._generate_item_id(file_path),
                filename=os.path.basename(file_path),
                file_path=file_path,
                status=BatchStatus.PENDING.value,
                progress=0
            )
            items.append(item)

        batch = BatchResult(
            batch_id=batch_id,
            total=len(file_paths),
            completed=0,
            failed=0,
            status=BatchStatus.PENDING.value,
            items=items,
            created_at=datetime.utcnow().isoformat()
        )

        self.batches[batch_id] = batch
        self._save_batch(batch_id)

        return batch

    async def process_batch(
        self,
        batch_id: str,
        dims: Optional[List[str]] = None
    ) -> BatchResult:
        """
        处理批量评估任务

        Args:
            batch_id: 批次 ID
            dims: 评估维度列表，如未提供则使用默认维度

        Returns:
            BatchResult: 处理完成的批量评估结果
        """
        if batch_id not in self.batches:
            raise ValueError(f"Batch {batch_id} not found")

        batch = self.batches[batch_id]
        batch.status = BatchStatus.PROCESSING.value
        self._save_batch(batch_id)

        # 异步处理所有文件
        tasks = []
        for item in batch.items:
            if item.status == BatchStatus.PENDING.value:
                task = asyncio.create_task(
                    self._process_item(item.id, batch_id, dims)
                )
                tasks.append(task)

        self.processing_tasks[batch_id] = asyncio.gather(*tasks)

        # 等待所有任务完成
        await self.processing_tasks[batch_id]

        # 更新批量状态
        completed = sum(1 for item in batch.items if item.status == BatchStatus.COMPLETED.value)
        failed = sum(1 for item in batch.items if item.status == BatchStatus.FAILED.value)

        batch.completed = completed
        batch.failed = failed

        if failed == 0:
            batch.status = BatchStatus.COMPLETED.value
        elif completed > 0:
            batch.status = BatchStatus.PARTIAL.value
        else:
            batch.status = BatchStatus.FAILED.value

        batch.completed_at = datetime.utcnow().isoformat()
        self._save_batch(batch_id)

        return batch

    async def _process_item(
        self,
        item_id: str,
        batch_id: str,
        dims: Optional[List[str]]
    ) -> None:
        """
        处理单个评估项

        Args:
            item_id: 评估项 ID
            batch_id: 批次 ID
            dims: 评估维度列表
        """
        batch = self.batches[batch_id]
        item = next((i for i in batch.items if i.id == item_id), None)

        if not item:
            return

        item.status = BatchStatus.PROCESSING.value
        item.progress = 10
        self._save_batch(batch_id)

        try:
            # 读取文件内容
            text_content = self._read_file_content(item.file_path)

            if not text_content or len(text_content.strip()) < 10:
                raise ValueError("文件内容太短或无法提取文本")

            # 创建评估请求
            request = EvaluationRequest(
                content=text_content,
                evaluation_dims=dims if dims else None
            )

            # 执行评估
            result = await self.evaluator.evaluate(request)

            item.status = BatchStatus.COMPLETED.value
            item.progress = 100
            item.result = {
                "overall_score": result.overall_score,
                "dimension_scores": asdict(result.dimension_scores),
                "issues_count": len(result.issues),
                "recommendations_count": len(result.recommendations)
            }
            item.completed_at = datetime.utcnow().isoformat()

        except Exception as e:
            item.status = BatchStatus.FAILED.value
            item.progress = 0
            item.error = str(e)
            item.completed_at = datetime.utcnow().isoformat()

        self._save_batch(batch_id)

    def _read_file_content(self, file_path: str) -> str:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件文本内容
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.docx':
            return self._read_docx(file_path)
        elif ext == '.pdf':
            return self._read_pdf(file_path)
        else:
            # 文本文件
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

    def _read_docx(self, file_path: str) -> str:
        """读取 DOCX 文件"""
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text.strip())
            return '\n'.join(paragraphs)
        except ImportError:
            raise ImportError("请安装 python-docx: pip install python-docx")

    def _read_pdf(self, file_path: str) -> str:
        """读取 PDF 文件"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append(text.strip())
                return '\n'.join(pages)
        except ImportError:
            raise ImportError("请安装 PyPDF2: pip install PyPDF2")

    def get_batch(self, batch_id: str) -> Optional[BatchResult]:
        """
        获取批量评估结果

        Args:
            batch_id: 批次 ID

        Returns:
            BatchResult: 批量评估结果
        """
        return self.batches.get(batch_id)

    def list_batches(self) -> List[BatchResult]:
        """
        获取所有批量评估任务

        Returns:
            List[BatchResult]: 批量评估结果列表
        """
        return list(self.batches.values())

    def delete_batch(self, batch_id: str) -> bool:
        """
        删除批量评估任务

        Args:
            batch_id: 批次 ID

        Returns:
            bool: 删除是否成功
        """
        if batch_id in self.batches:
            del self.batches[batch_id]
            self._delete_batch_file(batch_id)
            return True
        return False

    def _generate_batch_id(self, file_paths: List[str]) -> str:
        """生成批次 ID"""
        file_names = sorted([os.path.basename(p) for p in file_paths])
        content = '|'.join(file_names)
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_item_id(self, file_path: str) -> str:
        """生成评估项 ID"""
        content = os.path.basename(file_path) + datetime.utcnow().isoformat()
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _save_batch(self, batch_id: str) -> None:
        """保存批次到文件"""
        if batch_id in self.batches:
            file_path = self.storage_path / f"{batch_id}.json"
            data = asdict(self.batches[batch_id])
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _delete_batch_file(self, batch_id: str) -> None:
        """删除批次文件"""
        file_path = self.storage_path / f"{batch_id}.json"
        if file_path.exists():
            file_path.unlink()

    def load_batch_from_file(self, batch_id: str) -> Optional[BatchResult]:
        """从文件加载批次"""
        file_path = self.storage_path / f"{batch_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return BatchResult(**data)
        return None


# 全局单例
_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor() -> BatchProcessor:
    """获取全局批量处理器实例"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor

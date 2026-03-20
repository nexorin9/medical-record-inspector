"""
Batch Evaluation Engine for Medical Record Inspector.

This module provides batch processing functionality for evaluating multiple cases.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading

from api.evaluator import QualityEvaluator
from api.models import QualityAssessment, BatchResponse
from api.logger import get_logger

logger = get_logger(__name__)


class BatchEvaluator:
    """批量评估器"""

    def __init__(self, max_workers: int = 4):
        """
        初始化批量评估器。

        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers
        self.evaluator = QualityEvaluator()
        self.results = []
        self.lock = threading.Lock()

    def process_single_file(self, filepath: str) -> Dict[str, Any]:
        """
        处理单个文件。

        Args:
            filepath: 文件路径

        Returns:
            处理结果字典
        """
        result = {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "success": False,
            "assessment": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # 读取文件
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.endswith('.json'):
                    case_data = json.load(f)
                else:
                    # 其他格式（如txt），尝试解析JSON
                    content = f.read()
                    case_data = json.loads(content)

            # 执行评估
            assessment = self.evaluator.assess(case_data)
            result["success"] = True
            result["assessment"] = {
                "assessment_id": assessment.assessment_id,
                "overall_score": assessment.scores.overall_score,
                "issues_count": len(assessment.issues),
                "issues": [
                    {
                        "category": i.category,
                        "severity": i.severity,
                        "description": i.description
                    }
                    for i in assessment.issues
                ]
            }

        except json.JSONDecodeError as e:
            result["error"] = f"JSON 解析错误: {str(e)}"
        except Exception as e:
            result["error"] = f"处理失败: {str(e)}"

        return result

    def process_directory(
        self,
        directory: str,
        file_extensions: List[str] = None
    ) -> BatchResponse:
        """
        批量处理目录中的文件。

        Args:
            directory: 目录路径
            file_extensions: 文件扩展名列表

        Returns:
            BatchResponse 批量评估响应
        """
        if file_extensions is None:
            file_extensions = [".json", ".txt"]

        dir_path = Path(directory)

        if not dir_path.exists():
            return BatchResponse(
                success=False,
                total=0,
                successful=0,
                failed=0,
                results=[],
                summary={"error": f"目录不存在: {directory}"}
            )

        # 查找所有匹配的文件
        files = []
        for ext in file_extensions:
            files.extend(dir_path.glob(f"*{ext}"))

        files = list(files)
        total = len(files)

        if total == 0:
            return BatchResponse(
                success=False,
                total=0,
                successful=0,
                failed=0,
                results=[],
                summary={"error": f"未找到匹配的文件: {directory}"}
            )

        self.results = []
        successful = 0
        failed = 0

        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_single_file, str(f)): f
                for f in files
            }

            for future in as_completed(futures):
                result = future.result()
                with self.lock:
                    self.results.append(result)
                    if result["success"]:
                        successful += 1
                    else:
                        failed += 1

        # 计算平均分数
        scores = [r["assessment"]["overall_score"] for r in self.results if r["success"]]
        avg_score = sum(scores) / len(scores) if scores else 0

        return BatchResponse(
            success=True,
            total=total,
            successful=successful,
            failed=failed,
            results=self.results,
            summary={
                "average_score": round(avg_score, 2),
                "processing_time": f"{datetime.now().isoformat()}"
            }
        )

    def process_files_async(
        self,
        filepaths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        异步处理多个文件。

        Args:
            filepaths: 文件路径列表

        Returns:
            处理结果列表
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def process_all():
            tasks = [self._process_single_async(fp) for fp in filepaths]
            return await asyncio.gather(*tasks)

        results = loop.run_until_complete(process_all())
        loop.close()
        return results

    async def _process_single_async(self, filepath: str) -> Dict[str, Any]:
        """
        异步处理单个文件。

        Args:
            filepath: 文件路径

        Returns:
            处理结果字典
        """
        # 异步版本需要使用异步HTTP客户端
        # 这里使用线程池模拟异步
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process_single_file, filepath)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取汇总统计。

        Returns:
            汇总统计字典
        """
        if not self.results:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "error_rate": 0
            }

        successful = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - successful

        scores = [
            r["assessment"]["overall_score"]
            for r in self.results
            if r["success"] and r["assessment"]
        ]

        return {
            "total": len(self.results),
            "successful": successful,
            "failed": failed,
            "error_rate": round(failed / len(self.results) * 100, 2),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0
        }


def batch_evaluate(
    directory: str = None,
    files: List[str] = None,
    max_workers: int = 4
) -> BatchResponse:
    """
    批量评估的便捷函数。

    Args:
        directory: 目录路径
        files: 文件路径列表
        max_workers: 最大并发数

    Returns:
        BatchResponse 批量评估响应
    """
    evaluator = BatchEvaluator(max_workers=max_workers)

    if directory:
        return evaluator.process_directory(directory)
    elif files:
        return evaluator.process_directory(
            os.path.dirname(files[0]) if files else ".",
            file_extensions=[]
        )
    else:
        return BatchResponse(
            success=False,
            total=0,
            successful=0,
            failed=0,
            results=[],
            summary={"error": "未指定目录或文件"}
        )


if __name__ == "__main__":
    import sys

    # 测试批量评估
    if len(sys.argv) < 2:
        print("用法: python batch_engine.py <directory> [max_workers]")
        sys.exit(1)

    directory = sys.argv[1]
    max_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    evaluator = BatchEvaluator(max_workers=max_workers)

    print(f"开始批量评估目录: {directory}")
    print(f"并发数: {max_workers}")
    print("-" * 60)

    response = evaluator.process_directory(directory)

    print(f"\n评估完成!")
    print(f"总计: {response.total}")
    print(f"成功: {response.successful}")
    print(f"失败: {response.failed}")

    if response.successful > 0:
        print(f"平均评分: {response.summary.get('average_score', 0)}")

    # 输出每个文件的结果
    print("\n详细结果:")
    for result in response.results:
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {result['filename']}")
        if result["success"]:
            print(f"      评分: {result['assessment']['overall_score']}")
            print(f"      问题数: {result['assessment']['issues_count']}")

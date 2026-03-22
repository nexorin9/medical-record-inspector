"""
Batch Processing Engine for Medical Record Inspector.

This module provides async batch processing capabilities for evaluating
multiple medical records efficiently.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from api.performance import PerformanceEvaluator, token_tracker
from api.models import QualityAssessment, QualityScore, Issue

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class AsyncBatchEvaluator:
    """
    异步批量评估器。

    提供以下功能：
    - 并发处理多个病历
    - 异步 LLM 调用
    - 进度跟踪
    - 错误处理
    - 资源管理
    """

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "claude-3-5-sonnet-20240620",
        max_concurrent: int = 4,
        timeout: float = 60.0,
        max_retries: int = 2
    ):
        """
        初始化批量评估器。

        Args:
            api_key: Anthropic API key
            model_name: LLM 模型名称
            max_concurrent: 最大并发数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model_name
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries

        self._evaluator = PerformanceEvaluator(
            api_key=api_key,
            model_name=model_name,
            max_retries=max_retries,
            timeout=timeout
        )
        self._lock = threading.Lock()
        self._progress = 0
        self._total = 0

    async def evaluate_single_async(
        self,
        case: Dict,
        standard_template: Dict = None
    ) -> QualityAssessment:
        """
        异步评估单个病历。

        Args:
            case: 待评估病历
            standard_template: 标准病历模板

        Returns:
            评估结果
        """
        return await asyncio.to_thread(
            self._evaluator.assess, case, standard_template
        )

    async def evaluate_batch_async(
        self,
        cases: List[Dict],
        standard_template: Dict = None,
        on_progress: callable = None
    ) -> List[QualityAssessment]:
        """
        异步批量评估病历（使用 asyncio.gather 并发）。

        Args:
            cases: 待评估病历列表
            standard_template: 标准病历模板
            on_progress: 进度回调函数

        Returns:
            评估结果列表
        """
        self._total = len(cases)
        self._progress = 0

        results = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def evaluate_with_semaphore(case: Dict) -> QualityAssessment:
            async with semaphore:
                try:
                    result = await self.evaluate_single_async(case, standard_template)
                    with self._lock:
                        self._progress += 1
                        progress = self._progress
                    if on_progress:
                        on_progress(progress, self._total)
                    return result
                except Exception as e:
                    return QualityAssessment(
                        assessment_id=f"FAILED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        patient_id=case.get("patient_id"),
                        visit_id=case.get("visit_id"),
                        scores=QualityScore(
                            completeness_score=0,
                            consistency_score=0,
                            timeliness_score=0,
                            standardization_score=0,
                            overall_score=0
                        ),
                        issues=[],
                        report=f"评估失败：{str(e)}",
                        标注时间=datetime.now(),
                        standard_template_id=None
                    )

        # 创建任务列表
        tasks = [evaluate_with_semaphore(case) for case in cases]

        # 并发执行所有任务
        results = await asyncio.gather(*tasks)

        return results

    def evaluate_batch_threaded(
        self,
        cases: List[Dict],
        standard_template: Dict = None,
        on_progress: callable = None
    ) -> List[QualityAssessment]:
        """
        使用线程池批量评估（适用于同步环境）。

        Args:
            cases: 待评估病历列表
            standard_template: 标准病历模板
            on_progress: 进度回调函数

        Returns:
            评估结果列表
        """
        self._total = len(cases)
        self._progress = 0

        results = []

        def evaluate_single(case: Dict) -> QualityAssessment:
            try:
                result = self._evaluator.assess(case, standard_template)
                with self._lock:
                    self._progress += 1
                    progress = self._progress
                if on_progress:
                    on_progress(progress, self._total)
                return result
            except Exception as e:
                return QualityAssessment(
                    assessment_id=f"FAILED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    patient_id=case.get("patient_id"),
                    visit_id=case.get("visit_id"),
                    scores=QualityScore(
                        completeness_score=0,
                        consistency_score=0,
                        timeliness_score=0,
                        standardization_score=0,
                        overall_score=0
                    ),
                    issues=[],
                    report=f"评估失败：{str(e)}",
                    标注时间=datetime.now(),
                    standard_template_id=None
                )

        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {executor.submit(evaluate_single, case): case for case in cases}

            for future in as_completed(futures):
                results.append(future.result())

        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取评估统计信息"""
        perf_stats = self._evaluator.get_performance_stats()
        return {
            **perf_stats,
            "current_progress": self._progress,
            "total_tasks": self._total,
            "token_tracker": token_tracker.get_stats()
        }

    def reset(self):
        """重置评估器状态"""
        self._progress = 0
        self._total = 0
        self._evaluator.reset_stats()


class BatchFileProcessor:
    """
    批量文件处理器。

    处理目录中的病历文件并进行批量评估。
    """

    def __init__(
        self,
        evaluator: AsyncBatchEvaluator,
        standard_template: Dict = None
    ):
        """
        初始化文件处理器。

        Args:
            evaluator: 批量评估器实例
            standard_template: 标准病历模板
        """
        self.evaluator = evaluator
        self.standard_template = standard_template
        self.results = []
        self.errors = []

    def process_directory(
        self,
        directory: str,
        extensions: List[str] = None,
        on_progress: callable = None
    ) -> Dict[str, Any]:
        """
        处理目录中的所有病历文件。

        Args:
            directory: 文件目录路径
            extensions: 要处理的文件扩展名
            on_progress: 进度回调函数

        Returns:
            处理结果字典
        """
        if extensions is None:
            extensions = [".json", ".txt"]

        dir_path = Path(directory)
        if not dir_path.exists():
            return {"error": f"Directory not found: {directory}"}

        files = []
        for ext in extensions:
            files.extend(dir_path.glob(f"*{ext}"))

        if not files:
            return {"error": f"No files found with extensions {extensions}"}

        # 读取病历数据
        cases = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 尝试解析 JSON
                try:
                    case_data = json.loads(content)
                except json.JSONDecodeError:
                    # 如果不是 JSON，创建最小病历结构
                    case_data = {
                        "main_complaint": content[:100],
                        "present_illness": content,
                        "diagnosis": "未知",
                        "prescription": "未知"
                    }

                case_data["source_file"] = str(file_path)
                cases.append(case_data)
            except Exception as e:
                self.errors.append({
                    "file": str(file_path),
                    "error": str(e)
                })

        if not cases:
            return {"error": "No valid cases found"}

        # 异步执行批量评估
        import asyncio
        results = asyncio.run(
            self.evaluator.evaluate_batch_async(
                cases, self.standard_template, on_progress
            )
        )

        self.results = results
        return {
            "total_files": len(files),
            "valid_cases": len(cases),
            "results": results,
            "errors": self.errors
        }

    def process_file(self, file_path: str) -> QualityAssessment:
        """
        处理单个文件。

        Args:
            file_path: 文件路径

        Returns:
            评估结果
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            case_data = json.loads(content)
        except json.JSONDecodeError:
            case_data = {
                "main_complaint": content[:100],
                "present_illness": content,
                "diagnosis": "未知",
                "prescription": "未知"
            }

        case_data["source_file"] = file_path
        return self.evaluator._evaluator.assess(case_data, self.standard_template)


# ============================================================================
# Convenience Functions
# ============================================================================

def batch_evaluate(
    cases: List[Dict],
    api_key: str = None,
    model_name: str = "claude-3-5-sonnet-20240620",
    max_concurrent: int = 4,
    use_async: bool = True
) -> List[QualityAssessment]:
    """
    便捷的批量评估函数。

    Args:
        cases: 待评估病历列表
        api_key: API 密钥
        model_name: 模型名称
        max_concurrent: 最大并发数
        use_async: 是否使用异步

    Returns:
        评估结果列表
    """
    evaluator = AsyncBatchEvaluator(
        api_key=api_key,
        model_name=model_name,
        max_concurrent=max_concurrent
    )

    if use_async:
        import asyncio
        return asyncio.run(evaluator.evaluate_batch_async(cases))
    else:
        return evaluator.evaluate_batch_threaded(cases)


def batch_evaluate_files(
    directory: str,
    api_key: str = None,
    model_name: str = "claude-3-5-sonnet-20240620",
    max_concurrent: int = 4,
    extensions: List[str] = None
) -> Dict[str, Any]:
    """
    便捷的批量文件评估函数。

    Args:
        directory: 文件目录
        api_key: API 密钥
        model_name: 模型名称
        max_concurrent: 最大并发数
        extensions: 文件扩展名

    Returns:
        处理结果
    """
    evaluator = AsyncBatchEvaluator(
        api_key=api_key,
        model_name=model_name,
        max_concurrent=max_concurrent
    )
    processor = BatchFileProcessor(evaluator)

    return processor.process_directory(directory, extensions)


if __name__ == "__main__":
    # 简单测试
    test_cases = [
        {
            "patient_id": f"PAT{i:03d}",
            "visit_id": f"VIS{i:03d}",
            "department": "内科",
            "case_type": "门诊",
            "main_complaint": f"咳嗽{i}天",
            "present_illness": f"患者{i}天前受凉后出现咳嗽",
            "past_history": "无特殊",
            "physical_exam": "双肺呼吸音清",
            "auxiliary_exams": "血常规正常",
            "diagnosis": "急性支气管炎",
            "prescription": "阿莫西林 0.5g tid"
        }
        for i in range(1, 6)
    ]

    print(f"测试批量评估 {len(test_cases)} 个病历...")

    import asyncio

    async def main():
        evaluator = AsyncBatchEvaluator(max_concurrent=2)
        results = await evaluator.evaluate_batch_async(test_cases)

        print(f"\n评估结果:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. 评分: {result.scores.overall_score} - {result.assessment_id}")

        print(f"\n性能统计:")
        print(f"  {evaluator.get_stats()}")

    asyncio.run(main())

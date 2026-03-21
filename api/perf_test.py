"""
Performance Test Suite for Medical Record Inspector.

This module provides performance testing capabilities for the quality
evaluation system.
"""

import asyncio
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import statistics

from api.performance import PerformanceEvaluator, token_tracker, assess_case_optimized
from api.batch_optimizer import AsyncBatchEvaluator, batch_evaluate
from api.models import QualityAssessment

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class PerformanceTestSuite:
    """
    性能测试套件。

    提供以下测试：
    - 单次评估响应时间
    - 批量评估吞吐量
    - 并发性能测试
    - Token 使用统计
    """

    def __init__(self, api_key: str = None, model_name: str = "claude-3-5-sonnet-20240620"):
        """
        初始化性能测试套件。

        Args:
            api_key: Anthropic API key
            model_name: LLM 模型名称
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model_name

        self.test_cases = self._generate_test_cases()
        self.results = []

    def _generate_test_cases(self) -> List[Dict]:
        """生成测试用例"""
        return [
            {
                "patient_id": f"PAT{i:03d}",
                "visit_id": f"VIS{i:03d}",
                "department": "内科",
                "case_type": "门诊",
                "main_complaint": f"咳嗽{i}天",
                "present_illness": f"患者{i}天前受凉后出现咳嗽，伴有发热和咳痰。体温最高达38.5℃，持续2天。",
                "past_history": "既往体健，无高血压、糖尿病等慢性病史。无手术外伤史。",
                "physical_exam": "双肺呼吸音清，未闻及干湿啰音。心率80次/分，律齐。",
                "auxiliary_exams": "血常规：WBC 12.5×10^9/L，N 85%。胸片未见明显异常。",
                "diagnosis": f"急性支气管炎{i}",
                "prescription": f"阿莫西林胶囊 0.5g tid × 5天"
            }
            for i in range(1, 11)
        ]

    async def test_single_eval(self) -> Dict[str, Any]:
        """
        测试单次评估性能。

        Returns:
            测试结果
        """
        evaluator = PerformanceEvaluator(
            api_key=self.api_key,
            model_name=self.model_name
        )

        test_case = self.test_cases[0]

        # Warm up
        _ = evaluator.assess(test_case)

        # Actual test
        times = []
        for i in range(5):
            start = time.time()
            result = evaluator.assess(test_case)
            elapsed = time.time() - start
            times.append(elapsed)

            print(f"  Run {i+1}: {elapsed:.3f}s (Score: {result.scores.overall_score})")

        return {
            "test_type": "single_evaluation",
            "num_runs": 5,
            "response_times": times,
            "mean_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "avg_score": sum(r.scores.overall_score for r in [evaluator.assess(test_case) for _ in range(5)]) / 5
        }

    async def test_batch_eval(self, num_cases: int = 10) -> Dict[str, Any]:
        """
        测试批量评估性能。

        Args:
            num_cases: 测试用例数量

        Returns:
            测试结果
        """
        evaluator = AsyncBatchEvaluator(
            api_key=self.api_key,
            model_name=self.model_name,
            max_concurrent=4
        )

        cases = self.test_cases[:num_cases]

        # Warm up
        _ = await evaluator.evaluate_batch_async(cases[:2])

        # Actual test
        start = time.time()
        results = await evaluator.evaluate_batch_async(cases)
        elapsed = time.time() - start

        avg_score = sum(r.scores.overall_score for r in results) / len(results)

        return {
            "test_type": "batch_evaluation",
            "num_cases": num_cases,
            "total_time": elapsed,
            "avg_time_per_case": elapsed / num_cases,
            "cases_per_second": num_cases / elapsed if elapsed > 0 else 0,
            "avg_score": avg_score
        }

    async def test_concurrent_eval(self, num_concurrent: int = 5) -> Dict[str, Any]:
        """
        测试并发评估性能。

        Args:
            num_concurrent: 并发数量

        Returns:
            测试结果
        """
        evaluator = AsyncBatchEvaluator(
            api_key=self.api_key,
            model_name=self.model_name,
            max_concurrent=num_concurrent
        )

        # Generate more test cases
        cases = self.test_cases * (num_concurrent // len(self.test_cases) + 1)
        cases = cases[:num_concurrent]

        start = time.time()
        results = await evaluator.evaluate_batch_async(cases)
        elapsed = time.time() - start

        return {
            "test_type": "concurrent_evaluation",
            "num_concurrent": num_concurrent,
            "total_time": elapsed,
            "avg_time_per_case": elapsed / num_concurrent,
            "speedup": 1.0,  # Base ratio
            "throughput": num_concurrent / elapsed if elapsed > 0 else 0
        }

    async def test_token_usage(self) -> Dict[str, Any]:
        """
        测试 Token 使用情况。

        Returns:
            Token 使用统计
        """
        evaluator = PerformanceEvaluator(
            api_key=self.api_key,
            model_name=self.model_name
        )

        # Reset tracker
        token_tracker.reset()

        # Run evaluations
        for case in self.test_cases[:3]:
            evaluator.assess(case)

        stats = token_tracker.get_stats()

        return {
            "test_type": "token_usage",
            "input_tokens": stats["total_input_tokens"],
            "output_tokens": stats["total_output_tokens"],
            "total_tokens": stats["total_input_tokens"] + stats["total_output_tokens"],
            "total_requests": stats["total_requests"],
            "cost_usd": stats["total_cost_usd"],
            "avg_input_per_request": stats["total_input_tokens"] / max(stats["total_requests"], 1),
            "avg_output_per_request": stats["total_output_tokens"] / max(stats["total_requests"], 1)
        }

    async def test_all(self) -> Dict[str, Any]:
        """
        运行所有性能测试。

        Returns:
            完整测试结果
        """
        print("=" * 60)
        print("Medical Record Inspector - Performance Test Suite")
        print("=" * 60)

        all_results = {}

        # Test 1: Single Evaluation
        print("\n[1/4] Testing single evaluation...")
        result = await self.test_single_eval()
        all_results["single_evaluation"] = result
        print(f"  Mean response time: {result['mean_time']:.3f}s")

        # Test 2: Batch Evaluation
        print("\n[2/4] Testing batch evaluation...")
        result = await self.test_batch_eval(num_cases=10)
        all_results["batch_evaluation"] = result
        print(f"  Total time: {result['total_time']:.3f}s")
        print(f"  Avg per case: {result['avg_time_per_case']:.3f}s")

        # Test 3: Concurrent Evaluation
        print("\n[3/4] Testing concurrent evaluation...")
        result = await self.test_concurrent_eval(num_concurrent=5)
        all_results["concurrent_evaluation"] = result
        print(f"  Total time: {result['total_time']:.3f}s")

        # Test 4: Token Usage
        print("\n[4/4] Testing token usage...")
        result = await self.test_token_usage()
        all_results["token_usage"] = result
        print(f"  Total tokens: {result['total_tokens']}")
        print(f"  Estimated cost: ${result['cost_usd']:.4f}")

        # Summary
        print("\n" + "=" * 60)
        print("Performance Test Summary")
        print("=" * 60)
        print(json.dumps(all_results, indent=2, default=str))

        return all_results


async def run_performance_test(num_requests: int = 10) -> Dict[str, Any]:
    """
    便捷的性能测试函数。

    Args:
        num_requests: 请求数量

    Returns:
        测试结果
    """
    test_suite = PerformanceTestSuite()

    results = await test_suite.test_all()

    # Add overall metrics
    results["overall"] = {
        "total_requests": num_requests,
        "timestamp": datetime.now().isoformat()
    }

    return results


def report_performance(results: Dict[str, Any], output_file: str = None):
    """
    生成性能报告。

    Args:
        results: 性能测试结果
        output_file: 输出文件路径
    """
    lines = [
        "=" * 60,
        "Performance Test Report",
        "=" * 60,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]

    # Single Evaluation
    single = results.get("single_evaluation", {})
    if single:
        lines.extend([
            "Single Evaluation Performance:",
            "-" * 40,
            f"  Mean Response Time: {single.get('mean_time', 0):.3f}s",
            f"  Min Response Time: {single.get('min_time', 0):.3f}s",
            f"  Max Response Time: {single.get('max_time', 0):.3f}s",
            f"  Std Deviation: {single.get('std_dev', 0):.3f}s",
            ""
        ])

    # Batch Evaluation
    batch = results.get("batch_evaluation", {})
    if batch:
        lines.extend([
            "Batch Evaluation Performance:",
            "-" * 40,
            f"  Number of Cases: {batch.get('num_cases', 0)}",
            f"  Total Time: {batch.get('total_time', 0):.3f}s",
            f"  Avg Time Per Case: {batch.get('avg_time_per_case', 0):.3f}s",
            f"  Cases Per Second: {batch.get('cases_per_second', 0):.2f}",
            ""
        ])

    # Token Usage
    tokens = results.get("token_usage", {})
    if tokens:
        lines.extend([
            "Token Usage Statistics:",
            "-" * 40,
            f"  Input Tokens: {tokens.get('input_tokens', 0)}",
            f"  Output Tokens: {tokens.get('output_tokens', 0)}",
            f"  Total Tokens: {tokens.get('total_tokens', 0)}",
            f"  Total Cost: ${tokens.get('cost_usd', 0):.4f}",
            ""
        ])

    report = "\n".join(lines)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")
    else:
        print(report)


if __name__ == "__main__":
    import sys

    # 默认测试 10 个请求
    num_requests = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    print(f"Running performance test with {num_requests} requests...")
    print("Note: This may take several minutes due to API calls.\n")

    async def main():
        results = await run_performance_test(num_requests)

        # Print summary
        print("\n" + "=" * 60)
        print("Performance Summary")
        print("=" * 60)

        batch = results.get("batch_evaluation", {})
        if batch:
            print(f"\nBatch Evaluation (10 cases):")
            print(f"  Total Time: {batch.get('total_time', 0):.3f}s")
            print(f"  Avg Per Case: {batch.get('avg_time_per_case', 0):.3f}s")

        tokens = results.get("token_usage", {})
        if tokens:
            print(f"\nToken Usage:")
            print(f"  Total Tokens: {tokens.get('total_tokens', 0)}")
            print(f"  Estimated Cost: ${tokens.get('cost_usd', 0):.4f}")

        # Save report
        output = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_performance(results, output)

    asyncio.run(main())

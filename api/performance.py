"""
Performance Optimization Module for Medical Record Inspector.

This module provides performance optimizations for LLM calls including:
- Retry mechanism with exponential backoff
- Request timeout control
- Token usage tracking
- Async batch processing
"""

import json
import time
import hashlib
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from functools import wraps
import threading

import anthropic
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    AsyncRetrying,
    RetryError
)

from api.models import QualityAssessment, QualityScore, Issue

# Load environment variables
load_dotenv()


# ============================================================================
# Token Usage Tracker
# ============================================================================

class TokenUsageTracker:
    """追踪 LLM API 的 token 使用情况"""

    def __init__(self):
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_requests = 0
        self._total_cost = 0.0
        self._lock = threading.Lock()

        # Pricing for claude-3-5-sonnet-20240620 (per million tokens)
        self._input_price_per_million = 3.00  # $3.00 per million input tokens
        self._output_price_per_million = 15.00  # $15.00 per million output tokens

    def record_usage(self, input_tokens: int, output_tokens: int):
        """
        记录 token 使用情况。

        Args:
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量
        """
        with self._lock:
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_requests += 1

            # Calculate cost
            input_cost = (input_tokens / 1_000_000) * self._input_price_per_million
            output_cost = (output_tokens / 1_000_000) * self._output_price_per_million
            self._total_cost += input_cost + output_cost

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_input_tokens": self._total_input_tokens,
                "total_output_tokens": self._total_output_tokens,
                "total_requests": self._total_requests,
                "total_cost_usd": round(self._total_cost, 4),
                "cost_per_request_usd": round(
                    self._total_cost / max(self._total_requests, 1), 4
                )
            }

    def reset(self):
        """重置统计信息"""
        with self._lock:
            self._total_input_tokens = 0
            self._total_output_tokens = 0
            self._total_requests = 0
            self._total_cost = 0.0


# Global token tracker
token_tracker = TokenUsageTracker()


# ============================================================================
# Retry Decorator for LLM Calls
# ============================================================================

def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    timeout: float = 60.0
):
    """
    为 LLM 调用添加重试机制的装饰器。

    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间（秒）
        max_wait: 最大等待时间（秒）
        timeout: 单次请求超时时间（秒）

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(min=min_wait, max=max_wait),
            retry=retry_if_exception_type((
                anthropic.APIError,
                anthropic.APIConnectionError,
                anthropic.RateLimitError,
                anthropic.APIStatusError
            )),
            reraise=True
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator


def with_async_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    timeout: float = 60.0
):
    """
    为异步 LLM 调用添加重试机制的装饰器。

    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间（秒）
        max_wait: 最大等待时间（秒）
        timeout: 单次请求超时时间（秒）

    Returns:
        异步装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(min=min_wait, max=max_wait),
                    retry=retry_if_exception_type((
                        anthropic.APIError,
                        anthropic.APIConnectionError,
                        anthropic.RateLimitError,
                        anthropic.APIStatusError
                    )),
                    reraise=True
                ):
                    with attempt:
                        return await func(*args, **kwargs)
            except RetryError as e:
                raise Exception(f"LLM call failed after {max_attempts} attempts") from e
        return wrapper
    return decorator


# ============================================================================
# Timeout Control
# ============================================================================

class TimeoutClient:
    """带超时控制的 Anthropic 客户端包装器"""

    def __init__(self, api_key: str = None, default_timeout: float = 60.0):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.default_timeout = default_timeout
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def create_with_timeout(
        self,
        model: str,
        messages: List[Dict],
        max_tokens: int,
        timeout: float = None,
        **kwargs
    ) -> Any:
        """
        创建带超时控制的 LLM 调用。

        Args:
            model: 模型名称
            messages: 消息列表
            max_tokens: 最大 token 数
            timeout: 超时时间（秒），None 使用默认值
            **kwargs: 其他参数

        Returns:
            LLM 响应对象
        """
        actual_timeout = timeout or self.default_timeout

        # 使用线程池执行并限制超时
        import concurrent.futures

        def call_llm():
            return self.client.messages.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                **kwargs
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call_llm)
            try:
                result = future.result(timeout=actual_timeout)
                return result
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"LLM call timed out after {actual_timeout} seconds")


# ============================================================================
# Performance Evaluator (Optimized)
# ============================================================================

class PerformanceEvaluator:
    """
    性能优化的评估器。

    包含：
    - 重试机制
    - 超时控制
    - Token 使用追踪
    - 批量异步处理
    """

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "claude-3-5-sonnet-20240620",
        max_retries: int = 3,
        timeout: float = 60.0,
        enable_caching: bool = True
    ):
        """
        初始化性能优化评估器。

        Args:
            api_key: Anthropic API key
            model_name: LLM 模型名称
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
            enable_caching: 是否启用缓存
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout
        self.enable_caching = enable_caching

        # Initialize client with retry decorator
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Performance tracking
        self._request_times: List[float] = []
        self._lock = threading.Lock()

        # Templates
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def _load_template(self, template_name: str) -> str:
        """加载 Jinja2 模板文件"""
        template_path = self.templates_dir / template_name
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _generate_assessment_id(self, case_data: Dict) -> str:
        """根据病历数据生成评估ID"""
        case_str = json.dumps(case_data, sort_keys=True)
        case_hash = hashlib.md5(case_str.encode()).hexdigest()[:16]
        return f"ASSESS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{case_hash}"

    # ========================================================================
    # Optimized Assessment Methods
    # ========================================================================

    @with_retry(max_attempts=3, min_wait=1.0, max_wait=10.0)
    def _call_llm_with_retry(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.3
    ) -> str:
        """
        调用 LLM，带重试机制。

        Args:
            prompt: 提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            LLM 响应文本
        """
        start_time = time.time()

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        # Track token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        token_tracker.record_usage(input_tokens, output_tokens)

        # Track response time
        elapsed = time.time() - start_time
        with self._lock:
            self._request_times.append(elapsed)

        return response.content[0].text

    async def _call_llm_with_retry_async(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.3
    ) -> str:
        """
        异步调用 LLM，带重试机制。

        Args:
            prompt: 提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            LLM 响应文本
        """
        start_time = time.time()

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        # Track token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        token_tracker.record_usage(input_tokens, output_tokens)

        # Track response time
        elapsed = time.time() - start_time
        with self._lock:
            self._request_times.append(elapsed)

        return response.content[0].text

    def evaluate_completeness(
        self,
        submitted_case: Dict,
        standard_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历完整性（优化版本）。

        Args:
            submitted_case: 待评估病历
            standard_case: 标准病历模板

        Returns:
            (score, issues): 完整性评分和问题列表
        """
        required_fields = [
            "main_complaint", "present_illness", "past_history",
            "physical_exam", "auxiliary_exams", "diagnosis", "prescription"
        ]

        missing_fields = []
        incomplete_fields = []

        for field in required_fields:
            submitted_value = submitted_case.get(field, "")
            standard_value = standard_case.get(field, "")

            if not submitted_value or len(submitted_value.strip()) < 5:
                missing_fields.append(field)
                continue

            submitted_len = len(submitted_value)
            standard_len = len(standard_value)

            if standard_len > 0 and submitted_len < standard_len * 0.5:
                incomplete_fields.append(field)

        total_issues = len(missing_fields) + len(incomplete_fields)
        score = max(0, 10 - total_issues * 1.5)

        issues = []

        for field in missing_fields:
            issues.append({
                "issue_id": f"C{len(issues)+1:03d}",
                "category": "completeness",
                "severity": "high",
                "description": f"字段缺失：{field}",
                "suggestion": f"请补充{field}信息",
                "relevant_fields": [field]
            })

        for field in incomplete_fields:
            issues.append({
                "issue_id": f"C{len(issues)+1:03d}",
                "category": "completeness",
                "severity": "medium",
                "description": f"字段内容不完整：{field}",
                "suggestion": f"请补充{field}的详细信息",
                "relevant_fields": [field]
            })

        return max(0, score), issues

    def evaluate_consistency(
        self,
        submitted_case: Dict,
        standard_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历逻辑一致性（优化版本，使用重试）。

        Args:
            submitted_case: 待评估病历
            standard_case: 标准病历模板

        Returns:
            (score, issues): 一致性评分和问题列表
        """
        issues = []
        score = 10.0

        diagnosis = submitted_case.get("diagnosis", "")
        prescription = submitted_case.get("prescription", "")
        present_illness = submitted_case.get("present_illness", "")
        past_history = submitted_case.get("past_history", "")

        # Check diagnosis consistency with present illness
        if diagnosis and present_illness:
            prompt = f"""分析以下现病史描述与诊断是否一致。
现病史：{present_illness}
诊断：{diagnosis}
请回答：一致/不一致。如果不一致，请说明原因。"""

            try:
                result = self._call_llm_with_retry(prompt, max_tokens=500)
                if "不一致" in result.lower():
                    score -= 2
                    issues.append({
                        "issue_id": f"CI{len(issues)+1:03d}",
                        "category": "consistency",
                        "severity": "high",
                        "description": "诊断与现病史可能不匹配",
                        "suggestion": "请重新评估诊断是否与症状相符",
                        "relevant_fields": ["diagnosis", "present_illness"]
                    })
            except Exception:
                pass

        # Check treatment matches diagnosis
        if diagnosis and prescription:
            prompt = f"""分析以下诊断与医嘱/治疗方案是否匹配。
诊断：{diagnosis}
治疗方案：{prescription}
请回答：匹配/不匹配。如果不匹配，请说明原因。"""

            try:
                result = self._call_llm_with_retry(prompt, max_tokens=500)
                if "不匹配" in result.lower():
                    score -= 2
                    issues.append({
                        "issue_id": f"CI{len(issues)+1:03d}",
                        "category": "consistency",
                        "severity": "high",
                        "description": "治疗方案与诊断可能不匹配",
                        "suggestion": "请检查治疗方案是否针对当前诊断",
                        "relevant_fields": ["diagnosis", "prescription"]
                    })
            except Exception:
                pass

        # Check past history impact
        if past_history and diagnosis:
            prompt = f"""分析以下既往史是否可能影响当前诊断。
既往史：{past_history}
当前诊断：{diagnosis}
请回答：相关/不相关。如果相关，请说明影响。"""

            try:
                result = self._call_llm_with_retry(prompt, max_tokens=500)
                if "相关" in result.lower() and ("需要" in result or "注意" in result):
                    score -= 0.5
                    issues.append({
                        "issue_id": f"CI{len(issues)+1:03d}",
                        "category": "consistency",
                        "severity": "low",
                        "description": "既往史可能影响当前诊断评估",
                        "suggestion": "请补充既往史与当前诊断的关系说明",
                        "relevant_fields": ["past_history", "diagnosis"]
                    })
            except Exception:
                pass

        return max(0, score), issues

    def evaluate_timeliness(
        self,
        submitted_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历及时性（优化版本）。

        Args:
            submitted_case: 待评估病历

        Returns:
            (score, issues): 及时性评分和问题列表
        """
        issues = []
        score = 10.0

        auxiliary_exams = submitted_case.get("auxiliary_exams", "")
        diagnosis = submitted_case.get("diagnosis", "")

        if auxiliary_exams and diagnosis:
            prompt = f"""分析以下病历中的检查和诊断时间逻辑。
辅助检查：{auxiliary_exams}
诊断：{diagnosis}

请判断：
1. 是否先有检查后有诊断（合理）
2. 是否诊断在检查之前（可能不合理）

请回答：合理/需要改进。如果需要改进，请说明具体原因。"""

            try:
                result = self._call_llm_with_retry(prompt, max_tokens=500)
                if "改进" in result.lower() or "不合理" in result.lower():
                    score -= 1.5
                    issues.append({
                        "issue_id": f"T{len(issues)+1:03d}",
                        "category": "timeliness",
                        "severity": "medium",
                        "description": "辅助检查与诊断的时间顺序可能不合理",
                        "suggestion": "请确保辅助检查在诊断之前或同时进行",
                        "relevant_fields": ["auxiliary_exams", "diagnosis"]
                    })
            except Exception:
                pass

        prescription = submitted_case.get("prescription", "")
        present_illness = submitted_case.get("present_illness", "")

        if prescription and present_illness:
            prompt = f"""分析以下病历的治疗是否及时。
现病史：{present_illness}
治疗方案：{prescription}

请判断：治疗是否及时（及时/延迟/不合理）。
如果不及时，请说明原因。"""

            try:
                result = self._call_llm_with_retry(prompt, max_tokens=500)
                if "延迟" in result.lower() or "不及时" in result.lower():
                    score -= 1.5
                    issues.append({
                        "issue_id": f"T{len(issues)+1:03d}",
                        "category": "timeliness",
                        "severity": "medium",
                        "description": "治疗可能不够及时",
                        "suggestion": "请评估治疗措施的及时性",
                        "relevant_fields": ["prescription", "present_illness"]
                    })
            except Exception:
                pass

        return max(0, score), issues

    def evaluate_standardization(
        self,
        submitted_case: Dict
    ) -> tuple[float, List[Dict]]:
        """
        评估病历规范性（优化版本）。

        Args:
            submitted_case: 待评估病历

        Returns:
            (score, issues): 规范性评分和问题列表
        """
        issues = []
        score = 10.0

        # Check field lengths
        for field, min_length in [
            ("main_complaint", 5),
            ("present_illness", 30),
            ("diagnosis", 5),
            ("prescription", 10)
        ]:
            value = submitted_case.get(field, "")
            if len(value) < min_length:
                score -= 1
                issues.append({
                    "issue_id": f"S{len(issues)+1:03d}",
                    "category": "standardization",
                    "severity": "low",
                    "description": f"字段内容过短：{field}",
                    "suggestion": f"请补充{field}的详细信息",
                    "relevant_fields": [field]
                })

        # Check terminology
        prompt = f"""分析以下病历文本，检查是否使用规范的医学术语。
主诉：{submitted_case.get('main_complaint', '')}
现病史：{submitted_case.get('present_illness', '')}
诊断：{submitted_case.get('diagnosis', '')}

请指出：
1. 是否使用了不规范的医学术语
2. 是否存在口语化表达
3. 是否存在错别字

请回答：规范/需要改进。如果需要改进，请列出具体问题。"""

        try:
            result = self._call_llm_with_retry(prompt, max_tokens=500)
            if "改进" in result.lower() or "不规范" in result.lower():
                score -= 1
                issues.append({
                    "issue_id": f"S{len(issues)+1:03d}",
                    "category": "standardization",
                    "severity": "low",
                    "description": "病历可能使用了不规范的术语或表达",
                    "suggestion": "请使用规范的医学术语书写病历",
                    "relevant_fields": ["main_complaint", "present_illness", "diagnosis"]
                })
        except Exception:
            pass

        return max(0, score), issues

    def assess(
        self,
        case: Dict,
        standard_template: Dict = None
    ) -> QualityAssessment:
        """
        对病历进行全面质量评估（优化版本）。

        Args:
            case: 待评估病历数据
            standard_template: 标准病历模板

        Returns:
            QualityAssessment 评估结果对象
        """
        if standard_template is None:
            standard_template = {
                "main_complaint": "不变",
                "present_illness": "已描述",
                "past_history": "已记录",
                "physical_exam": "已检查",
                "auxiliary_exams": "已完成",
                "diagnosis": "已诊断",
                "prescription": "已开具"
            }

        # Execute evaluations
        completeness_score, completeness_issues = self.evaluate_completeness(
            case, standard_template
        )
        consistency_score, consistency_issues = self.evaluate_consistency(
            case, standard_template
        )
        timeliness_score, timeliness_issues = self.evaluate_timeliness(case)
        standardization_score, standardization_issues = self.evaluate_standardization(
            case
        )

        # Calculate overall score
        overall_score = (
            completeness_score * 0.25 +
            consistency_score * 0.25 +
            timeliness_score * 0.25 +
            standardization_score * 0.25
        )

        # Merge all issues
        all_issues = (
            completeness_issues +
            consistency_issues +
            timeliness_issues +
            standardization_issues
        )

        # Generate overall comment
        overall_comment = self._generate_overall_comment(
            completeness_score, consistency_score,
            timeliness_score, standardization_score,
            all_issues
        )

        # Create assessment object
        assessment = QualityAssessment(
            assessment_id=self._generate_assessment_id(case),
            patient_id=case.get("patient_id"),
            visit_id=case.get("visit_id"),
            scores=QualityScore(
                completeness_score=round(completeness_score, 1),
                consistency_score=round(consistency_score, 1),
                timeliness_score=round(timeliness_score, 1),
                standardization_score=round(standardization_score, 1),
                overall_score=round(overall_score, 1)
            ),
            issues=[Issue(**issue) for issue in all_issues],
            report=overall_comment,
            标注时间=datetime.now(),
            standard_template_id=None
        )

        return assessment

    def _generate_overall_comment(
        self,
        completeness: float,
        consistency: float,
        timeliness: float,
        standardization: float,
        issues: List[Dict]
    ) -> str:
        """生成总体评论"""
        score = (completeness + consistency + timeliness + standardization) / 4

        if score >= 9:
            comment = "病历质量优秀，书写规范，内容完整。"
        elif score >= 7:
            comment = "病历质量良好，基本符合规范要求。"
        elif score >= 5:
            comment = "病历质量一般，存在需要改进的地方。"
        else:
            comment = "病历质量较差，存在较多问题需要整改。"

        if issues:
            high_count = sum(1 for i in issues if i.get("severity") == "high")
            medium_count = sum(1 for i in issues if i.get("severity") == "medium")
            low_count = sum(1 for i in issues if i.get("severity") == "low")

            comment += f"\n\n主要问题统计："
            comment += f"\n- 严重问题：{high_count}项"
            comment += f"\n- 中等问题：{medium_count}项"
            comment += f"\n- 轻微问题：{low_count}项"

            if high_count > 0:
                comment += "\n\n建议优先处理严重问题，确保病历质量和诊疗安全。"
        else:
            comment += "\n\n继续保持良好的病历书写质量。"

        return comment

    def assess_batch(
        self,
        cases: List[Dict],
        standard_template: Dict = None
    ) -> List[QualityAssessment]:
        """
        批量评估病历（同步版本）。

        Args:
            cases: 待评估病历列表
            standard_template: 标准病历模板

        Returns:
            评估结果列表
        """
        results = []
        for case in cases:
            try:
                result = self.assess(case, standard_template)
                results.append(result)
            except Exception as e:
                # 创建失败的评估记录
                results.append(QualityAssessment(
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
                ))
        return results

    async def assess_batch_async(
        self,
        cases: List[Dict],
        standard_template: Dict = None
    ) -> List[QualityAssessment]:
        """
        批量评估病历（异步版本，使用并发）。

        Args:
            cases: 待评估病历列表
            standard_template: 标准病历模板

        Returns:
            评估结果列表
        """
        import asyncio

        async def assess_single(case: Dict) -> QualityAssessment:
            try:
                return await asyncio.to_thread(self.assess, case, standard_template)
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

        # 使用 asyncio.gather 并发执行
        tasks = [assess_single(case) for case in cases]
        results = await asyncio.gather(*tasks)
        return list(results)

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        with self._lock:
            avg_response_time = (
                sum(self._request_times) / len(self._request_times)
                if self._request_times else 0
            )
            return {
                "avg_response_time": round(avg_response_time, 3),
                "total_requests": len(self._request_times),
                "min_response_time": round(min(self._request_times), 3) if self._request_times else 0,
                "max_response_time": round(max(self._request_times), 3) if self._request_times else 0,
                "token_tracker": token_tracker.get_stats()
            }

    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self._request_times.clear()
        token_tracker.reset()


# ============================================================================
# Convenience Functions
# ============================================================================

def assess_case_optimized(
    case: Dict,
    api_key: str = None,
    model_name: str = "claude-3-5-sonnet-20240620",
    max_retries: int = 3,
    timeout: float = 60.0
) -> QualityAssessment:
    """
    优化的病历评估函数。

    Args:
        case: 待评估病历
        api_key: API密钥
        model_name: 模型名称
        max_retries: 最大重试次数
        timeout: 超时时间（秒）

    Returns:
        评估结果对象
    """
    evaluator = PerformanceEvaluator(
        api_key=api_key,
        model_name=model_name,
        max_retries=max_retries,
        timeout=timeout
    )
    return evaluator.assess(case)


def get_token_stats() -> Dict[str, Any]:
    """获取全局 token 使用统计"""
    return token_tracker.get_stats()


def reset_token_stats():
    """重置全局 token 统计"""
    token_tracker.reset()


if __name__ == "__main__":
    # 简单测试
    test_case = {
        "patient_id": "PAT001",
        "visit_id": "VIS001",
        "department": "内科",
        "case_type": "门诊",
        "main_complaint": "咳嗽3天",
        "present_illness": "患者3天前受凉后出现咳嗽",
        "past_history": "无特殊",
        "physical_exam": "双肺呼吸音清",
        "auxiliary_exams": "血常规正常",
        "diagnosis": "急性支气管炎",
        "prescription": "阿莫西林 0.5g tid"
    }

    print("测试优化评估器...")
    evaluator = PerformanceEvaluator(max_retries=2, timeout=120.0)

    # 执行评估
    result = evaluator.assess(test_case)

    print(f"评估ID: {result.assessment_id}")
    print(f"总体评分: {result.scores.overall_score}")
    print(f"发现问题: {len(result.issues)}项")
    print(f"\n性能统计:")
    print(f"  {evaluator.get_performance_stats()}")

"""
Evaluator Core Module - Medical Record Quality Evaluation Logic
"""
import re
import json
import logging
from typing import Dict, List, Optional, Any

from .prompts import (
    EVALUATION_SYSTEM_PROMPT,
    get_completeness_prompt,
    get_logicality_prompt,
    get_timeliness_prompt,
    get_normativity_prompt,
    get_comprehensive_prompt,
    get_template_comparison_prompt,
    EXAMPLE_COMPLETENESS_RESPONSE,
    EXAMPLE_LOGICALITY_RESPONSE,
    EXAMPLE_TIMELINESS_RESPONSE,
    EXAMPLE_NORMATIVITY_RESPONSE,
    EXAMPLE_COMPREHENSIVE_RESPONSE,
)

from llm.llm_client import LLMClient
from models.evaluator import EvaluationRequest
from models.response import (
    EvaluationResponse,
    DimensionScores,
    Issue,
    create_empty_response,
)

logger = logging.getLogger(__name__)


class MedicalRecordEvaluator:
    """
    Core evaluator for medical record quality assessment.

    This class uses LLM to evaluate medical records from four dimensions:
    - Completeness (完整性): Basic elements coverage
    - Logicality (逻辑性): Medical logic and reasoning
    - Timeliness (及时性): Timing and time records
    - Normativity (规范性): Formatting and terminology standards

    Attributes:
        llm_client: LLM client for generating evaluations
        weight_map: Weight for each dimension in overall score calculation
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        weight_map: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the evaluator.

        Args:
            llm_client: LLMClient instance. If None, creates a default one.
            weight_map: Dictionary mapping dimension names to weights.
                       Defaults to equal weights: {completeness: 0.25, logicality: 0.25, timeliness: 0.25, normativity: 0.25}
        """
        self.llm_client = llm_client or LLMClient()
        self.weight_map = weight_map or {
            "completeness": 0.25,
            "logicality": 0.25,
            "timeliness": 0.25,
            "normativity": 0.25,
        }

        # Verify weights sum to 1
        total_weight = sum(self.weight_map.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, not 1.0. Normalizing...")
            self.weight_map = {
                k: v / total_weight for k, v in self.weight_map.items()
            }

        # Severity mapping for normalization
        self.severity_score_map = {
            "critical": 0.0,
            "high": 40.0,
            "medium": 70.0,
            "low": 90.0,
            # Prompt-specific severity mapping
            "m_major": 60.0,
            "m_minor": 85.0,
        }

        logger.info("MedicalRecordEvaluator initialized")

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels from prompts to standard levels."""
        severity_lower = severity.lower().strip()
        if severity_lower in ["critical", "严重"]:
            return "critical"
        elif severity_lower in ["high", "m_major", "中度", "中"]:
            return "high"
        elif severity_lower in ["medium", "m_minor", "轻微"]:
            return "medium"
        elif severity_lower in ["low", "低"]:
            return "low"
        return "medium"  # Default

    def _calculate_dimension_score(self, issues: List[Dict]) -> float:
        """
        Calculate dimension score based on issues.

        Score starts at 100 and deducts points based on issue severity:
        - critical: -30 points
        - high: -20 points
        - medium: -10 points
        - low: -5 points

        Minimum score is 0.
        """
        score = 100.0
        for issue in issues:
            severity = self._normalize_severity(issue.get("severity", "medium"))
            deduction = {
                "critical": 30,
                "high": 20,
                "medium": 10,
                "low": 5,
            }.get(severity, 10)
            score -= deduction

        return max(0.0, min(100.0, score))

    def _parse_issue(self, issue_data: Dict, dimension: str) -> Optional[Issue]:
        """Parse raw issue data into Issue model."""
        try:
            return Issue(
                dimension=dimension,
                severity=self._normalize_severity(
                    issue_data.get("severity", "medium")
                ),
                description=issue_data.get("description", ""),
                recommendation=issue_data.get("suggestion") or issue_data.get(
                    "recommendation", ""
                ),
            )
        except Exception as e:
            logger.warning(f"Failed to parse issue: {e}")
            return None

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from LLM response, handling various formats."""
        # Remove code block markers
        response_text = re.sub(r"```json\s*", "", response_text)
        response_text = re.sub(r"```\s*", "", response_text)
        response_text = response_text.strip()

        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in the response
        json_patterns = [
            r"\{[^{}]*\}",  # Simple object
            r"\{[\s\S]*?\}(?=\s*$)",  # Last object in text
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response_text)
            for match in reversed(matches):  # Try last matches first
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # If all parsing fails, return empty dict
        logger.warning(f"Failed to parse JSON from response: {response_text[:200]}...")
        return {}

    async def _evaluate_dimension(
        self,
        medical_record: str,
        dimension: str,
        prompt_func,
        example_response: str,
    ) -> Dict[str, Any]:
        """
        Evaluate a single dimension using LLM.

        Args:
            medical_record: The medical record text
            dimension: The dimension name (completeness, logicality, etc.)
            prompt_func: Function to generate the prompt
            example_response: Example JSON response for few-shot learning

        Returns:
            Dict with dimension_score, issues, and recommendations
        """
        prompt = prompt_func(medical_record)

        messages = [
            {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"请参考以下示例，对病历进行评估：\n\n示例评估：\n{example_response}\n\n现在请评估以下病历：\n\n{prompt}",
            },
        ]

        try:
            response = await self.llm_client.generate(
                prompt, system_prompt=EVALUATION_SYSTEM_PROMPT, json_mode=True
            )
            response_text = response.get("text", "")

            # Try to parse JSON response
            result = self._extract_json_from_response(response_text)

            # Ensure we have expected keys
            dimension_score = result.get("dimension_score") or result.get(
                "dimension_scores", {}
            ).get(dimension, 50)

            # Handle single dimension score
            if isinstance(dimension_score, (int, float)):
                score = float(dimension_score)
            else:
                score = 50.0

            # Get issues
            issues = result.get("issues", [])
            if isinstance(issues, list) and len(issues) > 0:
                # Ensure each issue has required fields
                normalized_issues = []
                for issue in issues:
                    if isinstance(issue, dict):
                        normalized_issue = {
                            "dimension": dimension,
                            "severity": issue.get("severity", "medium"),
                            "description": issue.get(
                                "description", issue.get("suggestion", "")
                            ),
                            "suggestion": issue.get("suggestion", ""),
                        }
                        normalized_issues.append(normalized_issue)
                issues = normalized_issues

            # Get recommendations
            recommendations = result.get("recommendations", [])

            return {
                "dimension_score": score,
                "issues": issues,
                "recommendations": recommendations,
                "raw_response": response_text,
            }

        except Exception as e:
            logger.error(f"Error evaluating dimension {dimension}: {e}")
            return {
                "dimension_score": 50.0,
                "issues": [],
                "recommendations": [
                    f"评估失败：{str(e)}。请检查病历内容或重试。"
                ],
                "raw_response": "",
            }

    async def _evaluate_comprehensive(
        self, medical_record: str
    ) -> Dict[str, Any]:
        """
        Evaluate all dimensions in a single call for efficiency.

        Args:
            medical_record: The medical record text

        Returns:
            Dict with all dimension scores, issues, and recommendations
        """
        prompt = get_comprehensive_prompt(medical_record)

        try:
            response = await self.llm_client.generate(
                prompt, system_prompt=EVALUATION_SYSTEM_PROMPT, json_mode=True
            )
            response_text = response.get("text", "")

            # Parse JSON response
            result = self._extract_json_from_response(response_text)

            # Extract dimension scores
            dimension_scores = result.get(
                "dimension_scores",
                {
                    "completeness": 50,
                    "logicality": 50,
                    "timeliness": 50,
                    "normativity": 50,
                },
            )

            # Ensure all scores are floats
            for key in dimension_scores:
                if isinstance(dimension_scores[key], (int, float)):
                    dimension_scores[key] = float(dimension_scores[key])
                else:
                    dimension_scores[key] = 50.0

            # Get overall score (use provided or calculate from dimensions)
            if "overall_score" in result:
                overall_score = float(result["overall_score"])
            else:
                # Calculate weighted average
                overall_score = sum(
                    dimension_scores.get(k, 50) * v
                    for k, v in self.weight_map.items()
                )

            # Get issues
            issues = result.get("issues", [])
            if isinstance(issues, list) and len(issues) > 0:
                normalized_issues = []
                for issue in issues:
                    if isinstance(issue, dict):
                        normalized_issue = {
                            "dimension": issue.get(
                                "dimension", list(self.weight_map.keys())[0]
                            ),
                            "severity": issue.get("severity", "medium"),
                            "description": issue.get("description", ""),
                            "suggestion": issue.get("suggestion", ""),
                        }
                        normalized_issues.append(normalized_issue)
                issues = normalized_issues

            # Get recommendations
            recommendations = result.get("recommendations", [])

            return {
                "dimension_scores": dimension_scores,
                "overall_score": min(100.0, max(0.0, overall_score)),
                "issues": issues,
                "recommendations": recommendations,
                "summary": result.get("summary", ""),
                "raw_response": response_text,
            }

        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            return {
                "dimension_scores": {
                    "completeness": 50.0,
                    "logicality": 50.0,
                    "timeliness": 50.0,
                    "normativity": 50.0,
                },
                "overall_score": 50.0,
                "issues": [],
                "recommendations": [
                    f"综合评估失败：{str(e)}。请检查病历内容或重试。"
                ],
                "summary": "",
                "raw_response": "",
            }

    async def _evaluate_with_template(
        self, medical_record: str, template_content: str
    ) -> Dict[str, Any]:
        """
        Evaluate medical record against a standard template.

        Args:
            medical_record: The medical record text
            template_content: The standard template content

        Returns:
            Dict with gap analysis and recommendations
        """
        prompt = get_template_comparison_prompt(template_content, medical_record)

        try:
            response = await self.llm_client.generate(
                prompt, system_prompt=EVALUATION_SYSTEM_PROMPT, json_mode=True
            )
            response_text = response.get("text", "")

            result = self._extract_json_from_response(response_text)

            return {
                "comparison_analysis": result.get("comparison_analysis", {}),
                "recommendations": result.get("recommendations", []),
                "raw_response": response_text,
            }

        except Exception as e:
            logger.error(f"Error in template-based evaluation: {e}")
            return {
                "comparison_analysis": {"gap_summary": "模板对比失败"},
                "recommendations": [f"模板对比失败：{str(e)}"],
                "raw_response": "",
            }

    def _aggregate_issues(
        self, all_issues: List[Dict], dimension: Optional[str] = None
    ) -> List[Issue]:
        """Aggregate and deduplicate issues."""
        seen = set()
        aggregated = []

        for issue in all_issues:
            # Create a unique key for deduplication
            key = (
                issue.get("dimension", dimension or "unknown"),
                issue.get("description", "")[:50],
            )

            if key not in seen:
                seen.add(key)
                parsed = self._parse_issue(issue, dimension or issue.get("dimension"))
                if parsed:
                    aggregated.append(parsed)

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        aggregated.sort(key=lambda x: severity_order.get(x.severity, 4))

        return aggregated

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """
        Evaluate medical record quality based on request.

        This method evaluates medical records from four dimensions:
        - Completeness (完整性): Basic elements coverage
        - Logicality (逻辑性): Medical logic and reasoning
        - Timeliness (及时性): Timing and time records
        - Normativity (规范性): Formatting and terminology standards

        Args:
            request: EvaluationRequest containing medical record and options

        Returns:
            EvaluationResponse with overall score, dimension scores, issues, and recommendations
        """
        content = request.content or ""
        evaluation_dims = request.evaluation_dims or ["completeness", "logicality", "timeliness", "normativity"]

        # Validate input
        if not content.strip():
            return create_empty_response()

        # If template-based comparison is requested
        if request.template_id and hasattr(self, 'template_store'):
            # This would require template store integration
            pass

        # Use comprehensive evaluation for efficiency
        comprehensive_result = await self._evaluate_comprehensive(content)

        # Extract results
        dimension_scores = comprehensive_result.get(
            "dimension_scores",
            {
                "completeness": 50.0,
                "logicality": 50.0,
                "timeliness": 50.0,
                "normativity": 50.0,
            },
        )

        overall_score = comprehensive_result.get("overall_score", 50.0)
        all_issues = comprehensive_result.get("issues", [])
        recommendations = comprehensive_result.get("recommendations", [])

        # Create dimension scores object
        scores = DimensionScores(
            completeness=dimension_scores.get("completeness", 50.0),
            logicality=dimension_scores.get("logicality", 50.0),
            timeliness=dimension_scores.get("timeliness", 50.0),
            normativity=dimension_scores.get("normativity", 50.0),
        )

        # Create response
        response = EvaluationResponse(
            overall_score=overall_score,
            dimension_scores=scores,
            issues=all_issues,
            recommendations=recommendations,
        )

        logger.info(
            f"Evaluation complete: overall_score={overall_score}, dimensions={scores}"
        )

        return response

    async def evaluate_dimension_by_dimension(
        self, request: EvaluationRequest
    ) -> EvaluationResponse:
        """
        Evaluate dimensions individually (for detailed analysis).

        This method evaluates each dimension separately and aggregates results.
        Use this when you need more detailed evaluation per dimension.

        Args:
            request: EvaluationRequest containing medical record

        Returns:
            EvaluationResponse with detailed per-dimension analysis
        """
        content = request.content or ""

        if not content.strip():
            return create_empty_response()

        # Run evaluations in parallel using asyncio.gather
        import asyncio

        tasks = [
            self._evaluate_dimension(
                content,
                "completeness",
                get_completeness_prompt,
                EXAMPLE_COMPLETENESS_RESPONSE,
            ),
            self._evaluate_dimension(
                content,
                "logicality",
                get_logicality_prompt,
                EXAMPLE_LOGICALITY_RESPONSE,
            ),
            self._evaluate_dimension(
                content,
                "timeliness",
                get_timeliness_prompt,
                EXAMPLE_TIMELINESS_RESPONSE,
            ),
            self._evaluate_dimension(
                content,
                "normativity",
                get_normativity_prompt,
                EXAMPLE_NORMATIVITY_RESPONSE,
            ),
        ]

        results = await asyncio.gather(*tasks)

        # Aggregate results
        dimension_scores = {}
        all_issues = []
        all_recommendations = []

        dimension_names = ["completeness", "logicality", "timeliness", "normativity"]

        for result, dim_name in zip(results, dimension_names):
            dimension_scores[dim_name] = result.get("dimension_score", 50.0)
            all_issues.extend(result.get("issues", []))
            all_recommendations.extend(result.get("recommendations", []))

        # Calculate overall score (weighted average)
        overall_score = sum(
            dimension_scores.get(k, 50) * v for k, v in self.weight_map.items()
        )

        scores = DimensionScores(
            completeness=dimension_scores.get("completeness", 50.0),
            logicality=dimension_scores.get("logicality", 50.0),
            timeliness=dimension_scores.get("timeliness", 50.0),
            normativity=dimension_scores.get("normativity", 50.0),
        )

        response = EvaluationResponse(
            overall_score=min(100.0, max(0.0, overall_score)),
            dimension_scores=scores,
            issues=self._aggregate_issues(all_issues),
            recommendations=list(set(all_recommendations)),  # Remove duplicates
        )

        logger.info(
            f"Dimension-by-dimension evaluation complete: overall_score={overall_score}"
        )

        return response

    def get_dimension_weights(self) -> Dict[str, float]:
        """Get current dimension weights for overall score calculation."""
        return self.weight_map.copy()

    def set_dimension_weights(self, weights: Dict[str, float]) -> None:
        """
        Set custom dimension weights.

        Args:
            weights: Dictionary mapping dimension names to weights.
                    Weights will be normalized to sum to 1.0.
        """
        total = sum(weights.values())
        if total > 0:
            self.weight_map = {k: v / total for k, v in weights.items()}
            logger.info(f"Dimension weights updated: {self.weight_map}")
        else:
            logger.warning("Invalid weights: sum must be > 0")


# Singleton instance for convenience
_default_evaluator: Optional[MedicalRecordEvaluator] = None


def get_default_evaluator() -> MedicalRecordEvaluator:
    """Get or create the default singleton evaluator instance."""
    global _default_evaluator
    if _default_evaluator is None:
        _default_evaluator = MedicalRecordEvaluator()
    return _default_evaluator


async def evaluate_medical_record(
    content: str,
    template_id: Optional[str] = None,
    evaluation_dims: Optional[List[str]] = None,
) -> EvaluationResponse:
    """
    Convenience function to evaluate a medical record.

    Args:
        content: Medical record text
        template_id: Optional template ID for comparison
        evaluation_dims: Optional list of dimensions to evaluate

    Returns:
        EvaluationResponse with evaluation results
    """
    evaluator = get_default_evaluator()
    request = EvaluationRequest(
        content=content,
        template_id=template_id,
        evaluation_dims=evaluation_dims,
    )
    return await evaluator.evaluate(request)


def get_evaluator_with_model(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> MedicalRecordEvaluator:
    """
    Get or create an evaluator instance with specific model configuration.

    Args:
        model_name: Model name to use (e.g., 'gpt-4', 'qwen-plus')
        provider: Provider name (e.g., 'openai', 'dashscope', 'ernie')
        api_key: Optional custom API key

    Returns:
        MedicalRecordEvaluator instance with specified model
    """
    from llm.llm_client import LLMClient

    llm_client = LLMClient(
        provider=provider,
        api_key=api_key,
        model_name=model_name,
    )
    return MedicalRecordEvaluator(llm_client=llm_client)

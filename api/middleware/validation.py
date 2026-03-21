"""
Data Validation Middleware for Medical Record Inspector.

This module provides request validation middleware to ensure
incoming medical record data meets required format and constraints.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# Default required fields for a medical record
DEFAULT_REQUIRED_FIELDS = [
    "main_complaint",      # 主诉
    "present_illness",     # 现病史
    "past_history",        #既往史
    "physical_exam",       # 体格检查
    "auxiliary_exams",     # 辅助检查
    "diagnosis",           # 诊断
    "prescription"         # 医嘱/治疗方案
]

# Default minimum length for each field
DEFAULT_MIN_LENGTHS = {
    "main_complaint": 5,
    "present_illness": 30,
    "past_history": 10,
    "physical_exam": 10,
    "auxiliary_exams": 10,
    "diagnosis": 5,
    "prescription": 10
}

# Default maximum lengths
DEFAULT_MAX_LENGTHS = {
    "main_complaint": 500,
    "present_illness": 5000,
    "past_history": 2000,
    "physical_exam": 2000,
    "auxiliary_exams": 5000,
    "diagnosis": 500,
    "prescription": 1000
}


class ValidationError(Exception):
    """数据验证异常"""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error on field '{field}': {message}")


class CaseDataValidator:
    """
    病历数据验证器。

    提供以下验证功能：
    - 必填字段验证
    - 字段长度验证
    - 字段格式验证
    - 业务逻辑验证
    """

    def __init__(
        self,
        required_fields: List[str] = None,
        min_lengths: Dict[str, int] = None,
        max_lengths: Dict[str, int] = None,
       strict_mode: bool = False
    ):
        """
        初始化验证器。

        Args:
            required_fields: 必填字段列表
            min_lengths: 最小长度配置
            max_lengths: 最大长度配置
            strict_mode: 严格模式（启用更多验证规则）
        """
        self.required_fields = required_fields or DEFAULT_REQUIRED_FIELDS
        self.min_lengths = min_lengths or DEFAULT_MIN_LENGTHS
        self.max_lengths = max_lengths or DEFAULT_MAX_LENGTHS
        self.strict_mode = strict_mode

    def validate_required_fields(self, data: Dict) -> List[Dict]:
        """
        验证必填字段。

        Args:
            data: 病历数据

        Returns:
            错误列表
        """
        errors = []

        for field in self.required_fields:
            value = data.get(field)

            if value is None:
                errors.append({
                    "field": field,
                    "error": "required",
                    "message": f"字段 '{field}' 是必填项"
                })
            elif isinstance(value, str) and not value.strip():
                errors.append({
                    "field": field,
                    "error": "empty",
                    "message": f"字段 '{field}' 不能为空"
                })

        return errors

    def validate_field_lengths(self, data: Dict) -> List[Dict]:
        """
        验证字段长度。

        Args:
            data: 病历数据

        Returns:
            错误列表
        """
        errors = []

        for field, value in data.items():
            # 跳过非字符串字段
            if not isinstance(value, str):
                continue

            # 检查最小长度
            min_len = self.min_lengths.get(field)
            if min_len and len(value.strip()) < min_len:
                errors.append({
                    "field": field,
                    "error": "too_short",
                    "message": f"字段 '{field}' 长度不能少于 {min_len} 个字符（当前: {len(value.strip())}）"
                })

            # 检查最大长度
            max_len = self.max_lengths.get(field)
            if max_len and len(value) > max_len:
                errors.append({
                    "field": field,
                    "error": "too_long",
                    "message": f"字段 '{field}' 长度不能超过 {max_len} 个字符（当前: {len(value)}）"
                })

        return errors

    def validate_field_format(self, data: Dict) -> List[Dict]:
        """
        验证字段格式（如日期、数字等）。

        Args:
            data: 病历数据

        Returns:
            错误列表
        """
        errors = []

        # 日期格式验证（如 apply_time, visit_date 等）
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?Z?$')

        date_fields = [
            "apply_time", "visit_date", "examination_date",
            "diagnosis_date", "prescription_date"
        ]

        for field in date_fields:
            value = data.get(field)
            if value and isinstance(value, str):
                if not date_pattern.match(value):
                    errors.append({
                        "field": field,
                        "error": "invalid_date",
                        "message": f"字段 '{field}' 格式不正确，应为 YYYY-MM-DD 或 ISO 8601 格式"
                    })

        # 数字格式验证（如 patient_age, Vital signs）
        numeric_fields = ["patient_age", "temperature", "heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic"]

        for field in numeric_fields:
            value = data.get(field)
            if value is not None:
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append({
                        "field": field,
                        "error": "invalid_number",
                        "message": f"字段 '{field}' 应为数字类型"
                    })

        return errors

    def validate_business_logic(self, data: Dict) -> List[Dict]:
        """
        验证业务逻辑（如诊断与治疗的一致性提示）。

        Args:
            data: 病历数据

        Returns:
            警告列表（非错误）
        """
        warnings = []

        diagnosis = data.get("diagnosis", "").lower()
        prescription = data.get("prescription", "").lower()

        # 简单的关键词检查（实际应使用 LLM 进行更智能的判断）
        if diagnosis and prescription:
            # 检查是否有抗生素相关诊断但无抗生素处方
            antibiotic_keywords = ["细菌", "感染", "炎症", "脓肿"]
            antibiotic_medications = ["阿莫西林", "头孢", "青霉素", "克拉霉素", "甲硝唑"]

            has_infection = any(kw in diagnosis for kw in antibiotic_keywords)
            has_antibiotics = any(med in prescription for med in antibiotic_medications)

            if has_infection and not has_antibiotics:
                warnings.append({
                    "field": "consistency",
                    "warning": "diagnosis_prescription_mismatch",
                    "message": "诊断包含感染相关描述，但处方中未包含抗生素"
                })

        return warnings

    def validate(self, data: Dict) -> Dict[str, Any]:
        """
        完整验证病历数据。

        Args:
            data: 病历数据

        Returns:
            验证结果字典
        """
        all_errors = []
        all_warnings = []

        # 必填字段验证
        required_errors = self.validate_required_fields(data)
        all_errors.extend(required_errors)

        # 字段长度验证
        length_errors = self.validate_field_lengths(data)
        all_errors.extend(length_errors)

        # 字段格式验证
        format_errors = self.validate_field_format(data)
        all_errors.extend(format_errors)

        # 业务逻辑验证（警告）
        business_warnings = self.validate_business_logic(data)
        all_warnings.extend(business_warnings)

        is_valid = len(all_errors) == 0

        return {
            "is_valid": is_valid,
            "errors": all_errors,
            "warnings": all_warnings,
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings)
        }

    def validate_or_raise(self, data: Dict) -> bool:
        """
        验证数据，如果无效则抛出异常。

        Args:
            data: 病历数据

        Returns:
            验证通过返回 True

        Raises:
            HTTPException: 验证失败时抛出 400 错误
        """
        result = self.validate(data)

        if not result["is_valid"]:
            details = {
                "error": "Validation failed",
                "message": f"发现 {result['total_errors']} 个验证错误",
                "errors": result["errors"]
            }

            if self.strict_mode and result["total_errors"] > 0:
                raise HTTPException(status_code=400, detail=details)

        return result["is_valid"]


# Global validator instance
default_validator = CaseDataValidator()


# ============================================================================
# FastAPI Middleware
# ============================================================================

async def validation_middleware(request: Request, call_next):
    """
    FastAPI 请求验证中间件。

    Args:
        request: HTTP 请求
        call_next: 下一个处理函数

    Returns:
        HTTP 响应
    """
    # Skip validation for non-POST requests and health checks
    if request.method != "POST":
        return await call_next(request)

    # Skip validation for specific endpoints
    path = request.url.path
    if path in ["/api/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    # Try to get JSON body
    try:
        body = await request.json()
    except Exception:
        # If not JSON, skip validation
        return await call_next(request)

    # Validate the request body
    validator = default_validator
    result = validator.validate(body)

    if not result["is_valid"]:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Validation failed",
                "message": f"发现 {result['total_errors']} 个验证错误",
                "errors": result["errors"],
                "warnings": result["warnings"]
            }
        )

    # Continue with the request
    return await call_next(request)


# ============================================================================
# Validation Helper Functions
# ============================================================================

def validate_case_data(
    case: Dict,
    required_fields: List[str] = None,
    min_lengths: Dict[str, int] = None
) -> Dict[str, Any]:
    """
    便捷的病历数据验证函数。

    Args:
        case: 病历数据
        required_fields: 必填字段列表
        min_lengths: 最小长度配置

    Returns:
        验证结果
    """
    validator = CaseDataValidator(
        required_fields=required_fields,
        min_lengths=min_lengths
    )
    return validator.validate(case)


def safe_validate_case(
    case: Dict,
    required_fields: List[str] = None
) -> Tuple[bool, List[Dict]]:
    """
    安全验证函数，返回 (is_valid, errors) 元组。

    Args:
        case: 病历数据
        required_fields: 必填字段列表

    Returns:
        (验证通过, 错误列表)
    """
    try:
        validator = CaseDataValidator(required_fields=required_fields)
        result = validator.validate(case)
        return result["is_valid"], result["errors"]
    except Exception:
        return False, [{"field": "unknown", "error": "validation_error", "message": "验证过程中发生未知错误"}]


if __name__ == "__main__":
    # 测试验证器
    test_cases = [
        # 合法病例
        {
            "patient_id": "PAT001",
            "main_complaint": "咳嗽3天",
            "present_illness": "患者3天前受凉后出现咳嗽，伴有发热。",
            "past_history": "既往体健",
            "physical_exam": "双肺呼吸音清",
            "auxiliary_exams": "血常规正常",
            "diagnosis": "急性支气管炎",
            "prescription": "阿莫西林 0.5g tid"
        },
        # 缺少必填字段
        {
            "patient_id": "PAT002",
            "main_complaint": "咳嗽"
            # 缺少其他必填字段
        },
        # 字段太短
        {
            "patient_id": "PAT003",
            "main_complaint": "咳嗽",
            "present_illness": "短",
            "past_history": "短",
            "physical_exam": "短",
            "auxiliary_exams": "短",
            "diagnosis": "短",
            "prescription": "短"
        }
    ]

    validator = CaseDataValidator()

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        result = validator.validate(case)
        print(f"  有效: {result['is_valid']}")
        print(f"  错误数: {result['total_errors']}")
        print(f"  警告数: {result['total_warnings']}")
        if result["errors"]:
            for error in result["errors"]:
                print(f"    - {error['field']}: {error['message']}")

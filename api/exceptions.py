"""
Custom Exceptions and Error Handling for Medical Record Inspector.

This module provides custom exceptions and error handling utilities
for the medical record quality assessment system.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse


# ============================================================================
# Custom Exceptions
# ============================================================================

class MedicalRecordInspectorError(Exception):
    """Medical Record Inspector 基础异常"""

    def __init__(self, message: str, code: str = None, details: Dict = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class APIError(MedicalRecordInspectorError):
    """API 相关异常"""
    pass


class ValidationError(MedicalRecordInspectorError):
    """数据验证异常"""
    pass


class FileNotFoundError(MedicalRecordInspectorError):
    """文件未找到异常"""
    pass


class ConfigError(MedicalRecordInspectorError):
    """配置相关异常"""
    pass


class LLMAPIError(MedicalRecordInspectorError):
    """LLM API 调用异常"""

    def __init__(
        self,
        message: str,
        status_code: int = None,
        raw_error: str = None,
        retryable: bool = True
    ):
        super().__init__(message, "LLM_API_ERROR")
        self.status_code = status_code
        self.raw_error = raw_error
        self.retryable = retryable


class RateLimitError(LLMAPIError):
    """LLM API 速率限制异常"""

    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message, status_code=429, retryable=True)
        self.retry_after = retry_after


class AuthenticationError(LLMAPIError):
    """LLM API 认证异常"""

    def __init__(self, message: str):
        super().__init__(message, status_code=401, retryable=False)
        self.retryable = False


# ============================================================================
# Error Response Schema
# ============================================================================

class ErrorResponse:
    """错误响应结构"""

    def __init__(
        self,
        success: bool = False,
        error: str = "Unknown error",
        code: str = "INTERNAL_ERROR",
        details: Dict[str, Any] = None,
        suggestion: str = None
    ):
        self.success = success
        self.error = error
        self.code = code
        self.details = details or {}
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "success": self.success,
            "error": self.error,
            "code": self.code
        }

        if self.details:
            result["details"] = self.details

        if self.suggestion:
            result["suggestion"] = self.suggestion

        return result


# ============================================================================
# Error Handlers
# ============================================================================

def handle_validation_error(exc: ValidationError) -> JSONResponse:
    """
    处理验证错误。

    Args:
        exc: 验证异常

    Returns:
        HTTP 400 响应
    """
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            success=False,
            error="Validation failed",
            code="VALIDATION_ERROR",
            details={"field": exc.field, "message": exc.message} if hasattr(exc, 'field') else {},
            suggestion="请检查输入数据格式和必填字段"
        ).to_dict()
    )


def handle_api_error(exc: APIError) -> JSONResponse:
    """
    处理 API 错误。

    Args:
        exc: API 异常

    Returns:
        HTTP 响应
    """
    status_code = 400 if exc.code.startswith("VALIDATION") else 500

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            success=False,
            error=exc.message,
            code=exc.code,
            details=exc.details,
            suggestion="请检查请求参数或稍后重试"
        ).to_dict()
    )


def handle_file_error(exc: FileNotFoundError) -> JSONResponse:
    """
    处理文件相关错误。

    Args:
        exc: 文件异常

    Returns:
        HTTP 404 响应
    """
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            success=False,
            error="File not found",
            code="FILE_NOT_FOUND",
            details={"path": exc.details.get("path", "unknown")},
            suggestion="请检查文件路径是否正确"
        ).to_dict()
    )


def handle_llm_error(exc: LLMAPIError) -> JSONResponse:
    """
    处理 LLM API 错误。

    Args:
        exc: LLM API 异常

    Returns:
        HTTP 响应
    """
    if exc.retryable:
        status_code = 503 if exc.status_code == 429 else 500
        suggestion = "服务暂时不可用，请稍后重试"
    else:
        status_code = 400
        suggestion = "请检查 API Key 是否正确"

    details = {"message": exc.message}
    if exc.raw_error:
        details["raw_error"] = exc.raw_error

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            success=False,
            error="LLM API Error",
            code=exc.code,
            details=details,
            suggestion=suggestion
        ).to_dict()
    )


def handle_generic_error(exc: Exception) -> JSONResponse:
    """
    处理通用错误。

    Args:
        exc: 异常对象

    Returns:
        HTTP 500 响应
    """
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="Internal server error",
            code="INTERNAL_ERROR",
            details={"type": type(exc).__name__},
            suggestion="服务器内部错误，请稍后重试。如问题持续，请联系管理员"
        ).to_dict()
    )


# ============================================================================
# Utility Functions
# ============================================================================

def create_error_response(
    error: str,
    code: str = "INTERNAL_ERROR",
    details: Dict[str, Any] = None,
    suggestion: str = None,
    status_code: int = 500
) -> JSONResponse:
    """
    创建错误响应。

    Args:
        error: 错误消息
        code: 错误代码
        details: 详细信息
        suggestion: 建议
        status_code: HTTP 状态码

    Returns:
        JSONResponse 对象
    """
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            success=False,
            error=error,
            code=code,
            details=details,
            suggestion=suggestion
        ).to_dict()
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    记录错误信息（用于日志）。

    Args:
        error: 异常对象
        context: 上下文信息

    Returns:
        日志条目字典
    """
    log_entry = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }

    if context:
        log_entry["context"] = context

    return log_entry


# ============================================================================
# Exception Handlers for FastAPI
# ============================================================================

class ExceptionHandlers:
    """异常处理器注册器"""

    def __init__(self, app=None):
        self.app = app
        self._handlers = {}

        # Register default handlers
        self.register_handler(HTTPException, self._handle_http_exception)
        self.register_handler(ValidationError, handle_validation_error)
        self.register_handler(APIError, handle_api_error)
        self.register_handler(FileNotFoundError, handle_file_error)
        self.register_handler(LLMAPIError, handle_llm_error)
        self.register_handler(Exception, handle_generic_error)

    def register_handler(self, exception_type, handler):
        """
        注册异常处理器。

        Args:
            exception_type: 异常类型
            handler: 处理函数
        """
        self._handlers[exception_type] = handler

        if self.app:
            self.app.add_exception_handler(exception_type, handler)

    def _handle_http_exception(self, request, exc: HTTPException):
        """处理 FastAPI HTTPException"""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                error=exc.detail if isinstance(exc.detail, str) else "Validation failed",
                code=f"HTTP_{exc.status_code}",
                suggestion="请检查请求参数"
            ).to_dict()
        )

    def handle(self, error: Exception) -> JSONResponse:
        """
        处理异常并返回响应。

        Args:
            error: 异常对象

        Returns:
            JSONResponse 对象
        """
        # Find the most specific handler
        for exc_type, handler in self._handlers.items():
            if isinstance(error, exc_type):
                return handler(error)

        # Fallback to generic handler
        return handle_generic_error(error)


# Global exception handler instance
exception_handlers = ExceptionHandlers()


# ============================================================================
# Retryable Exception Check
# ============================================================================

def is_retryable_error(error: Exception) -> bool:
    """
    判断错误是否可重试。

    Args:
        error: 异常对象

    Returns:
        是否可重试
    """
    if isinstance(error, LLMAPIError):
        return error.retryable

    retryable_types = (
        ConnectionError,
        TimeoutError,
        RateLimitError
    )

    return isinstance(error, retryable_types)


# ============================================================================
# Error Context Manager
# ============================================================================

class error_context:
    """错误上下文管理器，添加额外上下文信息"""

    def __init__(self, error: Exception, context: Dict[str, Any]):
        self.error = error
        self.context = context

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            if hasattr(exc_val, 'context'):
                exc_val.context.update(self.context)
            else:
                exc_val.context = self.context


if __name__ == "__main__":
    # Test custom exceptions
    try:
        raise ValidationError("Field 'main_complaint' is required", "VALIDATION_ERROR", {"field": "main_complaint"})
    except ValidationError as e:
        print(f"Caught ValidationError:")
        print(f"  Message: {e.message}")
        print(f"  Code: {e.code}")
        print(f"  Details: {e.details}")

    try:
        raise LLMAPIError("Rate limit exceeded", status_code=429, retryable=True)
    except LLMAPIError as e:
        print(f"\nCaught LLMAPIError:")
        print(f"  Message: {e.message}")
        print(f"  Status Code: {e.status_code}")
        print(f"  Retryable: {e.retryable}")

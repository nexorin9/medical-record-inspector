"""
Logging system for Medical Record Inspector.

This module provides structured logging for the application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime

from api.config import Config


class MedicalRecordLogger:
    """病历日志器"""

    def __init__(
        self,
        name: str = "medical_record_inspector",
        log_level: str = None,
        log_dir: str = None
    ):
        """
        初始化日志器。

        Args:
            name: 日志器名称
            log_level: 日志级别（DEBUG, INFO, WARNING, ERROR）
            log_dir: 日志文件目录
        """
        self.name = name
        self.log_level = log_level or Config.LOG_LEVEL
        self.log_dir = log_dir or "logs"

        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)

        # 创建日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.log_level.upper(), logging.INFO))

        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """设置日志处理器"""
        # 格式化器
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器（添加轮转）
        log_file = os.path.join(self.log_dir, "app.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """DEBUG 级别日志"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.debug(message)

    def info(self, message: str, **kwargs):
        """INFO 级别日志"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.info(message)

    def warning(self, message: str, **kwargs):
        """WARNING 级别日志"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.warning(message)

    def error(self, message: str, **kwargs):
        """ERROR 级别日志"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.error(message)

    def critical(self, message: str, **kwargs):
        """CRITICAL 级别日志"""
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.critical(message)


# 全局日志器实例
_logger: Optional[MedicalRecordLogger] = None


def get_logger(name: str = None) -> MedicalRecordLogger:
    """
    获取日志器实例。

    Args:
        name: 日志器名称，如果为 None 使用默认名称

    Returns:
        MedicalRecordLogger: 日志器实例
    """
    global _logger
    if _logger is None:
        _logger = MedicalRecordLogger(name=name)
    return _logger


def init_logger(name: str = None, log_level: str = None, log_dir: str = None) -> MedicalRecordLogger:
    """
    初始化日志器。

    Args:
        name: 日志器名称
        log_level: 日志级别
        log_dir: 日志文件目录

    Returns:
        MedicalRecordLogger: 日志器实例
    """
    global _logger
    _logger = MedicalRecordLogger(name=name, log_level=log_level, log_dir=log_dir)
    return _logger


def log_request(path: str, method: str, status_code: int, duration: float):
    """
    记录请求日志。

    Args:
        path: 请求路径
        method: 请求方法
        status_code: 状态码
        duration: 响应时间（秒）
    """
    logger = get_logger()
    logger.info(
        f"{method} {path} - {status_code} - {duration:.3f}s"
    )


def log_evaluation(patient_id: str, score: float, issues_count: int):
    """
    记录评估日志。

    Args:
        patient_id: 患者ID
        score: 评估分数
        issues_count: 问题数量
    """
    logger = get_logger()
    logger.info(
        f"Evaluation completed - Patient: {patient_id}, Score: {score:.1f}, Issues: {issues_count}"
    )


def log_api_call(model: str, tokens_used: int, duration: float):
    """
    记录 API 调用日志。

    Args:
        model: 使用的模型
        tokens_used: 使用的 token 数量
        duration: 耗时
    """
    logger = get_logger()
    logger.debug(
        f"API call - Model: {model}, Tokens: {tokens_used}, Duration: {duration:.3f}s"
    )


if __name__ == "__main__":
    # 测试日志系统
    logger = init_logger()

    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")

    # 测试结构化日志
    logger.info("用户登录", user_id="U001", ip="127.0.0.1")
    logger.info("评估完成", patient_id="P001", score=8.5, issues=2)

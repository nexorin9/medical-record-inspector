"""
日志系统模块 - Medical Record Interpreter
实现完整的日志记录，便于调试和追踪
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys

# 默认日志目录
DEFAULT_LOG_DIR = Path(__file__).parent.parent / 'logs'
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / 'app.log'


def setup_logging(
    log_dir: str = None,
    log_file: str = None,
    log_level: str = 'INFO',
    verbose: bool = False
) -> logging.Logger:
    """
    设置日志系统

    Args:
        log_dir: 日志目录
        log_file: 日志文件路径
        log_level: 日志级别
        verbose: 是否显示详细日志

    Returns:
        配置好的 logger 实例
    """
    # 设置日志目录和文件
    log_dir_path = Path(log_dir or str(DEFAULT_LOG_DIR))
    log_file_path = Path(log_file or str(DEFAULT_LOG_FILE))

    # 创建日志目录
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # 获取日志级别
    level = logging.DEBUG if verbose else getattr(logging, log_level.upper(), logging.INFO)

    # 创建 logger
    logger = logging.getLogger('medical_interpreter')
    logger.setLevel(level)

    # 如果已存在 handler，先清除
    if logger.handlers:
        logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件 handler
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file_path),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 每日轮转 handler（可选）
    # daily_handler = logging.handlers.TimedRotatingFileHandler(
    #     str(log_file_path),
    #     when='midnight',
    #     interval=1,
    #     backupCount=30,
    #     encoding='utf-8'
    # )
    # daily_handler.setLevel(level)
    # daily_handler.setFormatter(formatter)
    # logger.addHandler(daily_handler)

    logger.info(f"日志系统初始化完成")
    logger.info(f"日志级别: {log_level}")
    logger.info(f"日志文件: {log_file_path}")

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取 logger 实例

    Args:
        name: logger 名称

    Returns:
        logger 实例
    """
    logger_name = f"medical_interpreter.{name}" if name else "medical_interpreter"
    return logging.getLogger(logger_name)


def log_exception(func):
    """装饰器：记录函数异常"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = get_logger(func.__module__)
            logger.exception(f"函数 {func.__name__} 执行异常: {e}")
            raise
    return wrapper


if __name__ == '__main__':
    # 测试日志系统
    setup_logging(verbose=True)

    logger = get_logger()
    logger.info("测试日志系统")

    logger.debug("这是 debug 级别日志")
    logger.info("这是 info 级别日志")
    logger.warning("这是 warning 级别日志")
    logger.error("这是 error 级别日志")

    try:
        raise ValueError("测试异常")
    except Exception as e:
        logger.exception("捕获到异常")

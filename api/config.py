"""
Configuration management for Medical Record Inspector.

This module provides configuration loading from environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """配置类"""

    # Anthropic API Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # LLM Model Name
    MODEL_NAME: str = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20240620")

    # Logging Level
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Server Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Cache Configuration
    CACHE_EXPIRY_HOURS: int = int(os.getenv("CACHE_EXPIRY_HOURS", "24"))

    # LLM Request Configuration
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    @classmethod
    def validate(cls) -> bool:
        """
        验证必需的配置项。

        Returns:
            bool: 配置是否有效
        """
        if not cls.ANTHROPIC_API_KEY:
            return False
        return True

    @classmethod
    def get_api_key(cls) -> str:
        """
        获取 API 密钥，如果不存在则抛出异常。

        Returns:
            str: API 密钥

        Raises:
            ValueError: 如果 API 密钥未设置
        """
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY 未设置。请在 .env 文件中配置 API 密钥，"
                "或使用 ANTHROPIC_API_KEY 环境变量。"
            )
        return cls.ANTHROPIC_API_KEY


def load_config() -> Config:
    """
    加载配置。

    Returns:
        Config: 配置对象
    """
    return Config()


def check_config() -> dict:
    """
    检查配置并返回结果。

    Returns:
        dict: 配置检查结果
    """
    config = Config()
    result = {
        "ANTHROPIC_API_KEY": "configured" if config.ANTHROPIC_API_KEY else "missing",
        "MODEL_NAME": config.MODEL_NAME,
        "LOG_LEVEL": config.LOG_LEVEL,
        "PORT": config.PORT,
        "CACHE_EXPIRY_HOURS": config.CACHE_EXPIRY_HOURS,
        "REQUEST_TIMEOUT": config.REQUEST_TIMEOUT,
        "MAX_RETRIES": config.MAX_RETRIES
    }
    return result


if __name__ == "__main__":
    # 测试配置加载
    print("配置检查：")
    config_info = check_config()
    for key, value in config_info.items():
        print(f"  {key}: {value}")

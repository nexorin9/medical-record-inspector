"""
Configuration Loader for Medical Record Inspector.

This module provides YAML configuration file loading and management.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from api.config import Config


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置加载器。

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"配置文件解析错误: {e}")
                self.config = {}
        else:
            print(f"配置文件不存在: {self.config_path}，使用默认配置")
            self.config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项。

        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_evaluation_config(self) -> Dict[str, Any]:
        """获取评估配置"""
        return self.get('evaluation', {})

    def get_threshold_config(self) -> Dict[str, Any]:
        """获取阈值配置"""
        evaluation = self.get('evaluation', {})
        return evaluation.get('thresholds', {})

    def get_standard_path(self) -> str:
        """获取标准病历路径"""
        standards = self.get('standards', {})
        return standards.get('path', 'data/standard_cases')

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        return self.get('llm', {})

    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return self.get('cache', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})

    def get_batch_config(self) -> Dict[str, Any]:
        """获取批量处理配置"""
        return self.get('batch', {})


def load_config_from_file(config_path: str = "config.yaml") -> ConfigLoader:
    """
    从文件加载配置。

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigLoader 实例
    """
    return ConfigLoader(config_path)


def merge_config(config_loader: ConfigLoader) -> Dict[str, Any]:
    """
    合并配置文件和环境变量配置。

    Args:
        config_loader: 配置加载器

    Returns:
        合并后的配置字典
    """
    merged = {}

    # 从环境变量加载配置
    env_config = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "MODEL_NAME": os.getenv("MODEL_NAME", "claude-3-5-sonnet-20240620"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "PORT": int(os.getenv("PORT", "8000")),
    }

    # 从配置文件加载
    file_config = {}
    if config_loader:
        file_config = {
            "evaluation": config_loader.get_evaluation_config(),
            "standards": config_loader.get('standards', {}),
            "llm": config_loader.get_llm_config(),
            "cache": config_loader.get_cache_config(),
            "logging": config_loader.get_logging_config(),
            "batch": config_loader.get_batch_config(),
        }

    # 合并配置（文件配置优先）
    merged.update(env_config)
    merged.update(file_config)

    return merged


if __name__ == "__main__":
    # 测试配置加载
    print("测试配置加载...")

    # 尝试加载配置文件
    config_loader = load_config_from_file()

    # 显示配置项
    print("\n配置项:")
    print(f"  评估维度权重: {config_loader.get('evaluation.dimensions')}")
    print(f"  标准病历路径: {config_loader.get_standard_path()}")
    print(f"  LLM 模型: {config_loader.get('llm.model')}")
    print(f"  缓存过期时间: {config_loader.get('cache.expiry_hours')} 小时")

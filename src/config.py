"""
配置管理模块 - Medical Record Inspector
实现配置文件系统，支持用户自定义参数
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""

    def __init__(self, config_path: str = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or 'config.yaml'
        self.config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """加载配置文件"""
        path = Path(self.config_path)

        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"配置文件加载成功: {self.config_path}")
            except Exception as e:
                logger.warning(f"配置文件加载失败，使用默认配置: {e}")
                self.config = {}
        else:
            logger.info(f"配置文件不存在，使用默认配置: {self.config_path}")
            self._save_defaults()

    def _save_defaults(self) -> None:
        """保存默认配置"""
        default_config = {
            'similarity_threshold': 0.7,
            'anomaly_sensitivity': 0.95,
            'llm': {
                'model': 'gpt-4',
                'api_base': 'https://api.openai.com/v1',
                'temperature': 0.3,
                'max_tokens': 500
            },
            'embedder': {
                'model': 'BAAI/bge-micro-v2',
                'device': 'auto'
            },
            'locator': {
                'chunk_size': 5,
                'min_chunk_length': 50
            }
        }

        self.config = default_config
        self.save()

    def save(self) -> None:
        """保存配置到文件"""
        path = Path(self.config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"配置已保存到: {self.config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键（支持嵌套，用点分隔）
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

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    # convenience methods
    @property
    def similarity_threshold(self) -> float:
        """相似度阈值"""
        return self.get('similarity_threshold', 0.7)

    @property
    def anomaly_sensitivity(self) -> float:
        """异常检测灵敏度"""
        return self.get('anomaly_sensitivity', 0.95)

    @property
    def llm_model(self) -> str:
        """LLM 模型名称"""
        return self.get('llm.model', 'gpt-4')

    @property
    def llm_api_base(self) -> str:
        """LLM API 基础 URL"""
        return self.get('llm.api_base', 'https://api.openai.com/v1')

    @property
    def embedder_model(self) -> str:
        """嵌入模型名称"""
        return self.get('embedder.model', 'BAAI/bge-micro-v2')

    @property
    def embedder_device(self) -> str:
        """嵌入模型设备"""
        device = self.get('embedder.device', 'auto')
        if device == 'auto':
            return 'cuda' if __import__('torch').cuda.is_available() else 'cpu'
        return device


def get_config(config_path: str = None) -> Config:
    """获取全局配置实例"""
    if not hasattr(get_config, '_instance'):
        get_config._instance = Config(config_path)
    return get_config._instance


def load_config_from_env() -> Dict[str, Any]:
    """从环境变量加载配置"""
    config = {}

    if os.environ.get('SIMILARITY_THRESHOLD'):
        config['similarity_threshold'] = float(os.environ['SIMILARITY_THRESHOLD'])

    if os.environ.get('LLM_MODEL'):
        config['llm'] = config.get('llm', {})
        config['llm']['model'] = os.environ['LLM_MODEL']

    if os.environ.get('LLM_API_BASE'):
        config['llm'] = config.get('llm', {})
        config['llm']['api_base'] = os.environ['LLM_API_BASE']

    if os.environ.get('EMBEDDER_MODEL'):
        config['embedder'] = config.get('embedder', {})
        config['embedder']['model'] = os.environ['EMBEDDER_MODEL']

    return config


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=== Config 测试 ===\n")

    # 创建配置
    config = get_config()

    print("当前配置:")
    print(f"  相似度阈值: {config.similarity_threshold}")
    print(f"  异常灵敏度: {config.anomaly_sensitivity}")
    print(f"  LLM 模型: {config.llm_model}")
    print(f"  嵌入模型: {config.embedder_model}")

    # 设置新值
    print("\n设置新配置:")
    config.set('similarity_threshold', 0.8)
    print(f"  新相似度阈值: {config.similarity_threshold}")

    # 保存配置
    config.save()

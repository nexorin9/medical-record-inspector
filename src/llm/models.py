"""
LLM Model Configuration - Model definitions and token limits
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LLMModel:
    """LLM Model configuration"""
    name: str
    provider: str
    max_tokens: int
    context_tokens: int
    cost_per_million_input: float
    cost_per_million_output: float
    description: str = ""
    is_default: bool = False


# Available models by provider
AVAILABLE_MODELS: Dict[str, List[LLMModel]] = {
    "openai": [
        LLMModel(
            name="gpt-4",
            provider="openai",
            max_tokens=4096,
            context_tokens=8192,
            cost_per_million_input=30.0,
            cost_per_million_output=30.0,
            description="GPT-4 最佳平衡性能和成本",
            is_default=True
        ),
        LLMModel(
            name="gpt-4-turbo",
            provider="openai",
            max_tokens=4096,
            context_tokens=128000,
            cost_per_million_input=30.0,
            cost_per_million_output=30.0,
            description="GPT-4 Turbo 支持长上下文",
            is_default=False
        ),
        LLMModel(
            name="gpt-4o",
            provider="openai",
            max_tokens=4096,
            context_tokens=128000,
            cost_per_million_input=5.0,
            cost_per_million_output=15.0,
            description="GPT-4o 多模态旗舰模型",
            is_default=False
        ),
        LLMModel(
            name="gpt-3.5-turbo",
            provider="openai",
            max_tokens=16385,
            context_tokens=16385,
            cost_per_million_input=0.5,
            cost_per_million_output=0.5,
            description="GPT-3.5 Turbo 快速且经济",
            is_default=False
        ),
    ],
    "dashscope": [
        LLMModel(
            name="qwen-plus",
            provider="dashscope",
            max_tokens=8192,
            context_tokens=32768,
            cost_per_million_input=2.0,
            cost_per_million_output=2.0,
            description="通义千问 Plus 平衡性能",
            is_default=True
        ),
        LLMModel(
            name="qwen-max",
            provider="dashscope",
            max_tokens=8192,
            context_tokens=32768,
            cost_per_million_input=2.0,
            cost_per_million_output=2.0,
            description="通义千问 Max 最强性能",
            is_default=False
        ),
        LLMModel(
            name="qwen-turbo",
            provider="dashscope",
            max_tokens=8192,
            context_tokens=32768,
            cost_per_million_input=0.5,
            cost_per_million_output=0.5,
            description="通义千问 Turbo 快速响应",
            is_default=False
        ),
    ],
    "ernie": [
        LLMModel(
            name="ERNIE-Bot-4",
            provider="ernie",
            max_tokens=4096,
            context_tokens=4096,
            cost_per_million_input=0.3,
            cost_per_million_output=0.3,
            description="文心一言 4.0 最强性能",
            is_default=True
        ),
        LLMModel(
            name="ERNIE-Bot-3",
            provider="ernie",
            max_tokens=4096,
            context_tokens=4096,
            cost_per_million_input=0.15,
            cost_per_million_output=0.15,
            description="文心一言 3.0 快速响应",
            is_default=False
        ),
    ],
    "local": [
        LLMModel(
            name="llama-3-70b",
            provider="local",
            max_tokens=8192,
            context_tokens=8192,
            cost_per_million_input=0.9,
            cost_per_million_output=0.9,
            description="Llama 3 70B 本地部署",
            is_default=True
        ),
        LLMModel(
            name="llama-3-8b",
            provider="local",
            max_tokens=8192,
            context_tokens=8192,
            cost_per_million_input=0.1,
            cost_per_million_output=0.1,
            description="Llama 3 8B 轻量级本地部署",
            is_default=False
        ),
    ],
}


def get_model_by_name(model_name: str, provider: Optional[str] = None) -> Optional[LLMModel]:
    """Get model configuration by name"""
    for prov, models in AVAILABLE_MODELS.items():
        if provider and prov != provider:
            continue
        for model in models:
            if model.name.lower() == model_name.lower():
                return model
    return None


def get_available_providers() -> List[str]:
    """Get list of available providers"""
    return list(AVAILABLE_MODELS.keys())


def get_models_by_provider(provider: str) -> List[LLMModel]:
    """Get models by provider"""
    return AVAILABLE_MODELS.get(provider, [])


def get_default_model(provider: Optional[str] = None) -> Optional[LLMModel]:
    """Get default model for provider"""
    if provider:
        for model in AVAILABLE_MODELS.get(provider, []):
            if model.is_default:
                return model
        return AVAILABLE_MODELS.get(provider, [None])[0] if AVAILABLE_MODELS.get(provider) else None
    else:
        # Return first default model found
        for models in AVAILABLE_MODELS.values():
            for model in models:
                if model.is_default:
                    return model
    return None

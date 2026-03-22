"""
LLM Client Module - Support multiple LLM providers
"""

import asyncio
import os
import time
import json
import logging
from typing import Optional, List, Dict, Any
from functools import lru_cache

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Custom exception for LLM errors"""
    pass


class LLMClient:
    """
    LLM Client supporting multiple providers:
    - OpenAI (GPT-4, GPT-3.5)
    - Tongyi Qianwen (DashScope)
    - ERNIE Bot (Baidu)
    - Local LLM (llama.cpp compatible APIs)
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize LLM Client

        Args:
            provider: LLM provider (openai, dashscope, ernie, local)
            api_key: API key for the provider
            model_name: Model name to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
        self.api_key = api_key or self._get_api_key()
        self.model_name = model_name or os.getenv("MODEL_NAME", "GPT-4")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries

        # Model configuration
        self.model_configs = {
            "gpt-4": {"max_tokens": 8192, "cost_per_million": 30.0},
            "gpt-4-turbo": {"max_tokens": 128000, "cost_per_million": 30.0},
            "gpt-3.5-turbo": {"max_tokens": 16385, "cost_per_million": 0.5},
            "qwen-plus": {"max_tokens": 8192, "cost_per_million": 2.0},
            "qwen-max": {"max_tokens": 8192, "cost_per_million": 2.0},
            "qwen-turbo": {"max_tokens": 8192, "cost_per_million": 0.5},
            "ERNIE-Bot-4": {"max_tokens": 4096, "cost_per_million": 0.3},
            "ERNIE-Bot-3": {"max_tokens": 4096, "cost_per_million": 0.15},
            "llama-3-70b": {"max_tokens": 8192, "cost_per_million": 0.9},
            "llama-3-8b": {"max_tokens": 8192, "cost_per_million": 0.1},
        }

        # Provider endpoints
        self.endpoints = {
            "openai": os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
            "dashscope": os.getenv("DASHSCOPE_ENDPOINT", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"),
            "ernie": os.getenv("ERNIE_ENDPOINT", "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"),
            "local": os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:8080/v1/chat/completions"),
        }

        # Validate provider
        if self.provider not in self.endpoints:
            raise ValueError(f"Unsupported provider: {self.provider}. Must be one of: {list(self.endpoints.keys())}")

        logger.info(f"LLM Client initialized with provider: {self.provider}, model: {self.model_name}")

    def _get_api_key(self) -> str:
        """Get API key based on provider"""
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY", "")
        elif self.provider == "dashscope":
            return os.getenv("DASHSCOPE_API_KEY", "")
        elif self.provider == "ernie":
            api_key = os.getenv("ERNIE_API_KEY", "")
            secret_key = os.getenv("ERNIE_SECRET_KEY", "")
            if api_key and secret_key:
                return f"{api_key}:{secret_key}"
            return api_key
        elif self.provider == "local":
            return os.getenv("LOCAL_LLM_API_KEY", "dummy")
        return ""

    def _get_model_config(self, model: str) -> Dict[str, Any]:
        """Get configuration for a model"""
        model_lower = model.lower()
        for key, config in self.model_configs.items():
            if key.lower() in model_lower:
                return config
        # Default config
        return {"max_tokens": 4096, "cost_per_million": 1.0}

    @lru_cache(maxsize=100)
    def _is_long_context_model(self, model: str) -> bool:
        """Check if model supports long context"""
        model_lower = model.lower()
        long_context_models = ["gpt-4-turbo", "gpt-4o", "qwen-max", "qwen-plus"]
        return any(m in model_lower for m in long_context_models)

    async def _call_openai_api(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Call OpenAI API"""
        # Prepare messages
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        # Prepare request
        payload = {
            "model": self.model_name,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoints["openai"],
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def _call_dashscope_api(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Call DashScope (Tongyi Qianwen) API"""
        # Prepare messages
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "input": {
                "messages": full_messages
            },
            "parameters": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        }

        if json_mode:
            payload["parameters"]["response_format"] = "json_object"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoints["dashscope"],
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def _call_ernie_api(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Call ERNIE Bot API"""
        # ERNIE doesn't support system prompt directly, prepend to user message
        full_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user" and system_prompt:
                content = f"{system_prompt}\n\n{content}"
            full_messages.append({"role": role, "content": content})

        payload = {
            "messages": full_messages,
            "temperature": self.temperature,
            "top_p": 0.7,
            "penalty_score": 1.0,
        }

        if json_mode:
            payload["response_format"] = "json"

        headers = {
            "Content-Type": "application/json",
        }

        # ERNIE uses access token, get from API key if needed
        access_token = self.api_key
        if ":" in access_token:
            # Need to get access token from api_key:secret_key
            api_key, secret_key = access_token.split(":", 1)
            access_token = await self._get_ernie_access_token(api_key, secret_key)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.endpoints['ernie']}/chat/completions?access_token={access_token}",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def _get_ernie_access_token(self, api_key: str, secret_key: str) -> str:
        """Get ERNIE access token from API key and secret key"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

    async def _call_local_api(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Call local LLM API (llama.cpp compatible)"""
        # Prepare messages
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.model_name,
            "messages": full_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.endpoints["local"],
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def _call_provider_api(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Call the appropriate provider API"""
        if self.provider == "openai":
            return await self._call_openai_api(messages, system_prompt, json_mode)
        elif self.provider == "dashscope":
            return await self._call_dashscope_api(messages, system_prompt, json_mode)
        elif self.provider == "ernie":
            return await self._call_ernie_api(messages, system_prompt, json_mode)
        elif self.provider == "local":
            return await self._call_local_api(messages, system_prompt, json_mode)
        else:
            raise LLMError(f"Unsupported provider: {self.provider}")

    async def _retry_call(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """Call API with retry mechanism"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self._call_provider_api(messages, system_prompt, json_mode)
            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {last_error}")
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP error {e.response.status_code}: {e.response.text}"
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {last_error}")
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {last_error}")

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)

        raise LLMError(f"API call failed after {self.max_retries} attempts: {last_error}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response from LLM

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            json_mode: Whether to request JSON output
            messages: Optional list of messages (for multi-turn对话)

        Returns:
            Dict with response text and metadata
        """
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        start_time = time.time()

        try:
            response = await self._retry_call(messages, system_prompt, json_mode)

            # Extract response based on provider
            output_text = self._extract_response_text(response)

            return {
                "text": output_text,
                "raw_response": response,
                "provider": self.provider,
                "model": self.model_name,
                "prompt_tokens": self._count_tokens(prompt),
                "completion_tokens": self._count_tokens(output_text),
                "total_tokens": self._count_tokens(prompt) + self._count_tokens(output_text),
                "cost_estimate": self._estimate_cost(prompt, output_text),
                "latency_ms": (time.time() - start_time) * 1000,
            }
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMError(f"LLM generation failed: {e}")

    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """Extract response text from provider response"""
        if self.provider == "openai":
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        elif self.provider == "dashscope":
            return response.get("output", {}).get("text", "")
        elif self.provider == "ernie":
            return response.get("result", "")
        elif self.provider == "local":
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ""

    def _count_tokens(self, text: str) -> int:
        """Approximate token count (1 token ~ 4 characters in English)"""
        if not text:
            return 0
        # Simple approximation: 1 token ≈ 4 characters for English
        # For Chinese: 1 token ≈ 2 characters
        return max(1, len(text) // 4)

    def _estimate_cost(self, prompt: str, completion: str) -> float:
        """Estimate API cost based on token usage"""
        config = self._get_model_config(self.model_name)
        cost_per_million = config.get("cost_per_million", 1.0)

        prompt_tokens = self._count_tokens(prompt)
        completion_tokens = self._count_tokens(completion)
        total_tokens = prompt_tokens + completion_tokens

        return (total_tokens / 1_000_000) * cost_per_million

    async def train(self):
        """Placeholder for training method (if needed for fine-tuning)"""
        logger.warning("Training not implemented for this client")
        raise NotImplementedError("Training not implemented")

    def clear_cache(self):
        """Clear LRU cache"""
        self._is_long_context_model.cache_clear()
        logger.info("LLM cache cleared")


# Simple synchronous wrapper for convenience
def create_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 60.0,
    max_retries: int = 3
) -> LLMClient:
    """
    Factory function to create LLM client

    Args:
        provider: LLM provider (openai, dashscope, ernie, local)
        api_key: API key for the provider
        model_name: Model name to use
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        LLMClient instance
    """
    return LLMClient(
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        max_retries=max_retries
    )


# Async wrapper for simple usage
async def generate_text(
    prompt: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    system_prompt: Optional[str] = None,
    json_mode: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to generate text

    Args:
        prompt: User prompt
        provider: LLM provider
        api_key: API key
        model_name: Model name
        system_prompt: Optional system prompt
        json_mode: Whether to request JSON output

    Returns:
        Dict with response text and metadata
    """
    client = create_llm_client(
        provider=provider,
        api_key=api_key,
        model_name=model_name
    )
    return await client.generate(prompt, system_prompt, json_mode)

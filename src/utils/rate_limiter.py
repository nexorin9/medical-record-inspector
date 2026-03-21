"""
限流器 - Rate Limiter
实现请求限流功能
"""

import time
import threading
from collections import deque
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """限流配置"""
    max_requests: int = 10  # 最大请求数
    window_seconds: int = 60  # 时间窗口（秒）


class TokenBucket:
    """
    令牌桶限流器

    支持突发流量处理
    """

    def __init__(
        self,
        rate: float = 10.0,  # 令牌生成速率（个/秒）
        capacity: int = 20,  # 桶容量
        initial_tokens: Optional[float] = None
    ):
        """
        初始化令牌桶

        Args:
            rate: 令牌生成速率（个/秒）
            capacity: 桶容量
            initial_tokens: 初始令牌数，默认为容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_update = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: float = 1.0) -> bool:
        """
        尝试消耗令牌

        Args:
            tokens: 需要消耗的令牌数

        Returns:
            是否成功获取令牌
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_tokens(self) -> float:
        """获取当前令牌数"""
        with self._lock:
            self._refill()
            return self.tokens

    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now


class SlidingWindowCounter:
    """
    滑动窗口计数器限流器

    更精确的限流方式
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        初始化滑动窗口计数器

        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: deque = deque()
        self._lock = threading.Lock()

    def is_allowed(self) -> bool:
        """
        检查是否允许请求

        Returns:
            是否允许
        """
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            # 移除过期的请求记录
            while self._requests and self._requests[0] < window_start:
                self._requests.popleft()

            # 检查是否超过限制
            if len(self._requests) >= self.max_requests:
                return False

            # 记录当前请求
            self._requests.append(now)
            return True

    def get_remaining(self) -> int:
        """获取剩余请求数"""
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            # 移除过期的请求记录
            while self._requests and self._requests[0] < window_start:
                self._requests.popleft()

            return max(0, self.max_requests - len(self._requests))


class RateLimiter:
    """
    限流器管理器

    支持多种限流策略
    """

    def __init__(self):
        """初始化限流器"""
        # 全局限流（令牌桶）
        self._global_bucket = TokenBucket(rate=10.0, capacity=20)

        # 每客户端限流（滑动窗口）
        self._client_windows: Dict[str, SlidingWindowCounter] = {}
        self._client_lock = threading.Lock()

    def is_allowed(self, client_id: Optional[str] = None) -> bool:
        """
        检查请求是否被允许

        Args:
            client_id: 客户端 ID，如未提供则仅检查全局限流

        Returns:
            是否允许
        """
        # 检查全局限流
        if not self._global_bucket.consume():
            return False

        # 检查客户端限流
        if client_id:
            with self._client_lock:
                if client_id not in self._client_windows:
                    self._client_windows[client_id] = SlidingWindowCounter(
                        max_requests=5,  # 每客户端每分钟限制
                        window_seconds=60
                    )
                return self._client_windows[client_id].is_allowed()

        return True

    def get_remaining(self, client_id: Optional[str] = None) -> int:
        """获取剩余配额"""
        remaining = self._global_bucket.get_tokens()
        if client_id:
            with self._client_lock:
                if client_id in self._client_windows:
                    remaining = min(
                        remaining,
                        self._client_windows[client_id].get_remaining()
                    )
        return int(remaining)

    def reset_client(self, client_id: str) -> None:
        """重置客户端限流"""
        with self._client_lock:
            if client_id in self._client_windows:
                del self._client_windows[client_id]


# 全局单例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def check_rate_limit(client_id: Optional[str] = None) -> bool:
    """检查请求是否被允许（全局快捷函数）"""
    return get_rate_limiter().is_allowed(client_id)


def get_rate_limit_remaining(client_id: Optional[str] = None) -> int:
    """获取剩余配额（全局快捷函数）"""
    return get_rate_limiter().get_remaining(client_id)

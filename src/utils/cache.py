"""
缓存工具 - Cache Utils
用于缓存评估结果，减少重复 LLM 调用
"""

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import threading


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Dict[str, Any]
    created_at: str
    expires_at: str
    hit_count: int = 0


class LRUCache:
    """
    LRU 缓存实现（内存级）

    支持：
    - LRU 淘汰策略
    - 过期自动清理
    - 线程安全
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒），默认 1 小时
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._usage_order: list = []  # 按使用顺序存储 key
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存条目

        Args:
            key: 缓存键

        Returns:
            缓存值，如不存在或已过期则返回 None
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # 检查是否过期
            if self._is_expired(entry):
                self._remove(key)
                return None

            # 更新使用顺序（移到末尾）
            self._usage_order.remove(key)
            self._usage_order.append(key)

            # 更新命中次数
            entry.hit_count += 1
            self._save_cache()

            return entry.value

    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        设置缓存条目

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如未提供则使用默认值
        """
        if ttl is None:
            ttl = self.default_ttl

        with self._lock:
            now = datetime.utcnow().isoformat()
            expire_time = datetime.utcfromtimestamp(
                time.time() + ttl
            ).isoformat()

            # 如果 key 已存在，先移除
            if key in self._cache:
                self._usage_order.remove(key)
                del self._cache[key]

            # 如果达到最大容量，移除最久未使用的条目
            while len(self._cache) >= self.max_size:
                if self._usage_order:
                    oldest_key = self._usage_order.pop(0)
                    if oldest_key in self._cache:
                        del self._cache[oldest_key]

            # 添加新条目
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=expire_time,
                hit_count=0
            )
            self._usage_order.append(key)
            self._save_cache()

    def delete(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                self._usage_order.remove(key)
                del self._cache[key]
                self._save_cache()
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._usage_order.clear()
            self._save_cache()

    def cleanup_expired(self) -> int:
        """
        清理所有已过期的缓存条目

        Returns:
            清理的条目数量
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            for key in expired_keys:
                self._remove(key)
            self._save_cache()
            return len(expired_keys)

    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self._cache)

    def keys(self) -> list:
        """获取所有缓存键"""
        return list(self._cache.keys())

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查条目是否已过期"""
        expires_at = datetime.fromisoformat(entry.expires_at)
        return datetime.utcnow() > expires_at

    def _remove(self, key: str) -> None:
        """移除缓存条目"""
        if key in self._cache:
            self._usage_order.remove(key)
            del self._cache[key]

    def _save_cache(self) -> None:
        """保存缓存到文件（用于持久化）"""
        try:
            cache_data = {
                "entries": {
                    k: asdict(v) for k, v in self._cache.items()
                },
                "usage_order": self._usage_order,
                "saved_at": datetime.utcnow().isoformat()
            }
            self._persist_cache(cache_data)
        except Exception:
            pass  # 忽略保存错误

    def _persist_cache(self, data: dict) -> None:
        """持久化缓存数据（可被子类重写）"""
        pass


class FileCache(LRUCache):
    """
    基于文件的 LRU 缓存

    支持：
    - 持久化到本地文件
    - LRU 淘汰策略
    - 过期自动清理
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        cache_dir: Optional[str] = None
    ):
        """
        初始化文件缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
            cache_dir: 缓存目录，如未提供则使用临时目录
        """
        super().__init__(max_size=max_size, default_ttl=default_ttl)
        self.cache_dir = Path(cache_dir or tempfile.gettempdir()) / "medical_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cache.json"
        self._load_cache()

    def _persist_cache(self, data: dict) -> None:
        """持久化缓存到文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_cache(self) -> None:
        """从文件加载缓存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 重新构建缓存
                self._cache.clear()
                self._usage_order.clear()

                for key, entry_data in data.get("entries", {}).items():
                    # 检查是否过期
                    expires_at = datetime.fromisoformat(entry_data["expires_at"])
                    if datetime.utcnow() < expires_at:
                        entry = CacheEntry(**entry_data)
                        self._cache[key] = entry
                        self._usage_order.append(key)
        except Exception:
            pass  # 忽略加载错误


class CacheManager:
    """
    缓存管理器

    统一管理所有缓存操作
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
        """
        self._file_cache = FileCache(
            max_size=1000,
            default_ttl=3600,  # 1 小时
            cache_dir=cache_dir
        )

    def get_cache_key(self, content: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        生成缓存键

        规则：hash(content + config_json)

        Args:
            content: 病历内容
            config: 配置参数

        Returns:
            缓存键（十六进制字符串）
        """
        config_str = json.dumps(config or {}, sort_keys=True)
        key_str = content + config_str
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存结果

        Args:
            key: 缓存键

        Returns:
            缓存结果，如不存在或已过期则返回 None
        """
        return self._file_cache.get(key)

    def set(self, key: str, result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        设置缓存结果

        Args:
            key: 缓存键
            result: 评估结果
            ttl: 过期时间（秒）

        Returns:
            是否成功
        """
        self._file_cache.set(key, result, ttl)
        return True

    def delete(self, key: str) -> bool:
        """
        删除缓存结果

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        return self._file_cache.delete(key)

    def clear(self) -> None:
        """清空所有缓存"""
        self._file_cache.clear()

    def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的条目数量
        """
        return self._file_cache.cleanup_expired()

    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息字典
        """
        total_hits = sum(
            entry.hit_count for entry in self._file_cache._cache.values()
        )
        return {
            "total_entries": len(self._file_cache._cache),
            "total_hits": total_hits,
            "cache_dir": str(self._file_cache.cache_dir),
        }


# 全局单例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def clear_cache():
    """清空缓存（全局快捷函数）"""
    manager = get_cache_manager()
    manager.clear()

"""
Local Cache System for Medical Record Inspector.

This module provides local caching for evaluation results to avoid
repeated LLM API calls for the same inputs.
"""

import os
import hashlib
import json
import time
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

from api.config import Config
from api.logger import get_logger

logger = get_logger(__name__)


class LocalCache:
    """本地缓存系统"""

    def __init__(
        self,
        cache_dir: str = "data/cache",
        expiry_hours: int = None
    ):
        """
        初始化缓存系统。

        Args:
            cache_dir: 缓存目录
            expiry_hours: 缓存过期时间（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.expiry_hours = expiry_hours or Config.CACHE_EXPIRY_HOURS
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }

    def _generate_cache_key(self, data: Dict) -> str:
        """
        生成缓存键。

        Args:
            data: 输入数据

        Returns:
            缓存键（MD5 哈希）
        """
        # 只对相关字段进行哈希
        relevant_data = {
            "main_complaint": data.get("main_complaint", ""),
            "present_illness": data.get("present_illness", ""),
            "past_history": data.get("past_history", ""),
            "physical_exam": data.get("physical_exam", ""),
            "auxiliary_exams": data.get("auxiliary_exams", ""),
            "diagnosis": data.get("diagnosis", ""),
            "prescription": data.get("prescription", "")
        }

        data_str = json.dumps(relevant_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{key}.json"

    def get(self, data: Dict) -> Optional[Dict]:
        """
        从缓存获取结果。

        Args:
            data: 输入数据

        Returns:
            缓存的结果，如果不存在或已过期则返回 None
        """
        cache_key = self._generate_cache_key(data)
        cache_path = self._get_cache_path(cache_key)

        self.stats["total_requests"] += 1

        if not cache_path.exists():
            self.stats["misses"] += 1
            logger.debug(f"Cache miss for key: {cache_key}")
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # 检查是否过期
            timestamp = cached.get("timestamp", 0)
            expiry_time = timestamp + (self.expiry_hours * 3600)
            current_time = time.time()

            if current_time > expiry_time:
                logger.debug(f"Cache expired for key: {cache_key}")
                self.stats["misses"] += 1
                # 删除过期缓存
                cache_path.unlink()
                return None

            self.stats["hits"] += 1
            logger.debug(f"Cache hit for key: {cache_key}")
            return cached.get("result")

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Cache read error for key {cache_key}: {e}")
            self.stats["misses"] += 1
            return None

    def set(self, data: Dict, result: Dict) -> None:
        """
        将结果存入缓存。

        Args:
            data: 输入数据
            result: 评估结果
        """
        cache_key = self._generate_cache_key(data)
        cache_path = self._get_cache_path(cache_key)

        try:
            cache_entry = {
                "key": cache_key,
                "timestamp": time.time(),
                "version": "1.0",
                "result": result
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)

            logger.debug(f"Cache set for key: {cache_key}")

        except IOError as e:
            logger.error(f"Cache write error for key {cache_key}: {e}")

    def delete(self, data: Dict) -> bool:
        """
        删除缓存。

        Args:
            data: 输入数据

        Returns:
            是否成功删除
        """
        cache_key = self._generate_cache_key(data)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Cache deleted for key: {cache_key}")
            return True

        return False

    def clear(self) -> int:
        """
        清空所有缓存。

        Returns:
            删除的文件数量
        """
        deleted = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                deleted += 1
            except OSError as e:
                logger.error(f"Failed to delete cache file {cache_file}: {e}")

        logger.info(f"Cleared {deleted} cache files")
        return deleted

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息。

        Returns:
            缓存统计字典
        """
        return {
            **self.stats,
            "cache_dir": str(self.cache_dir),
            "expiry_hours": self.expiry_hours,
            "hit_rate": round(
                self.stats["hits"] / self.stats["total_requests"] * 100, 2
            ) if self.stats["total_requests"] > 0 else 0
        }

    def get_cache_size(self) -> int:
        """
       Get cache directory size in bytes.

        Returns:
            缓存大小（字节）
        """
        total_size = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                total_size += cache_file.stat().st_size
            except OSError:
                pass
        return total_size

    def cleanup_expired(self) -> int:
        """
        清理过期缓存。

        Returns:
            清理的文件数量
        """
        cleaned = 0
        current_time = time.time()
        expiry_seconds = self.expiry_hours * 3600

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)

                timestamp = cached.get("timestamp", 0)
                if current_time > timestamp + expiry_seconds:
                    cache_file.unlink()
                    cleaned += 1
                    logger.debug(f"Cleaned expired cache: {cache_file.name}")

            except (json.JSONDecodeError, OSError):
                # 无法读取的文件也删除
                try:
                    cache_file.unlink()
                    cleaned += 1
                except OSError:
                    pass

        return cleaned


# 全局缓存实例
_cache: Optional[LocalCache] = None


def get_cache() -> LocalCache:
    """
    获取全局缓存实例。

    Returns:
        LocalCache 实例
    """
    global _cache
    if _cache is None:
        _cache = LocalCache()
    return _cache


def init_cache(cache_dir: str = None, expiry_hours: int = None) -> LocalCache:
    """
    初始化全局缓存。

    Args:
        cache_dir: 缓存目录
        expiry_hours: 过期时间（小时）

    Returns:
        LocalCache 实例
    """
    global _cache
    _cache = LocalCache(
        cache_dir=cache_dir or "data/cache",
        expiry_hours=expiry_hours
    )
    return _cache


def clear_cache():
    """清空全局缓存"""
    if _cache:
        _cache.clear()


if __name__ == "__main__":
    # 测试缓存系统
    cache = LocalCache()

    # 测试数据
    test_data = {
        "main_complaint": "咳嗽3天",
        "present_illness": "患者3天前受凉后出现咳嗽",
        "past_history": "无特殊",
        "physical_exam": "双肺呼吸音清",
        "auxiliary_exams": "血常规正常",
        "diagnosis": "急性支气管炎",
        "prescription": "阿莫西林 0.5g tid"
    }

    test_result = {
        "assessment_id": "TEST-001",
        "overall_score": 8.5,
        "issues": [],
        "report": "测试结果"
    }

    # 测试缓存
    print("测试缓存系统...")
    print(f"首次查询（应为 None）: {cache.get(test_data)}")
    print(f"统计: {cache.get_stats()}")

    # 设置缓存
    cache.set(test_data, test_result)
    print("缓存已设置")

    # 再次查询
    print(f"二次查询（应命中缓存）: {cache.get(test_data)}")
    print(f"统计: {cache.get_stats()}")

    # 清除缓存
    cache.clear()
    print(f"清除缓存后统计: {cache.get_stats()}")

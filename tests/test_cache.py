"""
测试缓存逻辑
tests/test_cache.py
"""

import sys
import os
import time

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.cache import LRUCache, CacheManager, get_cache_manager


def test_lru_cache_basic():
    """测试 LRU 缓存基本操作"""
    cache = LRUCache(max_size=3, default_ttl=60)

    # 设置缓存
    cache.set("key1", {"value": "test1"})
    assert cache.get("key1") == {"value": "test1"}

    # 覆盖缓存
    cache.set("key1", {"value": "test1_updated"})
    assert cache.get("key1") == {"value": "test1_updated"}

    # 添加多个键
    cache.set("key2", {"value": "test2"})
    cache.set("key3", {"value": "test3"})
    assert cache.size() == 3

    # 超出容量，evict 最旧的键 (key1 is the oldest at this point)
    cache.set("key4", {"value": "test4"})
    assert cache.size() == 3
    assert cache.get("key1") is None  # key1 应该被移除 (oldest)
    assert cache.get("key2") is not None  # key2 should still exist (LRU only removes oldest)
    assert cache.get("key3") is not None  # key3 should still exist
    assert cache.get("key4") == {"value": "test4"}

    print("test_lru_cache_basic passed!")


def test_lru_cache_expiry():
    """测试缓存过期"""
    cache = LRUCache(max_size=10, default_ttl=1)  # 1 second TTL

    cache.set("key1", {"value": "test1"})
    assert cache.get("key1") is not None

    # 等待过期
    time.sleep(1.1)
    assert cache.get("key1") is None

    print("test_lru_cache_expiry passed!")


def test_cache_manager():
    """测试缓存管理器"""
    manager = CacheManager()

    # 测试缓存键生成
    key1 = manager.get_cache_key("content1", {"config": "test"})
    key2 = manager.get_cache_key("content1", {"config": "test"})
    key3 = manager.get_cache_key("content2", {"config": "test"})

    # 相同内容和配置生成相同键
    assert key1 == key2
    # 不同内容生成不同键
    assert key1 != key3

    # 测试缓存设置和获取
    result = {
        "overall_score": 85.0,
        "issues": [],
        "recommendations": []
    }
    manager.set(key1, result)
    assert manager.get(key1) == result

    # 测试统计信息
    stats = manager.stats()
    assert "total_entries" in stats
    assert "total_hits" in stats

    print("test_cache_manager passed!")


def test_cache_manager_cleanup():
    """测试缓存清理"""
    manager = CacheManager()

    # 添加缓存
    manager.set("key1", {"value": "test1"}, ttl=3600)
    assert manager.get("key1") is not None

    # 清空缓存
    manager.clear()
    assert manager.get("key1") is None

    print("test_cache_manager_cleanup passed!")


def test_lru_cache_hit_count():
    """测试缓存命中次数"""
    cache = LRUCache(max_size=10, default_ttl=60)

    cache.set("key1", {"value": "test1"})
    cache.get("key1")
    cache.get("key1")
    cache.get("key1")

    entry = cache._cache["key1"]
    assert entry.hit_count == 3

    print("test_lru_cache_hit_count passed!")


if __name__ == "__main__":
    test_lru_cache_basic()
    test_lru_cache_expiry()
    test_cache_manager()
    test_cache_manager_cleanup()
    test_lru_cache_hit_count()
    print("\nAll cache tests passed!")

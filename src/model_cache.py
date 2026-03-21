"""
模型缓存系统 - Medical Record Inspector
优化模型加载和缓存，减少首次检测延迟，实现模型复用
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class ModelStats:
    """模型使用统计信息"""
    load_count: int = 0          # 加载次数
    last_load_time: float = 0.0  # 最后加载时间（秒）
    last_load_timestamp: Optional[float] = None  # 最后加载时间戳
    usage_count: int = 0         # 使用次数
    total_embedding_count: int = 0  # 总嵌入数量
    total_batch_count: int = 0     # 总批处理次数


class ModelCache:
    """
    模型缓存管理器

    功能特性：
    - 懒加载：首次使用时加载模型
    - 模型复用：多个请求共享同一模型实例
    - 统计信息：跟踪模型使用情况
    - 线程安全：支持多线程并发访问
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化模型缓存"""
        if self._initialized:
            return

        self._models: Dict[str, Any] = {}
        self._stats: Dict[str, ModelStats] = {}
        self._initialized = True
        logger.info("模型缓存管理器初始化完成")

    def get_embedder(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None
    ) -> Any:
        """
        获取嵌入器实例（懒加载 + 模型复用）

        Args:
            model_name: 模型名称
            device: 设备类型（'cpu' 或 'cuda'）

        Returns:
            已加载的 embedding 模型实例
        """
        # 使用默认值
        model_key = self._get_model_key(model_name, device)

        # 懒加载：检查缓存中是否已有模型
        if model_key in self._models:
            self._stats[model_key].usage_count += 1
            logger.debug(f"模型缓存命中: {model_key} (使用次数: {self._stats[model_key].usage_count})")
            return self._models[model_key]

        # 未命中缓存，加载新模型（懒加载）
        return self._load_model(model_key, model_name, device)

    def _get_model_key(self, model_name: Optional[str], device: Optional[str]) -> str:
        """生成模型键名"""
        name = model_name or os.environ.get('EMBEDDER_MODEL', 'multi-qa-MiniLM-L6-cos-v1')
        dev = device or ('cuda' if __import__('torch').cuda.is_available() else 'cpu')
        return f"{name}_{dev}"

    def _load_model(self, model_key: str, model_name: Optional[str], device: Optional[str]) -> Any:
        """实际加载模型（仅在缓存未命中时调用）"""
        start_time = time.time()
        logger.info(f"开始加载模型: {model_key}")

        # 导入 sentence-transformers
        from sentence_transformers import SentenceTransformer

        name = model_name or os.environ.get('EMBEDDER_MODEL', 'multi-qa-MiniLM-L6-cos-v1')
        dev = device or ('cuda' if __import__('torch').cuda.is_available() else 'cpu')

        try:
            model = SentenceTransformer(
                name,
                device=dev
            )

            # 缓存模型
            self._models[model_key] = model

            # 初始化统计信息
            if model_key not in self._stats:
                self._stats[model_key] = ModelStats()

            # 更新统计信息
            load_time = time.time() - start_time
            self._stats[model_key].load_count += 1
            self._stats[model_key].last_load_time = load_time
            self._stats[model_key].last_load_timestamp = time.time()
            self._stats[model_key].usage_count += 1

            logger.info(f"模型加载完成: {model_key}, 耗时: {load_time:.2f}s")

            return model

        except Exception as e:
            logger.error(f"模型加载失败: {model_key}, 错误: {str(e)}")
            raise

    def get_embedder_wrapper(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None
    ) -> 'CachedEmbedder':
        """
        获取包装后的嵌入器（带缓存功能）

        Args:
            model_name: 模型名称
            device: 设备类型

        Returns:
            CachedEmbedder 实例
        """
        return CachedEmbedder(self, model_name, device)

    def get_stats(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取模型统计信息

        Args:
            model_name: 模型名称（可选，不指定则返回所有模型）

        Returns:
            统计信息字典
        """
        stats = {}
        for key, stat in self._stats.items():
            if model_name is None or model_name in key:
                stats[key] = {
                    'load_count': stat.load_count,
                    'last_load_time': stat.last_load_time,
                    'usage_count': stat.usage_count,
                    'total_embedding_count': stat.total_embedding_count,
                    'total_batch_count': stat.total_batch_count
                }
        return stats

    def clear(self):
        """清除所有缓存的模型"""
        with self._lock:
            self._models.clear()
            self._stats.clear()
            logger.info("模型缓存已清空")

    def clear_model(self, model_name: str, device: Optional[str] = None):
        """清除指定模型的缓存"""
        model_key = self._get_model_key(model_name, device)
        with self._lock:
            if model_key in self._models:
                del self._models[model_key]
                logger.info(f"模型缓存已清除: {model_key}")
            if model_key in self._stats:
                del self._stats[model_key]


class CachedEmbedder:
    """
    带缓存功能的嵌入器包装器

    属性：
        cache: ModelCache 实例
        model_name: 模型名称
        device: 设备类型
        _model: 实际的 SentenceTransformer 模型实例
    """

    def __init__(self, cache: ModelCache, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        初始化包装器

        Args:
            cache: ModelCache 实例
            model_name: 模型名称
            device: 设备类型
        """
        self.cache = cache
        self.model_name = model_name
        self.device = device
        self._model = None

    def _ensure_model_loaded(self):
        """确保模型已加载（懒加载）"""
        if self._model is None:
            self._model = self.cache.get_embedder(self.model_name, self.device)

    def embed(self, text: str) -> list:
        """
        对单个文本进行嵌入

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        self._ensure_model_loaded()
        embedding = self._model.encode(text, convert_to_numpy=True)
        self.cache._stats.get(self.cache._get_model_key(self.model_name, self.device), ModelStats()).total_embedding_count += 1
        return embedding.tolist()

    def embed_batch(self, texts: list, batch_size: int = 32) -> list:
        """
        批量对文本进行嵌入

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            嵌入向量列表
        """
        self._ensure_model_loaded()
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True
        )
        self.cache._stats.get(self.cache._get_model_key(self.model_name, self.device), ModelStats()).total_batch_count += 1
        self.cache._stats.get(self.cache._get_model_key(self.model_name, self.device), ModelStats()).total_embedding_count += len(texts)
        return embeddings.tolist()

    def embed_with_metadata(self, text: str) -> dict:
        """
        对文本进行嵌入并返回元数据

        Args:
            text: 输入文本

        Returns:
            包含嵌入向量和元数据的字典
        """
        embedding = self.embed(text)
        return {
            'text': text,
            'embedding': embedding,
            'embedding_dim': len(embedding),
            'text_length': len(text)
        }


# 全局缓存实例
_global_cache: Optional[ModelCache] = None


def get_model_cache() -> ModelCache:
    """
    获取全局模型缓存实例

    Returns:
        ModelCache 单例实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ModelCache()
    return _global_cache


def get_cached_embedder(
    model_name: Optional[str] = None,
    device: Optional[str] = None
) -> CachedEmbedder:
    """
    获取带缓存的嵌入器（便捷函数）

    Args:
        model_name: 模型名称
        device: 设备类型

    Returns:
        CachedEmbedder 实例
    """
    cache = get_model_cache()
    return cache.get_embedder_wrapper(model_name, device)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("模型缓存系统测试")
    print("=" * 60)

    # 获取全局缓存
    cache = get_model_cache()

    # 测试 1：首次加载（冷启动）
    print("\n【测试 1】首次加载模型（冷启动）")
    # 使用公开可用的模型（无需认证）
    embedder1 = cache.get_embedder_wrapper('multi-qa-MiniLM-L6-cos-v1')
    start = time.time()
    _ = embedder1.embed("测试文本1")
    cold_load_time = time.time() - start
    print(f"  冷启动延迟: {cold_load_time:.2f}s")

    # 测试 2：再次获取同一模型（应使用缓存，热启动）
    print("\n【测试 2】再次获取同一模型（热启动）")
    start = time.time()
    embedder2 = cache.get_embedder_wrapper('multi-qa-MiniLM-L6-cos-v1')
    _ = embedder2.embed("测试文本2")
    hot_load_time = time.time() - start
    print(f"  热启动延迟: {hot_load_time:.4f}s (应远小于冷启动)")

    # 测试 3：验证模型复用
    print("\n【测试 3】验证模型复用")
    stats = cache.get_stats()
    for key, stat in stats.items():
        print(f"  模型: {key}")
        print(f"    加载次数: {stat['load_count']}")
        print(f"    使用次数: {stat['usage_count']}")
        print(f"    最后加载时间: {stat['last_load_time']:.2f}s")

    # 测试 4：多次连续检测延迟对比
    print("\n【测试 4】连续 3 次检测延迟对比")
    for i in range(3):
        start = time.time()
        _ = embedder1.embed(f"测试文本{i+3}")
        elapsed = time.time() - start
        print(f"  第 {i+1} 次检测: {elapsed:.4f}s")

    # 显示统计信息
    print("\n【统计信息】")
    stats = cache.get_stats()
    for key, stat in stats.items():
        print(f"  {key}:")
        print(f"    总嵌入数量: {stat['total_embedding_count']}")
        print(f"    总批处理次数: {stat['total_batch_count']}")

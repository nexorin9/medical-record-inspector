"""
文本嵌入模块 - Medical Record Inspector
使用 sentence-transformers 实现病历文本的向量化，选择医疗中文专项模型

此模块提供独立的文本嵌入功能，也支持使用 model_cache.py 中的缓存系统。
"""

import os
from typing import List, Optional
import torch
import logging

logger = logging.getLogger(__name__)


class TextEmbedder:
    """文本嵌入器 - 将病历文本转换为向量表示"""

    def __init__(self, model_name: str = None, device: str = None):
        """
        初始化嵌入器

        Args:
            model_name: 模型名称
                - 'bge-micro-v2': BAAI-bge-micro-v2 (轻量级，推荐)
                - 'multi-qa-minilm': 多语言 QA 模型
                - 'paraphrase-multilingual': 多语言平行句模型
            device: 设备类型 'cpu' 或 'cuda'
        """
        self.model_name = model_name or os.environ.get(
            'EMBEDDER_MODEL', 'multi-qa-MiniLM-L6-cos-v1'
        )
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        logger.info(f"初始化嵌入器: {self.model_name}, device={self.device}")

        # 延迟加载模型以加快启动速度
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """加载模型（延迟加载）"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"正在加载模型: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            logger.info(f"模型加载完成: {self._model}")
        return self._model

    def embed(self, text: str) -> List[float]:
        """
        对单个文本进行嵌入

        Args:
            text: 输入文本

        Returns:
            嵌入向量（list of floats）
        """
        model = self._load_model()
        # 使用 convert_to_numpy=True 确保返回 numpy 数组，避免 GPU tensor 问题
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        批量对文本进行嵌入

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            嵌入向量列表
        """
        model = self._load_model()
        # 使用 convert_to_numpy=True 确保返回 numpy 数组，避免 GPU tensor 问题
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True
        )
        # embeddings 已经是 numpy array，转换为 list
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


# 全局实例 - 为向后兼容提供
_embedder = None


def get_embedder(model_name: str = None, device: str = None) -> TextEmbedder:
    """
    获取全局嵌入器实例（向后兼容函数）

    Args:
        model_name: 模型名称
        device: 设备类型

    Returns:
        TextEmbedder 实例
    """
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedder(model_name=model_name, device=device)
    return _embedder


def embed_text(text: str, model_name: str = None) -> List[float]:
    """
    便捷函数：对单个文本进行嵌入

    Args:
        text: 输入文本
        model_name: 模型名称

    Returns:
        嵌入向量
    """
    embedder = get_embedder(model_name=model_name)
    return embedder.embed(text)


def embed_texts(texts: List[str], model_name: str = None) -> List[List[float]]:
    """
    便捷函数：批量对文本进行嵌入

    Args:
        texts: 文本列表
        model_name: 模型名称

    Returns:
        嵌入向量列表
    """
    embedder = get_embedder(model_name=model_name)
    return embedder.embed_batch(texts)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    # 创建测试文本
    test_texts = [
        "患者男性，45岁，因'发热咳嗽3天'入院。",
        "诊断：社区获得性肺炎。给予头孢曲松静滴，对症治疗。",
        "患者女性，32岁，主诉'反复头痛2年'，诊断为偏头痛。",
    ]

    # 测试嵌入器
    embedder = get_embedder('BAAI/bge-micro-v2')

    print(f"设备: {embedder.device}")
    print(f"模型: {embedder.model_name}")

    # 单个文本嵌入
    embedding = embedder.embed(test_texts[0])
    print(f"\n单个文本嵌入:")
    print(f"  维度: {len(embedding)}")
    print(f"  前5维: {embedding[:5]}")

    # 批量嵌入
    embeddings = embedder.embed_batch(test_texts)
    print(f"\n批量嵌入:")
    print(f"  批量大小: {len(embeddings)}")
    print(f"  维度: {len(embeddings[0])}")

    # 嵌入元数据
    meta = embedder.embed_with_metadata(test_texts[0])
    print(f"\n嵌入元数据:")
    print(f"  文本长度: {meta['text_length']}")
    print(f"  向量维度: {meta['embedding_dim']}")

"""
测试用例 - Medical Record Inspector
模块：embedder.py - 文本嵌入模块
"""

import pytest
import os
from pathlib import Path
import tempfile

# 添加 src 目录到路径
for p in os.sys.path:
    if 'medical-record-inspector' in p:
        break
else:
    os.sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTextEmbedder:
    """测试文本嵌入器"""

    @pytest.fixture
    def embedder(self):
        """创建嵌入器实例（使用轻量级模型）"""
        from src.embedder import TextEmbedder
        # 使用测试模式，不实际加载模型
        return TextEmbedder(model_name='test_model', device='cpu')

    def test_init_default_model(self):
        """测试初始化使用默认模型"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder()
        assert embedder.model_name == 'multi-qa-MiniLM-L6-cos-v1'
        # CUDA 如果可用，则使用 cuda，否则使用 cpu
        assert embedder.device in ['cpu', 'cuda']

    def test_init_custom_model(self):
        """测试初始化使用自定义模型"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='custom_model')
        assert embedder.model_name == 'custom_model'

    def test_init_custom_device(self):
        """测试初始化使用自定义设备"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(device='cpu')
        assert embedder.device == 'cpu'

    def test_embed_returns_list(self):
        """测试 embed 返回列表"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='test_model', device='cpu')

        # 模拟模型加载和编码
        original_load = embedder._load_model

        class MockModel:
            def encode(self, text, convert_to_numpy=True):
                import numpy as np
                return np.array([0.1] * 384)  # Mock embedding dimension

        def mock_load():
            return MockModel()

        embedder._load_model = mock_load

        embedding = embedder.embed("测试文本")
        assert isinstance(embedding, list)
        assert len(embedding) == 384

    def test_embed_batch_returns_list_of_lists(self):
        """测试批量嵌入返回列表的列表"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='test_model', device='cpu')

        class MockModel:
            def encode(self, texts, batch_size=32, convert_to_numpy=True):
                import numpy as np
                return np.array([[0.1] * 384 for _ in texts])

        def mock_load():
            return MockModel()

        embedder._load_model = mock_load

        texts = ["文本1", "文本2", "文本3"]
        embeddings = embedder.embed_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(isinstance(e, list) for e in embeddings)
        assert len(embeddings[0]) == 384

    def test_embed_with_metadata(self):
        """测试嵌入元数据"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='test_model', device='cpu')

        class MockModel:
            def encode(self, text, convert_to_numpy=True):
                import numpy as np
                return np.array([0.1] * 128)

        def mock_load():
            return MockModel()

        embedder._load_model = mock_load

        text = "测试文本元数据"
        result = embedder.embed_with_metadata(text)

        assert 'text' in result
        assert 'embedding' in result
        assert 'embedding_dim' in result
        assert 'text_length' in result

        assert result['text'] == text
        assert isinstance(result['embedding'], list)
        assert result['embedding_dim'] == 128
        assert result['text_length'] == len(text)

    def test_embed_caching(self):
        """测试模型缓存 - 使用 mock"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='mock_model', device='cpu')

        # 模拟 _model 来避免实际加载
        class MockModel:
            def encode(self, text, convert_to_numpy=True):
                import numpy as np
                return np.array([0.1] * 64)

        # 直接设置 _model 来模拟已加载状态
        embedder._model = MockModel()

        # 多次调用 embed，不应重新加载
        embedding1 = embedder.embed("文本1")
        embedding2 = embedder.embed("文本2")
        embedding3 = embedder.embed("文本3")

        # 验证返回的都是列表
        assert isinstance(embedding1, list)
        assert isinstance(embedding2, list)
        assert isinstance(embedding3, list)
        # 验证维度
        assert len(embedding1) == 64


class TestGetEmbedder:
    """测试全局嵌入器实例"""

    def test_get_embedder_returns_instance(self):
        """测试获取全局嵌入器实例"""
        from src.embedder import get_embedder

        embedder = get_embedder()
        assert embedder is not None
        assert hasattr(embedder, 'embed')
        assert hasattr(embedder, 'embed_batch')

    def test_get_embedder_custom_model(self):
        """测试获取自定义模型的嵌入器"""
        from src.embedder import get_embedder, _embedder
        import src.embedder as em_module

        # 清除全局缓存
        em_module._embedder = None

        embedder = get_embedder(model_name='custom_test')
        assert embedder.model_name == 'custom_test'


class TestEmbedTextFunctions:
    """测试便捷嵌入函数"""

    def test_embed_text(self):
        """测试 embed_text 便捷函数"""
        from src.embedder import embed_text

        # Mock 模型
        import src.embedder as em_module
        original_embedder = em_module._embedder
        em_module._embedder = None

        class MockModel:
            def encode(self, text, convert_to_numpy=True):
                import numpy as np
                return np.array([0.1] * 64)

        class MockEmbedder:
            def __init__(self):
                self._model = MockModel()

            def embed(self, text):
                return self._model.encode(text).tolist()

        em_module._embedder = MockEmbedder()

        try:
            embedding = embed_text("测试文本")
            assert isinstance(embedding, list)
            assert len(embedding) == 64
        finally:
            em_module._embedder = original_embedder

    def test_embed_texts(self):
        """测试 embed_texts 批量便捷函数"""
        from src.embedder import embed_texts

        original_embedder = __import__('src.embedder', fromlist=['_embedder']).__dict__.get('_embedder', None)

        class MockModel:
            def encode(self, texts, batch_size=32, convert_to_numpy=True):
                import numpy as np
                return np.array([[0.1] * 64 for _ in texts])

        class MockEmbedder:
            def __init__(self):
                self._model = MockModel()

            def embed_batch(self, texts):
                return self._model.encode(texts).tolist()

        # 直接设置模块变量
        import src.embedder as em_module
        em_module._embedder = MockEmbedder()

        try:
            texts = ["文本1", "文本2"]
            embeddings = embed_texts(texts)
            assert isinstance(embeddings, list)
            assert len(embeddings) == 2
        finally:
            em_module._embedder = original_embedder


class TestTextEmbedderEdgeCases:
    """测试文本嵌入器边界情况"""

    def test_embed_empty_string(self):
        """测试嵌入空字符串"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='test_model', device='cpu')

        class MockModel:
            def encode(self, text, convert_to_numpy=True):
                import numpy as np
                return np.array([0.0] * 64)

        def mock_load():
            return MockModel()

        embedder._load_model = mock_load

        embedding = embedder.embed("")
        assert isinstance(embedding, list)
        assert len(embedding) == 64

    def test_embed_with_special_characters(self):
        """测试嵌入包含特殊字符的文本"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='test_model', device='cpu')

        class MockModel:
            def encode(self, text, convert_to_numpy=True):
                import numpy as np
                return np.array([0.1] * 64)

        def mock_load():
            return MockModel()

        embedder._load_model = mock_load

        special_text = "特殊字符测试\n\tTab\nChinese: 中文测试!@#$%"
        embedding = embedder.embed(special_text)
        assert isinstance(embedding, list)

    def test_embed_batch_with_empty_list(self):
        """测试批量嵌入空列表"""
        from src.embedder import TextEmbedder

        embedder = TextEmbedder(model_name='test_model', device='cpu')

        class MockModel:
            def encode(self, texts, batch_size=32, convert_to_numpy=True):
                import numpy as np
                return np.array([]).reshape(0, 64)

        def mock_load():
            return MockModel()

        embedder._load_model = mock_load

        embeddings = embedder.embed_batch([])
        assert embeddings == []


class TestTextEmbedderIntegration:
    """测试文本嵌入器集成场景"""

    def test_embed_and_similarity_workflow(self):
        """测试嵌入和相似度计算工作流"""
        from src.embedder import TextEmbedder
        from src.similarity import SimilarityCalculator

        embedder = TextEmbedder(model_name='test_model', device='cpu')
        calculator = SimilarityCalculator()

        class MockModel:
            def encode(self, text, convert_to_numpy=True):
                import numpy as np
                # 简单的维度，用于测试
                return np.array([0.5] * 64 if 'similar' in text else [0.1] * 64)

        def mock_load():
            return MockModel()

        embedder._load_model = mock_load

        # 嵌入两个文本
        text1 = "相似的文本"
        text2 = "不相似的文本"

        embedding1 = embedder.embed(text1)
        embedding2 = embedder.embed(text2)

        # 计算相似度
        similarity = calculator.cosine_similarity_single(embedding1, embedding2)

        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1

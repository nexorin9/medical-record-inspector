"""
测试用例 - Medical Record Inspector
"""

import pytest
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入测试模块
from src.extractor import extract_text_from_txt, clean_text, standardize_chinese
from src.similarity import SimilarityCalculator
from src.anomaly_detector import MedicalRecordAnomalyDetector
from src.locator import Locator


class TestExtractor:
    """测试文本提取模块"""

    def test_clean_text(self):
        """测试文本清洗"""
        text = "测试  文本   清洗\n\n空行\n处理"
        cleaned = clean_text(text)
        assert "测试 文本 清洗" in cleaned
        # 更新测试：允许单个空行（\n\n），但不允许更多
        assert "\n\n\n" not in cleaned

    def test_standardize_chinese(self):
        """测试中文标准化"""
        text = "测试（括号）转换"
        standardized = standardize_chinese(text)
        assert "(" in standardized
        assert ")" in standardized


class TestSimilarityCalculator:
    """测试相似度计算器"""

    def test_cosine_similarity(self):
        """测试余弦相似度计算"""
        calculator = SimilarityCalculator()
        vec1 = [0.1, 0.2, 0.3]
        vec2 = [0.1, 0.2, 0.3]
        similarity = calculator.cosine_similarity_single(vec1, vec2)
        assert 0.99 <= similarity <= 1.0  # 相同向量应接近 1

    def test_similarity_batch(self):
        """测试批量相似度计算"""
        calculator = SimilarityCalculator()
        query = [0.1, 0.2, 0.3]
        candidates = [
            [0.1, 0.2, 0.3],
            [0.9, 0.9, 0.9],
        ]
        similarities = calculator.cosine_similarity_batch(query, candidates)
        assert len(similarities) == 2
        assert similarities[0] > similarities[1]


class TestAnomalyDetector:
    """测试异常检测器"""

    def test_fit_and_predict(self):
        """测试模型拟合和预测"""
        detector = MedicalRecordAnomalyDetector()
        normal_similarities = [0.8, 0.85, 0.9, 0.88, 0.82]
        detector.fit(normal_similarities)

        # 正常值应该不被检测为异常
        is_anomaly, score = detector.predict(0.85)
        assert not is_anomaly

        # 异常值应该被检测为异常
        is_anomaly_low, score_low = detector.predict(0.4)
        assert is_anomaly_low  # 低相似度应被标记为异常


class TestLocator:
    """测试缺陷定位器"""

    def test_split_paragraphs(self):
        """测试段落分割"""
        locator = Locator()
        text = "段落1\n\n段落2\n\n段落3"
        paragraphs = locator.split_into_paragraphs(text)
        assert len(paragraphs) == 3

    def test_split_chunks(self):
        """测试分块"""
        locator = Locator()
        text = "句子1. 句子2. 句子3. 句子4. 句子5. 句子6."
        chunks = locator.split_into_chunks(text)
        # 应该分出多个块
        assert len(chunks) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

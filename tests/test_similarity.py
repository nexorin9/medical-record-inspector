"""
测试用例 - Medical Record Inspector
模块：similarity.py - 向量相似度计算模块
"""

import pytest
import os
import numpy as np
from pathlib import Path

# 添加 src 目录到路径
for p in os.sys.path:
    if 'medical-record-inspector' in p:
        break
else:
    os.sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSimilarityCalculator:
    """测试相似度计算器"""

    @pytest.fixture
    def calculator(self):
        """创建相似度计算器实例"""
        from src.similarity import SimilarityCalculator
        return SimilarityCalculator()

    def test_init_default_threshold(self):
        """测试初始化默认阈值"""
        from src.similarity import SimilarityCalculator

        calc = SimilarityCalculator()
        assert calc.threshold == 0.7

    def test_init_custom_threshold(self):
        """测试初始化自定义阈值"""
        from src.similarity import SimilarityCalculator

        calc = SimilarityCalculator(threshold=0.85)
        assert calc.threshold == 0.85

    def test_cosine_similarity_identical_vectors(self):
        """测试相同向量的余弦相似度应为 1"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        vec = [0.1, 0.2, 0.3, 0.4, 0.5]

        similarity = calculator.cosine_similarity_single(vec, vec)
        assert 0.99 <= similarity <= 1.0  # 允许浮点误差

    def test_cosine_similarity_orthogonal_vectors(self):
        """测试正交向量的余弦相似度应为 0"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        vec1 = [1, 0, 0]
        vec2 = [0, 1, 0]

        similarity = calculator.cosine_similarity_single(vec1, vec2)
        assert -0.01 <= similarity <= 0.01  # 应接近 0

    def test_cosine_similarity_opposite_vectors(self):
        """测试反向向量的余弦相似度应为 -1"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        vec1 = [1, 2, 3]
        vec2 = [-1, -2, -3]

        similarity = calculator.cosine_similarity_single(vec1, vec2)
        assert -1.01 <= similarity <= -0.99  # 应接近 -1

    def test_cosine_similarity_returns_float(self):
        """测试返回值类型为 float"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        vec1 = [0.1, 0.2, 0.3]
        vec2 = [0.2, 0.3, 0.4]

        similarity = calculator.cosine_similarity_single(vec1, vec2)
        assert isinstance(similarity, float)

    def test_cosine_similarity_batch(self):
        """测试批量相似度计算"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 0, 0]
        candidates = [
            [1, 0, 0],  # 相同，相似度应为 1
            [0, 1, 0],  # 正交，相似度应为 0
            [-1, 0, 0],  # 反向，相似度应为 -1
        ]

        similarities = calculator.cosine_similarity_batch(query, candidates)
        assert len(similarities) == 3
        assert isinstance(similarities, list)
        assert all(isinstance(s, float) for s in similarities)

        # 验证排序：相同 > 正交 > 反向
        assert similarities[0] > similarities[1] > similarities[2]

    def test_cosine_similarity_batch_empty_candidates(self):
        """测试空候选列表"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 2, 3]
        candidates = []

        similarities = calculator.cosine_similarity_batch(query, candidates)
        assert similarities == []


class TestFindMostSimilar:
    """测试找出最相似向量功能"""

    @pytest.fixture
    def calculator(self):
        from src.similarity import SimilarityCalculator
        return SimilarityCalculator()

    def test_find_most_similar_with_names(self):
        """测试带名称的最相似查找"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 0, 0]
        candidates = [
            [1, 0, 0],  # 最相似
            [0, 1, 0],
            [0, 0, 1],
        ]
        names = ['vec1', 'vec2', 'vec3']

        most_similar_name, similarity = calculator.find_most_similar(query, candidates, names)
        assert most_similar_name == 'vec1'
        assert 0.99 <= similarity <= 1.0

    def test_find_most_similar_without_names(self):
        """测试不带名称的最相似查找"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 0, 0]
        candidates = [[1, 0, 0], [0, 1, 0]]

        most_similar_name, similarity = calculator.find_most_similar(query, candidates)
        assert most_similar_name == '0'  # 索引字符串
        assert 0.99 <= similarity <= 1.0

    def test_find_most_similar_empty_candidates(self):
        """测试空候选列表"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 2, 3]

        name, similarity = calculator.find_most_similar(query, [])
        assert name is None
        assert similarity == 0.0


class TestSortBySimilarity:
    """测试按相似度排序功能"""

    @pytest.fixture
    def calculator(self):
        from src.similarity import SimilarityCalculator
        return SimilarityCalculator()

    def test_sort_by_similarity_descending(self):
        """测试按相似度降序排列"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 0, 0]
        candidates = [
            [0, 1, 0],   # 0
            [1, 0, 0],   # 1
            [-1, 0, 0],  # -1
        ]
        names = ['a', 'b', 'c']

        sorted_result = calculator.sort_by_similarity(query, candidates, names)

        # 应按相似度降序：b(1) > a(0) > c(-1)
        assert len(sorted_result) == 3
        assert sorted_result[0][0] == 'b'
        assert sorted_result[1][0] == 'a'
        assert sorted_result[2][0] == 'c'

    def test_sort_by_similarity_without_names(self):
        """测试不带名称的排序"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 0, 0]
        candidates = [[1, 0, 0], [0, 1, 0]]

        sorted_result = calculator.sort_by_similarity(query, candidates)

        assert len(sorted_result) == 2
        assert sorted_result[0][0] == '0'  # 索引
        assert sorted_result[1][0] == '1'

    def test_sort_by_similarity_empty_candidates(self):
        """测试空候选列表"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()
        query = [1, 2, 3]

        result = calculator.sort_by_similarity(query, [])

        assert result == []


class TestAnomalyDetector:
    """测试异常检测器"""

    def test_init_default_threshold(self):
        """测试初始化默认阈值"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector()
        assert detector.threshold == 0.7
        assert detector.method == 'threshold'

    def test_init_custom_threshold_and_method(self):
        """测试初始化自定义阈值和方法"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.85, method='isolation_forest')
        assert detector.threshold == 0.85
        assert detector.method == 'isolation_forest'

    def test_detect_simple_normal(self):
        """测试正常样本检测"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)
        is_anomaly, reason = detector.detect_simple(0.8)

        assert not is_anomaly
        assert ">= 阈值" in reason

    def test_detect_simple_anomaly(self):
        """测试异常样本检测"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)
        is_anomaly, reason = detector.detect_simple(0.5)

        assert is_anomaly
        assert "< 阈值" in reason

    def test_detect_batch(self):
        """测试批量检测"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)
        similarities = [0.8, 0.5, 0.9, 0.6]

        results = detector.detect_batch(similarities)

        assert len(results) == 4
        assert all(isinstance(r, tuple) and len(r) == 3 for r in results)

        # 预期结果：(索引, 是否异常, 原因)
        assert results[0] == (0, False, "相似度 0.800 >= 阈值 0.7")  # 正常
        assert results[1] == (1, True, "相似度 0.500 < 阈值 0.7")   # 异常
        assert results[2] == (2, False, "相似度 0.900 >= 阈值 0.7")  # 正常
        assert results[3] == (3, True, "相似度 0.600 < 阈值 0.7")   # 异常

    def test_detect_anomaly_score_with_reference(self):
        """测试带参考数据的异常分数"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)
        reference = [0.8, 0.85, 0.82, 0.88, 0.84]
        similarity = 0.5

        score = detector.detect_anomaly_score(similarity, reference)

        # 0.5 远低于平均值，应返回低分数（高异常）
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_detect_anomaly_score_without_reference(self):
        """测试不带参考数据的异常分数"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)

        # 没有参考数据时，直接返回相似度
        score = detector.detect_anomaly_score(0.5, None)
        assert score == 0.5

    def test_detect_anomaly_score_minimal_reference(self):
        """测试少量参考数据"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)

        # 少于3个参考数据时，使用简单阈值
        score = detector.detect_anomaly_score(0.5, [0.6])
        assert score == 0.5


class TestGlobalFunctions:
    """测试全局便捷函数"""

    def test_calculate_similarity(self):
        """测试 calculate_similarity 便捷函数"""
        from src.similarity import calculate_similarity

        vec1 = [1, 0, 0]
        vec2 = [1, 0, 0]

        similarity = calculate_similarity(vec1, vec2)
        assert 0.99 <= similarity <= 1.0


class TestAnomalyDetectorEdgeCases:
    """测试异常检测器边界情况"""

    def test_detect_batch_empty(self):
        """测试空批量检测"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)
        results = detector.detect_batch([])

        assert results == []

    def test_detect_anomaly_score_zero_std(self):
        """测试标准差为 0 的情况"""
        from src.similarity import AnomalyDetector

        detector = AnomalyDetector(threshold=0.7)

        # 所有值都相同，std 为 0
        reference = [0.8, 0.8, 0.8, 0.8]
        score = detector.detect_anomaly_score(0.8, reference)

        # 应返回原始相似度
        assert score == 0.8


class TestIntegration:
    """测试集成场景"""

    def test_full_workflow(self):
        """测试完整工作流：计算相似度 -> 排序 -> 异常检测"""
        from src.similarity import SimilarityCalculator, AnomalyDetector

        calculator = SimilarityCalculator()
        detector = AnomalyDetector(threshold=0.7)

        # 创建测试向量
        query = [0.5, 0.5, 0.5]
        candidates = [
            [0.5, 0.5, 0.5],  # 相似度 1.0，正常
            [0.1, 0.1, 0.1],  # 相似度 ~0.2，异常
            [0.4, 0.4, 0.4],  # 相似度 ~1.0，正常
        ]
        names = ['c1', 'c2', 'c3']

        # 1. 计算相似度
        similarities = calculator.cosine_similarity_batch(query, candidates)
        assert len(similarities) == 3

        # 2. 排序
        sorted_result = calculator.sort_by_similarity(query, candidates, names)
        assert len(sorted_result) == 3

        # 3. 异常检测
        for sim in similarities:
            is_anomaly, reason = detector.detect_simple(sim)
            assert isinstance(is_anomaly, bool)

    def test_chi_square_similarity_calculation(self):
        """测试卡方相似度计算（验证计算正确性）"""
        from src.similarity import SimilarityCalculator

        calculator = SimilarityCalculator()

        # 测试已知结果的情况
        # [1, 2] 和 [2, 4] 是同方向的，相似度应为 1
        vec1 = [1, 2]
        vec2 = [2, 4]

        similarity = calculator.cosine_similarity_single(vec1, vec2)
        assert 0.99 <= similarity <= 1.0, f"Expected ~1.0, got {similarity}"

        # [1, 0] 和 [0, 1] 正交，相似度应为 0
        vec3 = [1, 0]
        vec4 = [0, 1]

        similarity = calculator.cosine_similarity_single(vec3, vec4)
        assert -0.01 <= similarity <= 0.01, f"Expected ~0.0, got {similarity}"

"""
向量相似度计算模块 - Medical Record Inspector
实现余弦相似度计算、排序和异常检测功能
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """相似度计算器 - 计算病历文本向量之间的相似度"""

    def __init__(self, threshold: float = 0.7):
        """
        初始化相似度计算器

        Args:
            threshold: 相似度阈值，低于此值标记为异常
        """
        self.threshold = threshold

    def cosine_similarity_single(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vec1: 第一个向量
            vec2: 第二个向量

        Returns:
            余弦相似度 (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        similarity = cosine_similarity([vec1], [vec2])[0][0]
        return float(similarity)

    def cosine_similarity_batch(self, vec: List[float],
                                vectors: List[List[float]]) -> List[float]:
        """
        计算单个向量与多个向量的相似度

        Args:
            vec: 查询向量
            vectors: 向量列表

        Returns:
            相似度列表
        """
        if not vectors:
            return []

        vec_array = np.array(vec).reshape(1, -1)
        vectors_array = np.array(vectors)
        similarities = cosine_similarity(vec_array, vectors_array)[0]
        return similarities.tolist()

    def find_most_similar(self, query: List[float],
                          candidates: List[List[float]],
                          candidate_names: List[str] = None) -> Tuple[str, float]:
        """
        找出最相似的候选向量

        Args:
            query: 查询向量
            candidates: 候选向量列表
            candidate_names: 候选名称列表（可选）

        Returns:
            (最相似名称, 相似度)
        """
        if not candidates:
            return None, 0.0

        similarities = self.cosine_similarity_batch(query, candidates)

        max_idx = int(np.argmax(similarities))
        max_similarity = float(similarities[max_idx])

        if candidate_names:
            return candidate_names[max_idx], max_similarity
        else:
            return str(max_idx), max_similarity

    def sort_by_similarity(self, query: List[float],
                           candidates: List[List[float]],
                           candidate_names: List[str] = None) -> List[Tuple[str, float]]:
        """
        按相似度排序候选向量

        Args:
            query: 查询向量
            candidates: 候选向量列表
            candidate_names: 候选名称列表（可选）

        Returns:
            (名称/索引, 相似度) 列表，按相似度降序排列
        """
        if not candidates:
            return []

        similarities = self.cosine_similarity_batch(query, candidates)

        # 排序
        sorted_indices = np.argsort(similarities)[::-1]
        result = []

        for idx in sorted_indices:
            name = candidate_names[idx] if candidate_names else str(idx)
            result.append((name, float(similarities[idx])))

        return result


class AnomalyDetector:
    """异常检测器 - 基于相似度的异常病历检测"""

    def __init__(self, threshold: float = 0.7, method: str = 'threshold'):
        """
        初始化异常检测器

        Args:
            threshold: 异常阈值
            method: 检测方法 ('threshold' or 'isolation_forest')
        """
        self.threshold = threshold
        self.method = method
        self._isolation_forest = None

    def detect_simple(self, similarity: float) -> Tuple[bool, str]:
        """
        简单阈值检测

        Args:
            similarity: 相似度值

        Returns:
            (是否异常, 原因)
        """
        if similarity >= self.threshold:
            return False, f"相似度 {similarity:.3f} >= 阈值 {self.threshold}"
        else:
            return True, f"相似度 {similarity:.3f} < 阈值 {self.threshold}"

    def detect_batch(self, similarities: List[float]) -> List[Tuple[int, bool, str]]:
        """
        批量检测

        Args:
            similarities: 相似度列表

        Returns:
            [(索引, 是否异常, 原因), ...]
        """
        results = []
        for i, sim in enumerate(similarities):
            is_anomaly, reason = self.detect_simple(sim)
            results.append((i, is_anomaly, reason))
        return results

    def _fit_isolation_forest(self, similarities: List[float]) -> None:
        """拟合 Isolation Forest 模型（内部使用）"""
        from sklearn.ensemble import IsolationForest

        # 转换为二维数组（sklearn 要求）
        X = np.array(similarities).reshape(-1, 1)

        self._isolation_forest = IsolationForest(
            contamination='auto',
            random_state=42
        )
        self._isolation_forest.fit(X)

    def detect_anomaly_score(self, similarity: float,
                             reference_similarities: List[float] = None) -> float:
        """
        计算异常分数（基于参考数据分布）

        Args:
            similarity: 当前相似度
            reference_similarities: 参考相似度列表

        Returns:
            异常分数 (越低越异常)
        """
        if reference_similarities is None or len(reference_similarities) < 3:
            # 没有足够参考数据，使用简单阈值
            return similarity

        # 计算参考数据的统计信息
        mean_sim = np.mean(reference_similarities)
        std_sim = np.std(reference_similarities)

        if std_sim == 0:
            return similarity

        # Z-score 作为异常分数
        z_score = (similarity - mean_sim) / std_sim

        # 转换为 0-1 分数（z_score 负值越大，越异常）
        anomaly_score = 1.0 / (1.0 + np.exp(-z_score))

        return float(anomaly_score)


# 全局实例
_similarity_calculator = None
_anomaly_detector = None


def get_similarity_calculator() -> SimilarityCalculator:
    """获取全局相似度计算器"""
    global _similarity_calculator
    if _similarity_calculator is None:
        _similarity_calculator = SimilarityCalculator()
    return _similarity_calculator


def get_anomaly_detector(threshold: float = 0.7) -> AnomalyDetector:
    """获取全局异常检测器"""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector(threshold=threshold)
    return _anomaly_detector


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """便捷函数：计算两个向量的余弦相似度"""
    calculator = get_similarity_calculator()
    return calculator.cosine_similarity_single(vec1, vec2)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    # 创建测试向量
    vec1 = [0.1, 0.2, 0.3, 0.4, 0.5]
    vec2 = [0.15, 0.25, 0.35, 0.45, 0.6]  # 与 vec1 相似
    vec3 = [-0.5, -0.4, -0.3, -0.2, -0.1]  # 与 vec1 不相似

    # 创建候选向量
    candidates = [vec1, vec3, vec2]
    candidate_names = ['template_1', 'template_2', 'template_3']

    # 测试相似度计算器
    calculator = get_similarity_calculator()

    print("=== 相似度计算器测试 ===")

    # 单个相似度
    sim_12 = calculator.cosine_similarity_single(vec1, vec2)
    sim_13 = calculator.cosine_similarity_single(vec1, vec3)
    print(f"vec1 vs vec2: {sim_12:.4f}")
    print(f"vec1 vs vec3: {sim_13:.4f}")

    # 批量相似度
    sims = calculator.cosine_similarity_batch(vec1, candidates)
    print(f"\nvec1 vs all candidates: {sims}")

    # 排序
    sorted_result = calculator.sort_by_similarity(vec1, candidates, candidate_names)
    print(f"\n排序结果:")
    for name, sim in sorted_result:
        print(f"  {name}: {sim:.4f}")

    # 最相似
    best_name, best_sim = calculator.find_most_similar(vec1, candidates, candidate_names)
    print(f"\n最相似: {best_name} (相似度: {best_sim:.4f})")

    # 测试异常检测器
    print("\n=== 异常检测器测试 ===")

    detector = get_anomaly_detector(threshold=0.8)

    for sim in [0.9, 0.75, 0.6, 0.5]:
        is_anomaly, reason = detector.detect_simple(sim)
        print(f"相似度 {sim:.2f} -> {'异常' if is_anomaly else '正常'}: {reason}")

    # Z-score 异常分数
    print("\nZ-score 异常分数:")
    for sim in [0.9, 0.75, 0.6, 0.5]:
        score = detector.detect_anomaly_score(
            sim, [0.85, 0.88, 0.82, 0.90, 0.87]
        )
        print(f"  相似度 {sim:.2f} -> 异常分数: {score:.4f}")

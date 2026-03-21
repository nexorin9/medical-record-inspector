"""
异常检测模块 - Medical Record Inspector
实现基于 Isolation Forest 的无监督异常检测
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger(__name__)


class MedicalRecordAnomalyDetector:
    """病历异常检测器 - 使用 Isolation Forest 进行无监督异常检测"""

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        初始化异常检测器

        Args:
            contamination: 异常数据比例估计 (0-1)
            random_state: 随机种子
        """
        self.contamination = contamination
        self.random_state = random_state

        # Isolation Forest 模型
        self._model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto'
        )
        self._fitted = False
        self._reference_similarities = []

    def fit(self, similarities: List[float]) -> None:
        """
        拟合异常检测模型

        Args:
            similarities: 参考相似度列表
        """
        if len(similarities) < 3:
            logger.warning("相似度数据太少，无法拟合 Isolation Forest")
            self._fitted = False
            return

        # 转换为二维数组（sklearn 要求）
        X = np.array(similarities).reshape(-1, 1)

        self._model.fit(X)
        self._reference_similarities = similarities
        self._fitted = True

        logger.info(f"Isolation Forest 模型拟合完成")
        logger.info(f"  参考数据量: {len(similarities)}")
        logger.info(f"  异常比例估计: {self.contamination}")

    def predict(self, similarity: float) -> Tuple[bool, float]:
        """
        预测单个相似度是否异常

        Args:
            similarity: 相似度值

        Returns:
            (是否异常, 异常分数)
        """
        if not self._fitted:
            # 模型未拟合，返回默认结果
            return False, 0.0

        # 预测
        X = np.array([[similarity]])
        prediction = self._model.predict(X)[0]  # 1 = 正常, -1 = 异常
        score = self._model.decision_function(X)[0]

        # 转换分数（让分数越高越异常）
        normalized_score = 1.0 / (1.0 + np.exp(-score))

        is_anomaly = prediction == -1

        return is_anomaly, float(normalized_score)

    def predict_batch(self, similarities: List[float]) -> List[Tuple[bool, float]]:
        """
        批量预测

        Args:
            similarities: 相似度列表

        Returns:
            [(是否异常, 异常分数), ...]
        """
        results = []
        for sim in similarities:
            is_anomaly, score = self.predict(sim)
            results.append((is_anomaly, score))
        return results

    def get_outlier_ranking(self, similarities: List[float]) -> List[Tuple[int, float, float]]:
        """
        获取异常排序（列出最异常的几个）

        Args:
            similarities: 相似度列表

        Returns:
            [(索引, 异常分数, 相似度), ...] 按异常分数降序排列
        """
        if not self._fitted:
            # 模型未拟合，返回简单排序
            ranking = [(i, 1.0 - sim, sim) for i, sim in enumerate(similarities)]
            # 按异常分数降序排列
            ranking.sort(key=lambda x: x[1], reverse=True)
            return ranking

        # 获取所有预测结果
        predictions = self.predict_batch(similarities)

        # 排序（异常分数最高的在前）
        ranked = [(i, score, similarities[i])
                  for i, (is_anomaly, score) in enumerate(predictions)]
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def explains_anomaly(self, similarity: float) -> str:
        """
        生成异常解释（自然语言）

        Args:
            similarity: 相似度值

        Returns:
            解释文本
        """
        if not self._fitted or not self._reference_similarities:
            return f"相似度 {similarity:.3f}，低于参考阈值"

        # 计算统计信息
        mean_sim = np.mean(self._reference_similarities)
        std_sim = np.std(self._reference_similarities)
        min_sim = np.min(self._reference_similarities)
        max_sim = np.max(self._reference_similarities)

        # Z-score
        z_score = (similarity - mean_sim) / (std_sim if std_sim > 0 else 1)

        explanation = []

        if similarity < mean_sim - 2 * std_sim:
            explanation.append(f"相似度 {similarity:.3f} 远低于平均值 {mean_sim:.3f}")
            explanation.append(f"(低于平均值 {abs(z_score):.2f} 个标准差)")
        elif similarity < mean_sim - std_sim:
            explanation.append(f"相似度 {similarity:.3f} 低于平均值 {mean_sim:.3f}")
            explanation.append(f"(低于平均值 {abs(z_score):.2f} 个标准差)")
        else:
            explanation.append(f"相似度 {similarity:.3f} 在正常范围内")
            explanation.append(f"(平均值: {mean_sim:.3f}, 标准差: {std_sim:.3f})")

        explanation.append(f"[参考范围: {min_sim:.3f} - {max_sim:.3f}]")

        return " ".join(explanation)


def create_anomaly_detector() -> MedicalRecordAnomalyDetector:
    """创建默认异常检测器"""
    return MedicalRecordAnomalyDetector(contamination=0.1)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    # 创建模拟相似度数据（正常病历相似度较高）
    np.random.seed(42)
    normal_similarities = np.random.uniform(0.75, 0.95, 20).tolist()

    # 创建异常相似度数据（明显偏低）
    anomaly_similarities = [0.45, 0.52, 0.38, 0.58]

    # 测试异常检测器
    print("=== 异常检测器测试 ===\n")

    detector = create_anomaly_detector()

    # 拟合模型
    detector.fit(normal_similarities)
    print("模型拟合完成\n")

    # 测试正常样本
    print("正常样本检测:")
    for sim in [0.80, 0.85, 0.90]:
        is_anomaly, score = detector.predict(sim)
        explanation = detector.explains_anomaly(sim)
        print(f"  相似度 {sim:.3f} -> {'异常' if is_anomaly else '正常'} (分数: {score:.4f})")
        print(f"    {explanation}")

    # 测试异常样本
    print("\n异常样本检测:")
    for sim in anomaly_similarities:
        is_anomaly, score = detector.predict(sim)
        explanation = detector.explains_anomaly(sim)
        print(f"  相似度 {sim:.3f} -> {'异常' if is_anomaly else '正常'} (分数: {score:.4f})")
        print(f"    {explanation}")

    # 异常排序
    print("\n异常排序:")
    all_similarities = normal_similarities + anomaly_similarities
    ranking = detector.get_outlier_ranking(all_similarities)

    print("Top 5 最异常的样本:")
    for i, (idx, score, sim) in enumerate(ranking[:5]):
        is_template = "异常模板" if idx >= len(normal_similarities) else "正常样本"
        print(f"  {i+1}. 索引 {idx} ({is_template}): 相似度 {sim:.3f}, 异常分数 {score:.4f}")

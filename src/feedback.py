"""
用户反馈收集 - Medical Record Inspector
实现用户反馈功能，允许质控员标记检测结果的准确性
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class FeedbackData:
    """反馈数据结构"""

    def __init__(self, record_id: str, result_id: str, feedback_type: str,
                 score: int = 0, comment: str = "", timestamp: str = None):
        """
        初始化反馈数据

        Args:
            record_id: 病历ID
            result_id: 检测结果ID
            feedback_type: 反馈类型（relevant/irrelevant/helpful/unhelpful）
            score: 评分（1-5）
            comment: 评论
            timestamp: 时间戳
        """
        self.record_id = record_id
        self.result_id = result_id
        self.feedback_type = feedback_type
        self.score = score
        self.comment = comment
        self.timestamp = timestamp or datetime.now().isoformat()


class FeedbackCollector:
    """反馈收集器 - 收集和管理用户反馈"""

    def __init__(self, feedback_dir: str = "data/feedback"):
        """
        初始化反馈收集器

        Args:
            feedback_dir: 反馈存储目录
        """
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.feedback_dir / "feedback.json"
        self.csv_file = self.feedback_dir / "feedback.csv"
        self.feedback_list = []
        self._load_feedback()

    def _load_feedback(self):
        """加载反馈数据"""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_list = json.load(f)
                logger.info(f"加载 {len(self.feedback_list)} 条反馈")
            except Exception as e:
                logger.error(f"加载反馈失败: {e}")
                self.feedback_list = []

    def _save_feedback(self):
        """保存反馈数据"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存反馈失败: {e}")

    def _save_csv(self):
        """保存反馈数据为 CSV"""
        try:
            if not self.feedback_list:
                return

            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                if self.feedback_list:
                    writer = csv.DictWriter(f, fieldnames=self.feedback_list[0].keys())
                    writer.writeheader()
                    writer.writerows(self.feedback_list)
        except Exception as e:
            logger.error(f"保存 CSV 失败: {e}")

    def add_feedback(self, record_id: str, result_id: str, feedback_type: str,
                     score: int = 0, comment: str = "") -> Dict[str, Any]:
        """
        添加反馈

        Args:
            record_id: 病历ID
            result_id: 检测结果ID
            feedback_type: 反馈类型
            score: 评分
            comment: 评论

        Returns:
            操作结果
        """
        valid_types = ['relevant', 'irrelevant', 'helpful', 'unhelpful', 'accurate', 'inaccurate']
        if feedback_type not in valid_types:
            return {
                'success': False,
                'message': f"无效的反馈类型。有效类型: {valid_types}"
            }

        if score < 1 or score > 5:
            return {
                'success': False,
                'message': "评分必须在 1-5 之间"
            }

        feedback = {
            'id': str(uuid.uuid4()),
            'record_id': record_id,
            'result_id': result_id,
            'feedback_type': feedback_type,
            'score': score,
            'comment': comment,
            'timestamp': datetime.now().isoformat()
        }

        self.feedback_list.append(feedback)
        self._save_feedback()
        self._save_csv()

        logger.info(f"添加反馈: {feedback_type}, record_id={record_id}, result_id={result_id}")

        return {
            'success': True,
            'message': '反馈已保存',
            'feedback_id': feedback['id']
        }

    def get_feedback_by_record(self, record_id: str) -> List[Dict]:
        """根据病历ID获取反馈"""
        return [f for f in self.feedback_list if f['record_id'] == record_id]

    def get_feedback_by_type(self, feedback_type: str) -> List[Dict]:
        """根据反馈类型获取反馈"""
        return [f for f in self.feedback_list if f['feedback_type'] == feedback_type]

    def get_all_feedback(self) -> List[Dict]:
        """获取所有反馈"""
        return self.feedback_list

    def delete_feedback(self, feedback_id: str) -> Dict[str, Any]:
        """删除反馈"""
        for i, f in enumerate(self.feedback_list):
            if f['id'] == feedback_id:
                self.feedback_list.pop(i)
                self._save_feedback()
                self._save_csv()
                return {
                    'success': True,
                    'message': '反馈已删除'
                }
        return {
            'success': False,
            'message': '反馈未找到'
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        if not self.feedback_list:
            return {
                'total': 0,
                'by_type': {},
                'avg_score': 0,
                'by_date': {}
            }

        # 按类型统计
        by_type = {}
        for f in self.feedback_list:
            ft = f['feedback_type']
            by_type[ft] = by_type.get(ft, 0) + 1

        # 计算平均评分
        scores = [f['score'] for f in self.feedback_list if f['score'] > 0]
        avg_score = sum(scores) / len(scores) if scores else 0

        # 按日期统计
        by_date = {}
        for f in self.feedback_list:
            date = f['timestamp'][:10]  # YYYY-MM-DD
            by_date[date] = by_date.get(date, 0) + 1

        return {
            'total': len(self.feedback_list),
            'by_type': by_type,
            'avg_score': round(avg_score, 2),
            'by_date': by_date
        }

    def export_feedback(self, output_path: str) -> Dict[str, Any]:
        """导出反馈到文件"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_list, f, ensure_ascii=False, indent=2)
            return {
                'success': True,
                'message': f"反馈已导出到 {output_path}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"导出失败: {e}"
            }

    def clear_all(self) -> Dict[str, Any]:
        """清空所有反馈"""
        self.feedback_list = []
        self._save_feedback()
        self._save_csv()
        logger.warning("清空所有反馈")
        return {
            'success': True,
            'message': '所有反馈已清空'
        }


def create_feedback_collector(feedback_dir: str = "data/feedback") -> FeedbackCollector:
    """创建反馈收集器"""
    return FeedbackCollector(feedback_dir)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=== Feedback Collector 测试 ===\n")

    # 创建收集器
    collector = create_feedback_collector()

    # 测试添加反馈
    print("1. 测试添加反馈:")
    result = collector.add_feedback(
        record_id="rec_001",
        result_id="result_001",
        feedback_type="accurate",
        score=5,
        comment="检测结果很准，这个病历确实符合肺炎特征"
    )
    print(f"   {result['message']}")

    result = collector.add_feedback(
        record_id="rec_002",
        result_id="result_002",
        feedback_type="inaccurate",
        score=2,
        comment="感觉这个段落缺陷标记不太准确"
    )
    print(f"   {result['message']}")

    result = collector.add_feedback(
        record_id="rec_001",
        result_id="result_001",
        feedback_type="helpful",
        score=4,
        comment="对病历质控有帮助"
    )
    print(f"   {result['message']}")

    # 测试获取统计
    print("\n2. 测试获取统计:")
    stats = collector.get_statistics()
    print(f"   总反馈数: {stats['total']}")
    print(f"   按类型:")
    for ft, count in stats['by_type'].items():
        print(f"     - {ft}: {count}")
    print(f"   平均评分: {stats['avg_score']}")

    # 测试按病历ID获取
    print("\n3. 测试按病历ID获取反馈:")
    feedbacks = collector.get_feedback_by_record("rec_001")
    print(f"   rec_001 有 {len(feedbacks)} 条反馈")

    # 测试导出
    print("\n4. 测试导出反馈:")
    export_result = collector.export_feedback("data/exported_feedback.json")
    print(f"   {export_result['message']}")

    # 测试删除
    print("\n5. 测试删除反馈:")
    if collector.feedback_list:
        feedback_id = collector.feedback_list[0]['id']
        delete_result = collector.delete_feedback(feedback_id)
        print(f"   {delete_result['message']}")

    # 测试清空
    print("\n6. 测试清空所有反馈:")
    clear_result = collector.clear_all()
    print(f"   {clear_result['message']}")

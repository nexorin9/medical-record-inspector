"""
History Management Module for Medical Record Inspector.

This module provides evaluation history tracking and management,
allowing users to track, review, and export past assessments.
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading


class HistoryManager:
    """
    评估历史管理器。

    提供以下功能：
    - 保存评估结果到历史记录
    - 查询历史记录
    - 按条件筛选（时间、评分、患者ID等）
    - 导出历史记录
    - 统计信息生成
    """

    def __init__(
        self,
        history_dir: str = None,
        max_history: int = 1000
    ):
        """
        初始化历史管理器。

        Args:
            history_dir: 历史记录存储目录
            max_history: 最大历史记录数量
        """
        if history_dir is None:
            history_dir = Path(__file__).parent.parent / "data" / "history"

        self.history_dir = Path(history_dir)
        self.max_history = max_history

        # Ensure history directory exists
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Lock for thread-safe operations
        self._lock = threading.Lock()

    def _generate_history_id(self, case_data: Dict) -> str:
        """生成历史记录ID"""
        case_str = json.dumps(case_data, sort_keys=True)
        case_hash = hashlib.md5(case_str.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"HIST-{timestamp}-{case_hash}"

    def save_evaluation(
        self,
        case: Dict,
        result: Dict,
        save_input: bool = True
    ) -> str:
        """
        保存评估结果到历史记录。

        Args:
            case: 评估的病历数据
            result: 评估结果
            save_input: 是否保存输入数据

        Returns:
            历史记录ID
        """
        history_id = self._generate_history_id(case)

        history_entry = {
            "history_id": history_id,
            "timestamp": datetime.now().isoformat(),
            "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "case_id": case.get("patient_id"),
            "visit_id": case.get("visit_id"),
            "department": case.get("department"),
            "case_type": case.get("case_type"),
            "result": result,
            "metadata": {
                "input_saved": save_input,
                "input_file_size": len(json.dumps(case)) if save_input else 0,
                "storage_version": "1.0"
            }
        }

        if save_input:
            history_entry["input_data"] = case

        # Save to file
        history_file = self.history_dir / f"{history_id}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_entry, f, indent=2, ensure_ascii=False)

        # Enforce maximum history
        self._enforce_max_history()

        return history_id

    def get_evaluation(self, history_id: str) -> Optional[Dict]:
        """
        获取单条历史记录。

        Args:
            history_id: 历史记录ID

        Returns:
            历史记录数据
        """
        history_file = self.history_dir / f"{history_id}.json"
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def get_evaluations(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_desc: bool = True
    ) -> List[Dict]:
        """
        获取历史记录列表。

        Args:
            limit: 返回数量限制
            offset: 偏移量
            sort_by: 排序字段
            sort_desc: 是否降序

        Returns:
            历史记录列表
        """
        history_files = sorted(
            self.history_dir.glob("HIST-*.json"),
            key=lambda x: x.name,
            reverse=sort_desc
        )

        evaluations = []
        for history_file in history_files[offset:offset + limit]:
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    evaluations.append(json.load(f))
            except Exception:
                continue

        return evaluations

    def filter_by_time(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        patient_id: str = None
    ) -> List[Dict]:
        """
        按时间范围筛选历史记录。

        Args:
            start_time: 开始时间
            end_time: 结束时间
            patient_id: 患者ID（可选）

        Returns:
            筛选后的历史记录列表
        """
        results = []

        for history_file in self.history_dir.glob("HIST-*.json"):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)

                # Parse timestamp
                timestamp = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))

                # Filter by time range
                if start_time and timestamp < start_time:
                    continue
                if end_time and timestamp > end_time:
                    continue

                # Filter by patient ID
                if patient_id and entry.get("case_id") != patient_id:
                    continue

                results.append(entry)
            except Exception:
                continue

        # Sort by timestamp descending
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results

    def filter_by_score(
        self,
        min_score: float = 0,
        max_score: float = 10,
        score_dimension: str = "overall_score"
    ) -> List[Dict]:
        """
        按评分筛选历史记录。

        Args:
            min_score: 最小评分
            max_score: 最大评分
            score_dimension: 评分维度（overall_score, completeness_score, etc.）

        Returns:
            筛选后的历史记录列表
        """
        results = []

        for history_file in self.history_dir.glob("HIST-*.json"):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)

                # Get score from result
                result = entry.get("result", {})
                scores = result.get("scores", {})
                score = scores.get(score_dimension, 0)

                if min_score <= score <= max_score:
                    results.append(entry)
            except Exception:
                continue

        # Sort by score descending
        results.sort(key=lambda x: x.get("result", {}).get("scores", {}).get(score_dimension, 0), reverse=True)
        return results

    def filter_by_patient(
        self,
        patient_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        按患者ID筛选历史记录。

        Args:
            patient_id: 患者ID
            limit: 返回数量限制

        Returns:
            筛选后的历史记录列表
        """
        results = []

        for history_file in self.history_dir.glob("HIST-*.json"):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)

                if entry.get("case_id") == patient_id:
                    results.append(entry)
            except Exception:
                continue

            if len(results) >= limit:
                break

        # Sort by timestamp descending
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results

    def export_history(
        self,
        format: str = "json",
        filter_start: datetime = None,
        filter_end: datetime = None
    ) -> str:
        """
        导出历史记录。

        Args:
            format: 导出格式（json, csv）
            filter_start: 过滤开始时间
            filter_end: 过滤结束时间

        Returns:
            导出的文件路径
        """
        # Get filtered evaluations
        evaluations = self.filter_by_time(filter_start, filter_end)

        if format == "json":
            output_file = self.history_dir / f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_entries": len(evaluations),
                "evaluations": evaluations
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            import csv
            output_file = self.history_dir / f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    "history_id", "timestamp", "patient_id", "visit_id",
                    "department", "case_type", "overall_score",
                    "completeness_score", "consistency_score",
                    "timeliness_score", "standardization_score"
                ])

                # Write data
                for entry in evaluations:
                    result = entry.get("result", {})
                    scores = result.get("scores", {})
                    writer.writerow([
                        entry["history_id"],
                        entry["timestamp"],
                        entry.get("case_id", ""),
                        entry.get("visit_id", ""),
                        entry.get("department", ""),
                        entry.get("case_type", ""),
                        scores.get("overall_score", ""),
                        scores.get("completeness_score", ""),
                        scores.get("consistency_score", ""),
                        scores.get("timeliness_score", ""),
                        scores.get("standardization_score", "")
                    ])
        else:
            raise ValueError(f"Unsupported format: {format}")

        return str(output_file)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取历史记录统计信息。

        Returns:
            统计信息字典
        """
        all_evaluations = list(self.history_dir.glob("HIST-*.json"))

        if not all_evaluations:
            return {"total_evaluations": 0}

        scores = []
        departments = {}
        case_types = {}

        for history_file in all_evaluations:
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)

                result = entry.get("result", {})
                scores.append(result.get("scores", {}).get("overall_score", 0))

                dept = entry.get("department", "Unknown")
                departments[dept] = departments.get(dept, 0) + 1

                case_type = entry.get("case_type", "Unknown")
                case_types[case_type] = case_types.get(case_type, 0) + 1
            except Exception:
                continue

        if scores:
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
        else:
            avg_score = 0
            min_score = 0
            max_score = 0

        return {
            "total_evaluations": len(all_evaluations),
            "average_score": round(avg_score, 2),
            "min_score": round(min_score, 2),
            "max_score": round(max_score, 2),
            "score_distribution": self._get_score_distribution(scores),
            "by_department": departments,
            "by_case_type": case_types,
            "last_evaluation": all_evaluations[-1].name if all_evaluations else None
        }

    def _get_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """获取评分分布"""
        distribution = {
            "excellent": 0,  # >= 9
            "good": 0,       # 7-9
            "average": 0,    # 5-7
            "poor": 0        # < 5
        }

        for score in scores:
            if score >= 9:
                distribution["excellent"] += 1
            elif score >= 7:
                distribution["good"] += 1
            elif score >= 5:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def _enforce_max_history(self):
        """强制执行最大历史记录数量"""
        history_files = sorted(
            self.history_dir.glob("HIST-*.json"),
            key=lambda x: x.name
        )

        while len(history_files) > self.max_history:
            oldest = history_files.pop(0)
            try:
                oldest.unlink()
            except Exception:
                continue

    def clear_history(self, older_than: datetime = None) -> int:
        """
        清除历史记录。

        Args:
            older_than: 清除早于该时间的记录

        Returns:
            删除的记录数
        """
        deleted = 0

        for history_file in self.history_dir.glob("HIST-*.json"):
            try:
                if older_than:
                    timestamp_str = history_file.name.split("-")[1] + "-" + history_file.name.split("-")[2]
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

                    if file_time < older_than:
                        history_file.unlink()
                        deleted += 1
                else:
                    history_file.unlink()
                    deleted += 1
            except Exception:
                continue

        return deleted


# Global history manager instance
_history_manager = None


def get_history_manager() -> HistoryManager:
    """获取全局历史管理器实例"""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager


def save_evaluation_result(case: Dict, result: Dict) -> str:
    """
    保存评估结果到历史记录（便捷函数）。

    Args:
        case: 病历数据
        result: 评估结果

    Returns:
        历史记录ID
    """
    manager = get_history_manager()
    return manager.save_evaluation(case, result)


def get_evaluation_history(
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """
    获取历史记录列表（便捷函数）。

    Args:
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        历史记录列表
    """
    manager = get_history_manager()
    return manager.get_evaluations(limit, offset)


if __name__ == "__main__":
    # Simple test
    test_case = {
        "patient_id": "PAT001",
        "visit_id": "VIS001",
        "department": "内科",
        "case_type": "门诊",
        "main_complaint": "咳嗽3天",
        "present_illness": "患者3天前受凉后出现咳嗽",
        "past_history": "既往体健",
        "physical_exam": "双肺呼吸音清",
        "auxiliary_exams": "血常规正常",
        "diagnosis": "急性支气管炎",
        "prescription": "阿莫西林 0.5g tid"
    }

    test_result = {
        "assessment_id": "ASSESS-TEST",
        "scores": {
            "completeness_score": 8.5,
            "consistency_score": 9.0,
            "timeliness_score": 8.0,
            "standardization_score": 8.5,
            "overall_score": 8.5
        },
        "issues": [],
        "report": "病历质量良好"
    }

    # Save evaluation
    manager = HistoryManager()
    history_id = manager.save_evaluation(test_case, test_result)
    print(f"Saved evaluation with ID: {history_id}")

    # Get history
    history = manager.get_evaluations(limit=10)
    print(f"\nRetrieved {len(history)} evaluations")

    # Get statistics
    stats = manager.get_statistics()
    print(f"\nStatistics: {stats}")

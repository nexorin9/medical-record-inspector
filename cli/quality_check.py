"""
Command-line interface for Medical Record Inspector.

Usage:
    python -m cli quality_check <file>
    python -m cli check-batch <directory>
    python -m cli list-standards
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.evaluator import QualityEvaluator
from api.standard_case_generator import StandardCaseGenerator


def check_single_file(file_path: str):
    """检查单个病历文件"""
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"错误：文件不存在 - {file_path}")
            return 1

        # 读取病历数据
        with open(path, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        # 执行评估
        evaluator = QualityEvaluator()
        result = evaluator.assess(case_data)

        # 输出结果
        print("=" * 60)
        print("病历质量评估结果")
        print("=" * 60)
        print(f"\n评估ID：{result.assessment_id}")
        print(f"患者ID：{result.patient_id or 'N/A'}")
        print(f"就诊ID：{result.visit_id or 'N/A'}")
        print(f"总体评分：{result.scores.overall_score:.1f}/10.0")
        print("\n各维度评分：")
        print(f"  完整性：{result.scores.completeness_score:.1f}/10.0")
        print(f"  逻辑一致性：{result.scores.consistency_score:.1f}/10.0")
        print(f"  及时性：{result.scores.timeliness_score:.1f}/10.0")
        print(f"  规范性：{result.scores.standardization_score:.1f}/10.0")

        if result.issues:
            print(f"\n发现 {len(result.issues)} 个问题：")
            for i, issue in enumerate(result.issues, 1):
                print(f"\n[{i}] {issue.category.upper()} ({issue.severity.upper()})")
                print(f"  {issue.description}")
                print(f"  建议：{issue.suggestion}")
        else:
            print("\n未发现明显问题。")

        print("\n" + result.report)
        print("=" * 60)

        return 0

    except json.JSONDecodeError as e:
        print(f"错误：JSON 格式错误 - {e}")
        return 1
    except Exception as e:
        print(f"错误：{e}")
        return 1


def check_batch_directory(directory: str):
    """批量检查目录中的病历文件"""
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"错误：目录不存在 - {directory}")
            return 1

        if not dir_path.is_dir():
            print(f"错误：不是目录 - {directory}")
            return 1

        # 查找所有 JSON 文件
        json_files = list(dir_path.glob("*.json")) + list(dir_path.glob("*.txt"))

        if not json_files:
            print(f"错误：在 {directory} 中未找到病历文件")
            return 1

        print(f"找到 {len(json_files)} 个文件，开始批量评估...\n")

        evaluator = QualityEvaluator()
        total = len(json_files)
        successful = 0
        failed = 0
        avg_score = 0

        for i, file_path in enumerate(json_files, 1):
            print(f"[{i}/{total}] 处理：{file_path.name}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)

                result = evaluator.assess(case_data)
                avg_score += result.scores.overall_score
                successful += 1

                print(f"      评分：{result.scores.overall_score:.1f}/10.0")

            except json.JSONDecodeError:
                print(f"      错误：JSON 格式错误")
                failed += 1
            except Exception as e:
                print(f"      错误：{e}")
                failed += 1

        # 输出汇总
        print("\n" + "=" * 60)
        print("批量评估结果汇总")
        print("=" * 60)
        print(f"总文件数：{total}")
        print(f"成功：{successful}")
        print(f"失败：{failed}")
        if successful > 0:
            print(f"平均评分：{avg_score / successful:.1f}/10.0")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"错误：{e}")
        return 1


def list_standard_cases():
    """列出所有标准病历模板"""
    try:
        generator = StandardCaseGenerator()
        standards = generator.load_cases()

        if not standards:
            print("未找到标准病历模板。")
            return 1

        print("=" * 60)
        print("标准病历模板列表")
        print("=" * 60)

        for i, case in enumerate(standards, 1):
            print(f"\n[{i}] {case['template_id']}")
            print(f"    科室：{case['department']}")
            print(f"    类型：{case['case_type']}")
            print(f"    主诉：{case['main_complaint']}")

        print("\n" + "=" * 60)
        print(f"共 {len(standards)} 个标准病历模板")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"错误：{e}")
        return 1


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="medical-record-inspector",
        description="Medical Record Inspector - 病历质量质控工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # check command
    check_parser = subparsers.add_parser(
        "check",
        help="检查单个病历文件"
    )
    check_parser.add_argument(
        "file",
        help="病历文件路径（JSON 格式）"
    )

    # check-batch command
    batch_parser = subparsers.add_parser(
        "check-batch",
        help="批量检查目录中的病历文件"
    )
    batch_parser.add_argument(
        "directory",
        help="包含病历文件的目录路径"
    )

    # list-standards command
    list_parser = subparsers.add_parser(
        "list-standards",
        help="列出所有标准病历模板"
    )

    # version command
    version_parser = subparsers.add_parser(
        "version",
        help="显示版本信息"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "check":
        return check_single_file(args.file)
    elif args.command == "check-batch":
        return check_batch_directory(args.directory)
    elif args.command == "list-standards":
        return list_standard_cases()
    elif args.command == "version":
        print("Medical Record Inspector CLI v1.0.0")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

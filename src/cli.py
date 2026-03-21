"""
CLI 命令行工具 - Medical Record Inspector
支持单个病历检测和批量检测
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict
import logging

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.inspector import create_inspector, MedicalRecordInspector
from src.extractor import extract_text
from src.explainer import create_explainer
from src.logger import setup_logging as setup_logger, get_logger

logger = get_logger(__name__)


def setup_logging(verbose: bool = False):
    """设置日志（调用统一的日志系统）"""
    # verbose 优先，否则使用 INFO 级别
    if verbose:
        setup_logger(log_level='DEBUG', verbose=True)
    else:
        setup_logger(log_level='INFO', verbose=False)
    # 重新获取 logger 以应用新配置
    global logger
    logger = get_logger(__name__)


def load_record_file(file_path: str) -> str:
    """加载病历文件"""
    return extract_text(file_path)


def load_records_from_directory(dir_path: str) -> List[Dict]:
    """从目录加载多个病历文件"""
    results = []
    exts = ['.pdf', '.docx', '.txt']

    for file_path in Path(dir_path).iterdir():
        if file_path.suffix.lower() in exts:
            try:
                text = extract_text(str(file_path))
                results.append({
                    'filename': file_path.name,
                    'text': text
                })
                logger.info(f"加载文件: {file_path.name} ({len(text)} 字符)")
            except Exception as e:
                logger.error(f"加载文件失败 {file_path}: {e}")

    return results


def output_result(result: Dict, output_format: str = 'text'):
    """输出结果"""
    if output_format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif output_format == 'text':
        print(format_text_result(result))


def format_text_result(result: Dict) -> str:
    """格式化文本结果"""
    lines = []

    # 概述
    score = result.get('overall_score', 0)
    template = result.get('template_used', 'N/A')
    defects = result.get('defects', [])
    defect_count = result.get('defect_count', len(defects))

    lines.append("=" * 60)
    lines.append("病历质控结果")
    lines.append("=" * 60)
    lines.append(f"\n总体分数: {score:.3f}")
    lines.append(f"使用模板: {template}")
    lines.append(f"缺陷数量: {defect_count}")

    # 评估等级
    if score >= 0.8:
        lines.append("质量等级: 优秀")
    elif score >= 0.6:
        lines.append("质量等级: 合格")
    else:
        lines.append("质量等级: 需要改进")

    # 详细缺陷
    if defects:
        lines.append("\n主要缺陷:")
        for i, defect in enumerate(defects[:5], 1):
            lines.append(f"\n  缺陷 {i}:")
            lines.append(f"    类型: {defect.get('type', 'unknown')}")
            lines.append(f"    相似度: {defect.get('similarity', 0):.3f}")
            lines.append(f"    内容: {defect.get('text', '')[:100]}")

    # 段落分析
    paragraph_analysis = result.get('paragraph_analysis', {})
    if paragraph_analysis:
        lines.append(f"\n段落分析:")
        lines.append(f"  总段落数: {paragraph_analysis.get('total', 0)}")
        lines.append(f"  异常段落数: {paragraph_analysis.get('defects', 0)}")

    # 分块分析
    chunk_analysis = result.get('chunk_analysis', {})
    if chunk_analysis:
        lines.append(f"\n分块分析:")
        lines.append(f"  总分块数: {chunk_analysis.get('total', 0)}")
        lines.append(f"  异常分块数: {chunk_analysis.get('defects', 0)}")

    # 模板相似度详情
    similarity_scores = result.get('similarity_scores', [])
    if similarity_scores:
        lines.append("\n相似度详情:")
        for sim in similarity_scores:
            lines.append(f"  {sim.get('reference', 'unknown')}: {sim.get('score', 0):.3f}")

    return '\n'.join(lines)


def cmd_single(args):
    """单个病历检测命令"""
    setup_logging(args.verbose)

    # 加载病历
    record_text = extract_text(args.input)
    logger.info(f"加载病历: {args.input} ({len(record_text)} 字符)")

    # 创建 Inspector
    inspector = create_inspector(args.templates)

    # 分析
    result = inspector.analyze(record_text, args.template)

    # 输出
    output_result(result, args.output_format)

    # 保存结果（如果指定了输出文件）
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"结果已保存到: {args.output}")


def cmd_batch(args):
    """批量检测命令"""
    setup_logging(args.verbose)

    # 创建 Inspector
    inspector = create_inspector(args.templates)

    # 加载所有病历
    records = load_records_from_directory(args.input)
    logger.info(f"加载了 {len(records)} 个病历文件")

    if not records:
        print("错误: 没有找到可处理的文件")
        sys.exit(1)

    # 批量分析
    results = inspector.analyze_batch([r['text'] for r in records], args.template)

    # 输出汇总
    if args.output_format == 'json':
        output_data = {
            'total': len(results),
            'results': [
                {
                    'filename': records[i]['filename'],
                    **results[i]
                }
                for i in range(len(results))
            ]
        }
        print(json.dumps(output_data, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("批量检测结果汇总")
        print("=" * 60)
        for i, result in enumerate(results):
            print(f"\n文件: {records[i]['filename']}")
            print(f"  分数: {result.get('overall_score', 0):.3f}")
            print(f"  模板: {result.get('template_used', 'N/A')}")
            print(f"  缺陷: {result.get('defect_count', 0)}")

    # 保存详细结果
    if args.output:
        output_data = {
            'total': len(results),
            'results': [
                {
                    'filename': records[i]['filename'],
                    **results[i]
                }
                for i in range(len(results))
            ]
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"详细结果已保存到: {args.output}")


def cmd_list_templates(args):
    """列出模板命令"""
    setup_logging(args.verbose)

    inspector = create_inspector(args.templates)
    templates = inspector.get_template_list()

    if args.output_format == 'json':
        print(json.dumps(templates, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("可用模板")
        print("=" * 60)
        for t in templates:
            print(f"\n名称: {t['name']}")
            print(f"  类型: {t['type']}")
            print(f"  科室: {t['department']}")
            print(f"  质量评分: {t['score']}")
            print(f"  长度: {t['length']} 字符")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Medical Record Inspector - 病历质控工具'
    )

    # 全局参数
    parser.add_argument(
        '--templates', '-t',
        default='templates',
        help='模板目录路径 (默认: templates)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )

    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # single 命令
    single_parser = subparsers.add_parser('single', help='检测单个病历')
    single_parser.add_argument('input', help='病历文件路径')
    single_parser.add_argument('--template', '-T', help='指定模板名称')
    single_parser.add_argument('--output', '-o', help='输出文件路径')
    single_parser.add_argument(
        '--format', '-f',
        dest='output_format',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)'
    )
    single_parser.set_defaults(func=cmd_single)

    # batch 命令
    batch_parser = subparsers.add_parser('batch', help='批量检测')
    batch_parser.add_argument('input', help='病历文件目录路径')
    batch_parser.add_argument('--template', '-T', help='指定模板名称')
    batch_parser.add_argument('--output', '-o', help='输出文件路径')
    batch_parser.add_argument(
        '--format', '-f',
        dest='output_format',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)'
    )
    batch_parser.set_defaults(func=cmd_batch)

    # list-templates 命令
    list_parser = subparsers.add_parser('list-templates', help='列出可用模板')
    list_parser.add_argument('--output', '-o', help='输出文件路径')
    list_parser.add_argument(
        '--format', '-f',
        dest='output_format',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)'
    )
    list_parser.set_defaults(func=cmd_list_templates)

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行命令
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

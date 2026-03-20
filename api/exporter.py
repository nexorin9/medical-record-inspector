"""
Report Exporter for Medical Record Inspector.

This module provides functionality to export quality assessment results
to multiple formats: JSON, HTML, PDF, and Markdown.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from api.models import QualityAssessment


class ReportExporter:
    """报告导出器"""

    def __init__(self, output_dir: str = "reports"):
        """
        初始化导出器。

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_json(self, assessment: QualityAssessment, filename: str = None) -> str:
        """
        导出为 JSON 格式。

        Args:
            assessment: 评估结果
            filename: 输出文件名

        Returns:
            文件路径
        """
        if filename is None:
            filename = f"{assessment.assessment_id}.json"

        filepath = os.path.join(self.output_dir, filename)

        data = {
            "assessment_id": assessment.assessment_id,
            "patient_id": assessment.patient_id,
            "visit_id": assessment.visit_id,
            "scores": {
                "completeness_score": assessment.scores.completeness_score,
                "consistency_score": assessment.scores.consistency_score,
                "timeliness_score": assessment.scores.timeliness_score,
                "standardization_score": assessment.scores.standardization_score,
                "overall_score": assessment.scores.overall_score
            },
            "issues": [
                {
                    "issue_id": issue.issue_id,
                    "category": issue.category,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                    "relevant_fields": issue.relevant_fields
                }
                for issue in assessment.issues
            ],
            "report": assessment.report,
            "timestamp": assessment.评估时间.isoformat(),
            "standard_template_id": assessment.standard_template_id
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def export_markdown(self, assessment: QualityAssessment, filename: str = None) -> str:
        """
        导出为 Markdown 格式。

        Args:
            assessment: 评估结果
            filename: 输出文件名

        Returns:
            文件路径
        """
        if filename is None:
            filename = f"{assessment.assessment_id}.md"

        filepath = os.path.join(self.output_dir, filename)

        lines = [
            f"# 病历质量评估报告\n",
            f"**评估ID**: {assessment.assessment_id}\n",
            f"**评估时间**: {assessment.评估时间.strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**患者ID**: {assessment.patient_id or 'N/A'}\n",
            f"**就诊ID**: {assessment.visit_id or 'N/A'}\n",
            f"\n## 综合评分\n",
            f"**总体评分**: {assessment.scores.overall_score:.1f}/10.0\n",
            f"\n### 各维度评分\n",
            f"- 完整性: {assessment.scores.completeness_score:.1f}/10.0\n",
            f"- 逻辑一致性: {assessment.scores.consistency_score:.1f}/10.0\n",
            f"- 及时性: {assessment.scores.timeliness_score:.1f}/10.0\n",
            f"- 规范性: {assessment.scores.standardization_score:.1f}/10.0\n",
            f"\n## 发现的问题\n"
        ]

        if assessment.issues:
            for i, issue in enumerate(assessment.issues, 1):
                lines.extend([
                    f"### [{i}] {issue.category.upper()} - {issue.severity.upper()}\n",
                    f"- **问题**: {issue.description}\n",
                    f"- **建议**: {issue.suggestion}\n",
                    f"- **相关字段**: {', '.join(issue.relevant_fields)}\n"
                ])
        else:
            lines.append("未发现明显问题。\n")

        lines.extend([
            f"\n## 总体评价\n",
            f"{assessment.report}\n",
            f"\n---\n",
            f"*报告由 Medical Record Inspector 生成*\n"
        ])

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return filepath

    def export_html(self, assessment: QualityAssessment, filename: str = None) -> str:
        """
        导出为 HTML 格式。

        Args:
            assessment: 评估结果
            filename: 输出文件名

        Returns:
            文件路径
        """
        if filename is None:
            filename = f"{assessment.assessment_id}.html"

        filepath = os.path.join(self.output_dir, filename)

        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>病历质量评估报告 - {assessment.assessment_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #1e88e5, #1565c0); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header-info {{ display: flex; justify-content: space-between; flex-wrap: wrap; }}
        .info-item {{ margin: 5px 15px; }}
        .score-card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .score-card h2 {{ font-size: 18px; margin-bottom: 15px; color: #1e88e5; border-bottom: 2px solid #1e88e5; padding-bottom: 10px; }}
        .scores-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .score-item {{ background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; }}
        .score-label {{ font-size: 12px; color: #666; margin-bottom: 5px; }}
        .score-value {{ font-size: 24px; font-weight: bold; }}
        .score-value.good {{ color: #4caf50; }}
        .score-value.fair {{ color: #ff9800; }}
        .score-value.poor {{ color: #f44336; }}
        .issues-section {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .issue {{ background: #fff5f5; border-left: 4px solid #f44336; padding: 15px; margin: 10px 0; border-radius: 0 5px 5px 0; }}
        .issue-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
        .issue-category {{ font-weight: bold; color: #f44336; }}
        .issue-severity {{ font-size: 12px; padding: 2px 8px; border-radius: 3px; background: #ffebee; }}
        .severity-high {{ background: #ffcdd2; color: #c62828; }}
        .severity-medium {{ background: #fff9c4; color: #f57f17; }}
        .severity-low {{ background: #e8f5e9; color: #2e7d32; }}
        .report {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .overall-score {{ font-size: 48px; font-weight: bold; text-align: center; }}
        .overall-score.good {{ color: #4caf50; }}
        .overall-score.fair {{ color: #ff9800; }}
        .overall-score.poor {{ color: #f44336; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>病历质量评估报告</h1>
        <div class="header-info">
            <div class="info-item">评估ID: {assessment.assessment_id}</div>
            <div class="info-item">评估时间: {assessment.评估时间.strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="info-item">患者ID: {assessment.patient_id or 'N/A'}</div>
        </div>
    </div>

    <div class="score-card">
        <h2>总体评分</h2>
        <div class="overall-score {'good' if assessment.scores.overall_score >= 7 else 'fair' if assessment.scores.overall_score >= 5 else 'poor'}">
            {assessment.scores.overall_score:.1f}<span style="font-size: 24px; color: #666;">/10</span>
        </div>
    </div>

    <div class="score-card">
        <h2>各维度评分</h2>
        <div class="scores-grid">
            <div class="score-item">
                <div class="score-label">完整性</div>
                <div class="score-value {'good' if assessment.scores.completeness_score >= 7 else 'fair' if assessment.scores.completeness_score >= 5 else 'poor'}">{assessment.scores.completeness_score:.1f}</div>
            </div>
            <div class="score-item">
                <div class="score-label">逻辑一致性</div>
                <div class="score-value {'good' if assessment.scores.consistency_score >= 7 else 'fair' if assessment.scores.consistency_score >= 5 else 'poor'}">{assessment.scores.consistency_score:.1f}</div>
            </div>
            <div class="score-item">
                <div class="score-label">及时性</div>
                <div class="score-value {'good' if assessment.scores.timeliness_score >= 7 else 'fair' if assessment.scores.timeliness_score >= 5 else 'poor'}">{assessment.scores.timeliness_score:.1f}</div>
            </div>
            <div class="score-item">
                <div class="score-label">规范性</div>
                <div class="score-value {'good' if assessment.scores.standardization_score >= 7 else 'fair' if assessment.scores.standardization_score >= 5 else 'poor'}">{assessment.scores.standardization_score:.1f}</div>
            </div>
        </div>
    </div>

    <div class="issues-section">
        <h2>发现的问题</h2>
"""

        if assessment.issues:
            for issue in assessment.issues:
                severity_class = f"severity-{issue.severity.lower()}"
                lines = [
                    f'<div class="issue">',
                    f'    <div class="issue-header">',
                    f'        <span class="issue-category">[{issue.issue_id}] {issue.category.upper()}</span>',
                    f'        <span class="issue-severity {severity_class}">{issue.severity.upper()}</span>',
                    f'    </div>',
                    f'    <div class="issue-content">',
                    f'        <p><strong>问题:</strong> {issue.description}</p>',
                    f'        <p><strong>建议:</strong> {issue.suggestion}</p>',
                    f'        <p><strong>相关字段:</strong> {", ".join(issue.relevant_fields)}</p>',
                    f'    </div>',
                    f'</div>'
                ]
                html_content += '\n'.join(lines)
        else:
            html_content += "<p>未发现明显问题。</p>"

        html_content += f"""
    </div>

    <div class="report">
        <h2>总体评价</h2>
        <p>{assessment.report}</p>
    </div>

    <div class="footer">
        <p>报告由 Medical Record Inspector 生成 | 评估ID: {assessment.assessment_id}</p>
    </div>
</body>
</html>
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content.strip())

        return filepath

    def export_pdf(self, html_filepath: str, pdf_filename: str = None) -> str:
        """
        将 HTML 报告转换为 PDF 格式。

        Args:
            html_filepath: HTML 文件路径
            pdf_filename: PDF 输出文件名

        Returns:
            PDF 文件路径
        """
        try:
            import weasyprint

            if pdf_filename is None:
                pdf_filename = Path(html_filepath).stem + ".pdf"

            html_path = Path(html_filepath)
            pdf_path = Path(self.output_dir) / pdf_filename

            weasyprint.HTML(html_path).write_pdf(pdf_path)

            return str(pdf_path)

        except ImportError:
            # weasyprint 未安装，尝试使用 pdfkit
            try:
                import pdfkit

                if pdf_filename is None:
                    pdf_filename = Path(html_filepath).stem + ".pdf"

                html_path = Path(html_filepath)
                pdf_path = Path(self.output_dir) / pdf_filename

                pdfkit.from_file(html_path, pdf_path)

                return str(pdf_path)

            except ImportError:
                # 都没有安装，返回 HTML 路径并提示
                return f"No PDF library installed. Please use 'pip install weasyprint' or 'pip install pdfkit'. HTML report available at: {html_filepath}"

    def export_all(self, assessment: QualityAssessment, base_filename: str = None) -> Dict[str, str]:
        """
        导出为所有格式。

        Args:
            assessment: 评估结果
            base_filename: 基础文件名

        Returns:
            各格式文件路径字典
        """
        if base_filename is None:
            base_filename = assessment.assessment_id

        results = {}

        # 导出 JSON
        results["json"] = self.export_json(assessment, f"{base_filename}.json")

        # 导出 Markdown
        results["markdown"] = self.export_markdown(assessment, f"{base_filename}.md")

        # 导出 HTML
        results["html"] = self.export_html(assessment, f"{base_filename}.html")

        return results


def quick_export(assessment: QualityAssessment, output_dir: str = "reports") -> Dict[str, str]:
    """
    快速导出的便捷函数。

    Args:
        assessment: 评估结果
        output_dir: 输出目录

    Returns:
        各格式文件路径字典
    """
    exporter = ReportExporter(output_dir=output_dir)
    return exporter.export_all(assessment)


if __name__ == "__main__":
    # 简单测试
    from api.models import QualityScore, Issue

    test_assessment = QualityAssessment(
        assessment_id="TEST-EXPORT-001",
        patient_id="PAT001",
        visit_id="VIS001",
        scores=QualityScore(
            completeness_score=8.5,
            consistency_score=9.0,
            timeliness_score=7.5,
            standardization_score=8.0,
            overall_score=8.25
        ),
        issues=[
            Issue(
                issue_id="I001",
                category="completeness",
                severity="medium",
                description="现病史描述不够详细",
                suggestion="请补充症状持续时间、严重程度等信息",
                relevant_fields=["present_illness"]
            )
        ],
        report="病历质量良好，略有改进空间。",
        标注时间=None
    )

    exporter = ReportExporter()
    results = exporter.export_all(test_assessment, "test_export")

    print("导出结果:")
    for fmt, filepath in results.items():
        print(f"  {fmt.upper()}: {filepath}")

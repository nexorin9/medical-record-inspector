"""
结果可视化模块 - Medical Record Inspector
实现 HTML 报告生成，用颜色和图表展示检测结果
"""

import os
from typing import Dict, List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """HTML 报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self.template_dir = Path(__file__).parent.parent / "templates"

    def generate_html_report(self, analysis_result: Dict, output_path: str = None) -> str:
        """
        生成 HTML 报告

        Args:
            analysis_result: 分析结果
            output_path: 输出文件路径（可选）

        Returns:
            HTML 内容字符串
        """
        html = self._build_html(analysis_result)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"HTML 报告已保存到: {output_path}")

        return html

    def _build_html(self, result: Dict) -> str:
        """构建 HTML 内容"""
        score = result.get('overall_score', 0)
        template = result.get('template_used', 'N/A')
        defects = result.get('defects', [])
        defect_count = result.get('defect_count', len(defects))

        # 评估等级和颜色
        if score >= 0.8:
            level = "优秀"
            level_color = "#28a745"
        elif score >= 0.6:
            level = "合格"
            level_color = "#ffc107"
        else:
            level = "需要改进"
            level_color = "#dc3545"

        # 段落分析
        para_analysis = result.get('paragraph_analysis', {})
        chunk_analysis = result.get('chunk_analysis', {})

        # 缺陷列表 HTML
        defects_html = self._build_defects_html(defects)

        # 热力图 HTML
        defect_map = result.get('defect_map', {})
        heat_map_html = self._build_heat_map_html(defect_map)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>病历质控报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .score-card {{ display: inline-block; margin-top: 20px; padding: 15px 30px; background: rgba(255,255,255,0.2); border-radius: 8px; }}
        .score-value {{ font-size: 2.5em; font-weight: bold; }}
        .score-label {{ font-size: 0.9em; opacity: 0.9; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .summary-card h3 {{ font-size: 0.9em; color: #666; margin-bottom: 10px; text-transform: uppercase; }}
        .summary-card .value {{ font-size: 1.5em; font-weight: bold; color: {level_color}; }}
        .section {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ font-size: 1.4em; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .defect-item {{ padding: 15px; border-left: 4px solid #dc3545; background: #fff5f5; margin-bottom: 10px; border-radius: 5px; }}
        .defect-item.warning {{ border-left-color: #ffc107; background: #fff9e6; }}
        .defect-item .defect-type {{ font-size: 0.8em; color: #666; text-transform: uppercase; }}
        .defect-item .defect-score {{ font-size: 1.2em; font-weight: bold; color: #dc3545; }}
        .defect-item .defect-text {{ margin-top: 10px; padding: 10px; background: white; border-radius: 5px; font-family: monospace; }}
        .heat-map {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }}
        .heat-map-item {{ padding: 10px 15px; border-radius: 5px; flex: 1 1 30%; max-width: 400px; }}
        .heat-map-item.anomaly {{ background: #fff0f0; border: 1px solid #dc3545; }}
        .heat-map-item.normal {{ background: #f0fff0; border: 1px solid #28a745; }}
        .heat-map-index {{ font-size: 0.8em; color: #666; }}
        .heat-map-score {{ font-size: 1.2em; font-weight: bold; }}
        .heat-map-item.anomaly .heat-map-score {{ color: #dc3545; }}
        .heat-map-item.normal .heat-map-score {{ color: #28a745; }}
        .info-box {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .info-box .label {{ font-weight: bold; color: #1976d2; }}
        .metric {{ display: inline-block; margin-right: 20px; }}
        .metric-label {{ font-size: 0.85em; color: #666; margin-right: 5px; }}
        .metric-value {{ font-size: 1.1em; font-weight: bold; }}
        .progress-bar {{ height: 10px; background: #e0e0e0; border-radius: 5px; overflow: hidden; margin-top: 5px; }}
        .progress-fill {{ height: 100%; border-radius: 5px; }}
        .status-{{level}} {{ background: {level_color}; }}
        @media (max-width: 600px) {{ .summary-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>病历质控报告</h1>
            <div class="summary-grid" style="display:flex; gap:30px; flex-wrap:wrap;">
                <div class="score-card">
                    <div class="score-value" style="color: white;">{score:.3f}</div>
                    <div class="score-label">相似度分数</div>
                </div>
                <div class="score-card">
                    <div class="score-value" style="color: white; font-size: 2em;">{level}</div>
                    <div class="score-label">质量等级</div>
                </div>
                <div class="score-card">
                    <div class="score-value" style="color: white; font-size: 2em;">{defect_count}</div>
                    <div class="score-label">发现缺陷</div>
                </div>
            </div>
        </div>

        <!-- Overview -->
        <div class="summary-grid">
            <div class="summary-card">
                <h3>使用模板</h3>
                <div class="value">{template}</div>
            </div>
            <div class="summary-card">
                <h3>总体评价</h3>
                <div class="value" style="color: {level_color};">{self._get_evaluation(score)}</div>
            </div>
            <div class="summary-card">
                <h3>风险等级</h3>
                <div class="value" style="color: {level_color};">{level}</div>
            </div>
        </div>

        <!-- Section: Definition -->
        <div class="section">
            <h2>分析详情</h2>

            <div class="info-box">
                <div class="metric">
                    <span class="metric-label">段落总数:</span>
                    <span class="metric-value">{para_analysis.get('total', 0)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">异常段落:</span>
                    <span class="metric-value">{para_analysis.get('defects', 0)}</span>
                </div>
            </div>

            <div class="info-box">
                <div class="metric">
                    <span class="metric-label">分块总数:</span>
                    <span class="metric-value">{chunk_analysis.get('total', 0)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">异常分块:</span>
                    <span class="metric-value">{chunk_analysis.get('defects', 0)}</span>
                </div>
            </div>

            <!-- Progress Bars -->
            <div style="margin-top: 20px;">
                <div>
                    <span class="metric-label">段落质量进度:</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {min(score*100, 100)}%; {self._get_progress_color(score)}"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Section: Defects -->
        {defects_html}

        <!-- Section: Heat Map -->
        {heat_map_html}
    </div>
</body>
</html>"""

        return html

    def _build_defects_html(self, defects: List[Dict]) -> str:
        """构建缺陷 HTML"""
        if not defects:
            return """<div class="section">
            <h2>缺陷列表</h2>
            <div class="info-box" style="background: #e8f5e9; border: 1px solid #28a745;">
                <strong style="color: #28a745;">没有发现明显缺陷</strong>
            </div>
        </div>"""

        defects_html = """<div class="section">
            <h2>缺陷列表</h2>
        """

        for i, defect in enumerate(defects[:10], 1):
            defect_type = defect.get('type', 'unknown')
            similarity = defect.get('similarity', 0)
            text = defect.get('text', '')[:300]

            warning_class = "warning" if similarity >= 0.5 else ""

            defects_html += f"""<div class="defect-item {warning_class}">
                <div class="defect-type">{defect_type} # {i}</div>
                <div class="defect-score">相似度: {similarity:.3f}</div>
                <div class="defect-text">{text}</div>
            </div>"""

        defects_html += "</div>"
        return defects_html

    def _build_heat_map_html(self, defect_map: Dict) -> str:
        """构建热力图 HTML"""
        heat_map = defect_map.get('heat_map', [])
        if not heat_map:
            return """<div class="section">
            <h2>缺陷热力图</h2>
            <div class="info-box">暂无热力图数据</div>
        </div>"""

        html = """<div class="section">
            <h2>缺陷热力图</h2>
            <div class="heat-map">
        """

        for item in heat_map[:30]:  # 最多显示30个
            anomaly_class = "anomaly" if item.get('anomaly') else "normal"
            score = item.get('similarity', 0)
            text = item.get('text', '')[:50]

            html += f"""<div class="heat-map-item {anomaly_class}">
                <div class="heat-map-index">#{item.get('order', 0)}</div>
                <div class="heat-map-score">{score:.3f}</div>
                <div>{text}</div>
            </div>"""

        html += "</div></div>"
        return html

    def _get_evaluation(self, score: float) -> str:
        """获取评价文本"""
        if score >= 0.8:
            return "病历质量良好，与模板高度相似"
        elif score >= 0.6:
            return "病历存在一定问题，建议参考模板进行完善"
        else:
            return "病历质量较差，需要重点修改"

    def _get_progress_color(self, score: float) -> str:
        """获取进度条颜色"""
        if score >= 0.8:
            return "background: #28a745;"
        elif score >= 0.6:
            return "background: #ffc107;"
        else:
            return "background: #dc3545;"


def create_report_generator() -> HTMLReportGenerator:
    """创建报告生成器"""
    return HTMLReportGenerator()


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    # 创建测试结果
    test_result = {
        'overall_score': 0.65,
        'template_used': '内科标准模板',
        'defect_count': 3,
        'defects': [
            {'type': 'paragraph', 'index': 2, 'similarity': 0.45, 'text': '患者有高血压病史'},
            {'type': 'paragraph', 'index': 4, 'similarity': 0.38, 'text': '给予青霉素治疗'},
            {'type': 'chunk', 'index': 5, 'similarity': 0.52, 'text': '体温最高39度'}
        ],
        'paragraph_analysis': {'total': 10, 'defects': 2},
        'chunk_analysis': {'total': 25, 'defects': 3},
        'defect_map': {
            'heat_map': [
                {'order': 0, 'text': '患者基本信息', 'similarity': 0.85, 'anomaly': False},
                {'order': 1, 'text': '主诉: 发热咳嗽3天', 'similarity': 0.78, 'anomaly': False},
                {'order': 2, 'text': '既往史', 'similarity': 0.45, 'anomaly': True},
                {'order': 3, 'text': '辅助检查', 'similarity': 0.38, 'anomaly': True},
            ]
        }
    }

    print("=== Report Generator 测试 ===\n")

    generator = create_report_generator()
    html = generator.generate_html_report(test_result)

    print(f"HTML 报告生成成功")
    print(f"长度: {len(html)} 字符")

    # 保存到文件
    output_path = Path(__file__).parent.parent / 'data' / 'reports' / 'test_report.html'
    generator.generate_html_report(test_result, str(output_path))
    print(f"\n报告已保存到: {output_path}")

"""
核心检测引擎 - Medical Record Inspector
整合所有模块，实现完整的病历检测流程
"""

import os
from typing import List, Dict, Optional
import logging

from src.extractor import extract_text, extract_text_from_directory
from src.template_loader import get_template_loader, TemplateLoader
from src.embedder import get_embedder
from src.similarity import get_similarity_calculator, SimilarityCalculator
from src.anomaly_detector import MedicalRecordAnomalyDetector
from src.locator import Locator, create_locator
from src.explainer import Explainer, create_explainer

logger = logging.getLogger(__name__)


class MedicalRecordInspector:
    """病历质控核心引擎 - 整合所有模块"""

    def __init__(self, template_dir: str = "templates", model_dir: str = None):
        """
        初始化质控引擎

        Args:
            template_dir: 模板目录
            model_dir: 模型目录（可选）
        """
        self.template_dir = template_dir
        self.model_dir = model_dir

        # 初始化模块
        self.template_loader = get_template_loader(template_dir)
        self.embedder = get_embedder()
        self.calculator = get_similarity_calculator()
        self.anomaly_detector = MedicalRecordAnomalyDetector()
        self.locator = create_locator()
        self.explainer = create_explainer()

        # 标记是否已加载模板
        self._templates_loaded = False

    def load_templates(self) -> int:
        """
        加载模板库

        Returns:
            加载的模板数量
        """
        self.template_loader = get_template_loader(self.template_dir)
        self._templates_loaded = True
        return len(self.template_loader.list_templates())

    def analyze(self, record_text: str,
                template_name: str = None) -> Dict:
        """
        分析单个病历

        Args:
            record_text: 病历文本
            template_name: 模板名称（可选，不指定则与所有模板比较）

        Returns:
            分析结果字典
        """
        if not self._templates_loaded:
            self.load_templates()

        results = {
            'record_length': len(record_text),
            'template_used': None,
            'overall_score': 0.0,
            'similarity_scores': [],
            'defects': [],
            'explanations': [],
            'defect_map': {}
        }

        # 如果指定了模板
        if template_name:
            template = self.template_loader.get_template(template_name)
            if not template:
                logger.warning(f"模板不存在: {template_name}")
                results['error'] = f"模板不存在: {template_name}"
                return results

            results['template_used'] = template_name
            result = self._analyze_against_template(record_text, template)
            results.update(result)
        else:
            # 与所有模板比较
            templates = self.template_loader.list_templates()
            best_score = 0
            best_template = None
            # 初始化为默认值，包含所有必需字段
            best_result = {
                'overall_score': 0.0,
                'template_used': None,
                'similarity_scores': [],
                'defects': [],
                'defect_count': 0,
                'defect_ratio': 0.0,
                'defect_map': {},
                'paragraph_analysis': {'total': 0, 'defects': 0},
                'chunk_analysis': {'total': 0, 'defects': 0}
            }

            for template_info in templates:
                name = template_info['name']
                template = self.template_loader.get_template(name)
                if not template:
                    continue

                result = self._analyze_against_template(record_text, template)

                if result['overall_score'] > best_score:
                    best_score = result['overall_score']
                    best_template = name
                    best_result = result

            results['template_used'] = best_template
            results['all_scores'] = {t['name']: t['score'] for t in results.get('similarity_scores', [])}
            results.update(best_result)

        return results

    def _analyze_against_template(self, record_text: str,
                                   template: Dict) -> Dict:
        """分析病历与单个模板的相似度"""
        template_name = template['path'].split('/')[-1].replace('.txt', '')
        template_text = template['content']

        # 计算整体相似度
        record_embedding = self.embedder.embed(record_text)
        template_embedding = self.embedder.embed(template_text)

        overall_score = self.calculator.cosine_similarity_single(
            record_embedding, template_embedding
        )

        # 段落级分析
        defect_result = self.locator.locate_defects(record_text, template_text)

        # 分块级分析
        chunk_results = self.locator.calculate_chunk_embedding_similarity(
            record_text, template_text
        )

        # 生成缺陷列表
        defects = []
        for p in defect_result['paragraph_scores']:
            if p['similarity'] < 0.6:
                defects.append({
                    'type': 'paragraph',
                    'index': p['index'],
                    'similarity': p['similarity'],
                    'text': p['text']
                })

        for c in chunk_results:
            if c['avg_similarity'] < 0.6:
                defects.append({
                    'type': 'chunk',
                    'index': c['index'],
                    'similarity': c['avg_similarity'],
                    'text': c['text']
                })

        # 生成热力图
        defect_map = self.locator.generate_defect_map(record_text, template_text)

        return {
            'overall_score': overall_score,
            'template_used': template_name,
            'similarity_scores': [
                {'reference': template_name, 'score': overall_score}
            ],
            'defects': defects[:10],  # 只返回前10个
            'defect_count': len(defects),
            'defect_ratio': defect_result['defect_ratio'],
            'defect_map': defect_map,
            'paragraph_analysis': {
                'total': defect_result['total_paragraphs'],
                'defects': defect_result['defect_count']
            },
            'chunk_analysis': {
                'total': len(chunk_results),
                'defects': sum(1 for c in chunk_results if c['avg_similarity'] < 0.6)
            }
        }

    def analyze_batch(self, records: List[str],
                      template_name: str = None) -> List[Dict]:
        """
        批量分析病历

        Args:
            records: 病历文本列表
            template_name: 模板名称（可选）

        Returns:
            分析结果列表
        """
        results = []
        for i, record in enumerate(records):
            result = self.analyze(record, template_name)
            result['record_index'] = i
            results.append(result)
            logger.info(f"完成第 {i+1}/{len(records)} 个病历分析")

        return results

    def generate_report(self, analysis_result: Dict) -> Dict:
        """
        生成详细报告

        Args:
            analysis_result: 分析结果

        Returns:
            报告字典
        """
        report = {
            'analysis': analysis_result,
            'summary': {},
            'explanations': []
        }

        # 生成总结
        score = analysis_result.get('overall_score', 0)
        defects = analysis_result.get('defects', [])

        if score >= 0.8:
            risk_level = "低"
            summary = "病历质量良好，与模板高度相似"
        elif score >= 0.6:
            risk_level = "中"
            summary = "病历存在一定问题，建议参考模板进行完善"
        else:
            risk_level = "高"
            summary = "病历质量较差，需要重点修改"

        report['summary'] = {
            'overall_score': score,
            'risk_level': risk_level,
            'defect_count': len(defects),
            'summary_text': summary
        }

        # 生成解释（如果有缺陷）
        if defects:
            defect_data = {
                'overall_score': score,
                'defects': [
                    {'index': d['index'], 'similarity': d['similarity'],
                     'text': d['text']}
                    for d in defects[:5]
                ]
            }
            explanations = self.explainer.generate_defect_report(defect_data)
            report['explanations'] = explanations

        return report

    def get_template_list(self) -> List[Dict]:
        """获取模板列表"""
        if not self._templates_loaded:
            self.load_templates()
        return self.template_loader.list_templates()


def create_inspector(template_dir: str = "templates") -> MedicalRecordInspector:
    """创建默认质控引擎"""
    return MedicalRecordInspector(template_dir=template_dir)


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=== Core Inspector 测试 ===\n")

    # 创建测试病历
    test_record = """患者基本信息
姓名：张三
性别：男
年龄：45岁

主诉
发热咳嗽3天。

现病史
患者3天前受凉后出现发热，体温最高39度，伴咳嗽咳痰。

既往史
否认高血压、糖尿病史。

体格检查
双肺呼吸音粗。

辅助检查
胸部CT示右肺下叶斑片影。

诊断
社区获得性肺炎。

诊疗经过
给予头孢曲松静滴，对症治疗。

出院诊断
社区获得性肺炎。
"""

    # 测试 Inspector
    try:
        inspector = create_inspector()

        # 测试模板列表
        print("模板列表:")
        templates = inspector.get_template_list()
        print(f"  共 {len(templates)} 个模板")

        # 测试分析（需要模板）
        print("\n分析单个病历:")
        result = inspector.analyze(test_record)
        print(f"  总体分数: {result.get('overall_score', 'N/A'):.3f}")
        print(f"  使用模板: {result.get('template_used', 'N/A')}")
        print(f"  缺陷数量: {result.get('defect_count', 'N/A')}")

        # 测试批量分析
        print("\n批量分析:")
        batch_result = inspector.analyze_batch([test_record, test_record])
        print(f"  分析数量: {len(batch_result)}")

    except Exception as e:
        print(f"  注意: {e}")
        print("  （需要先配置 templates/ 目录和 API key）")

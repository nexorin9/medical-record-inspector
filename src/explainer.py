"""
LLM 解释模块 - Medical Record Inspector
集成 LLM 生成可解释的缺陷报告，说明'为什么这个病历可疑'
"""

import os
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Explainer:
    """LLM 解释器 - 生成可解释的病历缺陷报告"""

    def __init__(self, model: str = None, api_base: str = None):
        """
        初始化解释器

        Args:
            model: LLM 模型名称
            api_base: API 基础 URL
        """
        self.model = model or os.environ.get('LLM_MODEL', 'gpt-4')
        self.api_base = api_base or os.environ.get('LLM_API_BASE', 'https://api.openai.com/v1')

        # 延迟加载
        self._client = None

    def _load_client(self):
        """加载 OpenAI 客户端"""
        if self._client is None:
            from openai import OpenAI
            api_key = os.environ.get('LLM_API_KEY')
            if not api_key:
                raise ValueError("需要设置 LLM_API_KEY 环境变量")

            self._client = OpenAI(
                api_key=api_key,
                base_url=self.api_base
            )
        return self._client

    def generate_explanation(self, defect_type: str, details: Dict) -> str:
        """
        生成自然语言解释

        Args:
            defect_type: 缺陷类型
            details: 缺陷详情

        Returns:
            自然语言解释
        """
        client = self._load_client()

        # 构建 prompt
        prompt = self._build_explanation_prompt(defect_type, details)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return f"无法生成解释: {e}"

    def _get_system_prompt(self) -> str:
        """获取系统 prompt"""
        return """你是一个专业的医疗质控专家。你的任务是：
1. 用简洁易懂的语言解释病历中的问题
2. 指出问题的严重程度
3. 给出改进建议
4. 保持专业但友好的语气"""

    def _build_explanation_prompt(self, defect_type: str, details: Dict) -> str:
        """构建解释 prompt"""
        prompt = f"""请分析以下病历缺陷并给出解释：

缺陷类型：{defect_type}

详情：
{json.dumps(details, ensure_ascii=False, indent=2)}

请按以下格式回答：
1. 问题描述
2. 潜在风险
3. 改进建议"""

        return prompt

    def generate_defect_report(self, defect_data: Dict) -> Dict:
        """
        生成完整的缺陷报告

        Args:
            defect_data: 缺陷数据字典

        Returns:
            报告字典
        """
        results = []

        # 段落级缺陷解释
        if 'paragraph_defects' in defect_data:
            for defect in defect_data['paragraph_defects'][:5]:  # 只解释前5个
                explanation = self.generate_explanation(
                    'paragraph_similarity_low',
                    {
                        'paragraph_index': defect.get('index'),
                        'similarity': defect.get('similarity', defect.get('avg_similarity', 0)),
                        'content': defect.get('text', '')[:200]
                    }
                )
                results.append({
                    'type': 'paragraph_defect',
                    'explanation': explanation
                })

        # 分块级缺陷解释
        if 'chunk_defects' in defect_data:
            for defect in defect_data['chunk_defects'][:5]:
                explanation = self.generate_explanation(
                    'content_deviation',
                    {
                        'chunk_index': defect.get('index'),
                        'similarity': defect.get('avg_similarity', defect.get('similarity', 0)),
                        'content': defect.get('text', '')[:200]
                    }
                )
                results.append({
                    'type': 'content_deviation',
                    'explanation': explanation
                })

        return {
            'total_issues': len(results),
            'issues': results
        }

    def generate_summary_report(self, record_text: str,
                                 template_name: str,
                                 overall_score: float,
                                 defects: List[Dict]) -> Dict:
        """
        生成总结报告

        Args:
            record_text: 病历文本（用于生成特定解释）
            template_name: 模板名称
            overall_score: 总体相似度分数
            defects: 缺陷列表

        Returns:
            报告字典
        """
        client = self._load_client()

        # 构建总结 prompt
        defects_summary = json.dumps(defects[:10], ensure_ascii=False)

        prompt = f"""请生成一份病历质控报告总结：

病历与模板 '{template_name}' 的匹配度：{overall_score:.3f}

发现的主要缺陷（按严重程度排序）：
{defects_summary}

请生成：
1. 总体评价
2. 主要问题（Top 3）
3. 具体改进建议
4. 风险等级评估（低/中/高）

格式要求：
- 使用Markdown格式
- 语言简洁专业
- 重点问题加粗标记"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )

            return {
                'template': template_name,
                'overall_score': overall_score,
                'summary': response.choices[0].message.content,
                'defects_count': len(defects),
                'risk_level': self._assess_risk_level(overall_score, defects)
            }
        except Exception as e:
            logger.error(f"总结报告生成失败: {e}")
            return {
                'template': template_name,
                'overall_score': overall_score,
                'summary': f"报告生成失败: {e}",
                'defects_count': len(defects),
                'risk_level': '未知'
            }

    def _assess_risk_level(self, score: float, defects: List[Dict]) -> str:
        """评估风险等级（基于相似度分数和缺陷数量）"""
        if score >= 0.8 and len(defects) == 0:
            return "低"
        elif score >= 0.6 and len(defects) <= 3:
            return "中"
        else:
            return "高"


def create_explainer() -> Explainer:
    """创建默认解释器"""
    return Explainer()


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    # 测试 Explainer（不实际调用 API）
    print("=== Explainer 测试 ===\n")

    # 创建缺陷数据
    test_defects = [
        {
            'type': 'paragraph_defect',
            'index': 2,
            'text': '患者有高血压病史',
            'similarity': 0.45
        },
        {
            'type': 'paragraph_defect',
            'index': 4,
            'text': '给予青霉素治疗',
            'similarity': 0.38
        }
    ]

    # 测试 explain（不实际调用 API）
    print("测试 Explain 方法:")
    try:
        explainer = create_explainer()
        print(f"  Explainer 初始化成功")
        print(f"  模型: {explainer.model}")
    except Exception as e:
        print(f"  警告: {e}")

    # 测试报告生成
    print("\n测试 generate_summary_report:")
    try:
        report = explainer.generate_summary_report(
            record_text="患者男性，45岁...（测试病历）",
            template_name="内科标准模板",
            overall_score=0.65,
            defects=test_defects
        )
        print(f"  报告模板: {report['template']}")
        print(f"  总体分数: {report['overall_score']:.3f}")
        print(f"  风险等级: {report['risk_level']}")
    except Exception as e:
        print(f"  警告: API 调用失败（需要设置 LLM_API_KEY）")

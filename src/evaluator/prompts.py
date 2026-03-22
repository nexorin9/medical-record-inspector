"""
Evaluator Prompts Module - Prompt templates for medical record evaluation
"""

from typing import Dict, Optional


# Base system prompt for evaluation
EVALUATION_SYSTEM_PROMPT = """你是一位资深的病历质控专家，具有丰富的临床经验和严谨的文书书写规范知识。

你的任务是对医生提交的病历文本进行质量评估。你需要从完整性、逻辑性、及时性和规范性四个维度进行分析，并以JSON格式返回结构化评估结果。

评估原则：
1. 客观公正：基于病历内容本身进行评估，不假设未书写的内容
2. 现实合理：考虑临床实际，对合理但非最优的书写不予苛责
3. 重点突出：优先关注影响诊疗安全的关键问题
4. 可解释性：每个问题都要说明具体原因和改进建议

输出必须为JSON格式，包含：dimension_scores（各维度得分0-100）、issues（问题列表）、recommendations（改进建议）"""

# Completeness evaluation prompt template
COMPLETENESS_PROMPT = """请评估以下病历文本的**完整性**。

完整性定义：病历应包含所有基本要素，能够清晰描述患者病情、诊疗过程和医疗决策。

必查基本要素：
- 主诉：患者就诊的主要原因（症状+持续时间）
- 现病史：发病情况、主要症状、诊疗经过、阳性结果
- 既往史：相关既往疾病、手术史、过敏史
- 体格检查：重要阳性体征和阴性体征
- 辅助检查：关键检查结果
- 诊断：诊断名称、诊断依据
- 治疗方案：治疗措施、药物使用
- 医疗决策：病情变化和应对措施

请按以下JSON格式返回评估结果：
{{"dimension_score": <0-100>, "issues": [<issue_object>], "recommendations": [<string>]}}

问题对象格式：
{{"dimension": "completeness", "severity": "critical|m_major|m_minor", "entity": "<缺失要素>", "description": "<具体说明>", "suggestion": "<改进建议>"}}

严重程度标准：
- critical（严重）：缺失关键信息，可能影响诊疗决策
- m_major（中度）：缺失重要信息，影响病历质量
- m_minor（轻微）：缺失常规信息，影响较小

病历文本：
{medical_record}

评估结果："""


# Logicality evaluation prompt template
LOGICALITY_PROMPT = """请评估以下病历文本的**逻辑性**。

逻辑性定义：病历内容之间应有合理的医学逻辑关系，症状、检查、诊断、治疗之间形成连贯的推理链条。

评估要点：
- 症状与体征是否相互印证
- 检查结果是否支持诊断
- 治疗方案是否针对病因和症状
- 病情发展是否符合医学规律
- 是否存在矛盾或不符之处

请按以下JSON格式返回评估结果：
{{"dimension_score": <0-100>, "issues": [<issue_object>], "recommendations": [<string>]}}

问题对象格式：
{{"dimension": "logicality", "severity": "critical|m_major|m_minor", "entity": "<逻辑环节>", "description": "<具体说明>", "suggestion": "<改进建议>"}}

严重程度标准：
- critical（严重）：逻辑矛盾或错误，可能误导诊疗
- m_major（中度）：推理不充分或关联性弱
- m_minor（轻微）：细节衔接不够紧密

病历文本：
{medical_record}

评估结果："""


# Timeliness evaluation prompt template
TIMELINESS_PROMPT = """请评估以下病历文本的**及时性**。

及时性定义：病历书写和医疗操作应及时进行，时间记录准确完整，反映病情变化的及时处理。

评估要点：
- 各时间点是否明确记录（发病时间、就诊时间、检查时间、治疗时间）
- 时间顺序是否合理
- 病情变化是否及时记录
- 操作执行是否及时（如抗生素使用、抢救措施）
- 是否存在时间逻辑矛盾

请按以下JSON格式返回评估结果：
{{"dimension_score": <0-100>, "issues": [<issue_object>], "recommendations": [<string>]}}

问题对象格式：
{{"dimension": "timeliness", "severity": "critical|m_major|m_minor", "entity": "<时间记录>", "description": "<具体说明>", "suggestion": "<改进建议>"}}

严重程度标准：
- critical（严重）：时间缺失或错误，影响医疗事件序列判断
- m_major（中度）：关键时间点记录不完整
- m_minor（轻微）：常规时间记录不够详细

病历文本：
{medical_record}

评估结果："""


# Normativity evaluation prompt template
NORMATIVITY_PROMPT = """请评估以下病历文本的**规范性**。

规范性定义：病历书写应符合国家卫健委《病历书写基本规范》和行业标准，使用规范医学术语，格式正确。

评估要点：
- 格式结构是否符合规范（标题、段落、缩进等）
- 医学术语是否规范准确
- 是否存在错别字、语法错误
- 符号使用是否规范（标点、数字、单位）
- 是否符合电子病历书写标准

请按以下JSON格式返回评估结果：
{{"dimension_score": <0-100>, "issues": [<issue_object>], "recommendations": [<string>]}}

问题对象格式：
{{"dimension": "normativity", "severity": "critical|m_major|m_minor", "entity": "<规范环节>", "description": "<具体说明>", "suggestion": "<改进建议>"}}

严重程度标准：
- critical（严重）：格式错误影响病历法律效力
- m_major（中度）：术语不规范或错误
- m_minor（轻微）：非关键性格式或文字问题

病历文本：
{medical_record}

评估结果："""


# Comprehensive evaluation prompt (all dimensions)
COMPREHENSIVE_PROMPT = """请全面评估以下病历文本的**整体质量**，从完整性、逻辑性、及时性和规范性四个维度进行综合分析。

综合评估要求：
1. 逐项检查四个评估维度
2. 识别每个维度存在的具体问题
3. 综合判断病历的整体质量水平
4. 提供针对性的改进建议

请按以下JSON格式返回评估结果：
{{
  "dimension_scores": {{
    "completeness": <0-100>,
    "logicality": <0-100>,
    "timeliness": <0-100>,
    "normativity": <0-100>
  }},
  "overall_score": <0-100>,
  "issues": [<issue_object>],
  "recommendations": [<string>],
  "summary": "<简要总结>"
}}

问题对象格式：
{{"dimension": "<completeness|logicality|timeliness|normativity>", "severity": "critical|m_major|m_minor", "entity": "<问题类型>", "description": "<具体说明>", "suggestion": "<改进建议>"}}

严重程度综合标准：
- critical（严重）：可能导致误诊、漏诊或医疗纠纷
- m_major（中度）：影响病历质量和教学价值
- m_minor（轻微）：不影响核心质量的小问题

病历文本：
{medical_record}

评估结果："""


# Template-based comparison prompt
TEMPLATE_COMPARISON_PROMPT = """你是一位资深质控专家。请将以下被评估病历与给定的标准模板进行对比，评估其质量差异。

标准模板：
{template_content}

被评估病历：
{medical_record}

请从以下角度进行对比分析：
1. 结构完整性：与模板相比，是否缺少必要的部分？
2. 内容深度：关键要素的描述是否充分？
3. 逻辑链条：推理过程是否完整清晰？
4. 规范性：是否符合标准书写格式？

请按以下JSON格式返回评估结果：
{{
  "comparison_analysis": {{
    "structure_gap": <0-100>,
    "content_depth_score": <0-100>,
    "logical_fulfillment": <0-100>,
    "gap_summary": "<结构和内容差距总结>",
    "key_missing_elements": ["<关键缺失项>"]
  }},
  "recommendations": ["<针对性改进建议>"]
}}

评估结果："""


def get_completeness_prompt(medical_record: str) -> str:
    """Get completeness evaluation prompt with medical record"""
    return COMPLETENESS_PROMPT.format(medical_record=medical_record)


def get_logicality_prompt(medical_record: str) -> str:
    """Get logicality evaluation prompt with medical record"""
    return LOGICALITY_PROMPT.format(medical_record=medical_record)


def get_timeliness_prompt(medical_record: str) -> str:
    """Get timeliness evaluation prompt with medical record"""
    return TIMELINESS_PROMPT.format(medical_record=medical_record)


def get_normativity_prompt(medical_record: str) -> str:
    """Get normativity evaluation prompt with medical record"""
    return NORMATIVITY_PROMPT.format(medical_record=medical_record)


def get_comprehensive_prompt(medical_record: str) -> str:
    """Get comprehensive evaluation prompt with medical record"""
    return COMPREHENSIVE_PROMPT.format(medical_record=medical_record)


def get_template_comparison_prompt(template_content: str, medical_record: str) -> str:
    """Get template-based comparison prompt"""
    return TEMPLATE_COMPARISON_PROMPT.format(
        template_content=template_content,
        medical_record=medical_record
    )


# Example prompts for LLM initialization
EXAMPLE_COMPLETENESS_RESPONSE = """```json
{
  "dimension_score": 75,
  "issues": [
    {
      "dimension": "completeness",
      "severity": "m_major",
      "entity": "现病史",
      "description": "现病史中对主要症状的描述不够详细，未说明症状的演变过程和伴随症状",
      "suggestion": "补充症状的起始时间、发展过程、性质、缓解加重因素等"
    },
    {
      "dimension": "completeness",
      "severity": "m_minor",
      "entity": "既往史",
      "description": "过敏史记录不够详细，仅记录'有青霉素过敏'，未记录过敏表现",
      "suggestion": "补充过敏反应的具体表现，如皮疹、休克等"
    }
  ],
  "recommendations": [
    "按照病历书写规范，系统补充各部分缺失内容",
    "重点完善现病史的描述，体现症状的动态变化"
  ]
}```"""

EXAMPLE_LOGICALITY_RESPONSE = """```json
{
  "dimension_score": 80,
  "issues": [
    {
      "dimension": "logicality",
      "severity": "m_major",
      "entity": "诊断依据",
      "description": "诊断为'慢性支气管炎'，但病历中未列出相关的阳性体征和检查结果作为依据",
      "suggestion": "补充肺部听诊体征、胸部影像学检查结果等诊断依据"
    }
  ],
  "recommendations": [
    "确保每个诊断都有充分的临床依据支持",
    "按照'症状-检查-诊断'的逻辑链梳理病历内容"
  ]
}```"""

EXAMPLE_TIMELINESS_RESPONSE = """```json
{
  "dimension_score": 85,
  "issues": [
    {
      "dimension": "timeliness",
      "severity": "m_minor",
      "entity": "医嘱时间",
      "description": "医嘱时间记录不够精确，'当天'等模糊表述较多",
      "suggestion": "使用具体的时间点（如'2024-01-15 14:30'）代替模糊表述"
    }
  ],
  "recommendations": [
    "所有医疗操作和医嘱应记录具体时间点",
    "确保时间逻辑的严密性"
  ]
}```"""

EXAMPLE_NORMATIVITY_RESPONSE = """```json
{
  "dimension_score": 90,
  "issues": [
    {
      "dimension": "normativity",
      "severity": "m_minor",
      "entity": "术语使用",
      "description": "使用了非标准术语'心慌'，应使用'心悸'等规范医学术语",
      "suggestion": "统一使用规范医学术语，提高病历专业性"
    }
  ],
  "recommendations": [
    "学习并使用规范的医学术语",
    "注意标点符号和格式的规范性"
  ]
}```"""

EXAMPLE_COMPREHENSIVE_RESPONSE = """```json
{
  "dimension_scores": {
    "completeness": 78,
    "logicality": 82,
    "timeliness": 88,
    "normativity": 92
  },
  "overall_score": 85,
  "issues": [
    {
      "dimension": "completeness",
      "severity": "m_major",
      "entity": "现病史",
      "description": "现病史描述较为简略，缺少症状演变过程和诊疗经过的详细记录",
      "suggestion": "补充症状的发展变化过程，包括首次就诊时间、主要症状变化、已进行的检查和治疗"
    },
    {
      "dimension": "logicality",
      "severity": "m_minor",
      "entity": "诊断与治疗",
      "description": "治疗方案与初步诊断之间缺乏详细的推理说明",
      "suggestion": "添加诊断依据的分析说明，解释为何选择当前治疗方案"
    }
  ],
  "recommendations": [
    "完善现病史书写，体现病情发展脉络",
    "加强诊断与治疗之间的逻辑连贯性",
    "建议在书写时'先列事实，再做推断'的思维模式"
  ],
  "summary": "该病历整体质量良好，基本要素齐全，书写较为规范。主要改进方向是加强现病史的详细描述和诊断治疗之间的逻辑阐述。建议重点完善症状演变过程和诊疗经过的记录。"
}```"""


def get_all_prompts() -> Dict[str, str]:
    """Get all prompt templates"""
    return {
        "completeness": COMPLETENESS_PROMPT,
        "logicality": LOGICALITY_PROMPT,
        "timeliness": TIMELINESS_PROMPT,
        "normativity": NORMATIVITY_PROMPT,
        "comprehensive": COMPREHENSIVE_PROMPT,
        "template_comparison": TEMPLATE_COMPARISON_PROMPT,
    }

# Medical Record Inspector

让病历自我审查的质控工具

![Buy Me a Coffee](buymeacoffee.png)

## 简介

Medical Record Inspector 是一个基于 LLM 的病历质量质控工具。它通过将高质量病历作为"检查者"，使用 LLM 对比新病历与标准病历的偏离程度，发现传统规则检查之外的缺陷。

### 核心功能

- **智能质控**：使用 LLM 进行病历质量评估，超越传统规则检查
- **多维度评估**：完整性、逻辑一致性、及时性、规范性
- **可解释报告**：生成包含具体问题和建议的详细报告
- **批量处理**：支持批量处理多个病历文件
- **API 服务**：提供 REST API 便于集成
- **CLI 工具**：命令行接口方便自动化

### 评估维度

| 维度 | 说明 |
|------|------|
| Completeness | 病历字段完整性检查 |
| Consistency | 逻辑一致性检查（如诊断与用药是否匹配） |
| Timeliness | 及时性检查（如检查项目是否及时开具） |
| Standardization | 规范性检查（如术语、格式） |

## 快速开始

### 环境要求

- Python 3.9+
- Anthropi API Key

### 安装

```bash
cd medical-record-inspector

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置 API 密钥
cp .env.example .env
# 编辑 .env，填入你的 Anthropi API Key
```

### 使用

#### 启动 API 服务

```bash
python -m uvicorn api.main:app --reload --port 8000
```

访问 `http://localhost:8000/docs` 查看 API 文档。

#### CLI 使用

```bash
# 检查单个病历文件
python -m cli quality_check <file>

# 批量检查
python -m cli check-batch <directory>

# 列出标准模板
python -m cli list-standards
```

## 项目结构

```
medical-record-inspector/
├── api/                  # FastAPI 服务
│   ├── main.py          # API 入口
│   ├── models.py        # Pydantic 数据模型
│   ├── evaluator.py     # 质控评估器
│   ├── batch_engine.py  # 批量处理引擎
│   ├── exporter.py      # 报告导出
│   ├── config.py        # 配置管理
│   └── logger.py        # 日志系统
├── cli/                  # 命令行工具
│   ├── __main__.py
│   └── quality_check.py
├── data/                 # 数据文件
│   ├── standard_cases/  # 标准病历模板
│   ├── test_cases/      # 测试用例
│   └── examples/        # 示例数据
├── templates/            # LLM prompt 模板
├── generators/           # 测试用例生成器
├── tests/                # 单元测试
├── docs/                 # 文档
├── logs/                 # 日志文件
├── requirements.txt
├── .env.example
├── config.yaml.example
└── README.md
```

## API 接口

### 健康检查

```
GET /api/health
```

### 质控评估

```
POST /api/v1/assess
```

请求体：
```json
{
  "case": {
    "patient_id": "PAT001",
    "visit_id": "VIS001",
    "department": "内科",
    "case_type": "门诊",
    "main_complaint": "咳嗽3天",
    "present_illness": "患者3天前受凉后出现咳嗽...",
    "past_history": "无特殊...",
    "physical_exam": "双肺呼吸音粗...",
    "auxiliary_exams": "血常规正常...",
    "diagnosis": "急性支气管炎",
    "prescription": "阿莫西林 0.5g tid"
  }
}
```

响应：
```json
{
  "assessment": {
    "completeness_score": 9.5,
    "consistency_score": 9.0,
    "timeliness_score": 8.5,
    "standardization_score": 9.2,
    "overall_score": 9.0,
    "issues": []
  },
  "report": "..."
}
```

## 配置

### 环境变量

```bash
ANTHROPIC_API_KEY=your_api_key_here
MODEL_NAME=claude-3-5-sonnet-20240620
LOG_LEVEL=INFO
```

### 配置文件

```yaml
# config.yaml
evaluation:
  dimensions:
    completeness:
      weight: 0.25
      threshold: 7.0
    consistency:
      weight: 0.25
      threshold: 7.0
    timeliness:
      weight: 0.25
      threshold: 7.0
    standardization:
      weight: 0.25
      threshold: 7.0
```

## 开发

```bash
# 运行测试
pytest -v

# 运行 lint
ruff check .

# 格式化
ruff format .
```

## Docker 部署

```bash
docker build -t medical-record-inspector .
docker run -p 8000:8000 --env-file .env medical-record-inspector
```

## 支持作者

如果您觉得这个项目对您有帮助，欢迎打赏支持！

![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| 币种 | 地址 |
|------|------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |

## 许可证

MIT License

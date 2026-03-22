# Medical Record Inspector

让病历"审查"其他病历的质控工具

---

## 简介

**Medical Record Inspector** 是一个创新的电子病历质控工具，将电子病历视为"检查者"而非"被检查对象"。

传统质控系统使用预定义规则检查病历（如缺项、逻辑矛盾），但有些缺陷 "没有明确错误但感觉不对"。本工具通过**样本对比**的方式，用高质量病历作为模板，检测新病历的偏离程度，发现传统规则检查的盲区。

### 核心特性

- **样本对比**：将高质量病历作为模板，检测新病历的偏离
- **段落级定位**：精确定位病历中与模板差异最大的部分
- **LLM 解释**：使用大语言模型生成可解释的缺陷报告
- **混合模式**：支持规则检查 + 样本对比的混合模式
- **命令行工具**：单个病历检测或批量处理
- **Web API**：RESTful API 服务，易于集成

### 项目结构

```
medical-record-inspector/
├── src/              # 源代码
│   ├── extractor.py      # 文本提取模块
│   ├── template_loader.py  # 模板加载模块
│   ├── embedder.py       # 文本嵌入模块
│   ├── similarity.py     # 相似度计算模块
│   ├── anomaly_detector.py # 异常检测模块
│   ├── locator.py        # 缺陷定位模块
│   ├── explainer.py      # LLM解释模块
│   ├── inspector.py      # 核心检测引擎
│   ├── cli.py            # 命令行工具
│   ├── api.py            # Web API 服务
│   ├── visualizer.py     # 结果可视化模块
│   ├── hybrid_checker.py # 混合模式模块
│   ├── template_manager.py # 模板管理模块
│   ├── batch_processor.py  # 批处理模块
│   ├── feedback.py       # 用户反馈模块
│   ├── config.py         # 配置管理
│   └── logger.py         # 日志系统
├── tests/            # 测试文件
├── docs/             # 用户文档
├── templates/        # 优质病历模板
├── data/             # 示例数据和反馈
│   └── samples/      # 示例病历
├── requirements.txt  # Python 依赖
├── setup.py          # 打包配置
├── README.md         # 本文档
├── README_EN.md      # 英文版文档（自动生成）
└── buymeacoffee.png  # 打赏二维码
```

---

## 快速开始

### 环境要求

- Python 3.9+
- pip 包管理器

### 安装

```bash
cd medical-record-inspector
pip install -r requirements.txt
```

### 使用

#### 1. 命令行工具

```bash
# 检测单个病历
python -m src.cli single path/to/record.txt

# 批量检测文件夹
python -m src.cli batch path/to(records/folder)

# 使用 API 模式
python -m src.api --port 8000
```

#### 2. Web API 服务

```bash
# 启动 API 服务
python -m src.api --port 8000

# 测试 API
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "病历文本..."}'
```

---

## 配置

配置文件位于 `config.yaml`，示例：

```yaml
# 相似度阈值 (0-1)，低于此值的病历标记为异常
similarity_threshold: 0.7

# 异常检测灵敏度
anomaly_sensitivity: 0.95

# LLM 配置
llm:
  model: gpt-4
  api_base: https://api.openai.com/v1
  # api_key: your_key_here  # 从环境变量读取

# 模板库路径
template_dir: templates/
```

---

## 模板制作

创建优质病历模板放在 `templates/` 目录：

```
templates/
├── internal_medicine_example.txt  # 内科模板
├── surgery_example.txt            # 外科模板
└── pediatric_example.txt          # 儿科模板
```

模板应包含完整的标准病历结构：

- 患者基本信息
- 主诉
- 现病史
- 既往史
- 体格检查
- 辅助检查
- 诊断
- 诊疗经过
- 出院诊断

---

## 技术栈

| 模块 | 技术 |
|------|------|
| 文本处理 | Python, PyPDF2, python-docx |
| 嵌入向量 | sentence-transformers, BAAI-bge-micro-v2 |
| API 服务 | FastAPI, Uvicorn |
| 异常检测 | scikit-learn, Isolation Forest |
| LLM 调用 | openai SDK |

---

## 项目状态

- ✅ Phase 1: Exploration - 10 个奇怪问题，10 个创意项目
- ✅ Phase 1: Research - 技术可行性评估
- ✅ Phase 2: Project Selection - Medical Record Inspector
- ✅ Phase 3: Task Planning - 27 个任务
- 🔜 Phase 4: Self Review - 项目已准备好
- 🔜 Phase 5: Execution - 开始实现

---

## 相关项目

本项目是 **ChaosForge** 医疗信息化系列项目的一部分：

- **Malpractice Test Generator** - 生成故意有缺陷的模拟病历
- **Quality Care Simulator** - 用 LLM 生成完美病历示例
- **Medical Record Inspector** - 让病历自我审查（本项目）
- **medicare-audit-game** - 游戏化医保对账工具
- **重复上报扫描仪** - GRA上报效率检查工具

---

## 支持作者

如果您觉得这个项目对您有帮助，欢迎打赏支持！

![Buy me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| 币种 | 地址 |
|------|------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |

---

*最后更新: 2026-03-18*

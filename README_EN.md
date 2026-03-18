# Medical Record Inspector

A quality control tool that lets病历 "inspect" other病历

---

## Introduction

**Medical Record Inspector** is an innovative electronic medical record (EMR) quality control tool that treats EMRs as "inspectors" rather than "objects to be inspected."

Traditional QC systems use predefined rules to check records (e.g., missing items, logical contradictions), but some defects are "not clearly wrong but feel wrong." This tool detects deviations in new records by comparing them against high-quality templates, uncovering blind spots that rule-based checking misses.

### Core Features

- **Sample Comparison**: Uses high-quality medical records as templates to detect deviations in new records
- **Paragraph-Level Localization**: Precisely identifies the parts of a record that differ most from the template
- **LLM Explanation**: Uses large language models to generate interpretable defect reports
- **Hybrid Mode**: Supports hybrid mode combining rule-based checking and sample comparison
- **CLI Tool**: Single record inspection or batch processing
- **Web API**: RESTful API service for easy integration

### Project Structure

```
medical-record-inspector/
├── src/              # Source code
│   ├── extractor.py      # Text extraction module
│   ├── template_loader.py  # Template loading module
│   ├── embedder.py       # Text embedding module
│   ├── similarity.py     # Similarity calculation module
│   ├── anomaly_detector.py # Anomaly detection module
│   ├── locator.py        # Defect localization module
│   ├── explainer.py      # LLM explanation module
│   ├── inspector.py      # Core inspection engine
│   ├── cli.py            # Command-line tool
│   ├── api.py            # Web API service
│   ├── visualizer.py     # Result visualization module
│   ├── hybrid_checker.py # Hybrid mode module
│   ├── template_manager.py # Template management module
│   ├── batch_processor.py  # Batch processing module
│   ├── feedback.py       # User feedback module
│   ├── config.py         # Configuration management
│   └── logger.py         # Logging system
├── tests/            # Test files
├── docs/             # User documentation
├── templates/        # High-quality record templates
├── data/             # Example data and feedback
│   └── samples/      # Example records
├── requirements.txt  # Python dependencies
├── setup.py          # Packaging configuration
├── README.md         # This document
├── README_EN.md      # English version (auto-generated)
└── buymeacoffee.png  # Donation QR code
```

---

## Quick Start

### Requirements

- Python 3.9+
- pip package manager

### Installation

```bash
cd medical-record-inspector
pip install -r requirements.txt
```

### Usage

#### 1. Command-Line Tool

```bash
# Inspect a single record
python -m src.cli single path/to/record.txt

# Batch inspect a folder
python -m src.cli batch path/to(records/folder)

# Use API mode
python -m src.api --port 8000
```

#### 2. Web API Service

```bash
# Start API service
python -m src.api --port 8000

# Test the API
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Record text..."}'
```

---

## Configuration

Configuration file is located at `config.yaml`, example:

```yaml
# Similarity threshold (0-1), records below this value are flagged as anomalous
similarity_threshold: 0.7

# Anomaly detection sensitivity
anomaly_sensitivity: 0.95

# LLM configuration
llm:
  model: gpt-4
  api_base: https://api.openai.com/v1
  # api_key: your_key_here  # Read from environment variable

# Template library path
template_dir: templates/
```

---

## Template Creation

Create high-quality medical record templates in the `templates/` directory:

```
templates/
├── internal_medicine_example.txt  # Internal medicine template
├── surgery_example.txt            # Surgery template
└── pediatric_example.txt          # Pediatrics template
```

Templates should include complete standard EMR structures:

- Patient基本信息 (Basic patient information)
- 主诉 (Chief complaint)
- 现病史 (Present illness history)
- 既往史 (Past history)
- 体格检查 (Physical examination)
- 辅助检查 (Auxiliary examinations)
- 诊断 (Diagnosis)
- 诊疗经过 (Treatment process)
- 出院诊断 (Discharge diagnosis)

---

## Tech Stack

| Module | Technology |
|--------|------------|
| Text Processing | Python, PyPDF2, python-docx |
| Embeddings | sentence-transformers, BAAI-bge-micro-v2 |
| API Service | FastAPI, Uvicorn |
| Anomaly Detection | scikit-learn, Isolation Forest |
| LLM Calls | openai SDK |

---

## Project Status

- ✅ Phase 1: Exploration - 10 strange questions, 10 project ideas
- ✅ Phase 1: Research - Technical feasibility assessment
- ✅ Phase 2: Project Selection - Medical Record Inspector
- ✅ Phase 3: Task Planning - 27 tasks
- 🔜 Phase 4: Self Review - Project ready
- 🔜 Phase 5: Execution - Implementation starting

---

## Related Projects

This project is part of the **ChaosForge** medical information system series:

- **Malpractice Test Generator** - Generate intentionally flawed simulation records
- **Quality Care Simulator** - Use LLM to generate perfect record examples
- **Medical Record Inspector** - Let records self-inspect (this project)
- **medicare-audit-game** - Gamified medicare reconciliation tool
- **重复上报扫描仪** - GRA reporting efficiency checker

---

*Last updated: 2026-03-18*

---

## Support Author

If you find this project helpful, welcome to support me!

![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| Coin | Address |
|------|---------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |

# Medical Record Inspector

Let病历自我审查的质控工具 - A LLM-based medical record quality control tool

![Buy Me a Coffee](buymeacoffee.png)

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Assessment Dimensions](#assessment-dimensions)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Development](#development)
- [Docker Deployment](#docker-deployment)
- [Support the Author](#support-the-author)
- [License](#license)

## Introduction

Medical Record Inspector is a medical record quality control tool based on LLM (Large Language Model). It uses high-quality standard medical records as "inspectors" and compares new records with standard templates using LLM to identify defects beyond traditional rule-based checking.

### Core Features

- **Smart QC**: Uses LLM for medical record quality assessment, going beyond traditional rule-based checks
- **Multi-dimensional Evaluation**: Completeness, Consistency, Timeliness, Standardization
- **Explainable Reports**: Generates detailed reports with specific issues and recommendations
- **Batch Processing**: Supports batch processing of multiple medical record files
- **API Service**: REST API for easy integration
- **CLI Tool**: Command-line interface for automation

### Assessment Dimensions

| Dimension | Description |
|-----------|-------------|
| Completeness | Checks if all required fields are present and information is complete |
| Consistency | Checks logical consistency (e.g., diagnosis matches symptoms and treatment) |
| Timeliness | Checks if examinations are performed及时 and procedures follow correct order |
| Standardization | Checks if medical terminology and formatting are standardized |

## Quick Start

### Requirements

- Python 3.9+
- Anthropic API Key

### Installation

```bash
cd medical-record-inspector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and fill in your Anthropic API Key
```

### Usage

#### Start API Server

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` to view the API documentation.

#### CLI Usage

```bash
# Check single file
python -m cli quality_check <file>

# Batch checking
python -m cli check-batch <directory>

# List standard templates
python -m cli list-standards
```

## Project Structure

```
medical-record-inspector/
├── api/                  # FastAPI service
│   ├── main.py          # API entry point
│   ├── models.py        # Pydantic data models
│   ├── evaluator.py     # Quality evaluator
│   ├── batch_engine.py  # Batch processing engine
│   ├── exporter.py      # Report exporter
│   ├── config.py        # Configuration management
│   ├── config_loader.py # YAML configuration loader
│   ├── logger.py        # Logging system
│   └── cache.py         # Local cache system
├── cli/                  # Command-line tools
│   ├── __main__.py
│   └── quality_check.py
├── data/                 # Data files
│   ├── standard_cases/  # Standard case templates
│   ├── test_cases/      # Test cases
│   ├── examples/        # Example data
│   └── history/         # Evaluation history
├── templates/            # LLM prompt templates
├── generators/           # Test case generators
├── tests/                # Unit tests
├── docs/                 # Documentation
├── logs/                 # Log files
├── reports/              # Exported reports
├── requirements.txt
├── requirements.dev.txt
├── .env.example
├── config.yaml.example
└── README_EN.md
```

## API Documentation

The API is built with FastAPI and includes automatic interactive documentation.

### Endpoints

#### Health Check

```
GET /api/health
```

#### Quality Assessment

```
POST /api/v1/assess
```

Request Body:
```json
{
  "patient_id": "PAT001",
  "visit_id": "VIS001",
  "department": "Internal Medicine",
  "case_type": "Outpatient",
  "main_complaint": "Cough for 3 days",
  "present_illness": "Patient developed cough after cold exposure...",
  "past_history": "No significant past history...",
  "physical_exam": "Bilateral lung breath sounds clear...",
  "auxiliary_exams": "CBC normal...",
  "diagnosis": "Acute bronchitis",
  "prescription": "Amoxicillin 0.5g tid"
}
```

Response:
```json
{
  "success": true,
  "result": {
    "assessment_id": "ASSESS-...",
    "scores": {
      "completeness_score": 8.5,
      "consistency_score": 9.0,
      "timeliness_score": 8.0,
      "standardization_score": 8.5,
      "overall_score": 8.5
    },
    "issues": [],
    "report": "..."
  }
}
```

#### List Standard Cases

```
GET /api/v1/list-standards
```

### Interactive Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

### Environment Variables

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=your_api_key_here
MODEL_NAME=claude-3-5-sonnet-20240620
LOG_LEVEL=INFO

# Server Configuration
PORT=8000
HOST=0.0.0.0

# Cache Configuration
CACHE_EXPIRY_HOURS=24
```

### Configuration File

Create `config.yaml` from `config.yaml.example`:

```yaml
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

llm:
  model: "claude-3-5-sonnet-20240620"
  max_tokens: 4000
  temperature: 0.3
```

## Development

### Running Tests

```bash
pytest -v
```

### Code Quality

```bash
# Lint check
ruff check .

# Format code
ruff format .
```

### Adding Dependencies

Add new dependencies to `requirements.txt` or `requirements.dev.txt`.

## Docker Deployment

### Build Image

```bash
docker build -t medical-record-inspector .
```

### Run Container

```bash
docker run -p 8000:8000 --env-file .env medical-record-inspector
```

### docker-compose.yml Example

```yaml
version: '3.8'
services:
  medical-record-inspector:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

## Support the Author

If you find this project helpful, please consider supporting the author!

![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| Currency | Address |
|----------|---------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Troubleshooting

### Common Issues

**Issue**: `ANTHROPIC_API_KEY not found`

**Solution**: Create a `.env` file and set your API key:
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

**Issue**: Lazy import error for `LangSegment`

**Solution**: Ensure you're using a clean virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For more help, please check the [issues](https://github.com/your-username/medical-record-inspector/issues) page.

# Medical Record Inspector

A quality control tool that enables self-review of medical records

## Project Introduction

Medical Record Inspector is an innovative medical record quality control tool that treats high-quality medical records as the "inspector" rather than the "subject being inspected". It uses LLM to compare new medical records against standard templates, identifying defects beyond traditional rule-based checks.

### Core Features

- **Multi-dimensional Assessment**: Automatically evaluates completeness, logic, timeliness, and standardization of medical records
- **Explainable Reports**: Generates explainable quality reports with detailed issues and improvement suggestions
- **Intelligent Template Matching**: Supports high-quality medical record templates for comparative assessment
- **File Upload Support**: Supports DOCX and PDF file upload and parsing
- **Batch Assessment**: Supports batch file evaluation and result export
- **Multiple Export Formats**: Supports export in JSON, Markdown, and PDF formats

### Technical Architecture

- **Backend**: Python + FastAPI
- **Frontend**: TypeScript + React + Vite
- **LLM**: Supports OpenAI API and domestic large model APIs (Qwen, ERNIE Bot, etc.)

### Installation and Usage

See [INSTALLATION.md](INSTALLATION.md) and [USAGE.md](USAGE.md) for details.

### Assessment Dimensions

See [EVALUATION_DIMENSIONS.md](EVALUATION_DIMENSIONS.md) for details.

### Quick Start Example

#### 1. Start the Services

```bash
# Backend
cd src
uvicorn main:app --reload

# Frontend (new terminal window)
cd frontend
npm run dev
```

#### 2. Evaluate Medical Records

Visit `http://localhost:5173` and input or paste medical record content:

```
Chief Complaint: Headache for 3 days, accompanied by nausea and vomiting.
Current Illness History: The patient developed headache without obvious诱因 3 days ago, presenting as persistent dull pain...
Past Medical History: Denies history of hypertension and diabetes.
Physical Examination: Conscious, no obvious neurological abnormalities.
Preliminary Diagnosis: Migraine
```

Select assessment dimensions and click "Start Assessment" to view results.

#### 3. File Assessment

Supports DOCX and PDF file uploads with automatic text extraction for assessment.

#### 4. Batch Assessment

Select multiple files for batch evaluation, viewing assessment progress and results for each file.

## Screenshot Documentation

The project includes screenshots of key interfaces (stored in the `screenshots/` directory):

| Screenshot | Description |
|------------|-------------|
| `main-interface.png` | Main interface - input area and result display |
| `evaluation-result.png` | Assessment results - overall score, dimension scores, issue list, improvement suggestions |
| `file-upload.png` | File upload - supports DOCX and PDF file uploads |
| `batch-evaluation.png` | Batch assessment - multi-file assessment progress display |

### How to Add Screenshots

1. Start the project:
   ```bash
   # Backend (Terminal 1)
   cd src
   uvicorn main:app --reload

   # Frontend (Terminal 2)
   cd frontend
   npm run dev
   ```

2. Visit `http://localhost:5173` and use the various features

3. Capture the following key pages:
   - Main interface (input box + assessment results)
   - Assessment result details
   - File upload functionality
   - Batch assessment progress

4. Save screenshots to the `screenshots/` directory:
   ```
   medical-record-inspector/
   └── screenshots/
       ├── main-interface.png
       ├── evaluation-result.png
       ├── file-upload.png
       └── batch-evaluation.png
   ```

5. Update image paths in this section if needed

### Screenshot Requirements

- **Format**: PNG / JPG
- **Size**: Suggested width 800-1200 pixels
- **Clarity**: Maintain readable interface clarity
- **Naming**: Use English description with lowercase letters and hyphens

### Screenshot Content Details

| Screenshot | Key Content Displayed |
|------------|----------------------|
| Main Interface | Responsive layout, theme switching, input area |
| Assessment Results | Circular progress bar, bar chart, issue list, severity coloring |
| File Upload | DOCX/PDF support, file preview, progress status |
| Batch Assessment | Progress bar, completion/failure counts, list display |

### License

MIT License

---

## Support the Author

If you find this project helpful, welcome to support with a donation!

![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| Cryptocurrency | Address |
|----------------|---------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |

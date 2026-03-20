# Medical Record Inspector - INSTALLATIONGuide

# Medical Record Inspector - 安装指南

本指南介绍如何安装和配置 Medical Record Inspector。

## 环境要求

- Python 3.9 或更高版本
- pip 包管理器
- 2GB 可用内存（推荐 4GB+ 用于大型模型）

## 快速安装

```bash
# 克隆或下载项目
cd medical-record-inspector

# 安装依赖
pip install -r requirements.txt
```

## 详细安装步骤

### 1. 创建虚拟环境（推荐）

```bash
# Python 3.9+
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API key（可选）

如果要使用 LLM 解释功能，需要设置 API key：

```bash
export LLM_API_KEY="your_openai_api_key"
export LLM_MODEL="gpt-4"
export LLM_API_BASE="https://api.openai.com/v1"
```

Windows PowerShell:
```powershell
$env:LLM_API_KEY="your_openai_api_key"
$env:LLM_MODEL="gpt-4"
```

### 4. 准备模板

将高质量病历模板放入 `templates/` 目录：

```
templates/
├── internal_medicine.txt    # 内科模板
├── surgery.txt              # 外科模板
└── pediatric.txt            # 儿科模板
```

## 验证安装

```bash
# 运行测试
pytest tests/

# 或运行 CLI 工具（如果已配置模板）
python -m src.cli --help
```

## Docker 安装（可选）

如果已配置 Docker：

```bash
# 构建镜像
docker build -t medical-inspector .

# 运行容器
docker run -it --rm -v $(pwd)/templates:/app/templates medical-inspector
```

## 常见问题

### Q: 安装速度Transformers错误

**A**: 尝试更新 PyTorch：
```bash
pip install --upgrade torch
```

### Q: 系统内存不足

**A**: 使用更小的模型：
```bash
# 在 config.yaml 中设置
embedder:
  model: "sentence-transformers/all-MiniLM-L6-v2"
```

### Q: API key invalid

**A**: 确保 API key 正确，并检查 API base URL：
```bash
export LLM_API_BASE="https://api.openai.com/v1"
```

## 卸载

```bash
pip uninstall medical-record-inspector
```

---

*最后更新: 2026-03-18*

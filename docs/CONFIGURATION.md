# Medical Record Inspector - 配置说明

## 目录

- [配置文件位置](#配置文件位置)
- [配置项说明](#配置项说明)
- [环境变量](#环境变量)
- [示例配置](#示例配置)

---

## 配置文件位置

默认配置文件路径：
```
medical-record-inspector/
├── config.yaml          # 主配置文件（运行时生成）
└── config.example.yaml  # 示例配置文件
```

## 配置项说明

### 相似度配置

```yaml
similarity:
  threshold: 0.70  # 相似度阈值（0-1）
  min_paragraph_length: 10  # 最小段落长度
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| threshold | float | 0.70 | 相似度阈值，低于此值视为缺陷 |
| min_paragraph_length | int | 10 | 最小段落长度（字符数） |

### 异常检测配置

```yaml
anomaly_detection:
  enabled: true  # 是否启用异常检测
  sensitivity: 0.5  # 灵敏度（0-1）
  contamination: 0.1  # 异常比例预估
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| enabled | boolean | true | 是否启用异常检测 |
| sensitivity | float | 0.5 | 异常检测灵敏度 |
| contamination | float | 0.1 | 预估异常样本比例 |

### 模型配置

```yaml
models:
  embedder:
    name: multi-qa-MiniLM-L6-cos-v1  # 嵌入模型名称
    device: cpu  # 设备：cpu 或 cuda
  llm:
    name: gpt-3.5-turbo  # LLM 模型名称
    api_base: https://api.openai.com/v1  # API 地址
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| embedder.name | string | multi-qa-MiniLM-L6-cos-v1 | 嵌入模型 |
| embedder.device | string | cpu | 设备（cuda 需 GPU） |
| llm.name | string | gpt-3.5-turbo | LLM 模型 |
| llm.api_base | string | https://api.openai.com/v1 | API 地址 |

### 混合模式配置

```yaml
hybrid:
  sample_weight: 0.6  # 样本对比权重
  rule_weight: 0.4  # 规则检查权重
```

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| sample_weight | float | 0.6 | 样本对比权重 |
| rule_weight | float | 0.4 | 规则检查权重 |

---

## 环境变量

环境变量优先级高于配置文件。

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `EMBEDDER_MODEL` | 嵌入模型名称 | `multi-qa-MiniLM-L6-cos-v1` |
| `EMBEDDER_DEVICE` | 嵌入模型设备 | `cpu` 或 `cuda` |
| `LLM_API_KEY` | LLM API 密钥 | `sk-xxx` |
| `LLM_API_BASE` | LLM API 地址 | `https://api.openai.com/v1` |
| `SIMILARITY_THRESHOLD` | 相似度阈值 | `0.70` |

---

## 示例配置

### 示例 1：通用配置

```yaml
# medical-record-inspector/config.yaml

# 相似度配置
similarity:
  threshold: 0.70
  min_paragraph_length: 10

# 异常检测配置
anomaly_detection:
  enabled: true
  sensitivity: 0.5
  contamination: 0.1

# 模型配置
models:
  embedder:
    name: multi-qa-MiniLM-L6-cos-v1
    device: cpu
  llm:
    name: gpt-3.5-turbo
    api_base: https://api.openai.com/v1

# 混合模式配置
hybrid:
  sample_weight: 0.6
  rule_weight: 0.4
```

### 示例 2：GPU 配置

```yaml
models:
  embedder:
    name: BAAI/bge-micro-v2
    device: cuda
```

**注意**：使用 GPU 需要：
1. 安装 CUDA 版本的 PyTorch
2. 设置 `device: cuda`

### 示例 3：高灵敏度配置（严格质控）

```yaml
similarity:
  threshold: 0.80

anomaly_detection:
  sensitivity: 0.7
```

### 示例 4：低灵敏度配置（宽松质控）

```yaml
similarity:
  threshold: 0.60

anomaly_detection:
  sensitivity: 0.3
```

---

## 修改配置

### 方法 1：修改 config.yaml

```bash
# 编辑配置文件
nano config.yaml

# 重新运行检测，配置会自动加载
```

### 方法 2：使用环境变量

```bash
# Linux/Mac
export SIMILARITY_THRESHOLD=0.80
export EMBEDDER_MODEL=BAAI/bge-micro-v2

# Windows PowerShell
$env:SIMILARITY_THRESHOLD = "0.80"
$env:EMBEDDER_MODEL = "BAAI/bge-micro-v2"
```

### 方法 3：通过 API 动态修改

使用 `/config` 端点动态修改配置（如实现）。

---

## 配置验证

运行检测时，系统会自动验证配置：

- 如果配置失效，使用默认值
- 如果配置类型错误，记录日志并使用默认值
- 如果模型不存在，记录错误日志

日志位置：`logs/app.log`

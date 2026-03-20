# Medical Record Inspector - 技术报告

## 项目概述

Medical Record Inspector 是一个基于大语言模型（LLM）的医疗记录质量控制系统。该项目使用高质量的标准病历作为"质检员"，通过 LLM 对比新病历与标准模板的偏离程度，发现传统规则检查之外的缺陷。

核心价值：
- **智能质控**：利用 LLM 的语义理解能力，检测逻辑不一致、诊断与症状不匹配等复杂问题
- **多维度评估**：完整性、一致性、及时性、规范性四个维度进行全面评估
- **可解释性**：生成包含具体问题和改进建议的详细报告
- **效率提升**：批量处理、本地缓存、性能优化大幅提高处理效率

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Medical Record Inspector                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐       ┌──────────────┐       ┌─────────────┐  │
│  │   API Layer  │──────▶│  Batch Layer │──────▶│   CLI Tool  │  │
│  │  (FastAPI)   │       │ (Concurrency)│       │  (argparse) │  │
│  └──────────────┘       └──────────────┘       └─────────────┘  │
│         │                       │                       │       │
│         ▼                       ▼                       ▼       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Quality Assessment Engine                  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │   │
│  │  │ Evaluation │ │ Validation │ │ History    │          │   │
│  │  │   Engine   │ │  Middleware│ │   Manager  │          │   │
│  │  └────────────┘ └────────────┘ └────────────┘          │   │
│  └─────────────────────────────────────────────────────────┘   │
│         │                       │                       │       │
│         ▼                       ▼                       ▼       │
│  ┌──────────────┐     ┌──────────────┐      ┌─────────────┐   │
│  │  LLM API     │     │   Local      │      │  Reporting  │   │
│  │ (Anthropic)  │     │   Cache      │      │  Exporter   │   │
│  └──────────────┘     └──────────────┘      └─────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心模块说明

#### 1. API Layer (`api/main.py`)
- **FastAPI 框架**：提供 RESTful API 服务
- **端点**：
  - `GET /api/health`：健康检查
  - `POST /api/v1/assess`：质量评估接口
  - `GET /api/v1/list-standards`：获取标准病历列表
- **中间件**：CORS、数据验证中间件

#### 2. Quality Evaluator (`api/evaluator.py` / `api/performance.py`)
- **QualityEvaluator**：基础评估器
  - `evaluate_completeness()`：完整性检查
  - `evaluate_consistency()`：逻辑一致性检查
  - `evaluate_timeliness()`：及时性检查
  - `evaluate_standardization()`：规范性检查
- **PerformanceEvaluator**：优化评估器
  - 请求重试机制（tenacity）
  - 超时控制（TimeoutClient）
  - Token 使用统计

#### 3. Validation Middleware (`api/middleware/validation.py`)
- **CaseDataValidator**：数据验证器
  - 必填字段验证
  - 字段长度验证
  - 字段格式验证（日期、数字）
  - 业务逻辑验证

#### 4. History Manager (`api/history.py`)
- **HistoryManager**：历史记录管理器
  - 保存评估结果到 JSON 文件
  - 按时间、评分、患者 ID 筛选
  - 导出为 JSON/CSV 格式
  - 生成统计数据

#### 5. Local Cache (`api/cache.py`)
- **LocalCache**：本地缓存系统
  - MD5 哈希键
  - 24 小时默认过期
  - 持久化存储在 `data/cache/`

#### 6. Batch Processing (`api/batch_engine.py` / `api/batch_optimizer.py`)
- **批量评估引擎**：多线程/异步并发处理
- **AsyncBatchEvaluator**：异步批量评估器
  - 使用 asyncio.gather 并发执行
  - 信号量控制并发度
  - 进度跟踪

---

## 技术决策记录

### 1. Python 作为主要语言
**决策**：选择 Python 3.9+ 作为主要开发语言
**原因**：
- FastAPI 提供高性能的异步 API 服务
- Pydantic 提供强大的数据验证能力
- 生态丰富（anthropic SDK、pytest 等）
- 适合数据处理和文本分析任务

### 2. FastAPI 作为 Web 框架
**决策**：使用 FastAPI 而非 Flask/Django
**原因**：
- 自动文档生成（Swagger UI, ReDoc）
- 原生异步支持
- 性能优异（与 Node.js/Go 相当）
- Pydantic 深度集成

### 3. Anthropic LLM API
**决策**：使用 Anthropic 的Claude 模型
**原因**：
- Model Quality：claude-3-5-sonnet 在医疗领域表现优异
- JSON Mode：确保结构化输出
- Cost-effectiveness：相对 GPT-4 成本更低

### 4. 文件存储而非数据库
**决策**：使用本地 JSON 文件而非 SQLite/PostgreSQL
**原因**：
- 简单性：减少部署复杂度
- 可移植性：项目可直接复制
- 适配性：评估结果数据量小，文件存储足够

### 5. 多维度评估设计
**决策**：采用四个独立维度进行评估
**原因**：
- 模块化设计便于扩展
- 每个维度可单独优化
- 便于生成可解释的评估报告

### 6. 中间件模式
**决策**：使用 FastAPI 中间件实现数据验证
**原因**：
- 与应用逻辑解耦
- 统一错误处理
- 易于测试和维护

---

## 性能测试结果

### 测试环境
- 模型：claude-3-5-sonnet-20240620
- 并发度：4
- 测试数量：10 个病历

### 测试结果（示例）

| 指标 | 结果 |
|------|------|
| 单次评估平均时间 | ~2.5 秒 |
| 批量评估总时间（10个） | ~8.5 秒 |
| 批量吞吐量 | ~1.2 个/秒 |
| Token 使用（单次） | ~3000 输入 + 500 输出 |
| API 调用成本（单次） | ~$0.015 |

### 性能优化措施

1. **请求重试**：指数退避策略，最多 3 次
2. **批量处理**：并发处理多个病历
3. **本地缓存**：避免重复 LLM 调用
4. ** Token 统计**：实时监控成本

---

## 配置说明

### 环境变量（`.env`）

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

# Performance Configuration
MAX_CONCURRENT=4
TIMEOUT=60
MAX_RETRIES=3
```

### YAML 配置（`config.yaml`）

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

---

## 部署方案

### 本地部署

```bash
# 克隆项目
git clone <repository>

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 配置 API 密钥
cp .env.example .env
# 编辑 .env 填入 API 密钥

# 启动服务
python -m uvicorn api.main:app --reload --port 8000
```

### Docker 部署

```bash
# 构建镜像
docker build -t medical-record-inspector .

# 运行容器
docker run -p 8000:8000 --env-file .env medical-record-inspector

# 或使用 docker-compose
docker-compose up -d
```

---

## 未来改进建议

### 短期改进（1-2 周）

1. **日志集成**：将评估日志集成到 logger.py
2. **Web UI**：简单的 HTML 前端用于文件上传和结果查看
3. **模板管理**：支持在线编辑和上传标准模板

### 中期改进（1-2 月）

1. **数据库支持**：引入 SQLite/PostgreSQL 支持
2. **用户系统**：添加用户认证和权限管理
3. **团队协作**：支持团队共享标准模板和评估结果

### 长期改进（3-6 月）

1. **模型微调**：在医疗质控数据上微调模型
2. **规则引擎**：结合 LLM 和传统规则引擎
3. **实时监控**：实时监控质控指标和趋势
4. **API 产品化**：添加更多企业级特性（限流、配额、账单）

---

## 总结

Medical Record Inspector 项目通过结合 LLM 技术和医疗质控领域知识，提供了一种创新的病历质控解决方案。项目设计遵循模块化原则，易于扩展和维护。目前项目已具备生产可用的基本功能，后续可根据实际需求继续完善。

**项目状态**：可发布 MVP
**技术栈**：Python 3.11+, FastAPI, Anthropic Claude, Pydantic v2
** license**：MIT License

# Medical Record Inspector API 文档

本文档介绍 Medical Record Inspector 的 API 接口使用方法。

## 快速开始

### 启动服务

```bash
cd medical-record-inspector
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
uvicorn api.main:app --reload --port 8000
```

### 访问 API

- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

## API 端点

### 健康检查

获取服务健康状态。

**端点**: `GET /api/health`

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-19T10:00:00",
  "version": "1.0.0"
}
```

### 质量评估

对病历进行质量评估。

**端点**: `POST /api/v1/assess`

**请求体**:
```json
{
  "patient_id": "PAT001",
  "visit_id": "VIS001",
  "department": "内科",
  "case_type": "门诊",
  "main_complaint": "咳嗽3天",
  "present_illness": "患者3天前受凉后出现咳嗽",
  "past_history": "无特殊",
  "physical_exam": "双肺呼吸音清",
  "auxiliary_exams": "血常规正常",
  "diagnosis": "急性支气管炎",
  "prescription": "阿莫西林 0.5g tid"
}
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "assessment_id": "ASSESS-20260319100000-abc123",
    "patient_id": "PAT001",
    "visit_id": "VIS001",
    "scores": {
      "completeness_score": 8.5,
      "consistency_score": 9.0,
      "timeliness_score": 8.0,
      "standardization_score": 8.5,
      "overall_score": 8.5
    },
    "issues": [],
    "report": "病历质量良好。",
    "标注时间": "2026-03-19T10:00:00"
  },
  "message": "评估完成"
}
```

### 获取标准病历列表

获取所有可用的标准病历模板。

**端点**: `GET /api/v1/list-standards`

**响应示例**:
```json
{
  "success": true,
  "standards": [
    {
      "template_id": "OUT-内科-20260319-001",
      "department": "内科",
      "case_type": "门诊",
      "main_complaint": "反复咳嗽、咳痰3年，加重1周",
      "present_illness": "患者3年前受凉后出现咳嗽...",
      "past_history": "高血压病史5年...",
      "physical_exam": "T 36.5℃...",
      "auxiliary_exams": "血常规：WBC 6.5×10^9/L...",
      "diagnosis": "慢性支气管炎急性发作期",
      "prescription": "1. 阿莫西林胶囊 0.5g 口服 tid × 7天"
    }
  ],
  "total": 9
}
```

## 评估维度说明

### 1. 完整性 (Completeness)
检查病历是否包含所有必要字段，信息是否完整。

- **评分标准**：
  - 9-10 分：所有字段完整，信息详尽
  - 7-8.9 分：基本完整，有少量 minor 缺失
  - 5-6.9 分：部分缺失，需要改进
  - <5 分：严重缺失

### 2. 逻辑一致性 (Consistency)
检查病历内部逻辑是否一致，诊断与症状、治疗方案是否匹配。

- **评分标准**：
  - 9-10 分：完全一致，逻辑严密
  - 7-8.9 分：基本一致，有少量矛盾
  - 5-6.9 分：存在明显矛盾
  - <5 分：严重不一致

### 3. 及时性 (Timeliness)
检查检查项目的时间顺序是否合理。

- **评分标准**：
  - 9-10 分：检查及时，顺序合理
  - 7-8.9 分：基本及时
  - 5-6.9 分：存在处理延迟
  - <5 分：严重延迟

### 4. 规范性 (Standardization)
检查病历书写是否规范，是否使用标准医学术语。

- **评分标准**：
  - 9-10 分：完全规范
  - 7-8.9 分：基本规范
  - 5-6.9 分：存在不规范之处
  - <5 分：严重不规范

## 错误响应

**400 Bad Request** - 请求参数错误
```json
{
  "detail": "缺少必要的字段: department"
}
```

**500 Internal Server Error** - 服务器错误
```json
{
  "detail": "评估失败：ANTHROPIC_API_KEY 未设置"
}
```

## 使用示例

### Python 客户端

```python
import requests

# 配置
API_URL = "http://localhost:8000"
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 评估病历
def assess_case(case_data):
    response = requests.post(
        f"{API_URL}/api/v1/assess",
        json=case_data
    )
    return response.json()

# 示例病历
case = {
    "patient_id": "PAT001",
    "visit_id": "VIS001",
    "department": "内科",
    "case_type": "门诊",
    "main_complaint": "咳嗽3天",
    "present_illness": "患者3天前受凉后出现咳嗽",
    "past_history": "无特殊",
    "physical_exam": "双肺呼吸音清",
    "auxiliary_exams": "血常规正常",
    "diagnosis": "急性支气管炎",
    "prescription": "阿莫西林 0.5g tid"
}

# 调用评估
result = assess_case(case)
print(f"总体评分: {result['result']['scores']['overall_score']}")
```

### cURL 示例

```bash
curl -X POST http://localhost:8000/api/v1/assess \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT001",
    "visit_id": "VIS001",
    "department": "内科",
    "case_type": "门诊",
    "main_complaint": "咳嗽3天",
    "present_illness": "患者3天前受凉后出现咳嗽",
    "past_history": "无特殊",
    "physical_exam": "双肺呼吸音清",
    "auxiliary_exams": "血常规正常",
    "diagnosis": "急性支气管炎",
    "prescription": "阿莫西林 0.5g tid"
  }'
```

## Rate Limiting

当前版本暂无速率限制。

## 许可证

MIT License

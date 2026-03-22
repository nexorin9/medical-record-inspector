# 使用说明

## 快速开始

### 1. 文本评估

1. 打开浏览器访问 `http://localhost:5173`
2. 在病历文本框中输入或粘贴病历内容
3. 选择需要评估的维度（完整性、逻辑性、及时性、规范性）
4. 点击"开始评估"按钮
5. 等待评估完成，查看结果

### 2. 文件上传评估

1. 点击"选择文件"按钮
2. 选择 DOCX 或 PDF 格式的病历文件
3. 文件内容会自动提取并填充到文本框
4. 选择评估维度
5. 点击"开始评估"

### 3. 批量评估

1. 点击"选择文件"按钮，按住 Ctrl/Shift 选择多个文件
2. 文件内容会自动提取
3. 选择评估维度
4. 点击"开始批量评估"
5. 查看每个文件的评估进度和结果

### 4. 结果导出

评估完成后，可以导出结果：

- **复制报告**: 点击"拷贝报告"按钮，将结果复制到剪贴板
- **下载 JSON**: 访问 `http://localhost:8000/api/v1/evaluator/export/json?evaluation_result={...}`
- **下载 Markdown**: 访问 `http://localhost:8000/api/v1/evaluator/export/md?evaluation_result={...}`
- **下载 PDF**: 访问 `http://localhost:8000/api/v1/evaluator/export/pdf?evaluation_result={...}`

## 评估维度说明

### 完整性 (Completeness)

检查病历是否包含基本要素：

| 检查项 | 说明 |
|--------|------|
| 主诉 | 患者本次就诊的主要症状 |
| 现病史 | 现在患病的情况，包括起病情况、症状特点等 |
| 既往史 | 以往的疾病史、手术史、外伤史等 |
| 个人史 | 生活习惯、职业、居住地等 |
| 婚育史 | 婚姻状况、生育情况 |
| 家族史 | 家族遗传病史 |

### 逻辑性 (Logicality)

检查病历内容的逻辑连贯性：

| 检查项 | 说明 |
|--------|------|
| 症状-体征一致性 | 症状描述与体检发现是否吻合 |
| 检查-诊断逻辑 | 辅助检查结果是否支持诊断 |
| 治疗-诊断匹配 | 治疗措施是否针对诊断 |
| 时间逻辑 | 病程发展是否符合医学规律 |

### 及时性 (Timeliness)

检查病历记录的及时性：

| 检查项 | 说明 |
|--------|------|
| 首次病程记录 | 是否在患者入院后规定时间内完成 |
| 医嘱执行时间 | 医嘱是否及时执行并记录 |
| 检查记录 | 检查申请和结果记录是否及时 |
| 手术记录 | 手术记录是否及时完成 |

### 规范性 (Normativity)

检查病历书写的规范性：

| 检查项 | 说明 |
|--------|------|
| 格式规范 | 是否符合病历书写基本规范 |
| 术语使用 | 是否使用标准医学术语 |
| 签名完整 | 是否有医生签名和时间 |
| 修改规范 | 修改是否规范（双线划线、签名） |

## API 使用

### 评估病历

```bash
curl -X POST http://localhost:8000/api/v1/evaluator \
  -H "Content-Type: application/json" \
  -d '{
    "content": "患者主诉：头痛三天...",
    "evaluation_dims": ["completeness", "logicality"]
  }'
```

### 批量评估

```bash
curl -X POST http://localhost:8000/api/v1/evaluator/batch \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"filename": "file1.docx", "content": "..."},
      {"filename": "file2.docx", "content": "..."}
    ],
    "evaluation_dims": ["completeness", "logicality"]
  }'
```

### 获取评估状态

```bash
curl http://localhost:8000/api/v1/evaluator/batch/{batch_id}
```

## 高级配置

### 自定义评估权重

修改 `src/evaluator/evaluator.py` 中的 `weight_map`：

```python
weight_map = {
    "completeness": 0.4,    # 完整性权重 40%
    "logicality": 0.3,      # 逻辑性权重 30%
    "timeliness": 0.2,      # 及时性权重 20%
    "normativity": 0.1,     # 规范性权重 10%
}
```

### 模板对比评估

1. 上传高质量病历模板到 `data/templates.json`
2. 在评估请求中指定 `template_id`
3. 系统会自动对比并生成差距分析

## 错误处理

### 请求频繁（HTTP 429）

系统使用限流策略，请稍后再试。

### 文件解析失败

- 检查文件格式是否为 DOCX 或 PDF
- 检查文件大小是否小于 10MB
- 检查文件是否损坏

### LLM 调用失败

- 检查 API 密钥是否有效
- 检查 API 额度是否充足
- 检查网络连接

## 支持

- 问题反馈: GitHub Issues
- 文档更新: 查看项目 README
- 更新日志: 查看 CHANGELOG.md

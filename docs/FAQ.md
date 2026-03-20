# Medical Record Inspector - 常见问题

## 目录

- [安装相关](#安装相关)
- [使用相关](#使用相关)
- [性能相关](#性能相关)
- [技术相关](#技术相关)

---

## 安装相关

### Q1: 安装依赖时报错 "failed to build wheel for xxx"

**问题原因**：可能是网络问题或依赖版本冲突

**解决方案**：

```bash
# 使用国内镜像源安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用 conda 安装
conda install pytorch -c pytorch
conda install -c conda-forge sentence-transformers
```

---

### Q2: 安装 PyTorch 失败

**问题原因**：PyTorch 需要 CUDA 驱动支持

**解决方案**：

```bash
# CPU 版本 PyTorch（无需 GPU）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 或使用 CPU 版本（推荐）
pip install torch torchvision torchaudio
```

---

## 使用相关

### Q3: 检测速度很慢怎么办？

**原因和解决方案**：

| 原因 | 解决方案 |
|------|----------|
| 首次加载模型 | 冷启动需要 15-30 秒，后续检测很快 |
| 模型较大 | 使用轻量级模型 `BAAI/bge-micro-v2` |
| 批量检测 | 使用 `batch` 模式而非多次 `single` |
| CPU 运行 | 使用 GPU（设置 `device: cuda`） |

**优化建议**：

1. 启动服务后保持运行（避免重复加载）
2. 使用批量检测功能
3. 根据需求选择模型（速度快的 vs 准确率高的）

---

### Q4: 相似度分数总是很低

**可能原因**：

1. **模板不匹配**：使用了错误类型的模板
   - 解决：使用与病历类型匹配的模板

2. **病历内容不完整**：缺失重要内容
   - 解决：检查病历是否包含必需字段

3. **段落切分问题**：文本过长或过短
   - 解决：调整 `min_paragraph_length` 配置

**诊断方法**：

```bash
# 查看详细报告
python -m src.cli --templates templates/ single case.txt --format json
```

---

### Q5: 如何自定义相似度阈值？

**方法 1：命令行参数**

```bash
python -m src.cli --templates templates/ single case.txt --threshold 0.80
```

**方法 2：修改配置文件**

```yaml
# config.yaml
similarity:
  threshold: 0.80
```

**方法 3：环境变量**

```bash
export SIMILARITY_THRESHOLD=0.80
```

---

## 性能相关

### Q6: 内存占用太高怎么办？

**解决方案**：

1. **使用 CPU 模式**

```yaml
models:
  embedder:
    device: cpu
```

2. **使用轻量级模型**

```yaml
models:
  embedder:
    name: BAAI/bge-micro-v2  # 参数量更小
```

3. **减少批量大小**

```python
# 在 embed_batch 中设置更小的 batch_size
embeddings = embedder.embed_batch(texts, batch_size=8)
```

---

### Q7: 如何提高检测准确率？

**建议**：

1. **使用高质量模板**
   - 使用专科模板而非通用模板
   - 模板内容详实、结构完整

2. **调整相似度阈值**
   - 严格质控：`threshold: 0.80`
   - 宽松质控：`threshold: 0.60`

3. **启用异常检测**
   - 使用 Isolation Forest 算法检测异常样本

---

## 技术相关

### Q8: 支持哪些病历格式？

**支持的格式**：

| 格式 | 说明 |
|------|------|
| TXT | 纯文本格式（推荐） |
| PDF | PDF 文档（需安装 PyPDF2） |
| DOCX | Word 文档（需安装 python-docx） |

**推荐格式**：TXT（解析简单、宽容度高）

---

### Q9: 如何添加自定义质控规则？

**规则定义格式**：

```python
# 在 src/hybrid_checker.py 中添加

def _init_rules(self):
    self.rules = [
        Rule(
            id="R007",
            name="药物剂量规范",
            check_func=self._check_dosage,
            severity="medium"
        ),
        # ...
    ]
```

**规则类型**：

- **high**：严重缺陷，必须修复
- **medium**：中等缺陷，建议修复
- **low**：轻微缺陷，可容忍

---

### Q10: 如何查看详细的缺陷报告？

**方法 1：JSON 格式输出**

```bash
python -m src.cli --templates templates/ single case.txt --format json -o report.json
```

**方法 2：使用 HTML 报告**

```python
from src.visualizer import HTMLReportGenerator

generator = HTMLReportGenerator()
generator.generate_html_report(report_data, "output.html")
```

**方法 3：查看日志**

```bash
# 查看详细日志
tail -f logs/app.log
```

---

## 其他问题

### 如何贡献模板？

欢迎提交优质病历模板！

**模板要求**：

1. 内容完整，符合诊疗规范
2. 结构清晰，使用统一格式
3. 无患者隐私信息（需脱敏）

**提交方式**：

1. 创建 Pull Request
2. 或发送邮件至项目维护者

---

### 如何联系支持？

- GitHub Issues: [项目地址]
- 邮件: support@medical-inspector.com
- Telegram: [@MedicalInspector](https://t.me/MedicalInspector)

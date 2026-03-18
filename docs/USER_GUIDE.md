# Medical Record Inspector - 用户指南

## 目录

- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [使用方法](#使用方法)
- [输出说明](#输出说明)
- [最佳实践](#最佳实践)

---

## 快速开始

### 第一步：准备数据

将待检测的病历文件放入 `data/samples/normal/` 目录，或将病历文本保存为 TXT 文件。

### 第二步：运行检测

#### 方法 1：使用命令行工具（推荐）

```bash
# 单个病历检测
python -m src.cli --templates templates/ single data/samples/normal/case_001.txt

# 批量检测
python -m src.cli --templates templates/ batch data/samples/normal/

# 输出 JSON 格式
python -m src.cli --templates templates/ single case.txt --format json
```

#### 方法 2：使用 Web API

启动服务：

```bash
python -m src.api
```

然后访问 http://localhost:8000/docs 查看 API 文档。

### 第三步：查看结果

检测结果会显示：
- 总体相似度分数（0-1）
- 质量等级（优秀/合格/需要改进）
- 风险等级（低/中/高）
- 缺陷列表（按严重程度排序）

---

## 核心功能

### 1. 相似度对比

系统使用 sentence-transformers 模型将病历转换为向量，通过余弦相似度计算与模板的相似程度。

**相似度分数说明：**

| 分数范围 | 等级 | 说明 |
|---------|------|------|
| 0.85-1.0 | 优秀 | 与模板高度相似，病历规范 |
| 0.70-0.84 | 合格 | 基本规范，可能有少量缺陷 |
| 0.60-0.69 | 需要改进 | 存在明显缺陷 |
| < 0.60 | 不合格 | 严重偏离标准，需重点关注 |

### 2. 规则检查

系统内置 6 条质控规则：

| 规则 ID | 规则名称 | 检查内容 |
|---------|---------|----------|
| R001 | 基本信息完整 | 姓名、性别、年龄、主诉 |
| R002 | 主诉规范 | 简明扼要，包含症状和时间 |
| R003 | 现病史完整 | 起病诱因、症状特点、诊疗经过 |
| R004 | 诊疗经过 | 检查、诊断、治疗措施 |
| R005 | 诊断规范 | 使用标准医学术语 |
| R006 | 出院诊断 | 与入院诊断对比，注明变化 |

### 3. 混合模式

系统默认使用混合模式，结合：
- **样本对比（权重 0.6）**：与优质模板对比相似度
- **规则检查（权重 0.4）**：检查必需字段和结构

---

## 使用方法

### 单个病历检测

```bash
python -m src.cli --templates templates/ single /path/to/patient.txt
```

可选参数：
- `--format json` - 输出 JSON 格式
- `-o output.json` - 输出到文件
- `--threshold 0.7` - 自定义相似度阈值

### 批量检测

```bash
python -m src.cli --templates templates/ batch /path/to/folder/
```

批量检测会：
- 自动扫描目录下所有 TXT 文件
- 逐个进行检测
- 汇总统计结果
- 显示处理进度

### 列出可用模板

```bash
python -m src.cli --templates templates/ list-templates
```

---

## 输出说明

### 命令行输出

```
=== 病历检测报告 ===

文件：case_001.txt

总体相似度：0.782（合格）
质量等级：合格
风险等级：中

缺陷数：4 个

[高风险] 段落 3 - 相似度 0.52
  缺失家族史详细信息

[中风险] 段落 5 - 相似度 0.61
  体格检查内容不够完整
```

### JSON 格式输出

```json
{
  "file": "case_001.txt",
  "overall_similarity": 0.782,
  "quality_level": "合格",
  "risk_level": "中",
  "defect_count": 4,
  "template_used": "general_template",
  "defects": [
    {
      "type": "paragraph",
      "index": 3,
      "similarity": 0.52,
      "content": "缺失家族史详细信息",
      "severity": "high"
    }
  ]
}
```

---

## 最佳实践

### 1. 模板选择

- **通用模板**：适用于初诊、入院记录
- **专科模板**：适用于特定科室（如心内科、神经内科）
- **急诊模板**：适用于急诊病历

### 2. 质量改进建议

- **相似度低**：检查是否缺失模块（如家族史、既往史）
- **段落相似度低**：检查对应段落的内容完整性
- **规则检查失败**：按规则提示补充缺失字段

### 3. 批量处理

- 将待检测病历放入统一目录
- 使用 batch 模式批量检测
- 导出 JSON 结果便于后续分析

### 4. 自定义模板

参考《模板制作指南》创建符合医院规范的模板。

---

## 常见问题

见 [FAQ.md](./FAQ.md)

---

## 技术支持

如有问题，请查看：
- [安装指南](./INSTALLATION.md)
- [配置说明](./CONFIGURATION.md)
- [模板制作指南](./TEMPLATE_GUIDE.md)

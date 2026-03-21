# Medical Record Inspector

让病历自我审查的质控工具

## 项目介绍

Medical Record Inspector 是一个创新的病历质控工具，它将高质量病历作为"检查者"而非"被检查对象"，通过 LLM 对比新病历与标准病历的偏离程度，发现传统规则检查之外的缺陷。

### 核心特性

- **多维度评估**：自动评估病历的完整性、逻辑性、及时性、规范性等维度
- **可解释报告**：生成包含问题详情和改进建议的可解释质量报告
- **智能模板匹配**：支持高质量病历模板，用于对比评估
- **文件上传支持**：支持 DOCX、PDF 文件上传和解析
- **批量评估**：支持批量文件评估和结果导出
- **多种导出格式**：支持 JSON、Markdown、PDF 格式导出

### 技术架构

- **后端**：Python + FastAPI
- **前端**：TypeScript + React + Vite
- **LLM**：支持 OpenAI API、国产大模型 API（通义千问、文心一言等）

### 安装和使用

详见 [INSTALLATION.md](INSTALLATION.md) 和 [USAGE.md](USAGE.md)。

### 评估维度

详见 [EVALUATION_DIMENSIONS.md](EVALUATION_DIMENSIONS.md)。

### 快速开始示例

#### 1. 启动服务

```bash
# 后端
cd src
uvicorn main:app --reload

# 前端（新终端窗口）
cd frontend
npm run dev
```

#### 2. 评估病历

访问 `http://localhost:5173`，输入或粘贴病历内容：

```
患者主诉：头痛三天，伴有恶心呕吐。
现病史：患者三天前无明显诱因出现头痛，呈持续性胀痛...
既往史：否认高血压、糖尿病史。
体格检查：神志清楚，神经系统未见明显异常。
初步诊断：偏头痛
```

选择评估维度，点击"开始评估"查看结果。

#### 3. 文件评估

支持 DOCX、PDF 文件上传，自动提取文本内容进行评估。

#### 4. 批量评估

选择多个文件进行批量评估，查看每个文件的评估进度和结果。

## 截图说明

项目包含以下关键界面的截图（存放在 `screenshots/` 目录）：

| 截图 | 说明 |
|------|------|
| `main-interface.png` | 主界面 - 输入区域和结果展示 |
| `evaluation-result.png` | 评估结果 - 总体评分、维度分数、问题列表、改进建议 |
| `file-upload.png` | 文件上传 - 支持 DOCX 和 PDF 文件上传 |
| `batch-evaluation.png` | 批量评估 - 多文件评估进度显示 |

### 如何添加截图

1. 启动项目：
   ```bash
   # 后端（终端 1）
   cd src
   uvicorn main:app --reload

   # 前端（终端 2）
   cd frontend
   npm run dev
   ```

2. 访问 `http://localhost:5173` 并使用各功能

3. 截取以下关键页面：
   - 主界面（输入框 + 评估结果）
   - 评估结果详情
   - 文件上传功能
   - 批量评估进度

4. 将截图保存到 `screenshots/` 目录：
   ```
   medical-record-inspector/
   └── screenshots/
       ├── main-interface.png
       ├── evaluation-result.png
       ├── file-upload.png
       └── batch-evaluation.png
   ```

5. 更新本节图片路径（如果需要）

### 截图要求

- **格式**: PNG / JPG
- **大小**: 建议宽度 800-1200 像素
- **清晰度**: 保持界面清晰可读
- **命名**: 使用英文描述，小写加连字符

### 截图内容说明

| 截图 | 关键展示内容 |
|------|--------------|
| 主界面 | 响应式布局、主题切换、输入区域 |
| 评估结果 | 环形进度条、条形图、问题列表、严重程度着色 |
| 文件上传 | DOCX/PDF 支持、文件预览、进度状态 |
| 批量评估 | 进度条、完成/失败计数、列表展示 |

### 开源协议

MIT License

---

## 支持作者

如果您觉得这个项目对您有帮助，欢迎打赏支持！

![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| 币种 | 地址 |
|------|------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |

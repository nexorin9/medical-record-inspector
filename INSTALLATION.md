# 安装说明

## 系统要求

- **Python**: 3.8 或更高版本
- **Node.js**: 18 或更高版本（用于前端）
- **操作系统**: Windows / Linux / macOS

## 后端安装

### 1. 克隆项目或进入项目目录

```bash
cd medical-record-inspector
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r src/requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 到 `.env` 并填写必要的 API 密钥：

```bash
cp src/.env.example src/.env
```

编辑 `.env` 文件：

```env
# LLM 提供商配置（至少配置一个）
OPENAI_API_KEY=your_openai_api_key_here
DASHSCOPE_API_KEY=your_dashscope_api_key_here
ERNIE-bot_API_KEY=your_ernie_bot_api_key_here

# LLM 模型名称（可选，默认使用第一个可用模型）
MODEL_NAME=gpt-4
LLM_PROVIDER=openai
```

### 5. 启动后端服务

```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 运行。

访问 API 文档：`http://localhost:8000/docs`

## 前端安装

### 1. 进入前端目录

```bash
cd frontend
```

### 2. 安装依赖

```bash
npm install
```

### 3. 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:5173` 运行。

## Docker 部署（可选）

### 构建镜像

```bash
docker build -t medical-record-inspector .
```

### 运行容器

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key \
  medical-record-inspector
```

## 验证安装

### 后端验证

```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 应返回：
# {"status":"healthy","service":"Medical Record Inspector"}
```

### 前端验证

打开浏览器访问 `http://localhost:5173`，应看到病历评估界面。

## 常见问题

### 1. Python 依赖安装失败

确保使用 Python 3.8+：
```bash
python --version
```

### 2. Node.js 版本过低

访问 [Node.js 官网](https://nodejs.org/) 下载最新版本。

### 3. API 密钥配置

确保 `.env` 文件中的 API 密钥正确且未过期。不同 LLM 提供商的密钥获取方式：

- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **通义千问**: [https://dashscope.console.aliyun.com/apiKey](https://dashscope.console.aliyun.com/apiKey)
- **文心一言**: [https://cloud.baidu.com/product/wenxinworkshop](https://cloud.baidu.com/product/wenxinworkshop)

### 4. 端口已被占用

修改 `uvicorn` 启动命令中的端口号：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

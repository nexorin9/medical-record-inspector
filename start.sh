#!/bin/bash

# Medical Record Inspector Startup Script
# Linux/Mac 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "Medical Record Inspector 启动脚本"
echo "======================================"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在，正在从 .env.example 创建..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "已创建 .env 文件，请编辑填入 API 密钥"
        echo "ANTHROPIC_API_KEY=your_api_key_here"
    else
        echo "错误: .env.example 文件也不存在"
        exit 1
    fi
fi

# 检查 ANTHROPIC_API_KEY 配置
if ! grep -q "^ANTHROPIC_API_KEY=" .env; then
    echo "警告: ANTHROPIC_API_KEY 未在 .env 文件中配置"
    echo "请编辑 .env 文件填入 API 密钥"
fi

# 安装依赖（如果 requirements.txt 存在）
if [ -f "requirements.txt" ]; then
    echo "检查依赖..."
    python3 -m pip install --user -r requirements.txt 2>/dev/null || {
        echo "依赖安装失败，请手动运行: python3 -m pip install -r requirements.txt"
    }
fi

# 解析参数
PORT=8000
HOST="0.0.0.0"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --host|-h)
            HOST="$2"
            shift 2
            ;;
        --reload|-r)
            RELOAD="--reload"
            shift
            ;;
        --help|-h)
            echo "用法: ./start.sh [选项]"
            echo ""
            echo "选项:"
            echo "  -p, --port PORT    设置端口号 (默认: 8000)"
            echo "  -h, --host HOST    设置主机 (默认: 0.0.0.0)"
            echo "  -r, --reload       启用自动重载 (开发模式)"
            echo "  --help             显示帮助信息"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

echo "启动服务..."
echo "  端口: $PORT"
echo "  主机: $HOST"
echo "  重载: ${RELOAD:-禁用}"
echo ""

# 启动服务
python3 -m uvicorn api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    ${RELOAD:---reload}

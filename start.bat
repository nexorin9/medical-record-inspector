@echo off
REM Medical Record Inspector Startup Script
REM Windows 启动脚本

echo ======================================
echo Medical Record Inspector 启动脚本
echo ======================================

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python 3.9+
    exit /b 1
)

REM 检查 .env 文件是否存在
if not exist ".env" (
    echo 警告: .env 文件不存在，正在从 .env.example 创建...
    if exist ".env.example" (
        copy .env.example .env
        echo 已创建 .env 文件，请编辑填入 API 密钥
        echo ANTHROPIC_API_KEY=your_api_key_here
    ) else (
        echo 错误: .env.example 文件也不存在
        exit /b 1
    )
)

REM 检查 ANTHROPIC_API_KEY 配置
findstr /C:"ANTHROPIC_API_KEY=" .env >nul
if %errorlevel% neq 0 (
    echo 警告: ANTHROPIC_API_KEY 未在 .env 文件中配置
    echo 请编辑 .env 文件填入 API 密钥
)

REM 安装依赖（如果 requirements.txt 存在）
if exist "requirements.txt" (
    echo 检查依赖...
    python -m pip install --user -r requirements.txt >nul 2>&1
    if %errorlevel% neq 0 (
        echo 依赖安装失败，请手动运行: python -m pip install -r requirements.txt
    )
)

REM 解析参数
set PORT=8000
set HOST=0.0.0.0
set RELOAD=--reload

:parse_args
if "%~1"=="" goto :end_parse
if "%~1"=="--port" (
    set PORT=%~2
    shift /2
    goto :parse_args
)
if "%~1"=="-p" (
    set PORT=%~2
    shift /2
    goto :parse_args
)
if "%~1"=="--host" (
    set HOST=%~2
    shift /2
    goto :parse_args
)
if "%~1"=="-h" (
    set HOST=%~2
    shift /2
    goto :parse_args
)
if "%~1"=="--reload" (
    set RELOAD=--reload
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    echo 用法: start.bat [选项]
    echo.
    echo 选项:
    echo   -p, --port PORT    设置端口号 (默认: 8000)
    echo   -h, --host HOST    设置主机 (默认: 0.0.0.0)
    echo   --reload           启用自动重载 (开发模式)
    echo   --help             显示帮助信息
    exit /b 0
)
shift
goto :parse_args

:end_parse

echo 启动服务...
echo   端口: %PORT%
echo   主机: %HOST%
echo   重载: %RELOAD%
echo.

REM 启动服务
python -m uvicorn api.main:app ^
    --host %HOST% ^
    --port %PORT% ^
    %RELOAD%

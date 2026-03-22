@echo off
REM =============================================================================
REM Medical Record Inspector - Start Script (Windows)
REM =============================================================================

echo  =======================================
echo   Medical Record Inspector
echo   Starting up...
echo  =======================================

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
set VENV_DIR=%SCRIPT_DIR%.venv
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Install dependencies if requirements.txt exists
if exist "src\requirements.txt" (
    echo Installing/updating dependencies...
    pip install --quiet -r "src\requirements.txt"
)

REM Check if .env exists, create from .env.example if not
if not exist "src\.env" (
    echo.
    echo WARNING: .env file not found. Please configure your API keys.
    echo Copy .env.example to .env and fill in your values:
    echo   copy src\.env.example src\.env
    echo   rem Edit src\.env with your API keys
    echo.
    set /p CONTINUE="Continue without .env file? (y/n) "
    if /i not "%CONTINUE%"=="y" (
        deactivate
        pause
        exit /b 1
    )
)

REM Start the backend server
echo.
echo Starting FastAPI backend server on http://localhost:8000
echo Open http://localhost:8000/docs for API documentation
echo.

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

REM Deactivate virtual environment when done
deactivate

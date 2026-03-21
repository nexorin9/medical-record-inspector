#!/bin/bash
# =============================================================================
# Medical Record Inspector - Start Script (Linux/Mac)
# =============================================================================

set -e

echo " ======================================="
echo "  Medical Record Inspector"
echo "  Starting up..."
echo " ======================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

# Create virtual environment if it doesn't exist
VENV_DIR="${SCRIPT_DIR}/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install dependencies if requirements.txt exists
if [ -f "${SCRIPT_DIR}/src/requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    pip install --quiet -r "${SCRIPT_DIR}/src/requirements.txt"
fi

# Check if .env exists, create from .env.example if not
if [ ! -f "${SCRIPT_DIR}/src/.env" ]; then
    echo ""
    echo "WARNING: .env file not found. Please configure your API keys."
    echo "Copy .env.example to .env and fill in your values:"
    echo "  cp src/.env.example src/.env"
    echo "  # Edit src/.env with your API keys"
    echo ""
    read -p "Continue without .env file? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the backend server
echo ""
echo "Starting FastAPI backend server on http://localhost:8000"
echo "Open http://localhost:8000/docs for API documentation"
echo ""

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

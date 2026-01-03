#!/bin/bash

echo "========================================"
echo "  HA Config Manager - Backend Setup"
echo "========================================"
echo ""

cd orchestrator

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        echo "Please ensure Python 3.9+ is installed"
        exit 1
    fi
    echo "Virtual environment created successfully!"
    echo ""
else
    echo "[1/4] Virtual environment already exists"
    echo ""
fi

# Activate virtual environment
echo "[2/4] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo ""

# Install dependencies
echo "[3/4] Installing dependencies..."
echo "This may take a few minutes on first run..."
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully!"
echo ""

# Start the server
echo "[4/4] Starting backend server on http://localhost:8081"
echo ""
echo "========================================"
echo "  Backend is starting..."
echo "  API Docs: http://localhost:8081/api/docs"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

uvicorn app.main:app --reload --port 8081 --host 0.0.0.0

#!/bin/bash

echo "========================================"
echo "  HA Config Manager - Frontend Setup"
echo "========================================"
echo ""

cd dashboard-react

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "[1/2] Installing dependencies..."
    echo "This may take a few minutes on first run..."
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo "Please ensure Node.js 18+ is installed"
        exit 1
    fi
    echo "Dependencies installed successfully!"
    echo ""
else
    echo "[1/2] Dependencies already installed"
    echo ""
fi

# Start the development server
echo "[2/2] Starting frontend server on http://localhost:3000"
echo ""
echo "========================================"
echo "  Frontend is starting..."
echo "  Open: http://localhost:3000"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

npm run dev

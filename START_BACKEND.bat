@echo off
echo ========================================
echo   HA Config Manager - Backend Setup
echo ========================================
echo.

cd orchestrator

REM Check if virtual environment exists
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please ensure Python 3.9+ is installed
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
) else (
    echo [1/4] Virtual environment already exists
    echo.
)

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install dependencies
echo [3/4] Installing dependencies...
echo This may take a few minutes on first run...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

REM Start the server
echo [4/4] Starting backend server on http://localhost:8081
echo.
echo ========================================
echo   Backend is starting...
echo   API Docs: http://localhost:8081/api/docs
echo   Press Ctrl+C to stop
echo ========================================
echo.

uvicorn app.main:app --reload --port 8081 --host 0.0.0.0

pause

@echo off
echo ========================================
echo   HA Config Manager - Frontend Setup
echo ========================================
echo.

cd dashboard-react

REM Check if node_modules exists
if not exist "node_modules" (
    echo [1/2] Installing dependencies...
    echo This may take a few minutes on first run...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Please ensure Node.js 18+ is installed
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
    echo.
) else (
    echo [1/2] Dependencies already installed
    echo.
)

REM Start the development server
echo [2/2] Starting frontend server on http://localhost:3000
echo.
echo ========================================
echo   Frontend is starting...
echo   Open: http://localhost:3000
echo   Press Ctrl+C to stop
echo ========================================
echo.

call npm run dev

pause

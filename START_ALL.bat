@echo off
echo ========================================
echo   HA Config Manager - Complete Setup
echo ========================================
echo.
echo This will start BOTH backend and frontend servers
echo in separate windows.
echo.
echo Press any key to continue...
pause >nul

REM Start backend in new window
echo Starting backend server...
start "HA Config Manager - Backend (Port 8081)" cmd /k START_BACKEND.bat

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start frontend in new window
echo Starting frontend server...
start "HA Config Manager - Frontend (Port 3000)" cmd /k START_FRONTEND.bat

echo.
echo ========================================
echo   Both servers are starting!
echo ========================================
echo.
echo Backend:  http://localhost:8081/api/docs
echo Frontend: http://localhost:3000
echo.
echo Two new windows have been opened.
echo You can close this window.
echo.
pause

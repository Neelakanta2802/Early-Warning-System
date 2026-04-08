@echo off
echo ========================================
echo Early Warning System - Startup Script
echo ========================================
echo.

echo [1] Starting Frontend Server...
echo     This will open in a new window
echo     Frontend URL: http://localhost:5173
echo.
start "Frontend - EWS" cmd /k "cd /d %~dp0 && set VITE_API_URL=http://127.0.0.1:8003 && npm run dev"

timeout /t 3 >nul

echo.
echo [2] Backend Server (Optional)
echo     To start backend, you need a .env file in the backend folder
echo     Backend URL: http://127.0.0.1:8003
echo.
echo     To start backend manually:
echo     cd backend
echo     python run.py
echo.

echo ========================================
echo Frontend is starting...
echo Open your browser to: http://localhost:5173
echo ========================================
echo.
echo Press any key to exit this window (frontend will keep running)...
pause >nul

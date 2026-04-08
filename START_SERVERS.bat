@echo off
echo ========================================
echo Starting Early Warning System Servers
echo ========================================
echo.

echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d %~dp0backend && set API_HOST=127.0.0.1 && set API_PORT=8003 && python run.py"
timeout /t 5 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd /d %~dp0 && set VITE_API_URL=http://127.0.0.1:8003 && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8003
echo Frontend: http://localhost:5173
echo.
echo Check the opened windows for server logs.
echo Press any key to exit this window...
pause >nul

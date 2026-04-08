@echo off
echo ========================================
echo Starting Both Servers
echo ========================================
echo.

echo [1] Starting Backend Server...
echo     URL: http://127.0.0.1:8006
echo     API Docs: http://127.0.0.1:8006/docs
echo.
start "Backend Server" cmd /k "cd /d %~dp0backend && set API_HOST=127.0.0.1 && set API_PORT=8006 && python run.py"

timeout /t 3 >nul

echo.
echo [2] Starting Frontend Server...
echo     URL: http://localhost:5173
echo.
start "Frontend Server" cmd /k "cd /d %~dp0 && set VITE_API_URL=http://127.0.0.1:8006 && npm run dev"

timeout /t 5 >nul

echo.
echo ========================================
echo Both servers are starting...
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8006
echo Frontend: http://localhost:5173
echo.
echo Check the two command windows that opened for any errors.
echo.
echo Press any key to close this window (servers will keep running)...
pause >nul

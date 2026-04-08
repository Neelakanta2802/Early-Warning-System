@echo off
echo ========================================
echo Starting Backend Server
echo ========================================
echo.

cd backend

if not exist .env (
    echo ERROR: .env file not found!
    echo.
    echo Please create a .env file in the backend folder with:
    echo   SUPABASE_URL=your-url
    echo   SUPABASE_KEY=your-key
    echo   SUPABASE_ANON_KEY=your-anon-key
    echo.
    echo See .env.example for template
    echo.
    pause
    exit /b 1
)

echo Starting backend on http://127.0.0.1:8006
echo API Docs will be at: http://127.0.0.1:8006/docs
echo.
set API_HOST=127.0.0.1
set API_PORT=8006
python run.py

pause

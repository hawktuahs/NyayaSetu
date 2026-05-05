@echo off
echo.
echo  ███╗   ██╗██╗   ██╗ █████╗ ██╗   ██╗ █████╗ ███████╗███████╗████████╗██╗   ██╗
echo  ████╗  ██║╚██╗ ██╔╝██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██║   ██║
echo  ██╔██╗ ██║ ╚████╔╝ ███████║ ╚████╔╝ ███████║███████╗█████╗     ██║   ██║   ██║
echo  ██║╚██╗██║  ╚██╔╝  ██╔══██║  ╚██╔╝  ██╔══██║╚════██║██╔══╝     ██║   ██║   ██║
echo  ██║ ╚████║   ██║   ██║  ██║   ██║   ██║  ██║███████║███████╗   ██║   ╚██████╔╝
echo  ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝    ╚═════╝
echo.
echo  न्यायसेतु — Justice Bridge  ^|  AI Court Judgment System
echo  =========================================================
echo.

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check Node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

REM Setup backend venv if not exists
if not exist "backend\venv" (
    echo [1/4] Creating Python virtual environment...
    python -m venv backend\venv
)

REM Install backend deps
echo [2/4] Installing backend dependencies...
backend\venv\Scripts\pip install -r backend\requirements.txt -q

REM Copy .env if not exists
if not exist "backend\.env" (
    copy backend\.env.example backend\.env >nul
    echo [INFO] Created backend\.env from template. Edit it to change LLM settings.
)

REM Create sample PDF
echo [3/4] Creating sample judgment PDF...
backend\venv\Scripts\python create_sample_pdf.py

REM Install frontend deps
if not exist "frontend\node_modules" (
    echo [4/4] Installing frontend dependencies...
    cd frontend && npm install --silent && cd ..
) else (
    echo [4/4] Frontend dependencies already installed.
)

echo.
echo  ✅ Setup complete! Starting NyayaSetu...
echo.
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo.

REM Start backend in background
start "NyayaSetu Backend" cmd /k "cd backend && venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
start "NyayaSetu Frontend" cmd /k "cd frontend && npm run dev"

echo  Both services starting. Press any key to open the browser...
pause >nul

start http://localhost:5173

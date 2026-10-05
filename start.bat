@echo off
echo ========================================================
echo   AutoML Genetic Optimizer
echo   Starting Backend and Frontend...
echo ========================================================

REM Add Node and Python to PATH
set PATH=C:\Program Files\nodejs;C:\Users\admin\AppData\Local\Programs\Python\Python314\Scripts;C:\Users\admin\AppData\Local\Programs\Python\Python314;%PATH%

REM Start Backend
start "AutoML Backend (FastAPI)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait 2 seconds
timeout /t 2 /nobreak >nul

REM Start Frontend
start "AutoML Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both servers are starting!
echo Backend:  http://localhost:8000 (API docs: http://localhost:8000/docs)
echo Frontend: http://localhost:5173
echo.
pause

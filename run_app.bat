@echo off
echo Starting Local Video Tool...

:: Activate venv
call .venv\Scripts\activate

:: Start Backend Server
start "Backend Server" cmd /k "python -m backend.app"

:: Start Worker
start "Worker Process" cmd /k "python -m backend.worker"

:: Start Frontend
cd frontend
start "Frontend" cmd /k "npm run dev"

echo All services started!

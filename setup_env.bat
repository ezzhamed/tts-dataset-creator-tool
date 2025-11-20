@echo off
echo Setting up Virtual Environment...

:: Create venv if it doesn't exist
if not exist .venv (
    python -m venv .venv
    echo Virtual environment created.
)

:: Activate venv
call .venv\Scripts\activate

:: Install Python Dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

:: Install Node Dependencies
echo Installing Node dependencies...
cd frontend
call npm install
cd ..

echo Setup Complete!
pause

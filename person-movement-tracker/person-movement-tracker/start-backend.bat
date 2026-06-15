@echo off
REM Start Backend Server
REM This script sets up and starts the FastAPI backend

cd /d "%~dp0backend"

echo.
echo ========================================
echo Person Movement Tracker - Backend
echo ========================================
echo.

REM Check if venv exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo Starting FastAPI server on port 8000...
echo.
echo API available at: http://localhost:8000
echo Swagger UI at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.
echo ========================================
echo.

REM Start server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

@echo off
REM Production startup script for Global ID Management System
REM Port: 8001

echo 🚀 Starting Global ID Management System - Production Mode (Port 8001)
echo ========================================================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo ✅ Virtual environment found.
    call venv\Scripts\activate.bat
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Using default settings.
    echo    Please create .env file for production settings.
) else (
    echo ✅ Environment file found.
)

REM Check database connectivity
echo 🔍 Checking database connectivity...
python -c "try: from app.models.database import engine; engine.connect(); print('✅ Database connection successful')" || (
    echo ❌ Database connection failed. Please check your configuration.
    pause
    exit /b 1
)

REM Start the application
echo 🌟 Starting FastAPI server on port 8001...
echo 📋 API Documentation will be available at: https://wecare.techconnect.co.id:8001/docs
echo 🔗 Pegawai REST API base URL: https://wecare.techconnect.co.id:8001/api/v1/pegawai
echo.
echo Press Ctrl+C to stop the server
echo.

REM Production startup with proper settings
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4 --access-log --no-reload --log-level info

pause
#!/bin/bash
# Production startup script for Global ID Management System
# Port: 8001

echo "🚀 Starting Global ID Management System - Production Mode (Port 8001)"
echo "========================================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ Virtual environment found."
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Using default settings."
    echo "   Please create .env file for production settings."
else
    echo "✅ Environment file found."
fi

# Check database connectivity
echo "🔍 Checking database connectivity..."
python -c "
try:
    from app.models.database import engine
    with engine.connect() as conn:
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please check your configuration."
    exit 1
fi

# Start the application
echo "🌟 Starting FastAPI server on port 8001..."
echo "📋 API Documentation will be available at: https://wecare.techconnect.co.id:8001/docs"
echo "🔗 Pegawai REST API base URL: https://wecare.techconnect.co.id:8001/api/v1/pegawai"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Production startup with proper workers and settings
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers 4 \
    --access-log \
    --no-reload \
    --log-level info
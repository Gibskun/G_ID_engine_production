#!/bin/bash
# Server Restart Script for G_ID Engine
# Run this on your server to properly restart the application

echo "🚀 Starting G_ID Engine Server Restart Process..."
echo "================================================"

# Step 1: Find and kill existing processes
echo "🔍 Step 1: Killing existing server processes..."
sudo pkill -f "uvicorn" 2>/dev/null
sudo pkill -f "main:app" 2>/dev/null
sudo pkill -f "python.*main" 2>/dev/null

# Kill processes using ports
echo "🔧 Freeing up ports 8000, 8001..."
sudo fuser -k 8000/tcp 2>/dev/null
sudo fuser -k 8001/tcp 2>/dev/null

# Wait for processes to fully terminate
echo "⏳ Waiting for processes to terminate..."
sleep 3

# Step 2: Clear Python cache
echo "🧹 Step 2: Clearing Python cache..."
cd /var/www/G_ID_engine_production
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "✅ Cache cleared"

# Step 3: Check if ports are free
echo "🔍 Step 3: Checking port availability..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 still in use"
else
    echo "✅ Port 8000 is free"
fi

if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8001 still in use"
else
    echo "✅ Port 8001 is free"
fi

# Step 4: Start server on new port
echo "🚀 Step 4: Starting server on port 8002..."
echo "Location: $(pwd)"
echo "Starting in 3 seconds..."
sleep 3

echo "================================================"
echo "🎉 STARTING G_ID ENGINE SERVER"
echo "🌐 Access at: http://your-server-ip:8002"
echo "🔄 Press Ctrl+C to stop"
echo "================================================"

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
#!/bin/bash
# Server Restart Script for G_ID System
# Run this script on the server after git pull

echo "🔧 G_ID System Server Restart Script"
echo "======================================"

# Navigate to project directory
cd /var/www/G_ID_engine_production

echo "1. Checking current service status..."
sudo systemctl status gid-system.service --no-pager

echo ""
echo "2. Stopping service..."
sudo systemctl stop gid-system.service

echo ""
echo "3. Checking if main.py exists..."
if [ -f "main.py" ]; then
    echo "✅ main.py found"
    ls -la main.py
else
    echo "❌ main.py not found!"
    exit 1
fi

echo ""
echo "4. Checking Python virtual environment..."
if [ -f "venv/bin/python" ]; then
    echo "✅ Virtual environment found"
    venv/bin/python --version
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

echo ""
echo "5. Reloading systemd configuration..."
sudo systemctl daemon-reload

echo ""
echo "6. Starting service..."
sudo systemctl start gid-system.service

echo ""
echo "7. Checking service status..."
sudo systemctl status gid-system.service --no-pager

echo ""
echo "8. Checking service logs (last 10 lines)..."
sudo journalctl -u gid-system.service --no-pager -n 10

echo ""
echo "9. Testing API endpoint..."
sleep 5  # Wait for service to fully start
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8001/api/v1/validation-config/status

echo ""
echo "🎯 Server restart complete!"
echo "If HTTP Status shows 200, the server is working correctly."
echo "If HTTP Status shows 000 or 404, check the service logs above for errors."
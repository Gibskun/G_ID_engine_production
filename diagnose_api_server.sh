#!/bin/bash

# Quick server diagnostic script to check API status

echo "🔍 Checking Global ID API Server Status..."
echo "========================================="
echo

# Check if service is running
echo "📋 Service Status:"
sudo systemctl status gid-system.service --no-pager -l
echo

# Check recent logs
echo "📄 Recent Service Logs:"
sudo journalctl -u gid-system.service --no-pager -n 20
echo

# Check application logs
echo "📝 Application Logs (last 20 lines):"
tail -n 20 /var/www/G_ID_engine_production/gid_system.log
echo

# Test basic connectivity
echo "🌐 Testing Basic Connectivity:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8001/
echo

# Test health endpoint if it exists
echo "💚 Testing Health Endpoint:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8001/api/v1/health
echo

# Test docs endpoint
echo "📚 Testing Docs Endpoint:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8001/docs
echo

# Check for any Python processes
echo "🐍 Python Processes:"
ps aux | grep python | grep -v grep
echo

echo "✅ Diagnostic complete!"
echo
echo "💡 If docs are failing:"
echo "   1. Restart service: sudo systemctl restart gid-system.service"
echo "   2. Check Python syntax: python -m py_compile main.py"
echo "   3. Test imports: python -c 'from main import app'"
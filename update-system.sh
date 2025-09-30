#!/bin/bash
# Update script for GID Management System

echo "🔄 Updating GID Management System..."

# Navigate to project directory
cd /var/www/gid-system

# Stop the service
echo "⏹️  Stopping service..."
sudo systemctl stop gid-system

# Pull latest changes from GitHub
echo "⬇️  Pulling latest changes..."
git pull origin main

# Activate virtual environment and update dependencies
echo "📦 Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Start the service
echo "▶️  Starting service..."
sudo systemctl start gid-system

# Check service status
echo "✅ Service status:"
sudo systemctl status gid-system --no-pager

echo "🚀 Update completed!"
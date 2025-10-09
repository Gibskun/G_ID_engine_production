# 🚨 URGENT FIX: Server 404 Error for Validation Endpoints

## Problem
After `git pull origin main` on server, the sync management page shows console errors:
```
GET https://wecare.techconnect.co.id/api/v1/validation-config/status 404 (Not Found)
Failed to load validation status
```

## Quick Fix Commands (Run on Server)

### Step 1: Connect to Server
```bash
ssh your-username@wecare.techconnect.co.id
```

### Step 2: Navigate to Project Directory
```bash
cd /var/www/G_ID_engine_production
```

### Step 3: Check Current Service Status
```bash
sudo systemctl status gid-system.service --no-pager
```

### Step 4: Restart the Service
```bash
sudo systemctl stop gid-system.service
sudo systemctl daemon-reload
sudo systemctl start gid-system.service
```

### Step 5: Verify Service is Running
```bash
sudo systemctl status gid-system.service --no-pager
```

### Step 6: Check Service Logs
```bash
sudo journalctl -u gid-system.service -f --lines=20
```

### Step 7: Test the API Endpoint
```bash
curl -X GET "http://localhost:8001/api/v1/validation-config/status" -H "Accept: application/json"
```

## Alternative: Use the Restart Script
```bash
cd /var/www/G_ID_engine_production
chmod +x restart_server.sh
./restart_server.sh
```

## Expected Results
- ✅ Service status should show "Active: active (running)"
- ✅ API endpoint should return JSON response (not 404)
- ✅ Sync management page should load validation status correctly
- ✅ Validation toggle button should work

## Verification
1. Open browser to: `https://wecare.techconnect.co.id/gid/sync-management`
2. Check browser console for errors (F12 → Console)
3. Click "Validation Rules Toggle" button
4. Verify it changes from "Loading..." to "Enable/Disable Validation Rules"

## Root Cause
The `git pull` command updated the codebase but the systemd service was still referencing the old configuration. The service needed to be restarted to use the updated `main.py` file and new route definitions.

## Files That Were Updated
- `main.py` - Application entry point
- `app/api/routes.py` - Contains validation endpoints
- `app/services/config_service.py` - Validation configuration logic
- `templates/sync_management.html` - Frontend validation toggle

## Service Configuration
The systemd service file should contain:
```ini
[Unit]
Description=Global ID Management System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/G_ID_engine_production
ExecStart=/var/www/G_ID_engine_production/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## If Problems Persist
1. Check if port 8001 is accessible: `netstat -tlnp | grep 8001`
2. Verify database connectivity
3. Check environment variables in `/var/www/G_ID_engine_production/.env.server`
4. Ensure all Python dependencies are installed: `venv/bin/pip list`

The issue is resolved once the systemd service is properly restarted and the API endpoints return valid JSON responses instead of 404 errors.
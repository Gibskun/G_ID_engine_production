# Server 404 Error and Validation Rules Fix

## Problem Summary
After `git pull origin main` on the server, the following issues occurred:
1. The systemd service `gid-system.service` failed to start because it couldn't find `main.py`
2. The validation rules toggle button on sync management page shows "loading..." indefinitely
3. Browser console shows: "Failed to load resource: the server responded with a status of 404 ()" and "Failed to load validation status"

## Root Cause Analysis
1. **Main.py Issue**: The git pull deleted the old `main.py` file but it has been recreated with updated structure
2. **Service Not Running**: The systemd service configuration is pointing to the correct file but the service failed to restart
3. **404 Endpoints**: The validation endpoints exist but the server isn't running to serve them

## Solution Steps

### 1. Verify Main.py Exists
The `main.py` file should now exist in the project root. Verify:
```bash
ls -la /var/www/G_ID_engine_production/main.py
```

### 2. Check Service Configuration
Verify the systemd service configuration:
```bash
sudo cat /etc/systemd/system/gid-system.service
```

The ExecStart should point to:
```
ExecStart=/var/www/G_ID_engine_production/venv/bin/python main.py
```

### 3. Restart the Service
```bash
cd /var/www/G_ID_engine_production
sudo systemctl daemon-reload
sudo systemctl restart gid-system.service
sudo systemctl status gid-system.service
```

### 4. Check Service Logs
If the service fails to start, check logs:
```bash
sudo journalctl -u gid-system.service -f --lines=50
```

### 5. Verify Endpoints
Once the service is running, test the validation endpoints:
```bash
# Test validation status endpoint
curl -X GET "http://localhost:8001/api/v1/validation-config/status" \
     -H "Accept: application/json"

# Test validation toggle endpoint
curl -X POST "http://localhost:8001/api/v1/validation-config/toggle-strict" \
     -H "Accept: application/json"
```

### 6. Test Web Interface
1. Navigate to: `http://your-server/gid/sync-management`
2. Click the "Validation Rules Toggle" button
3. Verify it changes from "Loading..." to either "Enable" or "Disable Validation Rules"

## Expected Results
After applying these fixes:
- ✅ The systemd service should start successfully
- ✅ The validation endpoints should return JSON responses (not 404)
- ✅ The sync management page validation toggle should work properly
- ✅ No more "Failed to load validation status" errors in browser console

## Validation Endpoints
The following endpoints should be working:
- `GET /api/v1/validation-config/status` - Get current validation status
- `POST /api/v1/validation-config/toggle-strict` - Toggle validation rules
- `POST /api/v1/validation-config/set` - Set specific validation settings

## Environment Configuration
The application automatically detects server vs local environment:
- **Server**: Uses direct database connection (10.182.128.3:1433)
- **Local**: Uses SSH tunnel (127.0.0.1:1435)

## Files Involved
- `/var/www/G_ID_engine_production/main.py` - Main application entry point
- `/var/www/G_ID_engine_production/app/api/routes.py` - Contains validation endpoints
- `/var/www/G_ID_engine_production/app/services/config_service.py` - Validation configuration service
- `/var/www/G_ID_engine_production/templates/sync_management.html` - Front-end validation toggle

## Troubleshooting
If issues persist:
1. Check if database is accessible
2. Verify environment variables are set correctly
3. Ensure all Python dependencies are installed in venv
4. Check firewall settings for port 8001

The main issue was that the server wasn't running after the git pull, causing all API endpoints (including validation endpoints) to return 404 errors.
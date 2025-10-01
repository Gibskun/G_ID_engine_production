# 🚀 Server Deployment & Swagger Fix Guide

## ❌ **Current Issue**
Swagger UI showing "end of the stream or document separator is expected" error.

## 🔍 **Root Cause**
The error occurs when the OpenAPI schema has parsing issues on the server, typically due to:
1. Service not restarted after code changes
2. Import errors in new modules
3. FastAPI route configuration conflicts
4. Missing dependencies

## ✅ **Step-by-Step Fix**

### **1. Deploy Latest Changes**
```bash
# SSH to your server
ssh your-server

# Navigate to project directory
cd /var/www/G_ID_engine_production

# Pull latest changes
git pull origin main

# Check what files were updated
git log --oneline -5
```

### **2. Install Missing Dependencies**
```bash
# Check current environment
source venv/bin/activate  # if using virtual environment

# Install any missing packages
pip install python-dotenv

# Verify all dependencies
pip install -r requirements.txt
```

### **3. Test Application Locally on Server**
```bash
# Test imports
python3 -c "from main import app; print('✅ Main app imports successfully')"

# Test OpenAPI generation
python3 fix_openapi_docs.py
```

### **4. Restart the Service**
```bash
# Stop the service
sudo systemctl stop gid-system.service

# Check if any processes are still running
ps aux | grep python | grep gid

# Kill any hanging processes if found
sudo pkill -f "gid-system"

# Start the service
sudo systemctl start gid-system.service

# Check status
sudo systemctl status gid-system.service

# Enable auto-start if not already enabled
sudo systemctl enable gid-system.service
```

### **5. Verify Service is Running**
```bash
# Check service logs
sudo journalctl -u gid-system.service -f --no-pager -n 50

# Test local connectivity
curl -i http://localhost:8001/

# Test health endpoint
curl -i http://localhost:8001/api/v1/health

# Test OpenAPI JSON
curl -i http://localhost:8001/openapi.json
```

### **6. Test Swagger UI**
```bash
# Test docs endpoint locally
curl -i http://localhost:8001/docs

# Check nginx is proxying correctly
curl -i https://wecare.techconnect.co.id/gid/docs
```

## 🔧 **Alternative Solutions**

### **Option A: Temporary Disable New Endpoints**
If the issue persists, temporarily comment out the new globalid_router:

```python
# In app/api/routes.py, comment out this line:
# api_router.include_router(globalid_router)  # Include Global ID data view endpoints
```

Then restart the service and test if Swagger works.

### **Option B: Check Nginx Configuration**
```bash
# Check nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Restart nginx if needed
sudo systemctl restart nginx
```

### **Option C: Direct Port Access**
Test if the issue is nginx-related by accessing directly:
- `http://your-server-ip:8001/docs`
- `http://your-server-ip:8001/openapi.json`

## 🎯 **Expected Results After Fix**

✅ **Service Status**: `active (running)`
✅ **Local Docs**: `http://localhost:8001/docs` shows Swagger UI
✅ **Production Docs**: `https://wecare.techconnect.co.id/gid/docs` shows Swagger UI  
✅ **API Endpoints**: All endpoints respond correctly
✅ **OpenAPI JSON**: Valid JSON schema at `/openapi.json`

## 📋 **New API Endpoints Available**

After successful deployment, these new endpoints will be available:

1. `GET /api/v1/global_id` - List all Global ID records
2. `GET /api/v1/global_id_non_database` - List all Non-Database Global ID records  
3. `GET /api/v1/global_id/{g_id}` - Get specific Global ID record
4. `GET /api/v1/global_id_non_database/{g_id}` - Get specific Non-Database record

## 🆘 **Emergency Rollback**

If issues persist, rollback the changes:

```bash
# Revert to previous commit
git log --oneline -10  # Find previous working commit
git checkout PREVIOUS_COMMIT_HASH -- .

# Restart service
sudo systemctl restart gid-system.service
```

## 📞 **Support Commands**

```bash
# Complete diagnostic
./diagnose_api_server.sh

# Check all processes
ps aux | grep -E "(python|gid|uvicorn|fastapi)"

# Check port usage
sudo netstat -tlnp | grep :8001

# Check firewall
sudo ufw status

# System resources
free -h
df -h
```

## 🎉 **Success Verification**

Once fixed, verify everything works:

1. ✅ Visit `https://wecare.techconnect.co.id/gid/docs`
2. ✅ See complete API documentation with all endpoints
3. ✅ Test employee creation via Swagger UI
4. ✅ Test Global ID data endpoints
5. ✅ Verify all endpoints return proper JSON responses

The system should now have comprehensive REST API functionality with both employee management and Global ID data access!
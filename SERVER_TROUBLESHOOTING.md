# 🚨 SERVER RESTART TROUBLESHOOTING GUIDE

## 🎯 **PROBLEM:** Server Already Running
You're getting "Address already in use" errors because there's already a server running.

## 🔧 **SOLUTION STEPS:**

### **STEP 1: Find Running Processes**
```bash
# Check what's using port 8000 and 8001
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8001

# OR use lsof
sudo lsof -i :8000
sudo lsof -i :8001

# Find all Python/uvicorn processes
ps aux | grep -E "(python|uvicorn|main)" | grep -v grep
```

### **STEP 2: Kill Existing Processes**
```bash
# Option A: Kill by port
sudo fuser -k 8000/tcp
sudo fuser -k 8001/tcp

# Option B: Kill by process name
sudo pkill -f "uvicorn"
sudo pkill -f "main:app"
sudo pkill -f "python.*main"

# Option C: Kill specific process ID (if you found it in step 1)
sudo kill -9 <PROCESS_ID>
```

### **STEP 3: Find Correct Systemd Service Name**
```bash
# List all services with 'gid' in the name
sudo systemctl list-units --type=service | grep -i gid

# List all services with 'g_id' in the name  
sudo systemctl list-units --type=service | grep -i g_id

# List all custom services
sudo systemctl list-units --type=service | grep -v "@"

# Check if there's a service for your app
sudo systemctl list-units --type=service | grep -E "(app|web|api|hr)"
```

### **STEP 4: Alternative Service Names to Try**
```bash
# Common service name patterns:
sudo systemctl restart gid-service
sudo systemctl restart g-id-service  
sudo systemctl restart g_id_service
sudo systemctl restart gid_engine
sudo systemctl restart hr-gid
sudo systemctl restart webapp
sudo systemctl restart fastapi-app
```

### **STEP 5: Manual Restart (If No Service Found)**
```bash
# After killing processes, start manually:
cd /var/www/G_ID_engine_production

# Clear Python cache first
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Start on a different port
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# OR start without reload (for production)
uvicorn main:app --host 0.0.0.0 --port 8002
```

## 🛠️ **COMPLETE RESTART SEQUENCE:**

```bash
# 1. Kill all existing processes
sudo pkill -f "uvicorn"
sudo pkill -f "main:app" 
sudo fuser -k 8000/tcp
sudo fuser -k 8001/tcp

# 2. Wait a moment
sleep 2

# 3. Clear cache
cd /var/www/G_ID_engine_production
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 4. Start fresh
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## 🔍 **VERIFY SUCCESS:**
After restart, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 🧪 **TEST THE FIX:**
1. Access your app at `http://your-server-ip:8002`
2. Upload your test file
3. Should see **0 skipped records**
4. No more "exceeds database limit" errors

---

## 📋 **QUICK COMMANDS TO RUN:**
```bash
# Run these commands in order:
sudo pkill -f "uvicorn"
sudo fuser -k 8000/tcp
sudo fuser -k 8001/tcp
cd /var/www/G_ID_engine_production
find . -name "*.pyc" -delete
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```
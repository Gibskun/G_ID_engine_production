# Production Server Deployment Configuration

## 🌐 **Production Server Details**
- **Domain**: `wecare.techconnect.co.id`
- **Port**: `8001`
- **Protocol**: `HTTPS`
- **Full API Base URL**: `https://wecare.techconnect.co.id:8001/api/v1/pegawai`

## 🚀 **Deployment Steps for Production Server**

### **Step 1: Update Server Configuration**

#### 1. Create Production Environment File
Create `.env.production` file:
```env
# Production Database Configuration
DB_SERVER=your_production_sql_server
DB_NAME=your_production_database
DB_USERNAME=your_production_username
DB_PASSWORD=your_production_password
DB_DRIVER=ODBC Driver 17 for SQL Server

# Application Configuration
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8001

# Security Settings
SECRET_KEY=your_production_secret_key
CORS_ORIGINS=https://wecare.techconnect.co.id

# Performance Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

#### 2. Update Systemd Service File
Update `/etc/systemd/system/gid-system.service`:
```ini
[Unit]
Description=Global ID Management System
After=network.target

[Service]
Type=simple
User=your_server_user
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/project/venv/bin
ExecStart=/path/to/your/project/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 3. Update Nginx Configuration
Update `/etc/nginx/sites-available/gid-system`:
```nginx
server {
    listen 80;
    server_name wecare.techconnect.co.id;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name wecare.techconnect.co.id;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # API Routes (Port 8001)
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # API Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files and main application (if needed)
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Step 2: Application Code Updates**

#### Update CORS Configuration in main.py
Ensure your `main.py` has production-ready CORS settings:
```python
from fastapi.middleware.cors import CORSMiddleware

# CORS configuration for production
origins = [
    "https://wecare.techconnect.co.id",
    "https://wecare.techconnect.co.id:8001",
    # Add other allowed origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Step 3: Database Configuration**

Ensure your production database is properly configured:
```python
# In app/models/database.py - Production settings should be optimized
DATABASE_URL = f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}?driver={DB_DRIVER}"

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False  # Set to False in production
)
```

### **Step 4: Security Checklist**

- [ ] SSL/TLS certificates installed and configured
- [ ] Database credentials secured in environment variables
- [ ] CORS origins restricted to your domain only
- [ ] Debug mode disabled in production
- [ ] Proper firewall rules configured
- [ ] Rate limiting implemented (optional but recommended)
- [ ] API key authentication (recommended for production API)

### **Step 5: Deployment Commands**

```bash
# 1. Upload files to server
scp -r . user@wecare.techconnect.co.id:/path/to/project/

# 2. Install dependencies on server
cd /path/to/project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Set up environment
cp .env.production .env

# 4. Test the application
python -m uvicorn main:app --host 0.0.0.0 --port 8001

# 5. Setup systemd service
sudo systemctl daemon-reload
sudo systemctl enable gid-system
sudo systemctl start gid-system

# 6. Restart nginx
sudo systemctl restart nginx

# 7. Check status
sudo systemctl status gid-system
sudo systemctl status nginx
```

## 🧪 **Production Testing**

### **Test URLs for Production:**

1. **API Documentation**: `https://wecare.techconnect.co.id:8001/docs`
2. **API Base**: `https://wecare.techconnect.co.id:8001/api/v1/pegawai/`
3. **Health Check**: `https://wecare.techconnect.co.id:8001/api/v1/dashboard/summary`

### **Postman Environment for Production:**

Create a new environment in Postman:
- **Environment Name**: "Production Server"
- **Variables**:
  - `baseUrl`: `https://wecare.techconnect.co.id:8001/api/v1/pegawai`
  - `serverUrl`: `https://wecare.techconnect.co.id:8001`

## 📊 **Performance Monitoring**

### **Key Metrics to Monitor:**

1. **Response Times**:
   - GET /api/v1/pegawai/ should be < 200ms
   - POST /api/v1/pegawai/ should be < 500ms

2. **Server Resources**:
   - CPU usage
   - Memory usage
   - Database connections

3. **Error Rates**:
   - 4xx client errors
   - 5xx server errors

### **Log Monitoring:**
```bash
# Monitor application logs
sudo journalctl -u gid-system -f

# Monitor nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## ✅ **Validation Checklist**

Before going live, ensure:

- [ ] All new Pegawai API endpoints are accessible
- [ ] Existing functionality still works
- [ ] Database connectivity is stable
- [ ] SSL certificates are valid
- [ ] API documentation is accessible
- [ ] Error responses are properly formatted
- [ ] Performance meets requirements
- [ ] Security configurations are in place

## 🔧 **Rollback Plan**

If issues occur:
1. **Immediate**: Stop the new service
2. **Revert**: Restore previous application version
3. **Restart**: Start services with old configuration
4. **Verify**: Test existing functionality

```bash
# Emergency rollback commands
sudo systemctl stop gid-system
# Restore backup files
sudo systemctl start gid-system
```

## 📞 **Support Information**

- **Server**: wecare.techconnect.co.id:8001
- **API Documentation**: https://wecare.techconnect.co.id:8001/docs
- **Status Check**: Monitor response times and error rates
- **Logs**: Check systemd and nginx logs for issues
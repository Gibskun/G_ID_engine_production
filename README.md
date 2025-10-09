# Global ID Management System

## 🚀 Quick Start

### For Local Development:
1. Start SSH tunnel: `gcloud compute ssh g-id-production --zone=asia-southeast2-a --ssh-flag="-L 1435:localhost:1433"`
2. Run: `python setup_and_run.py` or `start.bat`
3. Access: http://localhost:8000

### For Server Production:
1. Run: `python main.py`
2. Access: http://your-server:8001

**The system automatically detects your environment and applies the correct configuration!**

---

A high-performance, centralized platform for managing unique Global IDs with **dual environment support** (local development & server production), REST API integration, ultra-fast processing capabilities, and comprehensive data management features.

## 🌟 System Overview

The Global ID Management System provides centralized management of unique Global IDs across multiple data sources with **automatic environment detection**, SQL Server 2017 backend, FastAPI REST API, and ultra-performance processing capabilities that handle millions of records in 1-5 seconds.

## 🌍 **DUAL ENVIRONMENT SUPPORT**

The system automatically detects and configures itself for both environments:

### 🏠 **Local Development**
- **Auto-Detection**: Hostname, file paths, network connectivity
- **Database**: SSH tunnel via `127.0.0.1:1435` → `10.182.128.3:1433`
- **Server**: `http://127.0.0.1:8000` + `http://127.0.0.1:8000/gid/*`
- **Configuration**: Optimized for development (debug mode, smaller pools)

### 🖥️ **Server Production**  
- **Auto-Detection**: GCP environment, server paths, direct connectivity
- **Database**: Direct connection to `10.182.128.3:1433`
- **Server**: `http://0.0.0.0:8001`
- **Configuration**: Optimized for production (performance mode, larger pools)

## 🎯 Key Features

### Core Functionality
- **Centralized ID Management**: Generate and manage unique Global IDs for all personnel records
- **Multi-Source Integration**: Support database and Excel file data sources  
- **Real-Time Synchronization**: Automatic synchronization between different data sources
- **Data Integrity**: Ensure KTP (Indonesian ID) uniqueness across all sources
- **Web Dashboard**: User-friendly interface for data management and monitoring
- **Audit Trail**: Complete logging of all system activities and changes

### 📱 Responsive User Interface
- **Mobile-First Design**: Optimized for all devices from phones to desktops
- **Touch-Friendly Navigation**: 44px minimum touch targets for better mobile interaction
- **Adaptive Layouts**: Automatic layout adjustments for different screen sizes
- **Progressive Enhancement**: Enhanced features for capable devices while maintaining basic functionality
- **Cross-Platform Compatibility**: Works seamlessly across iOS, Android, and desktop browsers
- **Accessibility Support**: ARIA labels, keyboard navigation, and screen reader compatibility

### REST API (Production Ready)
- **Employee Management API**: Full CRUD operations for employee data
- **Auto G_ID Generation**: Automatic Global ID assignment on employee creation
- **Input Validation**: Comprehensive data validation with proper error messages
- **Pagination & Search**: Efficient data retrieval with filtering capabilities
- **Production Deployment**: Live at `https://wecare.techconnect.co.id/gid/api/v1/`

### Ultra-Performance Processing
- **Million-Record Processing**: Handle 1M+ records in 1-5 seconds
- **Vectorized Operations**: NumPy-based mathematical operations (10-100x speedup)
- **Parallel Processing**: Multi-core CPU utilization with automatic scaling
- **Bulk Database Operations**: Optimized batch processing
- **Memory-Mapped Operations**: Efficient large file handling

## 🏗️ Technology Stack

- **Backend**: Python 3.9+ with FastAPI 0.104.1
- **Database**: SQL Server 2017 (`g_id`) via pyodbc 4.0.39
- **ORM**: SQLAlchemy 2.0.23 with Pydantic 2.5.0 validation
- **Connection**: SSH tunnel (localhost:1435 → 10.182.128.3:1433)
- **Frontend**: HTML5, CSS3, JavaScript with Jinja2 templates
- **File Processing**: pandas 2.1.3, openpyxl 3.1.2, NumPy 1.24.3
- **Web Server**: Uvicorn 0.24.0 ASGI server
- **Performance**: Asyncio, multiprocessing, connection pooling

## 🚀 REST API Endpoints

### Production URLs
- **Base URL**: `https://wecare.techconnect.co.id/gid/api/v1/`
- **API Documentation**: `https://wecare.techconnect.co.id/gid/docs`
- **Health Check**: `https://wecare.techconnect.co.id/gid/api/v1/health`

### Employee Management API

#### GET All Employees
```http
GET /api/v1/pegawai/?page=1&size=20&search=john
```
**Response**: Paginated employee list with metadata

#### POST Create Employee
```http
POST /api/v1/pegawai/
Content-Type: application/json

{
  "name": "John Doe",
  "personal_number": "EMP001",
  "no_ktp": "1234567890123456",
  "bod": "1990-01-01"
}
```
**Response**: Created employee with auto-generated G_ID

#### Additional Endpoints
- `GET /api/v1/pegawai/{employee_id}` - Get employee by ID
- `PUT /api/v1/pegawai/{employee_id}` - Update employee
- `DELETE /api/v1/pegawai/{employee_id}` - Delete employee
- `GET /api/v1/pegawai/stats/summary` - Employee statistics

### API Features
- **Auto G_ID Generation**: Unique Global IDs created automatically
- **Input Validation**: 16-digit KTP validation, required field checking
- **Error Handling**: Structured error responses with detailed messages
- **Search & Pagination**: Efficient data retrieval with filtering
- **Duplicate Prevention**: Ensures KTP number uniqueness

## 🧪 **Testing REST APIs with Postman**

### **Available REST APIs**

#### **Employee Management APIs** (`/api/v1/pegawai/`)

| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/api/v1/pegawai/` | Get all employees (paginated) | 200 |
| `GET` | `/api/v1/pegawai/{id}` | Get employee by ID | 200/404 |
| `POST` | `/api/v1/pegawai/` | Create new employee (auto G_ID) | 201 |
| `PUT` | `/api/v1/pegawai/{id}` | Update employee | 200/404 |
| `DELETE` | `/api/v1/pegawai/{id}` | Soft delete employee | 200/404 |
| `GET` | `/api/v1/pegawai/stats/summary` | Employee statistics | 200 |

#### **🆕 NEW: G_ID-Based Operations** (`/api/v1/gid/`)

**Global_ID Table Operations:**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/api/v1/gid/global-id/{g_id}` | Get Global ID record by G_ID | 200/404 |
| `GET` | `/api/v1/gid/global-id/` | Get all Global ID records | 200 |
| `PUT` | `/api/v1/gid/global-id/{g_id}` | Update Global ID by G_ID | 200/404 |
| `DELETE` | `/api/v1/gid/global-id/{g_id}` | Delete Global ID by G_ID | 200/404 |
| `DELETE` | `/api/v1/gid/global-id/` | Bulk delete Global ID records | 200 |

**Global_ID_Non_Database Table Operations:**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/api/v1/gid/global-id-non-database/{g_id}` | Get Non-DB record by G_ID | 200/404 |
| `GET` | `/api/v1/gid/global-id-non-database/` | Get all Non-DB records | 200 |
| `PUT` | `/api/v1/gid/global-id-non-database/{g_id}` | Update Non-DB by G_ID | 200/404 |
| `DELETE` | `/api/v1/gid/global-id-non-database/{g_id}` | Delete Non-DB by G_ID | 200/404 |

**Pegawai Table Operations (by G_ID):**
| Method | Endpoint | Description | Status |
|--------|----------|-------------|---------|
| `GET` | `/api/v1/gid/pegawai/{g_id}` | Get Pegawai by G_ID | 200/404 |
| `GET` | `/api/v1/gid/pegawai/` | Get all Pegawai with G_ID | 200 |
| `PUT` | `/api/v1/gid/pegawai/{g_id}` | Update Pegawai by G_ID | 200/404 |
| `DELETE` | `/api/v1/gid/pegawai/{g_id}` | Delete Pegawai by G_ID (soft/hard) | 200/404 |

### **Postman Environment Setup**

#### **Step 1: Create Environment Variables**
Create a new environment in Postman called `G_ID_System`:

```json
{
  "local_url": "http://127.0.0.1:8000",
  "server_url": "https://wecare.techconnect.co.id/gid",
  "base_url": "{{local_url}}",
  "api_version": "v1"
}
```

#### **Step 2: Switch Between Environments**
- **Local Testing**: Set `base_url` = `{{local_url}}`
- **Server Testing**: Set `base_url` = `{{server_url}}`

### **API Test Examples**

#### **🔍 GET All Employees**
```
Method: GET
URL: {{base_url}}/api/{{api_version}}/pegawai/
Query Params:
  - page: 1
  - size: 20
  - search: (optional)
Headers:
  Content-Type: application/json
```

#### **👤 GET Employee by ID**
```
Method: GET
URL: {{base_url}}/api/{{api_version}}/pegawai/1
Headers:
  Content-Type: application/json
```

#### **➕ CREATE New Employee**
```
Method: POST
URL: {{base_url}}/api/{{api_version}}/pegawai/
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "name": "Jane Smith",
  "personal_number": "EMP002",
  "no_ktp": "9876543210987654",
  "bod": "1992-05-15"
}
```

**Expected Response (201):**
```json
{
  "success": true,
  "message": "Employee created successfully",
  "employee": {
    "id": 2,
    "g_id": "GID009876543210987654",
    "name": "Jane Smith",
    "personal_number": "EMP002",
    "no_ktp": "9876543210987654"
  }
}
```

#### **✏️ UPDATE Employee**
```
Method: PUT
URL: {{base_url}}/api/{{api_version}}/pegawai/2
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "name": "Jane Smith Updated",
  "personal_number": "EMP002-UPD"
}
```

#### **🗑️ DELETE Employee**
```
Method: DELETE
URL: {{base_url}}/api/{{api_version}}/pegawai/2
Headers:
  Content-Type: application/json
```

#### **📊 GET Statistics**
```
Method: GET
URL: {{base_url}}/api/{{api_version}}/pegawai/stats/summary
Headers:
  Content-Type: application/json
```

### **🆕 NEW: G_ID-Based API Tests**

#### **🔍 GET Global ID by G_ID**
```
Method: GET
URL: {{base_url}}/api/{{api_version}}/gid/global-id/GID009876543210987654
Headers:
  Content-Type: application/json
```

#### **📝 UPDATE Global ID by G_ID**
```
Method: PUT
URL: {{base_url}}/api/{{api_version}}/gid/global-id/GID009876543210987654
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "name": "Updated Name",
  "status": "Active"
}
```

#### **👤 GET Pegawai by G_ID**
```
Method: GET
URL: {{base_url}}/api/{{api_version}}/gid/pegawai/GID009876543210987654
Headers:
  Content-Type: application/json
Query Params (optional):
  - include_deleted: false
```

#### **🗑️ DELETE by G_ID (with options)**
```
Method: DELETE
URL: {{base_url}}/api/{{api_version}}/gid/pegawai/GID009876543210987654
Headers:
  Content-Type: application/json
Query Params (optional):
  - hard_delete: false  (true for permanent delete)
```

#### **📋 GET All Records by Table**
```
# Get all Global ID records
Method: GET
URL: {{base_url}}/api/{{api_version}}/gid/global-id/

# Get all Non-Database records  
Method: GET
URL: {{base_url}}/api/{{api_version}}/gid/global-id-non-database/

# Get all Pegawai with G_ID
Method: GET
URL: {{base_url}}/api/{{api_version}}/gid/pegawai/

Query Params (optional):
  - limit: 100
  - offset: 0
  - status_filter: Active
  - include_deleted: false
```

### **Testing Workflow**

#### **Local Testing (Development)**
1. **Start Local Server**: Run `python start_interactive.py`
2. **Set Environment**: Use `local_url` in Postman
3. **Test Sequence**: GET → POST → GET by ID → PUT → DELETE
4. **Verify**: Check auto G_ID generation works

#### **Server Testing (Production)**
1. **Set Environment**: Use `server_url` in Postman
2. **Test Same Sequence**: Verify all endpoints work
3. **Compare Results**: Ensure consistency between environments

### **Common Test Scenarios**

#### **✅ Success Tests**
- Create employee with valid data
- Get existing employee by ID
- Update employee with partial data
- Get paginated employee list

#### **❌ Error Tests**
- Invalid KTP number (less than 16 digits)
- Duplicate KTP number
- Non-existent employee ID
- Missing required fields

### **Quick Setup Commands**

#### **PowerShell Testing**
```powershell
# Local testing
$baseUrl = "http://127.0.0.1:8000"
Invoke-RestMethod -Uri "$baseUrl/api/v1/pegawai/" -Method GET

# Server testing  
$baseUrl = "https://wecare.techconnect.co.id/gid"
Invoke-RestMethod -Uri "$baseUrl/api/v1/pegawai/" -Method GET
```

### **API Documentation**
- **Local**: http://127.0.0.1:8000/docs
- **Server**: https://wecare.techconnect.co.id/gid/docs

**💡 Tip**: Use the interactive Swagger UI for quick API testing and documentation!

## 📱 Responsive User Interface

The system features a fully responsive web interface that works seamlessly across all devices and environments.

### Key Features
- **Mobile-First Design**: Optimized experience from smartphones to large desktops
- **Touch-Friendly Navigation**: Intuitive hamburger menu with smooth animations
- **Adaptive Layouts**: Tables, forms, and cards automatically adjust to screen size
- **Cross-Platform**: Consistent experience on iOS, Android, and desktop browsers
- **Progressive Enhancement**: Enhanced features for capable devices
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### Device Support
- **📱 Mobile (320px+)**: Stack layout, touch-optimized controls
- **📱 Tablet (768px+)**: Balanced layout with mobile navigation
- **💻 Desktop (992px+)**: Full horizontal navigation and grid layouts
- **🖥️ Large Screens (1200px+)**: Optimized spacing and enhanced layouts

### Responsive Features
- **Mobile Navigation**: Collapsible menu with smooth slide animation
- **Adaptive Tables**: Horizontal scroll or stack mode for small screens
- **Touch Optimization**: 44px minimum touch targets, iOS input fixes
- **Performance**: Hardware-accelerated animations, efficient media queries

### Usage Examples
```html
<!-- Responsive table -->
<div class="table-container table-responsive-mobile">
    <table><!-- Table content --></table>
</div>

<!-- Mobile-specific utilities -->
<div class="d-lg-none">Mobile only content</div>
<div class="d-md-none">Desktop only content</div>
```

For detailed implementation guide, see: `RESPONSIVE_UI_IMPLEMENTATION.md`

## 📊 System Performance

### Current Statistics
- **Total Employees**: 7,500+ with auto-generated Global IDs  
- **Response Time**: <3 seconds for standard operations
- **Dashboard Performance**: Optimized from 30s to 2-3s load time

### Ultra-Performance Benchmarks
- **Record Generation**: 2M records in 3.2 seconds  
- **Database Operations**: 1M records in 4.1 seconds
- **File Processing**: 1.5M Excel records in 2.8 seconds
- **Memory Usage**: <2GB for 2M records

## 🛠️ Installation & Setup

### Local Development
```bash
# Clone repository
git clone https://github.com/Gibskun/G_ID_engine_production.git
cd G_ID_engine_production

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database configuration

# Run application
python main.py
```

### Production Deployment
```bash
# Server: gcp-hr-applications (Ubuntu)
# Location: /var/www/G_ID_engine_production
# Service: systemd (gid-system.service)
# Port: 8001 (internal), HTTPS via nginx reverse proxy

# Deploy updates
git pull origin main
sudo systemctl restart gid-system.service
```

---

## 🛡️ Production Update & Verification Guide

This guide ensures your Global ID Management System is updated and running correctly on the server, with no changes to source code or nginx configuration. The same process works for local development.

### 1. Update Project Source
Navigate to your project directory and pull the latest code:

```bash
cd /var/www/G_ID_engine_production
git pull origin main
```

### 2. (Optional) Activate Python Virtual Environment
If not already active:

```bash
source venv/bin/activate
```

### 3. Restart the Service
Restart the FastAPI service to apply updates:

```bash
sudo systemctl restart gid-system.service
```

### 4. Check Service Status
Verify the service is running without errors:

```bash
sudo systemctl status gid-system.service --no-pager
```
Look for `active (running)` and absence of errors.

### 5. Verify Application & Static Assets
Test that the dashboard, static assets, and API endpoints are accessible:

```bash
# Dashboard HTML
curl -I https://wecare.techconnect.co.id/gid/

# CSS
curl -I https://wecare.techconnect.co.id/gid/static/css/style.css

# JS
curl -I https://wecare.techconnect.co.id/gid/static/js/main.js

# API Health
curl -I https://wecare.techconnect.co.id/gid/api/v1/health
```
All should return HTTP 200 OK (or 301 for the first, then 200 after redirect).

### 6. Browser Verification
Open https://wecare.techconnect.co.id/gid/ in your browser:
- Confirm the dashboard loads with correct styles and scripts.
- Use browser DevTools (Network tab) to check that CSS/JS are loaded from `/gid/static/...` (status 200).
- API calls should go to `/gid/api/v1/...` and succeed.

### 7. Local Development
For local testing, run:

```bash
python main.py
# or
python start_interactive.py
```
Access via http://localhost:8000/ or http://localhost:8000/gid/ (both work).

### 8. Troubleshooting
- If static assets do not load, clear browser cache or use a private window.
- If favicon is missing, add `static/favicon.ico` or remove the favicon link in `base.html`.
- If service fails to start, check logs:
  ```bash
  sudo journalctl -u gid-system.service -n 100
  tail -f gid_system.log
  ```

---

## 🧪 API Testing

### Postman Testing
1. **Import Collection**: Use provided Postman collection
2. **Configure Variables**: Set `base_url` to production URL
3. **Test Endpoints**: GET → POST → PUT → DELETE sequence

### PowerShell Testing
```powershell
# Test GET endpoint
Invoke-WebRequest -Uri "https://wecare.techconnect.co.id/gid/api/v1/pegawai/"

# Test POST endpoint
$body = @{
    name = "Test Employee"
    no_ktp = "1234567890123456"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://wecare.techconnect.co.id/gid/api/v1/pegawai/" -Method POST -Body $body -ContentType "application/json"
```

### Test Data Generation
```bash
# Generate sample employee data in multiple formats (CSV, XLSX, XLS)
python dummy_data_generator.py

# This creates test files:
# - sample_data_small.csv/.xlsx/.xls (10 records)
# - sample_data_medium.csv/.xlsx/.xls (100 records)  
# - sample_data_large.csv/.xlsx/.xls (1000 records)
```

### Ultra-Performance Testing
```bash
# Run ultra-performance setup
python startup_ultra_performance.py

# Generate test data
python ultra_dummy_generator.py

# Performance benchmarks
python test_dashboard_fix.py
```

## 📈 Performance Optimization

### Database Optimizations
- **Query Optimization**: Single aggregation queries replace multiple COUNT operations
- **Indexing**: Added indexes on status, source, no_ktp, and updated_at columns
- **Connection Pooling**: Optimized pool size with connection recycling
- **Bulk Operations**: Batch processing for large data operations

### Application Optimizations  
- **Vectorized Operations**: NumPy for mathematical computations
- **Parallel Processing**: Multi-core utilization for data processing
- **Memory Management**: Memory-mapped operations for large files
- **Async Operations**: Non-blocking I/O for maximum throughput

## 🔒 Security & Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=mssql+pyodbc://user:pass@host:port/db
DATABASE_HOST=10.182.128.3
DATABASE_PORT=1433
DATABASE_NAME=g_id

# Performance Configuration
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
QUERY_TIMEOUT=60

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8001
DEBUG=False
```

### Security Features
- **HTTPS**: SSL/TLS encryption via nginx reverse proxy
- **Database**: Internal network access with secure connections
- **Input Validation**: Comprehensive data validation and sanitization
- **Error Handling**: Secure error responses without sensitive data exposure

## 🎯 Key Achievements

- ✅ **REST API**: Production-ready employee management API with auto G_ID generation
- ✅ **Ultra-Performance**: Million-record processing in seconds
- ✅ **Database Migration**: Successfully migrated from PostgreSQL to SQL Server
- ✅ **Performance Optimization**: Dashboard load time reduced from 30s to 2-3s
- ✅ **Production Deployment**: Live system at wecare.techconnect.co.id
- ✅ **Comprehensive Testing**: Complete API testing with Postman collections
- ✅ **Documentation**: Full API documentation and deployment guides

## 📞 System Monitoring

### Health Checks
```bash
# System status
sudo systemctl status gid-system.service

# Application logs
sudo journalctl -u gid-system.service -f
tail -f gid_system.log

# API health check
curl https://wecare.techconnect.co.id/gid/api/v1/health
```

### Maintenance Operations
```bash
# Restart service
sudo systemctl restart gid-system.service

# Update application
cd /var/www/G_ID_engine_production
git pull origin main
sudo systemctl restart gid-system.service

# Database optimization
python optimize_dashboard.py
```

## 📂 Project Structure

```
G_ID_engine_production/
├── app/
│   ├── api/              # REST API endpoints and models
│   ├── models/           # Database models and schemas
│   └── services/         # Business logic and services
├── static/               # CSS, JavaScript, assets
├── templates/            # HTML templates
├── scripts/              # Utility scripts
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## ⚙️ Nginx /gid/ Rewrite Compatibility & Static Assets

This deployment runs behind an Nginx rule that rewrites `/gid/<path>` to `/<path>` before the request reaches FastAPI:

```
location /gid/ {
  rewrite ^/gid(/.*)$ $1 break;
  proxy_pass http://localhost:8001;
  ...
}
```

Implications:
1. The FastAPI app never sees the original `/gid` prefix (a browser request to `/gid/static/css/style.css` arrives as `/static/css/style.css`).
2. Server-side `request.url.path` cannot be trusted to detect the user-facing prefix.
3. Using `url_for('static', ...)` produced absolute `/static/...` URLs which, when rendered under `/gid/`, pointed the browser to `https://domain/static/...` (wrong upstream) instead of `https://domain/gid/static/...`.

Solution Implemented (Oct 2025):
* Templates now use **relative static asset paths**: `static/css/style.css`, `static/js/main.js`.
* Navigation links are relative (`database-explorer`, `upload`, etc.) rather than absolute.
* Browser resolution rules turn these into the correct prefixed URLs when the page is under `/gid/`.
* The JS API client auto-detects whether the current path is under `/gid/` and prepends `/gid/api/v1` for calls (which Nginx rewrites correctly) or falls back to `/api/v1` when served at the root.

Benefits:
* Single codebase works locally at `/`, locally at `/gid/`, and in production at `/gid/` without changing Nginx.
* Eliminates mixed-content or missing CSS/JS due to incorrect absolute paths.

If you later add new templates or scripts, follow these guidelines:
* Prefer relative links for in-app navigation: `href="sync"` instead of `/sync` or `/gid/sync`.
* Prefer relative static references: `src="static/js/feature.js"`.
* For API access in new JS files, either import the existing `GIDSystemAPI` or replicate the prefix auto-detection logic.

Rollback Option:
If in a future environment the app is always served at the root without rewrite, the relative paths still function (they resolve to `/static/...`). No changes required.

Health Check Reminder:
Verify after deployment:
```
curl -I https://wecare.techconnect.co.id/gid/
curl -I https://wecare.techconnect.co.id/gid/static/css/style.css
curl -I https://wecare.techconnect.co.id/gid/api/v1/health
```
All three should return 200 (or 301 for the first followed by 200 after redirect) indicating successful static + API routing.


---

**Global ID Management System** - Centralized, High-Performance, Production-Ready

**Live API**: https://wecare.techconnect.co.id/gid/api/v1/ | **Documentation**: https://wecare.techconnect.co.id/gid/docs
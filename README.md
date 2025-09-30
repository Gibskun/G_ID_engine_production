# Global ID (G_ID) Management System | Sistem Manajemen Global ID (G_ID)

**[English](#english)** | **[Bahasa Indonesia](#bahasa-indonesia)**

---

## English

### 🌟 System Overview

The Global ID Management System is a comprehensive, centralized platform for managing unique Global IDs across multiple data sources. **Migrated from PostgreSQL to SQL Server 2017** with a consolidated single-database architecture, it provides seamless integration between database systems and Excel file sources with real-time synchronization, monitoring capabilities, and an intuitive web interface.

### 🎯 Key Features

- **Centralized ID Management**: Generate and manage unique Global IDs for all personnel records
- **Multi-Source Integration**: Support both database and Excel file data sources  
- **Real-Time Synchronization**: Automatic synchronization between different data sources
- **Data Integrity**: Ensure No_KTP (Indonesian ID) uniqueness across all sources
- **Web Interface**: User-friendly dashboard for data management and monitoring
- **Audit Trail**: Complete logging of all system activities and changes
- **Excel/CSV Support**: Upload and process Excel/CSV files with validation
- **API Integration**: RESTful API for external system integration

### 🏗️ Technology Stack

- **Backend Framework**: Python 3.8+ with FastAPI 0.104.1
- **Database**: SQL Server 2017 with consolidated single database architecture (`dbvendor`)
- **Database Driver**: pyodbc 4.0.39 with ODBC Driver 17 for SQL Server
- **ORM**: SQLAlchemy 2.0.23 for database operations
- **Connection**: SSH tunnel via Google Cloud IAP (localhost:1435 → 10.182.128.3:1433)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+) with Jinja2 templates
- **File Processing**: pandas 2.1.3 and openpyxl 3.1.2 for Excel/CSV handling
- **Environment Management**: python-dotenv 1.0.0 for configuration
- **Web Server**: Uvicorn 0.24.0 ASGI server
- **Data Validation**: Pydantic 2.5.0 for request/response validation

### ⚡ Ultra-Performance System (NEW!)

**🚀 Million-Record Processing in 1-5 Seconds**

This system now includes **ultra-high-performance capabilities** designed to process millions of records in just 1-5 seconds:

#### 🎯 Performance Features
- **Vectorized Operations**: NumPy-based mathematical operations (10-100x speedup)
- **Parallel Processing**: Multi-core CPU utilization with automatic worker scaling
- **Bulk Database Operations**: Eliminates individual insert/update overhead
- **Connection Pooling**: Optimized database connection management
- **Memory-Mapped Operations**: Efficient handling of large files without full memory loading
- **Asyncio Integration**: Non-blocking operations for maximum throughput

#### 📊 Performance Targets
| Operation | Records | Target Time | Expected Speed |
|-----------|---------|-------------|----------------|
| Dummy Data Generation | 1M | ≤5 seconds | >200K records/sec |
| Excel/CSV Processing | 1M | ≤5 seconds | >200K records/sec |
| Data Synchronization | 1M | ≤5 seconds | >200K records/sec |

#### 🛠️ Ultra-Performance Tools
- **`ultra_dummy_generator.py`** - Million-record generation with benchmarking
- **`test_ultra_performance.py`** - Comprehensive performance validation suite
- **`startup_ultra_performance.py`** - Automated system setup and validation
- **Ultra API Endpoints** - `/api/v1/ultra/` for high-speed operations

#### 🚀 Quick Start Ultra-Performance
```bash
# Automated setup and validation
python startup_ultra_performance.py

# Generate 1 million records ultra-fast
python ultra_dummy_generator.py --records 1000000

# Run performance benchmarks
python test_ultra_performance.py
```

### 📁 Project Structure

```
engine_database_GID_SQLServer/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQL Server connections & sessions
│   │   └── models.py          # SQLAlchemy ORM models (SQL Server schema)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gid_generator.py   # G_ID generation logic
│   │   ├── sync_service.py    # Data synchronization
│   │   ├── excel_service.py   # Excel file processing
│   │   ├── excel_sync_service.py # Excel sync operations
│   │   ├── advanced_workflow_service.py # Advanced workflows
│   │   ├── optimized_sync.py  # Performance optimizations
│   │   ├── ultra_performance.py # Ultra-high-performance processor (NEW!)
│   │   └── monitoring_service.py # System monitoring (polling-based)
│   └── api/
│       ├── __init__.py
│       ├── routes.py          # FastAPI REST endpoints
│       ├── data_endpoints.py  # Data management endpoints
│       └── ultra_endpoints.py # Ultra-performance API endpoints (NEW!)
├── static/
│   ├── css/
│   │   └── style.css         # Application styling
│   └── js/
│       └── main.js           # Frontend JavaScript
├── templates/
│   ├── base.html             # Base template
│   ├── dashboard.html        # Main dashboard
│   ├── database_explorer.html # Database explorer (consolidated view)
│   ├── excel_upload.html     # File upload interface
│   ├── sync_management.html  # Sync operations
│   └── monitoring.html       # System monitoring
├── sql/
│   ├── create_schema_sqlserver.sql # SQL Server database schema
│   └── README.md             # SQL setup documentation
├── scripts/
│   └── generate_dummy_data.py # Test data generation
├── create_tables_first_time.py # First-time database setup script
├── create_tables_sqlalchemy.py # SQLAlchemy-based table creation
├── verify_tables.py         # Database verification script
├── main.py                   # Application entry point
├── dummy_data_generator.py   # Excel/CSV test data generator
├── ultra_dummy_generator.py  # Ultra-fast million-record generator
├── test_ultra_performance.py # Ultra-performance test suite
├── startup_ultra_performance.py # Ultra-performance system startup
├── requirements.txt          # Python dependencies (includes numpy, psutil)
├── .env.example             # Environment template (SQL Server config)
├── ADVANCED_SYNC_DOCUMENTATION.md # Advanced sync documentation
├── MIGRATION_SUMMARY.md      # PostgreSQL to SQL Server migration notes
├── sample_data_*.csv        # Sample CSV data files
└── README.md                # This documentation
```

### 🗄️ Database Architecture

#### Consolidated Single Database Design (SQL Server 2017)
- **dbvendor**: Consolidated SQL Server database containing all tables
- **Migration**: Successfully migrated from PostgreSQL dual-database to single SQL Server database
- **Connection**: Accessed via SSH tunnel through Google Cloud IAP
- **Schema**: All tables use `dbo` schema with proper SQL Server data types

#### Core Tables

**dbo.global_id** (Main G_ID storage)
```sql
- g_id NVARCHAR(10) PRIMARY KEY      # Unique Global ID (25YAAXX format)
- name NVARCHAR(255) NOT NULL        # Person name
- personal_number NVARCHAR(15)       # Employee ID (EMP-YYYY-NNNN)
- no_ktp NVARCHAR(16) UNIQUE NOT NULL # Indonesian National ID
- bod DATE                           # Birth date
- status NVARCHAR(15) DEFAULT 'Active' # Active/Non Active
- source NVARCHAR(20) DEFAULT 'database_pegawai' # Source: database_pegawai/excel
- created_at DATETIME2 DEFAULT GETDATE() # Creation timestamp
- updated_at DATETIME2 DEFAULT GETDATE() # Last update timestamp
```

**dbo.global_id_non_database** (Excel-sourced G_ID records)
```sql
- g_id NVARCHAR(10) PRIMARY KEY      # Unique Global ID (25YAAXX format)
- name NVARCHAR(255) NOT NULL        # Person name
- personal_number NVARCHAR(15)       # Employee ID (EMP-YYYY-NNNN)
- no_ktp NVARCHAR(16) UNIQUE NOT NULL # Indonesian National ID
- bod DATE                           # Birth date
- status NVARCHAR(15) DEFAULT 'Active' # Active/Non Active
- source NVARCHAR(20) DEFAULT 'excel' # Source: excel
- created_at DATETIME2 DEFAULT GETDATE() # Creation timestamp
- updated_at DATETIME2 DEFAULT GETDATE() # Last update timestamp
```

**dbo.pegawai** (Source employee data)
```sql
- id INT IDENTITY(1,1) PRIMARY KEY   # Auto-increment ID
- name NVARCHAR(255) NOT NULL        # Employee name
- personal_number NVARCHAR(15)       # Employee personal number
- no_ktp NVARCHAR(16) UNIQUE NOT NULL # National ID number
- bod DATE                           # Birth date
- g_id NVARCHAR(10)                  # Assigned Global ID (FK)
- created_at DATETIME2 DEFAULT GETDATE() # Creation timestamp
- updated_at DATETIME2 DEFAULT GETDATE() # Update timestamp
- deleted_at DATETIME2               # Soft delete timestamp
```

**dbo.g_id_sequence** (G_ID generation management)
```sql
- id INT IDENTITY(1,1) PRIMARY KEY   # Sequence ID
- current_year INT NOT NULL          # Current year (25 for 2025)
- current_digit INT NOT NULL         # Current digit (0-9)
- current_alpha_1 CHAR(1) NOT NULL   # First alpha character (A-Z)
- current_alpha_2 CHAR(1) NOT NULL   # Second alpha character (A-Z)
- current_number INT NOT NULL        # Current number (00-99)
- created_at DATETIME2 DEFAULT GETDATE() # Creation timestamp
- updated_at DATETIME2 DEFAULT GETDATE() # Update timestamp
```

**dbo.audit_log** (System audit trail)
```sql
- id INT IDENTITY(1,1) PRIMARY KEY   # Log entry ID
- table_name NVARCHAR(50) NOT NULL   # Affected table
- record_id NVARCHAR(50)             # Affected record ID
- action NVARCHAR(20) NOT NULL       # Action: INSERT/UPDATE/DELETE/SYNC
- old_values NVARCHAR(MAX)           # Previous values (JSON)
- new_values NVARCHAR(MAX)           # New values (JSON)
- changed_by NVARCHAR(100)           # User/system identifier
- change_reason NVARCHAR(MAX)        # Reason for change
- created_at DATETIME2 DEFAULT GETDATE() # Action timestamp
```

### 🔄 System Process Flow

#### 1. Initial System Setup
```
Database Creation → Schema Setup → Environment Configuration → Application Start
```

#### 2. Data Synchronization Process
```
Source Data Detection → Validation → G_ID Generation → Central Storage → Audit Logging
```

#### 3. G_ID Generation Algorithm
- **Format**: `25YAAXX` where:
  - `25` = Year 2025
  - `Y` = Digit (0-9)
  - `AA` = Two letters (AA-ZZ)
  - `XX` = Two digits (00-99)
- **Capacity**: 2,600,000 unique IDs per year

#### 4. Excel Upload Process34
```
File Upload → Validation → Data Parsing → Duplicate Check → G_ID Assignment → Database Integration
```

#### 5. Real-time Sync Process
```
Database Change Detection → Conflict Resolution → Update Processing → Audit Trail → Status Update
```

### 🚀 Installation Guide (From Zero to Running)

#### Prerequisites
- Windows 10/11 or Linux/MacOS
- Python 3.8 or higher
- **ODBC Driver 17 for SQL Server** (required for database connectivity)
- **Google Cloud CLI** (for SSH tunnel access)
- Git (optional)

#### Step 1: System Preparation
```bash
# Check Python version
python --version

# Install ODBC Driver 17 for SQL Server
# Windows: Download from Microsoft official site
# Or use winget: winget install Microsoft.SQLServer.2019.CmdLineUtils

# Install Google Cloud CLI (if not installed)
# Download from: https://cloud.google.com/sdk/docs/install

# Verify gcloud installation
gcloud --version
```

#### Step 2: Project Setup
```bash
# Navigate to your projects directory
cd "C:\Projects" # or your preferred directory

# Clone or extract project files
# If using git:
git clone <repository-url>
cd engine_database_GID_SQLServer

# If using zip file, extract and navigate to folder
```

#### Step 3: Python Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### Step 4: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

#### Step 5: Database Setup (SQL Server)

**Important**: Establish SSH tunnel first, then create SQL Server database

#### Method 1: Using Python Script (Recommended)
```bash
# Step 1: Authenticate with Google Cloud
gcloud auth login
gcloud config set project hris-292403

# Step 2: Create SSH tunnel to SQL Server (keep this terminal open)
gcloud compute start-iap-tunnel gcp-hr-applications 1433 --local-host-port=localhost:1435 --zone=asia-southeast2-a

# Step 3: Run first-time database setup (in a new terminal)
python create_tables_first_time.py

# Alternative: Use SQLAlchemy models approach
python create_tables_sqlalchemy.py

# Step 4: Verify tables were created
python verify_tables.py
```

#### Method 2: Using SQL Server Management Studio
1. **Establish SSH tunnel**: `gcloud compute start-iap-tunnel gcp-hr-applications 1433 --local-host-port=localhost:1435 --zone=asia-southeast2-a`
2. **Open SQL Server Management Studio**
3. **Connect to Server**: `localhost,1435` with credentials `sqlvendor1` / `1U~xO`2Un-gGqmPj`
4. **Open and execute**: `sql/create_schema_sqlserver.sql`

#### Method 3: Using sqlcmd (if available)
```bash
# Install SQL Server Command Line Utilities first:
winget install Microsoft.SQLServer.2019.CmdLineUtils

# Then execute (with SSH tunnel active):
sqlcmd -S localhost,1435 -U sqlvendor1 -P "1U~xO`2Un-gGqmPj" -i sql/create_schema_sqlserver.sql
```

**Troubleshooting Database Setup:**
- **SSH Tunnel Issues**: 
  - Ensure gcloud CLI is installed: `gcloud --version`
  - Authenticate: `gcloud auth login`
  - Set project: `gcloud config set project hris-292403`
  - Check tunnel status: `gcloud compute start-iap-tunnel --help`
- **Connection Issues**: 
  - Verify tunnel is active on port 1435: `netstat -an | findstr 1435`
  - Test connection: Use the verification script `python verify_tables.py`
  - Check firewall: Ensure port 1435 is not blocked
- **Authentication Issues**: 
  - Use exact password: `1U~xO`2Un-gGqmPj` (note the backtick, not backslash)
  - Verify credentials in SQL Server Management Studio first
- **ODBC Driver**: Install "ODBC Driver 17 for SQL Server" from Microsoft official site
- **pyodbc Issues**: Ensure `pip install pyodbc==4.0.39` is successful

#### Step 6: Environment Configuration
```bash
# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env file with your settings
```

**Required .env Configuration:**
```env
# SQL Server Database Configuration (via SSH Tunnel)
# Note: Use URL encoding for special characters in password
DATABASE_URL=mssql+pyodbc://sqlvendor1:1U~xO%602Un-gGqmPj@127.0.0.1:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Connection+Timeout=30
SOURCE_DATABASE_URL=mssql+pyodbc://sqlvendor1:1U~xO%602Un-gGqmPj@127.0.0.1:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes&Connection+Timeout=30

# Database Details (for direct connection testing)
DATABASE_HOST=127.0.0.1
DATABASE_PORT=1435
DATABASE_NAME=dbvendor
DATABASE_USER=sqlvendor1
DATABASE_PASSWORD=1U~xO`2Un-gGqmPj

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# File Upload Settings
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=xlsx,xls,csv

# SSH Tunnel Command Reference
# gcloud compute start-iap-tunnel gcp-hr-applications 1433 --local-host-port=localhost:1435 --zone=asia-southeast2-a
```

#### Step 7: Generate Test Data (Optional)
```bash
# Generate database test data
python scripts/generate_dummy_data.py

# Generate Excel/CSV test files
python dummy_data_generator.py
```

#### Step 8: Start the Application
```bash
# Run the application
python main.py
```

#### Step 9: Verify Installation
- Open browser and navigate to: `http://localhost:8000`
- Check system status and database connectivity
- Test file upload functionality
- Verify data synchronization

### 🌐 API Endpoints

#### Dashboard & System
- `GET /api/v1/dashboard` - Dashboard statistics and overview
- `GET /api/v1/database/explorer` - Database explorer (consolidated tables view)

#### G_ID Management
- `GET /api/v1/records` - List all Global IDs with pagination and filtering
- `GET /api/v1/records/count` - Get total count of records with filtering
- `GET /api/v1/records/{gid}` - Get specific G_ID details
- `POST /api/v1/gids/generate` - Generate new G_ID for No_KTP
- `PUT /api/v1/gids/{gid}` - Update G_ID record
- `DELETE /api/v1/gids/{gid}` - Deactivate G_ID record

#### Data Synchronization
- `POST /api/v1/sync/initial` - Perform complete synchronization
- `POST /api/v1/sync/incremental` - Sync only new/changed records
- `GET /api/v1/sync/status` - Get synchronization status
- `POST /api/v1/sync/excel/{file_id}` - Sync specific Excel file
- `POST /api/v1/system/repair-gid-sequence` - Repair G_ID sequence integrity

#### File Management
- `POST /api/v1/upload/excel` - Upload Excel/CSV file
- `GET /api/v1/files/` - List uploaded files
- `DELETE /api/v1/files/{file_id}` - Remove uploaded file

#### System Monitoring
- `GET /api/v1/monitor/status` - System health check
- `GET /api/v1/monitor/stats` - System statistics  
- `GET /api/v1/monitor/logs` - Recent audit logs

#### ⚡ Ultra-Performance Endpoints (NEW!)
- `POST /api/v1/ultra/generate-dummy-data` - Ultra-fast million-record generation
- `POST /api/v1/ultra/process-excel` - Ultra-fast Excel/CSV processing
- `POST /api/v1/ultra/sync-data` - Ultra-fast data synchronization
- `GET /api/v1/ultra/benchmark` - Performance benchmarking tools
- `GET /api/v1/ultra/status` - Ultra-performance system status

**Performance Targets**: Process 1M records in ≤5 seconds (>200K records/sec)

### 💻 Web Interface Features

#### Dashboard (`/`)
- System overview and statistics with real-time data
- Recent activity summary
- Quick access to all features
- System health indicators
- Consolidated SQL Server database metrics

#### Database Explorer (`/database-explorer`)
- **Consolidated view** of all tables in single SQL Server database
- Interactive table browser showing: `global_id`, `global_id_non_database`, `pegawai`
- Real-time data viewing with row counts
- Column schema information
- **Note**: Internal tables (`audit_log`, `g_id_sequence`) are hidden from UI

#### Excel Upload (`/excel-upload`)
- Drag-and-drop file upload interface
- File validation and preview
- Upload progress tracking with real-time feedback
- Error reporting and resolution
- Support for .xlsx, .xls, .csv formats

#### Sync Management (`/sync-management`)
- Manual sync controls for database operations
- Sync history and status monitoring
- Conflict resolution tools
- Performance metrics and optimization settings
- Advanced workflow management

#### Monitoring (`/monitoring`)
- Real-time system status with SQL Server connectivity
- Database connection health (SSH tunnel status)
- Performance graphs and metrics
- Alert management and logging
- Polling-based monitoring (replaced PostgreSQL LISTEN/NOTIFY)

### 🔧 Troubleshooting Guide

#### Common Issues and Solutions

**SQL Server Connection Errors**
```
Error: [Microsoft][ODBC Driver 17 for SQL Server]Login timeout expired
Solution:
1. Verify SSH tunnel is active: netstat -an | findstr 1435
2. Restart SSH tunnel: gcloud compute start-iap-tunnel gcp-hr-applications 1433 --local-host-port=localhost:1435 --zone=asia-southeast2-a
3. Check Google Cloud authentication: gcloud auth list
4. Test connection: python verify_tables.py

Error: [Microsoft][ODBC Driver 17 for SQL Server]Login failed for user 'sqlvendor1'
Solution:
1. Verify password format: 1U~xO`2Un-gGqmPj (backtick, not backslash)
2. Check connection string encoding in .env file
3. Test with SQL Server Management Studio first
4. Ensure SSH tunnel is pointing to correct server

Error: pyodbc.OperationalError: [Microsoft][ODBC Driver 17 for SQL Server]Named Pipes Provider: Could not open connection
Solution:
1. Confirm SSH tunnel is running and accessible
2. Check if port 1435 is available: netstat -an | findstr 1435
3. Restart gcloud tunnel with --verbosity=debug for detailed logs
4. Verify server is accessible: telnet 127.0.0.1 1435
```

**SSH Tunnel Issues**
```
Error: Permission denied (publickey,gssapi-keyex,gssapi-with-mic)
Solution:
1. Authenticate with Google Cloud: gcloud auth login
2. Set project: gcloud config set project hris-292403
3. Check IAP permissions in Google Cloud Console
4. Use IAP tunnel instead of direct SSH: gcloud compute start-iap-tunnel

Error: Tunnel connection failed
Solution:
1. Check if instance is running: gcloud compute instances list --project=hris-292403
2. Verify zone: --zone=asia-southeast2-a
3. Check firewall rules allow IAP access
4. Try different local port if 1435 is busy
```

**Database Schema Issues**
```
Error: Invalid object name 'dbo.global_id'
Solution:
1. Run first-time setup: python create_tables_first_time.py
2. Verify tables exist: python verify_tables.py
3. Check database name in connection string (should be 'dbvendor')
4. Ensure proper schema configuration in models.py

Error: Tables not showing in Database Explorer
Solution:
1. Check if tables exist in correct schema (dbo)
2. Verify API endpoint returns data: http://localhost:8000/api/v1/database/explorer
3. Clear browser cache and refresh page
4. Check console for JavaScript errors
```

**Python Import Errors**
```
Solution:
1. Activate virtual environment: venv\Scripts\activate
2. Install dependencies: pip install -r requirements.txt
3. Check Python path and module structure
4. Verify pyodbc installation: python -c "import pyodbc; print(pyodbc.version)"
```

**Excel Upload Failures**
```
Solution:
1. Verify file format (xlsx, xls, csv)
2. Check file size (max 10MB default)
3. Ensure required columns: name, personal_number, no_ktp, bod
4. Validate data format and No_KTP uniqueness
5. Check for special characters in data
```

**Application Startup Issues**
```
Error: FastAPI application won't start
Solution:
1. Check if SSH tunnel is active first
2. Verify .env file configuration
3. Test database connection: python verify_tables.py
4. Check port 8000 availability: netstat -an | findstr 8000
5. Run with debug: python main.py --reload
```

---

## Bahasa Indonesia

### 🌟 Gambaran Sistem

Sistem Manajemen Global ID adalah platform terpusat yang komprehensif untuk mengelola ID Global unik di berbagai sumber data. **Sistem telah dimigrasi dari PostgreSQL ke SQL Server 2017** dengan arsitektur database tunggal terkonsolidasi, menyediakan integrasi yang mulus antara sistem database dan sumber file Excel dengan sinkronisasi real-time, kemampuan monitoring, dan antarmuka web yang intuitif.

### 🎯 Fitur Utama

- **Manajemen ID Terpusat**: Generate dan kelola Global ID unik untuk semua record personel
- **Integrasi Multi-Sumber**: Mendukung sumber data database dan file Excel
- **Sinkronisasi Real-Time**: Sinkronisasi otomatis antar sumber data yang berbeda
- **Integritas Data**: Memastikan keunikan No_KTP di semua sumber data
- **Antarmuka Web**: Dashboard yang user-friendly untuk manajemen dan monitoring data
- **Audit Trail**: Logging lengkap semua aktivitas dan perubahan sistem
- **Dukungan Excel/CSV**: Upload dan proses file Excel/CSV dengan validasi
- **Integrasi API**: RESTful API untuk integrasi sistem eksternal

### 🏗️ Stack Teknologi

- **Framework Backend**: Python 3.8+ dengan FastAPI 0.104.1
- **Database**: SQL Server 2017 dengan arsitektur database tunggal terkonsolidasi (`dbvendor`)
- **Driver Database**: pyodbc 4.0.39 dengan ODBC Driver 17 for SQL Server
- **ORM**: SQLAlchemy 2.0.23 untuk operasi database
- **Koneksi**: SSH tunnel via Google Cloud IAP (localhost:1435 → 10.182.128.3:1433)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+) dengan template Jinja2
- **Pemrosesan File**: pandas 2.1.3 dan openpyxl 3.1.2 untuk handling Excel/CSV
- **Manajemen Environment**: python-dotenv 1.0.0 untuk konfigurasi
- **Web Server**: Uvicorn 0.24.0 ASGI server
- **Validasi Data**: Pydantic 2.5.0 untuk validasi request/response

### 🗄️ Arsitektur Database

#### Desain Database Tunggal Terkonsolidasi (SQL Server 2017)
- **dbvendor**: Database SQL Server terkonsolidasi berisi semua tabel
- **Migrasi**: Berhasil dimigrasi dari PostgreSQL dual-database ke SQL Server single-database
- **Koneksi**: Diakses via SSH tunnel melalui Google Cloud IAP
- **Schema**: Semua tabel menggunakan schema `dbo` dengan tipe data SQL Server yang sesuai

#### Tabel Inti

**Global_ID** (Penyimpanan G_ID utama)
```sql
- G_ID VARCHAR(10) PRIMARY KEY    # Global ID unik (format 25YAAXX)
- name VARCHAR(255)               # Nama person
- personal_number VARCHAR(15)     # ID Karyawan (EMP-YYYY-NNNN)
- No_KTP VARCHAR(16) UNIQUE       # Nomor KTP Indonesia
- BOD DATE                        # Tanggal lahir
- Status VARCHAR(15)              # Active/Non Active
- source VARCHAR(20)              # Sumber: database_pegawai/excel
- created_at TIMESTAMP            # Timestamp pembuatan
- updated_at TIMESTAMP            # Timestamp update terakhir
```

**pegawai** (Data karyawan sumber)
```sql
- id SERIAL PRIMARY KEY           # ID auto-increment
- name VARCHAR(255)               # Nama karyawan
- personal_number VARCHAR(15)     # Nomor personal karyawan
- No_KTP VARCHAR(16) UNIQUE       # Nomor KTP
- BOD DATE                        # Tanggal lahir
- G_ID VARCHAR(10)                # Global ID yang ditetapkan
- created_at TIMESTAMP            # Timestamp pembuatan
- updated_at TIMESTAMP            # Timestamp update
- deleted_at TIMESTAMP            # Timestamp soft delete
```

### 🔄 Alur Proses Sistem

#### 1. Setup Awal Sistem
```
Pembuatan Database → Setup Schema → Konfigurasi Environment → Start Aplikasi
```

#### 2. Proses Sinkronisasi Data
```
Deteksi Data Sumber → Validasi → Generate G_ID → Penyimpanan Terpusat → Audit Logging
```

#### 3. Algoritma Generate G_ID
- **Format**: `25YAAXX` dimana:
  - `25` = Tahun 2025
  - `Y` = Digit (0-9)
  - `AA` = Dua huruf (AA-ZZ)
  - `XX` = Dua digit (00-99)
- **Kapasitas**: 2.600.000 ID unik per tahun

#### 4. Proses Upload Excel
```
Upload File → Validasi → Parsing Data → Cek Duplikat → Assignment G_ID → Integrasi Database
```

### 🚀 Panduan Instalasi (Dari Nol Hingga Berjalan)

#### Prasyarat
- Windows 10/11 atau Linux/MacOS
- Python 3.8 atau lebih tinggi
- PostgreSQL 12 atau lebih tinggi
- Git (opsional)

#### Langkah 1: Persiapan Sistem
```bash
# Cek versi Python
python --version

# Install PostgreSQL (jika belum terinstall)
# Download dari: https://www.postgresql.org/download/

# Verifikasi instalasi PostgreSQL
psql --version
```

#### Langkah 2: Setup Proyek
```bash
# Navigasi ke direktori proyek
cd "C:\Projects" # atau direktori pilihan Anda

# Clone atau ekstrak file proyek
# Jika menggunakan git:
git clone <repository-url>
cd database_G_ID

# Jika menggunakan file zip, ekstrak dan navigasi ke folder
```

#### Langkah 3: Setup Environment Python
```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Di Windows:
venv\Scripts\activate
# Di Linux/Mac:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### Langkah 4: Install Dependencies
```bash
# Install semua package yang diperlukan
pip install -r requirements.txt

# Verifikasi instalasi
pip list
```

#### Langkah 5: Setup Database (SQL Server)

**Penting**: Buat SSH tunnel terlebih dahulu, kemudian setup database SQL Server

#### Metode 1: Menggunakan Script Python (Direkomendasikan)
```bash
# Langkah 1: Buat SSH tunnel ke SQL Server
gcloud compute ssh gcp-hr-applications --project hris-292403 --zone asia-southeast2-a --ssh-flag="-L 1435:10.182.128.3:1433"

# Langkah 2: Jalankan setup database menggunakan Python (di terminal baru)
python setup_database.py
```

#### Metode 2: Menggunakan SQL Server Management Studio
1. **Buat SSH tunnel** (sama seperti di atas)
2. **Buka SQL Server Management Studio**
3. **Connect ke Server**: `localhost,1435` dengan kredensial `sqlvendor1` / `1U~xO\`2Un-gGqmPj`
4. **Buka dan eksekusi**: `sql/create_schema_sqlserver.sql`

#### Metode 3: Menggunakan sqlcmd (jika tersedia)
```bash
# Install SQL Server Command Line Utilities terlebih dahulu:
winget install Microsoft.SQLServer.2019.CmdLineUtils

# Kemudian eksekusi:
sqlcmd -S localhost,1435 -U sqlvendor1 -P "1U~xO\`2Un-gGqmPj" -i sql/create_schema_sqlserver.sql
```

**Troubleshooting Setup Database:**
- **Masalah SSH Tunnel**: 
  - Pastikan gcloud CLI terinstall: `gcloud --version`
  - Otentikasi: `gcloud auth login`
  - Cek akses project: `gcloud projects list`
- **Masalah Koneksi**: 
  - Verifikasi tunnel aktif di port 1435: `netstat -an | findstr 1435`
  - Test dengan telnet: `telnet localhost 1435`
- **sqlcmd tidak ditemukan**: Gunakan metode Python atau install SQL Server tools
- **ODBC Driver**: Install "ODBC Driver 17 for SQL Server" dari Microsoft

#### Langkah 6: Konfigurasi Environment
```bash
# Copy template environment
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit file .env dengan pengaturan Anda
```

**Konfigurasi .env yang Diperlukan:**
```env
# Konfigurasi Database SQL Server (via SSH Tunnel)
DATABASE_URL=mssql+pyodbc://sqlvendor1:1U~xO%60%5C2Un-gGqmPj@localhost:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server
SOURCE_DATABASE_URL=mssql+pyodbc://sqlvendor1:1U~xO%60%5C2Un-gGqmPj@localhost:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server

# Detail Database
DATABASE_HOST=localhost
DATABASE_PORT=1435
DATABASE_NAME=dbvendor
DATABASE_USER=sqlvendor1
DATABASE_PASSWORD=1U~xO`\2Un-gGqmPj

# Pengaturan Aplikasi
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Pengaturan Upload File
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=xlsx,xls,csv
```

#### Langkah 7: Generate Data Test (Opsional)
```bash
# Generate data test database
python scripts/generate_dummy_data.py

# Generate file test Excel/CSV
python dummy_data_generator.py
```

#### Langkah 8: Jalankan Aplikasi
```bash
# Jalankan aplikasi
python main.py
```

#### Langkah 9: Verifikasi Instalasi
- Buka browser dan navigasi ke: `http://localhost:8000`
- Cek status sistem dan konektivitas database
- Test fungsi upload file
- Verifikasi sinkronisasi data

### 🌐 Endpoint API

#### Manajemen G_ID
- `GET /api/gids/` - List semua Global ID dengan pagination
- `POST /api/gids/generate` - Generate G_ID baru untuk No_KTP
- `GET /api/gids/{gid}` - Dapatkan detail G_ID spesifik
- `PUT /api/gids/{gid}` - Update record G_ID
- `DELETE /api/gids/{gid}` - Nonaktifkan record G_ID

#### Sinkronisasi Data
- `POST /api/sync/initial` - Lakukan sinkronisasi lengkap
- `POST /api/sync/incremental` - Sync hanya record baru/berubah
- `GET /api/sync/status` - Dapatkan status sinkronisasi
- `POST /api/sync/excel/{file_id}` - Sync file Excel spesifik

### 💻 Fitur Antarmuka Web

#### Dashboard (`/`)
- Gambaran dan statistik sistem
- Ringkasan aktivitas terbaru
- Akses cepat ke semua fitur
- Indikator kesehatan sistem

#### Excel Upload (`/excel-upload`)
- Upload file drag-and-drop
- Validasi dan preview file
- Tracking progress upload
- Pelaporan dan resolusi error

### 🔧 Panduan Troubleshooting

#### Masalah Umum dan Solusi

**Error Koneksi Database**
```
Error: psql: command not found
Solusi:
1. Tambahkan PostgreSQL ke system PATH:
   - Windows: Tambahkan C:\Program Files\PostgreSQL\[versi]\bin ke PATH
   - Restart terminal setelah menambahkan ke PATH
2. Atau gunakan path lengkap: "C:\Program Files\PostgreSQL\17\bin\psql.exe"

Error: password authentication failed for user [username]
Solusi:
1. Gunakan superuser postgres: psql -U postgres -d nama_database
2. Verifikasi password postgres (diatur saat instalasi PostgreSQL)
3. Cek service PostgreSQL berjalan: Get-Service "*postgres*"
4. Pastikan database ada: psql -U postgres -l
```

**Error Import Python**
```
Solusi:
1. Aktifkan virtual environment: venv\Scripts\activate
2. Install dependencies: pip install -r requirements.txt
3. Cek Python path dan struktur modul
```

**Gagal Upload Excel**
```
Solusi:
1. Verifikasi format file (xlsx, xls, csv)
2. Cek ukuran file (maks 10MB default)
3. Pastikan kolom diperlukan: name, personal_number, no_ktp, bod
4. Validasi format data dan keunikan
```

### 📋 Migration Notes (PostgreSQL → SQL Server)

This system has been successfully migrated from PostgreSQL to SQL Server 2017. Key changes include:

#### **Database Architecture Changes**
- **FROM**: Dual PostgreSQL databases (`global_id_db`, `pegawai_db`)
- **TO**: Single SQL Server database (`dbvendor`) with consolidated tables
- **Schema**: All tables now use `dbo` schema with proper SQL Server data types

#### **Technology Stack Updates**
- **Database Driver**: `psycopg2-binary` → `pyodbc 4.0.39`
- **Connection Protocol**: `postgresql://` → `mssql+pyodbc://`
- **Data Types**: `JSONB` → `NVARCHAR(MAX)` (JSON), `SERIAL` → `INT IDENTITY(1,1)`
- **Monitoring**: PostgreSQL `LISTEN/NOTIFY` → Polling-based approach

#### **Infrastructure Changes**
- **Connection Method**: Direct local connection → SSH tunnel via Google Cloud IAP
- **Server Access**: `localhost:5432` → `localhost:1435` (tunnel to `10.182.128.3:1433`)
- **Authentication**: Local credentials → Cloud-based authentication with specific credentials

#### **Application Updates**
- **API Endpoints**: Updated to `/api/v1/` versioning
- **Database Explorer**: Now shows consolidated view instead of dual-database view
- **Error Handling**: Enhanced for SQL Server specific error patterns
- **Configuration**: Updated `.env` structure for SQL Server parameters

#### **Files Added/Modified During Migration**
- `create_tables_first_time.py` - First-time database setup script
- `create_tables_sqlalchemy.py` - SQLAlchemy-based table creation
- `verify_tables.py` - Database verification utility
- `sql/create_schema_sqlserver.sql` - SQL Server-specific schema
- Updated all model files for SQL Server compatibility
- Enhanced monitoring and sync services

For detailed migration documentation, see `MIGRATION_SUMMARY.md`.

---

**Version**: 3.0.0 (SQL Server Edition)  
**Last Updated**: September 30, 2025  
**Migration Completed**: September 29, 2025  
**Maintainer**: Database Development Team  
**Database**: SQL Server 2017 (Consolidated Architecture)
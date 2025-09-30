# Database Migration Summary: PostgreSQL to SQL Server

## Overview
This document summarizes the complete migration of the Global ID Management System from PostgreSQL to SQL Server with database consolidation.

## Migration Details

### Original Architecture
- **Database System**: PostgreSQL 12+
- **Architecture**: Dual database (`global_id_db` and `pegawai_db`)
- **Driver**: `psycopg2-binary`
- **Schema**: `public` schema
- **Special Features**: JSONB, LISTEN/NOTIFY, PostgreSQL-specific triggers

### New Architecture
- **Database System**: SQL Server
- **Architecture**: Single consolidated database (`dbvendor`)
- **Driver**: `pyodbc` with ODBC Driver 17 for SQL Server
- **Schema**: `dbo` schema
- **Connection**: Via SSH tunnel (localhost:1435)

## Files Modified

### 1. Dependencies (`requirements.txt`)
- **Removed**: `psycopg2-binary==2.9.9`
- **Added**: `pyodbc==4.0.39`

### 2. Configuration Files
- **`.env`**: Updated database connection strings and credentials
- **`.env.example`**: Updated template with SQL Server configuration

### 3. Database Configuration (`app/models/database.py`)
- Updated connection URLs to use `mssql+pyodbc://` protocol
- Added SQL Server-specific connection parameters
- Added timeout and autocommit configurations

### 4. Models (`app/models/models.py`)
- Replaced `JSONB` with `JSON` for SQL Server compatibility
- Updated all `__tablename__` to include `dbo.` schema prefix
- Changed from `postgresql` dialect imports to generic types

### 5. API Routes (`app/api/routes.py`)
- Updated database explorer to show single consolidated database
- Changed schema references from `'public'` to `'dbo'`
- Updated table references to use `dbo.` prefix
- Consolidated dual database display into single database view

### 6. Monitoring Service (`app/services/monitoring_service.py`)
- Replaced PostgreSQL LISTEN/NOTIFY with polling-based monitoring
- Removed `psycopg2` dependencies
- Updated trigger creation to use SQL Server compatible approach

### 7. Advanced Workflow Service (`app/services/advanced_workflow_service.py`)
- Updated database reference comments from `pegawai_db` to `pegawai table`
- Updated audit log messages to reflect consolidated architecture

### 8. Dummy Data Generator (`scripts/generate_dummy_data.py`)
- Updated connection string to use SQL Server

### 9. SQL Schema Files
- **Created**: `sql/create_schema_sqlserver.sql` - New SQL Server schema
- **Updated**: `sql/README.md` - Updated with SQL Server instructions

### 10. Documentation (`README.md`)
- Updated technology stack section
- Replaced PostgreSQL setup with SQL Server + SSH tunnel instructions
- Updated environment configuration examples
- Added ODBC driver requirements
- Updated both English and Indonesian sections

## Key Technical Changes

### Database Connection
```python
# Old (PostgreSQL)
DATABASE_URL = "postgresql://postgres:123@localhost:5432/global_id_db"
SOURCE_DATABASE_URL = "postgresql://postgres:123@localhost:5432/pegawai_db"

# New (SQL Server)
DATABASE_URL = "mssql+pyodbc://sqlvendor1:1U~xO`\\2Un-gGqmPj@localhost:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server"
SOURCE_DATABASE_URL = "mssql+pyodbc://sqlvendor1:1U~xO`\\2Un-gGqmPj@localhost:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server"
```

### Schema Changes
```sql
-- Old (PostgreSQL)
CREATE TABLE global_id (...)
SELECT * FROM information_schema.tables WHERE table_schema = 'public'

-- New (SQL Server)  
CREATE TABLE dbo.global_id (...)
SELECT * FROM information_schema.tables WHERE table_schema = 'dbo'
```

### Data Types
```python
# Old (PostgreSQL-specific)
from sqlalchemy.dialects.postgresql import JSONB
old_values = Column(JSONB)

# New (Generic SQL Server compatible)
from sqlalchemy import JSON
old_values = Column(JSON)
```

### Monitoring Approach
```python
# Old (PostgreSQL LISTEN/NOTIFY)
conn.execute("LISTEN pegawai_changes;")
while conn.notifies:
    # Process notifications

# New (Polling-based)
while True:
    # Check for changes via polling
    await asyncio.sleep(5)
```

## Connection Requirements

### SSH Tunnel Setup
```bash
gcloud compute ssh gcp-hr-applications --project hris-292403 --zone asia-southeast2-a --ssh-flag="-L 1435:10.182.128.3:1433"
```

### Database Credentials
- **Host**: `localhost` (via tunnel)
- **Port**: `1435`
- **Database**: `dbvendor`
- **User**: `sqlvendor1`
- **Password**: `1U~xO\`2Un-gGqmPj`

## Testing Requirements

### Prerequisites for Testing
1. **ODBC Driver**: Install "ODBC Driver 17 for SQL Server"
2. **SSH Access**: Ensure gcloud CLI is configured
3. **Network**: Verify SSH tunnel connectivity
4. **Dependencies**: Run `pip install -r requirements.txt`

### Verification Steps
1. Establish SSH tunnel
2. Test database connection with `sqlcmd`
3. Run schema creation script
4. Test application startup
5. Verify all database operations

## Backward Compatibility
- **Breaking Change**: This migration is not backward compatible with PostgreSQL
- **Data Migration**: Manual data migration required from old PostgreSQL databases
- **Configuration**: All `.env` files need updating

## Notes and Considerations
- Real-time monitoring changed from event-driven (LISTEN/NOTIFY) to polling-based
- JSON handling may behave differently between PostgreSQL JSONB and SQL Server JSON
- Performance characteristics may differ; monitoring recommended
- Error handling may need adjustments for SQL Server-specific error codes
- Backup and recovery procedures need updating for SQL Server
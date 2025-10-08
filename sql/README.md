# SQL Database Scripts

This folder contains SQL scripts for setting up and managing the Global ID Management System database on **SQL Server**.

## Files:

### `create_schema_sqlserver.sql` 
**🚀 MAIN SQL SERVER DATABASE SETUP SCRIPT**
- Creates consolidated `g_id` database (replaces dual database architecture)
- Creates all tables with proper indexes and constraints (global_id, global_id_non_database, pegawai, audit_log, g_id_sequence)
- Sets up triggers for automatic timestamp updates using SQL Server syntax
- Creates audit logging system
- **Usage**: Run this script to set up the complete SQL Server database system from scratch

### `create_schema.sql` 
**�️ LEGACY POSTGRESQL SCRIPT (DEPRECATED)**
- Original PostgreSQL setup script
- Kept for reference only
- **DO NOT USE** - This is for PostgreSQL, not SQL Server

## Quick Setup (SQL Server):

### Prerequisites:
1. **SSH Tunnel**: Establish SSH tunnel to SQL Server
   ```bash
   gcloud compute ssh gcp-hr-applications --project hris-292403 --zone asia-southeast2-a --ssh-flag="-L 1435:10.182.128.3:1433"
   ```

2. **SQL Server Setup**:
   ```sql
   -- Run in SQL Server Management Studio or sqlcmd
   sqlcmd -S localhost,1435 -U sqlvendor1 -P "1U~xO\`2Un-gGqmPj" -i create_schema_sqlserver.sql
   ```

## Database Structure (Consolidated):

- **g_id**: Single consolidated SQL Server database containing:
  - `dbo.global_id`: Main Global ID records
  - `dbo.global_id_non_database`: Excel/manual Global ID records  
  - `dbo.pegawai`: Employee records
  - `dbo.audit_log`: System audit trail
  - `dbo.g_id_sequence`: Global ID sequence management

## Migration Notes:
- **BREAKING CHANGE**: Migrated from PostgreSQL dual-database to SQL Server single-database architecture
- All tables now use `dbo.` schema prefix
- JSON columns converted from JSONB (PostgreSQL) to NVARCHAR(MAX) (SQL Server)
- LISTEN/NOTIFY replaced with polling-based monitoring
- All queries updated for SQL Server compatibility
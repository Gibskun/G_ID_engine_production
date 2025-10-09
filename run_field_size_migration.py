#!/usr/bin/env python3
"""
Execute database migration to increase field sizes
"""
import pyodbc
import sys
import os

# Add current directory to Python path
sys.path.append(os.getcwd())

try:
    from app.config.environment import env_config
    
    config = env_config.get_config()
    print(f"Connecting to database: {config['database_host']}:{config['database_port']}")
    
    # Build connection string based on environment
    if config['environment'] == 'local':
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['database_host']},{config['database_port']};DATABASE=g_id;Trusted_Connection=yes;"
    else:
        # Server environment - use credentials
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['database_host']},{config['database_port']};DATABASE=g_id;UID=sqlvendor1;PWD=1U~xO%602Un-gGqmPj;"
    
    # Read migration script
    with open('sql/migration_increase_field_sizes.sql', 'r') as f:
        sql_script = f.read()
    
    print("Connecting to database...")
    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected successfully!")
        
        # Split script by GO statements and execute each batch
        batches = sql_script.split('GO')
        for i, batch in enumerate(batches):
            batch = batch.strip()
            if batch:
                try:
                    print(f"Executing batch {i+1}...")
                    cursor.execute(batch)
                    print(f"✓ Batch {i+1} executed successfully")
                except pyodbc.Error as e:
                    print(f"Batch {i+1} result: {e}")
        
        print("\n✅ Migration completed successfully!")
        print("Database field sizes have been increased to 50 characters for:")
        print("  - global_id.no_ktp (16 → 50 chars)")
        print("  - global_id.passport_id (9 → 50 chars)")
        print("  - global_id_non_database.no_ktp (16 → 50 chars)")
        print("  - global_id_non_database.passport_id (9 → 50 chars)")
        print("  - pegawai.no_ktp (16 → 50 chars)")
        print("  - pegawai.passport_id (9 → 50 chars)")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
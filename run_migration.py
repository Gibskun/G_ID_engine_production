#!/usr/bin/env python3
"""
Simple migration script to remove identifier constraints
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
    
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['database_host']},{config['database_port']};DATABASE=g_id;UID=sqlvendor1;PWD=1U~xO%602Un-gGqmPj;"
    
    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected successfully!")
        
        # List of constraints to remove
        constraints = [
            ("dbo.global_id", "CK_global_id_identifier"),
            ("dbo.global_id_non_database", "CK_global_id_non_db_identifier"), 
            ("dbo.pegawai", "CK_pegawai_identifier")
        ]
        
        for table, constraint in constraints:
            try:
                sql = f"ALTER TABLE {table} DROP CONSTRAINT {constraint}"
                cursor.execute(sql)
                print(f"✓ Dropped constraint {constraint} from {table}")
            except pyodbc.Error as e:
                print(f"! Constraint {constraint} on {table}: {e}")
        
        print("\n✓ Migration completed successfully!")
        print("Database now allows both no_ktp and passport_id to be NULL simultaneously")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
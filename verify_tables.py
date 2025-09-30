#!/usr/bin/env python3
"""
Quick verification script to check if tables were created successfully
"""

import pyodbc
from dotenv import load_dotenv

load_dotenv()

def verify_tables():
    """Check if all required tables exist"""
    
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER=127.0.0.1,1435;"
        f"DATABASE=dbvendor;"
        f"UID=sqlvendor1;"
        f"PWD=1U~xO`2Un-gGqmPj;"
        f"TrustServerCertificate=yes;"
    )
    
    required_tables = ['global_id', 'global_id_non_database', 'pegawai', 'g_id_sequence', 'audit_log']
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        print("🔍 Checking database tables...")
        
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Found {len(existing_tables)} tables:")
        for table in existing_tables:
            status = "✅" if table in required_tables else "❓"
            print(f"   {status} {table}")
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print(f"\n✅ All required tables exist!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    verify_tables()
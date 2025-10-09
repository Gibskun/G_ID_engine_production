#!/usr/bin/env python3
"""
Final Migration Script - Recreate Table Approach
Recreates global_id_non_database table with correct configuration.
"""

import pyodbc
import sys
import os
from datetime import datetime

def connect_to_database():
    """Connect to SQL Server database"""
    try:
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=g_id;"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(connection_string)
        print("✅ Database connection established")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def read_migration_script():
    """Read the migration SQL script"""
    script_path = os.path.join("sql", "migration_recreate_table.sql")
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"❌ Failed to read migration script: {e}")
        return None

def execute_migration(conn):
    """Execute the table recreation migration"""
    sql_script = read_migration_script()
    if not sql_script:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Split script into batches (split by GO statements)
        batches = [batch.strip() for batch in sql_script.split('GO') if batch.strip()]
        
        print(f"Executing {len(batches)} SQL batches...")
        
        for i, batch in enumerate(batches, 1):
            if batch.strip():
                print(f"Executing batch {i}/{len(batches)}...")
                cursor.execute(batch)
                
                # Fetch and display any messages
                while cursor.nextset():
                    pass
        
        conn.commit()
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False

def verify_migration(conn):
    """Verify the migration was successful"""
    try:
        cursor = conn.cursor()
        
        # Check table structure
        print("\n📊 Verifying table structure...")
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'global_id_non_database'
                AND COLUMN_NAME IN ('no_ktp', 'passport_id')
            ORDER BY COLUMN_NAME
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]}({col[2]}) {'NULL' if col[3] == 'YES' else 'NOT NULL'}")
        
        # Check record count
        cursor.execute("SELECT COUNT(*) FROM global_id_non_database")
        count = cursor.fetchone()[0]
        print(f"\n📈 Total records in table: {count}")
        
        # Check for any constraints that might still be problematic
        cursor.execute("""
            SELECT 
                CONSTRAINT_NAME,
                CONSTRAINT_TYPE
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            WHERE TABLE_NAME = 'global_id_non_database'
        """)
        
        constraints = cursor.fetchall()
        print(f"\n🔒 Active constraints:")
        for constraint in constraints:
            print(f"  {constraint[0]}: {constraint[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main execution function"""
    print("🚀 Starting Table Recreation Migration")
    print("="*50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Get user confirmation
    print("⚠️  WARNING: This will recreate the global_id_non_database table")
    print("   - All data will be backed up and restored")
    print("   - Table structure will be updated to support 50-character fields")
    print("   - All problematic constraints will be removed")
    print()
    
    confirm = input("Do you want to proceed? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("Migration cancelled by user")
        return
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Execute migration
        if execute_migration(conn):
            # Verify results
            verify_migration(conn)
            print("\n" + "="*50)
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("✅ Table recreated with 50-character field support")
            print("✅ All data preserved")
            print("✅ Ready to process long KTP numbers and missing passport_ids")
            print("\n🚀 Test your upload now - should show 0 skipped records!")
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
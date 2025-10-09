#!/usr/bin/env python3
"""
Execute the final migration that handles all specific dependencies
"""
import subprocess
import os

def run_final_migration():
    """Run the final migration script"""
    print("🔧 FINAL MIGRATION - DEPENDENCY HANDLER")
    print("="*60)
    print("This will:")
    print("1. Drop specific indexes: IX_global_id_non_db_passport_id_unique")
    print("2. Drop constraint: CK_global_id_non_db_identifier") 
    print("3. Increase field sizes to 50 characters")
    print("4. Verify the changes")
    print()
    
    sql_file = "sql/migration_final_fix.sql"
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    print(f"📁 Found migration file: {sql_file}")
    print("🚀 Run this command on your server:")
    print()
    print("   sqlcmd -S your_server_name -d g_id -E -i sql/migration_final_fix.sql")
    print()
    print("Or copy and paste this SQL into your SQL Server Management Studio:")
    print("-" * 60)
    
    # Read and display the SQL content
    try:
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Display the key parts
        print("-- Key commands to run:")
        print("USE g_id;")
        print()
        print("-- 1. Drop blocking dependencies")
        print("DROP INDEX IX_global_id_non_db_passport_id_unique ON dbo.global_id_non_database;")
        print("DROP INDEX IX_global_id_non_database_passport_id_unique ON dbo.global_id_non_database;")
        print("ALTER TABLE dbo.global_id_non_database DROP CONSTRAINT CK_global_id_non_db_identifier;")
        print()
        print("-- 2. Increase field sizes")
        print("ALTER TABLE dbo.global_id_non_database ALTER COLUMN no_ktp NVARCHAR(50) NULL;")
        print("ALTER TABLE dbo.global_id_non_database ALTER COLUMN passport_id NVARCHAR(50) NULL;")
        print()
        print("-- 3. Verify changes")
        print("SELECT COLUMN_NAME, CHARACTER_MAXIMUM_LENGTH")
        print("FROM INFORMATION_SCHEMA.COLUMNS") 
        print("WHERE TABLE_NAME = 'global_id_non_database'")
        print("  AND COLUMN_NAME IN ('no_ktp', 'passport_id');")
        print()
        print("-" * 60)
        print()
        print("📋 Expected Result After Migration:")
        print("COLUMN_NAME    CHARACTER_MAXIMUM_LENGTH")
        print("no_ktp         50")
        print("passport_id    50")
        print()
        print("🎉 After this migration succeeds:")
        print("✅ 0 skipped records (instead of 679)")
        print("✅ Long KTP numbers accepted (640.303.261.072.0002)")
        print("✅ 'nan' values cleaned to NULL")
        print("✅ No auto-generation of passport IDs")
        print("✅ Both identifier fields can be empty")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return False

if __name__ == "__main__":
    run_final_migration()
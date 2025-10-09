#!/usr/bin/env python3
"""
Server Update Verification Script
Check if the server has the latest code and database schema
"""

import pyodbc
import sys
import os

def check_database_schema():
    """Check if database has been updated to support 50-character fields"""
    try:
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=g_id;"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        print("🔍 Checking database schema...")
        
        # Check column sizes for all tables
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE COLUMN_NAME IN ('no_ktp', 'passport_id')
                AND TABLE_NAME IN ('global_id', 'global_id_non_database', 'pegawai')
            ORDER BY TABLE_NAME, COLUMN_NAME
        """)
        
        schema_results = cursor.fetchall()
        
        print("\n📋 Current Database Schema:")
        print("-" * 70)
        print(f"{'Table':<25} {'Column':<15} {'Type':<12} {'Max Len':<8} {'Nullable'}")
        print("-" * 70)
        
        all_updated = True
        for row in schema_results:
            table, column, data_type, max_len, nullable = row
            status = "✅" if max_len == 50 else "❌"
            if max_len != 50:
                all_updated = False
            
            print(f"{status} {table:<23} {column:<15} {data_type:<12} {max_len or 'N/A':<8} {nullable}")
        
        print("-" * 70)
        
        if all_updated:
            print("✅ Database schema is UPDATED - all fields support 50 characters")
        else:
            print("❌ Database schema needs UPDATE - some fields still limited to old sizes")
            print("\n🔧 Run the table recreation script to fix this:")
            print("   python run_table_recreation.py")
        
        conn.close()
        return all_updated
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_code_version():
    """Check if the code has the latest validation logic"""
    print("\n🔍 Checking code version...")
    
    try:
        # Check excel_service.py for new validation logic
        service_file = "app/services/excel_service.py"
        if os.path.exists(service_file):
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for old validation patterns
            old_patterns = [
                "must be exactly 16",
                "exceeds database limit",
                "AUTO-GENERATED",
                "_generate_passport_id"
            ]
            
            found_old = []
            for pattern in old_patterns:
                if pattern in content:
                    found_old.append(pattern)
            
            if found_old:
                print("❌ OLD validation logic found in code:")
                for pattern in found_old:
                    print(f"   - {pattern}")
                return False
            else:
                print("✅ Code has UPDATED validation logic - no restrictions")
                return True
        else:
            print("❌ excel_service.py not found")
            return False
            
    except Exception as e:
        print(f"❌ Code check failed: {e}")
        return False

def main():
    print("🚀 SERVER UPDATE VERIFICATION")
    print("=" * 50)
    
    code_ok = check_code_version()
    db_ok = check_database_schema()
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY:")
    
    if code_ok and db_ok:
        print("🎉 EVERYTHING IS UPDATED!")
        print("✅ Code: Latest validation logic (no restrictions)")
        print("✅ Database: 50-character field support")
        print("\n🔄 RESTART YOUR SERVER APPLICATION to load new code")
        print("   After restart, upload should show 0 skipped records!")
        
    elif code_ok and not db_ok:
        print("⚠️  CODE IS UPDATED, DATABASE NEEDS UPDATE")
        print("✅ Code: Latest validation logic")
        print("❌ Database: Still has old field sizes")
        print("\n🔧 RUN DATABASE UPDATE:")
        print("   python run_table_recreation.py")
        
    elif not code_ok and db_ok:
        print("⚠️  DATABASE IS UPDATED, CODE NEEDS UPDATE")
        print("❌ Code: Still has old validation logic")
        print("✅ Database: 50-character field support")
        print("\n🔧 UPDATE YOUR CODE FILES on the server")
        
    else:
        print("❌ BOTH CODE AND DATABASE NEED UPDATES")
        print("❌ Code: Still has old validation logic")
        print("❌ Database: Still has old field sizes")
        print("\n🔧 COMPLETE UPDATE NEEDED:")
        print("   1. Update code files on server")
        print("   2. Run: python run_table_recreation.py")
        print("   3. Restart server application")

if __name__ == "__main__":
    main()
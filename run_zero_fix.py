#!/usr/bin/env python3
"""
Fix Duplicate Zero Values Issue
Removes unique constraints that prevent multiple '0' passport_id values
"""

import pyodbc
import sys
import os

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

def run_zero_fix():
    """Execute the zero value fix script"""
    conn = connect_to_database()
    if not conn:
        return False
    
    try:
        # Read the SQL script
        script_path = os.path.join("sql", "fix_duplicate_zero_values.sql")
        with open(script_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
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
        print("✅ Zero value fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    print("🔧 FIXING DUPLICATE ZERO VALUES ISSUE")
    print("=" * 50)
    print("This will:")
    print("1. Remove unique constraints causing '0' value conflicts")
    print("2. Convert existing '0' values to NULL")
    print("3. Create conditional unique indexes (excluding '0' values)")
    print()
    
    if run_zero_fix():
        print("\n" + "=" * 50)
        print("🎉 FIX COMPLETED SUCCESSFULLY!")
        print("✅ Database updated to handle multiple '0' passport_id values")
        print("✅ Your upload should now process ALL records")
        print("\n🚀 RESTART YOUR SERVER AND RETRY UPLOAD!")
        print("   All records with passport_id='0' will be treated as empty/NULL")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
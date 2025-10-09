#!/usr/bin/env python3
"""
Update source columns to "SAP" for the entire system
- Add source column to pegawai table if it doesn't exist
- Update all global_id records to have source = "SAP"
- Update all pegawai records to have source = "SAP"
"""

import pyodbc
import sys
import os
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.getcwd())

def connect_to_database():
    """Connect to SQL Server database using environment config"""
    try:
        from app.config.environment import env_config
        
        config = env_config.get_config()
        print(f"Connecting to database: {config['database_host']}:{config['database_port']}")
        
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['database_host']},{config['database_port']};DATABASE=g_id;UID=sqlvendor1;PWD=1U~xO%602Un-gGqmPj;"
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        sys.exit(1)

def add_source_column_to_pegawai(cursor):
    """Add source column to pegawai table if it doesn't exist"""
    try:
        # Check if source column exists in pegawai table
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'pegawai' 
            AND COLUMN_NAME = 'source'
        """)
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("📝 Adding source column to pegawai table...")
            cursor.execute("""
                ALTER TABLE dbo.pegawai 
                ADD source NVARCHAR(20) NOT NULL DEFAULT 'SAP'
            """)
            print("✅ Source column added to pegawai table")
        else:
            print("✅ Source column already exists in pegawai table")
            
        return True
    except Exception as e:
        print(f"❌ Error adding source column to pegawai: {e}")
        return False

def update_global_id_source(cursor):
    """Update all global_id records to have source = 'SAP'"""
    try:
        print("📝 Updating global_id table source to 'SAP'...")
        
        # Update all records in global_id table
        cursor.execute("""
            UPDATE dbo.global_id 
            SET source = 'SAP',
                updated_at = GETDATE()
        """)
        
        updated_count = cursor.rowcount
        print(f"✅ Updated {updated_count} records in global_id table to source='SAP'")
        
        return True
    except Exception as e:
        print(f"❌ Error updating global_id source: {e}")
        return False

def update_pegawai_source(cursor):
    """Update all pegawai records to have source = 'SAP'"""
    try:
        print("📝 Updating pegawai table source to 'SAP'...")
        
        # Update all records in pegawai table
        cursor.execute("""
            UPDATE dbo.pegawai 
            SET source = 'SAP',
                updated_at = GETDATE()
            WHERE deleted_at IS NULL
        """)
        
        updated_count = cursor.rowcount
        print(f"✅ Updated {updated_count} records in pegawai table to source='SAP'")
        
        return True
    except Exception as e:
        print(f"❌ Error updating pegawai source: {e}")
        return False

def verify_updates(cursor):
    """Verify the updates were successful"""
    try:
        print("\n📊 Verification Results:")
        print("-" * 50)
        
        # Check global_id table
        cursor.execute("SELECT COUNT(*) FROM dbo.global_id WHERE source = 'SAP'")
        global_id_sap_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dbo.global_id")
        global_id_total_count = cursor.fetchone()[0]
        
        print(f"📋 global_id table:")
        print(f"   Total records: {global_id_total_count}")
        print(f"   Records with source='SAP': {global_id_sap_count}")
        
        # Check pegawai table
        cursor.execute("SELECT COUNT(*) FROM dbo.pegawai WHERE source = 'SAP' AND deleted_at IS NULL")
        pegawai_sap_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dbo.pegawai WHERE deleted_at IS NULL")
        pegawai_total_count = cursor.fetchone()[0]
        
        print(f"📋 pegawai table:")
        print(f"   Total active records: {pegawai_total_count}")
        print(f"   Records with source='SAP': {pegawai_sap_count}")
        
        # Check if pegawai has source column
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'pegawai' 
            AND COLUMN_NAME = 'source'
        """)
        
        pegawai_has_source = cursor.fetchone()[0] > 0
        print(f"📋 pegawai source column exists: {'✅ Yes' if pegawai_has_source else '❌ No'}")
        
        return True
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def main():
    """Main function to update source columns"""
    print("🚀 Starting SAP Source Update Process")
    print("=" * 50)
    
    # Connect to database
    conn = connect_to_database()
    cursor = conn.cursor()
    
    success = True
    
    try:
        # Step 1: Add source column to pegawai table
        if not add_source_column_to_pegawai(cursor):
            success = False
        
        # Step 2: Update global_id source
        if not update_global_id_source(cursor):
            success = False
        
        # Step 3: Update pegawai source
        if not update_pegawai_source(cursor):
            success = False
        
        if success:
            # Commit all changes
            conn.commit()
            print("\n✅ All updates committed successfully!")
            
            # Verify the changes
            verify_updates(cursor)
            
        else:
            # Rollback on any error
            conn.rollback()
            print("\n❌ Updates failed - all changes rolled back")
            
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Unexpected error: {e}")
        print("All changes have been rolled back")
        
    finally:
        cursor.close()
        conn.close()
        
    if success:
        print(f"\n🎉 SAP Source Update completed successfully!")
        print("📝 Next steps:")
        print("   1. Update the database_explorer.html to show 'Export SAP'")
        print("   2. Create new export endpoint for pegawai table")
        print("   3. Remove 'Include Empty Passport_ID' option")
    else:
        print(f"\n💥 SAP Source Update failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
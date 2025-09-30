#!/usr/bin/env python3
"""
First-time database table creation script
This script creates all necessary tables for the Global ID Management System
"""

import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables_first_time():
    """Create all tables for the first time"""
    
    # Connection string
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER=127.0.0.1,1435;"
        f"DATABASE=master;"  # Connect to master first
        f"UID=sqlvendor1;"
        f"PWD=1U~xO`2Un-gGqmPj;"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )
    
    try:
        print("🔗 Connecting to SQL Server...")
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Step 1: Create database
        print("📦 Creating database 'dbvendor'...")
        cursor.execute("""
            IF EXISTS (SELECT name FROM sys.databases WHERE name = 'dbvendor')
            BEGIN
                ALTER DATABASE dbvendor SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                DROP DATABASE dbvendor;
            END
        """)
        cursor.execute("CREATE DATABASE dbvendor")
        conn.commit()
        
        # Step 2: Switch to dbvendor database
        cursor.execute("USE dbvendor")
        conn.commit()
        
        # Step 3: Create tables
        print("🏗️ Creating tables...")
        
        # Global_ID table
        cursor.execute("""
            CREATE TABLE dbo.global_id (
                g_id NVARCHAR(10) PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                personal_number NVARCHAR(15),
                no_ktp NVARCHAR(16) NOT NULL UNIQUE,
                bod DATE,
                status NVARCHAR(15) NOT NULL DEFAULT 'Active',
                source NVARCHAR(20) NOT NULL DEFAULT 'database_pegawai',
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                CONSTRAINT chk_status CHECK (status IN ('Active', 'Non Active')),
                CONSTRAINT chk_source CHECK (source IN ('database_pegawai', 'excel'))
            )
        """)
        print("   ✅ global_id table created")
        
        # Global_ID_NON_Database table
        cursor.execute("""
            CREATE TABLE dbo.global_id_non_database (
                g_id NVARCHAR(10) PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                personal_number NVARCHAR(15),
                no_ktp NVARCHAR(16) NOT NULL UNIQUE,
                bod DATE,
                status NVARCHAR(15) NOT NULL DEFAULT 'Active',
                source NVARCHAR(20) NOT NULL DEFAULT 'excel',
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                CONSTRAINT chk_ndb_status CHECK (status IN ('Active', 'Non Active')),
                CONSTRAINT chk_ndb_source CHECK (source IN ('database_pegawai', 'excel'))
            )
        """)
        print("   ✅ global_id_non_database table created")
        
        # Pegawai table
        cursor.execute("""
            CREATE TABLE dbo.pegawai (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                personal_number NVARCHAR(15),
                no_ktp NVARCHAR(16) NOT NULL UNIQUE,
                bod DATE,
                g_id NVARCHAR(10),
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                deleted_at DATETIME2,
                FOREIGN KEY (g_id) REFERENCES dbo.global_id(g_id)
            )
        """)
        print("   ✅ pegawai table created")
        
        # G_ID_Sequence table
        cursor.execute("""
            CREATE TABLE dbo.g_id_sequence (
                id INT IDENTITY(1,1) PRIMARY KEY,
                current_year INT NOT NULL,
                current_digit INT NOT NULL,
                current_alpha_1 CHAR(1) NOT NULL,
                current_alpha_2 CHAR(1) NOT NULL,
                current_number INT NOT NULL,
                created_at DATETIME2 DEFAULT GETDATE(),
                updated_at DATETIME2 DEFAULT GETDATE(),
                CONSTRAINT chk_digit_range CHECK (current_digit >= 0 AND current_digit <= 9),
                CONSTRAINT chk_alpha_1 CHECK (current_alpha_1 >= 'A' AND current_alpha_1 <= 'Z'),
                CONSTRAINT chk_alpha_2 CHECK (current_alpha_2 >= 'A' AND current_alpha_2 <= 'Z'),
                CONSTRAINT chk_number_range CHECK (current_number >= 0 AND current_number <= 99)
            )
        """)
        print("   ✅ g_id_sequence table created")
        
        # Audit_Log table
        cursor.execute("""
            CREATE TABLE dbo.audit_log (
                id INT IDENTITY(1,1) PRIMARY KEY,
                table_name NVARCHAR(50) NOT NULL,
                record_id NVARCHAR(50),
                action NVARCHAR(20) NOT NULL,
                old_values NVARCHAR(MAX),
                new_values NVARCHAR(MAX),
                changed_by NVARCHAR(100),
                change_reason NVARCHAR(MAX),
                created_at DATETIME2 DEFAULT GETDATE(),
                CONSTRAINT chk_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'SYNC'))
            )
        """)
        print("   ✅ audit_log table created")
        
        # Step 4: Insert initial data
        print("📊 Inserting initial data...")
        
        # Initialize G_ID sequence
        cursor.execute("""
            INSERT INTO dbo.g_id_sequence (current_year, current_digit, current_alpha_1, current_alpha_2, current_number)
            VALUES (25, 0, 'A', 'A', 0)
        """)
        
        # Insert sample pegawai data
        cursor.execute("""
            INSERT INTO dbo.pegawai (name, personal_number, no_ktp, bod) VALUES
            ('Ahmad Budi Santoso', 'EMP-2025-0001', '3201234567890001', '1985-05-15'),
            ('Siti Aminah', 'EMP-2025-0002', '3201234567890002', '1987-08-20'),
            ('Rudi Hartono', 'EMP-2025-0003', '3201234567890003', '1990-12-10')
        """)
        
        conn.commit()
        print("   ✅ Initial data inserted")
        
        # Step 5: Verify tables
        print("🔍 Verifying tables...")
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo' 
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        print("   📋 Created tables:")
        for table in tables:
            print(f"      - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("📌 Next steps:")
        print("   1. Update your .env file with database credentials")
        print("   2. Run: python main.py")
        print("   3. Open: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Global ID Management System - First Time Setup")
    print("=" * 50)
    
    success = create_tables_first_time()
    if success:
        print("\n✅ Setup complete! Your database is ready to use.")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
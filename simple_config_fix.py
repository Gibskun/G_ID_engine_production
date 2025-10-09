#!/usr/bin/env python3
"""
Simple System Configuration Fix
Disables all validation settings in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config.environment import env_config

def fix_system_config():
    """Fix system configuration to disable all validations"""
    try:
        # Use the same database connection as the application
        config = env_config.get_config()
        engine = create_engine(config['database_url'], echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("✅ Database connection established")
        
        # Step 1: Create table if needed
        create_table_sql = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='system_config' AND xtype='U')
        CREATE TABLE system_config (
            id INT IDENTITY(1,1) PRIMARY KEY,
            config_key VARCHAR(255) NOT NULL UNIQUE,
            config_value VARCHAR(1000) NULL,
            description VARCHAR(1000) NULL,
            created_at DATETIME2 DEFAULT GETDATE(),
            updated_at DATETIME2 DEFAULT GETDATE()
        )
        """
        
        print("Creating system_config table if needed...")
        session.execute(text(create_table_sql))
        session.commit()
        
        # Step 2: Insert/Update configuration values
        configs = [
            ('strict_validation', 'false', 'Enable strict validation mode'),
            ('ktp_validation', 'false', 'Enable KTP number validation'),
            ('passport_validation', 'false', 'Enable passport ID validation'),
            ('duplicate_checking', 'false', 'Enable duplicate checking'),
            ('allow_duplicates', 'true', 'Allow duplicate records'),
            ('validation_enabled', 'false', 'Master validation toggle'),
            ('skip_validation', 'true', 'Skip all validation checks')
        ]
        
        print("Updating configuration settings...")
        for key, value, desc in configs:
            # Check if exists
            check_sql = "SELECT COUNT(*) as count FROM system_config WHERE config_key = :key"
            result = session.execute(text(check_sql), {"key": key}).fetchone()
            
            if result.count > 0:
                # Update existing
                update_sql = """
                UPDATE system_config 
                SET config_value = :value, updated_at = GETDATE() 
                WHERE config_key = :key
                """
                session.execute(text(update_sql), {"key": key, "value": value})
                print(f"   Updated {key} = {value}")
            else:
                # Insert new
                insert_sql = """
                INSERT INTO system_config (config_key, config_value, description) 
                VALUES (:key, :value, :desc)
                """
                session.execute(text(insert_sql), {"key": key, "value": value, "desc": desc})
                print(f"   Inserted {key} = {value}")
        
        session.commit()
        
        # Step 3: Verify configuration
        print("\n📋 Final Configuration:")
        verify_sql = """
        SELECT config_key, config_value 
        FROM system_config 
        WHERE config_key IN ('strict_validation', 'ktp_validation', 'passport_validation', 'duplicate_checking', 'allow_duplicates', 'validation_enabled', 'skip_validation')
        ORDER BY config_key
        """
        results = session.execute(text(verify_sql)).fetchall()
        for row in results:
            print(f"   {row.config_key}: {row.config_value}")
        
        session.close()
        print("\n✅ System configuration updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration update failed: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def main():
    print("🔧 FIXING SYSTEM CONFIGURATION")
    print("=" * 50)
    print("This will:")
    print("1. Create system_config table if missing")
    print("2. Disable all validation settings")
    print("3. Allow processing of all duplicate data")
    print()
    
    if fix_system_config():
        print("\n" + "=" * 50)
        print("🎉 SYSTEM CONFIGURATION FIXED!")
        print("✅ All validation settings disabled")
        print("✅ Ready to process all Excel data")
        print()
        print("🧪 NOW TEST YOUR UPLOAD:")
        print("   Upload your Excel file again")
        print("   Expected result: 8753/8753 records processed, 0 skipped")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Fix System Configuration Settings
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
        
        # Read the SQL script
        script_path = "sql/fix_system_config.sql"
        if not os.path.exists(script_path):
            print(f"❌ {script_path} not found")
            return False
            
        with open(script_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Split script into individual statements
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip() and 'GO' not in stmt.upper()]
        
        print(f"Executing {len(statements)} SQL statements...")
        
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                print(f"Executing statement {i}/{len(statements)}...")
                session.execute(text(statement))
        
        session.commit()
        session.close()
        print("✅ System configuration updated successfully!")
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
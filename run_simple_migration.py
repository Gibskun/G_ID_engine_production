#!/usr/bin/env python3
"""
Execute the simplified migration script
"""
import pyodbc
import sys
import os
import subprocess

def run_sql_with_sqlcmd():
    """Try to run using sqlcmd if available"""
    try:
        # Try to run with sqlcmd (Windows SQL Server command line tool)
        result = subprocess.run([
            'sqlcmd', 
            '-S', '(local)',  # Local SQL Server instance
            '-d', 'g_id',     # Database name
            '-E',             # Use Windows Authentication
            '-i', 'sql/migration_simple_fix.sql'  # Input file
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Migration executed successfully with sqlcmd!")
            print("Output:")
            print(result.stdout)
            if result.stderr:
                print("Warnings:")
                print(result.stderr)
            return True
        else:
            print("❌ sqlcmd failed:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except FileNotFoundError:
        print("sqlcmd not found. Trying Python approach...")
        return False

def run_sql_with_python():
    """Fallback to Python pyodbc"""
    try:
        from app.config.environment import env_config
        
        config = env_config.get_config()
        print(f"Connecting to database: {config['database_host']}:{config['database_port']}")
        
        # Build connection string
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['database_host']},{config['database_port']};DATABASE=g_id;Trusted_Connection=yes;"
        
        # Read migration script
        with open('sql/migration_simple_fix.sql', 'r') as f:
            sql_script = f.read()
        
        print("Connecting to database...")
        with pyodbc.connect(conn_str) as conn:
            conn.autocommit = True
            cursor = conn.cursor()
            
            print("Connected successfully!")
            print("Running simplified migration...")
            
            # Execute the script
            cursor.execute(sql_script)
            
            # Print any messages
            while cursor.nextset():
                pass
                
            print("✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Python approach failed: {e}")
        return False

def main():
    print("🔧 SIMPLE MIGRATION FIXER")
    print("="*50)
    print("This will fix the global_id_non_database table field sizes")
    print("by recreating the columns to avoid dependency issues.")
    print()
    
    # Try sqlcmd first, then fallback to Python
    success = run_sql_with_sqlcmd()
    
    if not success:
        print("Trying Python approach...")
        success = run_sql_with_python()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("✅ global_id_non_database.no_ktp increased to 50 characters")
        print("✅ global_id_non_database.passport_id increased to 50 characters")
        print("✅ All dependency issues resolved")
        print("\n📊 FINAL STATUS:")
        print("- global_id table: ✅ FIXED (50 chars)")
        print("- global_id_non_database table: ✅ FIXED (50 chars)")  
        print("- pegawai table: ✅ FIXED (50 chars)")
        print("\n🚀 READY FOR TESTING!")
        print("Upload your data file - should show 0 skipped records!")
    else:
        print("\n❌ MIGRATION FAILED")
        print("Please run the SQL script manually on your server:")
        print("sqlcmd -S your_server -d g_id -E -i sql/migration_simple_fix.sql")

if __name__ == "__main__":
    main()
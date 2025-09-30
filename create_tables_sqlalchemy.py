#!/usr/bin/env python3
"""
Create tables using SQLAlchemy models (for advanced users)
This method uses the existing model definitions
"""

import os
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add app to path
sys.path.append(os.path.dirname(__file__))

# Load environment
load_dotenv()

def create_tables_with_sqlalchemy():
    """Create tables using SQLAlchemy models"""
    
    try:
        # Import models after path setup
        from app.models.database import Base, engine
        from app.models.models import GlobalID, GlobalIDNonDatabase, Pegawai, GIDSequence, AuditLog
        
        print("🔗 Connecting to database with SQLAlchemy...")
        
        # Create all tables
        print("🏗️ Creating tables from models...")
        Base.metadata.drop_all(engine)  # Drop existing if any
        Base.metadata.create_all(engine)
        
        print("✅ All tables created successfully!")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema='dbo')
        
        print("📋 Created tables:")
        for table in sorted(tables):
            print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SQLAlchemy Table Creation")
    print("=" * 30)
    
    success = create_tables_with_sqlalchemy()
    if success:
        print("\n✅ Tables created successfully using SQLAlchemy!")
    else:
        print("\n❌ Failed to create tables.")
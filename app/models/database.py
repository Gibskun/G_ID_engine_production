"""
Database configuration and connection management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

# Database URLs - Both pointing to the same consolidated SQL Server database
DATABASE_URL = os.getenv("DATABASE_URL", "mssql+pyodbc://sqlvendor1:password@localhost:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server")
SOURCE_DATABASE_URL = os.getenv("SOURCE_DATABASE_URL", "mssql+pyodbc://sqlvendor1:password@localhost:1435/dbvendor?driver=ODBC+Driver+17+for+SQL+Server")

# Create engines with SQL Server specific settings
engine = create_engine(
    DATABASE_URL, 
    echo=True,
    pool_pre_ping=True,
    connect_args={
        "autocommit": False,
        "timeout": 30
    }
)
source_engine = create_engine(
    SOURCE_DATABASE_URL, 
    echo=True,
    pool_pre_ping=True,
    connect_args={
        "autocommit": False,
        "timeout": 30
    }
)

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SourceSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=source_engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get main database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_source_db():
    """Dependency to get source database session"""
    db = SourceSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=source_engine)
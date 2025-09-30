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

# Get performance configuration from environment
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "60"))

# Create engines with optimized performance settings
engine = create_engine(
    DATABASE_URL, 
    echo=False,  # Disable SQL logging in production for performance
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    connect_args={
        "autocommit": False,
        "timeout": QUERY_TIMEOUT
    }
)
source_engine = create_engine(
    SOURCE_DATABASE_URL, 
    echo=False,  # Disable SQL logging in production for performance
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    connect_args={
        "autocommit": False,
        "timeout": QUERY_TIMEOUT
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
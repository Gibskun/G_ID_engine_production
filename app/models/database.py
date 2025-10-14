"""
Database configuration and connection management with environment detection
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import urllib.parse

# Import environment configuration
try:
    from app.config.environment import env_config
except ImportError:
    # Fallback if environment config not available
    load_dotenv()
    env_config = None

# Get configuration from environment manager or fallback to env vars
if env_config:
    config = env_config.get_config()
    DATABASE_URL = config['database_url']
    SOURCE_DATABASE_URL = config['database_url']  # Same database for both
    POOL_SIZE = config['pool_size']
    MAX_OVERFLOW = config['max_overflow']
    POOL_TIMEOUT = config['pool_timeout']
    POOL_RECYCLE = config['pool_recycle']
    QUERY_TIMEOUT = config['query_timeout']
    
    # Print configuration for debugging
    env_config.print_config()
else:
    # Fallback configuration
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL", "mssql+pyodbc://sqlvendor1:1U~xO%602Un-gGqmPj@127.0.0.1:1435/gid_dev?driver=ODBC+Driver+17+for+SQL+Server")
    SOURCE_DATABASE_URL = os.getenv("SOURCE_DATABASE_URL", DATABASE_URL)
    POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "10"))
    POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "1800"))
    QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "30"))

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
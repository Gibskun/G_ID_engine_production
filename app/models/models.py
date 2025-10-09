"""
SQLAlchemy models for the Global ID system
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, func, CheckConstraint, UniqueConstraint, Text
from sqlalchemy.dialects.mssql import NVARCHAR
from sqlalchemy import JSON  # Generic JSON type for SQL Server compatibility
from app.models.database import Base
from datetime import datetime


class GlobalID(Base):
    """Main Global_ID table model"""
    __tablename__ = "global_id"
    # __table_args__ = {'schema': 'dbo'}  # Disabled for local testing

    g_id = Column(String(10), primary_key=True, nullable=False, name="g_id")
    name = Column(String(255), nullable=False)
    personal_number = Column(String(15))
    no_ktp = Column(String(16), nullable=False, unique=True, name="no_ktp")
    passport_id = Column(String(9), nullable=False, unique=True, name="passport_id")
    bod = Column(Date, name="bod")
    status = Column(String(15), nullable=False, default="Active", name="status")
    source = Column(String(20), nullable=False, default="database_pegawai")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GlobalID(g_id='{self.g_id}', name='{self.name}', status='{self.status}')>"


class GlobalIDNonDatabase(Base):
    """Global_ID_NON_Database table model - copy of Excel data"""
    __tablename__ = "global_id_non_database"
    # __table_args__ = {'schema': 'dbo'}  # Disabled for local testing

    g_id = Column(String(10), primary_key=True, nullable=False, name="g_id")
    name = Column(String(255), nullable=False)
    personal_number = Column(String(15))
    no_ktp = Column(String(16), nullable=False, unique=True, name="no_ktp")
    passport_id = Column(String(9), nullable=False, unique=True, name="passport_id")
    bod = Column(Date, name="bod")
    status = Column(String(15), nullable=False, default="Active", name="status")
    source = Column(String(20), nullable=False, default="excel")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GlobalIDNonDatabase(g_id='{self.g_id}', name='{self.name}')>"


class GIDSequence(Base):
    """G_ID sequence management table"""
    __tablename__ = "g_id_sequence"
    __table_args__ = (
        CheckConstraint("current_digit >= 0 AND current_digit <= 9", name='check_digit_range'),
        CheckConstraint("current_alpha_1 >= 'A' AND current_alpha_1 <= 'Z'", name='check_alpha_1'),
        CheckConstraint("current_alpha_2 >= 'A' AND current_alpha_2 <= 'Z'", name='check_alpha_2'),
        CheckConstraint("current_number >= 0 AND current_number <= 99", name='check_number_range'),
        # {'schema': 'dbo'}  # Disabled for local testing
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    current_year = Column(Integer, nullable=False)
    current_digit = Column(Integer, nullable=False)
    current_alpha_1 = Column(String(1), nullable=False)
    current_alpha_2 = Column(String(1), nullable=False)
    current_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GIDSequence(year={self.current_year}, digit={self.current_digit}, alpha={self.current_alpha_1}{self.current_alpha_2}, num={self.current_number})>"


class Pegawai(Base):
    """Source employee (pegawai) table model"""
    __tablename__ = "pegawai"
    # __table_args__ = {'schema': 'dbo'}  # Disabled for local testing

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    personal_number = Column(String(15))  # Match schema from scripts folder
    no_ktp = Column(String(16), nullable=False, unique=True, name="no_ktp")
    passport_id = Column(String(9), nullable=False, unique=True, name="passport_id")
    bod = Column(Date, name="bod")
    g_id = Column(String(10), name="g_id")  # Will be populated by sync system
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)  # For soft deletes

    def __repr__(self):
        return f"<Pegawai(id={self.id}, name='{self.name}', g_id='{self.g_id}')>"


class AuditLog(Base):
    """Audit log table for tracking changes"""
    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint("action IN ('INSERT', 'UPDATE', 'DELETE', 'SYNC')", name='check_action'),
        # {'schema': 'dbo'}  # Disabled for local testing
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(String(50))
    action = Column(String(20), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    changed_by = Column(String(100))
    change_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, table='{self.table_name}', action='{self.action}')>"


class SystemConfig(Base):
    """System configuration settings"""
    __tablename__ = 'system_config'
    # __table_args__ = {'schema': 'dbo'}  # Disabled for local testing
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(String(500), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.config_key}', value='{self.config_value}')>"


# Import fix - make sure the models are available when imported
G_ID_Sequence = GIDSequence  # For backward compatibility with the generator
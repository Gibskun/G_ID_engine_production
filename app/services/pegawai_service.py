"""
Service layer for Pegawai REST API operations
Handles business logic and database interactions for employee management
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func, or_
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
import logging

from app.models.models import Pegawai, GlobalID, GlobalIDNonDatabase
from app.api.pegawai_models import (
    PegawaiCreateRequest, 
    PegawaiUpdateRequest,
    PegawaiResponse,
    PegawaiListResponse
)
from app.services.gid_generator import GIDGenerator

logger = logging.getLogger(__name__)


class PegawaiService:
    """Service class for Pegawai operations"""
    
    @staticmethod
    def get_all_employees(
        db: Session,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> PegawaiListResponse:
        """
        Get paginated list of employees with optional search
        
        Args:
            db: Database session
            page: Page number (1-based)
            size: Page size (max 100)
            search: Search term for name, personal_number, or no_ktp
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            PegawaiListResponse with paginated employee data
        """
        try:
            # Validate and sanitize inputs
            page = max(1, page)
            size = min(100, max(1, size))
            
            # Base query
            query = db.query(Pegawai)
            
            # Filter deleted records unless explicitly requested
            if not include_deleted:
                query = query.filter(Pegawai.deleted_at.is_(None))
            
            # Apply search filter if provided
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Pegawai.name.ilike(search_term),
                        Pegawai.personal_number.ilike(search_term),
                        Pegawai.no_ktp.ilike(search_term)
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            employees = (
                query
                .order_by(Pegawai.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
                .all()
            )
            
            # Calculate total pages
            total_pages = (total_count + size - 1) // size if total_count > 0 else 1
            
            return PegawaiListResponse(
                total_count=total_count,
                page=page,
                size=size,
                total_pages=total_pages,
                employees=[PegawaiResponse.from_orm(emp) for emp in employees]
            )
            
        except Exception as e:
            logger.error(f"Error getting employees: {str(e)}")
            raise ValueError(f"Failed to retrieve employees: {str(e)}")
    
    @staticmethod
    def get_employee_by_id(db: Session, employee_id: int) -> Optional[PegawaiResponse]:
        """
        Get employee by ID
        
        Args:
            db: Database session
            employee_id: Employee ID
            
        Returns:
            PegawaiResponse if found, None otherwise
        """
        try:
            employee = (
                db.query(Pegawai)
                .filter(and_(
                    Pegawai.id == employee_id,
                    Pegawai.deleted_at.is_(None)
                ))
                .first()
            )
            
            if employee:
                return PegawaiResponse.from_orm(employee)
            return None
            
        except Exception as e:
            logger.error(f"Error getting employee {employee_id}: {str(e)}")
            raise ValueError(f"Failed to retrieve employee: {str(e)}")
    
    @staticmethod
    def create_employee(db: Session, employee_data: PegawaiCreateRequest) -> PegawaiResponse:
        """
        Create a new employee according to new business rules:
        - Uniqueness: (name, no_ktp, bod)
        - personal_number is NOT part of uniqueness
        - Add to pegawai, global_id, global_id_non_database
        - Reactivate if (name, no_ktp, bod) matches a non-active record
        - Generate new G_ID only if not found
        """
        try:
            # 1. Check for existing record by (name, no_ktp, bod) in global_id
            existing_global = db.query(GlobalID).filter(
                and_(
                    GlobalID.name == employee_data.name,
                    GlobalID.no_ktp == employee_data.no_ktp,
                    GlobalID.bod == employee_data.bod
                )
            ).first()

            now = datetime.utcnow()

            if existing_global:
                # If found, check status
                if existing_global.status == "Non Active":
                    # Reactivate: set status to Active, update updated_at
                    existing_global.status = "Active"
                    existing_global.updated_at = now
                    # Reactivate in pegawai (soft-deleted)
                    existing_pegawai = db.query(Pegawai).filter(
                        and_(
                            Pegawai.name == employee_data.name,
                            Pegawai.no_ktp == employee_data.no_ktp,
                            Pegawai.bod == employee_data.bod,
                            Pegawai.deleted_at.isnot(None)
                        )
                    ).first()
                    if existing_pegawai:
                        existing_pegawai.deleted_at = None
                        existing_pegawai.updated_at = now
                        existing_pegawai.personal_number = employee_data.personal_number
                    # Reactivate in global_id_non_database
                    existing_non_db = db.query(GlobalIDNonDatabase).filter(
                        and_(
                            GlobalIDNonDatabase.name == employee_data.name,
                            GlobalIDNonDatabase.no_ktp == employee_data.no_ktp,
                            GlobalIDNonDatabase.bod == employee_data.bod
                        )
                    ).first()
                    if existing_non_db:
                        existing_non_db.status = "Active"
                        existing_non_db.updated_at = now
                        existing_non_db.personal_number = employee_data.personal_number
                    db.commit()
                    logger.info(f"Reactivated employee and G_ID: {existing_global.g_id}")
                    # Return the active pegawai record (reuse original G_ID)
                    pegawai = db.query(Pegawai).filter(
                        and_(
                            Pegawai.name == employee_data.name,
                            Pegawai.no_ktp == employee_data.no_ktp,
                            Pegawai.bod == employee_data.bod,
                            Pegawai.deleted_at.is_(None)
                        )
                    ).first()
                    return PegawaiResponse.from_orm(pegawai)
                else:
                    # Already active, always block duplicates regardless of personal_number
                    raise ValueError("Employee with this (name, NIK, BOD) already exists and is active")

            # 2. Not found: create new G_ID and add to all tables
            gid_generator = GIDGenerator(db)
            new_gid = gid_generator.generate_next_gid()

            # Pegawai
            new_employee = Pegawai(
                name=employee_data.name,
                personal_number=employee_data.personal_number,
                no_ktp=employee_data.no_ktp,
                passport_id=employee_data.passport_id,
                bod=employee_data.bod,
                g_id=new_gid,
                created_at=now,
                updated_at=now
            )
            db.add(new_employee)

            # Global_ID
            global_id_record = GlobalID(
                g_id=new_gid,
                name=employee_data.name,
                personal_number=employee_data.personal_number,
                no_ktp=employee_data.no_ktp,
                passport_id=employee_data.passport_id,
                bod=employee_data.bod,
                status="Active",
                source="database_pegawai",
                created_at=now,
                updated_at=now
            )
            db.add(global_id_record)

            # Global_ID_NON_Database
            global_id_non_db_record = GlobalIDNonDatabase(
                g_id=new_gid,
                name=employee_data.name,
                personal_number=employee_data.personal_number,
                no_ktp=employee_data.no_ktp,
                passport_id=employee_data.passport_id,
                bod=employee_data.bod,
                status="Active",
                source="database_pegawai",
                created_at=now,
                updated_at=now
            )
            db.add(global_id_non_db_record)

            db.commit()
            db.refresh(new_employee)
            logger.info(f"Created new employee and G_ID: {new_gid}")
            return PegawaiResponse.from_orm(new_employee)

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error creating employee: {str(e)}")
            raise ValueError("Employee data violates database constraints")
        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating employee: {str(e)}")
            raise ValueError(f"Failed to create employee: {str(e)}")
    
    @staticmethod
    def update_employee(
        db: Session, 
        employee_id: int, 
        employee_data: PegawaiUpdateRequest
    ) -> Optional[PegawaiResponse]:
        """
        Update an existing employee
        
        Args:
            db: Database session
            employee_id: Employee ID to update
            employee_data: Updated employee data
            
        Returns:
            PegawaiResponse of updated employee if found, None otherwise
            
        Raises:
            ValueError: If validation fails or conflicts with existing data
        """
        try:
            # Get existing employee
            employee = (
                db.query(Pegawai)
                .filter(and_(
                    Pegawai.id == employee_id,
                    Pegawai.deleted_at.is_(None)
                ))
                .first()
            )
            
            if not employee:
                return None
            
            # Validate unique constraints for updates
            if employee_data.no_ktp and employee_data.no_ktp != employee.no_ktp:
                existing_ktp = (
                    db.query(Pegawai)
                    .filter(and_(
                        Pegawai.no_ktp == employee_data.no_ktp,
                        Pegawai.id != employee_id,
                        Pegawai.deleted_at.is_(None)
                    ))
                    .first()
                )
                
                if existing_ktp:
                    raise ValueError(f"Another employee with KTP number {employee_data.no_ktp} already exists")
                    
            if (employee_data.personal_number and 
                employee_data.personal_number != employee.personal_number):
                existing_personal = (
                    db.query(Pegawai)
                    .filter(and_(
                        Pegawai.personal_number == employee_data.personal_number,
                        Pegawai.id != employee_id,
                        Pegawai.deleted_at.is_(None)
                    ))
                    .first()
                )
                
                if existing_personal:
                    raise ValueError(f"Another employee with personal number {employee_data.personal_number} already exists")
            
            # Update fields that were provided
            update_data = employee_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(employee, field, value)
            
            employee.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(employee)
            
            logger.info(f"Updated employee: {employee.id} - {employee.name}")
            return PegawaiResponse.from_orm(employee)
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error updating employee: {str(e)}")
            raise ValueError("Updated employee data violates database constraints")
        except ValueError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating employee {employee_id}: {str(e)}")
            raise ValueError(f"Failed to update employee: {str(e)}")
    
    @staticmethod
    def soft_delete_employee(db: Session, employee_id: int) -> bool:
        """
        Soft delete an employee (set deleted_at timestamp) and set status to 'Non Active' in global_id/global_id_non_database
        """
        try:
            employee = (
                db.query(Pegawai)
                .filter(and_(
                    Pegawai.id == employee_id,
                    Pegawai.deleted_at.is_(None)
                ))
                .first()
            )
            if not employee:
                return False
            now = datetime.utcnow()
            employee.deleted_at = now
            employee.updated_at = now

            # Also set status to 'Non Active' in global_id
            if employee.g_id:
                global_id = db.query(GlobalID).filter(GlobalID.g_id == employee.g_id).first()
                if global_id:
                    global_id.status = "Non Active"
                    global_id.updated_at = now
                global_id_non_db = db.query(GlobalIDNonDatabase).filter(GlobalIDNonDatabase.g_id == employee.g_id).first()
                if global_id_non_db:
                    global_id_non_db.status = "Non Active"
                    global_id_non_db.updated_at = now

            db.commit()
            logger.info(f"Soft deleted employee and set G_ID status to Non Active: {employee.id} - {employee.name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting employee {employee_id}: {str(e)}")
            raise ValueError(f"Failed to delete employee: {str(e)}")
    
    @staticmethod
    def get_employee_statistics(db: Session) -> dict:
        """
        Get basic employee statistics
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with employee statistics
        """
        try:
            total_employees = db.query(Pegawai).filter(Pegawai.deleted_at.is_(None)).count()
            employees_with_gid = (
                db.query(Pegawai)
                .filter(and_(
                    Pegawai.deleted_at.is_(None),
                    Pegawai.g_id.isnot(None)
                ))
                .count()
            )
            employees_without_gid = total_employees - employees_with_gid
            
            return {
                "total_employees": total_employees,
                "employees_with_gid": employees_with_gid,
                "employees_without_gid": employees_without_gid,
                "gid_assignment_rate": (employees_with_gid / total_employees * 100) if total_employees > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting employee statistics: {str(e)}")
            raise ValueError(f"Failed to get employee statistics: {str(e)}")
    
    @staticmethod
    def check_passport_duplicate(db: Session, passport_id: str) -> Dict[str, Any]:
        """
        Check if passport ID is already in use
        
        Args:
            db: Database session
            passport_id: The passport ID to check
            
        Returns:
            Dictionary with duplicate check results
        """
        try:
            if not passport_id or not passport_id.strip():
                return {
                    "success": True,
                    "is_duplicate": False,
                    "message": "No passport ID provided"
                }
            
            passport_id = passport_id.strip()
            
            # Check in global_id table first (primary table)
            existing_global = db.query(GlobalID).filter(
                and_(
                    GlobalID.passport_id == passport_id,
                    GlobalID.status == "Active"
                )
            ).first()
            
            if existing_global:
                return {
                    "success": True,
                    "is_duplicate": True,
                    "message": f"Passport ID '{passport_id}' is already in use by G_ID {existing_global.g_id}",
                    "existing_data": {
                        "g_id": existing_global.g_id,
                        "name": existing_global.name,
                        "no_ktp": existing_global.no_ktp,
                        "bod": existing_global.bod.isoformat() if existing_global.bod else None,
                        "status": existing_global.status,
                        "source": existing_global.source
                    }
                }
            
            # Also check in global_id_non_database table
            existing_non_db = db.query(GlobalIDNonDatabase).filter(
                and_(
                    GlobalIDNonDatabase.passport_id == passport_id,
                    GlobalIDNonDatabase.status == "Active"
                )
            ).first()
            
            if existing_non_db:
                return {
                    "success": True,
                    "is_duplicate": True,
                    "message": f"Passport ID '{passport_id}' is already in use by G_ID {existing_non_db.g_id}",
                    "existing_data": {
                        "g_id": existing_non_db.g_id,
                        "name": existing_non_db.name,
                        "no_ktp": existing_non_db.no_ktp,
                        "bod": existing_non_db.bod.isoformat() if existing_non_db.bod else None,
                        "status": existing_non_db.status,
                        "source": existing_non_db.source
                    }
                }
            
            return {
                "success": True,
                "is_duplicate": False,
                "message": f"Passport ID '{passport_id}' is available"
            }
            
        except Exception as e:
            logger.error(f"Error checking passport duplicate for {passport_id}: {str(e)}")
            raise ValueError(f"Failed to check passport duplicate: {str(e)}")
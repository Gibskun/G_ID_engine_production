"""
Service layer for Pegawai REST API operations
Handles business logic and database interactions for employee management
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func, or_
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from app.models.models import Pegawai, GlobalID
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
        Create a new employee
        
        Args:
            db: Database session
            employee_data: Employee creation data
            
        Returns:
            PegawaiResponse of created employee
            
        Raises:
            ValueError: If validation fails or employee already exists
        """
        try:
            # Check if employee with same KTP already exists
            existing_employee = (
                db.query(Pegawai)
                .filter(and_(
                    Pegawai.no_ktp == employee_data.no_ktp,
                    Pegawai.deleted_at.is_(None)
                ))
                .first()
            )
            
            if existing_employee:
                raise ValueError(f"Employee with KTP number {employee_data.no_ktp} already exists")
            
            # Check personal number uniqueness if provided
            if employee_data.personal_number:
                existing_personal_number = (
                    db.query(Pegawai)
                    .filter(and_(
                        Pegawai.personal_number == employee_data.personal_number,
                        Pegawai.deleted_at.is_(None)
                    ))
                    .first()
                )
                
                if existing_personal_number:
                    raise ValueError(f"Employee with personal number {employee_data.personal_number} already exists")
            
            # Generate G_ID for the new employee
            gid_generator = GIDGenerator(db)
            g_id = gid_generator.generate_next_gid()
            
            # Create new employee with G_ID
            now = datetime.utcnow()
            new_employee = Pegawai(
                name=employee_data.name,
                personal_number=employee_data.personal_number,
                no_ktp=employee_data.no_ktp,
                bod=employee_data.bod,
                g_id=g_id,
                created_at=now,
                updated_at=now
            )
            
            # Create corresponding Global_ID record
            global_id_record = GlobalID(
                g_id=g_id,
                name=employee_data.name,
                personal_number=employee_data.personal_number,
                no_ktp=employee_data.no_ktp,
                bod=employee_data.bod,
                status="Active",
                source="database_pegawai",
                created_at=now,
                updated_at=now
            )
            
            db.add(new_employee)
            db.add(global_id_record)
            db.commit()
            db.refresh(new_employee)
            
            logger.info(f"Created new employee: {new_employee.id} - {new_employee.name}")
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
        Soft delete an employee (set deleted_at timestamp)
        
        Args:
            db: Database session
            employee_id: Employee ID to delete
            
        Returns:
            True if employee was deleted, False if not found
            
        Raises:
            ValueError: If deletion fails
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
            
            employee.deleted_at = datetime.utcnow()
            employee.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Soft deleted employee: {employee.id} - {employee.name}")
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
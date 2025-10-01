"""
REST API endpoints for Pegawai (Employee) management
Provides external API access for employee CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.models.database import get_db
from app.services.pegawai_service import PegawaiService
from app.api.pegawai_models import (
    PegawaiCreateRequest,
    PegawaiUpdateRequest,
    PegawaiResponse,
    PegawaiListResponse,
    PegawaiCreateResponse,
    PegawaiUpdateResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router for pegawai endpoints
pegawai_router = APIRouter(
    prefix="/pegawai",
    tags=["Employee Management"],
    responses={
        404: {"model": ErrorResponse, "description": "Employee not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@pegawai_router.get(
    "/",
    response_model=PegawaiListResponse,
    summary="Get all employees",
    description="Retrieve a paginated list of all employees with optional search functionality"
)
async def get_all_employees(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
    search: Optional[str] = Query(None, description="Search term for name, personal number, or KTP"),
    include_deleted: bool = Query(False, description="Include soft-deleted employees"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of employees
    
    **Parameters:**
    - **page**: Page number (starting from 1)
    - **size**: Number of employees per page (maximum 100)
    - **search**: Optional search term to filter by name, personal number, or KTP
    - **include_deleted**: Whether to include soft-deleted employees (default: false)
    
    **Returns:**
    - Paginated list of employees with metadata
    """
    try:
        result = PegawaiService.get_all_employees(
            db=db,
            page=page,
            size=size,
            search=search,
            include_deleted=include_deleted
        )
        
        logger.info(f"Retrieved employees: page={page}, size={size}, total={result.total_count}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error getting employees: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "error": "Validation error", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error getting employees: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve employees"}
        )


@pegawai_router.get(
    "/{employee_id}",
    response_model=PegawaiResponse,
    summary="Get employee by ID",
    description="Retrieve a specific employee by their unique ID"
)
async def get_employee_by_id(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get employee by ID
    
    **Parameters:**
    - **employee_id**: Unique employee identifier
    
    **Returns:**
    - Employee details if found
    
    **Raises:**
    - 404: Employee not found
    """
    try:
        employee = PegawaiService.get_employee_by_id(db=db, employee_id=employee_id)
        
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Employee not found", "detail": f"Employee with ID {employee_id} not found"}
            )
        
        logger.info(f"Retrieved employee: {employee_id}")
        return employee
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error getting employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "error": "Validation error", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error getting employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve employee"}
        )


@pegawai_router.post(
    "/",
    response_model=PegawaiCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new employee",
    description="Create a new employee record with validation"
)
async def create_employee(
    employee_data: PegawaiCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new employee
    
    **Request Body:**
    - **name**: Employee full name (required)
    - **personal_number**: Employee personal/staff number (optional)
    - **no_ktp**: 16-digit KTP number (required, must be unique)
    - **bod**: Birth date in YYYY-MM-DD format (optional)
    
    **Returns:**
    - Created employee details with success message
    
    **Raises:**
    - 422: Validation error (invalid data, duplicate KTP/personal number)
    """
    try:
        new_employee = PegawaiService.create_employee(db=db, employee_data=employee_data)
        
        logger.info(f"Created employee: {new_employee.id} - {new_employee.name}")
        
        return PegawaiCreateResponse(
            success=True,
            message="Employee created successfully",
            employee=new_employee
        )
        
    except ValueError as e:
        logger.error(f"Validation error creating employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "error": "Validation error", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error creating employee: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to create employee"}
        )


@pegawai_router.put(
    "/{employee_id}",
    response_model=PegawaiUpdateResponse,
    summary="Update employee",
    description="Update an existing employee's information"
)
async def update_employee(
    employee_id: int,
    employee_data: PegawaiUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing employee
    
    **Parameters:**
    - **employee_id**: Unique employee identifier
    
    **Request Body:**
    - **name**: Employee full name (optional)
    - **personal_number**: Employee personal/staff number (optional)
    - **no_ktp**: 16-digit KTP number (optional, must be unique)
    - **bod**: Birth date in YYYY-MM-DD format (optional)
    
    **Returns:**
    - Updated employee details with success message
    
    **Raises:**
    - 404: Employee not found
    - 422: Validation error (invalid data, duplicate KTP/personal number)
    """
    try:
        updated_employee = PegawaiService.update_employee(
            db=db,
            employee_id=employee_id,
            employee_data=employee_data
        )
        
        if not updated_employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Employee not found", "detail": f"Employee with ID {employee_id} not found"}
            )
        
        logger.info(f"Updated employee: {employee_id} - {updated_employee.name}")
        
        return PegawaiUpdateResponse(
            success=True,
            message="Employee updated successfully",
            employee=updated_employee
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "error": "Validation error", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error updating employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to update employee"}
        )


@pegawai_router.delete(
    "/{employee_id}",
    summary="Delete employee",
    description="Soft delete an employee (marks as deleted without removing from database)"
)
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete an employee
    
    **Parameters:**
    - **employee_id**: Unique employee identifier
    
    **Returns:**
    - Success message
    
    **Raises:**
    - 404: Employee not found
    
    **Note:**
    This performs a soft delete by setting the deleted_at timestamp.
    The employee record remains in the database but is excluded from normal queries.
    """
    try:
        success = PegawaiService.soft_delete_employee(db=db, employee_id=employee_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Employee not found", "detail": f"Employee with ID {employee_id} not found"}
            )
        
        logger.info(f"Deleted employee: {employee_id}")
        
        return {
            "success": True,
            "message": f"Employee {employee_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error deleting employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "error": "Validation error", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting employee {employee_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to delete employee"}
        )


@pegawai_router.get(
    "/stats/summary",
    summary="Get employee statistics",
    description="Get basic statistics about employees in the system"
)
async def get_employee_statistics(db: Session = Depends(get_db)):
    """
    Get employee statistics
    
    **Returns:**
    - Basic statistics about employees including total count and GID assignment rates
    """
    try:
        stats = PegawaiService.get_employee_statistics(db=db)
        
        logger.info("Retrieved employee statistics")
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except ValueError as e:
        logger.error(f"Validation error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "error": "Validation error", "detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to get statistics"}
        )
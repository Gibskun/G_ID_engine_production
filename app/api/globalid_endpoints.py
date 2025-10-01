"""
REST API endpoints for Global ID data tables
Provides read-only access to Global ID tables for external systems
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import logging

from app.models.database import get_db
from app.models.models import GlobalID, GlobalIDNonDatabase

logger = logging.getLogger(__name__)

# Create router for Global ID data endpoints
globalid_router = APIRouter(
    tags=["Global ID Data"],
    responses={
        404: {"description": "Data not found"},
        500: {"description": "Internal server error"}
    }
)


# Response Models
from pydantic import BaseModel
from datetime import datetime, date

class GlobalIDResponse(BaseModel):
    g_id: str
    name: str
    personal_number: Optional[str]
    no_ktp: str
    bod: Optional[date]
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GlobalIDNonDatabaseResponse(BaseModel):
    g_id: str
    name: str
    personal_number: Optional[str]
    no_ktp: str
    bod: Optional[date]
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GlobalIDListResponse(BaseModel):
    success: bool
    data: List[GlobalIDResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class GlobalIDNonDatabaseListResponse(BaseModel):
    success: bool
    data: List[GlobalIDNonDatabaseResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


@globalid_router.get(
    "/global_id",
    response_model=GlobalIDListResponse,
    summary="Get all Global ID records",
    description="Retrieve all records from the global_id table with pagination and filtering"
)
async def get_all_global_id(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(50, ge=1, le=1000, description="Page size (max 1000)"),
    status: Optional[str] = Query(None, description="Filter by status (Active, Non Active)"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search by name, KTP, or G_ID"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of Global ID records
    
    **Parameters:**
    - **page**: Page number (starting from 1)
    - **size**: Number of records per page (maximum 1000)
    - **status**: Filter by status (Active, Non Active)
    - **source**: Filter by source (database_pegawai, excel, etc.)
    - **search**: Search term for name, KTP number, or G_ID
    
    **Returns:**
    - Paginated list of Global ID records
    """
    try:
        # Build query
        query = db.query(GlobalID)
        
        # Apply filters
        if status:
            query = query.filter(GlobalID.status == status)
        if source:
            query = query.filter(GlobalID.source == source)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    GlobalID.name.ilike(search_term),
                    GlobalID.no_ktp.ilike(search_term),
                    GlobalID.g_id.ilike(search_term)
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        records = query.order_by(GlobalID.g_id.asc()).offset(offset).limit(size).all()
        
        # Calculate total pages
        total_pages = (total_count + size - 1) // size
        
        logger.info(f"Retrieved Global ID records: page={page}, size={size}, total={total_count}")
        
        return GlobalIDListResponse(
            success=True,
            data=[GlobalIDResponse.from_orm(record) for record in records],
            total_count=total_count,
            page=page,
            page_size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error retrieving Global ID records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Failed to retrieve Global ID records", "detail": str(e)}
        )


@globalid_router.get(
    "/global_id_non_database", 
    response_model=GlobalIDNonDatabaseListResponse,
    summary="Get all Global ID Non-Database records",
    description="Retrieve all records from the global_id_non_database table with pagination and filtering"
)
async def get_all_global_id_non_database(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(50, ge=1, le=1000, description="Page size (max 1000)"),
    status: Optional[str] = Query(None, description="Filter by status (Active, Non Active)"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search by name, KTP, or G_ID"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of Global ID Non-Database records
    
    **Parameters:**
    - **page**: Page number (starting from 1)
    - **size**: Number of records per page (maximum 1000)
    - **status**: Filter by status (Active, Non Active)
    - **source**: Filter by source (typically 'excel')
    - **search**: Search term for name, KTP number, or G_ID
    
    **Returns:**
    - Paginated list of Global ID Non-Database records
    """
    try:
        # Build query
        query = db.query(GlobalIDNonDatabase)
        
        # Apply filters
        if status:
            query = query.filter(GlobalIDNonDatabase.status == status)
        if source:
            query = query.filter(GlobalIDNonDatabase.source == source)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    GlobalIDNonDatabase.name.ilike(search_term),
                    GlobalIDNonDatabase.no_ktp.ilike(search_term),
                    GlobalIDNonDatabase.g_id.ilike(search_term)
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        records = query.order_by(GlobalIDNonDatabase.g_id.asc()).offset(offset).limit(size).all()
        
        # Calculate total pages
        total_pages = (total_count + size - 1) // size
        
        logger.info(f"Retrieved Global ID Non-Database records: page={page}, size={size}, total={total_count}")
        
        return GlobalIDNonDatabaseListResponse(
            success=True,
            data=[GlobalIDNonDatabaseResponse.from_orm(record) for record in records],
            total_count=total_count,
            page=page,
            page_size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error retrieving Global ID Non-Database records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Failed to retrieve Global ID Non-Database records", "detail": str(e)}
        )


@globalid_router.get(
    "/global_id/{g_id}",
    response_model=GlobalIDResponse,
    summary="Get Global ID record by G_ID",
    description="Retrieve a specific Global ID record by G_ID"
)
async def get_global_id_by_gid(
    g_id: str,
    db: Session = Depends(get_db)
):
    """
    Get Global ID record by G_ID
    
    **Parameters:**
    - **g_id**: The Global ID to lookup
    
    **Returns:**
    - Global ID record if found
    
    **Raises:**
    - 404: Global ID not found
    """
    try:
        record = db.query(GlobalID).filter(GlobalID.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Global ID not found", "detail": f"Global ID '{g_id}' not found"}
            )
        
        logger.info(f"Retrieved Global ID record: {g_id}")
        return GlobalIDResponse.from_orm(record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Global ID {g_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Failed to retrieve Global ID record", "detail": str(e)}
        )


@globalid_router.get(
    "/global_id_non_database/{g_id}",
    response_model=GlobalIDNonDatabaseResponse,
    summary="Get Global ID Non-Database record by G_ID",
    description="Retrieve a specific Global ID Non-Database record by G_ID"
)
async def get_global_id_non_database_by_gid(
    g_id: str,
    db: Session = Depends(get_db)
):
    """
    Get Global ID Non-Database record by G_ID
    
    **Parameters:**
    - **g_id**: The Global ID to lookup
    
    **Returns:**
    - Global ID Non-Database record if found
    
    **Raises:**
    - 404: Global ID not found
    """
    try:
        record = db.query(GlobalIDNonDatabase).filter(GlobalIDNonDatabase.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Global ID Non-Database record not found", "detail": f"Global ID '{g_id}' not found in non-database table"}
            )
        
        logger.info(f"Retrieved Global ID Non-Database record: {g_id}")
        return GlobalIDNonDatabaseResponse.from_orm(record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Global ID Non-Database {g_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Failed to retrieve Global ID Non-Database record", "detail": str(e)}
        )
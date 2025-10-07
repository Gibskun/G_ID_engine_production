"""
G_ID-based REST API endpoints for all tables
Provides CRUD operations using G_ID as the primary identifier
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel
from datetime import datetime, date
import logging

from app.models.database import get_db
from app.models.models import GlobalID, GlobalIDNonDatabase, Pegawai, AuditLog

logger = logging.getLogger(__name__)

# Create router for G_ID-based endpoints
gid_api_router = APIRouter(
    prefix="/gid",
    tags=["G_ID Operations"],
    responses={
        404: {"description": "Record not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)

# Pydantic models for requests/responses
class GlobalIDGIDResponse(BaseModel):
    g_id: str
    name: str
    personal_number: Optional[str] = None
    no_ktp: str
    bod: Optional[date] = None
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GlobalIDNonDatabaseGIDResponse(BaseModel):
    g_id: str
    name: str
    personal_number: Optional[str] = None
    no_ktp: str
    bod: Optional[date] = None
    status: str
    source: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PegawaiGIDResponse(BaseModel):
    id: int
    name: str
    personal_number: Optional[str] = None
    no_ktp: str
    bod: Optional[date] = None
    g_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class GlobalIDGIDUpdateRequest(BaseModel):
    name: Optional[str] = None
    personal_number: Optional[str] = None
    bod: Optional[date] = None
    status: Optional[str] = None

class GlobalIDNonDatabaseGIDUpdateRequest(BaseModel):
    name: Optional[str] = None
    personal_number: Optional[str] = None
    bod: Optional[date] = None
    status: Optional[str] = None

class PegawaiGIDUpdateRequest(BaseModel):
    name: Optional[str] = None
    personal_number: Optional[str] = None
    bod: Optional[date] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str

class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class BulkDeleteResponse(BaseModel):
    success: bool = True
    message: str
    deleted_count: int
    deleted_gids: List[str]

# =================
# GLOBAL_ID TABLE - G_ID Based Operations
# =================

@gid_api_router.get(
    "/global-id/{g_id}",
    response_model=GlobalIDGIDResponse,
    summary="Get Global ID record by G_ID",
    description="Retrieve a specific Global ID record using G_ID as identifier"
)
async def get_global_id_by_gid(
    g_id: str,
    db: Session = Depends(get_db)
):
    """Get Global ID record by G_ID"""
    try:
        record = db.query(GlobalID).filter(GlobalID.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Global ID record with G_ID {g_id} not found"}
            )
        
        logger.info(f"Retrieved Global ID record: {g_id}")
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Global ID record {g_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve record"}
        )

@gid_api_router.get(
    "/global-id/",
    response_model=List[GlobalIDGIDResponse],
    summary="Get all Global ID records",
    description="Retrieve all Global ID records with optional filtering"
)
async def get_all_global_id_by_gid(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    source_filter: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """Get all Global ID records with optional filtering"""
    try:
        query = db.query(GlobalID)
        
        if status_filter:
            query = query.filter(GlobalID.status == status_filter)
        if source_filter:
            query = query.filter(GlobalID.source == source_filter)
            
        # IMPORTANT (MSSQL Compatibility): SQL Server requires ORDER BY when using OFFSET/FETCH
        # Add a deterministic ordering to ensure stable pagination and avoid errors like:
        # "MSSQL requires an order_by when using an OFFSET or a non-simple LIMIT clause"
        if not query._order_by_clauses:  # type: ignore[attr-defined]
            # Prefer updated_at for most recent first, fallback to g_id for deterministic ordering
            try:
                query = query.order_by(GlobalID.updated_at.desc(), GlobalID.g_id)
            except Exception:
                # Absolute fallback (should not happen, but keeps system resilient)
                query = query.order_by(GlobalID.g_id)

        records = query.offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(records)} Global ID records")
        return records
        
    except Exception as e:
        logger.error(f"Error getting Global ID records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve records"}
        )

@gid_api_router.put(
    "/global-id/{g_id}",
    response_model=GlobalIDGIDResponse,
    summary="Update Global ID record by G_ID",
    description="Update a Global ID record using G_ID as identifier"
)
async def update_global_id_by_gid(
    g_id: str,
    update_data: GlobalIDGIDUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update Global ID record by G_ID"""
    try:
        record = db.query(GlobalID).filter(GlobalID.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Global ID record with G_ID {g_id} not found"}
            )
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(record, field, value)
        
        record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)
        
        # Log audit trail
        audit_log = AuditLog(
            table_name="global_id",
            record_id=g_id,
            action="UPDATE",
            new_values=update_dict,
            change_reason="Updated via G_ID API"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Updated Global ID record: {g_id}")
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Global ID record {g_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to update record"}
        )

@gid_api_router.delete(
    "/global-id/{g_id}",
    response_model=SuccessResponse,
    summary="Delete Global ID record by G_ID",
    description="Delete a Global ID record using G_ID as identifier"
)
async def delete_global_id_by_gid(
    g_id: str,
    db: Session = Depends(get_db)
):
    """Delete Global ID record by G_ID"""
    try:
        record = db.query(GlobalID).filter(GlobalID.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Global ID record with G_ID {g_id} not found"}
            )
        
        # Store record data for audit
        old_values = {
            "g_id": record.g_id,
            "name": record.name,
            "personal_number": record.personal_number,
            "no_ktp": record.no_ktp,
            "status": record.status
        }
        
        db.delete(record)
        
        # Log audit trail
        audit_log = AuditLog(
            table_name="global_id",
            record_id=g_id,
            action="DELETE",
            old_values=old_values,
            change_reason="Deleted via G_ID API"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Deleted Global ID record: {g_id}")
        
        return SuccessResponse(message=f"Global ID record {g_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Global ID record {g_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to delete record"}
        )

@gid_api_router.delete(
    "/global-id/",
    response_model=BulkDeleteResponse,
    summary="Bulk delete Global ID records",
    description="Delete multiple Global ID records by G_IDs or criteria"
)
async def bulk_delete_global_id_by_gid(
    gids: Optional[List[str]] = Query(None, description="List of G_IDs to delete"),
    status_filter: Optional[str] = Query(None, description="Delete by status"),
    source_filter: Optional[str] = Query(None, description="Delete by source"),
    confirm_bulk: bool = Query(False, description="Confirmation for bulk delete"),
    db: Session = Depends(get_db)
):
    """Bulk delete Global ID records"""
    try:
        if not confirm_bulk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": "Confirmation required", "detail": "Set confirm_bulk=true to confirm bulk delete"}
            )
        
        query = db.query(GlobalID)
        
        if gids:
            query = query.filter(GlobalID.g_id.in_(gids))
        else:
            if status_filter:
                query = query.filter(GlobalID.status == status_filter)
            if source_filter:
                query = query.filter(GlobalID.source == source_filter)
        
        records_to_delete = query.all()
        
        if not records_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "No records found", "detail": "No records match the deletion criteria"}
            )
        
        deleted_gids = [record.g_id for record in records_to_delete]
        
        # Delete records
        for record in records_to_delete:
            # Log audit trail for each deletion
            audit_log = AuditLog(
                table_name="global_id",
                record_id=record.g_id,
                action="DELETE",
                old_values={"g_id": record.g_id, "name": record.name},
                change_reason="Bulk deleted via G_ID API"
            )
            db.add(audit_log)
            db.delete(record)
        
        db.commit()
        
        logger.info(f"Bulk deleted {len(deleted_gids)} Global ID records")
        
        return BulkDeleteResponse(
            message=f"Successfully deleted {len(deleted_gids)} Global ID records",
            deleted_count=len(deleted_gids),
            deleted_gids=deleted_gids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting Global ID records: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to delete records"}
        )

# =================
# GLOBAL_ID_NON_DATABASE TABLE - G_ID Based Operations
# =================

@gid_api_router.get(
    "/global-id-non-database/{g_id}",
    response_model=GlobalIDNonDatabaseGIDResponse,
    summary="Get Global ID Non-Database record by G_ID",
    description="Retrieve a specific Global ID Non-Database record using G_ID as identifier"
)
async def get_global_id_non_database_by_gid(
    g_id: str,
    db: Session = Depends(get_db)
):
    """Get Global ID Non-Database record by G_ID"""
    try:
        record = db.query(GlobalIDNonDatabase).filter(GlobalIDNonDatabase.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Global ID Non-Database record with G_ID {g_id} not found"}
            )
        
        logger.info(f"Retrieved Global ID Non-Database record: {g_id}")
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Global ID Non-Database record {g_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve record"}
        )

@gid_api_router.get(
    "/global-id-non-database/",
    response_model=List[GlobalIDNonDatabaseGIDResponse],
    summary="Get all Global ID Non-Database records",
    description="Retrieve all Global ID Non-Database records with optional filtering"
)
async def get_all_global_id_non_database_by_gid(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    source_filter: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """Get all Global ID Non-Database records with optional filtering"""
    try:
        query = db.query(GlobalIDNonDatabase)
        
        if status_filter:
            query = query.filter(GlobalIDNonDatabase.status == status_filter)
        if source_filter:
            query = query.filter(GlobalIDNonDatabase.source == source_filter)
            
        # MSSQL requires ORDER BY when OFFSET/LIMIT used – ensure deterministic ordering
        if not query._order_by_clauses:  # type: ignore[attr-defined]
            try:
                query = query.order_by(GlobalIDNonDatabase.updated_at.desc(), GlobalIDNonDatabase.g_id)
            except Exception:
                query = query.order_by(GlobalIDNonDatabase.g_id)

        records = query.offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(records)} Global ID Non-Database records")
        return records
        
    except Exception as e:
        logger.error(f"Error getting Global ID Non-Database records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve records"}
        )

@gid_api_router.put(
    "/global-id-non-database/{g_id}",
    response_model=GlobalIDNonDatabaseGIDResponse,
    summary="Update Global ID Non-Database record by G_ID",
    description="Update a Global ID Non-Database record using G_ID as identifier"
)
async def update_global_id_non_database_by_gid(
    g_id: str,
    update_data: GlobalIDNonDatabaseGIDUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update Global ID Non-Database record by G_ID"""
    try:
        record = db.query(GlobalIDNonDatabase).filter(GlobalIDNonDatabase.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Global ID Non-Database record with G_ID {g_id} not found"}
            )
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(record, field, value)
        
        record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)
        
        # Log audit trail
        audit_log = AuditLog(
            table_name="global_id_non_database",
            record_id=g_id,
            action="UPDATE",
            new_values=update_dict,
            change_reason="Updated via G_ID API"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Updated Global ID Non-Database record: {g_id}")
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Global ID Non-Database record {g_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to update record"}
        )

@gid_api_router.delete(
    "/global-id-non-database/{g_id}",
    response_model=SuccessResponse,
    summary="Delete Global ID Non-Database record by G_ID",
    description="Delete a Global ID Non-Database record using G_ID as identifier"
)
async def delete_global_id_non_database_by_gid(
    g_id: str,
    db: Session = Depends(get_db)
):
    """Delete Global ID Non-Database record by G_ID"""
    try:
        record = db.query(GlobalIDNonDatabase).filter(GlobalIDNonDatabase.g_id == g_id).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Global ID Non-Database record with G_ID {g_id} not found"}
            )
        
        # Store record data for audit
        old_values = {
            "g_id": record.g_id,
            "name": record.name,
            "personal_number": record.personal_number,
            "no_ktp": record.no_ktp,
            "status": record.status
        }
        
        db.delete(record)
        
        # Log audit trail
        audit_log = AuditLog(
            table_name="global_id_non_database",
            record_id=g_id,
            action="DELETE",
            old_values=old_values,
            change_reason="Deleted via G_ID API"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Deleted Global ID Non-Database record: {g_id}")
        
        return SuccessResponse(message=f"Global ID Non-Database record {g_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Global ID Non-Database record {g_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to delete record"}
        )

# =================
# PEGAWAI TABLE - G_ID Based Operations
# =================

@gid_api_router.get(
    "/pegawai/{g_id}",
    response_model=PegawaiGIDResponse,
    summary="Get Pegawai record by G_ID",
    description="Retrieve a specific Pegawai record using G_ID as identifier"
)
async def get_pegawai_by_gid(
    g_id: str,
    include_deleted: bool = Query(False, description="Include soft-deleted records"),
    db: Session = Depends(get_db)
):
    """Get Pegawai record by G_ID"""
    try:
        query = db.query(Pegawai).filter(Pegawai.g_id == g_id)
        
        if not include_deleted:
            query = query.filter(Pegawai.deleted_at.is_(None))
        
        record = query.first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Pegawai record with G_ID {g_id} not found"}
            )
        
        logger.info(f"Retrieved Pegawai record: {g_id}")
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Pegawai record {g_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve record"}
        )

@gid_api_router.get(
    "/pegawai/",
    response_model=List[PegawaiGIDResponse],
    summary="Get all Pegawai records with G_ID",
    description="Retrieve all Pegawai records that have G_ID assigned"
)
async def get_all_pegawai_by_gid(
    include_deleted: bool = Query(False, description="Include soft-deleted records"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """Get all Pegawai records with G_ID"""
    try:
        query = db.query(Pegawai).filter(Pegawai.g_id.isnot(None))
        
        if not include_deleted:
            query = query.filter(Pegawai.deleted_at.is_(None))
            
        # MSSQL requires ORDER BY when using OFFSET – enforce consistent ordering
        if not query._order_by_clauses:  # type: ignore[attr-defined]
            try:
                query = query.order_by(Pegawai.updated_at.desc(), Pegawai.id)
            except Exception:
                query = query.order_by(Pegawai.id)

        records = query.offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(records)} Pegawai records with G_ID")
        return records
        
    except Exception as e:
        logger.error(f"Error getting Pegawai records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to retrieve records"}
        )

@gid_api_router.put(
    "/pegawai/{g_id}",
    response_model=PegawaiGIDResponse,
    summary="Update Pegawai record by G_ID",
    description="Update a Pegawai record using G_ID as identifier"
)
async def update_pegawai_by_gid(
    g_id: str,
    update_data: PegawaiGIDUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update Pegawai record by G_ID"""
    try:
        record = db.query(Pegawai).filter(
            and_(Pegawai.g_id == g_id, Pegawai.deleted_at.is_(None))
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Pegawai record with G_ID {g_id} not found"}
            )
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(record, field, value)
        
        record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)
        
        # Log audit trail
        audit_log = AuditLog(
            table_name="pegawai",
            record_id=str(record.id),
            action="UPDATE",
            new_values=update_dict,
            change_reason=f"Updated via G_ID API using G_ID {g_id}"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Updated Pegawai record: {g_id}")
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Pegawai record {g_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to update record"}
        )

@gid_api_router.delete(
    "/pegawai/{g_id}",
    response_model=SuccessResponse,
    summary="Delete Pegawai record by G_ID",
    description="Soft delete a Pegawai record using G_ID as identifier"
)
async def delete_pegawai_by_gid(
    g_id: str,
    hard_delete: bool = Query(False, description="Perform hard delete instead of soft delete"),
    db: Session = Depends(get_db)
):
    """Delete Pegawai record by G_ID (soft delete by default)"""
    try:
        record = db.query(Pegawai).filter(
            and_(Pegawai.g_id == g_id, Pegawai.deleted_at.is_(None))
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "error": "Record not found", "detail": f"Pegawai record with G_ID {g_id} not found"}
            )
        
        # Store record data for audit
        old_values = {
            "id": record.id,
            "g_id": record.g_id,
            "name": record.name,
            "personal_number": record.personal_number,
            "no_ktp": record.no_ktp
        }
        
        if hard_delete:
            db.delete(record)
            action = "DELETE"
            message = f"Pegawai record {g_id} permanently deleted"
        else:
            record.deleted_at = datetime.utcnow()
            record.updated_at = datetime.utcnow()
            action = "SOFT_DELETE"
            message = f"Pegawai record {g_id} soft deleted"
        
        # Log audit trail
        audit_log = AuditLog(
            table_name="pegawai",
            record_id=str(record.id),
            action=action,
            old_values=old_values,
            change_reason=f"Deleted via G_ID API using G_ID {g_id}"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Deleted Pegawai record: {g_id} (hard_delete={hard_delete})")
        
        return SuccessResponse(message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Pegawai record {g_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": "Internal server error", "detail": "Failed to delete record"}
        )
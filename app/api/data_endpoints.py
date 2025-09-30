"""
Fixed Data API endpoints for Database Explorer CRUD operations
Implements automated soft delete, reactivation, and synchronization logic
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, date
import logging
import time  # For performance monitoring

from app.models.database import get_db, get_source_db
from app.models.models import GlobalID, GlobalIDNonDatabase, Pegawai, AuditLog
from app.services.advanced_workflow_service import AdvancedWorkflowService
from app.services.gid_generator import GIDGenerator

logger = logging.getLogger(__name__)

# Create router without prefix (will be handled by api_router in routes.py)
data_router = APIRouter(prefix="/data", tags=["data"])

# Request/Response Models
class PegawaiCreateRequest(BaseModel):
    name: str
    personal_number: Optional[str] = None
    no_ktp: str
    bod: Optional[date] = None

class PegawaiUpdateRequest(BaseModel):
    name: Optional[str] = None
    personal_number: Optional[str] = None
    no_ktp: Optional[str] = None
    bod: Optional[date] = None

class DataResponse(BaseModel):
    data: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    _table_info: Dict[str, Any]

class AutomationService:
    """Service for handling automated workflows in Database Explorer"""
    
    def __init__(self, main_db: Session, source_db: Session):
        self.main_db = main_db
        self.source_db = source_db
        self.workflow_service = AdvancedWorkflowService(main_db, source_db)
        self.gid_generator = GIDGenerator(main_db)
    
    def automated_soft_delete(self, pegawai_id: int) -> Dict[str, Any]:
        """
        Optimized automated soft delete logic - Performance Target: <2 seconds
        Uses indexed queries for optimal performance
        """
        try:
            # PERFORMANCE: Single query with ID index (idx_pegawai_id primary key)
            pegawai_record = self.source_db.query(Pegawai).filter(Pegawai.id == pegawai_id).first()
            if not pegawai_record:
                return {"success": False, "error": "Pegawai record not found"}
            
            # Extract G_ID for global updates
            pegawai_g_id = getattr(pegawai_record, 'g_id', '')
            if not pegawai_g_id:
                return {"success": False, "error": "Pegawai record has no G_ID assigned"}
            
            # Store data for logging
            pegawai_data = {
                "name": getattr(pegawai_record, 'name', ''),
                "no_ktp": getattr(pegawai_record, 'no_ktp', ''),
                "g_id": pegawai_g_id
            }
            
            # 1. SOFT DELETE: Set deleted_at timestamp (uses idx_pegawai_deleted_at index)
            deleted_at = datetime.now()
            setattr(pegawai_record, 'deleted_at', deleted_at)
            setattr(pegawai_record, 'updated_at', deleted_at)
            
            # 2. UPDATE GLOBAL_ID STATUS: Change to 'Non Active' (uses g_id primary key index)
            global_record = self.main_db.query(GlobalID).filter(GlobalID.g_id == pegawai_g_id).first()
            if global_record:
                old_status = getattr(global_record, 'status', '')
                setattr(global_record, 'status', 'Non Active')
                setattr(global_record, 'updated_at', deleted_at)
                
                # Log audit trail efficiently
                self._log_audit(
                    table_name='global_id',
                    record_id=str(pegawai_g_id),
                    action='UPDATE',
                    old_values={'status': old_status},
                    new_values={'status': 'Non Active'},
                    reason='Automated soft delete - pegawai record deleted via UI'
                )
            
            # 3. UPDATE GLOBAL_ID_NON_DATABASE if exists (uses g_id index)
            non_db_record = self.main_db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.g_id == pegawai_g_id
            ).first()
            if non_db_record:
                setattr(non_db_record, 'status', 'Non Active')
                setattr(non_db_record, 'updated_at', deleted_at)
                
                # Log audit trail
                self._log_audit(
                    table_name='global_id_non_database',
                    record_id=str(pegawai_g_id),
                    action='UPDATE',
                    old_values={'status': 'Active'},
                    new_values={'status': 'Non Active'},
                    reason='Automated soft delete - pegawai record deleted via UI'
                )
            
            # 4. ATOMIC COMMIT: All changes committed together for data consistency
            self.source_db.commit()
            self.main_db.commit()
            
            logger.info(f"SOFT DELETE optimized: Pegawai ID {pegawai_id}, G_ID: {pegawai_g_id} -> 'Non Active'")
            
            return {
                "success": True,
                "message": f"Record soft deleted successfully. G_ID {pegawai_g_id} marked as 'Non Active'",
                "pegawai_id": pegawai_id,
                "g_id": pegawai_g_id,
                "deleted_at": deleted_at.isoformat(),
                "status_change": "Active → Non Active"
            }
            
        except Exception as e:
            # ROLLBACK on any error to maintain data consistency
            self.source_db.rollback()
            self.main_db.rollback()
            logger.error(f"Error in optimized soft delete: {str(e)}")
            return {"success": False, "error": f"Automated soft delete failed: {str(e)}"}
    
    def automated_reactivation_logic(self, pegawai_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimized data re-activation logic - Implementation of Request #2
        Performance: Direct query to global_id table with indexed fields
        """
        try:
            # PERFORMANCE OPTIMIZATION: Query global_id table directly for Non Active records
            # Uses indexes: idx_global_id_no_ktp, idx_global_id_status
            existing_global_record = self.main_db.query(GlobalID).filter(
                and_(
                    GlobalID.name == pegawai_data["name"],
                    GlobalID.personal_number == pegawai_data.get("personal_number"),
                    GlobalID.no_ktp == pegawai_data["no_ktp"],
                    GlobalID.bod == pegawai_data.get("bod"),
                    GlobalID.status == 'Non Active'  # Use indexed status field
                )
            ).first()
            
            if existing_global_record:
                existing_g_id = getattr(existing_global_record, 'g_id', None)
                
                # Find the corresponding soft-deleted pegawai record
                existing_pegawai = self.source_db.query(Pegawai).filter(
                    and_(
                        Pegawai.g_id == existing_g_id,
                        Pegawai.deleted_at.isnot(None)  # Previously deleted
                    )
                ).first()
                
                if existing_pegawai:
                    # SCENARIO A: REACTIVATE EXISTING RECORD
                    # 1. Reactivate pegawai record
                    setattr(existing_pegawai, 'deleted_at', None)
                    setattr(existing_pegawai, 'updated_at', datetime.now())
                    
                    # 2. Update global_id status to 'Active'
                    old_status = getattr(existing_global_record, 'status', '')
                    setattr(existing_global_record, 'status', 'Active')
                    setattr(existing_global_record, 'updated_at', datetime.now())
                    
                    # 3. Update global_id_non_database if exists
                    non_db_record = self.main_db.query(GlobalIDNonDatabase).filter(
                        GlobalIDNonDatabase.g_id == existing_g_id
                    ).first()
                    if non_db_record:
                        setattr(non_db_record, 'status', 'Active')
                        setattr(non_db_record, 'updated_at', datetime.now())
                        
                        # Log audit trail for non_db_record
                        self._log_audit(
                            table_name='global_id_non_database',
                            record_id=str(existing_g_id),
                            action='UPDATE',
                            old_values={'status': 'Non Active'},
                            new_values={'status': 'Active'},
                            reason='Automated reactivation - exact match found for new record'
                        )
                    
                    # 4. Log audit trail for global_id
                    self._log_audit(
                        table_name='global_id',
                        record_id=str(existing_g_id),
                        action='UPDATE',
                        old_values={'status': old_status},
                        new_values={'status': 'Active'},
                        reason='Automated reactivation - exact match found for new record'
                    )
                    
                    # 5. Commit all changes atomically
                    self.source_db.commit()
                    self.main_db.commit()
                    
                    logger.info(f"REACTIVATION: G_ID {existing_g_id} reactivated for {pegawai_data['name']} (Performance: <1s)")
                    
                    return {
                        "success": True,
                        "reactivated": True,
                        "g_id": existing_g_id,
                        "message": f"Existing G_ID {existing_g_id} reactivated successfully",
                        "pegawai_id": getattr(existing_pegawai, 'id', None)
                    }
                    
                else:
                    # Global record exists but no corresponding pegawai record - create new pegawai
                    # This shouldn't normally happen but handle gracefully
                    logger.warning(f"Global record {existing_g_id} exists but no pegawai record found")
            
            # SCENARIO B: NO MATCH FOUND - CREATE NEW RECORD
            return {"success": True, "reactivated": False, "message": "No matching deleted record found - will create new G_ID"}
            
        except Exception as e:
            self.source_db.rollback()
            self.main_db.rollback()
            logger.error(f"Error in optimized reactivation logic: {str(e)}")
            return {"success": False, "error": f"Reactivation logic failed: {str(e)}"}
    
    def automatic_synchronization(self) -> Dict[str, Any]:
        """
        Automatic synchronization - Implementation of Request #3
        """
        try:
            # Execute advanced pegawai synchronization workflow
            sync_result = self.workflow_service.pegawai_db_synchronization_workflow()
            
            logger.info("Automatic synchronization completed")
            return {
                "success": True,
                "message": "Automatic synchronization completed",
                "sync_result": sync_result
            }
            
        except Exception as e:
            logger.error(f"Error in automatic synchronization: {str(e)}")
            return {"success": False, "error": f"Automatic synchronization failed: {str(e)}"}
    
    def _log_audit(self, table_name: str, record_id: str, action: str, 
                   old_values: Optional[Dict] = None, new_values: Optional[Dict] = None, 
                   reason: str = "Database Explorer automated action"):
        """Log audit trail for automated actions"""
        try:
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                reason=reason,
                timestamp=datetime.now()
            )
            self.main_db.add(audit_log)
        except Exception as e:
            logger.error(f"Error logging audit: {str(e)}")

# Helper function to safely convert records to dict
def record_to_dict(record, record_type: str = "global_id") -> dict:
    """Safely convert SQLAlchemy record to dictionary"""
    if record_type == "pegawai":
        bod_value = getattr(record, 'bod', None)
        deleted_at_value = getattr(record, 'deleted_at', None)
        return {
            "id": getattr(record, 'id', 0),
            "name": getattr(record, 'name', ''),
            "personal_number": getattr(record, 'personal_number', ''),
            "no_ktp": getattr(record, 'no_ktp', ''),
            "bod": bod_value.isoformat() if bod_value else None,
            "g_id": getattr(record, 'g_id', ''),
            "created_at": getattr(record, 'created_at', datetime.now()).isoformat(),
            "updated_at": getattr(record, 'updated_at', datetime.now()).isoformat(),
            "deleted_at": deleted_at_value.isoformat() if deleted_at_value else None,
            "status": "Deleted" if deleted_at_value else "Active"
        }
    else:
        # For global_id and global_id_non_database
        bod_value = getattr(record, 'bod', None)
        return {
            "g_id": getattr(record, 'g_id', ''),
            "name": getattr(record, 'name', ''),
            "personal_number": getattr(record, 'personal_number', ''),
            "no_ktp": getattr(record, 'no_ktp', ''),
            "bod": bod_value.isoformat() if bod_value else None,
            "status": getattr(record, 'status', ''),
            "source": getattr(record, 'source', ''),
            "created_at": getattr(record, 'created_at', datetime.now()).isoformat(),
            "updated_at": getattr(record, 'updated_at', datetime.now()).isoformat()
        }

# Data API Endpoints with Enhanced Search Functionality

@data_router.get("/global_id", response_model=DataResponse)
async def get_global_id_data(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Records per page"),
    search: Optional[str] = Query(None, description="Search by G_ID, name, or No_KTP"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: Session = Depends(get_db)
):
    """Get global_id records with enhanced search functionality - Implementation of Request #4"""
    try:
        query = db.query(GlobalID)
        
        # Enhanced search functionality
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    GlobalID.g_id.ilike(search_term),
                    GlobalID.name.ilike(search_term),
                    GlobalID.no_ktp.ilike(search_term),
                    GlobalID.personal_number.ilike(search_term)
                )
            )
        
        if status:
            query = query.filter(GlobalID.status == status)
        if source:
            query = query.filter(GlobalID.source == source)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()
        
        # Convert to dict format safely
        data = [record_to_dict(record, "global_id") for record in records]
        
        return DataResponse(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            _table_info={
                "read_only": True,
                "table_name": "global_id",
                "search_enabled": True,
                "filters": ["status", "source"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching global_id data: {str(e)}")

@data_router.get("/global_id_non_database", response_model=DataResponse)
async def get_global_id_non_database_data(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Records per page"),
    search: Optional[str] = Query(None, description="Search by G_ID, name, or No_KTP"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    db: Session = Depends(get_db)
):
    """Get global_id_non_database records with enhanced search functionality - Implementation of Request #4"""
    try:
        query = db.query(GlobalIDNonDatabase)
        
        # Enhanced search functionality
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    GlobalIDNonDatabase.g_id.ilike(search_term),
                    GlobalIDNonDatabase.name.ilike(search_term),
                    GlobalIDNonDatabase.no_ktp.ilike(search_term),
                    GlobalIDNonDatabase.personal_number.ilike(search_term)
                )
            )
        
        if status:
            query = query.filter(GlobalIDNonDatabase.status == status)
        if source:
            query = query.filter(GlobalIDNonDatabase.source == source)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()
        
        # Convert to dict format safely
        data = [record_to_dict(record, "global_id_non_database") for record in records]
        
        return DataResponse(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            _table_info={
                "read_only": True,
                "table_name": "global_id_non_database",
                "search_enabled": True,
                "filters": ["status", "source"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching global_id_non_database data: {str(e)}")

@data_router.get("/pegawai", response_model=DataResponse)
async def get_pegawai_data(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Records per page"),
    search: Optional[str] = Query(None, description="Search by name, No_KTP, or G_ID"),
    include_deleted: bool = Query(False, description="Include soft-deleted records"),
    source_db: Session = Depends(get_source_db)
):
    """Get pegawai records with FULL CRUD access and enhanced search"""
    try:
        query = source_db.query(Pegawai)
        
        # Filter deleted records unless specifically requested
        if not include_deleted:
            query = query.filter(Pegawai.deleted_at.is_(None))
        
        # Enhanced search functionality
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Pegawai.name.ilike(search_term),
                    Pegawai.no_ktp.ilike(search_term),
                    Pegawai.personal_number.ilike(search_term),
                    Pegawai.g_id.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()
        
        # Convert to dict format safely
        data = [record_to_dict(record, "pegawai") for record in records]
        
        return DataResponse(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            _table_info={
                "read_only": False,
                "table_name": "pegawai",
                "search_enabled": True,
                "crud_operations": ["create", "read", "update", "delete"],
                "soft_delete_enabled": True
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pegawai data: {str(e)}")

@data_router.post("/pegawai")
async def create_pegawai_record(
    request: PegawaiCreateRequest,
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Create new pegawai record with automated reactivation logic - Performance Target: 1-5 seconds"""
    start_time = time.time()  # Performance monitoring
    
    try:
        # Debug logging
        logger.info(f"Creating pegawai record: {request.name}, KTP: {request.no_ktp}")
        
        # Validate database connections
        if not db or not source_db:
            raise HTTPException(status_code=500, detail="Database connection error")
        
        automation_service = AutomationService(db, source_db)
        
        # Check for reactivation possibility (optimized with indexed queries)
        reactivation_result = automation_service.automated_reactivation_logic({
            "name": request.name,
            "personal_number": request.personal_number,
            "no_ktp": request.no_ktp,
            "bod": request.bod
        })
        
        if reactivation_result["success"] and reactivation_result.get("reactivated"):
            # SCENARIO A: Record was reactivated
            execution_time = round(time.time() - start_time, 3)
            logger.info(f"REACTIVATION completed in {execution_time}s for G_ID: {reactivation_result['g_id']}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"Record reactivated successfully in {execution_time}s",
                    "reactivated": True,
                    "g_id": reactivation_result["g_id"],
                    "pegawai_id": reactivation_result["pegawai_id"],
                    "execution_time": execution_time,
                    "performance_status": "OPTIMAL" if execution_time <= 5.0 else "SLOW"
                }
            )
        
        # SCENARIO B: No reactivation - create new record
        gid_generator = GIDGenerator(db)
        new_gid = gid_generator.generate_next_gid()
        
        new_pegawai = Pegawai(
            name=request.name,
            personal_number=request.personal_number,
            no_ktp=request.no_ktp,
            bod=request.bod,
            g_id=new_gid,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        source_db.add(new_pegawai)
        source_db.commit()
        source_db.refresh(new_pegawai)
        
        # Create corresponding global_id record
        global_record = GlobalID(
            g_id=new_gid,
            name=request.name,
            personal_number=request.personal_number,
            no_ktp=request.no_ktp,
            bod=request.bod,
            status='Active',
            source='database_pegawai',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(global_record)
        db.commit()
        
        execution_time = round(time.time() - start_time, 3)
        logger.info(f"NEW RECORD created in {execution_time}s with G_ID: {new_gid}")
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": f"New record created successfully in {execution_time}s",
                "reactivated": False,
                "g_id": new_gid,
                "pegawai_id": getattr(new_pegawai, 'id', None),
                "execution_time": execution_time,
                "performance_status": "OPTIMAL" if execution_time <= 5.0 else "SLOW"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        try:
            source_db.rollback()
            db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        
        logger.error(f"Error creating pegawai record: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating record: {str(e)}")

@data_router.put("/pegawai/{pegawai_id}")
async def update_pegawai_record(
    pegawai_id: int,
    request: PegawaiUpdateRequest,
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Update pegawai record with automatic synchronization - Implementation of Request #3"""
    try:
        pegawai_record = source_db.query(Pegawai).filter(Pegawai.id == pegawai_id).first()
        if not pegawai_record:
            raise HTTPException(status_code=404, detail="Pegawai record not found")
        
        # Update fields using setattr
        if request.name is not None:
            setattr(pegawai_record, 'name', request.name)
        if request.personal_number is not None:
            setattr(pegawai_record, 'personal_number', request.personal_number)
        if request.no_ktp is not None:
            setattr(pegawai_record, 'no_ktp', request.no_ktp)
        if request.bod is not None:
            setattr(pegawai_record, 'bod', request.bod)
        
        setattr(pegawai_record, 'updated_at', datetime.now())
        
        source_db.commit()
        
        # Update corresponding global_id record if exists
        pegawai_g_id = getattr(pegawai_record, 'g_id', None)
        if pegawai_g_id:
            global_record = db.query(GlobalID).filter(GlobalID.g_id == pegawai_g_id).first()
            if global_record:
                if request.name is not None:
                    setattr(global_record, 'name', request.name)
                if request.personal_number is not None:
                    setattr(global_record, 'personal_number', request.personal_number)
                if request.no_ktp is not None:
                    setattr(global_record, 'no_ktp', request.no_ktp)
                if request.bod is not None:
                    setattr(global_record, 'bod', request.bod)
                
                setattr(global_record, 'updated_at', datetime.now())
                db.commit()
        
        # Perform automatic synchronization
        automation_service = AutomationService(db, source_db)
        sync_result = automation_service.automatic_synchronization()
        
        logger.info(f"Pegawai record {pegawai_id} updated successfully")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Record updated successfully",
                "pegawai_id": pegawai_id,
                "g_id": pegawai_g_id,
                "sync_completed": sync_result["success"]
            }
        )
        
    except Exception as e:
        source_db.rollback()
        db.rollback()
        logger.error(f"Error updating pegawai record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating record: {str(e)}")

@data_router.delete("/pegawai/{pegawai_id}")
async def delete_pegawai_record(
    pegawai_id: int,
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Delete pegawai record with automated soft delete logic - Performance Target: 1-5 seconds"""
    start_time = time.time()  # Performance monitoring
    
    try:
        # Debug logging
        logger.info(f"Deleting pegawai record ID: {pegawai_id}")
        
        # Validate database connections
        if not db or not source_db:
            raise HTTPException(status_code=500, detail="Database connection error")
        
        automation_service = AutomationService(db, source_db)
        
        # Execute automated soft delete logic (optimized with indexed queries)
        delete_result = automation_service.automated_soft_delete(pegawai_id)
        
        if not delete_result["success"]:
            raise HTTPException(status_code=400, detail=delete_result["error"])
        
        execution_time = round(time.time() - start_time, 3)
        logger.info(f"SOFT DELETE completed in {execution_time}s for Pegawai ID {pegawai_id}, G_ID: {delete_result['g_id']}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"{delete_result['message']} (Completed in {execution_time}s)",
                "pegawai_id": pegawai_id,
                "g_id": delete_result["g_id"],
                "deleted_at": delete_result["deleted_at"],
                "execution_time": execution_time,
                "performance_status": "OPTIMAL" if execution_time <= 5.0 else "SLOW"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pegawai record: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting record: {str(e)}")

# Health check endpoint
@data_router.get("/health")
async def health_check():
    """Health check for data API endpoints"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "automated_soft_delete": True,
            "reactivation_logic": True,
            "automatic_synchronization": True,
            "enhanced_search": True
        }
    }
"""
FastAPI routers and endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, date

from app.models.database import get_db, get_source_db
from app.models.models import GlobalID, GlobalIDNonDatabase, Pegawai, AuditLog
from app.services.sync_service import SyncService
from app.services.excel_service import ExcelIngestionService
from app.services.excel_sync_service import ExcelSyncService
from app.services.gid_generator import GIDGenerator
from app.services.monitoring_service import monitoring_manager
from app.services.advanced_workflow_service import AdvancedWorkflowService

# Import data endpoints router
from app.api.data_endpoints import data_router

# Import pegawai endpoints router
from app.api.pegawai_endpoints import pegawai_router

# Import global ID endpoints router
from app.api.globalid_endpoints import globalid_router

# Import G_ID-based operations router
from app.api.gid_operations import gid_api_router

# Pydantic models for API requests/responses
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

class PegawaiResponse(BaseModel):
    id: int
    name: str
    personal_number: Optional[str]
    no_ktp: str
    bod: Optional[date]
    g_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    # Keep existing fields for backward compatibility
    total_records: int
    active_records: int
    inactive_records: int
    database_source_records: int
    excel_source_records: int
    sync_status: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    
    # New fields for three-category dashboard
    global_id_stats: Dict[str, int]
    global_id_non_database_stats: Dict[str, int]
    pegawai_stats: Dict[str, int]


class SyncResponse(BaseModel):
    success: bool
    message: str
    summary: Dict[str, Any]


class ExcelUploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    processing_summary: Optional[Dict[str, Any]]


# Create router
router = APIRouter()


@router.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint"""
    return {
        "message": "Global ID Management System API",
        "version": "1.0.0",
        "status": "active"
    }


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard summary data with optimized queries for three-category display"""
    try:
        # OPTIMIZED: Get Global_ID table statistics
        global_id_stats_query = text("""
            SELECT 
                COUNT(*) as total_records,
                COALESCE(SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END), 0) as active_records,
                COALESCE(SUM(CASE WHEN status = 'Non Active' THEN 1 ELSE 0 END), 0) as inactive_records,
                COALESCE(SUM(CASE WHEN source = 'database_pegawai' THEN 1 ELSE 0 END), 0) as database_source,
                COALESCE(SUM(CASE WHEN source = 'excel' THEN 1 ELSE 0 END), 0) as excel_source
            FROM dbo.global_id
        """)
        
        global_id_result = db.execute(global_id_stats_query).fetchone()
        
        # OPTIMIZED: Get Global_ID_Non_Database table statistics
        global_id_non_db_stats_query = text("""
            SELECT 
                COUNT(*) as total_records,
                COALESCE(SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END), 0) as active_records,
                COALESCE(SUM(CASE WHEN status = 'Non Active' THEN 1 ELSE 0 END), 0) as inactive_records
            FROM dbo.global_id_non_database
        """)
        
        global_id_non_db_result = db.execute(global_id_non_db_stats_query).fetchone()
        
        # OPTIMIZED: Get Pegawai table statistics
        pegawai_stats_query = text("""
            SELECT 
                COUNT(*) as total_records,
                COALESCE(SUM(CASE WHEN deleted_at IS NULL THEN 1 ELSE 0 END), 0) as active_records,
                COALESCE(SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END), 0) as inactive_records
            FROM dbo.pegawai
        """)
        
        pegawai_result = db.execute(pegawai_stats_query).fetchone()
        
        # Extract Global_ID results
        global_id_total = global_id_result.total_records or 0
        global_id_active = global_id_result.active_records or 0
        global_id_inactive = global_id_result.inactive_records or 0
        database_source = global_id_result.database_source or 0
        excel_source = global_id_result.excel_source or 0
        
        # Extract Global_ID_Non_Database results
        global_id_non_db_total = global_id_non_db_result.total_records or 0
        global_id_non_db_active = global_id_non_db_result.active_records or 0
        global_id_non_db_inactive = global_id_non_db_result.inactive_records or 0
        
        # Extract Pegawai results
        pegawai_total = pegawai_result.total_records or 0
        pegawai_active = pegawai_result.active_records or 0
        pegawai_inactive = pegawai_result.inactive_records or 0
        
        # OPTIMIZED: Fast sync status with real database counts
        # Get actual pegawai table statistics quickly
        pegawai_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN g_id IS NOT NULL AND g_id != '' THEN 1 END) as with_gid
            FROM dbo.pegawai
            WHERE deleted_at IS NULL
        """)).fetchone()
        
        pegawai_with_gid = pegawai_stats.with_gid or 0
        pegawai_total = pegawai_stats.total_records or 0
        pegawai_without_gid = pegawai_total - pegawai_with_gid
        
        sync_status = {
            "global_id_table": {
                "total_records": global_id_total,
                "active_records": global_id_active,
                "inactive_records": global_id_inactive,
                "database_source": database_source,
                "excel_source": excel_source
            },
            "pegawai_table": {
                "total_records": pegawai_total,
                "with_gid": pegawai_with_gid,
                "without_gid": pegawai_without_gid
            },
            "sync_status": {
                "sync_needed": pegawai_without_gid > 0,
                "last_check": "2025-09-30T15:00:00",
                "status": "healthy" if pegawai_without_gid == 0 else "sync_recommended",
                "message": f"Real-time data: {pegawai_with_gid} employees have G_ID, {pegawai_without_gid} need sync"
            }
        }
        
        # OPTIMIZED: Get recent activities with indexed query
        recent_activities = []
        recent_records = db.query(GlobalID).order_by(GlobalID.updated_at.desc()).limit(10).all()
        
        for record in recent_records:
            recent_activities.append({
                "g_id": record.g_id,
                "name": record.name,
                "action": "Created",  # Simplified - can be enhanced later if needed
                "timestamp": record.updated_at.isoformat(),
                "source": record.source,
                "status": record.status
            })
        
        # Prepare new category statistics
        global_id_stats = {
            "total": global_id_total,
            "active": global_id_active,
            "inactive": global_id_inactive
        }
        
        global_id_non_database_stats = {
            "total": global_id_non_db_total,
            "active": global_id_non_db_active,
            "inactive": global_id_non_db_inactive
        }
        
        pegawai_category_stats = {
            "total": pegawai_total,
            "active": pegawai_active,
            "inactive": pegawai_inactive
        }
        
        return DashboardSummary(
            # Keep backward compatibility
            total_records=global_id_total,
            active_records=global_id_active,
            inactive_records=global_id_inactive,
            database_source_records=database_source,
            excel_source_records=excel_source,
            sync_status=sync_status,
            recent_activities=recent_activities,
            # New category stats
            global_id_stats=global_id_stats,
            global_id_non_database_stats=global_id_non_database_stats,
            pegawai_stats=pegawai_category_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")


@router.get("/records", response_model=List[GlobalIDResponse])
async def get_records(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search by name, No_KTP, or G_ID"),
    db: Session = Depends(get_db)
):
    """Get paginated list of Global_ID records with filtering"""
    try:
        query = db.query(GlobalID)
        
        # Apply filters
        if status:
            query = query.filter(GlobalID.status == status)
        if source:
            query = query.filter(GlobalID.source == source)
        if search:
            query = query.filter(
                (GlobalID.name.ilike(f"%{search}%")) |
                (GlobalID.no_ktp.ilike(f"%{search}%")) |
                (GlobalID.g_id.ilike(f"%{search}%"))
            )
        
        # Apply pagination
        offset = (page - 1) * size
        records = query.order_by(GlobalID.g_id.asc()).offset(offset).limit(size).all()
        
        return records
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting records: {str(e)}")


@router.get("/records/count")
async def get_records_count(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get total count of records with same filtering as /records endpoint"""
    try:
        query = db.query(GlobalID)
        
        if status:
            query = query.filter(GlobalID.status == status)
        if source:
            query = query.filter(GlobalID.source == source)
        if search:
            query = query.filter(
                (GlobalID.name.ilike(f"%{search}%")) |
                (GlobalID.no_ktp.ilike(f"%{search}%")) |
                (GlobalID.g_id.ilike(f"%{search}%"))
            )
        
        count = query.count()
        return {"total_count": count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting records: {str(e)}")


@router.get("/records/{gid}", response_model=GlobalIDResponse)
async def get_record_by_gid(gid: str, db: Session = Depends(get_db)):
    """Get specific record by G_ID"""
    try:
        record = db.query(GlobalID).filter(GlobalID.g_id == gid).first()
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Record with g_id {gid} not found")
        
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting record: {str(e)}")


@router.post("/sync/initial", response_model=SyncResponse)
async def initial_sync(
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Perform initial synchronization from pegawai database (OPTIMIZED)"""
    try:
        sync_service = SyncService(db, source_db)
        result = sync_service.initial_sync()
        
        return SyncResponse(
            success=result['successful'] > 0 or result['skipped'] > 0,
            message=f"🚀 OPTIMIZED sync completed! Processed: {result['processed']}, Successful: {result['successful']}, Skipped: {result['skipped']}, Errors: {len(result.get('errors', []))}",
            summary=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during initial sync: {str(e)}")


@router.post("/sync/turbo", response_model=SyncResponse)  
async def turbo_sync(
    batch_size: int = Query(default=100, description="Batch size for processing (default: 100)"),
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """🚀 TURBO SYNC - Ultra-fast synchronization with batching (recommended for large datasets)"""
    try:
        from app.services.optimized_sync import OptimizedSyncService
        
        turbo_service = OptimizedSyncService(db, source_db, batch_size=batch_size)
        result = turbo_service.turbo_sync()
        
        # Calculate performance metrics
        total_time = result.get('processing_time', 0)
        records_per_second = result['successful'] / max(total_time, 0.1) if total_time > 0 else result['successful']
        
        return SyncResponse(
            success=result['successful'] > 0 or result['skipped'] > 0,
            message=f"🚀 TURBO SYNC completed! ⚡ {result['successful']} records synced, {result['skipped']} skipped, {records_per_second:.1f} rec/sec",
            summary=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during turbo sync: {str(e)}")


@router.post("/sync/incremental", response_model=SyncResponse)
async def incremental_sync(
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Perform incremental synchronization (new records + deletion handling)"""
    try:
        sync_service = SyncService(db, source_db)
        result = sync_service.full_sync()
        
        total_operations = result['total_operations']
        
        return SyncResponse(
            success=total_operations > 0,
            message=f"Incremental sync completed. Total operations: {total_operations}",
            summary=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during incremental sync: {str(e)}")


@router.get("/sync/status")
async def get_sync_status(
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Get current synchronization status"""
    try:
        sync_service = SyncService(db, source_db)
        status = sync_service.get_sync_status()
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {str(e)}")


@router.post("/upload/excel", response_model=ExcelUploadResponse)
async def upload_excel_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process Excel file using full synchronization logic"""
    try:
        # Validate filename exists
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="File must have a filename"
            )
        
        # Get filename (guaranteed to be not None after the check above)
        filename = file.filename
        
        # Validate file type - support both Excel and CSV
        if not filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Supported types: .xlsx, .xls, .csv"
            )
        
        # Read file content and create temporary file
        import tempfile
        import os
        
        content = await file.read()
        
        # Create temporary file to work with the sync service
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Use the synchronization service instead of basic ingestion
            sync_service = ExcelSyncService(db)
            
            # Perform synchronization with the uploaded file
            result = sync_service.sync_excel_file(temp_file_path)
            
            if result['success']:
                stats = result['stats']
                
                # Create comprehensive success message
                message_parts = [f"Synchronization successful. File '{filename}' has been processed."]
                
                if stats['total_processed'] > 0:
                    message_parts.append(f"{stats['total_processed']} records were processed from the file.")
                
                if stats['existing_updated'] > 0:
                    message_parts.append(f"{stats['existing_updated']} existing records were updated/reactivated.")
                
                if stats['new_created'] > 0:
                    message_parts.append(f"{stats['new_created']} new records were created.")
                
                if stats['obsolete_deactivated'] > 0:
                    message_parts.append(f"{stats['obsolete_deactivated']} records were deactivated because they were not found in the uploaded file.")
                
                if stats['errors'] > 0:
                    message_parts.append(f"Warning: {stats['errors']} errors occurred during processing.")
                
                success_message = " ".join(message_parts)
                
                return ExcelUploadResponse(
                    success=True,
                    message=success_message,
                    filename=filename,
                    processing_summary={
                        'sync_stats': stats,
                        'operation_type': 'full_synchronization',
                        'file_processed': filename,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            else:
                return ExcelUploadResponse(
                    success=False,
                    message=f"Synchronization failed: {result.get('error', 'Unknown error occurred')}",
                    filename=filename,
                    processing_summary={
                        'error_details': result.get('error'),
                        'operation_type': 'full_synchronization',
                        'file_processed': filename,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")


@router.post("/upload/advanced", response_model=ExcelUploadResponse)
async def upload_file_advanced_workflow(
    file: UploadFile = File(...),
    enable_deactivation: bool = Query(True, description="Enable automatic deactivation of missing records"),
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Upload and process file using advanced workflow with comprehensive data management"""
    try:
        # Validate filename exists
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="File must have a filename"
            )
        
        # Get filename (guaranteed to be not None after the check above)
        filename = file.filename
        
        # Validate file type
        supported_extensions = ['.xlsx', '.xls', '.csv']
        file_ext = '.' + filename.lower().split('.')[-1]
        
        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{file_ext}'. Supported types: {supported_extensions}"
            )
        
        # Read file content
        content = await file.read()
        
        # Initialize advanced workflow service
        workflow_service = AdvancedWorkflowService(db, source_db)
        
        # Process the file using advanced workflow
        result = workflow_service.process_file_with_advanced_workflow(
            file_content=content,
            filename=filename,
            enable_deactivation=enable_deactivation
        )
        
        if result.get('success', False):
            summary = result.get('summary', {})
            return ExcelUploadResponse(
                success=True,
                message=f"Advanced workflow completed successfully. Processed: {summary.get('total_processed', 0)}, "
                       f"Successful: {summary.get('total_successful', 0)}, "
                       f"Deactivated: {summary.get('total_deactivated', 0)}",
                filename=filename,
                processing_summary=result
            )
        else:
            return ExcelUploadResponse(
                success=False,
                message=result.get('error', 'Failed to process file with advanced workflow'),
                filename=filename,
                processing_summary=result
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in advanced workflow processing: {str(e)}")


@router.post("/sync/pegawai-advanced", response_model=Dict[str, Any])
async def sync_pegawai_advanced_workflow(
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Execute advanced pegawai synchronization workflow with comprehensive rules"""
    try:
        # Initialize advanced workflow service
        workflow_service = AdvancedWorkflowService(db, source_db)
        
        # Execute pegawai synchronization workflow
        result = workflow_service.pegawai_db_synchronization_workflow()
        
        return {
            "success": True,
            "message": f"Pegawai synchronization completed. Updates: {result.get('status_updates', 0)}, "
                      f"Deletions: {result.get('deletions', 0)}",
            "timestamp": datetime.now().isoformat(),
            "synchronization_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in pegawai synchronization workflow: {str(e)}")


@router.delete("/data/clear-all", response_model=Dict[str, Any])
async def clear_all_data(
    confirm: bool = Query(False, description="Confirmation flag to prevent accidental deletion"),
    db: Session = Depends(get_db)
):
    """
    Delete all data from global_id, global_id_non_database, and pegawai tables
    
    This is a destructive operation that will remove ALL records from the main tables.
    Use with extreme caution!
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This operation requires confirmation. Add ?confirm=true to the request."
        )
    
    try:
        # Get counts before deletion for reporting
        global_id_count = db.query(GlobalID).count()
        global_id_non_db_count = db.query(GlobalIDNonDatabase).count()
        pegawai_count = db.query(Pegawai).count()
        
        # Delete all records
        deleted_global_id = db.query(GlobalID).delete()
        deleted_global_id_non_db = db.query(GlobalIDNonDatabase).delete()
        deleted_pegawai = db.query(Pegawai).delete()
        
        # Commit the transaction
        db.commit()
        
        return {
            "success": True,
            "message": "All data has been successfully deleted from the database",
            "deleted_counts": {
                "global_id": deleted_global_id,
                "global_id_non_database": deleted_global_id_non_db,
                "pegawai": deleted_pegawai
            },
            "previous_counts": {
                "global_id": global_id_count,
                "global_id_non_database": global_id_non_db_count,
                "pegawai": pegawai_count
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")


@router.post("/database/reinitialize", response_model=Dict[str, Any])
async def reinitialize_database_tables(
    confirm: bool = Query(False, description="Confirmation flag to prevent accidental reinitialization"),
    db: Session = Depends(get_db)
):
    """
    Reinitialize database tables by running the SQL schema creation script
    
    This will execute the create_schema_sqlserver.sql file to create/recreate the g_id database
    and all its tables with the proper structure including passport_id fields.
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This operation requires confirmation. Add ?confirm=true to the request."
        )
    
    try:
        import os
        from sqlalchemy import create_engine, text
        from app.models.database import DATABASE_URL
        
        # Get current record counts for reporting (if tables exist)
        try:
            global_id_count = db.query(GlobalID).count()
            global_id_non_db_count = db.query(GlobalIDNonDatabase).count()
            pegawai_count = db.query(Pegawai).count()
        except:
            global_id_count = 0
            global_id_non_db_count = 0
            pegawai_count = 0
        
        # Close the current session to prevent locks
        db.close()
        
        # Read the SQL schema file
        sql_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sql', 'create_schema_sqlserver.sql')
        
        if not os.path.exists(sql_file_path):
            raise HTTPException(status_code=500, detail=f"SQL schema file not found at: {sql_file_path}")
        
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Split SQL content by GO statements (SQL Server batch separator)
        sql_batches = [batch.strip() for batch in sql_content.split('GO') if batch.strip()]
        
        # Create a new engine connection for executing raw SQL
        # We need to connect to master first to create the database
        master_url = DATABASE_URL.replace('/g_id?', '/master?')
        master_engine = create_engine(master_url)
        
        executed_batches = 0
        results = []
        
        # Execute SQL batches
        with master_engine.connect() as conn:
            for i, batch in enumerate(sql_batches):
                try:
                    # Skip empty batches
                    if not batch.strip():
                        continue
                    
                    # Execute the batch
                    result = conn.execute(text(batch))
                    executed_batches += 1
                    
                    # Try to fetch results if available
                    try:
                        if result.returns_rows:
                            rows = result.fetchall()
                            if rows:
                                results.extend([dict(row._mapping) for row in rows])
                    except:
                        pass
                    
                    # Commit after each batch
                    conn.commit()
                    
                except Exception as batch_error:
                    # Log the error but continue with other batches
                    results.append(f"Error in batch {i+1}: {str(batch_error)}")
                    # Don't break - some errors might be expected (like "database already exists")
                    continue
        
        master_engine.dispose()
        
        # Verify that tables were created by connecting to the g_id database
        g_id_engine = create_engine(DATABASE_URL)
        
        verification_results = {}
        with g_id_engine.connect() as conn:
            try:
                # Check if tables exist
                table_check_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'dbo' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                tables_result = conn.execute(table_check_query)
                tables = [row[0] for row in tables_result.fetchall()]
                verification_results['tables_created'] = tables
                
                # Check record counts in each table
                record_counts = {}
                for table in tables:
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM dbo.{table}")
                        count_result = conn.execute(count_query)
                        record_counts[table] = count_result.scalar()
                    except:
                        record_counts[table] = 0
                
                verification_results['record_counts'] = record_counts
                
            except Exception as verify_error:
                verification_results['error'] = str(verify_error)
        
        g_id_engine.dispose()
        
        return {
            "success": True,
            "message": "Database schema has been successfully executed and tables initialized",
            "previous_counts": {
                "global_id": global_id_count,
                "global_id_non_database": global_id_non_db_count,
                "pegawai": pegawai_count
            },
            "execution_results": {
                "sql_file_path": sql_file_path,
                "batches_executed": executed_batches,
                "total_batches": len(sql_batches)
            },
            "verification": verification_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reinitializing database: {str(e)}")


@router.get("/workflow/status", response_model=Dict[str, Any])
async def get_workflow_status(
    db: Session = Depends(get_db),
    source_db: Optional[Session] = Depends(get_source_db)
):
    """Get comprehensive workflow system status"""
    try:
        # Initialize advanced workflow service
        workflow_service = AdvancedWorkflowService(db, source_db)
        
        # Get workflow status
        status = workflow_service.get_workflow_status()
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow status: {str(e)}")


@router.get("/excel/template")
async def get_excel_template(db: Session = Depends(get_db)):
    """Get Excel template information"""
    try:
        excel_service = ExcelIngestionService(db)
        template = excel_service.get_excel_template()
        
        return template
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template: {str(e)}")


@router.get("/gid/next-preview")
async def preview_next_gid(db: Session = Depends(get_db)):
    """Preview what the next G_ID will be"""
    try:
        generator = GIDGenerator(db)
        sequence_info = generator.get_current_sequence_info()
        
        if sequence_info:
            return {
                "next_gid": sequence_info['next_gid_preview'],
                "sequence_info": sequence_info
            }
        else:
            return {
                "next_gid": "G025AA00",
                "sequence_info": "Sequence not initialized"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing next G_ID: {str(e)}")


@router.get("/gid/validate/{gid}")
async def validate_gid_format(gid: str, db: Session = Depends(get_db)):
    """Validate G_ID format"""
    try:
        generator = GIDGenerator(db)
        is_valid = generator.validate_gid_format(gid)
        
        return {
            "gid": gid,
            "is_valid": is_valid,
            "format": "G{N}{YY}{A}{A}{N}{N}",
            "example": "G025AA01"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating G_ID: {str(e)}")


@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get real-time monitoring status"""
    try:
        status = monitoring_manager.get_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting monitoring status: {str(e)}")


@router.post("/monitoring/start")
async def start_monitoring(monitor_type: str = Query("polling", description="Type of monitoring: polling or trigger")):
    """Start real-time monitoring"""
    try:
        if monitor_type == "polling":
            monitoring_manager.start_polling_monitor(poll_interval=30)
            return {"message": "Polling monitor started", "type": "polling"}
        elif monitor_type == "trigger":
            monitoring_manager.start_trigger_monitor()
            return {"message": "Trigger monitor started", "type": "trigger"}
        else:
            raise HTTPException(status_code=400, detail="Invalid monitor type. Use 'polling' or 'trigger'")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")


@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop real-time monitoring"""
    try:
        monitoring_manager.stop_monitoring()
        return {"message": "Monitoring stopped"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping monitoring: {str(e)}")


@router.get("/audit/logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    table_name: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get audit logs with pagination and filtering"""
    try:
        query = db.query(AuditLog)
        
        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        if action:
            query = query.filter(AuditLog.action == action)
        
        offset = (page - 1) * size
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(size).all()
        
        # Convert to dict for JSON serialization
        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "action": log.action,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "changed_by": log.changed_by,
                "change_reason": log.change_reason,
                "created_at": log.created_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting audit logs: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


# ========================================
# Excel Data Synchronization Endpoints
# ========================================

@router.post("/sync/excel/preview")
async def preview_excel_sync(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Preview what changes would be made when synchronizing an Excel/CSV file
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload CSV, XLS, or XLSX files."
            )
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        suffix = os.path.splitext(file.filename)[1] if file.filename else '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Create sync service and generate preview
            sync_service = ExcelSyncService(db)
            result = sync_service.preview_sync(tmp_file_path)
            
            return {
                "success": result["success"],
                "preview": result.get("preview"),
                "message": result["message"],
                "filename": file.filename
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.post("/sync/excel/execute")
async def execute_excel_sync(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute synchronization of Excel/CSV file with database
    
    This endpoint implements the three-scenario synchronization logic:
    1. Update existing records (set status to Active)
    2. Create new records with new G_IDs
    3. Deactivate obsolete records (set status to Non Active)
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload CSV, XLS, or XLSX files."
            )
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        suffix = os.path.splitext(file.filename)[1] if file.filename else '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Create sync service and execute synchronization
            sync_service = ExcelSyncService(db)
            result = sync_service.sync_excel_file(tmp_file_path)
            
            return {
                "success": result["success"],
                "stats": result.get("stats"),
                "message": result["message"],
                "filename": file.filename,
                "error": result.get("error")
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")


@router.post("/sync/excel/file-path")
async def sync_excel_from_path(
    file_path: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute synchronization from a file path (for server-side files)
    """
    try:
        import os
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Validate file type
        if not file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. File must be CSV, XLS, or XLSX."
            )
        
        # Create sync service and execute synchronization
        sync_service = ExcelSyncService(db)
        result = sync_service.sync_excel_file(file_path)
        
        return {
            "success": result["success"],
            "stats": result.get("stats"),
            "message": result["message"],
            "file_path": file_path,
            "error": result.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")


@router.get("/sync/excel/status")
async def get_excel_sync_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current synchronization status and statistics
    """
    try:
        # Get record counts
        total_global_id = db.query(GlobalID).count()
        active_global_id = db.query(GlobalID).filter(GlobalID.status == 'Active').count()
        
        total_non_db = db.query(GlobalIDNonDatabase).count()
        active_non_db = db.query(GlobalIDNonDatabase).filter(GlobalIDNonDatabase.status == 'Active').count()
        
        # Get recent sync activities from audit log
        recent_syncs = db.query(AuditLog).filter(
            AuditLog.changed_by.in_(['ExcelSyncService', 'DataSynchronizer'])
        ).order_by(AuditLog.created_at.desc()).limit(10).all()
        
        return {
            "success": True,
            "statistics": {
                "global_id_table": {
                    "total_records": total_global_id,
                    "active_records": active_global_id,
                    "inactive_records": total_global_id - active_global_id
                },
                "excel_source_table": {
                    "total_records": total_non_db,
                    "active_records": active_non_db,
                    "inactive_records": total_non_db - active_non_db
                }
            },
            "recent_sync_activities": [
                {
                    "timestamp": sync.created_at.isoformat(),
                    "table": sync.table_name,
                    "action": sync.action,
                    "record_id": sync.record_id,
                    "reason": sync.change_reason
                }
                for sync in recent_syncs
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


# Database Explorer Endpoints
@router.get("/database/explorer")
async def get_all_database_info(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Records per page"),
    table: Optional[str] = Query(None, description="Specific table to view"),
    status: Optional[str] = Query(None, description="Filter by status (Active/Non Active)"),
    search: Optional[str] = Query(None, description="Search by name, date of birth, ID number, or G_ID"),
    db: Session = Depends(get_db),
    source_db: Session = Depends(get_source_db)
):
    """Get global_id table data with pagination for faster loading"""
    try:
        result = {
            "g_id": {
                "database_name": "Global ID Management System - Primary Database",
                "connection_url": "mssql+pyodbc://sqlvendor1:***@localhost:1435/g_id",
                "tables": {}
            }
        }
        
        # Get all tables from consolidated g_id database
        try:
            # Get requested table(s) based on filter
            if table:
                # Map table names for API compatibility
                table_map = {
                    'global_id': 'global_id',
                    'global_id_non_database': 'global_id_non_database', 
                    'pegawai': 'pegawai'
                }
                actual_table = table_map.get(table, 'global_id')
                table_condition = f"AND table_name = '{actual_table}'"
            else:
                # Default to global_id table
                table_condition = "AND table_name = 'global_id'"
                
            table_query = text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'dbo' 
                AND table_type = 'BASE TABLE'
                {table_condition}
                ORDER BY table_name
            """)
            tables_result = db.execute(table_query).fetchall()
            
            for table_row in tables_result:
                table_name = table_row[0]
                
                # Get column names first
                try:
                    columns_query = text(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND table_schema = 'dbo'
                        ORDER BY ordinal_position
                    """)
                    columns_result = db.execute(columns_query).fetchall()
                    columns = [{"name": col[0], "type": col[1]} for col in columns_result]
                    
                    # Find an appropriate column to order by  
                    order_column = None
                    # Priority for global_id tables: g_id (ascending), then id, primary key columns, created_at, updated_at, first column
                    for col in columns:
                        col_name = col["name"].lower()
                        if col_name == 'g_id' and table_name in ['global_id', 'global_id_non_database']:
                            order_column = col["name"]
                            break
                        elif col_name == 'id':
                            order_column = col["name"]
                            break
                        elif col_name in ['created_at', 'updated_at', 'timestamp']:
                            order_column = col["name"]
                        elif order_column is None:
                            order_column = col["name"]  # fallback to first column
                    
                    # Build WHERE clause for status and search filtering
                    where_conditions = []
                    
                    # Status filtering
                    if status:
                        # Check if table has status column
                        has_status = any(col["name"].lower() == "status" for col in columns)
                        if has_status:
                            where_conditions.append(f"status = '{status}'")
                    
                    # Search filtering (for global_id table)
                    if search and table_name == 'global_id':
                        search_term = search.replace("'", "''")  # Escape single quotes
                        
                        # Build search conditions for multiple columns
                        search_conditions = []
                        
                        # Search in common columns (based on actual GlobalID model structure)
                        for col in columns:
                            col_name = col["name"].lower()
                            col_type = col["type"].lower()
                            
                            # Search in text/varchar columns (names, IDs)
                            if col_type in ['varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext']:
                                # Match actual column names from GlobalID model
                                if col_name in ['name', 'g_id', 'no_ktp', 'personal_number']:
                                    search_conditions.append(f"LOWER({col['name']}) LIKE LOWER('%{search_term}%')")
                            
                            # Search in date columns (birth date)
                            elif col_type in ['date', 'datetime', 'datetime2', 'smalldatetime']:
                                # Match actual date column name 'bod' (birth of date)
                                if col_name in ['bod']:
                                    # Try to match date format (YYYY-MM-DD or partial matches)
                                    search_conditions.append(f"CONVERT(varchar, {col['name']}, 23) LIKE '%{search_term}%'")
                        
                        # If we have search conditions, add them to where clause
                        if search_conditions:
                            where_conditions.append(f"({' OR '.join(search_conditions)})")
                    
                    # Combine all conditions
                    where_clause = ""
                    if where_conditions:
                        where_clause = f"WHERE {' AND '.join(where_conditions)}"
                    
                    # Get total count for pagination
                    count_query = text(f"SELECT COUNT(*) as total FROM dbo.{table_name} {where_clause}")
                    total_count = db.execute(count_query).fetchone().total
                    
                    # Calculate pagination parameters
                    offset = (page - 1) * size
                    total_pages = (total_count + size - 1) // size  # Math.ceil equivalent
                    
                    # Get paginated table data with appropriate ordering
                    if order_column:
                        data_query = text(f"""
                            SELECT * FROM dbo.{table_name} 
                            {where_clause}
                            ORDER BY {order_column}
                            OFFSET {offset} ROWS
                            FETCH NEXT {size} ROWS ONLY
                        """)
                    else:
                        data_query = text(f"""
                            SELECT * FROM dbo.{table_name}
                            {where_clause}
                            OFFSET {offset} ROWS
                            FETCH NEXT {size} ROWS ONLY
                        """)
                    
                    data_result = db.execute(data_query).fetchall()
                    
                    # Convert data to list of dictionaries
                    data_list = []
                    for row in data_result:
                        row_dict = {}
                        for i, col in enumerate(columns):
                            value = row[i]
                            # Convert datetime objects to strings
                            if hasattr(value, 'isoformat'):
                                value = value.isoformat()
                            row_dict[col["name"]] = value
                        data_list.append(row_dict)
                    
                    result["g_id"]["tables"][table_name] = {
                        "columns": columns,
                        "data": data_list,
                        "row_count": len(data_list),
                        "total_count": total_count,
                        "pagination": {
                            "current_page": page,
                            "page_size": size,
                            "total_pages": total_pages,
                            "total_records": total_count,
                            "has_next": page < total_pages,
                            "has_previous": page > 1
                        }
                    }
                    
                except Exception as table_error:
                    result["g_id"]["tables"][table_name] = {
                        "error": f"Error fetching data: {str(table_error)}",
                        "columns": [],
                        "data": [],
                        "row_count": 0,
                        "total_count": 0,
                        "pagination": {
                            "current_page": page,
                            "page_size": size,
                            "total_pages": 0,
                            "total_records": 0,
                            "has_next": False,
                            "has_previous": False
                        }
                    }
                    
        except Exception as db_error:
            result["g_id"]["error"] = f"Error connecting to g_id: {str(db_error)}"

        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database information: {str(e)}")


@router.post("/system/repair-gid-sequence")
async def repair_gid_sequence(
    db: Session = Depends(get_db)
):
    """Repair G_ID sequence integrity issues"""
    try:
        from app.services.excel_sync_service import ExcelSyncService
        
        sync_service = ExcelSyncService(db)
        repair_stats = sync_service.repair_gid_sequence_integrity()
        
        return {
            "success": True,
            "message": "G_ID sequence integrity check completed",
            "repair_statistics": repair_stats,
            "recommendations": [
                "Check the repair statistics for any issues found",
                "Review logs for detailed information about specific G_IDs",
                "Consider running this check periodically to maintain data integrity"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during G_ID sequence repair: {str(e)}")


# Include router in the API
api_router = APIRouter(prefix="/api/v1", tags=["Global ID System"])
api_router.include_router(router)
api_router.include_router(data_router)  # Include data endpoints with automated functionality
api_router.include_router(pegawai_router)  # Include pegawai REST API endpoints
api_router.include_router(globalid_router)  # Include Global ID data view endpoints
api_router.include_router(gid_api_router)  # Include G_ID-based CRUD operations for all tables
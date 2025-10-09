"""
Data synchronization service for managing sync between pegawai and Global_ID tables
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_

from app.models.models import GlobalID, Pegawai, AuditLog
from app.services.gid_generator import GIDGenerator

logger = logging.getLogger(__name__)


class SyncService:
    """Handles synchronization between pegawai and Global_ID tables"""
    
    def __init__(self, main_db: Session, source_db: Session):
        self.main_db = main_db
        self.source_db = source_db
        self.gid_generator = GIDGenerator(main_db)
    
    def _check_tables_exist(self) -> Dict[str, Any]:
        """Check if required tables exist in the database"""
        from sqlalchemy import text
        
        required_tables = ['global_id', 'global_id_non_database', 'pegawai', 'g_id_sequence', 'audit_log']
        missing_tables = []
        
        try:
            # Check if tables exist
            for table in required_tables:
                try:
                    # Try to query the table schema
                    result = self.main_db.execute(text(f"""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = 'dbo' 
                        AND table_name = '{table}'
                    """))
                    
                    count = result.scalar()
                    if count == 0:
                        missing_tables.append(table)
                        
                except Exception as table_error:
                    logger.warning(f"Error checking table {table}: {str(table_error)}")
                    missing_tables.append(table)
            
            return {
                'all_exist': len(missing_tables) == 0,
                'missing_tables': missing_tables,
                'existing_tables': [t for t in required_tables if t not in missing_tables]
            }
            
        except Exception as e:
            logger.error(f"Error checking tables existence: {str(e)}")
            return {
                'all_exist': False,
                'missing_tables': required_tables,
                'existing_tables': [],
                'error': str(e)
            }
    
    def initial_sync(self) -> Dict[str, Any]:
        """
        Perform initial synchronization from pegawai table to Global_ID table (OPTIMIZED)
        Returns summary of sync operation
        """
        try:
            logger.info("Starting optimized initial synchronization...")
            
            # Get all active records from pegawai table
            pegawai_records = self.source_db.query(Pegawai).filter(
                Pegawai.deleted_at.is_(None)
            ).all()
            
            logger.info(f"Found {len(pegawai_records)} pegawai records to process")
            
            # Get all existing no_ktp values in one query to avoid N+1 problem
            existing_no_ktps = set(
                row[0] for row in self.main_db.query(GlobalID.no_ktp).all()
            )
            logger.info(f"Found {len(existing_no_ktps)} existing no_ktp records")
            
            sync_summary = {
                'total_source_records': len(pegawai_records),
                'processed': 0,
                'successful': 0,
                'skipped': 0,
                'errors': []
            }
            
            # Batch processing lists
            global_records_to_add = []
            pegawai_updates = []
            audit_records = []
            
            # Filter records that need G_IDs (skip duplicates)
            records_needing_gids = []
            for pegawai in pegawai_records:
                sync_summary['processed'] += 1
                
                # DISABLED: Check if no_ktp already exists (in-memory check, much faster)
                # User wants ALL data processed regardless of duplicates
                # if pegawai.no_ktp in existing_no_ktps:
                #     sync_summary['skipped'] += 1
                #     logger.debug(f"Skipping duplicate no_ktp: {pegawai.no_ktp}")
                #     continue
                
                records_needing_gids.append(pegawai)
            
            # BATCH OPTIMIZATION: Generate all G_IDs at once
            logger.info(f"🚀 Generating {len(records_needing_gids)} G_IDs in batch...")
            if records_needing_gids:
                batch_gids = self.gid_generator.generate_batch_gids(len(records_needing_gids))
            else:
                batch_gids = []
            
            # Process records with pre-generated G_IDs
            for i, pegawai in enumerate(records_needing_gids):
                try:
                    # Use pre-generated G_ID
                    new_gid = batch_gids[i]
                    
                    # Create new record in Global_ID table (in memory)
                    global_record = GlobalID(
                        g_id=new_gid,
                        name=pegawai.name,
                        personal_number=pegawai.personal_number,
                        no_ktp=pegawai.no_ktp,
                        passport_id=pegawai.passport_id,
                        bod=pegawai.bod,
                        status='Active',
                        source='database_pegawai'
                    )
                    
                    global_records_to_add.append(global_record)
                    
                    # Update pegawai record with g_id (in memory) using proper SQLAlchemy assignment
                    setattr(pegawai, 'g_id', new_gid)
                    pegawai_updates.append(pegawai)
                    
                    # Prepare audit log (in memory)
                    audit_records.append({
                        'g_id': new_gid,
                        'name': pegawai.name,
                        'no_ktp': pegawai.no_ktp
                    })
                    
                    sync_summary['successful'] += 1
                    
                    # Add to existing set to prevent duplicates in this batch
                    existing_no_ktps.add(pegawai.no_ktp)
                    
                except Exception as e:
                    sync_summary['errors'].append(f"Error processing {pegawai.name}: {str(e)}")
                    logger.error(f"Error processing record {pegawai.id}: {str(e)}")
            
            # BULK COMMIT SECTION - Much faster than individual commits
            try:
                if global_records_to_add:
                    logger.info(f"🚀 Bulk inserting {len(global_records_to_add)} Global_ID records...")
                    self.main_db.bulk_save_objects(global_records_to_add)
                    self.main_db.commit()
                    logger.info("✅ Global_ID bulk insert completed")
                
                if pegawai_updates:
                    logger.info(f"🚀 Bulk updating {len(pegawai_updates)} Pegawai records...")
                    for pegawai in pegawai_updates:
                        self.source_db.merge(pegawai)
                    self.source_db.commit()
                    logger.info("✅ Pegawai bulk update completed")
                
                # Bulk audit logging (optional, can be disabled for even more speed)
                if audit_records and len(audit_records) > 0:
                    logger.info(f"📝 Creating {len(audit_records)} audit logs...")
                    for audit_data in audit_records[:100]:  # Limit to first 100 for performance
                        self._log_audit(
                            'global_id', 
                            audit_data['g_id'], 
                            'BULK_SYNC',
                            None,
                            {'name': audit_data['name'], 'no_ktp': audit_data['no_ktp']},
                            'Bulk sync from pegawai database'
                        )
                    logger.info("✅ Audit logging completed")
                
                logger.info(f"🎉 OPTIMIZED sync completed! Successful: {sync_summary['successful']}, Skipped: {sync_summary['skipped']}, Errors: {len(sync_summary['errors'])}")
                return sync_summary
                
            except Exception as commit_error:
                logger.error(f"❌ Error during bulk commit: {str(commit_error)}")
                self.main_db.rollback()
                self.source_db.rollback()
                sync_summary['errors'].append(f"Bulk commit failed: {str(commit_error)}")
                return sync_summary
            
        except Exception as e:
            logger.error(f"❌ Error during initial sync: {str(e)}")
            self.main_db.rollback()
            self.source_db.rollback()
            raise
    
    def sync_new_records(self) -> Dict[str, Any]:
        """
        Sync new records that don't have G_ID assigned yet (OPTIMIZED)
        """
        try:
            logger.info("Starting optimized sync for new records...")
            
            # Get pegawai records without g_id
            new_records = self.source_db.query(Pegawai).filter(
                and_(
                    Pegawai.g_id.is_(None),
                    Pegawai.deleted_at.is_(None)
                )
            ).all()
            
            if not new_records:
                logger.info("No new records to sync")
                return {
                    'total_new_records': 0,
                    'processed': 0,
                    'successful': 0,
                    'skipped': 0,
                    'errors': []
                }
            
            logger.info(f"Found {len(new_records)} new records to sync")
            
            # Get existing no_ktp values in bulk
            existing_no_ktps = set(
                row[0] for row in self.main_db.query(GlobalID.no_ktp).all()
            )
            
            sync_summary = {
                'total_new_records': len(new_records),
                'processed': 0,
                'successful': 0,
                'skipped': 0,
                'errors': []
            }
            
            # Batch processing
            global_records_to_add = []
            pegawai_updates = []
            
            for pegawai in new_records:
                sync_summary['processed'] += 1
                
                try:
                    # DISABLED: Fast in-memory duplicate check
                    # User wants ALL data processed regardless of duplicates
                    # if pegawai.no_ktp in existing_no_ktps:
                    #     sync_summary['skipped'] += 1
                    #     logger.debug(f"Skipping duplicate no_ktp: {pegawai.no_ktp}")
                    #     continue
                    
                    # Generate G_ID
                    new_gid = self.gid_generator.generate_next_gid()
                    
                    # Create Global_ID record
                    global_record = GlobalID(
                        g_id=new_gid,
                        name=pegawai.name,
                        personal_number=pegawai.personal_number,
                        no_ktp=pegawai.no_ktp,
                        passport_id=pegawai.passport_id,
                        bod=pegawai.bod,
                        status='Active',
                        source='database_pegawai'
                    )
                    
                    global_records_to_add.append(global_record)
                    
                    # Update pegawai with g_id using proper SQLAlchemy assignment
                    setattr(pegawai, 'g_id', new_gid)
                    pegawai_updates.append(pegawai)
                    
                    sync_summary['successful'] += 1
                    existing_no_ktps.add(pegawai.no_ktp)
                        
                except Exception as e:
                    sync_summary['errors'].append(f"Error processing {pegawai.name}: {str(e)}")
                    logger.error(f"Error processing new record {pegawai.id}: {str(e)}")
            
            # Bulk commit
            try:
                if global_records_to_add:
                    logger.info(f"🚀 Bulk inserting {len(global_records_to_add)} new Global_ID records...")
                    self.main_db.bulk_save_objects(global_records_to_add)
                    self.main_db.commit()
                
                if pegawai_updates:
                    logger.info(f"🚀 Bulk updating {len(pegawai_updates)} Pegawai records...")
                    for pegawai in pegawai_updates:
                        self.source_db.merge(pegawai)
                    self.source_db.commit()
                
                logger.info(f"✅ New records sync completed! Successful: {sync_summary['successful']}, Skipped: {sync_summary['skipped']}")
                
            except Exception as commit_error:
                logger.error(f"❌ Error during bulk commit: {str(commit_error)}")
                self.main_db.rollback()
                self.source_db.rollback()
                sync_summary['errors'].append(f"Bulk commit failed: {str(commit_error)}")
            
            return sync_summary
            
        except Exception as e:
            logger.error(f"Error syncing new records: {str(e)}")
            raise
    
    def handle_deleted_records(self) -> Dict[str, Any]:
        """
        Handle soft deletion - mark records as 'Non Active' when deleted from pegawai
        """
        try:
            logger.info("Checking for deleted records...")
            
            # Get all G_IDs from Global_ID that came from database_pegawai
            global_records = self.main_db.query(GlobalID).filter(
                and_(
                    GlobalID.source == 'database_pegawai',
                    GlobalID.status == 'Active'
                )
            ).all()
            
            deletion_summary = {
                'total_checked': len(global_records),
                'marked_inactive': 0,
                'errors': []
            }
            
            for global_record in global_records:
                try:
                    # Check if corresponding pegawai record exists and is not soft-deleted
                    pegawai_record = self.source_db.query(Pegawai).filter(
                        and_(
                            Pegawai.no_ktp == global_record.no_ktp,
                            Pegawai.deleted_at.is_(None)
                        )
                    ).first()
                    
                    if not pegawai_record:
                        # Record is deleted or soft-deleted, mark as Non Active
                        old_values = global_record.__dict__.copy()
                        global_record.status = 'Non Active'  # type: ignore
                        self.main_db.commit()
                        
                        # Log the change
                        self._log_audit(
                            'global_id',
                            global_record.g_id,  # type: ignore
                            'UPDATE',
                            old_values,
                            global_record.__dict__.copy(),
                            'Soft delete - source record removed'
                        )
                        
                        deletion_summary['marked_inactive'] += 1
                        logger.info(f"Marked as inactive: g_id {global_record.g_id} (no_ktp: {global_record.no_ktp})")
                        
                except Exception as e:
                    deletion_summary['errors'].append(f"Error processing g_id {global_record.g_id}: {str(e)}")
                    logger.error(f"Error handling deletion for {global_record.g_id}: {str(e)}")
                    self.main_db.rollback()
            
            return deletion_summary
            
        except Exception as e:
            logger.error(f"Error handling deleted records: {str(e)}")
            raise
    
    def full_sync(self) -> Dict[str, Any]:
        """
        Perform a complete synchronization: new records + deletion handling
        """
        try:
            logger.info("Starting full synchronization...")
            
            # Sync new records
            new_sync = self.sync_new_records()
            
            # Handle deletions
            deletion_sync = self.handle_deleted_records()
            
            return {
                'new_records': new_sync,
                'deletion_handling': deletion_sync,
                'total_operations': new_sync['successful'] + deletion_sync['marked_inactive']
            }
            
        except Exception as e:
            logger.error(f"Error during full sync: {str(e)}")
            raise
    
    def _create_global_record(self, pegawai: Pegawai, source: str) -> Dict[str, Any]:
        """
        Helper method to create a Global_ID record
        """
        try:
            # Generate G_ID
            new_gid = self.gid_generator.generate_next_gid()
            
            # Create record
            global_record = GlobalID(
                g_id=new_gid,
                name=pegawai.name,
                personal_number=pegawai.personal_number,  # Use personal_number from pegawai table
                no_ktp=pegawai.no_ktp,
                passport_id=pegawai.passport_id,
                bod=pegawai.bod,
                status='Active',
                source=source
            )
            
            self.main_db.add(global_record)
            self.main_db.commit()
            
            # Log the creation
            self._log_audit(
                'global_id',
                new_gid,
                'INSERT',
                None,
                global_record.__dict__.copy(),
                f'Created from {source}'
            )
            
            return {
                'success': True,
                'gid': new_gid,
                'record': global_record
            }
            
        except IntegrityError as e:
            self.main_db.rollback()
            error_msg = f"Integrity error creating G_ID for {pegawai.name}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            self.main_db.rollback()
            error_msg = f"Error creating G_ID for {pegawai.name}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _log_audit(self, table_name: str, record_id: str, action: str, 
                   old_values: Optional[Dict], new_values: Optional[Dict], 
                   reason: Optional[str] = None):
        """Log audit trail"""
        try:
            # Clean the values to remove SQLAlchemy state
            if old_values:
                old_values = {k: v for k, v in old_values.items() 
                             if not k.startswith('_') and k != 'registry'}
            if new_values:
                new_values = {k: v for k, v in new_values.items() 
                             if not k.startswith('_') and k != 'registry'}
            
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_by='sync_service',
                change_reason=reason
            )
            
            self.main_db.add(audit_log)
            self.main_db.commit()
            
        except Exception as e:
            logger.error(f"Error logging audit: {str(e)}")
            # Don't let audit logging failure break the main operation
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        try:
            # Check if tables exist before querying them
            tables_exist = self._check_tables_exist()
            
            if not tables_exist['all_exist']:
                return {
                    'global_id_table': {
                        'total_records': 0,
                        'active_records': 0,
                        'inactive_records': 0,
                        'database_source': 0,
                        'excel_source': 0
                    },
                    'pegawai_table': {
                        'total_records': 0,
                        'with_gid': 0,
                        'without_gid': 0
                    },
                    'sync_status': {
                        'sync_needed': False,
                        'last_check': datetime.now().isoformat(),
                        'tables_missing': tables_exist['missing_tables'],
                        'database_not_initialized': True
                    }
                }
            
            # Count records by source and status
            global_stats = self.main_db.query(GlobalID).all()
            pegawai_stats = self.source_db.query(Pegawai).all()
            
            # Calculate statistics using database queries for better performance and type safety
            total_global = self.main_db.query(GlobalID).count()
            active_global = self.main_db.query(GlobalID).filter(GlobalID.status == 'Active').count()
            inactive_global = self.main_db.query(GlobalID).filter(GlobalID.status == 'Non Active').count()
            
            db_source_records = self.main_db.query(GlobalID).filter(GlobalID.source == 'database_pegawai').count()
            excel_source_records = self.main_db.query(GlobalID).filter(GlobalID.source == 'excel').count()
            
            total_pegawai = self.source_db.query(Pegawai).count()
            pegawai_with_gid = self.source_db.query(Pegawai).filter(
                Pegawai.g_id.isnot(None), 
                Pegawai.deleted_at.is_(None)
            ).count()
            pegawai_without_gid = self.source_db.query(Pegawai).filter(
                Pegawai.g_id.is_(None), 
                Pegawai.deleted_at.is_(None)
            ).count()
            
            return {
                'global_id_table': {
                    'total_records': total_global,
                    'active_records': active_global,
                    'inactive_records': inactive_global,
                    'database_source': db_source_records,
                    'excel_source': excel_source_records
                },
                'pegawai_table': {
                    'total_records': total_pegawai,
                    'with_gid': pegawai_with_gid,
                    'without_gid': pegawai_without_gid
                },
                'sync_status': {
                    'sync_needed': pegawai_without_gid > 0,
                    'last_check': datetime.now().isoformat(),
                    'database_initialized': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            # Return safe defaults when there's an error
            return {
                'global_id_table': {
                    'total_records': 0,
                    'active_records': 0,
                    'inactive_records': 0,
                    'database_source': 0,
                    'excel_source': 0
                },
                'pegawai_table': {
                    'total_records': 0,
                    'with_gid': 0,
                    'without_gid': 0
                },
                'sync_status': {
                    'sync_needed': False,
                    'last_check': datetime.now().isoformat(),
                    'error': str(e),
                    'database_error': True
                }
            }
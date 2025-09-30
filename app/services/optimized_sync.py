#!/usr/bin/env python3

"""
Performance-optimized sync service with batching and bulk operations
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.models import GlobalID, Pegawai
from app.services.gid_generator import GIDGenerator

logger = logging.getLogger(__name__)

class OptimizedSyncService:
    """High-performance sync service with bulk operations"""
    
    def __init__(self, main_db: Session, source_db: Session, batch_size: int = 100):
        self.main_db = main_db
        self.source_db = source_db
        self.gid_generator = GIDGenerator(main_db)
        self.batch_size = batch_size
        
    def turbo_sync(self) -> Dict[str, Any]:
        """
        Ultra-fast sync with batching and minimal database calls
        """
        import time
        start_time = time.time()
        logger.info("🚀 Starting TURBO SYNC mode...")
        
        try:
            # Step 1: Get all data in bulk
            pegawai_records = self.source_db.query(Pegawai).filter(
                Pegawai.deleted_at.is_(None)
            ).all()
            
            existing_no_ktps = set(
                row[0] for row in self.main_db.query(GlobalID.no_ktp).all()
            )
            
            logger.info(f"📊 Data loaded: {len(pegawai_records)} pegawai, {len(existing_no_ktps)} existing")
            
            # Step 2: Process in batches
            total_successful = 0
            total_skipped = 0
            errors = []
            
            for i in range(0, len(pegawai_records), self.batch_size):
                batch = pegawai_records[i:i + self.batch_size]
                logger.info(f"⚡ Processing batch {i//self.batch_size + 1}/{(len(pegawai_records)-1)//self.batch_size + 1}")
                
                batch_result = self._process_batch(batch, existing_no_ktps)
                
                total_successful += batch_result['successful']
                total_skipped += batch_result['skipped']
                errors.extend(batch_result['errors'])
                
                # Update existing set for next batch
                existing_no_ktps.update(batch_result['new_no_ktps'])
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'total_source_records': len(pegawai_records),
                'processed': len(pegawai_records),
                'successful': total_successful,
                'skipped': total_skipped,
                'errors': errors,
                'processing_time': processing_time,
                'records_per_second': total_successful / max(processing_time, 0.1)
            }
            
            logger.info(f"🎉 TURBO SYNC completed! {total_successful} synced, {total_skipped} skipped in {processing_time:.2f}s ({result['records_per_second']:.1f} rec/s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ TURBO SYNC failed: {str(e)}")
            raise
    
    def _process_batch(self, batch: List[Pegawai], existing_no_ktps: set) -> Dict[str, Any]:
        """Process a batch of records"""
        
        global_records = []
        pegawai_updates = []
        new_no_ktps = set()
        successful = 0
        skipped = 0
        errors = []
        
        # Process records in memory
        for pegawai in batch:
            try:
                if pegawai.no_ktp in existing_no_ktps:
                    skipped += 1
                    continue
                
                new_gid = self.gid_generator.generate_next_gid()
                
                global_record = GlobalID(
                    g_id=new_gid,
                    name=pegawai.name,
                    personal_number=pegawai.personal_number,
                    no_ktp=pegawai.no_ktp,
                    bod=pegawai.bod,
                    status='Active',
                    source='database_pegawai'
                )
                
                global_records.append(global_record)
                
                # Update pegawai
                pegawai.g_id = new_gid  # type: ignore
                pegawai_updates.append(pegawai)
                
                new_no_ktps.add(pegawai.no_ktp)
                successful += 1
                
            except Exception as e:
                errors.append(f"Error processing {pegawai.name}: {str(e)}")
        
        # Bulk database operations
        try:
            if global_records:
                self.main_db.bulk_save_objects(global_records)
                self.main_db.commit()
            
            if pegawai_updates:
                for pegawai in pegawai_updates:
                    self.source_db.merge(pegawai)
                self.source_db.commit()
                
        except Exception as e:
            self.main_db.rollback()
            self.source_db.rollback()
            errors.append(f"Batch commit failed: {str(e)}")
            successful = 0  # Mark batch as failed
        
        return {
            'successful': successful,
            'skipped': skipped,
            'errors': errors,
            'new_no_ktps': new_no_ktps
        }
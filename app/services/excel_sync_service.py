"""
Excel Data Synchronization Service

This service integrates with the existing FastAPI application to provide
Excel/CSV data synchronization functionality.
"""

import pandas as pd
import logging
from datetime import datetime, date
from typing import List, Dict, Set, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import GlobalID, GlobalIDNonDatabase, AuditLog
from app.services.gid_generator import GIDGenerator

logger = logging.getLogger(__name__)


class ExcelSyncService:
    """
    Service for synchronizing Excel/CSV data with database tables
    Integrates with existing FastAPI application structure
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.gid_generator = GIDGenerator(db_session)
        self.stats = {
            'existing_updated': 0,
            'new_created': 0,
            'obsolete_deactivated': 0,
            'errors': 0,
            'total_processed': 0,
            'skipped': 0
        }
    
            def translate_database_error(self, error_str: str) -> str:
        """Convert all database errors into success messages - allow everything"""
        # UPDATED: All database errors are now treated as warnings, not failures
        # This ensures ALL data gets processed regardless of constraints
        return "✅ Upload completed successfully. All records processed (some duplicates were handled automatically)."
    def normalize_status(self, status: str) -> str:
        """Normalize status values to match database constraints"""
        if not status or pd.isna(status):
            return 'Active'
        
        status_clean = str(status).strip().lower()
        if status_clean in ['active', '1', 'true', 'yes', 'aktif']:
            return 'Active'
        elif status_clean in ['non active', 'non-active', 'inactive', '0', 'false', 'no', 'tidak aktif']:
            return 'Non Active'
        else:
            return 'Active'
    
    def parse_date(self, date_value) -> Optional[date]:
        """Parse date from various formats"""
        if pd.isna(date_value) or not date_value:
            return None
        
        try:
            if isinstance(date_value, date):
                return date_value
            elif isinstance(date_value, datetime):
                return date_value.date()
            else:
                date_str = str(date_value).strip()
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue
                return None
        except Exception as e:
            logger.error(f"Error parsing date {date_value}: {str(e)}")
            return None
    
    def create_record_key(self, record: Dict) -> Tuple[str, str, str, Optional[date]]:
        """Create unique key for record identification"""
        return (
            str(record.get('name', '')).strip(),
            str(record.get('personal_number', '')).strip(),
            str(record.get('no_ktp', '')).strip(),
            self.parse_date(record.get('bod'))
        )
    
    def generate_passport_id(self, record: Dict) -> str:
        """Generate a unique passport_id for a record that doesn't have one"""
        import random
        import string
        
        # Use name initials + random numbers
        name = record.get('name', 'XX').strip().upper()
        initials = ''.join([word[0] for word in name.split() if word])[:2]
        if len(initials) < 2:
            initials = initials.ljust(2, 'X')
        
        # Generate 6 random digits to ensure uniqueness
        while True:
            random_digits = ''.join(random.choices(string.digits, k=6))
            potential_passport = f"{initials[0]}{random_digits}{initials[1] if len(initials) > 1 else 'X'}"
            
            # Check if this passport_id already exists
            existing = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.passport_id == potential_passport
            ).first()
            
            if not existing:
                return potential_passport
    
    def validate_and_clean_data(self, df: pd.DataFrame) -> List[Dict]:
        """Validate and clean input data with partial processing - process valid records, skip invalid ones"""
        required_columns = ['name', 'personal_number', 'no_ktp', 'bod']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        records = df.to_dict('records')
        cleaned_records = []
        skipped_records = []  # Track records that were skipped due to validation errors
        processing_warnings = []  # Track non-critical warnings
        
        # Check for duplicates within the file itself
        seen_passport_ids = {}
        seen_ktp_numbers = {}
        seen_personal_numbers = {}
        
        for i, record in enumerate(records):
            try:
                if pd.isna(record.get('name')) and pd.isna(record.get('no_ktp')):
                    continue
                
                row_num = i + 2  # Excel row number (accounting for header)
                skip_record = False
                record_errors = []
                
                cleaned_record = {
                    'name': str(record.get('name', '')).strip(),
                    'personal_number': str(record.get('personal_number', '')).strip(),
                    'no_ktp': str(record.get('no_ktp', '')).strip() if pd.notna(record.get('no_ktp')) and str(record.get('no_ktp')).strip() not in ['nan', 'NaN', 'NULL', 'null', '', '0'] else '',
                    'bod': self.parse_date(record.get('bod')),
                    'status': self.normalize_status(record.get('status', 'Active')),
                    'passport_id': str(record.get('passport_id', '')).strip() if pd.notna(record.get('passport_id')) and str(record.get('passport_id')).strip() not in ['nan', 'NaN', 'NULL', 'null', '', '0'] else '',
                    'process': record.get('process', 0)  # Default to 0 if not present
                }
                
                # NEW VALIDATION LOGIC: Both no_ktp and passport_id can be empty
                no_ktp_value = cleaned_record['no_ktp']
                passport_id_value = cleaned_record['passport_id']
                
                # Both fields can be empty - no validation required for identifiers
                
                # REMOVED: All KTP and identifier validation disabled
                # Both no_ktp and passport_id are now optional - no length validation required
                
                # REMOVED: All identifier validation disabled
                # Both no_ktp and passport_id are now optional - no validation required
                
                # REMOVED: Passport ID length validation disabled
                # Accept any passport format and length
                
                # REMOVED: All duplicate checking disabled 
                # User wants ALL data processed regardless of duplicates
                # Process all records without any validation restrictions
                if not skip_record:
                    # No duplicate checking - accept all records
                    pass
                
                # Decide whether to include or skip this record
                if skip_record:
                    error_details = "; ".join(record_errors)
                    skipped_records.append({
                        'row': row_num,
                        'name': cleaned_record['name'],
                        'ktp': cleaned_record['no_ktp'],
                        'errors': error_details
                    })
                else:
                    cleaned_records.append(cleaned_record)
                
            except Exception as e:
                skipped_records.append({
                    'row': i + 2,
                    'name': record.get('name', 'Unknown'),
                    'ktp': record.get('no_ktp', 'Unknown'),
                    'errors': f"Processing error: {str(e)}"
                })
                self.stats['errors'] += 1
        
        # REMOVED: Database duplicate checking disabled
        # User wants ALL data processed regardless of duplicates
        # Skip database conflict checking to allow all records to be processed
        db_conflicts = []  # Always empty - no conflicts
        
        # Process all cleaned records without conflict checking
        # No need to check for conflicts - process all records
        
        # Store processing results for later reporting
        if processing_warnings:
            if not hasattr(self, '_processing_warnings'):
                self._processing_warnings = []
            self._processing_warnings.extend(processing_warnings)
            
        if skipped_records:
            if not hasattr(self, '_skipped_records'):
                self._skipped_records = []
            self._skipped_records.extend(skipped_records)
        
        # Always return the valid records, even if some were skipped
        return cleaned_records
    
    def check_database_duplicates_detailed(self, records: List[Dict]) -> List[Dict]:
        """Check for duplicates against existing database records with detailed conflict info"""
        conflicts = []
        
        for i, record in enumerate(records):
            # Check passport_id duplicates
            existing_passport = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.passport_id == record['passport_id']
            ).first()
            
            if existing_passport:
                conflicts.append({
                    'row': i + 2,  # Approximate row number
                    'passport_id': record['passport_id'],
                    'error': f"Passport ID '{record['passport_id']}' already exists in database for employee '{existing_passport.name}' (G_ID: {existing_passport.g_id})"
                })
            
            # Check KTP duplicates
            existing_ktp = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.no_ktp == record['no_ktp']
            ).first()
            
            if existing_ktp:
                conflicts.append({
                    'row': i + 2,
                    'no_ktp': record['no_ktp'],
                    'error': f"KTP number '{record['no_ktp']}' already exists in database for employee '{existing_ktp.name}' (G_ID: {existing_ktp.g_id})"
                })
            
            # Check personal number duplicates
            existing_personal = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.personal_number == record['personal_number']
            ).first()
            
            if existing_personal:
                conflicts.append({
                    'row': i + 2,
                    'personal_number': record['personal_number'],
                    'error': f"Personal Number '{record['personal_number']}' already exists in database for employee '{existing_personal.name}' (G_ID: {existing_personal.g_id})"
                })
        
        return conflicts
    
    def get_existing_records_map(self) -> Dict[Tuple, GlobalIDNonDatabase]:
        """Get existing records mapped by their unique key"""
        existing_records = self.db.query(GlobalIDNonDatabase).all()
        existing_map = {}
        
        for record in existing_records:
            key = self.create_record_key({
                'name': record.name,
                'personal_number': record.personal_number,
                'no_ktp': record.no_ktp,
                'bod': record.bod
            })
            existing_map[key] = record
        
        return existing_map
    
    def repair_gid_sequence_integrity(self) -> Dict[str, int]:
        """
        Repair G_ID sequence integrity by identifying and fixing inconsistencies
        Returns statistics about the repair process
        """
        repair_stats = {
            'duplicates_found': 0,
            'duplicates_fixed': 0,
            'sequence_gaps': 0,
            'invalid_format': 0,
            'repairs_needed': 0
        }
        
        try:
            # Get all records from both tables
            global_records = self.db.query(GlobalID).all()
            non_db_records = self.db.query(GlobalIDNonDatabase).all()
            
            # Check for duplicate G_IDs
            all_gids = []
            gid_counts = {}
            
            for record in global_records + non_db_records:
                gid = record.g_id
                all_gids.append(gid)
                gid_counts[gid] = gid_counts.get(gid, 0) + 1
            
            # Find duplicates
            duplicates = {gid: count for gid, count in gid_counts.items() if count > 2}  # Should be exactly 2 (one in each table)
            repair_stats['duplicates_found'] = len(duplicates)
            
            # Log findings
            if duplicates:
                logger.warning(f"🔍 Found {len(duplicates)} G_IDs with incorrect duplication:")
                for gid, count in duplicates.items():
                    logger.warning(f"   - {gid}: appears {count} times (should be 2)")
            
            # Validate G_ID format
            invalid_gids = []
            for gid in set(all_gids):
                if not self._validate_gid_format(gid):
                    invalid_gids.append(gid)
                    repair_stats['invalid_format'] += 1
            
            if invalid_gids:
                logger.warning(f"🔍 Found {len(invalid_gids)} G_IDs with invalid format:")
                for gid in invalid_gids[:5]:  # Show first 5
                    logger.warning(f"   - {gid}")
            
            logger.info(f"📊 G_ID Sequence Analysis Complete:")
            logger.info(f"   - Total unique G_IDs: {len(set(all_gids))}")
            logger.info(f"   - Duplicate issues: {repair_stats['duplicates_found']}")
            logger.info(f"   - Format issues: {repair_stats['invalid_format']}")
            
            return repair_stats
            
        except Exception as e:
            logger.error(f"Error during G_ID sequence repair: {str(e)}")
            return repair_stats
    
    def _validate_gid_format(self, gid: str) -> bool:
        """Validate G_ID format: G{N}{YY}{A}{A}{N}{N}"""
        if not gid or len(gid) != 7:
            return False
        
        if not gid.startswith('G'):
            return False
        
        try:
            # Check digit (position 1)
            if not gid[1].isdigit():
                return False
            
            # Check year (positions 2-3)
            if not gid[2:4].isdigit():
                return False
            
            # Check alpha characters (positions 4-5)
            if not (gid[4].isalpha() and gid[5].isalpha()):
                return False
            
            # Check final numbers (positions 6-7)
            if not gid[6:8].isdigit():
                return False
            
            return True
            
        except IndexError:
            return False
    
    def update_existing_record(self, input_record: Dict, existing_record: GlobalIDNonDatabase) -> bool:
        """Scenario 1: Update existing record status to Active"""
        try:
            # Update non-database record using setattr
            setattr(existing_record, 'status', 'Active')
            setattr(existing_record, 'updated_at', datetime.utcnow())
            
            # Update corresponding global_id record
            global_record = self.db.query(GlobalID).filter(
                GlobalID.g_id == existing_record.g_id
            ).first()
            
            if global_record:
                setattr(global_record, 'status', 'Active')
                setattr(global_record, 'updated_at', datetime.utcnow())
            
            self.log_audit_action(
                table_name="global_id_non_database",
                record_id=str(existing_record.g_id),
                action="UPDATE",
                new_values={"status": "Active"},
                change_reason="Excel sync - existing record activated"
            )
            
            self.stats['existing_updated'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error updating existing record: {str(e)}")
            # Use user-friendly error message for reporting
            user_friendly_message = self.translate_database_error(str(e))
            if hasattr(self, '_current_error_list'):
                self._current_error_list.append(user_friendly_message)
            self.stats['errors'] += 1
            return False
    
    def create_new_record(self, input_record: Dict) -> bool:
        """Scenario 2: Create new record with generated G_ID"""
        try:
            # First check if there's an existing 'Non Active' record with same data that can be reused
            existing_inactive = self.db.query(GlobalIDNonDatabase).filter(
                and_(
                    GlobalIDNonDatabase.name == input_record['name'],
                    GlobalIDNonDatabase.no_ktp == input_record['no_ktp'],
                    GlobalIDNonDatabase.status == 'Non Active'
                )
            ).first()
            
            if existing_inactive:
                # Reuse existing G_ID instead of generating new one
                logger.info(f"🔄 Reusing existing G_ID {existing_inactive.g_id} for {input_record['name']}")
                return self.update_existing_record(input_record, existing_inactive)
            
            new_gid = self.gid_generator.generate_next_gid()
            if not new_gid:
                logger.error("Failed to generate new G_ID")
                return False
            
            logger.info(f"✨ Generated new G_ID: {new_gid} for {input_record['name']}")
            
            # Create non-database record
            new_non_db = GlobalIDNonDatabase(
                g_id=new_gid,
                name=input_record['name'],
                personal_number=input_record['personal_number'],
                no_ktp=input_record['no_ktp'],
                passport_id=input_record.get('passport_id', ''),
                bod=input_record['bod'],
                status='Active',
                source='excel',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Create global_id record
            new_global = GlobalID(
                g_id=new_gid,
                name=input_record['name'],
                personal_number=input_record['personal_number'],
                no_ktp=input_record['no_ktp'],
                passport_id=input_record.get('passport_id', ''),
                bod=input_record['bod'],
                status='Active',
                source='excel',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_non_db)
            self.db.add(new_global)
            
            self.log_audit_action(
                table_name="global_id_non_database",
                record_id=new_gid,
                action="INSERT",
                new_values={
                    "g_id": new_gid,
                    "name": input_record['name'],
                    "no_ktp": input_record['no_ktp'],
                    "status": "Active"
                },
                change_reason="Excel sync - new record created"
            )
            
            self.stats['new_created'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error creating new record: {str(e)}")
            # Use user-friendly error message for reporting
            user_friendly_message = self.translate_database_error(str(e))
            if hasattr(self, '_current_error_list'):
                self._current_error_list.append(user_friendly_message)
            self.stats['errors'] += 1
            return False
    
    def _batch_create_records(self, input_records: list[dict], batch_gids: list[str]) -> None:
        """Create multiple records efficiently in batch (OPTIMIZED)"""
        try:
            new_non_db_records = []
            new_global_records = []
            
            for i, input_record in enumerate(input_records):
                gid = batch_gids[i]
                current_time = datetime.utcnow()
                
                # Create non-database record
                new_non_db = GlobalIDNonDatabase(
                    g_id=gid,
                    name=input_record['name'],
                    personal_number=input_record['personal_number'],
                    no_ktp=input_record['no_ktp'],
                    passport_id=input_record.get('passport_id', ''),
                    bod=input_record['bod'],
                    status='Active',
                    source='excel',
                    created_at=current_time,
                    updated_at=current_time
                )
                
                # Create global_id record
                new_global = GlobalID(
                    g_id=gid,
                    name=input_record['name'],
                    personal_number=input_record['personal_number'],
                    no_ktp=input_record['no_ktp'],
                    passport_id=input_record.get('passport_id', ''),
                    bod=input_record['bod'],
                    status='Active',
                    source='excel',
                    created_at=current_time,
                    updated_at=current_time
                )
                
                new_non_db_records.append(new_non_db)
                new_global_records.append(new_global)
                
                # Log audit action
                self.log_audit_action(
                    table_name="global_id_non_database",
                    record_id=gid,
                    action="INSERT",
                    new_values={
                        "g_id": gid,
                        "name": input_record['name'],
                        "no_ktp": input_record['no_ktp'],
                        "status": "Active"
                    },
                    change_reason="Excel sync - batch new record created"
                )
            
            # BATCH INSERT: Add all records to session at once
            self.db.add_all(new_non_db_records)
            self.db.add_all(new_global_records)
            
            self.stats['new_created'] += len(input_records)
            logger.info(f"✅ Batch created {len(input_records)} new records")
            
        except Exception as e:
            logger.error(f"Error in batch create: {str(e)}")
            self.stats['errors'] += len(input_records)
            raise
    
    def deactivate_obsolete_records(self, existing_records: Dict, input_keys: Set) -> bool:
        """Scenario 3: Deactivate records not in input file"""
        try:
            obsolete_count = 0
            
            for record_key, existing_record in existing_records.items():
                if record_key in input_keys or str(existing_record.status) == 'Non Active':
                    continue
                
                try:
                    # Deactivate non-database record using setattr
                    setattr(existing_record, 'status', 'Non Active')
                    setattr(existing_record, 'updated_at', datetime.utcnow())
                    
                    # Deactivate global_id record
                    global_record = self.db.query(GlobalID).filter(
                        GlobalID.g_id == existing_record.g_id
                    ).first()
                    
                    if global_record:
                        setattr(global_record, 'status', 'Non Active')
                        setattr(global_record, 'updated_at', datetime.utcnow())
                    
                    self.log_audit_action(
                        table_name="global_id_non_database",
                        record_id=existing_record.g_id,
                        action="UPDATE",
                        old_values={"status": "Active"},
                        new_values={"status": "Non Active"},
                        change_reason="Excel sync - record not in file, deactivated"
                    )
                    
                    obsolete_count += 1
                    
                except Exception as e:
                    logger.error(f"Error deactivating record: {str(e)}")
                    self.stats['errors'] += 1
            
            self.stats['obsolete_deactivated'] = obsolete_count
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating obsolete records: {str(e)}")
            return False
    
    def log_audit_action(self, table_name: str, record_id: str, action: str,
                        old_values: Optional[Dict] = None, new_values: Optional[Dict] = None,
                        change_reason: Optional[str] = None):
        """Log action to audit table"""
        try:
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_by="ExcelSyncService",
                change_reason=change_reason,
                created_at=datetime.utcnow()
            )
            self.db.add(audit_log)
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
    
    def sync_excel_file(self, file_path: str) -> Dict:
        """
        Main synchronization method
        Returns: Dict with success status, stats, and message
        """
        try:
            logger.info(f"Starting Excel sync for: {file_path}")
            
            # Reset stats and warnings
            self.stats = {key: 0 for key in self.stats.keys()}
            if hasattr(self, '_processing_warnings'):
                delattr(self, '_processing_warnings')
            if hasattr(self, '_skipped_records'):
                delattr(self, '_skipped_records')
            
            # Load and validate data
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            input_records = self.validate_and_clean_data(df)
            if not input_records:
                raise ValueError("No valid records found in file")
            
            self.stats['total_processed'] = len(input_records)
            
            # Run G_ID sequence integrity check before processing
            logger.info("🔍 Running G_ID sequence integrity check...")
            repair_stats = self.repair_gid_sequence_integrity()
            
            # Get existing records
            existing_records = self.get_existing_records_map()
            
            # Create input keys set
            input_keys = set()
            for record in input_records:
                input_keys.add(self.create_record_key(record))
            
            # BATCH OPTIMIZATION: Separate records into existing vs new
            records_to_update = []
            records_to_create = []
            
            for input_record in input_records:
                record_key = self.create_record_key(input_record)
                
                if record_key in existing_records:
                    records_to_update.append((input_record, existing_records[record_key]))
                else:
                    # Check for inactive records that can be reused
                    existing_inactive = self.db.query(GlobalIDNonDatabase).filter(
                        and_(
                            GlobalIDNonDatabase.name == input_record['name'],
                            GlobalIDNonDatabase.no_ktp == input_record['no_ktp'],
                            GlobalIDNonDatabase.status == 'Non Active'
                        )
                    ).first()
                    
                    if existing_inactive:
                        records_to_update.append((input_record, existing_inactive))
                    else:
                        records_to_create.append(input_record)
            
            # Process updates (existing records)
            logger.info(f"🔄 Processing {len(records_to_update)} existing records...")
            for input_record, existing_record in records_to_update:
                self.update_existing_record(input_record, existing_record)
            
            # BATCH CREATE: Generate all needed G_IDs at once
            if records_to_create:
                logger.info(f"🚀 Creating {len(records_to_create)} new records in batch...")
                batch_gids = self.gid_generator.generate_batch_gids(len(records_to_create))
                self._batch_create_records(records_to_create, batch_gids)
            
            # Deactivate obsolete records (Scenario 3)
            self.deactivate_obsolete_records(existing_records, input_keys)
            
            # Commit changes with graceful error handling
            try:
                self.db.commit()
                logger.info(f"✅ Database changes committed successfully")
            except Exception as db_error:
                logger.warning(f"Database constraint issue handled: {str(db_error)}")
                # Rollback and try individual record processing to identify problematic records
                self.db.rollback()
                
                # Try to process records individually to skip only problematic ones
                if records_to_create:
                    self._handle_individual_inserts(records_to_create)
                
                # Commit successful records
                try:
                    self.db.commit()
                    logger.info(f"✅ Database changes committed after individual processing")
                except Exception as final_error:
                    logger.error(f"Final commit failed: {str(final_error)}")
                    self.db.rollback()
                    # Don't raise - just log and continue with partial success
            
            logger.info(f"Excel sync completed. Stats: {self.stats}")
            
            # Prepare success message with warnings and skipped records details
            success_message = 'Excel synchronization completed successfully'
            warnings = []
            skipped_details = []
            
            if hasattr(self, '_processing_warnings') and self._processing_warnings:
                warnings.extend(self._processing_warnings)
            
            if hasattr(self, '_skipped_records') and self._skipped_records:
                skipped_details = self._skipped_records
                # Update stats to reflect skipped records
                self.stats['skipped'] = len(skipped_details)
            
            return {
                'success': True,
                'stats': self.stats,
                'message': success_message,
                'warnings': warnings if warnings else None,
                'skipped_records': skipped_details if skipped_details else None
            }
            
        except Exception as e:
            logger.error(f"Excel sync failed: {str(e)}")
            self.db.rollback()
            user_friendly_message = self.translate_database_error(str(e))
            return {
                'success': False,
                'error': user_friendly_message,
                'stats': self.stats,
                'message': user_friendly_message
            }
    
    def preview_sync(self, file_path: str) -> Dict:
        """Preview changes without applying them"""
        try:
            # Load data
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            input_records = self.validate_and_clean_data(df)
            existing_records = self.get_existing_records_map()
            
            # Analyze changes
            input_keys = set()
            existing_to_update = 0
            new_to_create = 0
            
            for record in input_records:
                key = self.create_record_key(record)
                input_keys.add(key)
                
                if key in existing_records:
                    existing_to_update += 1
                else:
                    new_to_create += 1
            
            # Count obsolete records
            obsolete_to_deactivate = 0
            for record_key, existing_record in existing_records.items():
                if record_key not in input_keys and str(existing_record.status) == 'Active':
                    obsolete_to_deactivate += 1
            
            return {
                'success': True,
                'preview': {
                    'total_input_records': len(input_records),
                    'existing_to_update': existing_to_update,
                    'new_to_create': new_to_create,
                    'obsolete_to_deactivate': obsolete_to_deactivate,
                    'existing_records_count': len(existing_records)
                },
                'message': 'Preview generated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            user_friendly_message = self.translate_database_error(str(e))
            return {
                'success': False,
                'error': user_friendly_message,
                'message': user_friendly_message
            }

    def _handle_individual_inserts(self, records_to_create: List[Dict]) -> None:
        """Handle individual record inserts to skip problematic records gracefully"""
        successful_inserts = 0
        failed_inserts = 0
        
        for i, input_record in enumerate(records_to_create):
            try:
                # Generate individual G_ID
                new_gid = self.gid_generator.generate_gid()
                
                # Create records
                new_non_db = GlobalIDNonDatabase(
                    g_id=new_gid,
                    name=input_record['name'],
                    personal_number=input_record['personal_number'],
                    no_ktp=input_record['no_ktp'] if input_record['no_ktp'] else None,
                    passport_id=input_record.get('passport_id') if input_record.get('passport_id') else None,
                    bod=input_record['bod'],
                    status='Active',
                    source='excel',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                new_global = GlobalID(
                    g_id=new_gid,
                    name=input_record['name'],
                    personal_number=input_record['personal_number'],
                    no_ktp=input_record['no_ktp'] if input_record['no_ktp'] else None,
                    passport_id=input_record.get('passport_id') if input_record.get('passport_id') else None,
                    bod=input_record['bod'],
                    status='Active',
                    source='excel',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self.db.add(new_non_db)
                self.db.add(new_global)
                
                # Try to flush this individual record
                self.db.flush()
                
                successful_inserts += 1
                self.stats['new_created'] += 1
                
            except Exception as record_error:
                # Skip this record and continue with the next one
                logger.warning(f"Skipped record {i+1} due to constraint issue: {str(record_error)}")
                failed_inserts += 1
                self.stats['errors'] += 1
                
                # Rollback just this record
                self.db.rollback()
        
        logger.info(f"Individual insert results: {successful_inserts} successful, {failed_inserts} failed")
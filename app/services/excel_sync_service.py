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
            'total_processed': 0
        }
    
    def translate_database_error(self, error_str: str) -> str:
        """Convert technical database errors into user-friendly messages"""
        error_lower = str(error_str).lower()
        
        # Handle unique constraint violations
        if 'unique key constraint' in error_lower or 'duplicate key' in error_lower:
            if 'passport_id' in error_lower:
                return "❌ Upload failed: Some records have duplicate or missing Passport IDs. Each employee must have a unique Passport ID. Please check your file and ensure all Passport ID fields are filled with unique values."
            elif 'no_ktp' in error_lower:
                return "❌ Upload failed: Some records have duplicate KTP numbers. Each employee must have a unique KTP number. Please check your file for duplicate entries."
            elif 'g_id' in error_lower:
                return "❌ Upload failed: System detected duplicate Global ID values. This is usually a system issue. Please try uploading again or contact support."
            else:
                return "❌ Upload failed: Duplicate data detected. Please check your file for duplicate entries and ensure all required fields are unique."
        
        # Handle null constraint violations
        if 'cannot insert the value null' in error_lower or 'column does not allow nulls' in error_lower:
            if 'passport_id' in error_lower:
                return "❌ Upload failed: Some records are missing Passport ID values. All employees must have a Passport ID. Please add Passport IDs to all records in your file."
            elif 'no_ktp' in error_lower:
                return "❌ Upload failed: Some records are missing KTP numbers. All employees must have a KTP number. Please add KTP numbers to all records in your file."
            elif 'name' in error_lower:
                return "❌ Upload failed: Some records are missing employee names. All records must have a name. Please add names to all records in your file."
            else:
                return "❌ Upload failed: Some required information is missing from your file. Please ensure all required fields (Name, KTP, Passport ID) are filled for every record."
        
        # Handle data truncation errors
        if 'string or binary data would be truncated' in error_lower:
            return "❌ Upload failed: Some data in your file is too long for the database fields. Please check that KTP numbers are exactly 16 digits and Passport IDs are 8-9 characters."
        
        # Handle connection errors
        if 'connection' in error_lower or 'timeout' in error_lower:
            return "❌ Upload failed: Database connection issue. Please try again in a moment. If the problem persists, contact support."
        
        # Handle file format errors
        if 'unsupported file format' in error_lower or 'file format' in error_lower:
            return "❌ Upload failed: Unsupported file format. Please use CSV, XLS, or XLSX files only."
        
        # Handle validation errors
        if 'validation' in error_lower or 'invalid' in error_lower:
            return "❌ Upload failed: Some data in your file doesn't meet the required format. Please check that KTP numbers are 16 digits and Passport IDs follow the correct format (8-9 characters, starting with a letter)."
        
        # Generic database error
        if 'sql' in error_lower or 'database' in error_lower:
            return "❌ Upload failed: Database error occurred while processing your file. Please verify your data format and try again. If the problem continues, contact support."
        
        # Fallback for any other errors
        return "❌ Upload failed: An unexpected error occurred while processing your file. Please check your data format and try again. If the problem persists, contact support."

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
        """Validate and clean input data with detailed error reporting"""
        required_columns = ['name', 'personal_number', 'no_ktp', 'bod']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        records = df.to_dict('records')
        cleaned_records = []
        validation_errors = []
        
        # Check for duplicates within the file itself
        seen_passport_ids = {}
        seen_ktp_numbers = {}
        seen_personal_numbers = {}
        
        for i, record in enumerate(records):
            try:
                if pd.isna(record.get('name')) and pd.isna(record.get('no_ktp')):
                    continue
                
                row_num = i + 2  # Excel row number (accounting for header)
                
                cleaned_record = {
                    'name': str(record.get('name', '')).strip(),
                    'personal_number': str(record.get('personal_number', '')).strip(),
                    'no_ktp': str(record.get('no_ktp', '')).strip(),
                    'bod': self.parse_date(record.get('bod')),
                    'status': self.normalize_status(record.get('status', 'Active')),
                    'passport_id': str(record.get('passport_id', '')).strip() if record.get('passport_id') else ''
                }
                
                # Validate required fields
                if not cleaned_record['name']:
                    validation_errors.append(f"Row {row_num}: Missing employee name")
                    continue
                    
                if not cleaned_record['no_ktp']:
                    validation_errors.append(f"Row {row_num}: Missing KTP number for employee '{cleaned_record['name']}'")
                    continue
                    
                if not cleaned_record['passport_id']:
                    # Auto-generate passport_id but warn user
                    cleaned_record['passport_id'] = self.generate_passport_id(cleaned_record)
                    validation_errors.append(f"Row {row_num}: Missing Passport ID for employee '{cleaned_record['name']}' - AUTO-GENERATED: {cleaned_record['passport_id']} (please verify this is correct)")
                    # Don't continue, allow processing with generated passport_id
                
                # Check for duplicates within the file
                if cleaned_record['passport_id'] in seen_passport_ids:
                    other_row = seen_passport_ids[cleaned_record['passport_id']]
                    validation_errors.append(f"Row {row_num}: Duplicate Passport ID '{cleaned_record['passport_id']}' - also found in row {other_row} for employee '{cleaned_record['name']}'")
                    continue
                else:
                    seen_passport_ids[cleaned_record['passport_id']] = row_num
                
                if cleaned_record['no_ktp'] in seen_ktp_numbers:
                    other_row = seen_ktp_numbers[cleaned_record['no_ktp']]
                    validation_errors.append(f"Row {row_num}: Duplicate KTP number '{cleaned_record['no_ktp']}' - also found in row {other_row} for employee '{cleaned_record['name']}'")
                    continue
                else:
                    seen_ktp_numbers[cleaned_record['no_ktp']] = row_num
                
                if cleaned_record['personal_number'] in seen_personal_numbers:
                    other_row = seen_personal_numbers[cleaned_record['personal_number']]
                    validation_errors.append(f"Row {row_num}: Duplicate Personal Number '{cleaned_record['personal_number']}' - also found in row {other_row} for employee '{cleaned_record['name']}'")
                    continue
                else:
                    seen_personal_numbers[cleaned_record['personal_number']] = row_num
                
                cleaned_records.append(cleaned_record)
                
            except Exception as e:
                validation_errors.append(f"Row {i+2}: Error processing data - {str(e)}")
                self.stats['errors'] += 1
        
        # Check for duplicates against existing database records
        if cleaned_records:
            db_errors = self.check_database_duplicates(cleaned_records)
            validation_errors.extend(db_errors)
        
        # Separate critical errors from warnings
        critical_errors = [error for error in validation_errors if not "AUTO-GENERATED" in error]
        warnings = [error for error in validation_errors if "AUTO-GENERATED" in error]
        
        # If there are critical validation errors, raise them as a detailed message
        if critical_errors:
            error_summary = f"❌ CRITICAL VALIDATION ERRORS ({len(critical_errors)} issues):\n\n"
            error_summary += "\n".join(critical_errors[:10])  # Show first 10 errors
            if len(critical_errors) > 10:
                error_summary += f"\n... and {len(critical_errors) - 10} more errors."
            error_summary += "\n\nPlease fix these issues and try uploading again."
            raise ValueError(error_summary)
        
        # Store warnings for later reporting
        if warnings:
            if not hasattr(self, '_validation_warnings'):
                self._validation_warnings = []
            self._validation_warnings.extend(warnings)
        
        return cleaned_records
    
    def check_database_duplicates(self, records: List[Dict]) -> List[str]:
        """Check for duplicates against existing database records"""
        errors = []
        
        for record in records:
            # Check passport_id duplicates
            existing_passport = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.passport_id == record['passport_id']
            ).first()
            
            if existing_passport:
                errors.append(f"❌ Passport ID '{record['passport_id']}' for employee '{record['name']}' already exists in database for employee '{existing_passport.name}' (G_ID: {existing_passport.g_id})")
            
            # Check KTP duplicates
            existing_ktp = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.no_ktp == record['no_ktp']
            ).first()
            
            if existing_ktp:
                errors.append(f"❌ KTP number '{record['no_ktp']}' for employee '{record['name']}' already exists in database for employee '{existing_ktp.name}' (G_ID: {existing_ktp.g_id})")
            
            # Check personal number duplicates
            existing_personal = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.personal_number == record['personal_number']
            ).first()
            
            if existing_personal:
                errors.append(f"❌ Personal Number '{record['personal_number']}' for employee '{record['name']}' already exists in database for employee '{existing_personal.name}' (G_ID: {existing_personal.g_id})")
        
        return errors
    
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
            if hasattr(self, '_validation_warnings'):
                delattr(self, '_validation_warnings')
            
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
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Excel sync completed. Stats: {self.stats}")
            
            # Prepare success message with any warnings
            success_message = 'Excel synchronization completed successfully'
            warnings = []
            
            if hasattr(self, '_validation_warnings') and self._validation_warnings:
                warnings.extend(self._validation_warnings)
            
            return {
                'success': True,
                'stats': self.stats,
                'message': success_message,
                'warnings': warnings if warnings else None
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
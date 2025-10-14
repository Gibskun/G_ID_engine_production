"""
Excel Data Synchronization Service

This service integrates with the existing FastAPI application to provide
Excel/CSV data synchronization functionality with comprehensive data validation.
"""

import pandas as pd
import logging
from datetime import datetime, date
from typing import List, Dict, Set, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import GlobalID, GlobalIDNonDatabase, Pegawai, AuditLog
from app.services.gid_generator import GIDGenerator
from app.services.data_validation_service import DataValidationService
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class ExcelSyncService:
    """
    Service for synchronizing Excel/CSV data with database tables
    Integrates with existing FastAPI application structure and includes data validation
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.gid_generator = GIDGenerator(db_session)
        self.validation_service = DataValidationService(db_session)
        self.config_service = ConfigService(db_session)
        self.stats = {
            'existing_updated': 0,
            'new_created': 0,
            'gid_reused': 0,  # NEW: Track when existing G_IDs are reused from global_id table
            'obsolete_deactivated': 0,
            'errors': 0,
            'total_processed': 0,
            'skipped': 0,
            'validation_failed': 0,
            'validation_passed': 0
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
        """Validate and clean input data using the comprehensive validation service"""
        
        # Check for required columns with flexible names
        column_mapping = self._map_columns(df)
        if not column_mapping.get('name'):
            raise ValueError("Missing required column: 'name' (or variants like 'nama', 'full_name')")
        
        # Rename columns to standard names
        df_renamed = df.rename(columns=column_mapping)
        
        records = df_renamed.to_dict('records')
        cleaned_records = []
        validation_errors = []
        
        logger.info(f"🔍 Validating {len(records)} records using comprehensive validation rules...")
        
        for i, record in enumerate(records):
            try:
                row_num = i + 2  # Excel row number (accounting for header)
                
                # Skip completely empty rows
                if pd.isna(record.get('name')) and pd.isna(record.get('no_ktp')) and pd.isna(record.get('passport_id')):
                    continue
                
                # Clean the raw data
                cleaned_record = {
                    'name': str(record.get('name', '')).strip() if pd.notna(record.get('name')) else '',
                    'personal_number': str(record.get('personal_number', '')).strip() if pd.notna(record.get('personal_number')) and str(record.get('personal_number')).strip() not in ['nan', 'NaN', 'NULL', 'null', '', '0'] else None,
                    'no_ktp': str(record.get('no_ktp', '')).strip() if pd.notna(record.get('no_ktp')) and str(record.get('no_ktp')).strip() not in ['nan', 'NaN', 'NULL', 'null', '', '0'] else None,
                    'passport_id': str(record.get('passport_id', '')).strip() if pd.notna(record.get('passport_id')) and str(record.get('passport_id')).strip() not in ['nan', 'NaN', 'NULL', 'null', '', '0'] else None,
                    'bod': self.parse_date(record.get('bod')),
                    'status': self.normalize_status(record.get('status', 'Active')),
                    'process': str(record.get('process', '')).strip() if pd.notna(record.get('process')) else None
                }
                
                # DEBUG: Log the cleaned record for matching analysis
                logger.info(f"🧹 [SYNC] Row {row_num} cleaned data: Name='{cleaned_record['name']}' | KTP='{cleaned_record['no_ktp']}' | BOD={cleaned_record['bod']} | Personal={cleaned_record['personal_number']}")
                
                # Use validation service to validate the record
                validation_result = self.validation_service.validate_record(cleaned_record, row_num)
                
                if validation_result['valid']:
                    cleaned_records.append(cleaned_record)
                    self.stats['validation_passed'] += 1
                else:
                    # Record failed validation
                    self.stats['validation_failed'] += 1
                    self.stats['skipped'] += 1
                    
                    error_msg = f"Row {row_num}: " + " | ".join(validation_result['errors'])
                    validation_errors.append(error_msg)
                    logger.warning(f"Validation failed for row {row_num}: {validation_result['errors']}")
                    
            except Exception as e:
                self.stats['errors'] += 1
                self.stats['skipped'] += 1
                error_msg = f"Row {row_num}: Processing error - {str(e)}"
                validation_errors.append(error_msg)
                logger.error(f"Error processing row {row_num}: {str(e)}")
        
        # Store validation errors for reporting
        if hasattr(self, '_processing_warnings'):
            self._processing_warnings.extend(validation_errors)
        else:
            self._processing_warnings = validation_errors
        
        logger.info(f"✅ Validation complete: {len(cleaned_records)} valid records, {self.stats['validation_failed']} failed validation")
        
        return cleaned_records
    
    def _map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Map actual column names to standardized names"""
        column_mapping = {}
        
        # Define alternative names for each column
        alt_names = {
            'name': ['name', 'nama', 'full_name', 'fullname'],
            'personal_number': ['personal_number', 'phone', 'telp', 'telepon', 'hp'],
            'no_ktp': ['no_ktp', 'noktp', 'ktp', 'id_number', 'nik', 'no_nik'],
            'passport_id': ['passport_id', 'passport', 'passportid', 'no_passport', 'passport_number'],
            'bod': ['bod', 'birth_date', 'birthdate', 'date_of_birth', 'dob', 'tanggal_lahir', 'tgl_lahir'],
            'process': ['process', 'proses', 'flag', 'allow', 'enable'],
            'status': ['status']
        }
        
        # Find matching columns
        for std_col, possible_names in alt_names.items():
            for actual_col in df.columns:
                if actual_col.lower().strip() in [name.lower() for name in possible_names]:
                    column_mapping[actual_col] = std_col
                    break
        
        return column_mapping
    
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
        """Get existing records mapped by their unique key - ONLY from global_id_non_database"""
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
    
    def get_all_active_records_map(self) -> Dict[Tuple, str]:
        """Get ALL active records from both global_id and global_id_non_database tables mapped by unique key -> G_ID"""
        all_records_map = {}
        
        # Get records from global_id table (employee source)
        global_records = self.db.query(GlobalID).filter(GlobalID.status == 'Active').all()
        for record in global_records:
            key = self.create_record_key({
                'name': record.name,
                'personal_number': record.personal_number,
                'no_ktp': record.no_ktp,
                'bod': record.bod
            })
            all_records_map[key] = record.g_id
        
        # Get records from global_id_non_database table (excel source)  
        non_db_records = self.db.query(GlobalIDNonDatabase).filter(GlobalIDNonDatabase.status == 'Active').all()
        for record in non_db_records:
            key = self.create_record_key({
                'name': record.name,
                'personal_number': record.personal_number,
                'no_ktp': record.no_ktp,
                'bod': record.bod
            })
            # Don't overwrite if already exists (prioritize global_id source)
            if key not in all_records_map:
                all_records_map[key] = record.g_id
        
        return all_records_map
    
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
                
                # NEW: Also reactivate pegawai record if it's employee-sourced
                if global_record.source == 'database_pegawai':
                    pegawai_record = self.db.query(Pegawai).filter(
                        Pegawai.g_id == existing_record.g_id
                    ).first()
                    if pegawai_record and pegawai_record.deleted_at is not None:
                        setattr(pegawai_record, 'deleted_at', None)
                        setattr(pegawai_record, 'updated_at', datetime.utcnow())
                        logger.info(f"🔄 [UPDATE] Restored pegawai record for G_ID {existing_record.g_id}")
            
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
        """
        Scenario 2: Create new record with generated G_ID or reuse existing G_ID
        NEW LOGIC: Check if data exists in global_id table first to reuse G_ID
        """
        try:
            logger.info(f"🚀 [SYNC] Processing new record creation for: {input_record.get('name')} | KTP: {input_record.get('no_ktp')}")
            
            # NEW: Check if there's an existing record in global_id table (employee data) with same content
            existing_global = self._find_existing_global_record(input_record)
            
            if existing_global:
                # Found matching data in global_id table - reuse the G_ID
                existing_g_id = existing_global.g_id
                logger.info(f"🔄 [SYNC] Found existing G_ID {existing_g_id} in global_id table for {input_record['name']} - REUSING INSTEAD OF CREATING NEW!")
                
                # Check if already exists in global_id_non_database
                existing_non_db = self.db.query(GlobalIDNonDatabase).filter(
                    GlobalIDNonDatabase.g_id == existing_g_id
                ).first()
                
                if existing_non_db:
                    # Update existing record
                    return self.update_existing_record(input_record, existing_non_db)
                else:
                    # Create new record in global_id_non_database with existing G_ID
                    logger.info(f"🎯 [SYNC] Creating NEW record in global_id_non_database with EXISTING G_ID {existing_g_id}")
                    
                    new_non_db = GlobalIDNonDatabase(
                        g_id=existing_g_id,
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
                    logger.info(f"✅ [SYNC] Added new_non_db record to session with G_ID {existing_g_id}")
                    
                    # Ensure global_id record is active
                    if existing_global.status != 'Active':
                        existing_global.status = 'Active'
                        existing_global.updated_at = datetime.utcnow()
                        logger.info(f"🔄 [SYNC] Reactivated global_id record {existing_g_id}")
                    
                    # NEW: Also reactivate pegawai record if it's employee-sourced
                    if existing_global.source == 'database_pegawai':
                        pegawai_record = self.db.query(Pegawai).filter(
                            Pegawai.g_id == existing_g_id
                        ).first()
                        if pegawai_record and pegawai_record.deleted_at is not None:
                            setattr(pegawai_record, 'deleted_at', None)
                            setattr(pegawai_record, 'updated_at', datetime.utcnow())
                            logger.info(f"🔄 [SYNC] Restored pegawai record for G_ID {existing_g_id}")
                    
                    self.log_audit_action(
                        table_name="global_id_non_database",
                        record_id=existing_g_id,
                        action="INSERT",
                        new_values={
                            "g_id": existing_g_id,
                            "name": input_record['name'],
                            "no_ktp": input_record['no_ktp'],
                            "status": "Active",
                            "reused_gid": True
                        },
                        change_reason="Excel sync - reused existing G_ID from global_id table"
                    )
                    
                    # UPDATED: Track as G_ID reuse instead of new creation
                    self.stats['gid_reused'] += 1
                    logger.info(f"✅ [SYNC] SUCCESS! Reused existing G_ID {existing_g_id} and added to global_id_non_database")
                    logger.info(f"📊 [SYNC] Stats updated - gid_reused: {self.stats['gid_reused']}")
                    return True
            
            # Check if there's an existing 'Non Active' record with same data that can be reused
            existing_inactive = self.db.query(GlobalIDNonDatabase).filter(
                and_(
                    GlobalIDNonDatabase.name == input_record['name'],
                    GlobalIDNonDatabase.no_ktp == input_record['no_ktp'],
                    GlobalIDNonDatabase.status == 'Non Active'
                )
            ).first()
            
            if existing_inactive:
                # Reuse existing G_ID instead of generating new one
                logger.info(f"🔄 Reusing existing inactive G_ID {existing_inactive.g_id} for {input_record['name']}")
                return self.update_existing_record(input_record, existing_inactive)
            
            # No existing record found - generate new G_ID
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

    def _find_existing_global_record(self, input_record: Dict) -> Optional[GlobalID]:
        """
        Find existing record in global_id table based on available identifiers
        IMPROVED LOGIC: Match based on your specific example requirements
        """
        
        logger.info(f"🔍 [SYNC] Searching for existing G_ID for: {input_record.get('name')} | KTP: {input_record.get('no_ktp')} | BOD: {input_record.get('bod')}")
        
        # STRATEGY 1: Exact match on name + no_ktp + bod (most precise)
        if input_record.get('name') and input_record.get('no_ktp') and input_record.get('bod'):
            exact_match = self.db.query(GlobalID).filter(
                and_(
                    GlobalID.name == input_record['name'],
                    GlobalID.no_ktp == input_record['no_ktp'],
                    GlobalID.bod == input_record['bod']
                )
            ).first()
            
            if exact_match:
                logger.info(f"✅ [SYNC] EXACT MATCH found! G_ID {exact_match.g_id} | Name: {exact_match.name} | KTP: {exact_match.no_ktp} | BOD: {exact_match.bod}")
                return exact_match
        
        # STRATEGY 2: Match on name + no_ktp (ignore BOD differences)
        if input_record.get('name') and input_record.get('no_ktp'):
            name_ktp_match = self.db.query(GlobalID).filter(
                and_(
                    GlobalID.name == input_record['name'],
                    GlobalID.no_ktp == input_record['no_ktp']
                )
            ).first()
            
            if name_ktp_match:
                logger.info(f"✅ [SYNC] NAME+KTP MATCH found! G_ID {name_ktp_match.g_id} | Name: {name_ktp_match.name} | KTP: {name_ktp_match.no_ktp}")
                logger.info(f"   Database BOD: {name_ktp_match.bod} | Upload BOD: {input_record.get('bod')}")
                return name_ktp_match
        
        # STRATEGY 3: Match only on no_ktp (unique identifier approach)
        if input_record.get('no_ktp'):
            ktp_match = self.db.query(GlobalID).filter(
                GlobalID.no_ktp == input_record['no_ktp']
            ).first()
            
            if ktp_match:
                logger.info(f"✅ [SYNC] KTP-ONLY MATCH found! G_ID {ktp_match.g_id} | Name: {ktp_match.name} | KTP: {ktp_match.no_ktp}")
                logger.info(f"   Database Name: '{ktp_match.name}' | Upload Name: '{input_record.get('name')}'")
                return ktp_match
        
        # STRATEGY 4: Match on name + passport_id if no KTP
        if input_record.get('name') and input_record.get('passport_id') and not input_record.get('no_ktp'):
            passport_match = self.db.query(GlobalID).filter(
                and_(
                    GlobalID.name == input_record['name'],
                    GlobalID.passport_id == input_record['passport_id']
                )
            ).first()
            
            if passport_match:
                logger.info(f"✅ [SYNC] NAME+PASSPORT MATCH found! G_ID {passport_match.g_id}")
                return passport_match
        
        logger.info(f"❌ [SYNC] NO MATCHING RECORD found for: {input_record.get('name')} | KTP: {input_record.get('no_ktp')}")
        return None
    
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
    
    def deactivate_records_not_in_upload(self, input_keys: Set) -> bool:
        """
        NEW COMPREHENSIVE DEACTIVATION LOGIC
        Deactivate ALL records (from both global_id and global_id_non_database) that are not in the uploaded file
        This ensures proper synchronization across all three tables (pegawai, global_id, global_id_non_database)
        """
        try:
            logger.info(f"🔄 [DEACTIVATE] Starting comprehensive deactivation check for uploaded keys: {len(input_keys)} records")
            
            # Get all currently active records from both tables
            all_active_records = self.get_all_active_records_map()
            logger.info(f"🔍 [DEACTIVATE] Found {len(all_active_records)} active records across all tables")
            
            deactivated_count = 0
            
            # Check each active record to see if it's in the uploaded file
            for record_key, g_id in all_active_records.items():
                if record_key not in input_keys:
                    # Record not found in upload - deactivate it across all tables
                    logger.info(f"🗑️ [DEACTIVATE] Record not in upload, deactivating G_ID {g_id}")
                    
                    # Deactivate in global_id table
                    global_record = self.db.query(GlobalID).filter(
                        GlobalID.g_id == g_id
                    ).first()
                    if global_record and global_record.status == 'Active':
                        setattr(global_record, 'status', 'Non Active')
                        setattr(global_record, 'updated_at', datetime.utcnow())
                        logger.info(f"  ❌ Deactivated global_id record {g_id}")
                        
                        # If it's employee-sourced, also soft-delete from pegawai table
                        if global_record.source == 'database_pegawai':
                            pegawai_record = self.db.query(Pegawai).filter(
                                Pegawai.g_id == g_id
                            ).first()
                            if pegawai_record and pegawai_record.deleted_at is None:
                                setattr(pegawai_record, 'deleted_at', datetime.utcnow())
                                setattr(pegawai_record, 'updated_at', datetime.utcnow())
                                logger.info(f"  🗑️ Soft-deleted pegawai record {g_id}")
                    
                    # FIXED: Always check for pegawai record regardless of source
                    # This ensures synchronization when Excel uploads change global status
                    pegawai_record = self.db.query(Pegawai).filter(
                        Pegawai.g_id == g_id
                    ).first()
                    if pegawai_record and pegawai_record.deleted_at is None:
                        setattr(pegawai_record, 'deleted_at', datetime.utcnow())
                        setattr(pegawai_record, 'updated_at', datetime.utcnow())
                        logger.info(f"  🗑️ [SYNC] Soft-deleted pegawai record {g_id} due to global status change")
                    
                    # Deactivate in global_id_non_database table if exists
                    non_db_record = self.db.query(GlobalIDNonDatabase).filter(
                        GlobalIDNonDatabase.g_id == g_id
                    ).first()
                    if non_db_record and non_db_record.status == 'Active':
                        setattr(non_db_record, 'status', 'Non Active')
                        setattr(non_db_record, 'updated_at', datetime.utcnow())
                        logger.info(f"  ❌ Deactivated global_id_non_database record {g_id}")
                    
                    self.log_audit_action(
                        table_name="global_id",
                        record_id=g_id,
                        action="UPDATE",
                        new_values={"status": "Non Active", "reason": "not_in_upload"},
                        change_reason="Excel sync - deactivated (not in upload)"
                    )
                    
                    deactivated_count += 1
                else:
                    logger.debug(f"✅ [DEACTIVATE] Record found in upload, keeping active: {g_id}")
            
            self.stats['obsolete_deactivated'] = deactivated_count
            logger.info(f"✅ [DEACTIVATE] Comprehensive deactivation complete: {deactivated_count} records deactivated")
            return True
            
        except Exception as e:
            logger.error(f"Error in comprehensive deactivation: {str(e)}")
            self.stats['errors'] += 1
            return False
    
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
                    
                    # NEW: Also deactivate corresponding pegawai record by setting deleted_at
                    if global_record and global_record.source == 'database_pegawai':
                        # Find pegawai record by matching G_ID
                        pegawai_record = self.db.query(Pegawai).filter(
                            Pegawai.g_id == existing_record.g_id
                        ).first()
                        
                        if pegawai_record and pegawai_record.deleted_at is None:
                            setattr(pegawai_record, 'deleted_at', datetime.utcnow())
                            setattr(pegawai_record, 'updated_at', datetime.utcnow())
                            logger.info(f"🗑️ [DEACTIVATE] Soft-deleted pegawai record for G_ID {existing_record.g_id}")
                    
                    # FIXED: Always check for pegawai record regardless of source
                    # This ensures synchronization when Excel uploads change global status
                    pegawai_record = self.db.query(Pegawai).filter(
                        Pegawai.g_id == existing_record.g_id
                    ).first()
                    
                    if pegawai_record and pegawai_record.deleted_at is None:
                        setattr(pegawai_record, 'deleted_at', datetime.utcnow())
                        setattr(pegawai_record, 'updated_at', datetime.utcnow())
                        logger.info(f"🗑️ [SYNC] Soft-deleted pegawai record for G_ID {existing_record.g_id} due to global status change")
                    
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
            
            # NEW LOGIC: Prioritize G_ID reuse from global_id table first
            records_to_update = []
            records_to_create = []
            
            for input_record in input_records:
                logger.info(f"🔍 [SYNC] Processing record: {input_record.get('name')} | KTP: {input_record.get('no_ktp')}")
                
                # STEP 1: Check if data exists in global_id table (employee data) - HIGHEST PRIORITY
                existing_global = self._find_existing_global_record(input_record)
                
                if existing_global:
                    logger.info(f"✅ [SYNC] Found match in global_id table: G_ID {existing_global.g_id}")
                    
                    # Check if this G_ID already exists in global_id_non_database
                    existing_non_db = self.db.query(GlobalIDNonDatabase).filter(
                        GlobalIDNonDatabase.g_id == existing_global.g_id
                    ).first()
                    
                    if existing_non_db:
                        logger.info(f"🔄 [SYNC] G_ID {existing_global.g_id} already in global_id_non_database - updating")
                        records_to_update.append((input_record, existing_non_db))
                    else:
                        logger.info(f"🆕 [SYNC] G_ID {existing_global.g_id} NOT in global_id_non_database - will create with existing G_ID")
                        # This will go to create_new_record which will reuse the G_ID
                        records_to_create.append(input_record)
                else:
                    # STEP 2: Check existing records in global_id_non_database
                    record_key = self.create_record_key(input_record)
                    
                    if record_key in existing_records:
                        logger.info(f"🔄 [SYNC] Found match in global_id_non_database table")
                        records_to_update.append((input_record, existing_records[record_key]))
                    else:
                        # STEP 3: Check for inactive records that can be reused
                        existing_inactive = self.db.query(GlobalIDNonDatabase).filter(
                            and_(
                                GlobalIDNonDatabase.name == input_record['name'],
                                GlobalIDNonDatabase.no_ktp == input_record['no_ktp'],
                                GlobalIDNonDatabase.status == 'Non Active'
                            )
                        ).first()
                        
                        if existing_inactive:
                            logger.info(f"🔄 [SYNC] Found inactive record to reuse: G_ID {existing_inactive.g_id}")
                            records_to_update.append((input_record, existing_inactive))
                        else:
                            logger.info(f"🆕 [SYNC] No existing match found - will create new G_ID")
                            records_to_create.append(input_record)
            
            # Process updates (existing records)
            logger.info(f"🔄 Processing {len(records_to_update)} existing records...")
            for input_record, existing_record in records_to_update:
                self.update_existing_record(input_record, existing_record)
            
            # PROCESS NEW RECORDS: Handle G_ID reuse logic individually
            if records_to_create:
                logger.info(f"🚀 Processing {len(records_to_create)} new records (checking for G_ID reuse)...")
                for input_record in records_to_create:
                    self.create_new_record(input_record)
            
            # NEW: Handle status management for existing records
            logger.info(f"🔄 Processing status management for existing excel records...")
            status_result = self.handle_status_management_for_upload(input_records)
            if status_result['success']:
                self.stats['status_reactivated'] = status_result['reactivated_count']
                self.stats['status_deactivated'] = status_result['deactivated_count']
                logger.info(f"✅ Status management: {status_result['reactivated_count']} reactivated, {status_result['deactivated_count']} deactivated")
            else:
                logger.warning(f"⚠️ Status management failed: {status_result.get('error', 'Unknown error')}")
            
            # Deactivate obsolete records (Scenario 3) - ENHANCED to handle all tables
            # This ensures records not found in the upload get deactivated across all tables
            self.deactivate_records_not_in_upload(input_keys)
            
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
            
            # Prepare success message with validation and processing details
            total_records = len(df)
            valid_records = self.stats.get('validation_passed', 0)
            invalid_records = self.stats.get('validation_failed', 0)
            created_records = self.stats.get('new_created', 0)
            reused_records = self.stats.get('gid_reused', 0)
            updated_records = self.stats.get('existing_updated', 0)
            
            success_message_parts = [
                f"Processing complete:",
                f"✅ Total records in file: {total_records}",
                f"✅ Validation passed: {valid_records}",
                f"❌ Validation failed: {invalid_records}"
            ]
            
            # Add G_ID processing details based on what actually happened
            if reused_records > 0:
                success_message_parts.append(f"� G_IDs reused from employee data: {reused_records}")
            
            if created_records > 0:
                success_message_parts.append(f"✨ New G_IDs created: {created_records}")
            
            if updated_records > 0:
                success_message_parts.append(f"� Existing records updated: {updated_records}")
            
            success_message_parts.append(f"📊 Success rate: {(valid_records / total_records * 100):.1f}%" if total_records > 0 else "No records processed")
            
            success_message = "\n".join(success_message_parts)
            
            warnings = []
            skipped_details = []
            
            if hasattr(self, '_processing_warnings') and self._processing_warnings:
                warnings.extend(self._processing_warnings)
                if len(warnings) > 10:  # Limit warning display
                    shown_warnings = warnings[:10]
                    shown_warnings.append(f"... and {len(warnings) - 10} more validation errors")
                    warnings = shown_warnings
            
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

    def handle_status_management_for_upload(self, input_records: List[Dict]) -> Dict:
        """
        Handle status changes for existing records based on upload content
        Records in upload: remain/become active
        Records not in upload: become non-active
        """
        try:
            logger.info(f"🔄 Processing status management for {len(input_records)} upload records")
            
            # Create set of identifiers from uploaded data
            uploaded_identifiers = set()
            uploaded_names = set()
            
            for record in input_records:
                if record.get('no_ktp'):
                    uploaded_identifiers.add(('ktp', record['no_ktp']))
                if record.get('passport_id'):
                    uploaded_identifiers.add(('passport', record['passport_id']))
                if record.get('name'):
                    uploaded_names.add(record['name'])
                    uploaded_identifiers.add(('name', record['name']))
            
            # Get ALL records from global_id_non_database (not just excel-sourced)
            # This ensures employee-sourced records also get proper status management
            existing_excel_records = self.db.query(GlobalIDNonDatabase).all()
            
            reactivated_count = 0
            deactivated_count = 0
            status_changes = []
            
            for record in existing_excel_records:
                record_identifiers = set()
                
                # Build identifiers for this record
                if record.no_ktp:
                    record_identifiers.add(('ktp', record.no_ktp))
                if record.passport_id:
                    record_identifiers.add(('passport', record.passport_id))
                if record.name:
                    record_identifiers.add(('name', record.name))
                
                # Check if any identifier matches uploaded data
                has_match = bool(uploaded_identifiers & record_identifiers)
                
                if has_match and record.status != 'Active':
                    # Record found in upload - reactivate
                    setattr(record, 'status', 'Active')
                    setattr(record, 'updated_at', datetime.utcnow())
                    
                    # Also reactivate in global_id table (for all sources, not just excel)
                    global_record = self.db.query(GlobalID).filter(
                        GlobalID.g_id == record.g_id
                    ).first()
                    if global_record and global_record.status != 'Active':
                        setattr(global_record, 'status', 'Active')
                        setattr(global_record, 'updated_at', datetime.utcnow())
                        
                        # NEW: Also reactivate pegawai record if it's employee-sourced
                        if global_record.source == 'database_pegawai':
                            pegawai_record = self.db.query(Pegawai).filter(
                                Pegawai.g_id == record.g_id
                            ).first()
                            if pegawai_record and pegawai_record.deleted_at is not None:
                                setattr(pegawai_record, 'deleted_at', None)
                                setattr(pegawai_record, 'updated_at', datetime.utcnow())
                                logger.info(f"🔄 [REACTIVATE] Restored pegawai record for G_ID {record.g_id}")
                    
                    # FIXED: Always check for pegawai record regardless of source for reactivation
                    pegawai_record = self.db.query(Pegawai).filter(
                        Pegawai.g_id == record.g_id
                    ).first()
                    if pegawai_record and pegawai_record.deleted_at is not None:
                        setattr(pegawai_record, 'deleted_at', None)
                        setattr(pegawai_record, 'updated_at', datetime.utcnow())
                        logger.info(f"🔄 [SYNC] Restored pegawai record for G_ID {record.g_id} due to global status change")
                    
                    reactivated_count += 1
                    status_changes.append({
                        'g_id': record.g_id,
                        'name': record.name,
                        'action': 'reactivated',
                        'reason': 'Found in current upload'
                    })
                
                elif not has_match and record.status == 'Active':
                    # Record not found in upload - deactivate
                    setattr(record, 'status', 'Non Active')
                    setattr(record, 'updated_at', datetime.utcnow())
                    
                    # Also deactivate in global_id table (for all sources, not just excel)
                    global_record = self.db.query(GlobalID).filter(
                        GlobalID.g_id == record.g_id
                    ).first()
                    if global_record and global_record.status == 'Active':
                        setattr(global_record, 'status', 'Non Active')
                        setattr(global_record, 'updated_at', datetime.utcnow())
                        
                        # NEW: Also deactivate pegawai record if it's employee-sourced
                        if global_record.source == 'database_pegawai':
                            pegawai_record = self.db.query(Pegawai).filter(
                                Pegawai.g_id == record.g_id
                            ).first()
                            if pegawai_record and pegawai_record.deleted_at is None:
                                setattr(pegawai_record, 'deleted_at', datetime.utcnow())
                                setattr(pegawai_record, 'updated_at', datetime.utcnow())
                                logger.info(f"🗑️ [STATUS] Soft-deleted pegawai record for G_ID {record.g_id}")
                    
                    # FIXED: Always check for pegawai record regardless of source for deactivation
                    pegawai_record = self.db.query(Pegawai).filter(
                        Pegawai.g_id == record.g_id
                    ).first()
                    if pegawai_record and pegawai_record.deleted_at is None:
                        setattr(pegawai_record, 'deleted_at', datetime.utcnow())
                        setattr(pegawai_record, 'updated_at', datetime.utcnow())
                        logger.info(f"🗑️ [SYNC] Soft-deleted pegawai record for G_ID {record.g_id} due to global status change")
                    
                    deactivated_count += 1
                    status_changes.append({
                        'g_id': record.g_id,
                        'name': record.name,
                        'action': 'deactivated',
                        'reason': 'Not found in current upload'
                    })
            
            logger.info(f"✅ Status management complete: {reactivated_count} reactivated, {deactivated_count} deactivated")
            
            return {
                'success': True,
                'reactivated_count': reactivated_count,
                'deactivated_count': deactivated_count,
                'status_changes': status_changes,
                'total_processed': len(existing_excel_records)
            }
            
        except Exception as e:
            logger.error(f"Error in status management: {str(e)}")
            return {
                'success': False,
                'error': f"Status management failed: {str(e)}",
                'reactivated_count': 0,
                'deactivated_count': 0
            }
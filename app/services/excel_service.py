"""
Excel and CSV file ingestion service for processing uploaded files
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from io import BytesIO, StringIO

from app.models.models import GlobalID, GlobalIDNonDatabase, AuditLog
from app.services.gid_generator import GIDGenerator
from app.services.config_service import ConfigService
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class ExcelIngestionService:
    """Handles Excel and CSV file upload and data processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gid_generator = GIDGenerator(db)
        self.config_service = ConfigService(db)
    
    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process Excel or CSV file and insert data into Global_ID and Global_ID_NON_Database tables
        
        Args:
            file_content: Binary content of the file
            filename: Name of the uploaded file
            
        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Starting file processing: {filename}")
            
            # Determine file type and read accordingly
            file_ext = self._get_file_extension(filename)
            
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(BytesIO(file_content))
            elif file_ext == '.csv':
                # Try different encodings for CSV
                df = self._read_csv_with_encoding(file_content, filename)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported file type: {file_ext}. Supported types: .xlsx, .xls, .csv",
                    'filename': filename
                }
            
            # Validate file structure
            validation_result = self._validate_file_structure(df, filename)
            if not validation_result['valid']:
                return validation_result
            
            # Use the processed dataframe from validation
            df = validation_result['dataframe']
            
            # Process each row
            processing_result = self._process_file_rows(df, filename)
            
            logger.info(f"File processing completed for {filename}")
            return processing_result
            
        except Exception as e:
            error_msg = f"Error processing file {filename}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'filename': filename
            }
    
    def _read_csv_with_encoding(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Try to read CSV with different encodings and separators"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        separators = [',', ';']  # Support both comma and semicolon
        
        for encoding in encodings:
            for separator in separators:
                try:
                    content_str = file_content.decode(encoding)
                    df = pd.read_csv(StringIO(content_str), sep=separator)
                    
                    # Check if we got meaningful data (more than 1 column usually means correct separator)
                    if len(df.columns) > 1:
                        logger.info(f"Successfully read CSV {filename} with encoding: {encoding} and separator: '{separator}'")
                        return df
                    
                except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                    logger.debug(f"Failed to read {filename} with encoding {encoding} and separator '{separator}': {str(e)}")
                    continue
        
        # If all combinations fail, try auto-detection with pandas
        try:
            for encoding in encodings:
                try:
                    content_str = file_content.decode(encoding)
                    # Let pandas auto-detect the separator
                    df = pd.read_csv(StringIO(content_str), sep=None, engine='python')
                    logger.info(f"Successfully read CSV {filename} with encoding: {encoding} using auto-detection")
                    return df
                except Exception:
                    continue
        except Exception:
            pass
        
        # If everything fails, raise an informative error
        raise ValueError(f"Could not read CSV file {filename}. Please ensure the file uses comma (,) or semicolon (;) as separator and is properly encoded.")
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension in lowercase"""
        import os
        return os.path.splitext(filename)[1].lower()
    
    # Keep backward compatibility
    def process_excel_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Legacy method - redirects to process_file"""
        return self.process_file(file_content, filename)
    
    def _validate_file_structure(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Validate file structure and required columns"""
        try:
            required_columns = ['name', 'no_ktp', 'passport_id', 'bod']  # passport_id is now required
            optional_columns = ['personal_number']
            all_columns = required_columns + optional_columns
            
            # Handle both uppercase and lowercase column names
            df_columns_lower = [col.lower().strip() for col in df.columns]
            
            # Map actual column names to standardized names
            column_mapping = {}
            
            # Define alternative names for each column
            alt_names = {
                'name': ['name', 'nama', 'full_name', 'fullname'],
                'personal_number': ['personal_number', 'phone', 'telp', 'telepon', 'hp'],
                'no_ktp': ['no_ktp', 'noktp', 'ktp', 'id_number', 'nik', 'no_nik'],
                'passport_id': ['passport_id', 'passport', 'passportid', 'no_passport', 'passport_number'],
                'bod': ['bod', 'birth_date', 'birthdate', 'date_of_birth', 'dob', 'tanggal_lahir', 'tgl_lahir']
            }
            
            # Find matching columns
            for std_col in all_columns:
                found = False
                possible_names = alt_names.get(std_col, [std_col])
                
                for possible_name in possible_names:
                    for actual_col in df.columns:
                        if actual_col.lower().strip() == possible_name.lower():
                            column_mapping[std_col] = actual_col
                            found = True
                            break
                    if found:
                        break
                
                # Check if required column is missing
                if not found and std_col in required_columns:
                    return {
                        'valid': False,
                        'success': False,
                        'error': f"Missing required column: {std_col}. Found columns: {', '.join(df.columns)}. Expected one of: {', '.join(alt_names.get(std_col, [std_col]))}",
                        'filename': filename,
                        'required_columns': required_columns,
                        'found_columns': list(df.columns)
                    }
            
            # Rename columns to standardized names
            rename_dict = {v: k for k, v in column_mapping.items() if v in df.columns}
            df.rename(columns=rename_dict, inplace=True)
            
            if df.empty:
                return {
                    'valid': False,
                    'success': False,
                    'error': "File is empty",
                    'filename': filename
                }
            
            # Check for duplicate No_KTP within the file
            if 'no_ktp' in df.columns:
                duplicate_ktps = df[df.duplicated(subset=['no_ktp'], keep=False)]['no_ktp'].unique()
                if len(duplicate_ktps) > 0:
                    return {
                        'valid': False,
                        'success': False,
                        'error': f"Duplicate No_KTP found in file: {', '.join(map(str, duplicate_ktps))}",
                        'filename': filename,
                        'duplicate_ktps': list(duplicate_ktps)
                    }
            
            return {
                'valid': True,
                'total_rows': len(df),
                'columns': list(df.columns),
                'dataframe': df  # Return the processed dataframe
            }
            
        except Exception as e:
            return {
                'valid': False,
                'success': False,
                'error': f"Error validating file structure: {str(e)}",
                'filename': filename
            }
    
    def _process_file_rows(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Process each row from the file"""
        try:
            processing_summary = {
                'success': True,
                'filename': filename,
                'total_rows': len(df),
                'processed': 0,
                'successful': 0,
                'skipped': 0,
                'errors': [],
                'created_gids': []
            }
            
            # NEW LOGIC: Use (name, No_KTP, BOD) for uniqueness, ignore personal_number
            logger.info("🚀 Starting batch processing optimization...")
            valid_records = []
            reactivated_records = []
            for row_idx in range(len(df)):
                row = df.iloc[row_idx]
                row_num = row_idx + 2
                processing_summary['processed'] += 1
                try:
                    row_data = self._validate_and_clean_row(row, row_num)
                    if not row_data['valid']:
                        processing_summary['skipped'] += 1
                        processing_summary['errors'].append(row_data['error'])
                        continue
                    # Check for existing record by (name, No_KTP, BOD)
                    existing_global = self.db.query(GlobalID).filter(
                        and_(
                            GlobalID.name == row_data['name'],
                            GlobalID.no_ktp == row_data['No_KTP'],
                            GlobalID.bod == row_data.get('BOD')
                        )
                    ).first()
                    if existing_global:
                        if existing_global.status == "Non Active":
                            # Reactivate
                            existing_global.status = "Active"
                            existing_global.updated_at = datetime.now()
                            # Reactivate in global_id_non_database
                            existing_non_db = self.db.query(GlobalIDNonDatabase).filter(
                                and_(
                                    GlobalIDNonDatabase.name == row_data['name'],
                                    GlobalIDNonDatabase.no_ktp == row_data['No_KTP'],
                                    GlobalIDNonDatabase.bod == row_data.get('BOD')
                                )
                            ).first()
                            if existing_non_db:
                                existing_non_db.status = "Active"
                                existing_non_db.updated_at = datetime.now()
                            self.db.commit()
                            reactivated_records.append({
                                'gid': existing_global.g_id,
                                'name': row_data['name'],
                                'no_ktp': row_data['No_KTP'],
                                'reactivated': True
                            })
                            processing_summary['successful'] += 1
                            continue
                        else:
                            # Already active, skip
                            processing_summary['skipped'] += 1
                            processing_summary['errors'].append(
                                f"Row {row_num}: (name, No_KTP, BOD) already exists and is active"
                            )
                            continue
                    valid_records.append((row_num, row_data))
                except Exception as e:
                    processing_summary['errors'].append(f"Row {row_num}: {str(e)}")
                    logger.error(f"Error validating row {row_num}: {str(e)}")
                    processing_summary['skipped'] += 1
            # BATCH G_ID GENERATION: Generate all G_IDs at once for new records
            if valid_records:
                logger.info(f"🚀 Generating {len(valid_records)} G_IDs in batch...")
                batch_gids = self.gid_generator.generate_batch_gids(len(valid_records))
                result = self._batch_create_excel_records(valid_records, batch_gids, filename)
                processing_summary['successful'] += result['successful']
                processing_summary['created_gids'] = result['created_gids'] + reactivated_records
                if result['errors']:
                    processing_summary['errors'].extend(result['errors'])
            else:
                processing_summary['created_gids'] = reactivated_records
                logger.info("No valid new records to process")
            if processing_summary['successful'] == 0 and processing_summary['errors']:
                processing_summary['success'] = False
                processing_summary['error'] = "No records were successfully processed"
            return processing_summary
            
        except Exception as e:
            logger.error(f"Error processing Excel rows: {str(e)}")
            return {
                'success': False,
                'error': f"Error processing Excel rows: {str(e)}",
                'filename': filename
            }
    
    def _validate_and_clean_row(self, row: pd.Series, row_number: int) -> Dict[str, Any]:
        """Validate and clean individual row data"""
        try:
            # Check for missing required fields
            if pd.isna(row['name']) or not str(row['name']).strip():
                return {
                    'valid': False,
                    'error': f"Row {row_number}: Name is required"
                }
            
            if pd.isna(row['no_ktp']) or not str(row['no_ktp']).strip():
                return {
                    'valid': False,
                    'error': f"Row {row_number}: No_KTP is required"
                }
            
            if pd.isna(row['passport_id']) or not str(row['passport_id']).strip():
                return {
                    'valid': False,
                    'error': f"Row {row_number}: Passport_ID is required"
                }
            
            # Clean and validate data
            cleaned_data = {
                'name': str(row['name']).strip()[:255],  # Limit to 255 chars
                'personal_number': str(row['personal_number']).strip()[:15] if pd.notna(row.get('personal_number', '')) and str(row.get('personal_number', '')).strip() else None,
                'No_KTP': str(row['no_ktp']).strip()[:16],  # Limit to 16 chars
                'passport_id': str(row['passport_id']).strip()[:9]  # Limit to 9 chars
            }
            
            # Handle BOD (Birth of Date)
            if pd.notna(row['bod']):
                if isinstance(row['bod'], str):
                    try:
                        # Try to parse date string
                        cleaned_data['BOD'] = pd.to_datetime(row['bod']).date()
                    except:
                        return {
                            'valid': False,
                            'error': f"Row {row_number}: Invalid date format for BOD. Use YYYY-MM-DD"
                        }
                else:
                    try:
                        cleaned_data['BOD'] = pd.to_datetime(row['bod']).date()
                    except:
                        cleaned_data['BOD'] = None
            else:
                cleaned_data['BOD'] = None
            
            # Validate No_KTP format (should be numeric and proper length)
            # Only validate if strict validation is enabled
            if self.config_service.is_strict_validation_enabled() and self.config_service.is_ktp_validation_enabled():
                if not cleaned_data['No_KTP'].isdigit():
                    return {
                        'valid': False,
                        'error': f"Row {row_number}: No_KTP must contain only digits"
                    }
                
                if len(cleaned_data['No_KTP']) != 16:
                    return {
                        'valid': False,
                        'error': f"Row {row_number}: No_KTP must be exactly 16 digits"
                    }
            
            # Validate passport_id format (8-9 characters, first letter, numbers must dominate)
            # Only validate if strict validation is enabled
            if self.config_service.is_strict_validation_enabled() and self.config_service.is_passport_validation_enabled():
                passport_id = cleaned_data['passport_id']
                if len(passport_id) < 8 or len(passport_id) > 9:
                    return {
                        'valid': False,
                        'error': f"Row {row_number}: Passport_ID must be 8-9 characters long"
                    }
                
                # Check if passport_id starts with letters and has numbers
                if not passport_id[0].isalpha():
                    return {
                        'valid': False,
                        'error': f"Row {row_number}: Passport_ID must start with a letter"
                    }
                
                # Check if all characters are alphanumeric
                if not passport_id.isalnum():
                    return {
                        'valid': False,
                        'error': f"Row {row_number}: Passport_ID can only contain letters and numbers"
                    }
                
                # Count letters and numbers
                letter_count = sum(1 for c in passport_id if c.isalpha())
                number_count = sum(1 for c in passport_id if c.isdigit())
                
                # Numbers must dominate (be more than letters)
                if number_count <= letter_count:
                    return {
                        'valid': False,
                        'error': f"Row {row_number}: Passport_ID must have more numbers than letters"
                    }
            
            return {
                'valid': True,
                **cleaned_data
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Row {row_number}: Error validating data - {str(e)}"
            }
    
    def _batch_create_excel_records(self, input_records: list[dict], batch_gids: list[str], filename: str | None = None) -> dict:
        """Create multiple Excel records efficiently in batch (OPTIMIZED)"""
        try:
            logger.info(f"🚀 Batch creating {len(input_records)} records...")
            start_time = datetime.now()
            
            global_records = []
            non_db_records = []
            created_gids = []
            errors = []
            successful = 0
            
            current_time = datetime.now()
            
            for i, (row_num, row_data) in enumerate(input_records):
                try:
                    gid = batch_gids[i]
                    
                    # Create Global_ID record
                    global_record = GlobalID(
                        g_id=gid,
                        name=row_data['name'],
                        personal_number=row_data.get('personal_number'),
                        no_ktp=row_data['No_KTP'],
                        bod=row_data.get('BOD'),
                        status='Active',
                        source='excel',
                        created_at=current_time,
                        updated_at=current_time
                    )
                    
                    # Create Global_ID_NON_Database record
                    non_db_record = GlobalIDNonDatabase(
                        g_id=gid,
                        name=row_data['name'],
                        personal_number=row_data.get('personal_number'),
                        no_ktp=row_data['No_KTP'],
                        passport_id=row_data.get('passport_id', ''),
                        bod=row_data.get('BOD'),
                        status='Active',
                        source='excel',
                        created_at=current_time,
                        updated_at=current_time
                    )
                    
                    global_records.append(global_record)
                    non_db_records.append(non_db_record)
                    
                    created_gids.append({
                        'gid': gid,
                        'name': row_data['name'],
                        'no_ktp': row_data['No_KTP']
                    })
                    
                    successful += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: Error preparing record - {str(e)}")
                    logger.error(f"Error preparing record for row {row_num}: {str(e)}")
            
            # BATCH INSERT: Add all records at once
            if global_records and non_db_records:
                self.db.add_all(global_records)
                self.db.add_all(non_db_records)
                
                # Create audit logs
                for gid_info in created_gids:
                    audit_log = AuditLog(
                        table_name='global_id',
                        record_id=gid_info['gid'],
                        action='INSERT',
                        new_values=f"G_ID: {gid_info['gid']}, Name: {gid_info['name']}, No_KTP: {gid_info['no_ktp']}",
                        timestamp=current_time,
                        source='excel_batch_upload'
                    )
                    self.db.add(audit_log)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"✅ Batch created {successful} records in {duration:.3f} seconds ({successful/duration:.0f} records/sec)")
                logger.info(f"   📊 Global_ID table: {len(global_records)} records")
                logger.info(f"   📊 Global_ID_NON_Database table: {len(non_db_records)} records")
            
            return {
                'successful': successful,
                'created_gids': created_gids,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error in batch create: {str(e)}")
            return {
                'successful': 0,
                'created_gids': [],
                'errors': [f"Batch creation failed: {str(e)}"]
            }
    
    def _create_excel_records(self, gid: str, row_data: Dict, filename: str) -> Dict[str, Any]:
        """Create records in both Global_ID and Global_ID_NON_Database tables"""
        global_record_created = False
        non_db_record_created = False
        
        try:
            logger.info(f"🔄 Creating records for G_ID: {gid}, Name: {row_data['name']}")
            
            # Create record for Global_ID table (MAIN TABLE)
            try:
                global_record = GlobalID(
                    g_id=gid,
                    name=row_data['name'],
                    personal_number=row_data.get('personal_number'),
                    no_ktp=row_data['No_KTP'],
                    passport_id=row_data['passport_id'],
                    bod=row_data.get('BOD'),
                    status='Active',
                    source='excel'
                )
                
                self.db.add(global_record)
                self.db.flush()  # Flush to check constraints before full commit
                logger.info(f"✅ Global_ID record created successfully for {gid}")
                global_record_created = True
                
            except Exception as e:
                logger.error(f"❌ FAILED to create Global_ID record for {gid}: {str(e)}")
                self.db.rollback()
                return {
                    'success': False,
                    'error': f"Failed to create main Global_ID record: {str(e)}",
                    'table_failed': 'global_id'
                }
            
            # Create identical record for Global_ID_NON_Database table (BACKUP TABLE)
            try:
                non_db_record = GlobalIDNonDatabase(
                    g_id=gid,
                    name=row_data['name'],
                    personal_number=row_data.get('personal_number'),
                    no_ktp=row_data['No_KTP'],
                    passport_id=row_data['passport_id'],
                    bod=row_data.get('BOD'),
                    status='Active',
                    source='excel'
                )
                
                self.db.add(non_db_record)
                self.db.flush()  # Flush to check constraints
                logger.info(f"✅ Global_ID_NON_Database record created successfully for {gid}")
                non_db_record_created = True
                
            except Exception as e:
                logger.error(f"❌ FAILED to create Global_ID_NON_Database record for {gid}: {str(e)}")
                self.db.rollback()
                return {
                    'success': False,
                    'error': f"Failed to create backup Global_ID_NON_Database record: {str(e)}",
                    'table_failed': 'global_id_non_database'
                }
            
            # Commit both records together
            self.db.commit()
            logger.info(f"🎉 BOTH records committed successfully for G_ID: {gid}")
            
            # Log audit trail for both tables
            try:
                self._log_audit(
                    'global_id',
                    gid,
                    'INSERT',
                    None,
                    global_record.__dict__.copy(),
                    f'Created from Excel file: {filename}'
                )
                
                self._log_audit(
                    'global_id_non_database',
                    gid,
                    'INSERT',
                    None,
                    non_db_record.__dict__.copy(),
                    f'Created from Excel file: {filename}'
                )
                logger.debug(f"📝 Audit logs created for G_ID: {gid}")
                
            except Exception as audit_error:
                logger.warning(f"⚠️ Audit logging failed for G_ID {gid}: {str(audit_error)}")
                # Don't fail the main operation due to audit logging issues
            
            return {
                'success': True,
                'gid': gid,
                'global_record_created': global_record_created,
                'non_db_record_created': non_db_record_created
            }
            
        except IntegrityError as e:
            self.db.rollback()
            error_msg = f"Integrity error creating records for {row_data['name']}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error creating records for {row_data['name']}: {str(e)}"
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
            if new_values:
                new_values = {k: v for k, v in new_values.items() 
                             if not k.startswith('_') and k != 'registry'}
            
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_by='excel_ingestion',
                change_reason=reason
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging audit: {str(e)}")
            # Don't let audit logging failure break the main operation
    
    def get_supported_file_types(self) -> List[str]:
        """Return list of supported file types"""
        return ['.xlsx', '.xls', '.csv']
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate if file type is supported"""
        import os
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in self.get_supported_file_types()
    
    def get_excel_template(self) -> Dict[str, Any]:
        """Return Excel template structure for users"""
        return {
            'required_columns': [
                {
                    'name': 'name',
                    'description': 'Full name of the person',
                    'type': 'Text',
                    'required': True,
                    'max_length': 255,
                    'example': 'Ahmad Suharto'
                },
                {
                    'name': 'no_ktp',
                    'description': 'Indonesian ID number (exactly 16 digits)',
                    'type': 'Text (16 digits)',
                    'required': True,
                    'format': '16 digits only',
                    'example': '3201234567890001'
                },
                {
                    'name': 'personal_number',
                    'description': 'Employee personal/staff number',
                    'type': 'Text',
                    'required': False,
                    'max_length': 50,
                    'example': 'EMP-2025-0001'
                },
                {
                    'name': 'passport_id',
                    'description': 'Passport ID (8-9 characters, alphanumeric)',
                    'type': 'Text (8-9 chars)',
                    'required': False,
                    'format': 'Alphanumeric, 8-9 characters',
                    'example': 'A12345678'
                },
                {
                    'name': 'bod',
                    'description': 'Birth Date',
                    'type': 'Date',
                    'required': False,
                    'format': 'YYYY-MM-DD',
                    'example': '1990-01-15'
                }
            ],
            'notes': [
                'no_ktp must be exactly 16 digits and unique (no duplicates)',
                'name is required and cannot be empty',
                'Date format for bod must be YYYY-MM-DD',
                'personal_number and passport_id are optional',
                'CSV files support both comma (,) and semicolon (;) separators',
                'Multiple text encodings are automatically detected',
                'Remove any "process" column if copying from dummy data'
            ]
        }
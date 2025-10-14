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

from app.models.models import GlobalID, GlobalIDNonDatabase, AuditLog, Pegawai
from app.services.gid_generator import GIDGenerator
from app.services.config_service import ConfigService
from app.services.data_validation_service import DataValidationService
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class ExcelIngestionService:
    """Handles Excel and CSV file upload and data processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gid_generator = GIDGenerator(db)
        self.config_service = ConfigService(db)
        self.validation_service = DataValidationService(db)
    
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
            required_columns = ['name']  # Only name is strictly required
            optional_columns = ['personal_number', 'no_ktp', 'passport_id', 'bod', 'process']
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
                'bod': ['bod', 'birth_date', 'birthdate', 'date_of_birth', 'dob', 'tanggal_lahir', 'tgl_lahir'],
                'process': ['process', 'proses', 'flag', 'allow', 'enable']
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
            
            # REMOVED: Duplicate KTP checking disabled
            # User wants ALL data processed regardless of duplicates
            # Allow duplicate KTP numbers (including '9999999999999999999999', '-', etc.)
            # if 'no_ktp' in df.columns:
            #     duplicate_ktps = df[df.duplicated(subset=['no_ktp'], keep=False)]['no_ktp'].unique()
            #     if False:  # DISABLED: duplicate checking
            #         return {
            #             'valid': False,
            #             'success': False,
            #             'error': f"Duplicate No_KTP found in file: {', '.join(map(str, duplicate_ktps))}",
            #             'filename': filename,
            #             'duplicate_ktps': list(duplicate_ktps)
            #         }
            
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
        """Process each row from the file with comprehensive validation"""
        try:
            processing_summary = {
                'success': True,
                'filename': filename,
                'total_rows': len(df),
                'processed': 0,
                'successful': 0,
                'skipped': 0,
                'errors': [],
                'created_gids': [],
                'validation_report': None
            }
            
            logger.info(f"🚀 Starting validation and processing for {len(df)} rows...")
            
            # First, convert DataFrame to list of dictionaries for validation
            records_for_validation = []
            for row_idx in range(len(df)):
                row = df.iloc[row_idx]
                raw_data = {
                    'name': row.get('name'),
                    'personal_number': row.get('personal_number'),
                    'no_ktp': row.get('no_ktp'),
                    'passport_id': row.get('passport_id'),
                    'bod': row.get('bod'),
                    'process': row.get('process')
                }
                
                # Clean the data
                cleaned_data = self._clean_row_data(raw_data, row_idx + 2)
                if cleaned_data['valid']:
                    records_for_validation.append(cleaned_data)
                else:
                    processing_summary['errors'].append(cleaned_data['error'])
                    processing_summary['skipped'] += 1
            
            # Perform batch validation
            validation_results = self.validation_service.validate_batch(records_for_validation)
            
            # Create validation report
            processing_summary['validation_report'] = self.validation_service.create_validation_report(
                validation_results, filename
            )
            
            # Log validation summary
            logger.info(f"Validation complete: {validation_results['validation_summary']['valid_count']} valid, "
                       f"{validation_results['validation_summary']['invalid_count']} invalid records")
            
            # Process valid records
            valid_records = []
            reactivated_records = []
            
            for valid_record in validation_results['valid_records']:
                row_num = valid_record['row_number'] + 1  # Adjust for header row
                row_data = valid_record['data']
                processing_summary['processed'] += 1
                
                try:
                    # Check for existing record in global_id table (employee data)
                    existing_global = self._find_existing_record(row_data)
                    
                    if existing_global:
                        # Found existing G_ID - reuse it and add/update in global_id_non_database
                        existing_g_id = existing_global.g_id
                        
                        # Check if already exists in global_id_non_database table
                        existing_non_db = self.db.query(GlobalIDNonDatabase).filter(
                            GlobalIDNonDatabase.g_id == existing_g_id
                        ).first()
                        
                        if existing_non_db:
                            # Update existing record in global_id_non_database
                            if existing_non_db.status != "Active":
                                # Reactivate the record
                                existing_non_db.status = "Active"
                                existing_non_db.updated_at = datetime.now()
                                existing_non_db.name = row_data['name']
                                existing_non_db.personal_number = row_data.get('personal_number')
                                existing_non_db.no_ktp = row_data.get('no_ktp')
                                existing_non_db.passport_id = row_data.get('passport_id')
                                existing_non_db.bod = row_data.get('bod')
                                
                                # Also reactivate in global_id table if needed
                                if existing_global.status != "Active":
                                    existing_global.status = "Active"
                                    existing_global.updated_at = datetime.now()
                                
                                reactivated_records.append({
                                    'row_number': row_num,
                                    'gid': existing_g_id,
                                    'name': row_data['name'],
                                    'no_ktp': row_data.get('no_ktp'),
                                    'passport_id': row_data.get('passport_id'),
                                    'reactivated': True,
                                    'reason': 'Existing G_ID reused and reactivated in global_id_non_database'
                                })
                                processing_summary['successful'] += 1
                                logger.info(f"✅ Reactivated existing G_ID {existing_g_id} in global_id_non_database for {row_data['name']}")
                                continue
                            else:
                                # Already active - just update data if needed
                                existing_non_db.name = row_data['name']
                                existing_non_db.personal_number = row_data.get('personal_number')
                                existing_non_db.no_ktp = row_data.get('no_ktp')
                                existing_non_db.passport_id = row_data.get('passport_id')
                                existing_non_db.bod = row_data.get('bod')
                                existing_non_db.updated_at = datetime.now()
                                
                                reactivated_records.append({
                                    'row_number': row_num,
                                    'gid': existing_g_id,
                                    'name': row_data['name'],
                                    'no_ktp': row_data.get('no_ktp'),
                                    'passport_id': row_data.get('passport_id'),
                                    'reactivated': False,
                                    'reason': 'Existing G_ID reused and updated in global_id_non_database'
                                })
                                processing_summary['successful'] += 1
                                logger.info(f"✅ Updated existing G_ID {existing_g_id} in global_id_non_database for {row_data['name']}")
                                continue
                        else:
                            # Create new record in global_id_non_database with existing G_ID
                            new_non_db_record = GlobalIDNonDatabase(
                                g_id=existing_g_id,
                                name=row_data['name'],
                                personal_number=row_data.get('personal_number'),
                                no_ktp=row_data.get('no_ktp'),
                                passport_id=row_data.get('passport_id'),
                                bod=row_data.get('bod'),
                                status='Active',
                                source='excel',
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            
                            self.db.add(new_non_db_record)
                            
                            # Also ensure global_id record is active
                            if existing_global.status != "Active":
                                existing_global.status = "Active"
                                existing_global.updated_at = datetime.now()
                            
                            reactivated_records.append({
                                'row_number': row_num,
                                'gid': existing_g_id,
                                'name': row_data['name'],
                                'no_ktp': row_data.get('no_ktp'),
                                'passport_id': row_data.get('passport_id'),
                                'reactivated': False,
                                'reason': 'Existing G_ID reused and added to global_id_non_database'
                            })
                            processing_summary['successful'] += 1
                            logger.info(f"✅ Reused existing G_ID {existing_g_id} and added to global_id_non_database for {row_data['name']}")
                            continue
                    
                    # No existing G_ID found - create new record (original logic)
                    valid_records.append((row_num, row_data))
                    
                except Exception as e:
                    processing_summary['errors'].append(f"Row {row_num}: {str(e)}")
                    logger.error(f"Error processing existing record check for row {row_num}: {str(e)}")
                    processing_summary['skipped'] += 1
            
            # Add validation errors to processing summary
            for invalid_record in validation_results['invalid_records']:
                row_num = invalid_record['row_number'] + 1  # Adjust for header row
                for error in invalid_record['errors']:
                    processing_summary['errors'].append(f"Row {row_num}: {error}")
                processing_summary['skipped'] += 1

            # BATCH G_ID GENERATION: Generate all G_IDs at once for new valid records
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

            # NEW: Handle status changes based on upload content
            # Process status changes for existing excel-sourced records
            all_processed_data = []
            for valid_record in validation_results['valid_records']:
                all_processed_data.append(valid_record['data'])
            
            if all_processed_data:
                logger.info(f"🔄 Processing status changes for existing records based on upload...")
                status_result = self.handle_upload_status_changes(all_processed_data, filename)
                if status_result['success']:
                    processing_summary['status_changes'] = {
                        'reactivated': status_result['reactivated_count'],
                        'deactivated': status_result['deactivated_count'],
                        'details': status_result['status_changes']
                    }
                    logger.info(f"✅ Status changes: {status_result['reactivated_count']} reactivated, {status_result['deactivated_count']} deactivated")
                else:
                    processing_summary['errors'].append(f"Status change processing failed: {status_result.get('error', 'Unknown error')}")

            # Commit all changes together
            try:
                self.db.commit()
                logger.info("✅ All changes committed successfully")
            except Exception as commit_error:
                self.db.rollback()
                logger.error(f"❌ Failed to commit changes: {str(commit_error)}")
                processing_summary['errors'].append(f"Failed to save changes: {str(commit_error)}")
                processing_summary['success'] = False            # Final success determination
            if processing_summary['successful'] == 0 and processing_summary['errors']:
                processing_summary['success'] = False
                processing_summary['error'] = "No records were successfully processed"
            
            # Add summary message
            total_processed = processing_summary['successful']
            total_skipped = processing_summary['skipped']
            
            processing_summary['summary_message'] = (
                f"Processing complete for {filename}:\n"
                f"✅ Successfully processed: {total_processed} records\n"
                f"❌ Skipped/Invalid: {total_skipped} records\n"
                f"📊 Success rate: {(total_processed / len(df) * 100):.1f}%"
            )
            
            return processing_summary
            
        except Exception as e:
            logger.error(f"Error processing Excel rows: {str(e)}")
            return {
                'success': False,
                'error': f"Error processing Excel rows: {str(e)}",
                'filename': filename
            }
    
    def _find_existing_record(self, row_data: Dict[str, Any]) -> Optional[GlobalID]:
        """
        Find existing record based on available identifiers.
        IMPROVED LOGIC: Handle exact matching for G_ID reuse from global_id table (employee data)
        """
        
        # Debug logging to understand the matching process
        logger.info(f"🔍 Searching for existing record for: {row_data.get('name')} | KTP: {row_data.get('no_ktp')} | BOD: {row_data.get('bod')}")
        
        # STRATEGY 1: Exact match on name + no_ktp + bod (most precise)
        if row_data.get('name') and row_data.get('no_ktp') and row_data.get('bod'):
            exact_match = self.db.query(GlobalID).filter(
                and_(
                    GlobalID.name == row_data['name'],
                    GlobalID.no_ktp == row_data['no_ktp'],
                    GlobalID.bod == row_data['bod']
                )
            ).first()
            
            if exact_match:
                logger.info(f"✅ EXACT MATCH found! G_ID {exact_match.g_id} | Name: {exact_match.name} | KTP: {exact_match.no_ktp} | BOD: {exact_match.bod}")
                return exact_match
        
        # STRATEGY 2: Match on name + no_ktp (ignore BOD for flexibility)
        if row_data.get('name') and row_data.get('no_ktp'):
            name_ktp_match = self.db.query(GlobalID).filter(
                and_(
                    GlobalID.name == row_data['name'],
                    GlobalID.no_ktp == row_data['no_ktp']
                )
            ).first()
            
            if name_ktp_match:
                logger.info(f"✅ NAME+KTP MATCH found! G_ID {name_ktp_match.g_id} | Name: {name_ktp_match.name} | KTP: {name_ktp_match.no_ktp}")
                logger.info(f"   Database BOD: {name_ktp_match.bod} | Upload BOD: {row_data.get('bod')}")
                return name_ktp_match
        
        # STRATEGY 3: Match only on no_ktp (unique identifier)
        if row_data.get('no_ktp'):
            ktp_match = self.db.query(GlobalID).filter(
                GlobalID.no_ktp == row_data['no_ktp']
            ).first()
            
            if ktp_match:
                logger.info(f"✅ KTP-ONLY MATCH found! G_ID {ktp_match.g_id} | Name: {ktp_match.name} | KTP: {ktp_match.no_ktp}")
                logger.info(f"   Database Name: '{ktp_match.name}' | Upload Name: '{row_data.get('name')}'")
                logger.info(f"   Database BOD: {ktp_match.bod} | Upload BOD: {row_data.get('bod')}")
                return ktp_match
        
        # STRATEGY 4: Match on name + passport_id if no KTP
        if row_data.get('name') and row_data.get('passport_id') and not row_data.get('no_ktp'):
            passport_match = self.db.query(GlobalID).filter(
                and_(
                    GlobalID.name == row_data['name'],
                    GlobalID.passport_id == row_data['passport_id']
                )
            ).first()
            
            if passport_match:
                logger.info(f"✅ NAME+PASSPORT MATCH found! G_ID {passport_match.g_id} | Name: {passport_match.name} | Passport: {passport_match.passport_id}")
                return passport_match
        
        # STRATEGY 5: Debug - show what records exist with similar names or KTPs
        if row_data.get('name'):
            similar_names = self.db.query(GlobalID).filter(
                GlobalID.name.ilike(f"%{row_data['name']}%")
            ).limit(3).all()
            
            if similar_names:
                logger.info(f"🔍 Found {len(similar_names)} similar name(s) in database:")
                for similar in similar_names:
                    logger.info(f"   G_ID: {similar.g_id} | Name: '{similar.name}' | KTP: {similar.no_ktp} | BOD: {similar.bod}")
        
        if row_data.get('no_ktp'):
            similar_ktps = self.db.query(GlobalID).filter(
                GlobalID.no_ktp == row_data['no_ktp']
            ).limit(3).all()
            
            if similar_ktps:
                logger.info(f"🔍 Found {len(similar_ktps)} record(s) with same KTP:")
                for similar in similar_ktps:
                    logger.info(f"   G_ID: {similar.g_id} | Name: '{similar.name}' | KTP: {similar.no_ktp} | BOD: {similar.bod}")
        
        logger.info(f"❌ NO MATCHING RECORD found for: {row_data.get('name')} | KTP: {row_data.get('no_ktp')}")
        return None
    
    def _validate_and_clean_row(self, row: pd.Series, row_number: int) -> Dict[str, Any]:
        """Validate and clean individual row data using the new validation service"""
        try:
            # Extract raw data from the row
            raw_data = {
                'name': row.get('name'),
                'personal_number': row.get('personal_number'),
                'no_ktp': row.get('no_ktp'),
                'passport_id': row.get('passport_id'),
                'bod': row.get('bod'),
                'process': row.get('process')  # Include process column for KTP validation
            }
            
            # Clean the data first
            cleaned_data = self._clean_row_data(raw_data, row_number)
            if not cleaned_data['valid']:
                return cleaned_data
            
            # Use validation service for comprehensive validation
            validation_result = self.validation_service.validate_record(cleaned_data, row_number)
            
            if validation_result['valid']:
                return {
                    'valid': True,
                    **validation_result['processed_data']
                }
            else:
                return {
                    'valid': False,
                    'error': ' | '.join(validation_result['errors'])
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f"Row {row_number}: Error validating data - {str(e)}"
            }
    
    def _clean_row_data(self, raw_data: Dict[str, Any], row_number: int) -> Dict[str, Any]:
        """Clean and normalize raw row data"""
        try:
            # Clean name
            name = str(raw_data.get('name', '')).strip() if pd.notna(raw_data.get('name')) else ''
            if not name or name.lower() in ['nan', 'null', '']:
                return {
                    'valid': False,
                    'error': f"Row {row_number}: Name is required"
                }
            
            # Clean personal_number
            personal_number = str(raw_data.get('personal_number', '')).strip() if pd.notna(raw_data.get('personal_number')) else ''
            if personal_number.lower() in ['nan', 'null', '', '0']:
                personal_number = None
            
            # Clean no_ktp
            no_ktp = str(raw_data.get('no_ktp', '')).strip() if pd.notna(raw_data.get('no_ktp')) else ''
            if no_ktp.lower() in ['nan', 'null', '', '0']:
                no_ktp = None
            
            # Clean passport_id
            passport_id = str(raw_data.get('passport_id', '')).strip() if pd.notna(raw_data.get('passport_id')) else ''
            if passport_id.lower() in ['nan', 'null', '', '0']:
                passport_id = None
            
            # Clean process column
            process = str(raw_data.get('process', '')).strip() if pd.notna(raw_data.get('process')) else ''
            if process.lower() in ['nan', 'null', '']:
                process = None
            
            # Handle BOD (Birth of Date)
            bod = None
            if pd.notna(raw_data.get('bod')):
                if isinstance(raw_data['bod'], str):
                    try:
                        bod = pd.to_datetime(raw_data['bod']).date()
                    except:
                        return {
                            'valid': False,
                            'error': f"Row {row_number}: Invalid date format for BOD. Use YYYY-MM-DD"
                        }
                else:
                    try:
                        bod = pd.to_datetime(raw_data['bod']).date()
                    except:
                        bod = None
            
            return {
                'valid': True,
                'name': name[:255],  # Limit to 255 chars
                'personal_number': personal_number,
                'no_ktp': no_ktp,
                'passport_id': passport_id,
                'bod': bod,
                'process': process
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Row {row_number}: Error cleaning data - {str(e)}"
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
                        no_ktp=row_data['no_ktp'],
                        passport_id=row_data.get('passport_id'),  # Include passport_id in global_id
                        bod=row_data.get('bod'),
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
                        no_ktp=row_data['no_ktp'],
                        passport_id=row_data.get('passport_id'),  # Use actual passport_id value
                        bod=row_data.get('bod'),
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
                        'no_ktp': row_data['no_ktp']
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
    
    def handle_upload_status_changes(self, uploaded_data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Handle status changes based on upload data:
        - Records in upload: remain/become active
        - Records not in upload: become non-active
        """
        try:
            logger.info(f"🔄 Processing status changes based on upload: {filename}")
            
            # Create set of identifiers from uploaded data for comparison
            uploaded_identifiers = set()
            for row_data in uploaded_data:
                # Create identifier based on available data
                if row_data.get('no_ktp'):
                    uploaded_identifiers.add(('ktp', row_data['no_ktp']))
                elif row_data.get('passport_id'):
                    uploaded_identifiers.add(('passport', row_data['passport_id']))
                
                # Also add name-based identifier as fallback
                if row_data.get('name'):
                    uploaded_identifiers.add(('name', row_data['name']))
            
            # Get all records from global_id_non_database that were from excel source
            existing_excel_records = self.db.query(GlobalIDNonDatabase).filter(
                GlobalIDNonDatabase.source == 'excel'
            ).all()
            
            deactivated_count = 0
            reactivated_count = 0
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
                    record.status = 'Active'
                    record.updated_at = datetime.now()
                    
                    # Also reactivate in global_id table
                    global_record = self.db.query(GlobalID).filter(
                        GlobalID.g_id == record.g_id
                    ).first()
                    if global_record and global_record.status != 'Active':
                        global_record.status = 'Active'
                        global_record.updated_at = datetime.now()
                    
                    reactivated_count += 1
                    status_changes.append({
                        'g_id': record.g_id,
                        'name': record.name,
                        'action': 'reactivated',
                        'reason': 'Found in current upload'
                    })
                    logger.info(f"✅ Reactivated G_ID {record.g_id} for {record.name}")
                
                elif not has_match and record.status == 'Active':
                    # Record not found in upload - deactivate
                    record.status = 'Non Active'
                    record.updated_at = datetime.now()
                    
                    # Also deactivate in global_id table if it's from excel source
                    global_record = self.db.query(GlobalID).filter(
                        and_(
                            GlobalID.g_id == record.g_id,
                            GlobalID.source == 'excel'
                        )
                    ).first()
                    if global_record and global_record.status == 'Active':
                        global_record.status = 'Non Active'
                        global_record.updated_at = datetime.now()
                    
                    deactivated_count += 1
                    status_changes.append({
                        'g_id': record.g_id,
                        'name': record.name,
                        'action': 'deactivated',
                        'reason': 'Not found in current upload'
                    })
                    logger.info(f"⛔ Deactivated G_ID {record.g_id} for {record.name}")
            
            # Commit status changes
            if status_changes:
                self.db.commit()
                logger.info(f"✅ Status changes committed: {reactivated_count} reactivated, {deactivated_count} deactivated")
            
            return {
                'success': True,
                'reactivated_count': reactivated_count,
                'deactivated_count': deactivated_count,
                'status_changes': status_changes,
                'total_processed': len(existing_excel_records)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error handling status changes: {str(e)}")
            return {
                'success': False,
                'error': f"Status change processing failed: {str(e)}",
                'reactivated_count': 0,
                'deactivated_count': 0,
                'status_changes': []
            }
    
    def reactivate_by_explore_data(self, explore_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reactivate records when data is added via explore page with exact matching content
        """
        try:
            logger.info(f"🔍 Checking for reactivation via explore data: {explore_data.get('name', 'Unknown')}")
            
            # Find matching records in both tables that are Non Active
            matching_records = []
            
            # Search in global_id table
            global_filters = []
            if explore_data.get('name'):
                global_filters.append(GlobalID.name == explore_data['name'])
            if explore_data.get('no_ktp'):
                global_filters.append(GlobalID.no_ktp == explore_data['no_ktp'])
            if explore_data.get('passport_id'):
                global_filters.append(GlobalID.passport_id == explore_data['passport_id'])
            if explore_data.get('bod'):
                global_filters.append(GlobalID.bod == explore_data['bod'])
            
            if global_filters:
                global_records = self.db.query(GlobalID).filter(
                    and_(
                        *global_filters,
                        GlobalID.status == 'Non Active'
                    )
                ).all()
                
                matching_records.extend(global_records)
            
            reactivated_count = 0
            reactivated_gids = []
            
            for record in matching_records:
                # Reactivate the record
                record.status = 'Active'
                record.updated_at = datetime.now()
                
                # Also reactivate corresponding record in global_id_non_database if exists
                non_db_record = self.db.query(GlobalIDNonDatabase).filter(
                    GlobalIDNonDatabase.g_id == record.g_id
                ).first()
                if non_db_record and non_db_record.status == 'Non Active':
                    non_db_record.status = 'Active'
                    non_db_record.updated_at = datetime.now()
                
                reactivated_count += 1
                reactivated_gids.append({
                    'g_id': record.g_id,
                    'name': record.name,
                    'reason': 'Reactivated via explore page data match'
                })
                logger.info(f"✅ Reactivated G_ID {record.g_id} via explore page for {record.name}")
            
            # Commit changes
            if reactivated_count > 0:
                self.db.commit()
                logger.info(f"✅ Reactivated {reactivated_count} records via explore page")
            
            return {
                'success': True,
                'reactivated_count': reactivated_count,
                'reactivated_gids': reactivated_gids
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reactivating via explore data: {str(e)}")
            return {
                'success': False,
                'error': f"Explore reactivation failed: {str(e)}",
                'reactivated_count': 0
            }
    
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
                    'description': 'Indonesian ID number (any format)',
                    'type': 'Text (any length)',
                    'required': False,
                    'format': 'Any format accepted',
                    'example': '3201234567890001 or 640.303.261.072.0002'
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
                'no_ktp can be any format and length (optional)',
                'name is required and cannot be empty',
                'Date format for bod must be YYYY-MM-DD',
                'personal_number and passport_id are optional',
                'CSV files support both comma (,) and semicolon (;) separators',
                'Multiple text encodings are automatically detected',
                'Remove any "process" column if copying from dummy data',
                '🔄 System automatically reuses existing G_IDs for matching data',
                '⚡ Status management: Active for data in uploads, Non-Active for missing data'
            ]
        }
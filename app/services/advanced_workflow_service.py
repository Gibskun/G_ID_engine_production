"""
Advanced Workflow Service for Global ID System
Handles comprehensive data processing, validation, and synchronization workflows
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, text
import pandas as pd
from io import BytesIO
import hashlib

from app.models.models import (
    GlobalID, 
    GlobalIDNonDatabase, 
    Pegawai, 
    AuditLog
)
from app.services.gid_generator import GIDGenerator
from app.services.excel_service import ExcelIngestionService

logger = logging.getLogger(__name__)


class AdvancedWorkflowService:
    """
    Advanced workflow service implementing comprehensive data processing and synchronization
    following the specified business rules and workflow requirements
    """
    
    def __init__(self, main_db: Session, source_db: Optional[Session] = None):
        self.main_db = main_db
        self.source_db = source_db
        self.gid_generator = GIDGenerator(main_db)
        self.excel_service = ExcelIngestionService(main_db)
    
    def process_file_with_advanced_workflow(
        self, 
        file_content: bytes, 
        filename: str,
        enable_deactivation: bool = True
    ) -> Dict[str, Any]:
        """
        Advanced file processing with complete workflow implementation
        
        Args:
            file_content: Binary content of the file
            filename: Name of the uploaded file
            enable_deactivation: Whether to deactivate missing records
            
        Returns:
            Comprehensive processing results
        """
        try:
            logger.info(f"Starting advanced workflow processing: {filename}")
            
            # Phase 1: File Reading and Validation
            df = self._read_and_validate_file(file_content, filename)
            if df is None:
                return self._create_error_response("Failed to read file")
            
            # Phase 2: Data Validation and Structure Check
            validation_result = self._validate_data_structure(df)
            if not validation_result['valid']:
                return self._create_error_response(
                    f"Data validation failed: {validation_result['error']}"
                )
            
            # Phase 3: Process New Data Ingestion
            ingestion_result = self._process_data_ingestion(df, filename)
            
            # Phase 4: Deactivation Process (if enabled)
            deactivation_result = {}
            if enable_deactivation:
                deactivation_result = self._process_deactivation_workflow(df)
            
            # Phase 5: Compile Final Results
            return self._compile_workflow_results(
                ingestion_result, 
                deactivation_result, 
                filename
            )
            
        except Exception as e:
            logger.error(f"Error in advanced workflow processing: {str(e)}")
            return self._create_error_response(f"Workflow processing failed: {str(e)}")
    
    def _read_and_validate_file(self, file_content: bytes, filename: str) -> Optional[pd.DataFrame]:
        """Read file content and return DataFrame"""
        try:
            file_ext = filename.lower().split('.')[-1]
            
            if file_ext in ['xlsx', 'xls']:
                return pd.read_excel(BytesIO(file_content))
            elif file_ext == 'csv':
                # Try multiple encodings for CSV
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        content_str = file_content.decode(encoding)
                        return pd.read_csv(BytesIO(content_str.encode('utf-8')))
                    except UnicodeDecodeError:
                        continue
                raise ValueError("Unable to decode CSV file with supported encodings")
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            return None
    
    def _validate_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate that DataFrame has required columns and data"""
        required_columns = ['name', 'personal_number', 'no_ktp', 'bod']
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                'valid': False,
                'error': f"Missing required columns: {missing_columns}"
            }
        
        # Check for empty data
        if df.empty:
            return {
                'valid': False,
                'error': "File contains no data rows"
            }
        
        # Validate data types and formats
        validation_errors = []
        
        for idx, row in df.iterrows():
            row_num = (idx if isinstance(idx, int) else 0) + 2  # Excel row number (1-indexed + header)
            
            # Validate name
            if pd.isna(row['name']) or str(row['name']).strip() == '':
                validation_errors.append(f"Row {row_num}: Name is required")
            
            # NEW VALIDATION LOGIC: Both no_ktp and passport_id can be empty
            no_ktp_value = str(row['no_ktp']).strip() if pd.notna(row['no_ktp']) else ""
            passport_id_value = str(row['passport_id']).strip() if pd.notna(row.get('passport_id', '')) else ""
            
            # Both fields can be empty - no validation required for identifiers
            
            # Validate no_ktp format if provided
            if no_ktp_value and len(no_ktp_value) != 16:
                validation_errors.append(f"Row {row_num}: No_KTP must be exactly 16 characters")
            
            # Validate passport_id format if provided
            if passport_id_value and (len(passport_id_value) < 8 or len(passport_id_value) > 9):
                validation_errors.append(f"Row {row_num}: Passport_ID must be 8-9 characters long")
            
            # Validate date of birth
            if pd.isna(row['bod']):
                validation_errors.append(f"Row {row_num}: Date of Birth is required")
            else:
                try:
                    if isinstance(row['bod'], str):
                        pd.to_datetime(row['bod'])
                except ValueError:
                    validation_errors.append(f"Row {row_num}: Invalid Date of Birth format")
        
        if validation_errors:
            return {
                'valid': False,
                'error': f"Data validation errors: {'; '.join(validation_errors[:5])}"  # Show first 5 errors
            }
        
        return {'valid': True}
    
    def _process_data_ingestion(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Process new data ingestion following the workflow rules"""
        result = {
            'processed': 0,
            'successful': 0,
            'skipped': 0,
            'errors': [],
            'created_gids': []
        }
        
        for idx, row in df.iterrows():
            row_num = (idx if isinstance(idx, int) else 0) + 2
            result['processed'] += 1
            
            try:
                # Clean and prepare data
                clean_data = self._clean_row_data(row)
                
                # Check if record already exists in global_id table
                existing_record = self.main_db.query(GlobalID).filter(
                    GlobalID.no_ktp == clean_data['no_ktp']
                ).first()
                
                if existing_record:
                    result['skipped'] += 1
                    result['errors'].append(
                        f"Row {row_num}: No_KTP {clean_data['no_ktp']} already exists (G_ID: {existing_record.g_id})"
                    )
                    logger.warning(f"Skipping duplicate No_KTP: {clean_data['no_ktp']}")
                    continue
                
                # Generate new G_ID
                new_gid = self.gid_generator.generate_next_gid()
                
                # Create record in global_id table
                global_record = GlobalID(
                    g_id=new_gid,
                    name=clean_data['name'],
                    personal_number=clean_data['personal_number'],
                    no_ktp=clean_data['no_ktp'],
                    passport_id=clean_data.get('passport_id', ''),
                    bod=clean_data['bod'],
                    status='Active',
                    source='excel'
                )
                
                # Create record in global_id_non_database table (log table)
                log_record = GlobalIDNonDatabase(
                    g_id=new_gid,
                    name=clean_data['name'],
                    personal_number=clean_data['personal_number'],
                    no_ktp=clean_data['no_ktp'],
                    passport_id=clean_data.get('passport_id', ''),
                    bod=clean_data['bod'],
                    status='Active',
                    source='excel'
                )
                
                # Add records to session
                self.main_db.add(global_record)
                self.main_db.add(log_record)
                
                # Commit changes
                self.main_db.commit()
                
                # Log audit trail
                self._log_audit(
                    table_name='global_id',
                    record_id=new_gid,
                    action='CREATE',
                    old_values=None,
                    new_values=clean_data,
                    reason=f'File ingestion from {filename}'
                )
                
                result['successful'] += 1
                result['created_gids'].append({
                    'gid': new_gid,
                    'name': clean_data['name'],
                    'no_ktp': clean_data['no_ktp']
                })
                
                logger.info(f"Successfully created G_ID {new_gid} for {clean_data['name']}")
                
            except Exception as e:
                result['errors'].append(f"Row {row_num}: {str(e)}")
                logger.error(f"Error processing row {row_num}: {str(e)}")
                self.main_db.rollback()
        
        return result
    
    def _process_deactivation_workflow(self, current_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process deactivation workflow by comparing current file data 
        with existing records in global_id_non_database
        """
        result = {
            'deactivated_count': 0,
            'deactivated_records': [],
            'errors': []
        }
        
        try:
            # Get current file data as a set of unique identifiers
            current_records = set()
            for _, row in current_df.iterrows():
                # Create unique identifier using name, personal_number, and bod
                identifier = self._create_record_identifier(
                    name=str(row['name']).strip(),
                    personal_number=str(row.get('personal_number', '')).strip(),
                    bod=str(row['bod'])
                )
                current_records.add(identifier)
            
            # Get all active records from global_id_non_database (Excel source)
            existing_excel_records = self.main_db.query(GlobalIDNonDatabase).filter(
                and_(
                    GlobalIDNonDatabase.source == 'excel',
                    GlobalIDNonDatabase.status == 'Active'
                )
            ).all()
            
            # Check each existing record against current file data
            for record in existing_excel_records:
                record_identifier = self._create_record_identifier(
                    name=getattr(record, 'name', '') or '',
                    personal_number=getattr(record, 'personal_number', '') or '',
                    bod=str(getattr(record, 'bod', '')) if getattr(record, 'bod') else ''
                )
                
                # If record is not in current file, deactivate it
                if record_identifier not in current_records:
                    try:
                        # Update status in global_id_non_database
                        setattr(record, 'status', 'Non Active')
                        
                        # Update corresponding record in global_id table
                        global_record = self.main_db.query(GlobalID).filter(
                            GlobalID.g_id == record.g_id
                        ).first()
                        
                        if global_record:
                            old_values = {
                                'status': getattr(global_record, 'status', '')
                            }
                            setattr(global_record, 'status', 'Non Active')
                            
                            # Log audit trail
                            self._log_audit(
                                table_name='global_id',
                                record_id=str(getattr(record, 'g_id', '')),
                                action='UPDATE',
                                old_values=old_values,
                                new_values={'status': 'Non Active'},
                                reason='Deactivated - not found in latest file upload'
                            )
                        
                        self.main_db.commit()
                        
                        result['deactivated_count'] += 1
                        result['deactivated_records'].append({
                            'g_id': getattr(record, 'g_id', ''),
                            'name': getattr(record, 'name', ''),
                            'no_ktp': getattr(record, 'no_ktp', ''),
                            'reason': 'Not found in latest file upload'
                        })
                        
                        logger.info(f"Deactivated record G_ID: {getattr(record, 'g_id', '')} - {getattr(record, 'name', '')}")
                        
                    except Exception as e:
                        result['errors'].append(f"Error deactivating G_ID {getattr(record, 'g_id', '')}: {str(e)}")
                        self.main_db.rollback()
            
        except Exception as e:
            logger.error(f"Error in deactivation workflow: {str(e)}")
            result['errors'].append(f"Deactivation workflow error: {str(e)}")
        
        return result
    
    def pegawai_db_synchronization_workflow(self) -> Dict[str, Any]:
        """
        Advanced synchronization workflow with consolidated g_id database following business rules
        """
        if not self.source_db:
            return self._create_error_response("Source database connection not available")
        
        result = {
            'status_updates': 0,
            'deletions': 0,
            'updated_records': [],
            'deleted_records': [],
            'errors': []
        }
        
        try:
            # Get all records from global_id that have database_pegawai source
            global_records = self.main_db.query(GlobalID).filter(
                GlobalID.source == 'database_pegawai'
            ).all()
            
            for global_record in global_records:
                try:
                    # Find corresponding record in pegawai table
                    pegawai_record = self.source_db.query(Pegawai).filter(
                        Pegawai.no_ktp == getattr(global_record, 'no_ktp')
                    ).first()
                    
                    if not pegawai_record:
                        # Rule: If employee record is deleted from pegawai table, delete from global_id
                        old_values = {
                            'g_id': getattr(global_record, 'g_id', ''),
                            'name': getattr(global_record, 'name', ''),
                            'no_ktp': getattr(global_record, 'no_ktp', ''),
                            'status': getattr(global_record, 'status', '')
                        }
                        self.main_db.delete(global_record)
                        
                        # Log audit trail
                        self._log_audit(
                            table_name='global_id',
                            record_id=str(getattr(global_record, 'g_id', '')),
                            action='DELETE',
                            old_values=old_values,
                            new_values=None,
                            reason='Employee record deleted from pegawai table'
                        )
                        
                        result['deletions'] += 1
                        result['deleted_records'].append({
                            'g_id': getattr(global_record, 'g_id', ''),
                            'name': getattr(global_record, 'name', ''),
                            'no_ktp': getattr(global_record, 'no_ktp', ''),
                            'reason': 'Deleted from pegawai table'
                        })
                        
                        logger.info(f"Deleted G_ID {getattr(global_record, 'g_id', '')} - record not found in pegawai table")
                        
                    elif getattr(pegawai_record, 'deleted_at', None) is not None:
                        # Rule: If employee status is non-active, update to non-active
                        current_status = getattr(global_record, 'status', '')
                        old_values = {'status': current_status}  # Always define old_values
                        
                        if current_status != 'Non Active':
                            setattr(global_record, 'status', 'Non Active')
                            
                            # Log audit trail
                            self._log_audit(
                                table_name='global_id',
                                record_id=str(getattr(global_record, 'g_id', '')),
                                action='UPDATE',
                                old_values=old_values,
                                new_values={'status': 'Non Active'},
                                reason='Employee deactivated in pegawai table'
                            )
                            
                            result['status_updates'] += 1
                            
                        result['updated_records'].append({
                            'g_id': getattr(global_record, 'g_id', ''),
                            'name': getattr(global_record, 'name', ''),
                            'no_ktp': getattr(global_record, 'no_ktp', ''),
                            'old_status': old_values['status'],
                            'new_status': 'Non Active',
                            'reason': 'Employee deactivated in pegawai table'
                        })
                        
                        logger.info(f"Updated G_ID {getattr(global_record, 'g_id', '')} status to Non Active")                    # Additional rule: Reactivate if employee becomes active again
                    elif getattr(pegawai_record, 'deleted_at', None) is None and getattr(global_record, 'status', '') == 'Non Active':
                        current_status = getattr(global_record, 'status', '')
                        old_values = {'status': current_status}
                        setattr(global_record, 'status', 'Active')
                        
                        # Log audit trail
                        self._log_audit(
                            table_name='global_id',
                            record_id=str(getattr(global_record, 'g_id', '')),
                            action='UPDATE',
                            old_values=old_values,
                            new_values={'status': 'Active'},
                            reason='Employee reactivated in pegawai table'
                        )
                        
                        result['status_updates'] += 1
                        result['updated_records'].append({
                            'g_id': getattr(global_record, 'g_id', ''),
                            'name': getattr(global_record, 'name', ''),
                            'no_ktp': getattr(global_record, 'no_ktp', ''),
                            'old_status': old_values['status'],
                            'new_status': 'Active',
                            'reason': 'Employee reactivated in pegawai table'
                        })
                        
                        logger.info(f"Reactivated G_ID {getattr(global_record, 'g_id', '')}")
                    
                except Exception as e:
                    result['errors'].append(f"Error processing G_ID {getattr(global_record, 'g_id', '')}: {str(e)}")
                    logger.error(f"Error in pegawai sync for G_ID {getattr(global_record, 'g_id', '')}: {str(e)}")
                    self.main_db.rollback()
            
            # Commit all changes
            self.main_db.commit()
            
        except Exception as e:
            logger.error(f"Error in pegawai synchronization workflow: {str(e)}")
            result['errors'].append(f"Synchronization workflow error: {str(e)}")
            self.main_db.rollback()
        
        return result
    
    def _clean_row_data(self, row: pd.Series) -> Dict[str, Any]:
        """Clean and prepare row data for database insertion"""
        # Clean personal_number (handle empty strings and None)
        personal_number = row.get('personal_number')
        if pd.isna(personal_number) or str(personal_number).strip() == '':
            personal_number = None
        else:
            personal_number = str(personal_number).strip()
        
        # Parse date of birth
        bod = None
        if not pd.isna(row['bod']):
            if isinstance(row['bod'], str):
                try:
                    bod = pd.to_datetime(row['bod']).date()
                except ValueError:
                    raise ValueError(f"Invalid date format for BOD: {row['bod']}")
            elif hasattr(row['bod'], 'date'):
                bod = row['bod'].date()
            else:
                bod = row['bod']
        
        return {
            'name': str(row['name']).strip(),
            'personal_number': personal_number,
            'no_ktp': str(row['no_ktp']).strip(),
            'bod': bod
        }
    
    def _create_record_identifier(self, name: str, personal_number: str, bod: str) -> str:
        """Create a unique identifier for record comparison"""
        # Normalize data for comparison
        normalized = f"{name.lower().strip()}|{personal_number.lower().strip()}|{bod.strip()}"
        # Create hash to handle long identifiers efficiently
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _log_audit(
        self, 
        table_name: str, 
        record_id: str, 
        action: str,
        old_values: Optional[Dict], 
        new_values: Optional[Dict], 
        reason: Optional[str] = None
    ):
        """Log audit trail for workflow operations"""
        try:
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_by='advanced_workflow_system',
                change_reason=reason
            )
            self.main_db.add(audit_log)
            # Note: Don't commit here, let the caller handle commits
            
        except Exception as e:
            logger.error(f"Error logging audit: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }
    
    def _compile_workflow_results(
        self, 
        ingestion_result: Dict[str, Any], 
        deactivation_result: Dict[str, Any], 
        filename: str
    ) -> Dict[str, Any]:
        """Compile comprehensive workflow results"""
        return {
            'success': True,
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'ingestion': {
                'processed': ingestion_result.get('processed', 0),
                'successful': ingestion_result.get('successful', 0),
                'skipped': ingestion_result.get('skipped', 0),
                'created_gids': ingestion_result.get('created_gids', []),
                'errors': ingestion_result.get('errors', [])
            },
            'deactivation': {
                'deactivated_count': deactivation_result.get('deactivated_count', 0),
                'deactivated_records': deactivation_result.get('deactivated_records', []),
                'errors': deactivation_result.get('errors', [])
            },
            'summary': {
                'total_processed': ingestion_result.get('processed', 0),
                'total_successful': ingestion_result.get('successful', 0),
                'total_skipped': ingestion_result.get('skipped', 0),
                'total_deactivated': deactivation_result.get('deactivated_count', 0),
                'total_errors': len(ingestion_result.get('errors', [])) + len(deactivation_result.get('errors', []))
            }
        }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the workflow system"""
        try:
            # Get counts from various tables
            total_global_records = self.main_db.query(GlobalID).count()
            active_global_records = self.main_db.query(GlobalID).filter(GlobalID.status == 'Active').count()
            excel_records = self.main_db.query(GlobalID).filter(GlobalID.source == 'excel').count()
            db_records = self.main_db.query(GlobalID).filter(GlobalID.source == 'database_pegawai').count()
            log_records = self.main_db.query(GlobalIDNonDatabase).count()
            
            # Get recent audit logs
            recent_audits = self.main_db.query(AuditLog).order_by(
                AuditLog.created_at.desc()
            ).limit(10).all()
            
            return {
                'status': 'operational',
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'total_global_records': total_global_records,
                    'active_records': active_global_records,
                    'inactive_records': total_global_records - active_global_records,
                    'excel_source_records': excel_records,
                    'database_source_records': db_records,
                    'log_table_records': log_records
                },
                'recent_activities': [
                    {
                        'action': getattr(audit, 'action', ''),
                        'table': getattr(audit, 'table_name', ''),
                        'record_id': getattr(audit, 'record_id', ''),
                        'timestamp': getattr(audit, 'created_at').isoformat() if getattr(audit, 'created_at') else None,
                        'reason': getattr(audit, 'change_reason', '')
                    }
                    for audit in recent_audits
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
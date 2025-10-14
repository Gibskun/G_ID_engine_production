"""
Data Validation Service for Global ID Management System

This service implements comprehensive validation rules for:
- Name validation
- KTP (ID Number) validation with 16-character requirement and process column logic
- Passport ID validation with specific alphabet/numeric pattern requirements
- Process column validation
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
import pandas as pd

from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)


class DataValidationService:
    """Comprehensive data validation service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
    
    def validate_record(self, record_data: Dict[str, Any], row_number: int = None) -> Dict[str, Any]:
        """
        Validate a single record according to business rules
        
        Args:
            record_data: Dictionary containing record data
            row_number: Row number for error reporting
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'processed_data': record_data.copy()
        }
        
        row_prefix = f"Row {row_number}: " if row_number else ""
        
        # Check if validation is enabled
        if not self._is_validation_enabled():
            logger.info("Validation is disabled - accepting all records")
            return validation_result
        
        # 1. Name validation
        name_validation = self._validate_name(record_data.get('name'))
        if not name_validation['valid']:
            validation_result['valid'] = False
            validation_result['errors'].append(f"{row_prefix}{name_validation['error']}")
        
        # 2. KTP validation (if enabled)
        if self.config_service.get_bool_config('ktp_validation_enabled', True):
            ktp_validation = self._validate_ktp_with_process(
                record_data.get('no_ktp'),
                record_data.get('process')
            )
            if not ktp_validation['valid']:
                validation_result['valid'] = False
                validation_result['errors'].append(f"{row_prefix}{ktp_validation['error']}")
        
        # 3. Passport validation (if enabled)
        if self.config_service.get_bool_config('passport_validation_enabled', True):
            passport_validation = self._validate_passport_id(record_data.get('passport_id'))
            if not passport_validation['valid']:
                validation_result['valid'] = False
                validation_result['errors'].append(f"{row_prefix}{passport_validation['error']}")
        
        # 4. Check that at least one identifier (KTP or Passport) is provided and valid
        identifier_validation = self._validate_identifier_requirement(
            record_data.get('no_ktp'),
            record_data.get('passport_id'),
            record_data.get('process')
        )
        if not identifier_validation['valid']:
            validation_result['valid'] = False
            validation_result['errors'].append(f"{row_prefix}{identifier_validation['error']}")
        
        return validation_result
    
    def validate_batch(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of records
        
        Args:
            records: List of record dictionaries
            
        Returns:
            Dictionary with batch validation results
        """
        batch_result = {
            'total_records': len(records),
            'valid_records': [],
            'invalid_records': [],
            'validation_summary': {
                'valid_count': 0,
                'invalid_count': 0,
                'errors': [],
                'warnings': []
            }
        }
        
        for i, record in enumerate(records, 1):
            validation_result = self.validate_record(record, i)
            
            if validation_result['valid']:
                batch_result['valid_records'].append({
                    'row_number': i,
                    'data': validation_result['processed_data']
                })
                batch_result['validation_summary']['valid_count'] += 1
            else:
                batch_result['invalid_records'].append({
                    'row_number': i,
                    'data': record,
                    'errors': validation_result['errors']
                })
                batch_result['validation_summary']['invalid_count'] += 1
                batch_result['validation_summary']['errors'].extend(validation_result['errors'])
        
        return batch_result
    
    def _validate_name(self, name: Any) -> Dict[str, Any]:
        """Validate name field"""
        if not name or pd.isna(name) or not str(name).strip():
            return {
                'valid': False,
                'error': "Name is required and cannot be empty"
            }
        
        name_str = str(name).strip()
        
        if len(name_str) < 2:
            return {
                'valid': False,
                'error': "Name must be at least 2 characters long"
            }
        
        if len(name_str) > 255:
            return {
                'valid': False,
                'error': "Name cannot exceed 255 characters"
            }
        
        return {'valid': True}
    
    def _validate_ktp_with_process(self, no_ktp: Any, process: Any) -> Dict[str, Any]:
        """
        Validate KTP (ID Number) with process column logic
        
        Business Rules:
        1. If KTP is exactly 16 numeric characters: Always valid (process column ignored)
        2. If KTP is not 16 characters: Only valid if process column contains '1'
        3. If KTP is empty/null: Only valid if passport_id is provided and valid
        """
        # Handle empty/null KTP
        if not no_ktp or pd.isna(no_ktp) or str(no_ktp).strip() in ['', 'nan', 'NaN', 'NULL', 'null']:
            # Empty KTP is allowed if passport_id is valid - will be checked in identifier validation
            return {'valid': True}
        
        ktp_str = str(no_ktp).strip()
        
        # Remove any formatting (dots, spaces, hyphens)
        ktp_clean = re.sub(r'[.\s-]', '', ktp_str)
        
        # Check if KTP is numeric
        if not ktp_clean.isdigit():
            return {
                'valid': False,
                'error': f"KTP number '{ktp_str}' must contain only numeric characters"
            }
        
        # Check length and process column logic
        if len(ktp_clean) == 16:
            # Exactly 16 digits: Always valid regardless of process column
            return {'valid': True}
        else:
            # Not 16 digits: Check process column
            process_str = str(process).strip() if process and not pd.isna(process) else ""
            
            if process_str == '1':
                return {'valid': True}
            else:
                return {
                    'valid': False,
                    'error': f"KTP number '{ktp_str}' has {len(ktp_clean)} digits (not 16). Process column must contain '1' to allow processing, but found: '{process_str}'"
                }
    
    def _validate_passport_id(self, passport_id: Any) -> Dict[str, Any]:
        """
        Validate Passport ID with specific pattern requirements
        
        Business Rules:
        1. Must be 8 or 9 characters
        2. First character must be alphabetic
        3. Must contain both alphabetic and numeric characters
        4. Number of alphabetic characters must be less than numeric characters
        
        Valid examples: AB1234567 (9 chars), ABNC12345 (9 chars), B1234567 (8 chars), AB123456 (8 chars)
        Invalid examples: 12NC45632, IKJKL1234, A123456 (too short), ABC1234567 (too long)
        """
        # Handle empty/null passport
        if not passport_id or pd.isna(passport_id) or str(passport_id).strip() in ['', 'nan', 'NaN', 'NULL', 'null']:
            # Empty passport is allowed if KTP is valid - will be checked in identifier validation
            return {'valid': True}
        
        passport_str = str(passport_id).strip().upper()
        
        # Check length (accept 8 or 9 characters)
        if len(passport_str) not in [8, 9]:
            return {
                'valid': False,
                'error': f"Passport ID '{passport_id}' must be 8 or 9 characters, found {len(passport_str)} characters"
            }
        
        # Check first character is alphabetic
        if not passport_str[0].isalpha():
            return {
                'valid': False,
                'error': f"Passport ID '{passport_id}' must start with an alphabetic character, found: '{passport_str[0]}'"
            }
        
        # Count alphabetic and numeric characters
        alpha_count = sum(1 for c in passport_str if c.isalpha())
        numeric_count = sum(1 for c in passport_str if c.isdigit())
        
        # Check that all characters are alphanumeric
        if alpha_count + numeric_count != len(passport_str):
            return {
                'valid': False,
                'error': f"Passport ID '{passport_id}' must contain only alphabetic and numeric characters"
            }
        
        # Check that both types are present
        if alpha_count == 0:
            return {
                'valid': False,
                'error': f"Passport ID '{passport_id}' must contain at least one alphabetic character"
            }
        
        if numeric_count == 0:
            return {
                'valid': False,
                'error': f"Passport ID '{passport_id}' must contain at least one numeric character"
            }
        
        # Check that alphabetic count is less than numeric count
        if alpha_count >= numeric_count:
            return {
                'valid': False,
                'error': f"Passport ID '{passport_id}' must have fewer alphabetic characters ({alpha_count}) than numeric characters ({numeric_count})"
            }
        
        return {'valid': True}
    
    def _validate_identifier_requirement(self, no_ktp: Any, passport_id: Any, process: Any) -> Dict[str, Any]:
        """
        Validate that at least one valid identifier is provided
        
        Business Rules:
        - Data can be processed if either KTP OR Passport ID is valid
        - Both cannot be empty/invalid
        """
        # Check KTP validity
        ktp_valid = False
        if no_ktp and not pd.isna(no_ktp) and str(no_ktp).strip() not in ['', 'nan', 'NaN', 'NULL', 'null']:
            ktp_validation = self._validate_ktp_with_process(no_ktp, process)
            ktp_valid = ktp_validation['valid']
        
        # Check Passport validity
        passport_valid = False
        if passport_id and not pd.isna(passport_id) and str(passport_id).strip() not in ['', 'nan', 'NaN', 'NULL', 'null']:
            passport_validation = self._validate_passport_id(passport_id)
            passport_valid = passport_validation['valid']
        
        # At least one must be valid
        if not ktp_valid and not passport_valid:
            return {
                'valid': False,
                'error': "At least one valid identifier (KTP or Passport ID) must be provided"
            }
        
        return {'valid': True}
    
    def _is_validation_enabled(self) -> bool:
        """Check if validation is globally enabled"""
        # Check multiple config keys for validation enablement
        validation_enabled = self.config_service.get_bool_config('validation_enabled', True)
        skip_validation = self.config_service.get_bool_config('skip_validation', False)
        strict_validation = self.config_service.get_bool_config('strict_validation_enabled', True)
        
        # Validation is enabled if any of the enabling flags are true and skip is not true
        return (validation_enabled or strict_validation) and not skip_validation
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation configuration status"""
        return {
            'validation_enabled': self._is_validation_enabled(),
            'strict_validation_enabled': self.config_service.get_bool_config('strict_validation_enabled', True),
            'ktp_validation_enabled': self.config_service.get_bool_config('ktp_validation_enabled', True),
            'passport_validation_enabled': self.config_service.get_bool_config('passport_validation_enabled', True),
            'duplicate_checking': self.config_service.get_bool_config('duplicate_checking', True),
            'allow_duplicates': self.config_service.get_bool_config('allow_duplicates', False),
            'skip_validation': self.config_service.get_bool_config('skip_validation', False)
        }
    
    def create_validation_report(self, validation_results: Dict[str, Any], filename: str = None) -> str:
        """
        Create a human-readable validation report
        
        Args:
            validation_results: Results from validate_batch
            filename: Optional filename for the report
            
        Returns:
            Formatted validation report string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("DATA VALIDATION REPORT")
        report_lines.append("=" * 80)
        
        if filename:
            report_lines.append(f"File: {filename}")
            report_lines.append("-" * 80)
        
        summary = validation_results['validation_summary']
        report_lines.append(f"Total Records: {validation_results['total_records']}")
        report_lines.append(f"Valid Records: {summary['valid_count']}")
        report_lines.append(f"Invalid Records: {summary['invalid_count']}")
        report_lines.append(f"Success Rate: {(summary['valid_count'] / validation_results['total_records'] * 100):.1f}%")
        report_lines.append("")
        
        if validation_results['invalid_records']:
            report_lines.append("VALIDATION ERRORS:")
            report_lines.append("-" * 40)
            for invalid_record in validation_results['invalid_records']:
                report_lines.append(f"Row {invalid_record['row_number']}:")
                for error in invalid_record['errors']:
                    report_lines.append(f"  • {error}")
                report_lines.append("")
        
        if validation_results['valid_records']:
            report_lines.append("SUCCESSFULLY VALIDATED RECORDS:")
            report_lines.append("-" * 40)
            for valid_record in validation_results['valid_records'][:10]:  # Show first 10
                data = valid_record['data']
                report_lines.append(f"Row {valid_record['row_number']}: {data.get('name', 'N/A')} - KTP: {data.get('no_ktp', 'N/A')} - Passport: {data.get('passport_id', 'N/A')}")
            
            if len(validation_results['valid_records']) > 10:
                report_lines.append(f"... and {len(validation_results['valid_records']) - 10} more valid records")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)

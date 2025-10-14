"""
System Configuration Service for managing application settings
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.models import SystemConfig

logger = logging.getLogger(__name__)


class ConfigService:
    """Manages system configuration settings"""
    
    DEFAULT_CONFIGS = {
        'strict_validation_enabled': {
            'value': 'true',
            'description': 'Enable strict validation rules for ID numbers and passport IDs during Excel/CSV uploads'
        },
        'ktp_validation_enabled': {
            'value': 'true', 
            'description': 'Enable KTP number validation (16 digits, numeric only)'
        },
        'passport_validation_enabled': {
            'value': 'true',
            'description': 'Enable passport ID validation (9 chars, starts with letter, numbers dominate)'
        },
        'duplicate_checking': {
            'value': 'true',
            'description': 'Enable duplicate record checking'
        },
        'allow_duplicates': {
            'value': 'false',
            'description': 'Allow duplicate records to be processed'
        },
        'validation_enabled': {
            'value': 'true',
            'description': 'Master validation toggle'
        },
        'skip_validation': {
            'value': 'false',
            'description': 'Skip all validation checks'
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_default_configs()
    
    def _ensure_default_configs(self):
        """Ensure default configuration values exist in database"""
        try:
            for key, config in self.DEFAULT_CONFIGS.items():
                existing = self.db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
                if not existing:
                    new_config = SystemConfig(
                        config_key=key,
                        config_value=config['value'],
                        description=config['description']
                    )
                    self.db.add(new_config)
            
            self.db.commit()
            logger.info("Default configurations initialized")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error initializing default configs: {str(e)}")
    
    def get_config(self, key: str, default: str = None) -> str:
        """Get configuration value by key"""
        try:
            config = self.db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
            if config:
                return config.config_value
            return default or self.DEFAULT_CONFIGS.get(key, {}).get('value', 'false')
        except Exception as e:
            logger.error(f"Error getting config {key}: {str(e)}")
            return default or 'false'
    
    def set_config(self, key: str, value: str, description: str = None) -> bool:
        """Set configuration value"""
        try:
            config = self.db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
            
            if config:
                config.config_value = value
                if description:
                    config.description = description
            else:
                config = SystemConfig(
                    config_key=key,
                    config_value=value,
                    description=description or f"Configuration for {key}"
                )
                self.db.add(config)
            
            self.db.commit()
            logger.info(f"Configuration updated: {key} = {value}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting config {key}: {str(e)}")
            return False
    
    def get_bool_config(self, key: str, default: bool = False) -> bool:
        """Get configuration value as boolean"""
        value = self.get_config(key, str(default).lower())
        return value.lower() in ['true', '1', 'yes', 'on']
    
    def set_bool_config(self, key: str, value: bool, description: str = None) -> bool:
        """Set configuration value as boolean"""
        return self.set_config(key, str(value).lower(), description)
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        try:
            configs = self.db.query(SystemConfig).all()
            return {
                config.config_key: {
                    'value': config.config_value,
                    'description': config.description,
                    'updated_at': config.updated_at.isoformat() if config.updated_at else None
                }
                for config in configs
            }
        except Exception as e:
            logger.error(f"Error getting all configs: {str(e)}")
            return {}
    
    def is_strict_validation_enabled(self) -> bool:
        """Check if strict validation is enabled"""
        return self.get_bool_config('strict_validation_enabled', True)
    
    def is_ktp_validation_enabled(self) -> bool:
        """Check if KTP validation is enabled"""
        return self.get_bool_config('ktp_validation_enabled', True)
    
    def is_passport_validation_enabled(self) -> bool:
        """Check if passport validation is enabled"""
        return self.get_bool_config('passport_validation_enabled', True)
    
    def toggle_strict_validation(self) -> Dict[str, Any]:
        """Toggle strict validation and return new status"""
        current = self.is_strict_validation_enabled()
        new_value = not current
        
        success = self.set_bool_config('strict_validation_enabled', new_value)
        
        return {
            'success': success,
            'enabled': new_value,
            'message': f"Strict validation {'enabled' if new_value else 'disabled'}"
        }
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status"""
        return {
            'strict_validation_enabled': self.is_strict_validation_enabled(),
            'ktp_validation_enabled': self.is_ktp_validation_enabled(),
            'passport_validation_enabled': self.is_passport_validation_enabled()
        }
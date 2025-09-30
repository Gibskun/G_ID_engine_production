"""
Real-time monitoring service for pegawai table changes
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.database import get_db, get_source_db
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)


class RealtimeMonitorService:
    """
    Monitors pegawai table for changes and triggers synchronization
    Uses polling approach to detect changes
    """
    
    def __init__(self, poll_interval: int = 30):
        self.poll_interval = poll_interval  # seconds
        self.is_running = False
        self.last_check = None
        
    async def start_monitoring(self):
        """Start the real-time monitoring service"""
        logger.info("Starting real-time monitoring service...")
        self.is_running = True
        self.last_check = datetime.now()
        
        while self.is_running:
            try:
                await self._check_for_changes()
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.poll_interval)  # Continue after error
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        logger.info("Stopping real-time monitoring service...")
        self.is_running = False
    
    async def _check_for_changes(self):
        """Check for changes in the pegawai table"""
        try:
            # Get database sessions
            main_db = next(get_db())
            source_db = next(get_source_db())
            
            try:
                sync_service = SyncService(main_db, source_db)
                
                # Check for new records (without G_ID)
                new_records_result = sync_service.sync_new_records()
                
                if new_records_result['successful'] > 0:
                    logger.info(f"Synced {new_records_result['successful']} new records")
                
                # Check for deleted records (soft delete handling)
                deletion_result = sync_service.handle_deleted_records()
                
                if deletion_result['marked_inactive'] > 0:
                    logger.info(f"Marked {deletion_result['marked_inactive']} records as inactive")
                
                self.last_check = datetime.now()
                
            finally:
                main_db.close()
                source_db.close()
                
        except Exception as e:
            logger.error(f"Error checking for changes: {str(e)}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_running': self.is_running,
            'poll_interval': self.poll_interval,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'next_check': (self.last_check + timedelta(seconds=self.poll_interval)).isoformat() 
                         if self.last_check else None
        }


class DatabaseTriggerService:
    """
    Alternative approach using database triggers for real-time sync
    This creates triggers on the pegawai table to notify the application
    """
    
    def __init__(self):
        self.trigger_function_name = "notify_pegawai_changes"
        self.trigger_name = "pegawai_change_trigger"
    
    def create_notification_trigger(self, source_db: Session) -> bool:
        """Create database trigger for pegawai table changes - SQL Server implementation"""
        try:
            logger.warning("SQL Server does not support LISTEN/NOTIFY. Using polling-based monitoring instead.")
            # SQL Server doesn't support PostgreSQL-style LISTEN/NOTIFY
            # We would need to implement this using Service Broker or other mechanisms
            # For now, we'll use polling-based monitoring
            return True
            
        except Exception as e:
            logger.error(f"Error creating database trigger: {str(e)}")
            source_db.rollback()
            return False
    
    def remove_notification_trigger(self, source_db: Session) -> bool:
        """Remove database trigger - SQL Server implementation"""
        try:
            # SQL Server trigger removal would be different
            logger.info("SQL Server trigger cleanup - no action needed for polling-based monitoring")
            return True
            
        except Exception as e:
            logger.error(f"Error removing database trigger: {str(e)}")
            source_db.rollback()
            return False
    
    async def listen_for_notifications(self):
        """Polling-based monitoring for SQL Server (replacement for PostgreSQL LISTEN/NOTIFY)"""
        try:
            logger.info("Starting polling-based monitoring for SQL Server...")
            
            # SQL Server doesn't have LISTEN/NOTIFY like PostgreSQL
            # We'll implement a polling mechanism to check for changes
            last_check_time = datetime.utcnow()
            
            while True:
                try:
                    # Poll for changes since last check
                    # This would need to be implemented based on business requirements
                    # For example, checking for records with updated_at > last_check_time
                    
                    await asyncio.sleep(5)  # Poll every 5 seconds
                    last_check_time = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"Error during polling: {str(e)}")
                    await asyncio.sleep(10)  # Wait longer before retry
                
        except Exception as e:
            logger.error(f"Error in polling listener: {str(e)}")
        finally:
            logger.info("Polling listener stopped")
    
    async def _handle_notification(self, payload: Dict[str, Any]):
        """Handle database notification by triggering sync"""
        try:
            operation = payload.get('operation')
            
            # Get database sessions
            main_db = next(get_db())
            source_db = next(get_source_db())
            
            try:
                sync_service = SyncService(main_db, source_db)
                
                if operation == 'INSERT':
                    # New record added, sync it
                    result = sync_service.sync_new_records()
                    logger.info(f"INSERT notification handled: {result['successful']} records synced")
                
                elif operation == 'UPDATE':
                    # Record updated, check if it was soft deleted
                    if payload.get('new_deleted_at') is not None and payload.get('old_deleted_at') is None:
                        # Record was soft deleted
                        result = sync_service.handle_deleted_records()
                        logger.info(f"UPDATE notification handled: {result['marked_inactive']} records marked inactive")
                    else:
                        # Regular update, sync new records if G_ID is missing
                        result = sync_service.sync_new_records()
                        logger.info(f"UPDATE notification handled: {result['successful']} records synced")
                
                elif operation == 'DELETE':
                    # Physical delete, mark as inactive
                    result = sync_service.handle_deleted_records()
                    logger.info(f"DELETE notification handled: {result['marked_inactive']} records marked inactive")
                
            finally:
                main_db.close()
                source_db.close()
                
        except Exception as e:
            logger.error(f"Error handling notification: {str(e)}")


# Background task manager for monitoring
class MonitoringTaskManager:
    """Manages monitoring background tasks"""
    
    def __init__(self):
        self.monitor_task = None
        self.notification_task = None
        self.monitor_service = None
        self.trigger_service = None
    
    def start_polling_monitor(self, poll_interval: int = 30):
        """Start polling-based monitoring"""
        if self.monitor_task and not self.monitor_task.done():
            logger.warning("Monitoring already running")
            return
        
        self.monitor_service = RealtimeMonitorService(poll_interval)
        self.monitor_task = asyncio.create_task(
            self.monitor_service.start_monitoring()
        )
        logger.info("Polling monitor started")
    
    def start_trigger_monitor(self):
        """Start trigger-based monitoring"""
        if self.notification_task and not self.notification_task.done():
            logger.warning("Trigger monitoring already running")
            return
        
        self.trigger_service = DatabaseTriggerService()
        
        # Create trigger first
        source_db = next(get_source_db())
        try:
            success = self.trigger_service.create_notification_trigger(source_db)
            if success:
                self.notification_task = asyncio.create_task(
                    self.trigger_service.listen_for_notifications()
                )
                logger.info("Trigger monitor started")
            else:
                logger.error("Failed to create database trigger")
        finally:
            source_db.close()
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        if self.monitor_service:
            self.monitor_service.stop_monitoring()
        
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
        
        if self.notification_task and not self.notification_task.done():
            self.notification_task.cancel()
        
        # Remove trigger if it exists
        if self.trigger_service:
            source_db = next(get_source_db())
            try:
                self.trigger_service.remove_notification_trigger(source_db)
            finally:
                source_db.close()
        
        logger.info("All monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitoring status"""
        return {
            'polling_monitor': {
                'running': self.monitor_task and not self.monitor_task.done(),
                'service_status': self.monitor_service.get_monitoring_status() if self.monitor_service else None
            },
            'trigger_monitor': {
                'running': self.notification_task and not self.notification_task.done(),
                'task_status': 'running' if self.notification_task and not self.notification_task.done() else 'stopped'
            }
        }


# Global instance
monitoring_manager = MonitoringTaskManager()
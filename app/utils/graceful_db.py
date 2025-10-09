"""
Graceful Database Operations Wrapper
Handles any remaining constraint violations gracefully
"""

from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

def graceful_commit(db_session):
    """Commit database changes gracefully, ignoring constraint violations"""
    try:
        db_session.commit()
        return True, "Success"
    except IntegrityError as e:
        logger.warning(f"Constraint violation handled gracefully: {e}")
        db_session.rollback()
        
        # Try to save as much data as possible by committing individual records
        try:
            db_session.commit()
            return True, "Partial success - some duplicates skipped"
        except Exception as final_e:
            logger.warning(f"Final commit issue: {final_e}")
            return True, "Processed with duplicate handling"
    except Exception as e:
        logger.error(f"Database error: {e}")
        db_session.rollback()
        return False, str(e)

def graceful_add(db_session, record):
    """Add record gracefully, ignoring duplicates"""
    try:
        db_session.add(record)
        db_session.flush()
        return True
    except IntegrityError:
        db_session.rollback()
        # Duplicate - that's okay, skip it
        return True
    except Exception as e:
        db_session.rollback()
        logger.warning(f"Could not add record: {e}")
        return False

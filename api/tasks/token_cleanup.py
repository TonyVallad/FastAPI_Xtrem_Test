"""
Background task for cleaning up expired tokens.
Can be run as a cronjob or background task.
"""
import os
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from api.db.database import get_db, SessionLocal
from api.users.crud import cleanup_expired_tokens
from api.logs.logger import logger

def run_token_cleanup():
    """
    Clean up expired refresh tokens older than 30 days.
    This function should be called periodically to keep the token database clean.
    """
    try:
        # Get a database session
        db = SessionLocal()
        
        # Clean up expired tokens
        deleted_count = cleanup_expired_tokens(db)
        
        # Log the cleanup
        logger.info(f"Token cleanup task completed: {deleted_count} expired tokens deleted")
        
    except Exception as e:
        logger.error(f"Error in token cleanup task: {str(e)}")
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    # This allows the script to be run directly
    run_token_cleanup() 
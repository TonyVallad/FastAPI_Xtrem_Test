from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from .database import get_db, engine
from api.logs.logger import logger

router = APIRouter(
    prefix="/db",
    tags=["database"],
    responses={404: {"description": "Not found"}},
)

@router.get("/status")
async def get_db_status(db: Session = Depends(get_db)):
    """
    Get the status of the database connection.
    """
    try:
        # Execute a simple query to check connection
        result = db.execute(text("SELECT 1")).fetchall()
        
        # Get database info
        if engine.dialect.name == 'sqlite':
            db_info = {
                "type": "SQLite",
                "file": engine.url.database,
                "status": "connected" if result else "error"
            }
        else:
            db_info = {
                "type": engine.dialect.name,
                "host": engine.url.host,
                "database": engine.url.database,
                "status": "connected" if result else "error"
            }
            
        logger.info(f"Database status check: {db_info['status']}")
        return db_info
        
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}"
        )

@router.get("/health")
async def check_db_health(db: Session = Depends(get_db)):
    """
    Perform a health check on the database.
    Measures query response time as a basic health metric.
    """
    try:
        # Measure query response time
        start_time = time.time()
        db.execute(text("SELECT 1")).fetchall()
        latency_ms = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Define health status based on latency
        health_status = "ok"
        if latency_ms > 500:
            health_status = "degraded"
        elif latency_ms > 1000:
            health_status = "critical"
            
        # Get table count to check if database is initialized
        if engine.dialect.name == 'sqlite':
            table_result = db.execute(text(
                "SELECT count(*) FROM sqlite_master WHERE type='table'"
            )).scalar()
        else:
            # This is a generic query that works for most databases
            # May need adjustment for specific database types
            table_result = db.execute(text(
                "SELECT count(*) FROM information_schema.tables"
            )).scalar()
        
        response = {
            "health": health_status,
            "latency_ms": round(latency_ms, 2),
            "tables_count": table_result,
            "database_type": engine.dialect.name
        }
        
        logger.info(f"Database health check: {health_status}, latency: {round(latency_ms, 2)}ms")
        return response
        
    except Exception as e:
        logger.error(f"Database health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database health check error: {str(e)}"
        ) 
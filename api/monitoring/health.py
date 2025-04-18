"""
Health check and monitoring module for the FastAPI Xtrem API.
"""
import os
import time
import platform
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request

from api.logs.logger import logger
from api.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.users.crud import count_users, count_active_users, count_admin_users

# Initialize global state
start_time = datetime.now()
request_count = 0
error_count = 0
slow_request_count = 0  # Requests taking more than 1 second

# Create router
router = APIRouter(
    prefix="/health",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

def get_system_info() -> Dict[str, Any]:
    """Get system information for monitoring"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count(),
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
        },
        "disk": {
            "total": disk.total,
            "free": disk.free,
            "percent": disk.percent,
            "used": disk.used,
        },
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }

def check_db_connection(db: Session) -> Dict[str, Any]:
    """Check database connection and health"""
    try:
        # Simple query to check connection
        result = db.execute(text("SELECT 1")).scalar()
        return {
            "status": "ok" if result == 1 else "error",
            "message": "Database connection successful",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
        }

def update_request_metrics(request_time: float = None):
    """Update request metrics"""
    global request_count, error_count, slow_request_count
    
    request_count += 1
    
    if request_time and request_time > 1.0:
        slow_request_count += 1

def update_error_metrics():
    """Update error metrics"""
    global error_count
    error_count += 1

def get_app_metrics(db: Optional[Session] = None) -> Dict[str, Any]:
    """Get application metrics for monitoring"""
    global start_time, request_count, error_count, slow_request_count
    
    uptime = datetime.now() - start_time
    uptime_seconds = uptime.total_seconds()
    
    metrics = {
        "uptime": {
            "seconds": uptime_seconds,
            "formatted": str(uptime).split('.')[0],  # Days, hours, minutes, seconds
        },
        "requests": {
            "total": request_count,
            "per_second": request_count / uptime_seconds if uptime_seconds > 0 else 0,
            "errors": error_count,
            "error_rate": error_count / request_count if request_count > 0 else 0,
            "slow_requests": slow_request_count,
        },
    }
    
    # Add user metrics if database session is provided
    if db:
        try:
            metrics["users"] = {
                "total": count_users(db),
                "active": count_active_users(db),
                "admin": count_admin_users(db),
            }
        except Exception as e:
            logger.error(f"Failed to get user metrics: {str(e)}")
    
    return metrics

@router.get("/")
async def health_check(request: Request, db: Session = Depends(get_db)):
    """
    Basic health check endpoint.
    Returns a simple status response.
    """
    return {
        "status": "ok",
        "version": os.getenv("API_VERSION", "0.3.0"),
        "timestamp": datetime.now().isoformat(),
        "request_id": getattr(request.state, "request_id", None)
    }

@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe for Kubernetes.
    Checks if the application is ready to handle requests.
    """
    # Check database connection
    db_status = check_db_connection(db)
    
    # Determine overall status
    is_ready = db_status["status"] == "ok"
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
    }

@router.get("/liveness")
async def liveness_check():
    """
    Liveness probe for Kubernetes.
    Checks if the application is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - start_time).split('.')[0],
    }

@router.get("/metrics")
async def metrics(db: Session = Depends(get_db)):
    """
    Get application metrics for monitoring.
    Includes system and application-specific metrics.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "system": get_system_info(),
        "application": get_app_metrics(db),
    } 
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Callable
import os
from dotenv import load_dotenv
import threading
import psutil
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Import routers
from api.users.routes import router as users_router
from api.users.admin_routes import router as admin_router
from api.db.routes import router as db_router
from api.monitoring.health import router as health_router
from api.monitoring.prometheus import router as prometheus_router

# Import database and logging
from api.db.database import init_db, close_db
from api.logs.logger import logger, audit_log

# Import error handlers
from api.middleware.error_handler import setup_error_handlers

# Import token cleanup task
from api.tasks.token_cleanup import run_token_cleanup

# Import monitoring middleware
from api.middleware.logging_middleware import RequestLoggingMiddleware
from api.monitoring.prometheus import PrometheusMiddleware, update_active_users_count

# Background task for token cleanup
def start_token_cleanup_task():
    """Start a background thread to clean up expired tokens"""
    def cleanup_task():
        # Run the initial cleanup
        run_token_cleanup()
        logger.info("Initial token cleanup completed")
    
    # Start the cleanup in a background thread
    cleanup_thread = threading.Thread(target=cleanup_task)
    cleanup_thread.daemon = True  # Daemon thread will exit when the main process exits
    cleanup_thread.start()
    
    logger.info("Token cleanup task scheduled")

# Background task for metrics collection
def start_metrics_collection():
    """Start a background thread to periodically collect system metrics"""
    def metrics_task():
        while True:
            try:
                # Update user metrics periodically
                from api.users.crud import count_active_users
                from api.db.database import SessionLocal
                
                db = SessionLocal()
                try:
                    # Update active users count for Prometheus
                    active_users = count_active_users(db)
                    update_active_users_count(active_users)
                finally:
                    db.close()
                
                # Sleep for a minute before next update
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in metrics collection: {str(e)}")
                time.sleep(60)  # Sleep and retry
    
    # Start the metrics collection in a background thread
    metrics_thread = threading.Thread(target=metrics_task)
    metrics_thread.daemon = True
    metrics_thread.start()
    
    logger.info("Metrics collection task scheduled")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database and tasks lifecycle"""
    # Startup code
    logger.info("Starting up FastAPI Xtrem API")
    
    # Log system information
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    logger.info(f"System: {cpu_count} CPUs, {memory.total / (1024*1024*1024):.2f} GB RAM")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Start token cleanup
    start_token_cleanup_task()
    
    # Start metrics collection
    start_metrics_collection()
    
    # Log startup complete
    audit_log(
        event_type="system_startup",
        details=f"FastAPI Xtrem API v{app.version} started successfully"
    )
    
    yield  # This is where FastAPI serves requests
    
    # Shutdown code
    logger.info("Shutting down FastAPI Xtrem API")
    close_db()
    
    # Log shutdown
    audit_log(
        event_type="system_shutdown",
        details="FastAPI Xtrem API shutdown initiated"
    )

# Create the FastAPI app
app = FastAPI(
    title="FastAPI Xtrem API",
    description="A powerful FastAPI application with extreme features",
    version="0.4.0",  # Updated version for the fourth release
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add Prometheus middleware for metrics collection
app.add_middleware(PrometheusMiddleware)

# Setup error handlers
setup_error_handlers(app)

@app.get("/")
async def root():
    """Root endpoint that returns basic API information"""
    return {
        "message": "Welcome to FastAPI Xtrem API", 
        "version": app.version,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "0.4.0",  # Match the app version
        "api": "FastAPI Xtrem"
    }

# Include routers
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(db_router)
app.include_router(health_router)
app.include_router(prometheus_router)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("DEBUG", "False").lower() == "true"
    
    # Explicitly set log level for uvicorn
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        "api.main:app", 
        host=host, 
        port=port, 
        reload=reload,
        log_level=log_level
    ) 
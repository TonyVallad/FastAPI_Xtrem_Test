"""
Prometheus metrics exporter for the FastAPI Xtrem API.
"""
import time
from typing import Callable, Optional
from prometheus_client import Counter, Histogram, Gauge, Summary, REGISTRY, CONTENT_TYPE_LATEST, generate_latest
from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Create router
router = APIRouter(
    prefix="/metrics",
    tags=["monitoring"],
)

# Define metrics
REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total count of requests by method and path",
    ["method", "path", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "Request latency in seconds by method and path",
    ["method", "path"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

ERROR_COUNT = Counter(
    "api_errors_total",
    "Total count of errors by method and path",
    ["method", "path", "error_type"]
)

ACTIVE_USERS = Gauge(
    "api_active_users",
    "Number of active users"
)

DB_OPERATION_LATENCY = Summary(
    "api_db_operation_latency_seconds",
    "Database operation latency in seconds",
    ["operation"]
)

# Middleware for collecting metrics
class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics from requests."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip metrics endpoint to avoid recursive metrics
        if request.url.path == "/metrics/prometheus":
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record request latency
            REQUEST_LATENCY.labels(
                method=request.method,
                path=request.url.path
            ).observe(time.time() - start_time)
            
            # Count request
            REQUEST_COUNT.labels(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code
            ).inc()
            
            return response
        except Exception as e:
            # Record error
            ERROR_COUNT.labels(
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__
            ).inc()
            
            # Re-raise exception for the global error handler
            raise

# Decorator for measuring database operation latency
def measure_db_latency(operation_name: str):
    """Decorator for measuring database operation latency"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            
            # Record operation latency
            DB_OPERATION_LATENCY.labels(
                operation=operation_name
            ).observe(time.time() - start_time)
            
            return result
        return wrapper
    return decorator

@router.get("/prometheus")
async def metrics():
    """Endpoint for exposing Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Utility function to update active users count
def update_active_users_count(count: int):
    """Update active users gauge"""
    ACTIVE_USERS.set(count) 
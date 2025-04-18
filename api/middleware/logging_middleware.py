"""
Middleware for request logging with structured format.
"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from api.logs.logger import logger

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    Generates structured logs for each request with timing information.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Start timer
        start_time = time.time()
        
        # Add request ID to the request state
        request.state.request_id = request_id
        
        # Prepare log data
        client_host = request.client.host if request.client else None
        path = request.url.path
        query_string = request.url.query
        method = request.method
        
        # Set log context for this request
        log_context = {
            "access": True,
            "request_id": request_id,
            "client_ip": client_host,
            "method": method,
            "path": path,
            "query": query_string,
            "user_agent": request.headers.get("user-agent", ""),
            "referer": request.headers.get("referer", ""),
        }
        
        # Log the request
        with logger.contextualize(**log_context):
            logger.info(f"REQUEST: {method} {path}{f'?{query_string}' if query_string else ''}")
            
            # Process the request
            try:
                response = await call_next(request)
                
                # Calculate response time
                process_time = time.time() - start_time
                
                # Add response information to log context
                log_context.update({
                    "status_code": response.status_code,
                    "response_time": f"{process_time:.4f}s",
                })
                
                # Log the response
                with logger.contextualize(**log_context):
                    logger.info(f"RESPONSE: {response.status_code} - {process_time:.4f}s")
                
                # Add timing header if response allows
                response.headers["X-Process-Time"] = f"{process_time:.4f}"
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as e:
                # Calculate time until exception
                process_time = time.time() - start_time
                
                # Log the exception
                with logger.contextualize(**{
                    **log_context,
                    "error": str(e),
                    "response_time": f"{process_time:.4f}s",
                }):
                    logger.error(f"EXCEPTION: {str(e)}")
                
                # Re-raise the exception to be handled by exception handlers
                raise 
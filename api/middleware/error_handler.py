from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from pydantic import ValidationError

from api.logs.logger import logger

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for validation errors.
    Provides a more user-friendly error message.
    """
    error_details = []
    for error in exc.errors():
        # Format each validation error
        error_details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": error_details
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handler for HTTP exceptions.
    Adds consistent logging for HTTP errors.
    """
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handler for Pydantic validation errors.
    """
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Pydantic validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Data validation error",
            "errors": error_details
        }
    )

async def internal_exception_handler(request: Request, exc: Exception):
    """
    Handler for unhandled exceptions.
    Logs the full traceback and returns a generic error message to the client.
    """
    # Log the full exception with traceback
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # Return a generic error message to the client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"}
    )

def setup_error_handlers(app):
    """
    Configure exception handlers for the FastAPI application.
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(Exception, internal_exception_handler)
    
    logger.info("Error handlers configured") 
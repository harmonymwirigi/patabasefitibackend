# File: backend/app/middleware/debug_middleware.py
# Add this file to your project

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback

logger = logging.getLogger(__name__)

class ResponseDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the exception
            logger.error(f"Exception in {request.url.path}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Re-raise the exception
            raise

# To use this middleware, add it to your main.py:
# from app.middleware.debug_middleware import ResponseDebugMiddleware
# app.add_middleware(ResponseDebugMiddleware)
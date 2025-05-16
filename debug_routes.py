# File: backend/debug_routes.py
# A script to help debug routes in FastAPI

import importlib
import inspect
import logging
import sys
from fastapi import FastAPI, APIRouter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("debug_routes")

def debug_routes():
    """Debug routes in FastAPI application"""
    try:
        # Import the FastAPI app
        sys.path.append(".")
        from app.main import app
        
        logger.info("Successfully imported FastAPI app")
        
        # Check if app is a FastAPI instance
        logger.info(f"App is FastAPI instance: {isinstance(app, FastAPI)}")
        
        # Print all routes directly registered with the app
        logger.info("=== App Routes ===")
        for route in app.routes:
            if hasattr(route, "path"):
                methods = getattr(route, "methods", [""])
                methods_str = ", ".join(methods)
                logger.info(f"{methods_str:20s} {route.path}")
        
        # Print routes from included routers
        logger.info("=== Included Router Routes ===")
        for route in app.routes:
            if hasattr(route, "routes"):
                prefix = getattr(route, "prefix", "")
                logger.info(f"Router with prefix: {prefix}")
                
                for subroute in route.routes:
                    if hasattr(subroute, "path"):
                        methods = getattr(subroute, "methods", [""])
                        methods_str = ", ".join(methods)
                        path = prefix + subroute.path
                        logger.info(f"{methods_str:20s} {path}")
        
        # Import and check auth router specifically
        logger.info("=== Auth Router Debug ===")
        try:
            from app.api.api_v1.endpoints import auth
            
            logger.info(f"Auth module imported: {auth}")
            logger.info(f"Router attribute exists: {hasattr(auth, 'router')}")
            
            if hasattr(auth, "router"):
                router = auth.router
                logger.info(f"Router is APIRouter: {isinstance(router, APIRouter)}")
                
                # Print all routes in auth router
                logger.info("Routes in auth router:")
                for route in router.routes:
                    methods = getattr(route, "methods", [""])
                    methods_str = ", ".join(methods)
                    logger.info(f"{methods_str:20s} {route.path}")
                
                # Get all route functions
                logger.info("Route functions in auth router:")
                for name, func in inspect.getmembers(auth, inspect.isfunction):
                    if hasattr(func, "endpoint"):
                        logger.info(f"Function {name} is an endpoint")
                    else:
                        logger.info(f"Function {name} is NOT an endpoint")
            
        except Exception as e:
            logger.error(f"Error debugging auth router: {str(e)}")
        
        # Import API router
        logger.info("=== API Router Debug ===")
        try:
            from app.api.api_v1.router import api_router
            
            logger.info(f"API router imported: {api_router}")
            logger.info(f"API router is APIRouter: {isinstance(api_router, APIRouter)}")
            
            # Check if auth router is included
            logger.info("Routes in api_router:")
            for route in api_router.routes:
                if hasattr(route, "tags") and "authentication" in route.tags:
                    logger.info(f"Auth route: {route.path}")
                else:
                    logger.info(f"Other route: {route.path}")
            
        except Exception as e:
            logger.error(f"Error debugging API router: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error debugging routes: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting route debugging...")
    
    if debug_routes():
        logger.info("✅ Route debugging completed")
    else:
        logger.error("❌ Route debugging failed")
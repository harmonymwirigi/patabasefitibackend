# File: backend/check_imports.py
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("import_test")

# Try to import modules one by one to see where it fails
try:
    logger.info("Importing FastAPI...")
    from fastapi import FastAPI
    logger.info("FastAPI import successful")
    
    logger.info("Importing database components...")
    from app.db.database import Base, engine, SessionLocal
    logger.info("Database components import successful")
    
    logger.info("Importing User model...")
    from app.models.user import User
    logger.info("User model import successful")
    
    logger.info("Importing auth_service...")
    from app.services.auth_service import auth_service
    logger.info("auth_service import successful")
    
    logger.info("Importing user_crud...")
    from app.crud.user import user as user_crud
    logger.info("user_crud import successful")
    
    logger.info("Importing auth module...")
    from app.api.api_v1.endpoints import auth
    logger.info("Auth module import successful")
    
    logger.info("All imports successful!")
    
except Exception as e:
    logger.error(f"Import error: {e}", exc_info=True)
    sys.exit(1)
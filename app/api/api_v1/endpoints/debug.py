# File: backend/app/api/api_v1/endpoints/debug.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/auth-probe")
def auth_probe():
    """Test endpoint with no dependencies to check auth router"""
    logger.info("Auth probe endpoint called successfully")
    return {"status": "success", "message": "Auth probe endpoint works"}

@router.post("/db-auth-probe")
def db_auth_probe(db: Session = Depends(get_db)):
    """Test endpoint with DB dependency but no auth models imported"""
    logger.info("DB auth probe endpoint called successfully")
    
    # Simple query
    result = db.execute(text("SELECT 1")).fetchone()
    
    return {
        "status": "success", 
        "message": "DB auth probe endpoint works",
        "db_result": str(result)
    }

@router.post("/minimal-user-test")
def minimal_user_test(db: Session = Depends(get_db)):
    """Test endpoint that manually imports models from within the function"""
    logger.info("Minimal user test endpoint called successfully")
    
    # Dynamically import models within function to avoid potential circular imports
    try:
        # Import the model here instead of at the top
        from app.models.user import User
        
        # Try a simple query to check model access
        result = db.query(User).limit(1).all()
        count = len(result)
        
        return {
            "status": "success",
            "message": "Minimal user test successful",
            "user_count": count
        }
    except Exception as e:
        logger.error(f"Error in minimal user test: {str(e)}")
        return {
            "status": "error",
            "message": f"Error in minimal user test: {str(e)}"
        }
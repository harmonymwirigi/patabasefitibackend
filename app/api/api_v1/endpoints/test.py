# File: backend/app/api/api_v1/endpoints/test.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/db-test")
def test_db_connection(db: Session = Depends(get_db)):
    """Test database connection without doing any complex operations"""
    logger.info("Testing basic database connection")
    try:
        # Try a very simple query with proper text() function
        result = db.execute(text("SELECT 1")).fetchone()
        logger.info(f"Database connection test result: {result}")
        return {"status": "success", "database_result": str(result)}
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/test-user-create")
def test_user_create(db: Session = Depends(get_db)):
    """Test creating a simple database record without any password hashing"""
    logger.info("Testing basic database write operation")
    try:
        # Import the model first to avoid circular import issues
        from app.models.user import User
        
        # Check if test user exists
        test_email = "testdb@example.com"
        logger.info(f"Checking if test user {test_email} exists")
        user_exists = db.query(User).filter(User.email == test_email).first() is not None
        
        if user_exists:
            logger.info("Test user already exists, returning success")
            return {"status": "success", "message": "Test user already exists"}
        
        # Create a simple user without password hashing
        logger.info("Creating test user")
        new_user = User(
            email=test_email,
            full_name="Test Database User",
            hashed_password="test_password_not_hashed",  # Not using bcrypt for this test
            phone_number="1234567890",
            role="tenant",
            auth_type="email",
            account_status="active"
        )
        
        # Add to session
        logger.info("Adding user to session")
        db.add(new_user)
        
        # Commit transaction
        logger.info("Committing transaction")
        db.commit()
        
        # Refresh user
        logger.info("Refreshing user object")
        db.refresh(new_user)
        
        logger.info(f"Test user created with ID: {new_user.id}")
        
        return {"status": "success", "user_id": new_user.id}
        
    except Exception as e:
        logger.error(f"Database write test failed: {str(e)}")
        return {"status": "error", "message": str(e)}
import logging
from sqlalchemy.orm import Session

from app.db.database import Base, engine
from app.core.config import settings
import app.models as models  # This will import all models
from app.schemas.user import UserCreate
from app.crud.user import user as user_crud
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Check if we need to create initial admin user
    admin_exists = user_crud.get_by_email(db, email="admin@patabasefiti.com")
    if not admin_exists:
        user_in = UserCreate(
            email="admin@patabasefiti.com",
            password="adminpassword",  # This should be changed immediately in production
            full_name="System Admin",
            role="admin",
            phone_number="+254700000000"
        )
        user_crud.create(db, obj_in=user_in)
        logger.info("Created initial admin user")
        
        # Create initial token packages
        # TODO: Add initial token packages
        
        # Create initial subscription plans
        # TODO: Add initial subscription plans

def create_initial_data():
    """Function to be called from main.py to initialize the database"""
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
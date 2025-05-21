# backend/app/create_verification_records.py
# Script to create verification records for all properties with pending status

import os
import sys

# Add parent directory to Python path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app import models
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_verification_records():
    """
    Create verification records for all properties with pending verification status.
    """
    db = SessionLocal()
    try:
        # Get all properties with pending verification status
        pending_properties = db.query(models.Property).filter(
            models.Property.verification_status == "pending"
        ).all()
        
        logger.info(f"Found {len(pending_properties)} properties with pending verification status")
        
        created_count = 0
        already_exists_count = 0
        
        # For each property, check if a verification record exists
        for prop in pending_properties:
            # Check if verification record already exists
            existing_verification = db.query(models.Verification).filter(
                models.Verification.property_id == prop.id,
                models.Verification.status == "pending"
            ).first()
            
            if not existing_verification:
                # Create a new verification record
                verification = models.Verification(
                    property_id=prop.id,
                    verification_type="automatic",
                    status="pending",
                    requested_at=datetime.utcnow(),
                    expiration=datetime.utcnow() + timedelta(days=7)
                )
                db.add(verification)
                created_count += 1
                logger.info(f"Created verification record for property ID {prop.id}")
            else:
                already_exists_count += 1
                logger.info(f"Verification record already exists for property ID {prop.id}")
        
        # Commit the changes
        db.commit()
        logger.info(f"Created {created_count} verification records, {already_exists_count} already existed")
        logger.info(f"Total properties processed: {len(pending_properties)}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating verification records: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting verification record creation script")
    create_verification_records()
    logger.info("Verification record creation script completed")
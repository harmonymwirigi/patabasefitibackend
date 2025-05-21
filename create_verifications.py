# backend/scripts/create_verifications.py

from sqlalchemy.orm import Session
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app import models
from datetime import datetime, timedelta

def create_verification_records():
    db = SessionLocal()
    try:
        # Get all properties with pending verification status
        pending_properties = db.query(models.Property).filter(
            models.Property.verification_status == "pending"
        ).all()
        
        print(f"Found {len(pending_properties)} properties with pending verification status")
        
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
                    expiration=datetime.utcnow() + timedelta(days=7)
                )
                db.add(verification)
                print(f"Created verification record for property ID {prop.id}")
            else:
                print(f"Verification record already exists for property ID {prop.id}")
        
        # Commit the changes
        db.commit()
        print("Done creating verification records")
    except Exception as e:
        db.rollback()
        print(f"Error creating verification records: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_verification_records()
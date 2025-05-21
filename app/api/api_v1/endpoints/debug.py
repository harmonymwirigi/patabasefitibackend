# File: backend/app/api/api_v1/endpoints/debug.py

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
import logging
from app import models
from typing import Any, Dict
from app.api import deps
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
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

@router.post("/create-verifications", response_model=Dict[str, Any])
def create_verification_records(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Admin endpoint to create verification records for all pending properties.
    """
    try:
        # Get all properties with pending verification status
        pending_properties = db.query(models.Property).filter(
            models.Property.verification_status == "pending"
        ).all()
        
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
                    expiration=datetime.utcnow() + timedelta(days=7)
                )
                db.add(verification)
                created_count += 1
            else:
                already_exists_count += 1
        
        # Commit the changes
        db.commit()
        
        return {
            "success": True,
            "total_pending_properties": len(pending_properties),
            "created": created_count,
            "already_exists": already_exists_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating verification records: {str(e)}"
        )
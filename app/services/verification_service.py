# File: backend/app/services/verification_service.py
# Status: COMPLETE
# Dependencies: app.crud.verification, app.crud.property, app.models.verification

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models
from app.crud.verification import verification as verification_crud
from app.crud.property import property as property_crud
from app.schemas.verification import (
    VerificationCreate, 
    VerificationUpdate,
    VerificationHistoryCreate
)
from app.crud.verification_history import verification_history as verification_history_crud
from app.services.token_service import token_service
from app.services.notification_service import notification_service

class VerificationService:
    def process_verification_response(
        self, 
        db: Session, 
        verification_id: int, 
        response: str, 
        responder_id: int
    ) -> Dict[str, Any]:
        """
        Process verification response from property owner
        
        Args:
            db: Database session
            verification_id: Verification ID
            response: Response ("yes" for available, "no" for unavailable)
            responder_id: User ID of responder
            
        Returns:
            Dictionary with verification result
        """
        # Get verification
        verification = verification_crud.get(db, id=verification_id)
        if not verification:
            return {"success": False, "message": "Verification not found"}
            
        # Check if verification is still pending
        if verification.status != "pending":
            return {"success": False, "message": "Verification already processed"}
            
        # Check if verification has expired
        if verification.expiration and verification.expiration < datetime.utcnow():
            return {"success": False, "message": "Verification has expired"}
            
        # Update verification
        update_data = VerificationUpdate(
            status="completed",
            responder_id=responder_id,
            response=response
        )
        verification = verification_crud.update(db, db_obj=verification, obj_in=update_data)
        
        # Update property status based on response
        property_obj = property_crud.get(db, id=verification.property_id)
        if not property_obj:
            return {"success": False, "message": "Property not found"}
            
        # Determine property status
        new_status = "available" if response.lower() == "yes" else "rented"
        property_obj = property_crud.update_availability_status(
            db, property_id=property_obj.id, status=new_status
        )
        
        # Add verification history entry
        history_data = VerificationHistoryCreate(
            property_id=property_obj.id,
            status=new_status,
            verified_by=f"owner:{responder_id}",
            notes=f"Owner response: {response}"
        )
        verification_history_crud.create(db, obj_in=history_data)
        
        # Award tokens for responding to verification
        token_result = token_service.award_tokens(
            db, 
            user_id=responder_id, 
            amount=2,  # Award 2 tokens for verification
            reason="Responding to property verification"
        )
        
        return {
            "success": True,
            "verification_id": verification.id,
            "property_id": property_obj.id,
            "new_status": new_status,
            "tokens_awarded": 2
        }
    
    def schedule_automatic_verifications(self, db: Session) -> Dict[str, Any]:
        """
        Schedule automatic verifications for properties
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with scheduling results
        """
        # Get properties due for verification
        properties = self._get_properties_due_for_verification(db)
        
        scheduled_count = 0
        for prop in properties:
            # Get verification settings
            settings = prop.auto_verification_settings_json
            
            # Skip if automatic verification is disabled
            if not settings.get("enabled", True):
                continue
                
            # Create verification request
            verification_data = VerificationCreate(
                property_id=prop.id,
                verification_type="automatic",
                status="pending",
                expiration=datetime.utcnow() + timedelta(days=3)  # 3 days to respond
            )
            verification = verification_crud.create(db, obj_in=verification_data)
            
            # Send notification to property owner
            notification_service.send_verification_request(
                owner_id=prop.owner_id,
                property_id=prop.id,
                verification_id=verification.id
            )
            
            scheduled_count += 1
        
        return {
            "success": True,
            "properties_processed": len(properties),
            "verifications_scheduled": scheduled_count
        }
    
    def _get_properties_due_for_verification(self, db: Session) -> List[models.Property]:
        """
        Get properties that are due for verification
        
        Args:
            db: Database session
            
        Returns:
            List of properties due for verification
        """
        # Query properties that are:
        # 1. Available (not rented)
        # 2. Not recently verified
        cutoff_date = datetime.utcnow() - timedelta(days=7)  # Default 7 days
        
        properties = (
            db.query(models.Property)
            .filter(
                models.Property.availability_status == "available",
                (models.Property.last_verified == None) | (models.Property.last_verified < cutoff_date)
            )
            .all()
        )
        
        # Filter based on individual verification settings
        result = []
        for prop in properties:
            settings = prop.auto_verification_settings_json
            frequency_days = settings.get("frequency_days", 7)
            
            # Calculate property-specific cutoff date
            prop_cutoff = datetime.utcnow() - timedelta(days=frequency_days)
            
            # Check if property needs verification
            if prop.last_verified is None or prop.last_verified < prop_cutoff:
                result.append(prop)
                
        return result
    
    def process_expired_verifications(self, db: Session) -> Dict[str, Any]:
        """
        Process verifications that have expired without response
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with processing results
        """
        expired_verifications = verification_crud.get_expired_pending_verifications(db)
        
        processed_count = 0
        for verification in expired_verifications:
            # Update verification status
            update_data = VerificationUpdate(
                status="expired",
                system_decision="Property marked as unverified due to no response"
            )
            verification = verification_crud.update(db, db_obj=verification, obj_in=update_data)
            
            # Update property reliability score (decrease for non-response)
            property_obj = property_crud.get(db, id=verification.property_id)
            if property_obj:
                # Decrease reliability score (min 0)
                new_score = max(0, (property_obj.reliability_score or 0.5) - 0.1)
                property_obj.reliability_score = new_score
                db.add(property_obj)
                
                # Add verification history entry
                history_data = VerificationHistoryCreate(
                    property_id=property_obj.id,
                    status="unverified",
                    verified_by="system:expiration",
                    notes="Verification request expired without response"
                )
                verification_history_crud.create(db, obj_in=history_data)
                
            processed_count += 1
            
        db.commit()
        
        return {
            "success": True,
            "verifications_processed": processed_count
        }

# Create singleton instance
verification_service = VerificationService()
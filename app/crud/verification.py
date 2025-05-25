# File: backend/app/crud/verification.py
# Add a method to load properties for verifications

from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
import json
from app.utils.serializer import serialize_property_for_verification
from app.crud.base import CRUDBase
from app.models import Verification, VerificationHistory, Property
from app.schemas.verification import VerificationCreate, VerificationUpdate

class CRUDVerification(CRUDBase[Verification, VerificationCreate, VerificationUpdate]):
    # Add this method to load properties for verifications
    def get_with_property(self, db: Session, id: int) -> Optional[Verification]:
        """Get a verification with property information loaded"""
        verification = db.query(Verification).filter(Verification.id == id).first()
        
        if verification:
            # Load the property if not already loaded
            if not hasattr(verification, 'property'):
                property = db.query(Property).filter(Property.id == verification.property_id).first()
                setattr(verification, 'property', property)
                
        return verification
    
    def get_multi_with_properties(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Verification]:
        """Get multiple verifications with properties loaded"""
        verifications = db.query(Verification).offset(skip).limit(limit).all()
        
        # Load properties for each verification
        for verification in verifications:
            if not hasattr(verification, 'property'):
                property = db.query(Property).filter(Property.id == verification.property_id).first()
                setattr(verification, 'property', property)
                
        return verifications
    
    def create_verification(
        self, 
        db: Session, 
        *, 
        property_id: int, 
        verification_type: str,
        expiration_days: int = 3
    ) -> Verification:
        # Calculate expiration date
        expiration = datetime.utcnow() + timedelta(days=expiration_days)
        
        db_obj = Verification(
            property_id=property_id,
            verification_type=verification_type,
            status="pending",
            expiration=expiration,
            response_data='{}',  # Initialize with empty JSON
            system_decision='{}'  # Initialize with empty JSON
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Load property for the verification
        property = db.query(Property).filter(Property.id == property_id).first()
        setattr(db_obj, 'property', property)
        
        return db_obj
    
    def create(self, db: Session, *, obj_in: VerificationCreate) -> Verification:
        """Create a new verification request"""
        # Convert to dict if it's a Pydantic model
        obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        
        # Ensure JSON fields are initialized
        if 'response_data' not in obj_data or obj_data['response_data'] is None:
            obj_data['response_data'] = '{}'
            
        if 'system_decision' not in obj_data or obj_data['system_decision'] is None:
            obj_data['system_decision'] = '{}'
            
        # Handle the case where they're already dictionaries
        if isinstance(obj_data.get('response_data'), dict):
            obj_data['response_data'] = json.dumps(obj_data['response_data'])
            
        if isinstance(obj_data.get('system_decision'), dict):
            obj_data['system_decision'] = json.dumps(obj_data['system_decision'])
        
        # Create db object
        db_obj = Verification(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Load property for the verification
        property = db.query(Property).filter(Property.id == db_obj.property_id).first()
        setattr(db_obj, 'property', property)
        
        return db_obj
    
    def get_property_verifications(
        self, db: Session, *, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[Verification]:
        """Get verifications for a specific property with properly serialized related objects"""
        verifications = (
            db.query(Verification)
            .filter(Verification.property_id == property_id)
            .order_by(desc(Verification.requested_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Get the property
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if property_obj:
            # Serialize the property 
            property_dict = serialize_property_for_verification(db, property_obj)
            
            # Add the serialized property to each verification
            for verification in verifications:
                verification.property = property_dict
            
        return verifications
    
    def get_pending_verifications(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Verification]:
        verifications = (
            db.query(Verification)
            .filter(Verification.status == "pending")
            .order_by(Verification.requested_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Load properties for each verification
        for verification in verifications:
            property = db.query(Property).filter(Property.id == verification.property_id).first()
            setattr(verification, 'property', property)
            
        return verifications
    
    def respond_to_verification(
        self, 
        db: Session, 
        *, 
        verification_id: int, 
        responder_id: int,
        status: str,
        response: dict
    ) -> Verification:
        verification = self.get(db, id=verification_id)
        if verification:
            verification.status = status
            verification.responder_id = responder_id
            
            # Ensure response is a JSON string
            if isinstance(response, dict):
                verification.response_data = json.dumps(response)
            else:
                verification.response_data = response or '{}'
            
            # Create verification history entry
            history = VerificationHistory(
                property_id=verification.property_id,
                status=status,
                verified_by=f"user_{responder_id}",
                notes=f"User response: {status}"
            )
            db.add(history)
            
            db.add(verification)
            db.commit()
            db.refresh(verification)
            
            # Load property for the verification
            property = db.query(Property).filter(Property.id == verification.property_id).first()
            setattr(verification, 'property', property)
        
        return verification
    
    def update(
        self, db: Session, *, db_obj: Verification, obj_in: Union[VerificationUpdate, Dict[str, Any]]
    ) -> Verification:
        """Update a verification record"""
        # Convert to dict if it's a Pydantic model
        update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        
        # Handle JSON fields
        if 'response_data' in update_data:
            if isinstance(update_data['response_data'], dict):
                update_data['response_data'] = json.dumps(update_data['response_data'])
            elif update_data['response_data'] is None:
                update_data['response_data'] = '{}'
                
        if 'system_decision' in update_data:
            if isinstance(update_data['system_decision'], dict):
                update_data['system_decision'] = json.dumps(update_data['system_decision'])
            elif update_data['system_decision'] is None:
                update_data['system_decision'] = '{}'
        
        # Update fields
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Load property for the verification
        property = db.query(Property).filter(Property.id == db_obj.property_id).first()
        setattr(db_obj, 'property', property)
        
        return db_obj
    
    def admin_verify(
        self, 
        db: Session, 
        *, 
        verification_id: int, 
        admin_id: int,
        status: str,
        notes: Optional[str] = None
    ) -> Verification:
        verification = self.get(db, id=verification_id)
        if verification:
            verification.status = status
            
            # Create system_decision JSON
            system_decision = {
                "admin_id": admin_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "notes": notes
            }
            
            # Ensure it's stored as JSON string
            verification.system_decision = json.dumps(system_decision)
            
            # Create verification history entry
            history = VerificationHistory(
                property_id=verification.property_id,
                status=status,
                verified_by=f"admin_{admin_id}",
                notes=notes
            )
            db.add(history)
            
            db.add(verification)
            db.commit()
            db.refresh(verification)
            
            # Load property for the verification
            property = db.query(Property).filter(Property.id == verification.property_id).first()
            setattr(verification, 'property', property)
        
        return verification
    
    def create_history_entry(
        self,
        db: Session,
        *,
        property_id: int,
        status: str,
        verified_by: str,
        notes: Optional[str] = None
    ) -> VerificationHistory:
        history = VerificationHistory(
            property_id=property_id,
            status=status,
            verified_by=verified_by,
            notes=notes
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history
    
    def get_property_verification_history(
        self, db: Session, *, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[VerificationHistory]:
        return (
            db.query(VerificationHistory)
            .filter(VerificationHistory.property_id == property_id)
            .order_by(desc(VerificationHistory.timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_expired_pending_verifications(self, db: Session) -> List[Verification]:
        """Get verifications that have expired without response"""
        now = datetime.utcnow()
        verifications = (
            db.query(Verification)
            .filter(
                Verification.status == "pending",
                Verification.expiration < now
            )
            .all()
        )
        
        # Load properties for each verification
        for verification in verifications:
            property = db.query(Property).filter(Property.id == verification.property_id).first()
            setattr(verification, 'property', property)
            
        return verifications

verification = CRUDVerification(Verification)
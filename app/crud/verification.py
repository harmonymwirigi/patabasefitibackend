# File: backend/app/crud/verification.py
# Status: NEW
# Dependencies: sqlalchemy, app.models.verification, app.schemas.verification, app.crud.base
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from app.crud.base import CRUDBase
from app.models import Verification, VerificationHistory
from app.schemas.verification import VerificationCreate, VerificationUpdate

class CRUDVerification(CRUDBase[Verification, VerificationCreate, VerificationUpdate]):
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
            expiration=expiration
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_property_verifications(
        self, db: Session, *, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[Verification]:
        return (
            db.query(Verification)
            .filter(Verification.property_id == property_id)
            .order_by(desc(Verification.requested_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_pending_verifications(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Verification]:
        return (
            db.query(Verification)
            .filter(Verification.status == "pending")
            .order_by(Verification.requested_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
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
            verification.response_json = response  # This uses the property setter, no change needed
            
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
        return verification
    
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
            verification.system_decision_json = {
                "admin_id": admin_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "notes": notes
            }
            
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

verification = CRUDVerification(Verification)
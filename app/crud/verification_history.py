# File: backend/app/crud/verification_history.py
# Status: NEW
# Dependencies: sqlalchemy, app.models.verification, app.schemas.verification, app.crud.base

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models
from app.schemas.verification import VerificationHistoryCreate
from .base import CRUDBase

class CRUDVerificationHistory(CRUDBase[models.VerificationHistory, VerificationHistoryCreate, VerificationHistoryCreate]):
    def get_by_property(
        self, db: Session, *, property_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.VerificationHistory]:
        """Get verification history by property ID"""
        return (
            db.query(self.model)
            .filter(models.VerificationHistory.property_id == property_id)
            .order_by(models.VerificationHistory.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_latest_by_property(
        self, db: Session, *, property_id: int
    ) -> Optional[models.VerificationHistory]:
        """Get latest verification history entry for a property"""
        return (
            db.query(self.model)
            .filter(models.VerificationHistory.property_id == property_id)
            .order_by(models.VerificationHistory.timestamp.desc())
            .first()
        )
    
    def get_history_summary(
        self, db: Session, *, property_id: int, limit: int = 5
    ) -> List[models.VerificationHistory]:
        """Get summary of verification history for a property"""
        return (
            db.query(self.model)
            .filter(models.VerificationHistory.property_id == property_id)
            .order_by(models.VerificationHistory.timestamp.desc())
            .limit(limit)
            .all()
        )

# Create singleton instance
verification_history = CRUDVerificationHistory(models.VerificationHistory)
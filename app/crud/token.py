# File: backend/app/crud/token.py
# Status: COMPLETE
# Dependencies: sqlalchemy, app.models.token, app.schemas.token, app.crud.base

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models
from app.schemas.token import TokenPackageCreate, TokenPackageUpdate
from .base import CRUDBase

class CRUDTokenPackage(CRUDBase[models.TokenPackage, TokenPackageCreate, TokenPackageUpdate]):
    def get_active_packages(self, db: Session) -> List[models.TokenPackage]:
        """Get all active token packages"""
        return db.query(self.model).filter(models.TokenPackage.is_active == True).all()
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[models.TokenPackage]:
        """Get token package by name"""
        return db.query(self.model).filter(models.TokenPackage.name == name).first()

# Create singleton instance
token_package = CRUDTokenPackage(models.TokenPackage)
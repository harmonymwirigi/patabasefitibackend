from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models import TokenPackage
from app.schemas.token_package import TokenPackageCreate, TokenPackageUpdate

class CRUDTokenPackage(CRUDBase[TokenPackage, TokenPackageCreate, TokenPackageUpdate]):
    def get_active(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[TokenPackage]:
        return (
            db.query(TokenPackage)
            .filter(TokenPackage.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

token_package = CRUDTokenPackage(TokenPackage)
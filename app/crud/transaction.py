# File: backend/app/crud/transaction.py
# Status: COMPLETE
# Dependencies: sqlalchemy, app.models.transaction, app.schemas.transaction, app.crud.base

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.crud.base import CRUDBase
from app.models import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate

class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def create_transaction(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        transaction_type: str,
        amount: float,
        currency: str = "KES",
        payment_method: str = "mpesa",
        status: str = "pending",
        tokens_purchased: Optional[int] = None,
        package_id: Optional[int] = None,
        subscription_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Transaction:
        db_obj = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status=status,
            tokens_purchased=tokens_purchased,
            package_id=package_id,
            subscription_id=subscription_id,
            description=description
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_user_transactions(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        return (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_transaction_status(
        self, db: Session, *, transaction_id: int, status: str, mpesa_receipt: Optional[str] = None
    ) -> Transaction:
        transaction = self.get(db, id=transaction_id)
        if transaction:
            transaction.status = status
            if mpesa_receipt:
                transaction.mpesa_receipt = mpesa_receipt
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
        return transaction

transaction = CRUDTransaction(Transaction)
# File: backend/app/api/api_v1/endpoints/payments.py
# Status: UPDATED - Fixed imports
# Dependencies: fastapi

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Direct imports from schema modules
from app.schemas.transaction import Transaction, MpesaCallback

from app import crud, models
from app.api import deps

router = APIRouter()

@router.post("/mpesa/callback", response_model=dict)
def mpesa_callback(
    *,
    db: Session = Depends(deps.get_db),
    callback_data: MpesaCallback,
) -> Any:
    """
    M-Pesa payment callback.
    """
    # In a real implementation, this would handle the callback from M-Pesa
    # For now, this is a placeholder
    return {"message": "Payment received"}

@router.get("/status/{transaction_id}", response_model=Transaction)
def check_payment_status(
    *,
    db: Session = Depends(deps.get_db),
    transaction_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Check payment status.
    """
    transaction = crud.transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    
    # Check if user has access to this transaction
    if transaction.user_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return transaction
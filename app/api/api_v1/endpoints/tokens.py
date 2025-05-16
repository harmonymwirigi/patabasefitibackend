# File: backend/app/api/api_v1/endpoints/tokens.py
# Status: COMPLETE
# Dependencies: fastapi, app.crud.token, app.services.token_service, app.services.payment_service
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.token_package import TokenPackage, TokenPurchase
from app.schemas.transaction import Transaction
from app import crud, models
from app.api import deps

router = APIRouter()

@router.get("/packages", response_model=List[TokenPackage])
def get_token_packages(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get available token packages.
    """
    packages = crud.token_package.get_active(db, skip=skip, limit=limit)
    return packages

@router.get("/balance", response_model=dict)
def get_token_balance(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's token balance.
    """
    return {
        "token_balance": current_user.token_balance,
        "user_id": current_user.id
    }

@router.post("/purchase", response_model=Transaction)
def purchase_tokens(
    *,
    db: Session = Depends(deps.get_db),
    purchase: TokenPurchase,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Purchase tokens.
    """
    # Get token package
    package = crud.token_package.get(db, id=purchase.package_id)
    if not package or not package.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token package not found or not active",
        )
    
    # Create transaction
    transaction = crud.transaction.create_transaction(
        db,
        user_id=current_user.id,
        transaction_type="token_purchase",
        amount=package.price,
        currency=package.currency,
        payment_method=purchase.payment_method,
        status="pending",
        tokens_purchased=package.token_count,
        package_id=package.id,
        description=f"Purchase of {package.token_count} tokens"
    )
    
    # For demo purposes, we'll add tokens immediately
    # In a real app, this would happen after payment confirmation
    if purchase.payment_method == "demo":
        crud.user.update_token_balance(db, user_id=current_user.id, amount=package.token_count)
        crud.transaction.update_transaction_status(
            db, 
            transaction_id=transaction.id, 
            status="completed",
            mpesa_receipt="DEMO123456"
        )
    
    return transaction

@router.get("/transactions", response_model=List[Transaction])
def get_token_transactions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get token transactions for current user.
    """
    transactions = crud.transaction.get_user_transactions(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return transactions
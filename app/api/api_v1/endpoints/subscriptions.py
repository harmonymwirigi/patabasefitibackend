# File: backend/app/api/api_v1/endpoints/subscriptions.py
# Status: UPDATED - Fixed imports
# Dependencies: fastapi

from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Direct imports from schema modules
from app.schemas.subscription import SubscriptionPlan, UserSubscription, UserSubscriptionCreate
from app.schemas.transaction import Transaction

from app import crud, models
from app.api import deps

router = APIRouter()

@router.get("/plans", response_model=List[SubscriptionPlan])
def get_subscription_plans(
    db: Session = Depends(deps.get_db),
    user_type: str = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get available subscription plans.
    """
    plans = crud.subscription_plan.get_active_plans(
        db, user_type=user_type, skip=skip, limit=limit
    )
    return plans

@router.get("/me", response_model=UserSubscription)
def get_user_subscription(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's subscription.
    """
    subscription = crud.user_subscription.get_active_subscription(
        db, user_id=current_user.id
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )
    return subscription

@router.post("/subscribe", response_model=Transaction)
def subscribe(
    *,
    db: Session = Depends(deps.get_db),
    subscription_in: UserSubscriptionCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Subscribe to a plan.
    """
    # Get plan
    plan = crud.subscription_plan.get(db, id=subscription_in.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found or not active",
        )
    
    # Create transaction
    transaction = crud.transaction.create_transaction(
        db,
        user_id=current_user.id,
        transaction_type="subscription",
        amount=plan.price,
        currency=plan.currency,
        payment_method=subscription_in.payment_method,
        status="pending",
        subscription_id=plan.id,
        description=f"Subscription to {plan.name} plan"
    )
    
    # For demo purposes, we'll create subscription immediately
    # In a real app, this would happen after payment confirmation
    if subscription_in.payment_method == "demo":
        subscription = crud.user_subscription.create_subscription(
            db,
            user_id=current_user.id,
            plan_id=plan.id,
            auto_renew=subscription_in.auto_renew
        )
        
        # Add tokens if included
        if plan.tokens_included > 0:
            crud.user.update_token_balance(
                db, user_id=current_user.id, amount=plan.tokens_included
            )
        
        crud.transaction.update_transaction_status(
            db, 
            transaction_id=transaction.id, 
            status="completed",
            mpesa_receipt="DEMO123456"
        )
    
    return transaction

@router.post("/cancel", response_model=UserSubscription)
def cancel_subscription(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancel subscription.
    """
    subscription = crud.user_subscription.get_active_subscription(
        db, user_id=current_user.id
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )
    
    subscription = crud.user_subscription.cancel_subscription(
        db, subscription_id=subscription.id
    )
    
    return subscription
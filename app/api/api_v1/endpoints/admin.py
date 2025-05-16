
# File: backend/app/api/api_v1/endpoints/admin.py
# Status: UPDATED - Fixed imports
# Dependencies: fastapi, app.crud.user, app.crud.property, app.services.auth_service

from typing import Any, List
from sqlalchemy import func

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

# Direct imports from schema modules
from app.schemas.user import User
from app.schemas.verification import Verification
from app.schemas.property import Property

from app import crud, models
from app.api import deps

router = APIRouter()

@router.get("/users", response_model=List[User])
def get_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Retrieve users.
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/properties/pending-verification", response_model=List[Verification])
def get_pending_verifications(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get properties pending verification.
    """
    verifications = crud.verification.get_pending_verifications(
        db, skip=skip, limit=limit
    )
    return verifications

@router.put("/properties/{property_id}/verify", response_model=Property)
def verify_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    status: str = Body(..., embed=True),
    notes: str = Body(None, embed=True),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Verify a property.
    """
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Validate status
    valid_statuses = ["verified", "rejected", "pending_changes"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )
    
    # Update property verification status
    property = crud.property.update_verification_status(
        db, property_id=property_id, status=status
    )
    
    # Create verification history entry
    crud.verification.create_history_entry(
        db,
        property_id=property_id,
        status=status,
        verified_by=f"admin_{current_user.id}",
        notes=notes
    )
    
    # Check for active verifications and update
    verifications = crud.verification.get_property_verifications(
        db, property_id=property_id, skip=0, limit=5
    )
    
    for verification in verifications:
        if verification.status == "pending":
            crud.verification.admin_verify(
                db,
                verification_id=verification.id,
                admin_id=current_user.id,
                status=status,
                notes=notes
            )
    
    return property

@router.get("/stats", response_model=dict)
def get_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Get platform statistics.
    """
    # Count users
    total_users = db.query(models.User).count()
    tenant_users = db.query(models.User).filter(models.User.role == "tenant").count()
    owner_users = db.query(models.User).filter(models.User.role == "owner").count()
    
    # Count properties
    total_properties = db.query(models.Property).count()
    available_properties = db.query(models.Property).filter(
        models.Property.availability_status == "available"
    ).count()
    verified_properties = db.query(models.Property).filter(
        models.Property.verification_status == "verified"
    ).count()
    
    # Count transactions
    total_transactions = db.query(models.Transaction).count()
    completed_transactions = db.query(models.Transaction).filter(
        models.Transaction.status == "completed"
    ).count()
    
    # Calculate revenue (simplified for demo)
    revenue = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.status == "completed"
    ).scalar() or 0
    
    # Active subscriptions
    active_subscriptions = db.query(models.UserSubscription).filter(
        models.UserSubscription.end_date > datetime.utcnow()
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "tenants": tenant_users,
            "owners": owner_users
        },
        "properties": {
            "total": total_properties,
            "available": available_properties,
            "verified": verified_properties
        },
        "transactions": {
            "total": total_transactions,
            "completed": completed_transactions,
            "revenue": revenue
        },
        "subscriptions": {
            "active": active_subscriptions
        }
    }
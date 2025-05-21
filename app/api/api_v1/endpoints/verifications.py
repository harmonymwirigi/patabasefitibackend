# File: backend/app/api/api_v1/endpoints/verifications.py
# Status: COMPLETE
# Dependencies: fastapi, app.crud.verification, app.services.verification_service
from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta

from app.schemas.verification import Verification, VerificationCreate, VerificationUpdate, VerificationHistory
from app import crud, models
from app.api import deps


from app import crud, models, schemas
from app.services import file_service

router = APIRouter()
@router.get("/", response_model=List[Verification])
def get_verifications(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get verifications.
    """
    if crud.user.is_admin(current_user):
        # Admins can see all verifications
        verifications = crud.verification.get_multi(db, skip=skip, limit=limit)
    else:
        # Property owners can only see verifications for their properties
        verifications = db.query(models.Verification).\
            join(models.Property, models.Verification.property_id == models.Property.id).\
            filter(models.Property.owner_id == current_user.id).\
            offset(skip).limit(limit).all()
    
    return verifications

@router.post("/", response_model=Verification)
def create_verification(
    *,
    db: Session = Depends(deps.get_db),
    verification_in: VerificationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a verification request.
    """
    # Check if property exists and if user has permission
    property = crud.property.get(db, id=verification_in.property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Only owners or admins can create verification requests
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Create verification
    verification = crud.verification.create(db, obj_in=verification_in)
    return verification

@router.get("/property/{property_id}", response_model=List[Verification])
def get_property_verifications(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get verifications for a property.
    """
    # Check if property exists and if user has permission
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Only owners or admins can see verifications
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get verifications for property
    verifications = crud.verification.get_property_verifications(
        db, property_id=property_id, skip=skip, limit=limit
    )
    
    return verifications

@router.get("/history/{property_id}", response_model=List[VerificationHistory])
def get_verification_history(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get verification history for a property.
    """
    # Check if property exists and if user has permission
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Only owners or admins can see verification history
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get verification history
    history = db.query(models.VerificationHistory).filter(
        models.VerificationHistory.property_id == property_id
    ).order_by(models.VerificationHistory.timestamp.desc()).offset(skip).limit(limit).all()
    
    return history

@router.get("/pending", response_model=List[schemas.verification.Verification])
def get_pending_verifications(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_owner_user),
) -> Any:
    """
    Get pending verifications for properties owned by the current user.
    """
    # Get user's properties
    properties = crud.property.get_multi_by_owner(
        db, owner_id=current_user.id, skip=0, limit=1000
    )
    
    if not properties:
        return []
    
    property_ids = [prop.id for prop in properties]
    
    # Get pending verifications for these properties
    pending_verifications = []
    for property_id in property_ids:
        verifications = crud.verification.get_property_verifications(
            db, property_id=property_id, skip=0, limit=5
        )
        
        for verification in verifications:
            if verification.status == "pending":
                pending_verifications.append(verification)
    
    # Sort by requested_at and apply pagination
    pending_verifications.sort(key=lambda x: x.requested_at)
    
    return pending_verifications[skip:skip+limit]

@router.get("/{verification_id}", response_model=Verification)
def get_verification(
    *,
    db: Session = Depends(deps.get_db),
    verification_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get verification by ID.
    """
    verification = crud.verification.get(db, id=verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found",
        )
    
    # Get property
    property = crud.property.get(db, id=verification.property_id)
    
    # Check permissions
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return verification

@router.put("/{verification_id}", response_model=Verification)
def update_verification(
    *,
    db: Session = Depends(deps.get_db),
    verification_id: int,
    verification_in: VerificationUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a verification request.
    """
    verification = crud.verification.get(db, id=verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found",
        )
    
    # Get property
    property = crud.property.get(db, id=verification.property_id)
    
    # Check permissions - only admins can update verifications
    if not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Update verification
    verification = crud.verification.update(db, db_obj=verification, obj_in=verification_in)
    return verification

@router.post("/respond/{verification_id}", response_model=Verification)
def respond_to_verification(
    *,
    db: Session = Depends(deps.get_db),
    verification_id: int,
    response: str = Body(..., embed=True),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Respond to a verification request.
    """
    verification = crud.verification.get(db, id=verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found",
        )
    
    # Get property
    property = crud.property.get(db, id=verification.property_id)
    
    # Check permissions - only property owner can respond to verification
    if property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Update verification response
    response_data = {
        "owner_id": current_user.id,
        "response": response,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    verification_update = VerificationUpdate(
        responder_id=current_user.id,
        response_data=response_data
    )
    
    verification = crud.verification.update(db, db_obj=verification, obj_in=verification_update)
    
    # Create history entry
    crud.verification.create_history_entry(
        db,
        property_id=property.id,
        status="owner_responded",
        verified_by=f"owner_{current_user.id}",
        notes=f"Owner responded to verification request: {response[:100]}..."
    )
    
    return verification

@router.post("/request/{property_id}", response_model=Verification)
def request_verification(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    verification_type: str = Body(..., embed=True),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Request verification for a property.
    """
    # Check if property exists
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Set expiration date
    expiration = datetime.utcnow() + timedelta(days=7)
    
    # Create verification request
    verification_in = VerificationCreate(
        property_id=property_id,
        verification_type=verification_type,
        status="pending",
        expiration=expiration
    )
    
    verification = crud.verification.create(db, obj_in=verification_in)
    
    # Create history entry
    crud.verification.create_history_entry(
        db,
        property_id=property_id,
        status="verification_requested",
        verified_by=f"system",
        notes=f"Verification requested: {verification_type}"
    )
    
    return verification

@router.post("/{verification_id}/evidence", response_model=schemas.verification.Verification)
def upload_verification_evidence(
    *,
    db: Session = Depends(deps.get_db),
    verification_id: int,
    files: List[UploadFile] = File(...),
    current_user: models.User = Depends(deps.get_current_owner_user),
) -> Any:
    """
    Upload evidence for verification.
    """
    verification = crud.verification.get(db, id=verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found",
        )
    
    # Check if property belongs to user
    property = crud.property.get(db, id=verification.property_id)
    if not property or property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property not owned by current user",
        )
    
    # Save evidence files
    file_paths = file_service.save_multiple_uploads(files, folder=f"verification/{verification_id}")
    
    # Update verification response with file paths
    response = verification.response_json if verification.response else {}
    if "evidence_files" not in response:
        response["evidence_files"] = []
    
    response["evidence_files"].extend(file_paths)
    
    verification = crud.verification.update(
        db,
        db_obj=verification,
        obj_in={"response": response}
    )
    
    return verification
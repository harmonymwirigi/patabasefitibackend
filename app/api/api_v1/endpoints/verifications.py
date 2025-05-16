# File: backend/app/api/api_v1/endpoints/verifications.py
# Status: COMPLETE
# Dependencies: fastapi, app.crud.verification, app.services.verification_service
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services import file_service

router = APIRouter()

@router.get("/property/{property_id}", response_model=schemas.verification.Verification)
def get_property_verification(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get latest verification status for a property.
    """
    # Check if property exists
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Get latest verification
    verifications = crud.verification.get_property_verifications(
        db, property_id=property_id, skip=0, limit=1
    )
    
    if not verifications:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No verification requests found for this property",
        )
    
    return verifications[0]

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

@router.get("/{verification_id}", response_model=schemas.verification.Verification)
def get_verification(
    *,
    db: Session = Depends(deps.get_db),
    verification_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get verification details.
    """
    verification = crud.verification.get(db, id=verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found",
        )
    
    # Check if user has access (owner or admin)
    property = crud.property.get(db, id=verification.property_id)
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return verification

@router.post("/{verification_id}/respond", response_model=schemas.verification.Verification)
def respond_to_verification(
    *,
    db: Session = Depends(deps.get_db),
    verification_id: int,
    response: schemas.verification.VerificationResponse,
    current_user: models.User = Depends(deps.get_current_owner_user),
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
    
    # Check if property belongs to user
    property = crud.property.get(db, id=verification.property_id)
    if not property or property.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property not owned by current user",
        )
    
    # Check if verification is still pending
    if verification.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verification already {verification.status}",
        )
    
    # Update verification
    verification = crud.verification.respond_to_verification(
        db,
        verification_id=verification_id,
        responder_id=current_user.id,
        status=response.status,
        response={
            "status": response.status,
            "evidence": response.evidence,
            "notes": response.notes,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    # Update property status if needed
    if response.status in ["available", "rented", "unavailable"]:
        crud.property.update(
            db, 
            db_obj=property, 
            obj_in={"availability_status": response.status}
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
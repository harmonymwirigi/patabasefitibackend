# File: backend/app/api/api_v1/endpoints/properties.py
# Status: COMPLETE
# Dependencies: fastapi, app.crud.property, app.services.property_service, app.services.token_service
from typing import Any, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

# Direct imports from schemas
from app.schemas.property import PropertyCreate, Property, PropertyListItem, PropertyUpdate, PropertyImage, PropertySearch
from app import crud, models
from app.api import deps
from app.services import file_service
# Import property_service properly
from app.services.property_service import property_service
import json
import logging
router = APIRouter()
logger = logging.getLogger(__name__)
@router.get("/", response_model=List[PropertyListItem])
def read_properties(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve properties with pagination.
    """
    properties = crud.property.get_multi(db, skip=skip, limit=limit)
    return properties

@router.post("/", response_model=Property)
def create_property(
    *,
    db: Session = Depends(deps.get_db),
    property_in: PropertyCreate,
    current_user: models.User = Depends(deps.get_current_owner_user),
) -> Any:
    """
    Create new property.
    """
    try:
        # Use the service to handle JSON serialization properly
        property = property_service.create_property(
            db, property_data=property_in, owner_id=current_user.id
        )
        return property
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error creating property: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating property: {str(e)}"
        )

@router.get("/{property_id}", response_model=Property)
def read_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get property by ID.
    """
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Update view count
    crud.property.update_engagement_metrics(db, property_id=property_id, metric_type="view")
    
    # If user is logged in, check if property is in favorites
    if current_user:
        property_dict = jsonable_encoder(property)
        favorite = db.query(models.PropertyFavorite).filter(
            models.PropertyFavorite.user_id == current_user.id,
            models.PropertyFavorite.property_id == property_id
        ).first()
        property_dict["is_favorite"] = favorite is not None
        return property_dict
    
    return property

@router.put("/{property_id}", response_model=Property)
def update_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    property_in: PropertyUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a property.
    """
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    property = crud.property.update(db, db_obj=property, obj_in=property_in)
    return property

@router.delete("/{property_id}", response_model=Property)
def delete_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a property.
    """
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    property = crud.property.remove(db, id=property_id)
    return property

@router.post("/search", response_model=List[PropertyListItem])
def search_properties(
    *,
    db: Session = Depends(deps.get_db),
    search_params: PropertySearch,
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Search properties with filters.
    """
    # Check if user has tokens (if required)
    if current_user and current_user.token_balance <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Not enough tokens. Please purchase tokens to search properties.",
        )
    
    # Calculate pagination
    skip = (search_params.page - 1) * search_params.page_size
    limit = search_params.page_size
    
    # Search properties
    properties = crud.property.search(
        db,
        skip=skip,
        limit=limit,
        property_type=search_params.property_type,
        min_price=search_params.min_price,
        max_price=search_params.max_price,
        bedrooms=search_params.bedrooms,
        city=search_params.city,
        amenities=search_params.amenities,
        keyword=search_params.keyword,
        sort_by=search_params.sort_by
    )
    
    # Deduct token if user is logged in
    if current_user:
        crud.user.update_token_balance(db, user_id=current_user.id, amount=-1)
        
        # Save search history
        search_history = models.SearchHistory(
            user_id=current_user.id,
            parameters=json.dumps(search_params.dict()),
            results_count=len(properties),
            token_cost=1
        )
        db.add(search_history)
        db.commit()
    
    return properties

@router.get("/featured/list", response_model=List[PropertyListItem])
def get_featured_properties(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 10,
) -> Any:
    """
    Get featured properties.
    """
    properties = crud.property.get_featured(db, skip=skip, limit=limit)
    return properties

@router.post("/{property_id}/images", response_model=List[PropertyImage])
def upload_property_images(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    images: List[UploadFile] = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload property images.
    """
    logger.info(f"Uploading {len(images)} images for property {property_id}")
    
    # Verify property exists and user has permission
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Create folder structure for property images
    folder = f"properties/{property_id}"
    
    try:
        # Save images
        file_paths = file_service.save_multiple_uploads(images, folder=folder)
        logger.info(f"Saved {len(file_paths)} images for property {property_id}")
        
        # Add to database
        db_images = []
        for i, path in enumerate(file_paths):
            # Check if any image exists
            existing_images = db.query(models.PropertyImage).filter(
                models.PropertyImage.property_id == property_id
            ).count()
            
            is_primary = existing_images == 0 and i == 0
            
            db_image = models.PropertyImage(
                property_id=property_id,
                path=path,
                is_primary=is_primary
            )
            db.add(db_image)
            db_images.append(db_image)
        
        db.commit()
        
        # Refresh to get IDs
        for image in db_images:
            db.refresh(image)
        
        return db_images
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading images: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading images: {str(e)}"
        )
@router.put("/{property_id}/status", response_model=Property)
def update_property_status(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    availability_status: str = Body(..., embed=True),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update property availability status.
    """
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    if property.owner_id != current_user.id and not crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Validate status
    valid_statuses = ["available", "rented", "unavailable", "maintenance"]
    if availability_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )
    
    property = crud.property.update(
        db, 
        db_obj=property, 
        obj_in={"availability_status": availability_status}
    )
    
    # Create verification history entry
    crud.verification.create_history_entry(
        db,
        property_id=property_id,
        status=availability_status,
        verified_by=f"owner_{current_user.id}",
        notes=f"Status updated by owner to: {availability_status}"
    )
    
    return property

@router.post("/{property_id}/favorite", response_model=dict)
def add_to_favorites(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add property to favorites.
    """
    property = crud.property.get(db, id=property_id)
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )
    
    # Check if already favorited
    favorite = db.query(models.PropertyFavorite).filter(
        models.PropertyFavorite.user_id == current_user.id,
        models.PropertyFavorite.property_id == property_id
    ).first()
    
    if favorite:
        return {"success": True, "message": "Property already in favorites"}
    
    # Add to favorites
    favorite = models.PropertyFavorite(
        user_id=current_user.id,
        property_id=property_id
    )
    db.add(favorite)
    db.commit()
    
    # Update engagement metrics
    crud.property.update_engagement_metrics(db, property_id=property_id, metric_type="favorite")
    
    return {"success": True, "message": "Property added to favorites"}

@router.delete("/{property_id}/favorite", response_model=dict)
def remove_from_favorites(
    *,
    db: Session = Depends(deps.get_db),
    property_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Remove property from favorites.
    """
    favorite = db.query(models.PropertyFavorite).filter(
        models.PropertyFavorite.user_id == current_user.id,
        models.PropertyFavorite.property_id == property_id
    ).first()
    
    if not favorite:
        return {"success": True, "message": "Property not in favorites"}
    
    # Remove from favorites
    db.delete(favorite)
    db.commit()
    
    return {"success": True, "message": "Property removed from favorites"}
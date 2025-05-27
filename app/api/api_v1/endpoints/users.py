# File: backend/app/api/api_v1/endpoints/users.py
# Status: FIXED
# Dependencies: fastapi, app.crud.user, app.services.user_service

from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.schemas.user import User, UserUpdate
from app import crud, models
from app.api import deps
from app.services import file_service
from app.services.user_service import user_service
from typing import Any, List, Optional
from sqlalchemy import or_, func
router = APIRouter()

@router.get("/me", response_model=User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    # Use user_service to get a fully formatted user profile
    user_data = user_service.get_user_profile(db, current_user.id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user_data

@router.get("/search", response_model=List[User])
def search_users(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, le=50, description="Maximum number of results")
) -> Any:
    """
    Search users by name or email.
    """
    try:
        # Search users by full name or email (case insensitive)
        search_term = f"%{q.lower()}%"
        
        users = db.query(models.User).filter(
            and_(
                models.User.id != current_user.id,  # Exclude current user
                models.User.account_status == "active",  # Only active users
                or_(
                    func.lower(models.User.full_name).like(search_term),
                    func.lower(models.User.email).like(search_term)
                )
            )
        ).limit(limit).all()
        
        return users
        
    except Exception as e:
        print(f"Error searching users: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching users"
        )

@router.get("/by-role/{role}", response_model=List[User])
def get_users_by_role(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    role: str,
    limit: int = Query(20, le=100, description="Maximum number of results")
) -> Any:
    """
    Get users by role.
    """
    try:
        valid_roles = ["tenant", "owner", "admin"]
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        users = db.query(models.User).filter(
            and_(
                models.User.role == role,
                models.User.account_status == "active",
                models.User.id != current_user.id  # Exclude current user
            )
        ).limit(limit).all()
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting users by role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update current user.
    """
    try:
        # Convert Pydantic model to dict
        update_data = user_in.dict(exclude_unset=True)
        
        # Use user_service to update the user with proper JSON serialization
        updated_user = user_service.update_user_profile(db, current_user.id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Return the formatted user profile
        return user_service.get_user_profile(db, updated_user.id)
    except Exception as e:
        print(f"Error updating user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.post("/me/profile-image", response_model=User)
def upload_profile_image(
    *,
    db: Session = Depends(deps.get_db),
    profile_image: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload profile image.
    """
    try:
        # Save image
        file_path = file_service.save_upload(profile_image, folder="profile")
        
        # Update user with direct SQL to avoid JSON serialization issues
        updated_user = user_service.update_user_profile(
            db, 
            current_user.id, 
            {"profile_image": file_path}
        )
        
        # Return the formatted user profile
        return user_service.get_user_profile(db, updated_user.id)
    except Exception as e:
        print(f"Error uploading profile image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading profile image: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific user by id.
    """
    user_data = user_service.get_user_profile(db, user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user_data

@router.put("/me/notification-preferences", response_model=dict)
def update_notification_preferences(
    *,
    db: Session = Depends(deps.get_db),
    preferences: dict = Body(...),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update notification preferences.
    """
    try:
        result = user_service.change_notification_preferences(db, current_user.id, preferences)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )
        return result
    except Exception as e:
        print(f"Error updating notification preferences: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating notification preferences: {str(e)}"
        )
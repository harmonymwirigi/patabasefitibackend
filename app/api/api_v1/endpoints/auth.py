# File: backend/app/api/api_v1/endpoints/auth.py
# Updated to handle role selection for Google users

from datetime import timedelta
from typing import Any, Dict
import json
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy import text

from app import crud, models
from app.api import deps
from app.core import security
from app.core.config import settings
from app.db.database import get_db
from app.services.user_service import user_service

# Import specific schema modules directly
from app.schemas.user import UserCreate, UserWithToken, User
from app.schemas.token import Token, GoogleToken, TokenResponse
from app.schemas.auth import GoogleAuthWithRole, GoogleVerifyResponse

router = APIRouter()

@router.post("/register", response_model=UserWithToken)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user.
    """
    # Check if user with this email already exists
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    try:
        # Set auth_type to "email" for regular registration
        user_in_dict = user_in.dict()
        user_in_dict["auth_type"] = "email"
        user_in = UserCreate(**user_in_dict)
        
        # Create new user
        user = crud.user.create(db, obj_in=user_in)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        # Update last login - using the user_service to avoid JSON serialization issues
        user_service.update_last_login(db, user_id=user.id)
        
        # Get formatted user data
        user_dict = user_service.get_user_profile(db, user.id)
        
        return {
            "user": user_dict,
            "token": {
                "access_token": access_token,
                "token_type": "bearer"
            }
        }
    except Exception as e:
        print(f"Error in register: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=UserWithToken)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        user = crud.user.authenticate(
            db, email=form_data.username, password=form_data.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not crud.user.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Inactive user"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        # Update last login - using the user_service to avoid JSON serialization issues
        user_service.update_last_login(db, user_id=user.id)
        
        # Get formatted user data
        user_dict = user_service.get_user_profile(db, user.id)
        
        return {
            "user": user_dict,
            "token": {
                "access_token": access_token,
                "token_type": "bearer"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in login: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during login: {str(e)}"
        )

@router.post("/google/verify", response_model=Dict[str, Any])
async def google_verify_token(
    token: GoogleToken,
    db: Session = Depends(get_db)
):
    """
    Verify Google token and return user info.
    If user exists, return user data. If not, return user info for role selection.
    """
    try:
        print(f"Verifying Google token: {token.token[:15]}...")
        
        # Verify Google token
        try:
            req = requests.Request()
            idinfo = id_token.verify_oauth2_token(
                token.token, 
                req, 
                settings.GOOGLE_CLIENT_ID
            )
            print(f"Token verified successfully. Email: {idinfo.get('email')}")
            
        except Exception as token_error:
            print(f"Token verification error: {str(token_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(token_error)}",
            )
        
        # Extract user info from token
        email = idinfo.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token",
            )
        
        # Check if user exists
        user = crud.user.get_by_email(db, email=email)
        
        if user:
            # User exists, return success with user data
            return {
                "user_exists": True,
                "user_info": {
                    "email": email,
                    "name": idinfo.get("name", "Google User"),
                    "picture": idinfo.get("picture"),
                    "google_id": idinfo.get("sub")
                },
                "user_data": user_service.get_user_profile(db, user.id)
            }
        else:
            # User doesn't exist, return user info for role selection
            return {
                "user_exists": False,
                "user_info": {
                    "email": email,
                    "name": idinfo.get("name", "Google User"),
                    "picture": idinfo.get("picture"),
                    "google_id": idinfo.get("sub")
                },
                "needs_role_selection": True
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in google_verify_token: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying Google token: {str(e)}",
        )

@router.post("/google/complete", response_model=TokenResponse)
async def google_complete_registration(
    auth_data: GoogleAuthWithRole,
    db: Session = Depends(get_db)
):
    """
    Complete Google authentication with role selection.
    """
    try:
        print(f"Completing Google auth with role: {auth_data.role}")
        
        # Verify Google token again
        try:
            req = requests.Request()
            idinfo = id_token.verify_oauth2_token(
                auth_data.token, 
                req, 
                settings.GOOGLE_CLIENT_ID
            )
        except Exception as token_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(token_error)}",
            )
        
        email = idinfo.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token",
            )
        
        # Validate role
        if auth_data.role not in ['tenant', 'owner']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'tenant' or 'owner'",
            )
        
        # Check if user exists
        user = crud.user.get_by_email(db, email=email)
        
        if not user:
            # Create new user with selected role
            print(f"Creating new user with role: {auth_data.role}")
            
            # Generate a random password for the user
            random_password = security.generate_random_password()
            
            # Create a UserCreate object with proper fields
            user_in = UserCreate(
                email=email,
                full_name=idinfo.get("name", "Google User"),
                password=random_password,
                role=auth_data.role,  # Use the selected role
            )
            
            # Create the user
            user = crud.user.create(db, obj_in=user_in)
            
            # Update the auth_type using direct SQL
            sql = text("UPDATE users SET auth_type = :auth_type, google_id = :google_id WHERE id = :user_id")
            db.execute(sql, {
                "auth_type": "google",
                "google_id": idinfo.get("sub"),
                "user_id": user.id
            })
            db.commit()
            
            print(f"New user created with ID: {user.id} and role: {auth_data.role}")
        
        # Create access token
        access_token = security.create_access_token(user.id)
        
        # Update last login
        user_service.update_last_login(db, user_id=user.id)
        
        # Get user profile
        user_dict = user_service.get_user_profile(db, user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name, 
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in google_complete_registration: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing Google authentication: {str(e)}",
        )

@router.post("/google", response_model=TokenResponse)
async def google_auth(
    token: GoogleToken,
    db: Session = Depends(get_db)
):
    """
    Legacy Google auth endpoint for existing users.
    """
    try:
        # First verify the token
        verify_response = await google_verify_token(token, db)
        
        if verify_response["user_exists"]:
            # User exists, complete login
            user_data = verify_response["user_data"]
            
            # Create access token
            access_token = security.create_access_token(user_data["id"])
            
            # Update last login
            user_service.update_last_login(db, user_id=user_data["id"])
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "full_name": user_data["full_name"], 
                    "role": user_data["role"]
                }
            }
        else:
            # User doesn't exist, need role selection
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New user detected. Please use the role selection flow.",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in google_auth: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing Google authentication: {str(e)}",
        )

@router.post("/logout")
def logout() -> Any:
    """
    Logout endpoint (client-side only for JWT tokens).
    """
    return {"message": "Logged out successfully"}

@router.options("/register", include_in_schema=False)
async def options_register():
    return {}

@router.options("/login", include_in_schema=False)
async def options_login():
    return {}

@router.options("/google", include_in_schema=False)
async def options_google():
    return {}

@router.options("/google/verify", include_in_schema=False)
async def options_google_verify():
    return {}

@router.options("/google/complete", include_in_schema=False)
async def options_google_complete():
    return {}

@router.options("/logout", include_in_schema=False)
async def options_logout():
    return {}
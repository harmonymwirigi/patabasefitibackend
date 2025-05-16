# File: backend/app/services/auth_service.py
# Status: FIXED
# Dependencies: jwt, app.core.security, app.crud.user, app.schemas.auth, app.models

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.crud.user import user as user_crud
from app.db.database import get_db
from app import models
from app.schemas.auth import TokenPayload
from app.schemas.user import OAuthUserCreate

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

class AuthService:
    @staticmethod
    def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a new JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode = {"exp": expire, "sub": str(subject)}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def get_current_user(
        db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
    ) -> models.User:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            
            if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
                raise credentials_exception
                
        except JWTError:
            raise credentials_exception
            
        user = user_crud.get(db, id=token_data.sub)
        if not user:
            raise credentials_exception
            
        if not user_crud.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
            
        return user
    
    @staticmethod
    def get_current_active_user(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        """Get current active user"""
        if not user_crud.is_active(current_user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        return current_user
    
    @staticmethod
    def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a Google OAuth token and extract user information
        
        This is a simplified implementation. In production, you should validate the token
        with Google's tokeninfo endpoint or use the google-auth library.
        """
        try:
            # For development/testing purposes, return dummy data
            # In production, replace this with actual Google token verification
            
            # This is a placeholder - replace with actual Google token verification
            user_info = {
                "sub": "google123456",  # Google user ID
                "email": "testuser@example.com",
                "name": "Test User",
                "picture": "https://example.com/profile.jpg"
            }
            
            return user_info
            
        except Exception as e:
            # Log the error
            import logging
            logging.error(f"Error verifying Google token: {str(e)}")
            return None
    
    @staticmethod
    def get_current_admin_user(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        """Get current admin user"""
        if not user_crud.is_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges"
            )
        return current_user
    
    @staticmethod
    def process_google_auth(
        db: Session, user_info: Dict[str, Any]
    ) -> models.User:
        """Process Google OAuth authentication"""
        # Check if user exists with Google ID
        user = user_crud.get_by_google_id(db, google_id=user_info.get("id"))
        
        # If user exists, return the user
        if user:
            # Update last login time
            user.last_login = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        # Check if user exists with email
        user = user_crud.get_by_email(db, email=user_info.get("email"))
        
        # If user exists with email but no Google ID, link accounts
        if user:
            user.google_id = user_info.get("id")
            user.last_login = datetime.utcnow()
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        # Create new user with Google information
        user_data = OAuthUserCreate(
            email=user_info.get("email"),
            full_name=user_info.get("name"),
            google_id=user_info.get("id"),
            profile_image=user_info.get("picture"),
            role="tenant"  # Default role for new users
        )
        
        return user_crud.create_oauth_user(db, obj_in=user_data)

auth_service = AuthService()
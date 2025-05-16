# File: backend/app/core/dependencies.py
# Status: COMPLETE
# Dependencies: fastapi, python-jose, app.schemas, app.core.config, app.db.database
from typing import Generator, Optional
import json

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User
from app.core.config import settings
from app.core.security import verify_password
from app.schemas.token import TokenPayload
from app.crud.user import user as user_crud

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = user_crud.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user account"
        )
        
    # Convert JSON string fields to dictionaries
    if hasattr(user, 'notification_preferences') and isinstance(user.notification_preferences, str):
        try:
            user.notification_preferences = json.loads(user.notification_preferences)
        except:
            user.notification_preferences = {"email": True, "sms": True, "in_app": True}
            
    if hasattr(user, 'token_history') and isinstance(user.token_history, str):
        try:
            user.token_history = json.loads(user.token_history)
        except:
            user.token_history = []
            
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

def get_current_owner_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions (owner role required)"
        )
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions (admin role required)"
        )
    return current_user
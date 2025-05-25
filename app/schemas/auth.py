# File: backend/app/schemas/auth.py
# Updated to include GoogleAuthWithRole

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from app.schemas.base import BaseSchema

# Token data
class Token(BaseSchema):
    access_token: str
    token_type: str

# Token payload data
class TokenPayload(BaseSchema):
    sub: Optional[int] = None

# Email and password login
class Login(BaseSchema):
    email: EmailStr
    password: str

# Password change/reset
class PasswordChange(BaseSchema):
    current_password: str
    new_password: str

# Password reset request
class PasswordResetRequest(BaseSchema):
    email: EmailStr

# Password reset
class PasswordReset(BaseSchema):
    token: str
    new_password: str

# Google OAuth authentication request
class GoogleAuthRequest(BaseSchema):
    token: str

# Google OAuth authentication with role selection
class GoogleAuthWithRole(BaseSchema):
    token: str
    role: str
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ["tenant", "owner"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return v

# Google token verification response
class GoogleVerifyResponse(BaseSchema):
    user_exists: bool
    user_info: dict
    needs_role_selection: Optional[bool] = None
    user_data: Optional[dict] = None
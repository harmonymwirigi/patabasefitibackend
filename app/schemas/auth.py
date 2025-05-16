# File: backend/app/schemas/auth.py
# Status: UPDATED - Added GoogleAuthRequest
# Dependencies: pydantic, app.schemas.base

from pydantic import BaseModel, EmailStr
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
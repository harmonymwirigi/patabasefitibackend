# File: backend/app/schemas/token.py
# Status: UPDATED - Added missing response schemas
# Dependencies: pydantic, app.schemas.base
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None


class GoogleToken(BaseModel):
    """Schema for Google authentication token"""
    token: str = Field(..., description="Google ID token")

class TokenData(BaseModel):
    """Schema for decoded JWT token data"""
    sub: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    user: Dict[str, Any]
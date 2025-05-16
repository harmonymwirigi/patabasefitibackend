# File: backend/app/schemas/user.py
# Updated User schema to match the database model

from typing import Optional, Dict, List, Any
import datetime
import json
from pydantic import BaseModel, EmailStr, validator, ConfigDict

from app.schemas.token import Token

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None
    profile_image: Optional[str] = None
    auth_type: Optional[str] = None  # Added auth_type field

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str
    role: str
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ["tenant", "owner", "admin"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return v

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    email: EmailStr
    auth_type: str  # Required field
    role: str
    full_name: str
    token_balance: int
    reliability_score: Optional[float] = None
    account_status: str
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None
    notification_preferences: Dict[str, bool]
    google_id: Optional[str] = None  # Added google_id field if your model has it
    
    model_config = ConfigDict(from_attributes=True)
    
    @validator('notification_preferences', pre=True)
    def parse_notification_preferences(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {"email": True, "sms": True, "in_app": True}
        return v

# Properties to return via API
class User(UserInDBBase):
    pass

# Properties stored in DB but not returned via API
class UserInDB(UserInDBBase):
    hashed_password: Optional[str] = None
    token_history: List[Any]
    
    @validator('token_history', pre=True)
    def parse_token_history(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        return v

# Response for login
class UserWithToken(BaseModel):
    user: User
    token: Token

# For token payload
class UserInToken(BaseModel):
    id: int
    email: EmailStr
    role: str
    
    model_config = ConfigDict(from_attributes=True)
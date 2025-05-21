# File: backend/app/schemas/verification.py
# Status: COMPLETE
# Dependencies: pydantic, app.schemas.base
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime
import json
from app.schemas.base import BaseSchema, TimestampedSchema
# Verification model
class VerificationBase(BaseSchema):
    property_id: int
    verification_type: str
    status: str = "pending"
    expiration: Optional[datetime] = None
    
    # JSON Fields that need special handling
    response_data: Optional[Union[Dict[str, Any], str]] = None
    system_decision: Optional[Union[Dict[str, Any], str]] = None
    
    # Validators for JSON fields that might come as strings
    @validator('response_data', pre=True)
    def parse_response_data(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

# For creating a new verification request
class VerificationCreate(VerificationBase):
    pass


# For updating a verification
class VerificationUpdate(BaseSchema):
    status: Optional[str] = None
    responder_id: Optional[int] = None
    expiration: Optional[datetime] = None
    response_data: Optional[Union[Dict[str, Any], str]] = None
    system_decision: Optional[Union[Dict[str, Any], str]] = None
    
    # Validators for JSON fields
    @validator('response_data', pre=True)
    def parse_response_data(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @validator('system_decision', pre=True)
    def parse_system_decision(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v
class VerificationOwner(BaseSchema):
    id: int
    full_name: str
    email: str

class VerificationProperty(BaseSchema):
    id: int
    title: str
    property_type: str
    rent_amount: float
    bedrooms: int
    bathrooms: int
    address: str
    city: str
    neighborhood: Optional[str] = None
    owner: Optional[VerificationOwner] = None
    
    # Include simplified images array
    images: List[Dict[str, Any]] = []
# Verification in DB with all properties
class VerificationInDBBase(VerificationBase):
    id: int
    property_id: int
    requested_at: datetime
    status: str
    responder_id: Optional[int] = None
    expiration: Optional[datetime] = None
    system_decision: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

# Verification to return via API
class Verification(TimestampedSchema):
    id: int
    property_id: int
    verification_type: str
    requested_at: datetime
    status: str
    responder_id: Optional[int] = None
    expiration: Optional[datetime] = None
    
    # Include the property with key fields
    property: Optional[VerificationProperty] = None
    
    # JSON fields with parsing
    response_data: Dict[str, Any] = {}
    system_decision: Dict[str, Any] = {}
    
    # Validators for JSON fields
    @validator('response_data', pre=True)
    def parse_response_data(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @validator('system_decision', pre=True)
    def parse_system_decision(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    class Config:
        orm_mode = True

# Verification history
class VerificationHistory(BaseSchema):
    id: int
    property_id: int
    status: str
    verified_by: str
    timestamp: datetime
    notes: Optional[str] = None

    class Config:
        orm_mode = True

# Verification response from the property owner
class VerificationResponse(BaseModel):
    status: str
    evidence: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "available",
                "evidence": {"photo_verification": True},
                "notes": "Property is currently available for rent"
            }
        }
    )
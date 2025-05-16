# File: backend/app/schemas/verification.py
# Status: COMPLETE
# Dependencies: pydantic, app.schemas.base
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
import datetime

# Verification model
class VerificationBase(BaseModel):
    verification_type: str
    response: Optional[Dict[str, Any]] = None

# For creating a new verification request
class VerificationCreate(VerificationBase):
    property_id: int

# For updating a verification
class VerificationUpdate(BaseModel):
    status: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    system_decision: Optional[Dict[str, Any]] = None

# Verification in DB with all properties
class VerificationInDBBase(VerificationBase):
    id: int
    property_id: int
    requested_at: datetime.datetime
    status: str
    responder_id: Optional[int] = None
    expiration: Optional[datetime.datetime] = None
    system_decision: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

# Verification to return via API
class Verification(VerificationInDBBase):
    property_title: Optional[str] = None
    responder_name: Optional[str] = None

# Verification history
class VerificationHistory(BaseModel):
    id: int
    property_id: int
    status: str
    verified_by: str
    timestamp: datetime.datetime
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

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
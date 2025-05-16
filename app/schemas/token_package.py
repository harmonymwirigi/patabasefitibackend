from typing import Optional, List
from pydantic import BaseModel
import datetime

# Shared properties
class TokenPackageBase(BaseModel):
    name: Optional[str] = None
    token_count: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    duration_days: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

# Properties to receive via API on creation
class TokenPackageCreate(TokenPackageBase):
    name: str
    token_count: int
    price: float
    currency: str = "KES"

# Properties to receive via API on update
class TokenPackageUpdate(TokenPackageBase):
    pass

# Properties shared by models stored in DB
class TokenPackageInDBBase(TokenPackageBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    class Config:
        orm_mode = True

# Properties to return via API
class TokenPackage(TokenPackageInDBBase):
    pass

# Token purchase request
class TokenPurchase(BaseModel):
    package_id: int
    payment_method: str
    
    class Config:
        schema_extra = {
            "example": {
                "package_id": 1,
                "payment_method": "mpesa"
            }
        }
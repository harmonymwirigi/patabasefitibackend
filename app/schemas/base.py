# File: backend/app/schemas/base.py
# Status: COMPLETE
# Dependencies: pydantic

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BaseSchema(BaseModel):
    """Base schema with common fields"""
    class Config:
        from_attributes = True

class TimestampedSchema(BaseSchema):
    """Base schema with timestamp fields"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
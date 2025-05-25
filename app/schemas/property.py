# File: backend/app/schemas/property.py

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json
from pydantic import BaseModel, Field, validator

from app.schemas.base import BaseSchema, TimestampedSchema

# Property Base Schema
class PropertyBase(BaseSchema):
    title: str
    description: Optional[str] = None
    property_type: str
    rent_amount: float
    bedrooms: int
    bathrooms: int
    size_sqm: Optional[float] = None
    address: str
    neighborhood: Optional[str] = None
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    availability_status: Optional[str] = "available"
    
    # JSON Fields that need special handling
    amenities: Optional[Union[List[str], str]] = []
    lease_terms: Optional[Union[Dict[str, Any], str]] = {}
    auto_verification_settings: Optional[Union[Dict[str, Any], str]] = {"enabled": True, "frequency_days": 7}
    
    # Validators for JSON fields that might come as strings
    @validator('amenities', pre=True)
    def parse_amenities(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    @validator('lease_terms', pre=True)
    def parse_lease_terms(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @validator('auto_verification_settings', pre=True)
    def parse_auto_verification(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"enabled": True, "frequency_days": 7}
        return v

# Property Create Schema
class PropertyCreate(PropertyBase):
    pass

# Property Update Schema
class PropertyUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    rent_amount: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqm: Optional[float] = None
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    availability_status: Optional[str] = None
    verification_status: Optional[str] = None
    expiration_date: Optional[datetime] = None
    
    # JSON Fields that need special handling
    amenities: Optional[Union[List[str], str]] = None
    lease_terms: Optional[Union[Dict[str, Any], str]] = None
    auto_verification_settings: Optional[Union[Dict[str, Any], str]] = None
    
    # Validators for JSON fields that might come as strings
    @validator('amenities', pre=True)
    def parse_amenities(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    @validator('lease_terms', pre=True)
    def parse_lease_terms(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @validator('auto_verification_settings', pre=True)
    def parse_auto_verification(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"enabled": True, "frequency_days": 7}
        return v

# Property in DB
class Property(TimestampedSchema):
    id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    property_type: str
    rent_amount: float
    bedrooms: int
    bathrooms: int
    size_sqm: Optional[float] = None
    address: str
    neighborhood: Optional[str] = None
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    landmark: Optional[str] = None
    availability_status: str
    verification_status: str
    reliability_score: Optional[float] = None
    last_verified: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    
    # JSON fields with parsing
    amenities: List[str] = []
    lease_terms: Dict[str, Any] = {}
    engagement_metrics: Dict[str, Any] = {"view_count": 0, "favorite_count": 0, "contact_count": 0}
    auto_verification_settings: Dict[str, Any] = {"enabled": True, "frequency_days": 7}
    featured_status: Dict[str, Any] = {"is_featured": False}
    
    # Field added by endpoint for user convenience
    is_favorite: Optional[bool] = False
    
    # Validators for JSON fields
    @validator('amenities', pre=True)
    def parse_amenities(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    @validator('lease_terms', pre=True)
    def parse_lease_terms(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    @validator('engagement_metrics', pre=True)
    def parse_engagement_metrics(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"view_count": 0, "favorite_count": 0, "contact_count": 0}
        return v

    @validator('auto_verification_settings', pre=True)
    def parse_auto_verification(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"enabled": True, "frequency_days": 7}
        return v

    @validator('featured_status', pre=True)
    def parse_featured_status(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {"is_featured": False}
        return v

# Property List Item
class PropertyListItem(BaseSchema):
    id: int
    title: str
    property_type: str
    rent_amount: float
    bedrooms: int
    bathrooms: int
    city: str
    neighborhood: Optional[str] = None
    availability_status: str
    verification_status: str
    
    # Main image will be populated by frontend from the images relationship
    main_image: Optional[str] = None
    
    # Parse amenities for the list view
    amenities: List[str] = []
    
    @validator('amenities', pre=True)
    def parse_amenities(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v
    
    class Config:
        orm_mode = True
        from_attributes = True

# Property Image
class PropertyImage(BaseSchema):
    id: int
    property_id: int
    path: str
    description: Optional[str] = None
    is_primary: bool
    uploaded_at: datetime

# Property Search Parameters
class PropertySearch(BaseSchema):
    property_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    city: Optional[str] = None
    amenities: Optional[List[str]] = None
    keyword: Optional[str] = None
    sort_by: Optional[str] = "newest"  # newest, price_low, price_high
    page: int = 1
    page_size: int = 10
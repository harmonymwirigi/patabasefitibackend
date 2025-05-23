# File: backend/app/schemas/analytics.py
# Status: UPDATED - Added SystemStatsResponse
# Dependencies: pydantic, app.schemas.base

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.schemas.base import BaseSchema, TimestampedSchema

class AdminStats(BaseModel):
    users: Dict[str, int]
    properties: Dict[str, int]
    transactions: Dict[str, Any]
    subscriptions: Dict[str, int]
    
    class Config:
        orm_mode = True

class NeighborhoodCount(BaseModel):
    name: str
    count: int

class PropertyTypeCount(BaseModel):
    type: str
    count: int

class PropertyAnalytics(BaseModel):
    newPropertiesCount: int
    popularNeighborhoods: List[NeighborhoodCount]
    propertyTypes: List[PropertyTypeCount]
    
    class Config:
        orm_mode = True

class RegistrationTrendPoint(BaseModel):
    date: str
    tenants: int
    owners: int

class UserRoleCount(BaseModel):
    role: str
    count: int

class UserAnalytics(BaseModel):
    activeUsers: int
    registrationTrend: List[RegistrationTrendPoint]
    usersByRole: List[UserRoleCount]
    
    class Config:
        orm_mode = True
class RevenueTrendPoint(BaseModel):
    date: str
    amount: float

class RevenueSourceAmount(BaseModel):
    source: str
    amount: float

class RevenueAnalytics(BaseModel):
    revenueTrend: List[RevenueTrendPoint]
    revenueBySource: List[RevenueSourceAmount]
    
    class Config:
        orm_mode = True
# Search history
class SearchHistory(BaseSchema):
    id: int
    user_id: int
    parameters: Dict[str, Any]
    results_count: int
    token_cost: int
    timestamp: datetime

# Viewed property
class ViewedProperty(BaseSchema):
    id: int
    user_id: int
    property_id: int
    last_viewed: datetime
    view_count: int

# Property favorite
class PropertyFavorite(BaseSchema):
    id: int
    user_id: int
    property_id: int
    created_at: datetime

# Analytics event
class AnalyticsEvent(BaseSchema):
    id: int
    event_type: str
    user_id: Optional[int] = None
    property_id: Optional[int] = None
    session_id: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any]
    location: Optional[Dict[str, Any]] = None

# Analytics dashboard data
class AnalyticsDashboard(BaseSchema):
    user_count: int
    property_count: int
    active_property_count: int
    total_searches: int
    total_tokens_purchased: int
    total_revenue: float
    recent_activity: List[Dict[str, Any]]
    popular_properties: List[Dict[str, Any]]
    active_users: List[Dict[str, Any]]
    search_trends: List[Dict[str, Any]]

# System statistics response for admin dashboard
class SystemStatsResponse(BaseSchema):
    users: Dict[str, Any]  # Total and by role
    properties: Dict[str, Any]  # Total and by status
    tokens: Dict[str, Any]  # Total sold and revenue
    recent_transactions: List[Dict[str, Any]]  # Recent token transactions
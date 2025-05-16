# File: backend/app/schemas/search.py
# Status: NEW
# Dependencies: pydantic, app.schemas.base

from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema, TimestampedSchema

class SearchHistoryBase(BaseSchema):
    """Base schema for search history"""
    user_id: int
    parameters: Dict[str, Any]
    results_count: int = 0
    token_cost: int = 1

class SearchHistoryCreate(SearchHistoryBase):
    """Schema for creating search history records"""
    pass

class SearchHistoryUpdate(BaseSchema):
    """Schema for updating search history records"""
    parameters: Optional[Dict[str, Any]] = None
    results_count: Optional[int] = None
    token_cost: Optional[int] = None

class SearchHistoryResponse(SearchHistoryBase, TimestampedSchema):
    """Schema for search history response"""
    id: int
    timestamp: datetime

class SearchSuggestionResponse(BaseSchema):
    """Schema for search suggestions"""
    suggestions: List[Dict[str, Any]]
    popular_searches: List[Dict[str, Any]]
# File: backend/app/crud/search_history.py
# Status: NEW
# Dependencies: sqlalchemy, app.models.analytics, app.schemas.search, app.crud.base

from typing import List, Optional
from sqlalchemy.orm import Session
from app import models
from app.schemas.search import SearchHistoryCreate, SearchHistoryUpdate
from .base import CRUDBase

class CRUDSearchHistory(CRUDBase[models.SearchHistory, SearchHistoryCreate, SearchHistoryUpdate]):
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.SearchHistory]:
        """Get search history by user ID"""
        return (
            db.query(self.model)
            .filter(models.SearchHistory.user_id == user_id)
            .order_by(models.SearchHistory.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recent_searches(
        self, db: Session, *, user_id: int, limit: int = 5
    ) -> List[models.SearchHistory]:
        """Get most recent searches for a user"""
        return (
            db.query(self.model)
            .filter(models.SearchHistory.user_id == user_id)
            .order_by(models.SearchHistory.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_popular_searches(
        self, db: Session, *, limit: int = 10
    ) -> List[dict]:
        """Get most popular search parameters across all users"""
        # This is a complex query that groups by parameters and counts occurrences
        # For SQLite, we'll use a simplified approach
        query = """
            SELECT parameters, COUNT(*) as search_count
            FROM search_history
            GROUP BY parameters
            ORDER BY search_count DESC
            LIMIT :limit
        """
        result = db.execute(query, {"limit": limit}).fetchall()
        
        # Format results
        return [
            {"parameters": row[0], "count": row[1]}
            for row in result
        ]

    def delete_user_history(self, db: Session, *, user_id: int) -> int:
        """Delete all search history for a user"""
        deleted = db.query(self.model).filter(
            models.SearchHistory.user_id == user_id
        ).delete()
        db.commit()
        return deleted

# Create singleton instance
search_history = CRUDSearchHistory(models.SearchHistory)
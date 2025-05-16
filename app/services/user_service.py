# File: backend/app/services/user_service.py
# Updated to include auth_type in the user profile

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from app.models import User
from app.core.security import get_password_hash

class UserService:
    def get_user_profile(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get user profile with properly parsed JSON fields
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User profile dictionary
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Parse JSON fields
        try:
            if isinstance(user.notification_preferences, str):
                notification_prefs = json.loads(user.notification_preferences)
            else:
                notification_prefs = user.notification_preferences or {"email": True, "sms": True, "in_app": True}
        except:
            notification_prefs = {"email": True, "sms": True, "in_app": True}
        
        try:
            if isinstance(user.token_history, str):
                token_history = json.loads(user.token_history)
            else:
                token_history = user.token_history or []
        except:
            token_history = []
        
        # Include all required fields from the User Pydantic model
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "phone_number": user.phone_number,
            "profile_image": user.profile_image,
            "token_balance": user.token_balance,
            "notification_preferences": notification_prefs,
            "token_history": token_history,
            "account_status": user.account_status,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "auth_type": user.auth_type,  # Added this field
            "google_id": user.google_id   # Add this if it's in your User model
        }
    
    def update_user_profile(
        self,
        db: Session,
        user_id: int,
        data: Dict[str, Any]
    ) -> Optional[User]:
        """
        Update user profile with proper JSON serialization
        
        Args:
            db: Database session
            user_id: User ID
            data: Update data
            
        Returns:
            Updated user or None if user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Create a dictionary of fields to update
        update_values = {}
        
        # Handle password separately
        if "password" in data and data["password"]:
            update_values["hashed_password"] = get_password_hash(data["password"])
        
        # Copy non-special fields
        for field in ["full_name", "phone_number", "profile_image", "role", "account_status"]:
            if field in data and data[field] is not None:
                update_values[field] = data[field]
        
        # Handle notification_preferences
        if "notification_preferences" in data and data["notification_preferences"] is not None:
            # Ensure it's stored as a JSON string
            if isinstance(data["notification_preferences"], dict):
                update_values["notification_preferences"] = json.dumps(data["notification_preferences"])
            elif isinstance(data["notification_preferences"], str):
                # Try to validate it's a valid JSON string
                try:
                    json.loads(data["notification_preferences"])
                    update_values["notification_preferences"] = data["notification_preferences"]
                except:
                    # Not valid JSON, store a default
                    update_values["notification_preferences"] = json.dumps({"email": True, "sms": True, "in_app": True})
        
        # Add updated_at timestamp
        update_values["updated_at"] = datetime.utcnow()
        
        # Construct SQL update statement with parameters
        if update_values:
            # Create the SET clause for the SQL statement
            set_clauses = []
            params = {"user_id": user_id}
            
            for key, value in update_values.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
            
            set_clause = ", ".join(set_clauses)
            
            # Create and execute the SQL statement
            sql = text(f"UPDATE users SET {set_clause} WHERE id = :user_id")
            db.execute(sql, params)
            db.commit()
        
        # Get fresh user object
        return db.query(User).filter(User.id == user_id).first()
    
    def update_last_login(self, db: Session, user_id: int) -> None:
        """
        Update last login time using direct SQL to avoid JSON serialization issues
        
        Args:
            db: Database session
            user_id: User ID
        """
        now = datetime.utcnow().isoformat()
        
        sql = text("UPDATE users SET last_login = :now, updated_at = :now WHERE id = :user_id")
        db.execute(sql, {"now": now, "user_id": user_id})
        db.commit()
    
    def change_notification_preferences(
        self,
        db: Session,
        user_id: int,
        preferences: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Update notification preferences
        
        Args:
            db: Database session
            user_id: User ID
            preferences: Notification preferences
            
        Returns:
            Result dictionary
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Serialize preferences to JSON
        preferences_json = json.dumps(preferences)
        
        # Update using direct SQL
        sql = text("UPDATE users SET notification_preferences = :prefs, updated_at = :now WHERE id = :user_id")
        db.execute(sql, {"prefs": preferences_json, "now": datetime.utcnow().isoformat(), "user_id": user_id})
        db.commit()
        
        return {"success": True, "message": "Notification preferences updated"}

# Create singleton instance
user_service = UserService()
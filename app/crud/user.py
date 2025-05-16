# Fixes for backend/app/crud/user.py

from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from datetime import datetime
import json
from sqlalchemy import text

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models import User
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_by_google_id(self, db: Session, *, google_id: str) -> Optional[User]:
        return db.query(User).filter(User.google_id == google_id).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        # Prepare default JSON values - ensure they're strings
        notification_prefs = json.dumps({"email": True, "sms": True, "in_app": True})
        token_history = json.dumps([])
        
        # Create user with properly serialized JSON fields
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            role=obj_in.role,
            phone_number=obj_in.phone_number,
            auth_type=obj_in.auth_type if hasattr(obj_in, "auth_type") and obj_in.auth_type else "email",  # Set default
            token_balance=0,
            account_status="active",
            notification_preferences=notification_prefs,
            token_history=token_history
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def create_google_user(
        self, db: Session, *, email: str, full_name: str, google_id: str, role: str = "tenant"
    ) -> User:
        # Prepare default JSON values - ensure they're strings
        notification_prefs = json.dumps({"email": True, "sms": True, "in_app": True})
        token_history = json.dumps([])
        
        db_obj = User(
            email=email,
            full_name=full_name,
            google_id=google_id,
            role=role,
            auth_type="google",
            token_balance=0,
            account_status="active",
            notification_preferences=notification_prefs,
            token_history=token_history
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_user(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update user with proper JSON serialization
        """
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        # Handle notification preferences if present
        if "notification_preferences" in update_data:
            # Ensure it's stored as a JSON string
            if isinstance(update_data["notification_preferences"], dict):
                update_data["notification_preferences"] = json.dumps(update_data["notification_preferences"])
        
        # Handle token history if present
        if "token_history" in update_data:
            # Ensure it's stored as a JSON string
            if isinstance(update_data["token_history"], list):
                update_data["token_history"] = json.dumps(update_data["token_history"])
        
        # Use direct SQL for update to avoid issues with JSON fields
        from sqlalchemy import update
        stmt = update(User).where(User.id == db_obj.id)
        
        # Add each field individually to the update statement
        set_values = {}
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                set_values[field] = value
        
        # Add updated_at
        set_values['updated_at'] = datetime.utcnow()
        
        # Execute the update
        stmt = stmt.values(**set_values)
        db.execute(stmt)
        db.commit()
        
        # Refresh the object
        db.refresh(db_obj)
        return db_obj
    
    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def update_last_login(self, db: Session, *, user_id: int) -> User:
        """
        Update user's last login time using direct SQL to avoid JSON serialization issues.
        """
        # Use raw SQL to update ONLY the last_login and updated_at fields
        now = datetime.utcnow().isoformat()
        
        sql = text("UPDATE users SET last_login = :now, updated_at = :now WHERE id = :user_id")
        db.execute(sql, {"now": now, "user_id": user_id})
        db.commit()
        
        # Get fresh user object
        user = self.get(db, id=user_id)
        return user
            
    def update_token_balance(
        self, db: Session, *, user_id: int, amount: int
    ) -> User:
        """
        Update user's token balance with proper JSON serialization
        """
        # First, get the user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
            
        # Get current token balance
        new_balance = user.token_balance + amount
        
        # Get current token history as a list
        try:
            if isinstance(user.token_history, str):
                token_history = json.loads(user.token_history)
            else:
                token_history = []
        except:
            token_history = []
        
        # Add new entry
        token_history.append({
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat(),
            "balance": new_balance
        })
        
        # Convert to JSON string
        token_history_json = json.dumps(token_history)
        
        # Update fields directly using SQL
        sql = text("""
            UPDATE users 
            SET token_balance = :balance, 
                token_history = :history, 
                updated_at = :now 
            WHERE id = :user_id
        """)
        
        db.execute(sql, {
            "balance": new_balance,
            "history": token_history_json,
            "now": datetime.utcnow().isoformat(),
            "user_id": user_id
        })
        
        db.commit()
        
        # Refresh the user object
        db.refresh(user)
        return user
    
    def is_active(self, user: User) -> bool:
        return user.account_status == "active"
    
    def is_owner(self, user: User) -> bool:
        return user.role == "owner" or user.role == "admin"
    
    def is_admin(self, user: User) -> bool:
        return user.role == "admin"

user = CRUDUser(User)
# File: backend/app/utils/db_utils.py
# Utilities for database operations

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime

def update_user_fields(
    db: Session, 
    user_id: int, 
    fields: Dict[str, Any],
    include_timestamp: bool = True
) -> bool:
    """
    Update user fields with direct SQL to avoid JSON serialization issues
    
    Args:
        db: Database session
        user_id: User ID
        fields: Fields to update
        include_timestamp: Whether to include updated_at timestamp
        
    Returns:
        Success status
    """
    try:
        # Create SET clause and parameters
        set_clauses = []
        params = {"user_id": user_id}
        
        for key, value in fields.items():
            # Handle JSON fields
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        # Add timestamp if requested
        if include_timestamp:
            set_clauses.append("updated_at = :updated_at")
            params["updated_at"] = datetime.utcnow().isoformat()
        
        # Create SQL statement
        set_clause = ", ".join(set_clauses)
        sql = text(f"UPDATE users SET {set_clause} WHERE id = :user_id")
        
        # Execute the statement
        db.execute(sql, params)
        db.commit()
        return True
    except Exception as e:
        print(f"Error updating user fields: {e}")
        db.rollback()
        return False

def update_timestamp_only(
    db: Session,
    table: str,
    id_field: str,
    id_value: Any
) -> bool:
    """
    Update only the timestamp of a record
    
    Args:
        db: Database session
        table: Table name
        id_field: ID field name
        id_value: ID value
        
    Returns:
        Success status
    """
    try:
        sql = text(f"UPDATE {table} SET updated_at = :now WHERE {id_field} = :id_value")
        db.execute(sql, {"now": datetime.utcnow().isoformat(), "id_value": id_value})
        db.commit()
        return True
    except Exception as e:
        print(f"Error updating timestamp: {e}")
        db.rollback()
        return False

def get_json_field(
    db: Session,
    table: str,
    field: str,
    id_field: str,
    id_value: Any,
    default: Any = None
) -> Any:
    """
    Get a JSON field from a record
    
    Args:
        db: Database session
        table: Table name
        field: JSON field name
        id_field: ID field name
        id_value: ID value
        default: Default value if field is empty or invalid
        
    Returns:
        Parsed JSON value
    """
    try:
        sql = text(f"SELECT {field} FROM {table} WHERE {id_field} = :id_value")
        result = db.execute(sql, {"id_value": id_value}).fetchone()
        
        if not result or not result[0]:
            return default
            
        # Try to parse JSON
        try:
            return json.loads(result[0])
        except:
            return default
    except Exception as e:
        print(f"Error getting JSON field: {e}")
        return default

def set_json_field(
    db: Session,
    table: str,
    field: str,
    value: Any,
    id_field: str,
    id_value: Any,
    include_timestamp: bool = True
) -> bool:
    """
    Set a JSON field in a record
    
    Args:
        db: Database session
        table: Table name
        field: JSON field name
        value: Value to set (will be JSON serialized)
        id_field: ID field name
        id_value: ID value
        include_timestamp: Whether to include updated_at timestamp
        
    Returns:
        Success status
    """
    try:
        # Serialize value to JSON
        json_value = json.dumps(value)
        
        # Create SQL statement
        if include_timestamp:
            sql = text(f"UPDATE {table} SET {field} = :value, updated_at = :now WHERE {id_field} = :id_value")
            params = {"value": json_value, "now": datetime.utcnow().isoformat(), "id_value": id_value}
        else:
            sql = text(f"UPDATE {table} SET {field} = :value WHERE {id_field} = :id_value")
            params = {"value": json_value, "id_value": id_value}
        
        # Execute the statement
        db.execute(sql, params)
        db.commit()
        return True
    except Exception as e:
        print(f"Error setting JSON field: {e}")
        db.rollback()
        return False
    
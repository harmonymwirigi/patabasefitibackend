# File: backend/app/json_validator.py
# Simple JSON validation functions

import json
from typing import Any, Dict, List, Optional, Union

def to_json_string(value: Any) -> Optional[str]:
    """
    Convert a Python object to a JSON string
    
    Args:
        value: The value to convert
        
    Returns:
        JSON string or None if value is None
    """
    if value is None:
        return None
    if isinstance(value, str):
        try:
            # Check if it's already a valid JSON string
            json.loads(value)
            return value
        except json.JSONDecodeError:
            pass
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)

def from_json_string(value: Union[str, Dict, List, None], default: Any = None) -> Any:
    """
    Convert a JSON string to a Python object
    
    Args:
        value: The JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Python object or default if parsing fails
    """
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default

def ensure_json_field(obj: Any, field_name: str) -> None:
    """
    Ensure a field on an object is stored as a JSON string
    
    Args:
        obj: The object containing the field
        field_name: The field name
    """
    if not hasattr(obj, field_name):
        return
    
    value = getattr(obj, field_name)
    if isinstance(value, (dict, list)):
        setattr(obj, field_name, to_json_string(value))

# Function to apply to models
def validate_json_fields(obj: Any) -> None:
    """
    Validate and fix all JSON fields on an object
    
    Args:
        obj: The object to validate
    """
    # Common JSON field names in the application
    json_fields = [
        "notification_preferences", "token_history", 
        "amenities", "lease_terms", "engagement_metrics", 
        "auto_verification_settings", "featured_status"
    ]
    
    for field in json_fields:
        ensure_json_field(obj, field)
# File: backend/app/utils/json_utils.py
# Status: COMPLETE
import requests
from app.core.config import settings

import json
from typing import Any, Dict, List, Optional, Union
def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google OAuth token and return user info.
    """
    try:
        # Use Google's API to verify the token
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}"
        )
        
        if response.status_code != 200:
            return None
            
        token_info = response.json()
        
        # Verify that the token was intended for our app
        if settings.GOOGLE_CLIENT_ID and token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
            return None
            
        # Return user info
        return {
            "sub": token_info.get("sub"),
            "email": token_info.get("email"),
            "name": token_info.get("name"),
            "picture": token_info.get("picture")
        }
    except Exception:
        return None
    



def ensure_json_string(value: Any) -> str:
    """
    Ensures the value is a proper JSON string
    
    Args:
        value: Value to convert to JSON string
        
    Returns:
        JSON string representation of the value
    """
    if value is None:
        return '{}'
        
    if isinstance(value, str):
        try:
            # Check if it's already a valid JSON string
            json.loads(value)
            return value
        except json.JSONDecodeError:
            # Not a valid JSON string, serialize it
            return json.dumps(value)
    
    # Convert to JSON string
    return json.dumps(value)

def parse_json_string(json_str: Optional[str], default: Any = None) -> Any:
    """
    Parse a JSON string to a Python object
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Python object representation of the JSON string
    """
    if json_str is None:
        return default
        
    if not isinstance(json_str, str):
        return json_str
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return default

def dict_to_json_string(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary values that are dicts or lists to JSON strings
    
    Args:
        data: Dictionary with values to convert
        
    Returns:
        Dictionary with JSON string values
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            result[key] = ensure_json_string(value)
        else:
            result[key] = value
    return result

def ensure_dict(value: Union[Dict[str, Any], str, None], default: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Ensures the value is a Python dictionary
    
    Args:
        value: Value to convert to dict
        default: Default value if conversion fails
        
    Returns:
        Python dictionary
    """
    if default is None:
        default = {}
        
    if value is None:
        return default
        
    if isinstance(value, dict):
        return value
        
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
            return default
        except json.JSONDecodeError:
            return default
            
    return default

def ensure_list(value: Union[List[Any], str, None], default: List[Any] = None) -> List[Any]:
    """
    Ensures the value is a Python list
    
    Args:
        value: Value to convert to list
        default: Default value if conversion fails
        
    Returns:
        Python list
    """
    if default is None:
        default = []
        
    if value is None:
        return default
        
    if isinstance(value, list):
        return value
        
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return default
        except json.JSONDecodeError:
            return default
            
    return default


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

def safe_get_json_field(obj: Any, field_name: str, default: Any = None) -> Any:
    """
    Safely get a JSON field from an object, handling serialization
    
    Args:
        obj: The object containing the field
        field_name: The field name
        default: Default value if field doesn't exist or parsing fails
        
    Returns:
        Python object or default if field doesn't exist or parsing fails
    """
    if not hasattr(obj, field_name):
        return default
    
    value = getattr(obj, field_name)
    return from_json_string(value, default)

def safe_set_json_field(obj: Any, field_name: str, value: Any) -> None:
    """
    Safely set a JSON field on an object, handling serialization
    
    Args:
        obj: The object to update
        field_name: The field name
        value: The value to set
    """
    if not hasattr(obj, field_name):
        return
    
    serialized_value = to_json_string(value)
    setattr(obj, field_name, serialized_value)
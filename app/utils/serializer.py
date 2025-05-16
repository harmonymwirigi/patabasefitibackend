import json
from typing import Any, Dict, List
from sqlalchemy.orm import Query
import datetime

def convert_to_json(value: Any) -> Any:
    """Convert value to JSON-compatible type"""
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    elif isinstance(value, datetime.date):
        return value.isoformat()
    elif isinstance(value, bytes):
        return value.decode('utf-8')
    elif hasattr(value, '__dict__'):
        return value.__dict__
    else:
        return value

def serialize_model(model: Any) -> Dict:
    """Serialize a SQLAlchemy model to a dictionary"""
    result = {}
    for key in dir(model):
        # Skip private attributes and methods
        if key.startswith('_') or callable(getattr(model, key)):
            continue
            
        value = getattr(model, key)
        
        # Handle JSON fields
        if key == 'notification_preferences' and isinstance(value, str):
            try:
                result[key] = json.loads(value)
                continue
            except:
                pass
        elif key == 'token_history' and isinstance(value, str):
            try:
                result[key] = json.loads(value)
                continue
            except:
                pass
                
        # Handle normal fields
        result[key] = convert_to_json(value)
    
    return result

def serialize_query(query: Query) -> List:
    """Serialize a SQLAlchemy query to a list of dictionaries"""
    return [serialize_model(model) for model in query]
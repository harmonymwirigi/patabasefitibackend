import json
from typing import Any, Dict, List
from sqlalchemy.orm import Query
import datetime
from app.models import Property, PropertyImage, User
from sqlalchemy.orm import Session
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

def serialize_property_for_verification(db: Session, property_obj: Property) -> Dict[str, Any]:
    """
    Serialize a property object into a dictionary suitable for verification responses
    
    Args:
        db: Database session
        property_obj: Property model instance
        
    Returns:
        Dictionary with property data formatted for verification responses
    """
    if not property_obj:
        return None
        
    # Get images for this property
    images = db.query(PropertyImage).filter(
        PropertyImage.property_id == property_obj.id
    ).all()
    
    # Convert image objects to dictionaries
    image_dicts = [
        {
            "id": img.id,
            "property_id": img.property_id,
            "path": img.path,
            "is_primary": img.is_primary,
            "uploaded_at": img.uploaded_at
        }
        for img in images
    ]
    
    # Get the owner if needed (optional) - fixed query
    owner_dict = None
    if property_obj.owner_id:
        owner = db.query(User).filter(User.id == property_obj.owner_id).first()
        if owner:
            owner_dict = {
                "id": owner.id,
                "full_name": owner.full_name,
                "email": owner.email
            }
    
    # Create property dictionary with all required fields
    return {
        "id": property_obj.id,
        "title": property_obj.title,
        "property_type": property_obj.property_type,
        "rent_amount": property_obj.rent_amount,
        "bedrooms": property_obj.bedrooms,
        "bathrooms": property_obj.bathrooms,
        "address": property_obj.address,
        "city": property_obj.city,
        "neighborhood": property_obj.neighborhood,
        "verification_status": property_obj.verification_status,
        "availability_status": property_obj.availability_status,
        "owner": owner_dict,
        "images": image_dicts
    }
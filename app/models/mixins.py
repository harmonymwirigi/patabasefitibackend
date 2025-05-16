# File: backend/app/models/mixins.py
# Comprehensive mixins for model functionality and JSON compatibility

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import event, inspect

class TimestampMixin:
    """Mixin to automatically handle created_at and updated_at timestamps"""
    
    created_at = None  # These will be defined in the actual model
    updated_at = None
    
    @classmethod
    def _set_timestamps(cls, mapper, connection, target):
        """Set timestamps before insert"""
        now = datetime.utcnow()
        if hasattr(target, 'created_at') and target.created_at is None:
            target.created_at = now
        if hasattr(target, 'updated_at'):
            target.updated_at = now
    
    @classmethod
    def _update_timestamp(cls, mapper, connection, target):
        """Update the updated_at timestamp before update"""
        if hasattr(target, 'updated_at'):
            target.updated_at = datetime.utcnow()
    
    @classmethod
    def register_timestamp_listeners(cls):
        """Register timestamp event listeners for the class"""
        event.listen(cls, 'before_insert', cls._set_timestamps)
        event.listen(cls, 'before_update', cls._update_timestamp)


class JSONSerializationMixin:
    """Mixin to handle JSON serialization for SQLite compatibility"""
    
    # Override this in your model class to list all JSON columns
    _json_columns: List[str] = []
    
    @classmethod
    def _json_serialize_column(cls, mapper, connection, target):
        """Convert dict/list attributes to JSON strings before insert/update"""
        for column_name in target._json_columns:
            value = getattr(target, column_name, None)
            if value is not None and not isinstance(value, str):
                setattr(target, column_name, json.dumps(value))
    
    @classmethod
    def register_json_listeners(cls):
        """Register JSON serialization event listeners for the class"""
        if cls._json_columns:  # Only register if there are JSON columns
            event.listen(cls, 'before_insert', cls._json_serialize_column)
            event.listen(cls, 'before_update', cls._json_serialize_column)
    
    def get_json_field(self, field_name: str) -> Union[Dict[str, Any], List[Any], Any]:
        """Get a JSON field as a Python object"""
        if field_name not in self._json_columns:
            raise ValueError(f"Field {field_name} is not defined as a JSON column")
        
        value = getattr(self, field_name)
        if value is None:
            return None
        
        if isinstance(value, (dict, list)):
            return value
        
        try:
            return json.loads(value)
        except Exception:
            # Return appropriate default based on expected type
            for method_name in dir(self):
                if method_name == f"get_{field_name}_json":
                    # Use the getter method to get the default
                    method = getattr(self, method_name)
                    if callable(method):
                        return method()
            
            # Default fallbacks
            if field_name.endswith('_history'):
                return []
            elif field_name.endswith('_preferences') or field_name.endswith('_settings'):
                return {}
            else:
                return {}
    
    def set_json_field(self, field_name: str, value: Any) -> None:
        """Set a JSON field with proper serialization"""
        if field_name not in self._json_columns:
            raise ValueError(f"Field {field_name} is not defined as a JSON column")
        
        if isinstance(value, (dict, list)):
            # Store as string for SQLite compatibility
            setattr(self, field_name, json.dumps(value))
        elif value is None:
            setattr(self, field_name, None)
        elif isinstance(value, str):
            # Validate that it's valid JSON if it's a string
            try:
                json.loads(value)
                setattr(self, field_name, value)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON string provided for {field_name}")
        else:
            # Try to serialize other types
            setattr(self, field_name, json.dumps(value))


class SoftDeleteMixin:
    """Mixin to implement soft delete functionality"""
    
    deleted_at = None  # This will be defined in the actual model
    
    def soft_delete(self, session):
        """Mark the record as deleted"""
        self.deleted_at = datetime.utcnow()
        session.add(self)
        session.commit()
    
    def restore(self, session):
        """Restore a soft-deleted record"""
        self.deleted_at = None
        session.add(self)
        session.commit()
    
    @classmethod
    def apply_active_filter(cls, query):
        """Filter out soft-deleted records"""
        return query.filter(cls.deleted_at == None)


class BaseModelMixin(TimestampMixin, JSONSerializationMixin):
    """Combined base mixin with common functionality for all models"""
    
    @classmethod
    def register_all_listeners(cls):
        """Register all event listeners for the class"""
        cls.register_timestamp_listeners()
        cls.register_json_listeners()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary, handling JSON fields"""
        result = {}
        for column in inspect(self.__class__).columns:
            value = getattr(self, column.name)
            
            # Handle JSON columns
            if hasattr(self, '_json_columns') and column.name in self._json_columns:
                if value is not None:
                    if isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, keep as is
                            pass
            
            result[column.name] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Create a model instance from a dictionary, handling JSON fields"""
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                # Handle JSON columns
                if hasattr(instance, '_json_columns') and key in instance._json_columns:
                    instance.set_json_field(key, value)
                else:
                    setattr(instance, key, value)
        return instance


# Helper functions for working with models
def get_default_json_fields() -> Dict[str, Any]:
    """Return common default JSON fields with their default values"""
    return {
        'notification_preferences': {"email": True, "sms": True, "in_app": True},
        'token_history': [],
        'amenities': [],
        'lease_terms': {},
        'engagement_metrics': {"view_count": 0, "favorite_count": 0, "contact_count": 0},
        'auto_verification_settings': {"enabled": True, "frequency_days": 7},
        'featured_status': {"is_featured": False},
        'metadata': {}
    }
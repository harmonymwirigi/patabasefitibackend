# File: backend/app/crud/base.py
# Add JSON serialization support to CRUD base class

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()
        
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()
        
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record with proper JSON serialization"""
        try:
            obj_in_data = jsonable_encoder(obj_in)
            
            # Serialize JSON fields for SQLite
            for k, v in obj_in_data.items():
                if isinstance(v, (dict, list)):
                    obj_in_data[k] = json.dumps(v)
            
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            print(f"Error in create: {e}")
            import traceback
            traceback.print_exc()
            raise
        
    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update model instance with properly handling JSON fields
        """
        try:
            obj_data = jsonable_encoder(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in.copy()
            else:
                update_data = obj_in.dict(exclude_unset=True)
            
            # Process each field - handle JSON serialization for dict/list values
            for field in obj_data:
                if field in update_data:
                    value = update_data[field]
                    
                    # If value is dict or list, serialize to JSON string
                    if isinstance(value, (dict, list)):
                        setattr(db_obj, field, json.dumps(value))
                    else:
                        setattr(db_obj, field, value)
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            print(f"Error in update: {e}")
            import traceback
            traceback.print_exc()
            raise
            
    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
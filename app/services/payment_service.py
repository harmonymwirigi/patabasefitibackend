# File: backend/app/services/property_service.py
# This file already exists but we'll enhance it to handle JSON serialization

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from app import models
from app.crud.property import property as property_crud
from app.crud.verification import verification as verification_crud
from app.schemas.verification import VerificationCreate
from app.schemas.property import PropertyCreate

class PropertyService:
    def create_property(
        self, 
        db: Session, 
        property_data: PropertyCreate, 
        owner_id: int
    ) -> models.Property:
        """
        Create a new property with proper JSON serialization
        
        Args:
            db: Database session
            property_data: Property data
            owner_id: Owner ID
            
        Returns:
            Created property
        """
        # Create a dictionary from property_data
        data_dict = property_data.dict()
        
        # Ensure JSON fields are properly serialized
        if "amenities" in data_dict and data_dict["amenities"] is not None:
            if isinstance(data_dict["amenities"], list):
                data_dict["amenities"] = json.dumps(data_dict["amenities"])
        
        if "lease_terms" in data_dict and data_dict["lease_terms"] is not None:
            if isinstance(data_dict["lease_terms"], dict):
                data_dict["lease_terms"] = json.dumps(data_dict["lease_terms"])
        
        if "auto_verification_settings" in data_dict and data_dict["auto_verification_settings"] is not None:
            if isinstance(data_dict["auto_verification_settings"], dict):
                data_dict["auto_verification_settings"] = json.dumps(data_dict["auto_verification_settings"])
        
        # Create PropertyCreate with serialized fields
        property_in = PropertyCreate(**data_dict)
        
        # Use the CRUD method to create the property
        return property_crud.create_with_owner(db, obj_in=property_in, owner_id=owner_id)

    def add_property_images(
        self, 
        db: Session, 
        property_id: int, 
        image_paths: List[str]
    ) -> Optional[models.Property]:
        """
        Add images to a property
        
        Args:
            db: Database session
            property_id: Property ID
            image_paths: List of image file paths
            
        Returns:
            Updated property if successful, None otherwise
        """
        property_obj = property_crud.get(db, id=property_id)
        if not property_obj:
            return None
            
        # Add images
        for path in image_paths:
            image = models.PropertyImage(
                property_id=property_id,
                path=path,
                is_primary=False  # Default to non-primary
            )
            db.add(image)
            
        db.commit()
        db.refresh(property_obj)
        return property_obj
    
    def schedule_verification(
        self, 
        db: Session, 
        property_id: int, 
        verification_type: str = "automatic"
    ) -> Dict[str, Any]:
        """
        Schedule property verification
        
        Args:
            db: Database session
            property_id: Property ID
            verification_type: Type of verification ("automatic", "owner", "agent")
            
        Returns:
            Dictionary with verification details
        """
        property_obj = property_crud.get(db, id=property_id)
        if not property_obj:
            return {"success": False, "message": "Property not found"}
            
        # Create verification request
        expiration = datetime.utcnow() + timedelta(days=3)  # 3 days to respond
        verification_data = VerificationCreate(
            property_id=property_id,
            verification_type=verification_type,
            expiration=expiration,
            status="pending"
        )
        
        verification = verification_crud.create(db, obj_in=verification_data)
        
        return {
            "success": True,
            "verification_id": verification.id,
            "property_id": property_id,
            "status": "pending",
            "expiration": expiration
        }
    
    def handle_expired_properties(self, db: Session) -> Dict[str, Any]:
        """
        Handle properties that have expired (listing period ended)
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with results summary
        """
        expired_properties = property_crud.get_expired_properties(db)
        
        updated_count = 0
        for prop in expired_properties:
            # Mark as inactive
            prop.availability_status = "inactive"
            db.add(prop)
            updated_count += 1
            
        db.commit()
        
        return {
            "success": True,
            "processed_count": len(expired_properties),
            "updated_count": updated_count
        }
    
    def update_featured_status(
        self, 
        db: Session, 
        property_id: int, 
        is_featured: bool
    ) -> Optional[models.Property]:
        """
        Update property featured status
        
        Args:
            db: Database session
            property_id: Property ID
            is_featured: Whether property should be featured
            
        Returns:
            Updated property if successful, None otherwise
        """
        property_obj = property_crud.get(db, id=property_id)
        if not property_obj:
            return None
            
        # Update featured status
        # Ensure we're working with a dictionary
        try:
            if isinstance(property_obj.featured_status, str):
                featured_status = json.loads(property_obj.featured_status)
            else:
                featured_status = property_obj.featured_status or {}
        except:
            featured_status = {"is_featured": False}
            
        featured_status["is_featured"] = is_featured
        
        # Store as JSON string
        property_obj.featured_status = json.dumps(featured_status)
        
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        return property_obj

# Create singleton instance
property_service = PropertyService()
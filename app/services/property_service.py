# File: backend/app/services/property_service.py
# Direct property creation without using CRUD

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
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
        Create a new property with manual transaction control
        
        Args:
            db: Database session
            property_data: Property data
            owner_id: Owner ID
            
        Returns:
            Created property
        """
        try:
            # Extract amenities from property data
            amenities = []
            if hasattr(property_data, 'amenities') and property_data.amenities:
                if isinstance(property_data.amenities, list):
                    amenities = property_data.amenities
                elif isinstance(property_data.amenities, str):
                    try:
                        amenities = json.loads(property_data.amenities)
                    except json.JSONDecodeError:
                        amenities = []
            
            # Create property directly
            data_dict = property_data.dict()
            
            # Make sure to serialize any JSON fields
            for field in ["amenities", "lease_terms", "auto_verification_settings"]:
                if field in data_dict and isinstance(data_dict[field], (dict, list)):
                    data_dict[field] = json.dumps(data_dict[field])
            
            # Create Property object and add to database
            property_obj = models.Property(
                **data_dict,
                owner_id=owner_id,
                # Set default values for fields not in the schema
                verification_status="pending",
                engagement_metrics=json.dumps({"view_count": 0, "favorite_count": 0, "contact_count": 0}),
                featured_status=json.dumps({"is_featured": False})
            )
            
            # Add to database and get ID
            db.add(property_obj)
            db.flush()  # Flush to get the ID but don't commit yet
            
            # Now add the amenities with the correct property_id
            for amenity in amenities:
                amenity_obj = models.PropertyAmenity(
                    property_id=property_obj.id,
                    amenity=amenity
                )
                db.add(amenity_obj)
            
            # Update the owner's last activity without touching JSON fields
            sql = text("UPDATE users SET updated_at = :now WHERE id = :user_id")
            db.execute(sql, {
                "now": datetime.utcnow().isoformat(),
                "user_id": owner_id
            })
            
            # Create a verification record for this property
            verification = models.Verification(
                property_id=property_obj.id,
                verification_type="automatic",
                status="pending",
                expiration=datetime.utcnow() + timedelta(days=7)
            )
            db.add(verification)
            
            # Commit everything
            db.commit()
            db.refresh(property_obj)
            
            return property_obj
        except Exception as e:
            db.rollback()
            print(f"Error in create_property: {e}")
            import traceback
            traceback.print_exc()
            raise
    def create_verification_for_property(self, db: Session, property_id: int) -> bool:
        """
        Create a verification record for a property
        
        Args:
            db: Database session
            property_id: Property ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime, timedelta
            
            # Check if verification record already exists
            existing_verification = db.query(models.Verification).filter(
                models.Verification.property_id == property_id,
                models.Verification.status == "pending"
            ).first()
            
            if not existing_verification:
                # Create a new verification record
                verification = models.Verification(
                    property_id=property_id,
                    verification_type="automatic",
                    status="pending",
                    expiration=datetime.utcnow() + timedelta(days=7)
                )
                db.add(verification)
                db.commit()
                
            return True
        except Exception as e:
            print(f"Error creating verification record: {e}")
            return False
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
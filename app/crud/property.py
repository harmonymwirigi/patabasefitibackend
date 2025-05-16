# File: backend/app/crud/property.py
# Modified to add create_with_owner_without_commit method

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
import datetime
import json

from app.crud.base import CRUDBase
from app.models import Property, PropertyImage, PropertyAmenity
from app.schemas.property import PropertyCreate, PropertyUpdate

class CRUDProperty(CRUDBase[Property, PropertyCreate, PropertyUpdate]):
    def create_with_owner_without_commit(
        self, db: Session, *, obj_in: PropertyCreate, owner_id: int
    ) -> Property:
        """
        Create property with owner but don't commit to DB.
        This allows for better control of when the commit happens.
        """
        try:
            # Create a dictionary from the PropertyCreate object
            obj_in_data = obj_in.dict()
            
            # Handle JSON fields specifically - serialize them to strings for SQLite
            amenities_data = obj_in_data.get("amenities", [])
            if isinstance(amenities_data, str):
                try:
                    amenities_data = json.loads(amenities_data)
                except json.JSONDecodeError:
                    amenities_data = []
                    
            lease_terms_data = obj_in_data.get("lease_terms", {})
            if isinstance(lease_terms_data, str):
                try:
                    lease_terms_data = json.loads(lease_terms_data)
                except json.JSONDecodeError:
                    lease_terms_data = {}
                    
            auto_verification_settings_data = obj_in_data.get("auto_verification_settings", {"enabled": True, "frequency_days": 7})
            if isinstance(auto_verification_settings_data, str):
                try:
                    auto_verification_settings_data = json.loads(auto_verification_settings_data)
                except json.JSONDecodeError:
                    auto_verification_settings_data = {"enabled": True, "frequency_days": 7}
            
            # Remove these fields from the dictionary to avoid validation issues
            if "amenities" in obj_in_data:
                del obj_in_data["amenities"]
            if "lease_terms" in obj_in_data:
                del obj_in_data["lease_terms"]
            if "auto_verification_settings" in obj_in_data:
                del obj_in_data["auto_verification_settings"]
            
            # Create the property object with basic fields
            db_obj = Property(
                **obj_in_data,
                owner_id=owner_id,
                # Set the JSON fields with proper serialization
                amenities=json.dumps(amenities_data) if amenities_data else '[]',
                lease_terms=json.dumps(lease_terms_data) if lease_terms_data else '{}',
                engagement_metrics=json.dumps({"view_count": 0, "favorite_count": 0, "contact_count": 0}),
                auto_verification_settings=json.dumps(auto_verification_settings_data) if auto_verification_settings_data else '{"enabled": true, "frequency_days": 7}',
                featured_status=json.dumps({"is_featured": False})
            )
            
            # Add to session but don't commit yet
            db.add(db_obj)
            
            # Add amenities as separate records if provided
            if amenities_data:
                for amenity in amenities_data:
                    db_amenity = PropertyAmenity(
                        property_id=0,  # This will be updated after commit
                        amenity=amenity
                    )
                    # We'll keep track of these to update their property_id after commit
                    db_obj._amenity_objects = getattr(db_obj, '_amenity_objects', []) + [db_amenity]
                    db.add(db_amenity)
            
            return db_obj
            
        except Exception as e:
            db.rollback()
            print(f"Error in create_with_owner_without_commit: {e}")
            import traceback
            traceback.print_exc()
            raise

    def create_with_owner(
        self, db: Session, *, obj_in: PropertyCreate, owner_id: int
    ) -> Property:
        """
        Create property with owner, handling JSON serialization properly
        """
        try:
            db_obj = self.create_with_owner_without_commit(db, obj_in=obj_in, owner_id=owner_id)
            
            # Commit to get the ID
            db.commit()
            db.refresh(db_obj)
            
            # Update amenity property_ids if any exist
            if hasattr(db_obj, '_amenity_objects'):
                for amenity_obj in db_obj._amenity_objects:
                    amenity_obj.property_id = db_obj.id
                    db.add(amenity_obj)
                
                # Commit amenity updates
                db.commit()
                
                # Remove temporary attribute
                delattr(db_obj, '_amenity_objects')
            
            # Return the complete object
            return db_obj
            
        except Exception as e:
            db.rollback()
            print(f"Error in create_with_owner: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Property]:
        return (
            db.query(Property)
            .filter(Property.owner_id == owner_id)
            .order_by(desc(Property.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_featured(
        self, db: Session, *, skip: int = 0, limit: int = 10
    ) -> List[Property]:
        return (
            db.query(Property)
            .filter(
                Property.availability_status == "available",
                Property.featured_status.contains('{"is_featured": true}')
            )
            .order_by(desc(Property.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_expired_properties(self, db: Session) -> List[Property]:
        """Get properties that have expired (for maintenance)"""
        now = datetime.datetime.utcnow()
        return (
            db.query(Property)
            .filter(
                Property.expiration_date.isnot(None),
                Property.expiration_date < now,
                Property.availability_status == "available"
            )
            .all()
        )
    
    def search(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        property_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[int] = None,
        city: Optional[str] = None,
        amenities: Optional[List[str]] = None,
        keyword: Optional[str] = None,
        sort_by: Optional[str] = "newest"
    ) -> List[Property]:
        """
        Search properties with filters
        """
        query = db.query(Property).filter(Property.availability_status == "available")
        
        # Apply filters
        if property_type:
            query = query.filter(Property.property_type == property_type)
            
        if min_price is not None:
            query = query.filter(Property.rent_amount >= min_price)
            
        if max_price is not None:
            query = query.filter(Property.rent_amount <= max_price)
            
        if bedrooms is not None:
            query = query.filter(Property.bedrooms >= bedrooms)
            
        if bathrooms is not None:
            query = query.filter(Property.bathrooms >= bathrooms)
            
        if city:
            query = query.filter(func.lower(Property.city).like(f"%{city.lower()}%"))
            
        if amenities:
            # For SQLite, we need to query the amenities table
            for amenity in amenities:
                query = query.join(PropertyAmenity, Property.id == PropertyAmenity.property_id)
                query = query.filter(PropertyAmenity.amenity == amenity)
            
        if keyword:
            # Full-text search (simplified for SQLite)
            keyword_lower = f"%{keyword.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Property.title).like(keyword_lower),
                    func.lower(Property.description).like(keyword_lower),
                    func.lower(Property.address).like(keyword_lower),
                    func.lower(Property.neighborhood).like(keyword_lower)
                )
            )
            
        # Apply sorting
        if sort_by == "price_low":
            query = query.order_by(Property.rent_amount)
        elif sort_by == "price_high":
            query = query.order_by(desc(Property.rent_amount))
        else:  # Default to newest
            query = query.order_by(desc(Property.created_at))
            
        # Apply pagination and return results
        return query.offset(skip).limit(limit).all()
    
    def update_engagement_metrics(
        self, db: Session, *, property_id: int, metric_type: str
    ) -> Property:
        property_obj = self.get(db, id=property_id)
        if not property_obj:
            return None
            
        try:
            # Get the current metrics
            if hasattr(property_obj, 'engagement_metrics_json'):
                metrics = property_obj.engagement_metrics_json
            else:
                # Manual parsing
                if isinstance(property_obj.engagement_metrics, str):
                    metrics = json.loads(property_obj.engagement_metrics)
                else:
                    metrics = property_obj.engagement_metrics or {"view_count": 0, "favorite_count": 0, "contact_count": 0}
            
            # Update the specific metric
            if metric_type == "view":
                metrics["view_count"] = metrics.get("view_count", 0) + 1
            elif metric_type == "favorite":
                metrics["favorite_count"] = metrics.get("favorite_count", 0) + 1
            elif metric_type == "contact":
                metrics["contact_count"] = metrics.get("contact_count", 0) + 1
            
            # Store back the metrics
            if hasattr(property_obj, 'engagement_metrics_json'):
                property_obj.engagement_metrics_json = metrics
            else:
                # Manual serialization
                property_obj.engagement_metrics = json.dumps(metrics)
            
            db.add(property_obj)
            db.commit()
            db.refresh(property_obj)
            return property_obj
        except Exception as e:
            print(f"Error updating engagement metrics: {e}")
            db.rollback()
            raise
    
    def update_verification_status(
        self, db: Session, *, property_id: int, status: str
    ) -> Property:
        property_obj = self.get(db, id=property_id)
        if not property_obj:
            return None
            
        property_obj.verification_status = status
        property_obj.last_verified = datetime.datetime.utcnow()
        
        if status == "verified":
            # Set expiration date for 30 days from now
            property_obj.expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        return property_obj

# Create singleton instance
property = CRUDProperty(Property)
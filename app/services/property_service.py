# File: backend/app/services/property_service.py
# Enhanced property service with better error handling and geocoding

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging

from app import models
from app.crud.property import property as property_crud
from app.crud.verification import verification as verification_crud
from app.schemas.verification import VerificationCreate
from app.schemas.property import PropertyCreate, PropertyUpdate

logger = logging.getLogger(__name__)

# Import geocoding service with fallback
try:
    from app.services.geocoding_service import geocoding_service
    GEOCODING_AVAILABLE = True
except ImportError:
    GEOCODING_AVAILABLE = False
    logger.warning("Geocoding service not available")

class PropertyService:
    def create_property(
        self, 
        db: Session, 
        property_data: PropertyCreate, 
        owner_id: int
    ) -> models.Property:
        """
        Create a new property with optional geocoding
        
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
            
            # Get property data as dict
            data_dict = property_data.dict()
            
            # Auto-geocode if coordinates not provided and geocoding is available
            if GEOCODING_AVAILABLE and (not data_dict.get('latitude') or not data_dict.get('longitude')):
                logger.info(f"Attempting to geocode address: {data_dict.get('address')}, {data_dict.get('city')}")
                
                try:
                    geocode_result = geocoding_service.geocode_address(
                        address=data_dict.get('address', ''),
                        city=data_dict.get('city', ''),
                        country="Kenya"
                    )
                    
                    if geocode_result:
                        data_dict['latitude'] = geocode_result['latitude']
                        data_dict['longitude'] = geocode_result['longitude']
                        
                        logger.info(f"Geocoding successful: {geocode_result.get('formatted_address', 'No formatted address')}")
                    else:
                        logger.warning(f"Geocoding failed for address: {data_dict.get('address')}")
                        # Continue without coordinates
                        data_dict['latitude'] = None
                        data_dict['longitude'] = None
                        
                except Exception as e:
                    logger.error(f"Geocoding error: {e}")
                    # Continue without coordinates
                    data_dict['latitude'] = None
                    data_dict['longitude'] = None
            elif not GEOCODING_AVAILABLE:
                logger.info("Geocoding service not available, creating property without coordinates")
                
            # Validate provided coordinates if they exist
            if data_dict.get('latitude') is not None and data_dict.get('longitude') is not None:
                try:
                    lat, lng = float(data_dict['latitude']), float(data_dict['longitude'])
                    
                    # Basic validation for Kenya bounds
                    if not (-5.0 <= lat <= 5.0 and 33.5 <= lng <= 42.0):
                        logger.warning(f"Coordinates outside Kenya bounds: {lat}, {lng}")
                        # You could either reject or allow with warning
                        # For now, we'll allow but log the warning
                    
                    data_dict['latitude'] = lat
                    data_dict['longitude'] = lng
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid coordinate values: {e}")
                    data_dict['latitude'] = None
                    data_dict['longitude'] = None
            
            # Ensure required JSON fields have default values
            default_json_fields = {
                'amenities': amenities,
                'lease_terms': data_dict.get('lease_terms', {}),
                'auto_verification_settings': data_dict.get('auto_verification_settings', {"enabled": True, "frequency_days": 7}),
                'engagement_metrics': {"view_count": 0, "favorite_count": 0, "contact_count": 0},
                'featured_status': {"is_featured": False}
            }
            
            # Serialize JSON fields to strings for SQLite
            for field, default_value in default_json_fields.items():
                if field in data_dict:
                    value = data_dict[field]
                    if isinstance(value, (dict, list)):
                        data_dict[field] = json.dumps(value)
                    elif isinstance(value, str):
                        # Validate it's proper JSON
                        try:
                            json.loads(value)
                        except json.JSONDecodeError:
                            data_dict[field] = json.dumps(default_value)
                    else:
                        data_dict[field] = json.dumps(default_value)
                else:
                    data_dict[field] = json.dumps(default_value)
            
            # Set default availability_status if not provided
            if 'availability_status' not in data_dict or data_dict['availability_status'] is None:
                data_dict['availability_status'] = 'available'
            
            # Remove fields that shouldn't be passed to the constructor
            excluded_fields = ['amenities']  # amenities are handled separately
            
            # Prepare constructor arguments
            constructor_args = {
                k: v for k, v in data_dict.items() 
                if k not in excluded_fields
            }
            
            # Add required fields
            constructor_args.update({
                'owner_id': owner_id,
                'verification_status': 'pending'
            })
            
            # Create Property object
            property_obj = models.Property(**constructor_args)
            
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
            
            # Update the owner's last activity
            try:
                sql = text("UPDATE users SET updated_at = :now WHERE id = :user_id")
                db.execute(sql, {
                    "now": datetime.utcnow().isoformat(),
                    "user_id": owner_id
                })
            except Exception as e:
                logger.warning(f"Failed to update owner activity: {e}")
            
            # Create a verification record for this property
            try:
                verification = models.Verification(
                    property_id=property_obj.id,
                    verification_type="automatic",
                    status="pending",
                    expiration=datetime.utcnow() + timedelta(days=7)
                )
                db.add(verification)
            except Exception as e:
                logger.warning(f"Failed to create verification record: {e}")
            
            # Commit everything
            db.commit()
            db.refresh(property_obj)
            
            logger.info(f"Property created successfully with ID: {property_obj.id}")
            return property_obj
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in create_property: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def update_property_location(
        self,
        db: Session,
        property_id: int,
        address: str = None,
        city: str = None,
        latitude: float = None,
        longitude: float = None,
        force_geocode: bool = False
    ) -> Optional[models.Property]:
        """
        Update property location with optional geocoding
        """
        property_obj = property_crud.get(db, id=property_id)
        if not property_obj:
            return None
        
        try:
            update_data = {}
            
            # Update address fields if provided
            if address is not None:
                update_data['address'] = address
            if city is not None:
                update_data['city'] = city
            
            # Handle coordinates
            if latitude is not None and longitude is not None:
                # Manual coordinates provided
                try:
                    lat, lng = float(latitude), float(longitude)
                    
                    # Basic validation for Kenya bounds
                    if -5.0 <= lat <= 5.0 and 33.5 <= lng <= 42.0:
                        update_data['latitude'] = lat
                        update_data['longitude'] = lng
                    else:
                        logger.warning(f"Invalid coordinates for Kenya: {lat}, {lng}")
                        return None
                        
                except (ValueError, TypeError):
                    logger.warning(f"Invalid coordinate format: {latitude}, {longitude}")
                    return None
                    
            elif GEOCODING_AVAILABLE and (address or city or force_geocode):
                # Need to geocode
                current_address = update_data.get('address', property_obj.address)
                current_city = update_data.get('city', property_obj.city)
                
                try:
                    geocode_result = geocoding_service.geocode_address(
                        address=current_address,
                        city=current_city,
                        country="Kenya"
                    )
                    
                    if geocode_result:
                        update_data['latitude'] = geocode_result['latitude']
                        update_data['longitude'] = geocode_result['longitude']
                        logger.info(f"Re-geocoded property {property_id}")
                    else:
                        logger.warning(f"Failed to geocode updated address for property {property_id}")
                except Exception as e:
                    logger.error(f"Geocoding error for property {property_id}: {e}")
            
            # Update the property
            if update_data:
                for field, value in update_data.items():
                    setattr(property_obj, field, value)
                
                property_obj.updated_at = datetime.utcnow()
                db.add(property_obj)
                db.commit()
                db.refresh(property_obj)
            
            return property_obj
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating property location: {e}")
            raise
    
    def geocode_existing_properties(self, db: Session, limit: int = 100) -> Dict[str, Any]:
        """
        Batch geocode existing properties that don't have coordinates
        """
        if not GEOCODING_AVAILABLE:
            return {
                'total_processed': 0,
                'successful_geocodes': 0,
                'failed_geocodes': 0,
                'errors': ['Geocoding service not available']
            }
        
        try:
            # Get properties without coordinates
            properties_without_coords = db.query(models.Property).filter(
                models.Property.latitude.is_(None) | 
                models.Property.longitude.is_(None)
            ).limit(limit).all()
            
            results = {
                'total_processed': 0,
                'successful_geocodes': 0,
                'failed_geocodes': 0,
                'errors': []
            }
            
            for property_obj in properties_without_coords:
                try:
                    results['total_processed'] += 1
                    
                    geocode_result = geocoding_service.geocode_address(
                        address=property_obj.address,
                        city=property_obj.city,
                        country="Kenya"
                    )
                    
                    if geocode_result:
                        property_obj.latitude = geocode_result['latitude']
                        property_obj.longitude = geocode_result['longitude']
                        db.add(property_obj)
                        results['successful_geocodes'] += 1
                        
                        logger.info(f"Geocoded property {property_obj.id}: {geocode_result.get('formatted_address', 'No formatted address')}")
                    else:
                        results['failed_geocodes'] += 1
                        logger.warning(f"Failed to geocode property {property_obj.id}")
                        
                except Exception as e:
                    results['failed_geocodes'] += 1
                    results['errors'].append(f"Property {property_obj.id}: {str(e)}")
                    logger.error(f"Error geocoding property {property_obj.id}: {e}")
            
            # Commit all successful geocodes
            if results['successful_geocodes'] > 0:
                db.commit()
                logger.info(f"Batch geocoding completed: {results}")
            
            return results
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in batch geocoding: {e}")
            raise
    
    def get_nearby_properties(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        limit: int = 10
    ) -> List[models.Property]:
        """
        Get properties near a location using Haversine formula
        """
        try:
            # Haversine formula for SQLite
            sql = text("""
                SELECT *, 
                       (6371 * acos(cos(radians(:lat)) * cos(radians(latitude)) * 
                       cos(radians(longitude) - radians(:lng)) + sin(radians(:lat)) * 
                       sin(radians(latitude)))) AS distance
                FROM properties 
                WHERE latitude IS NOT NULL 
                  AND longitude IS NOT NULL
                  AND availability_status = 'available'
                HAVING distance <= :radius
                ORDER BY distance
                LIMIT :limit
            """)
            
            result = db.execute(sql, {
                'lat': latitude,
                'lng': longitude,
                'radius': radius_km,
                'limit': limit
            })
            
            # Convert results to Property objects
            properties = []
            for row in result:
                property_obj = db.query(models.Property).filter(
                    models.Property.id == row.id
                ).first()
                if property_obj:
                    # Add distance as an attribute
                    property_obj.distance_km = round(row.distance, 2)
                    properties.append(property_obj)
            
            return properties
            
        except Exception as e:
            logger.error(f"Error finding nearby properties: {e}")
            return []

# Create singleton instance
property_service = PropertyService()
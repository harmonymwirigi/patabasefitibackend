# File: backend/app/api/api_v1/endpoints/locations.py
# Fixed endpoints for location and geocoding features

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models
from app.api import deps
from app.services.geocoding_service import geocoding_service
from app.services.property_service import property_service
from app.schemas.property import PropertyListItem

router = APIRouter()

class GeocodeRequest(BaseModel):
    address: str
    city: Optional[str] = None
    country: str = "Kenya"

class GeocodeResponse(BaseModel):
    success: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None
    provider: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None

class ReverseGeocodeRequest(BaseModel):
    latitude: float
    longitude: float

class ReverseGeocodeResponse(BaseModel):
    success: bool
    formatted_address: Optional[str] = None
    street: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    country: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None

class LocationUpdateRequest(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    force_geocode: bool = False

class NearbyPropertiesResponse(BaseModel):
    properties: List[dict]
    total_found: int
    search_radius_km: float
    center_latitude: float
    center_longitude: float

@router.post("/geocode", response_model=GeocodeResponse)
def geocode_address(
    request: GeocodeRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Convert address to coordinates
    """
    try:
        result = geocoding_service.geocode_address(
            address=request.address,
            city=request.city,
            country=request.country
        )
        
        if result:
            return GeocodeResponse(
                success=True,
                latitude=result['latitude'],
                longitude=result['longitude'],
                formatted_address=result.get('formatted_address'),
                provider=result.get('provider'),
                confidence=result.get('confidence')
            )
        else:
            return GeocodeResponse(
                success=False,
                error="Address could not be geocoded"
            )
            
    except Exception as e:
        return GeocodeResponse(
            success=False,
            error=f"Geocoding failed: {str(e)}"
        )

@router.post("/reverse-geocode", response_model=ReverseGeocodeResponse)
def reverse_geocode_coordinates(
    request: ReverseGeocodeRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Convert coordinates to address
    """
    try:
        # Validate coordinates
        if not geocoding_service.validate_coordinates(request.latitude, request.longitude):
            return ReverseGeocodeResponse(
                success=False,
                error="Coordinates are outside Kenya bounds"
            )
        
        result = geocoding_service.reverse_geocode(
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        if result:
            return ReverseGeocodeResponse(
                success=True,
                formatted_address=result.get('formatted_address'),
                street=result.get('street'),
                neighborhood=result.get('neighborhood'),
                city=result.get('city'),
                county=result.get('county'),
                country=result.get('country'),
                provider=result.get('provider')
            )
        else:
            return ReverseGeocodeResponse(
                success=False,
                error="Coordinates could not be reverse geocoded"
            )
            
    except Exception as e:
        return ReverseGeocodeResponse(
            success=False,
            error=f"Reverse geocoding failed: {str(e)}"
        )

@router.get("/nearby", response_model=NearbyPropertiesResponse)
def get_nearby_properties(
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    radius: float = Query(5.0, description="Search radius in kilometers", ge=0.1, le=50),
    limit: int = Query(10, description="Maximum number of properties", ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get properties near a location
    """
    try:
        # Validate coordinates
        if not geocoding_service.validate_coordinates(latitude, longitude):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coordinates are outside Kenya bounds"
            )
        
        # Get nearby properties
        properties = property_service.get_nearby_properties(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius,
            limit=limit
        )
        
        # Convert to response format with proper error handling
        property_list = []
        for prop in properties:
            try:
                # Parse amenities safely
                amenities = []
                if hasattr(prop, 'get_amenities_json'):
                    amenities = prop.get_amenities_json()
                elif prop.amenities:
                    try:
                        import json
                        amenities = json.loads(prop.amenities) if isinstance(prop.amenities, str) else prop.amenities
                    except:
                        amenities = []
                
                prop_dict = {
                    "id": prop.id,
                    "title": prop.title,
                    "property_type": prop.property_type,
                    "rent_amount": prop.rent_amount,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "city": prop.city,
                    "neighborhood": prop.neighborhood or "",
                    "availability_status": prop.availability_status,
                    "verification_status": prop.verification_status,
                    "amenities": amenities,
                    "distance_km": getattr(prop, 'distance_km', None)
                }
                property_list.append(prop_dict)
            except Exception as e:
                # Log the error but continue with other properties
                print(f"Error processing property {prop.id}: {str(e)}")
                continue
        
        return NearbyPropertiesResponse(
            properties=property_list,
            total_found=len(property_list),
            search_radius_km=radius,
            center_latitude=latitude,
            center_longitude=longitude
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding nearby properties: {str(e)}"
        )

@router.post("/properties/{property_id}/update-location")
def update_property_location(
    property_id: int,
    request: LocationUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update property location with automatic geocoding
    """
    # Check if user owns the property or is admin
    property_obj = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    if property_obj.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        updated_property = property_service.update_property_location(
            db=db,
            property_id=property_id,
            address=request.address,
            city=request.city,
            latitude=request.latitude,
            longitude=request.longitude,
            force_geocode=request.force_geocode
        )
        
        if updated_property:
            return {
                "success": True,
                "message": "Property location updated successfully",
                "latitude": updated_property.latitude,
                "longitude": updated_property.longitude,
                "address": updated_property.address,
                "city": updated_property.city
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update property location"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating property location: {str(e)}"
        )

@router.post("/admin/batch-geocode")
def batch_geocode_properties(
    limit: int = Query(100, description="Maximum properties to process", ge=1, le=1000),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    Batch geocode existing properties without coordinates (Admin only)
    """
    try:
        results = property_service.geocode_existing_properties(db, limit=limit)
        return {
            "success": True,
            "message": "Batch geocoding completed",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch geocoding failed: {str(e)}"
        )

@router.get("/validate-coordinates")
def validate_coordinates(
    latitude: float = Query(..., description="Latitude to validate"),
    longitude: float = Query(..., description="Longitude to validate"),
) -> Any:
    """
    Validate if coordinates are within Kenya bounds
    """
    is_valid = geocoding_service.validate_coordinates(latitude, longitude)
    
    return {
        "valid": is_valid,
        "latitude": latitude,
        "longitude": longitude,
        "message": "Coordinates are within Kenya bounds" if is_valid else "Coordinates are outside Kenya bounds"
    }

@router.get("/search-suggestions")
def get_location_suggestions(
    query: str = Query(..., description="Search query for location"),
    limit: int = Query(5, description="Maximum suggestions", ge=1, le=20),
    current_user: Optional[models.User] = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get location suggestions for autocomplete
    """
    try:
        # For now, return Kenya cities/areas. You could enhance this with a proper geocoding service
        kenya_locations = [
            "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Malindi", "Kitale",
            "Garissa", "Kakamega", "Machakos", "Meru", "Nyeri", "Kericho", "Embu", "Migori",
            "Westlands", "Karen", "Kilimani", "Lavington", "Runda", "Muthaiga", "Kileleshwa",
            "South B", "South C", "Hurlingham", "Parklands", "Eastleigh", "Kasarani", "Ruaka"
        ]
        
        # Simple string matching - in production, use a proper search service
        suggestions = [loc for loc in kenya_locations if query.lower() in loc.lower()][:limit]
        
        return {
            "success": True,
            "query": query,
            "suggestions": suggestions,
            "total": len(suggestions)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get suggestions: {str(e)}"
        }
# File: backend/app/services/geocoding_service.py
# Service to convert addresses to coordinates

import requests
import logging
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for geocoding addresses to coordinates"""
    
    def __init__(self):
        # You can use different providers based on your needs
        self.providers = {
            'nominatim': self._geocode_nominatim,
            'google': self._geocode_google,
            'opencage': self._geocode_opencage
        }
        self.default_provider = 'nominatim'  # Free option
    
    def geocode_address(
        self, 
        address: str, 
        city: str = None, 
        country: str = "Kenya",
        provider: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Convert address to coordinates
        
        Args:
            address: Street address
            city: City name
            country: Country name (default: Kenya)
            provider: Geocoding provider to use
            
        Returns:
            Dictionary with lat, lng, and formatted_address or None
        """
        provider = provider or self.default_provider
        
        if provider not in self.providers:
            logger.error(f"Unknown geocoding provider: {provider}")
            return None
        
        # Build full address
        full_address = address
        if city:
            full_address += f", {city}"
        if country:
            full_address += f", {country}"
        
        try:
            return self.providers[provider](full_address)
        except Exception as e:
            logger.error(f"Geocoding failed for '{full_address}': {str(e)}")
            return None
    
    def _geocode_nominatim(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode using OpenStreetMap Nominatim (Free)
        """
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'ke',  # Restrict to Kenya
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'PataBaseFiti/1.0 (property-platform)'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                result = data[0]
                return {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'formatted_address': result.get('display_name', address),
                    'provider': 'nominatim',
                    'confidence': float(result.get('importance', 0.5))
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Nominatim geocoding error: {str(e)}")
            return None
    
    def _geocode_google(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode using Google Maps API (Requires API key)
        """
        if not hasattr(settings, 'GOOGLE_MAPS_API_KEY') or not settings.GOOGLE_MAPS_API_KEY:
            logger.warning("Google Maps API key not configured")
            return None
        
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': settings.GOOGLE_MAPS_API_KEY,
            'region': 'ke'  # Bias results to Kenya
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'formatted_address': result['formatted_address'],
                    'provider': 'google',
                    'confidence': 1.0,  # Google typically has high confidence
                    'place_id': result.get('place_id')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Google geocoding error: {str(e)}")
            return None
    
    def _geocode_opencage(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode using OpenCage API (Freemium)
        """
        if not hasattr(settings, 'OPENCAGE_API_KEY') or not settings.OPENCAGE_API_KEY:
            logger.warning("OpenCage API key not configured")
            return None
        
        url = "https://api.opencagedata.com/geocode/v1/json"
        params = {
            'q': address,
            'key': settings.OPENCAGE_API_KEY,
            'countrycode': 'ke',
            'limit': 1
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['status']['code'] == 200 and data['results']:
                result = data['results'][0]
                geometry = result['geometry']
                
                return {
                    'latitude': geometry['lat'],
                    'longitude': geometry['lng'],
                    'formatted_address': result['formatted'],
                    'provider': 'opencage',
                    'confidence': result['confidence']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"OpenCage geocoding error: {str(e)}")
            return None
    
    def reverse_geocode(
        self, 
        latitude: float, 
        longitude: float, 
        provider: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Convert coordinates to address (reverse geocoding)
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            provider: Geocoding provider to use
            
        Returns:
            Dictionary with address information or None
        """
        provider = provider or self.default_provider
        
        try:
            if provider == 'nominatim':
                return self._reverse_geocode_nominatim(latitude, longitude)
            elif provider == 'google':
                return self._reverse_geocode_google(latitude, longitude)
            elif provider == 'opencage':
                return self._reverse_geocode_opencage(latitude, longitude)
            else:
                logger.error(f"Unknown provider for reverse geocoding: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {str(e)}")
            return None
    
    def _reverse_geocode_nominatim(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """Reverse geocode using Nominatim"""
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'PataBaseFiti/1.0 (property-platform)'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                address = data.get('address', {})
                return {
                    'formatted_address': data.get('display_name'),
                    'street': address.get('road'),
                    'neighborhood': address.get('suburb') or address.get('neighbourhood'),
                    'city': address.get('city') or address.get('town') or address.get('village'),
                    'county': address.get('county'),
                    'country': address.get('country'),
                    'postcode': address.get('postcode'),
                    'provider': 'nominatim'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Nominatim reverse geocoding error: {str(e)}")
            return None
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate if coordinates are within Kenya bounds
        
        Kenya approximate bounds:
        North: 5.0°N, South: -5.0°S
        West: 33.5°E, East: 42.0°E
        """
        return (
            -5.0 <= latitude <= 5.0 and
            33.5 <= longitude <= 42.0
        )

# Create singleton instance
geocoding_service = GeocodingService()
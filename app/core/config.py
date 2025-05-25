# File: backend/app/core/config.py
# Ultra simplified config without env file parsing

import os
from typing import List, Optional

# Default values
DEFAULT_SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
DEFAULT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 11520  # 8 days
DEFAULT_GOOGLE_CLIENT_ID = os.getenv("DEFAULT_GOOGLE_CLIENT_ID")
DEFAULT_GOOGLE_CLIENT_SECRET = os.getenv("DEFAULT_GOOGLE_CLIENT_SECRET")
DEFAULT_UPLOAD_DIRECTORY = "./uploads"
DEFAULT_MAX_UPLOAD_SIZE = 5242880  # 5MB

# Simple settings class
class Settings:
    API_V1_STR: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", DEFAULT_SECRET_KEY)
    ALGORITHM: str = os.getenv("ALGORITHM", DEFAULT_ALGORITHM)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES))
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    OPENCAGE_API_KEY: Optional[str] = os.getenv("OPENCAGE_API_KEY")
    
    # Geocoding settings
    GEOCODING_PROVIDER: str = os.getenv("GEOCODING_PROVIDER", "nominatim")  # nominatim, google, opencage
    GEOCODING_TIMEOUT: int = int(os.getenv("GEOCODING_TIMEOUT", "10"))
    
    # Map settings
    DEFAULT_MAP_ZOOM: int = int(os.getenv("DEFAULT_MAP_ZOOM", "15"))
    MAP_CENTER_LAT: float = float(os.getenv("MAP_CENTER_LAT", "-1.2921"))  # Nairobi
    MAP_CENTER_LNG: float = float(os.getenv("MAP_CENTER_LNG", "36.8219"))  # Nairobi

    # CORS settings - hardcoded for now to avoid parsing issues
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./patabasefiti.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", DEFAULT_GOOGLE_CLIENT_ID)
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", DEFAULT_GOOGLE_CLIENT_SECRET)
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/v1/auth/google/callback"
    )
    
    # M-Pesa settings
    MPESA_CONSUMER_KEY: Optional[str] = os.getenv("MPESA_CONSUMER_KEY")
    MPESA_CONSUMER_SECRET: Optional[str] = os.getenv("MPESA_CONSUMER_SECRET")
    MPESA_SHORTCODE: Optional[str] = os.getenv("MPESA_SHORTCODE")
    MPESA_PASSKEY: Optional[str] = os.getenv("MPESA_PASSKEY")
    MPESA_CALLBACK_URL: Optional[str] = os.getenv("MPESA_CALLBACK_URL")
    
    # File storage settings
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", DEFAULT_UPLOAD_DIRECTORY)
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", DEFAULT_MAX_UPLOAD_SIZE))
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg", 
        "image/png", 
        "image/gif", 
        "image/webp"
    ]

# Create settings instance
settings = Settings()

# Print key settings to verify they loaded correctly
print(f"API_V1_STR: {settings.API_V1_STR}")
print(f"GOOGLE_CLIENT_ID: {settings.GOOGLE_CLIENT_ID}")
print(f"BACKEND_CORS_ORIGINS: {settings.BACKEND_CORS_ORIGINS}")
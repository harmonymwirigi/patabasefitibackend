# File: backend/app/utils/google_auth.py
# Status: COMPLETE
# Dependencies: google.oauth2.id_token, google.auth.transport.requests, app.core.config

from typing import Dict, Any, Optional
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings

def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Google OAuth token and extract user information
    
    Returns:
        Dictionary with user information if token is valid, None otherwise
    """
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        # Check issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None
            
        # Return user information
        return {
            "id": idinfo.get("sub"),
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture")
        }
        
    except Exception as e:
        print(f"Google token verification error: {e}")
        return None
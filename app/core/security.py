from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
import string
import secrets
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def generate_random_password(length: int = 16) -> str:
    """
    Generate a secure random password for users created via OAuth.
    
    Args:
        length: Length of the password to generate, defaults to 16
        
    Returns:
        A secure random password string
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Ensure at least one of each character type
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Make sure the password has at least one uppercase, one lowercase, one digit, and one special character
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)
    
    # If any requirement is not met, try again
    if not (has_upper and has_lower and has_digit and has_special):
        return generate_random_password(length)
    
    return password
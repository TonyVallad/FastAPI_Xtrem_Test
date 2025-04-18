from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
import os
import secrets
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from api.users.schemas import TokenData
from api.logs.logger import logger

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Handle special data types (like lists of scopes)
    if "scopes" in to_encode and isinstance(to_encode["scopes"], list):
        # Make sure all scopes are strings
        to_encode["scopes"] = [str(scope) for scope in to_encode["scopes"]]
    
    # Create JWT token
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT token: {str(e)}")
        raise

def ensure_timezone(dt):
    """Ensure a datetime object has timezone information"""
    if dt and not dt.tzinfo:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def create_refresh_token() -> Tuple[str, datetime]:
    """
    Create a refresh token and its expiration date.
    Returns a tuple of (token_string, expiration_datetime)
    """
    # Generate a secure random token
    token_string = secrets.token_urlsafe(64)
    
    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    return token_string, expires_at

def decode_token(token: str) -> dict:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_tokens_for_user(user_data: Dict, request_info: Optional[Dict] = None) -> Dict:
    """
    Create both access and refresh tokens for a user.
    Returns a dictionary with both tokens and related information.
    """
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=user_data,
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_str, refresh_token_expires = create_refresh_token()
    
    # Return both tokens
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token_str,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "refresh_token_expires_at": refresh_token_expires,
        "user_id": user_data.get("user_id"),
        "issued_by": request_info.get("ip") if request_info else None,
        "device_info": request_info.get("user_agent") if request_info else None
    }

def encrypt_sensitive_data(data: str) -> str:
    """
    Simple encryption for sensitive data.
    In a real production app, you'd use a more secure encryption method.
    """
    # This is a placeholder. In production, use a proper encryption library
    # like cryptography with a secure key management system.
    return f"encrypted_{data}"

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Simple decryption for sensitive data.
    In a real production app, you'd use a more secure decryption method.
    """
    # This is a placeholder. In production, use a proper decryption method
    # corresponding to your encryption method.
    if encrypted_data.startswith("encrypted_"):
        return encrypted_data[10:]
    return encrypted_data 
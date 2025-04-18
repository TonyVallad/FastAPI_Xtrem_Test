from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import os
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.logs.logger import logger
from api.users import crud
from api.users.schemas import TokenData, UserInDB

# Load environment variables
load_dotenv()

# Settings for password hashing and JWT token
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

# Get security settings from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def verify_password(plain_password, hashed_password):
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Generate a password hash"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username and password"""
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    # Update last login time
    crud.update_user_login(db, user.id)
    
    # Log the successful login
    logger.info(f"User {username} logged in successfully")
    
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the specified data and expiration.
    
    Args:
        data (dict): The data to encode in the token
        expires_delta (Optional[timedelta]): How long the token should be valid for
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    # Set the expiration time based on input or default
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration to token data
    to_encode.update({"exp": expire})
    
    # Encode and return the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> UserInDB:
    """Get the current user based on the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get the current admin user"""
    if not current_user.is_admin and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


def has_access(user: UserInDB, requested_user_id: int) -> bool:
    """Check if a user has access to another user's data"""
    # Admins have access to all users
    if user.is_admin or user.role == "ADMIN":
        return True
    # Users only have access to their own data
    return user.id == requested_user_id 
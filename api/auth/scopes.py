"""
Scope-based permission system for the FastAPI Xtrem API.
This module defines available scopes and utility functions for scope validation.
"""
from enum import Enum
from typing import List, Set, Dict, Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from api.users.schemas import TokenData, UserInDB
from api.db.models import User, UserRole
from api.logs.logger import logger
from .security import oauth2_scheme, decode_token, SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from api.db.database import get_db

# Define available scopes
class Scopes(str, Enum):
    # User scopes
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Profile scopes
    PROFILE_READ = "profile:read"
    PROFILE_WRITE = "profile:write"
    
    # Admin scopes
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    
    # System scopes
    STATS_READ = "stats:read"
    LOGS_READ = "logs:read"

# Define role-based scope assignments
ROLE_SCOPES: Dict[UserRole, List[Scopes]] = {
    UserRole.USER: [
        Scopes.USER_READ,        # Users can read their own data
        Scopes.PROFILE_READ,     # Users can read profiles
        Scopes.PROFILE_WRITE,    # Users can update their own profile
    ],
    UserRole.MODERATOR: [
        Scopes.USER_READ,        # Moderators can read user data
        Scopes.PROFILE_READ,     # Moderators can read profiles
        Scopes.PROFILE_WRITE,    # Moderators can update their own profile
        Scopes.STATS_READ,       # Moderators can view statistics
        Scopes.LOGS_READ,        # Moderators can view logs
    ],
    UserRole.ADMIN: [
        Scopes.USER_READ,        # Admins can read all user data
        Scopes.USER_WRITE,       # Admins can modify user data
        Scopes.USER_DELETE,      # Admins can delete users
        Scopes.PROFILE_READ,     # Admins can read all profiles
        Scopes.PROFILE_WRITE,    # Admins can update any profile
        Scopes.ADMIN_READ,       # Admins can access admin features
        Scopes.ADMIN_WRITE,      # Admins can modify admin settings
        Scopes.ADMIN_DELETE,     # Admins can delete admin resources
        Scopes.STATS_READ,       # Admins can view statistics
        Scopes.LOGS_READ,        # Admins can view logs
    ]
}

def get_user_scopes(user: User) -> List[str]:
    """
    Get a list of scopes for a user based on their role.
    """
    try:
        # Convert string role to enum if needed
        user_role = user.role
        if isinstance(user_role, str):
            user_role = UserRole(user_role)
            
        # Return scopes for the user's role
        return ROLE_SCOPES.get(user_role, [])
    except (ValueError, KeyError):
        # If role is invalid, return empty list
        logger.error(f"Invalid role for user {user.username}: {user.role}")
        return []

# Scope-based security dependencies
def get_user_with_scopes(*required_scopes: str):
    """
    Create a dependency that requires specific scopes.
    """
    def dependency(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        # Create error messages for authentication failures
        scopes_str = " ".join(required_scopes)
        authenticate_value = f'Bearer scope="{scopes_str}"'
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            
            if username is None:
                logger.warning("JWT token missing 'sub' claim")
                raise credentials_exception
                
            # Get token scopes (if any)
            token_scopes = payload.get("scopes", [])
            token_data = TokenData(username=username, scopes=token_scopes)
            
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise credentials_exception
            
        # Get the user from the database
        user = db.query(User).filter(User.username == token_data.username).first()
        
        if user is None:
            logger.warning(f"User not found for token with username: {token_data.username}")
            raise credentials_exception
            
        if not user.is_active:
            logger.warning(f"Inactive user tried to access with token: {token_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Check if the user has the required scopes
        if required_scopes:
            # Get user's scopes based on their role
            user_scopes = get_user_scopes(user)
            
            # Convert to set for faster lookup
            user_scope_set = set(user_scopes)
            
            # Check if the user has all required scopes
            for scope in required_scopes:
                if scope not in user_scope_set:
                    logger.warning(
                        f"User {user.username} with role {user.role} doesn't have required scope: {scope}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Not enough permissions. Required scope: {scope}",
                        headers={"WWW-Authenticate": authenticate_value},
                    )
        
        return user
    
    return dependency 
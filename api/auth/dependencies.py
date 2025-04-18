from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from api.db.database import get_db
from api.users import crud
from api.users.schemas import TokenData
from api.logs.logger import logger
from .security import oauth2_scheme, SECRET_KEY, ALGORITHM

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    Dependency to get the current user from a JWT token.
    Can be used to protect routes that require authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            logger.warning("JWT token missing 'sub' claim")
            raise credentials_exception
            
        token_data = TokenData(username=username)
        
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
        
    # Get the user from the database
    user = crud.get_user_by_username(db, username=token_data.username)
    
    if user is None:
        logger.warning(f"User not found for token with username: {token_data.username}")
        raise credentials_exception
        
    if not user.is_active:
        logger.warning(f"Inactive user tried to access with token: {token_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Dependency to get the current active user.
    Additional check on top of get_current_user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_admin_user(current_user = Depends(get_current_user)):
    """
    Dependency to get an admin user.
    Can be used to protect routes that require admin privileges.
    """
    if not current_user.is_admin:
        logger.warning(f"User {current_user.username} tried to access admin-only resource")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user 
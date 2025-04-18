from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta, datetime, timezone

from api.db.database import get_db
from api.logs.logger import logger
from api.auth.security import (
    verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,
    create_tokens_for_user, create_refresh_token, ensure_timezone
)
from api.auth.dependencies import get_current_user, get_current_active_user, get_admin_user
from api.auth.scopes import Scopes, get_user_with_scopes, get_user_scopes
from . import schemas, crud
from api.db.models import User as DBUser, UserRole
from api.users.schemas import RefreshTokenCreate, TokenRefresh, UserInDB, UserCreate, UserUpdate, ProfileUpdate, ActivityLogCreate

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Token endpoint for authentication
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Also issues a refresh token for getting new access tokens.
    """
    # Authenticate the user
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Get user scopes based on role
    user_scopes = get_user_scopes(user)
    
    # Get request information for token tracking
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    request_info = {"ip": client_ip, "user_agent": user_agent}
    
    # Create tokens (both access and refresh)
    token_data = create_tokens_for_user(
        user_data={
            "sub": user.username,
            "scopes": user_scopes,
            "user_id": user.id
        },
        request_info=request_info
    )
    
    # Store refresh token in database
    refresh_token_data = RefreshTokenCreate(
        user_id=user.id,
        token=token_data["refresh_token"],
        expires_at=token_data["refresh_token_expires_at"],
        issued_by=token_data["issued_by"],
        device_info=token_data["device_info"]
    )
    crud.create_refresh_token(db=db, token_data=refresh_token_data)
    
    # Update last login time
    crud.update_user_login(db, user.id)
    
    # Log successful login
    logger.info(f"Successful login for user: {user.username}")
    
    # Create activity log
    activity_log = ActivityLogCreate(
        user_id=user.id,
        action="user_login",
        details=f"User {user.username} logged in from {client_ip}",
        ip_address=client_ip
    )
    crud.create_activity_log(db=db, log=activity_log)
    
    # Return tokens
    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "refresh_token": token_data["refresh_token"],
        "expires_in": token_data["expires_in"]
    }

@router.post("/refresh-token", response_model=schemas.Token)
async def refresh_access_token(
    request: Request,
    refresh_token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Get a new access token using a refresh token.
    Implements token rotation - the old refresh token is invalidated and a new one is issued.
    """
    # Get the refresh token from database
    db_token = crud.get_refresh_token(db, token=refresh_token_data.refresh_token)
    
    # Validate refresh token
    if not db_token:
        logger.warning(f"Invalid refresh token used from IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if token is expired or revoked
    current_time = datetime.now(timezone.utc)
    
    # Ensure expires_at has timezone information
    if db_token.expires_at:
        db_token.expires_at = ensure_timezone(db_token.expires_at)
        db.commit()
        db.refresh(db_token)
    
    # Ensure explicit timezone check
    token_expires_at = ensure_timezone(db_token.expires_at) if db_token.expires_at else None
    
    if db_token.revoked or (token_expires_at and token_expires_at < current_time):
        logger.warning(f"Expired or revoked refresh token used from IP: {request.client.host}")
        # Ensure the token is marked as revoked
        if not db_token.revoked:
            crud.revoke_token(db, token_string=refresh_token_data.refresh_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user
    user = crud.get_user(db, user_id=db_token.user_id)
    if not user or not user.is_active:
        logger.warning(f"Refresh token used for inactive or deleted user from IP: {request.client.host}")
        crud.revoke_token(db, token_string=refresh_token_data.refresh_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Revoke the current refresh token (token rotation for security)
    crud.revoke_token(db, token_string=refresh_token_data.refresh_token)
    
    # Get user scopes
    user_scopes = get_user_scopes(user)
    
    # Get request information for token tracking
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    request_info = {"ip": client_ip, "user_agent": user_agent}
    
    # Create new tokens
    token_data = create_tokens_for_user(
        user_data={
            "sub": user.username,
            "scopes": user_scopes,
            "user_id": user.id
        },
        request_info=request_info
    )
    
    # Store new refresh token in database
    refresh_token_data = RefreshTokenCreate(
        user_id=user.id,
        token=token_data["refresh_token"],
        expires_at=token_data["refresh_token_expires_at"],
        issued_by=token_data["issued_by"],
        device_info=token_data["device_info"]
    )
    crud.create_refresh_token(db=db, token_data=refresh_token_data)
    
    # Log token refresh
    logger.info(f"Refresh token rotated for user: {user.username}")
    
    # Create activity log
    activity_log = ActivityLogCreate(
        user_id=user.id,
        action="token_refresh",
        details=f"User {user.username} refreshed their token from {client_ip}",
        ip_address=client_ip
    )
    crud.create_activity_log(db=db, log=activity_log)
    
    # Return new tokens
    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "refresh_token": token_data["refresh_token"],
        "expires_in": token_data["expires_in"]
    }

@router.post("/revoke-token", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_refresh_token(
    refresh_token_data: TokenRefresh,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Revoke a refresh token, making it invalid for future use"""
    # Get the refresh token from database
    db_token = crud.get_refresh_token(db, token=refresh_token_data.refresh_token)
    
    # Validate token exists and belongs to current user
    if not db_token or db_token.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    # Revoke the token
    crud.revoke_token(db, token_string=refresh_token_data.refresh_token)
    logger.info(f"Refresh token revoked for user: {current_user.username}")
    
    return None

@router.post("/revoke-all-tokens", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_user_tokens(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """Revoke all refresh tokens for the current user"""
    count = crud.revoke_all_user_tokens(db, user_id=current_user.id)
    logger.info(f"Revoked {count} refresh tokens for user: {current_user.username}")
    
    return None

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: DBUser = Depends(get_user_with_scopes(Scopes.USER_READ))):
    """Get the current user's information"""
    return current_user

@router.put("/me", response_model=UserInDB)
async def update_user_profile(
    profile_update: ProfileUpdate,
    request: Request,
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.PROFILE_WRITE)),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.
    Requires user:write and profile:write scopes.
    """
    # Create a UserUpdate object with only the fields that can be updated by the user
    user_update = UserUpdate(
        full_name=profile_update.full_name,
        email=profile_update.email,
        bio=profile_update.bio,
        profile_picture=profile_update.profile_picture
    )
    
    # If password update is requested, add it to the update
    if profile_update.password:
        user_update.password = profile_update.password
    
    # Update the user in the database
    updated_user = crud.update_user(db=db, user_id=current_user.id, user_update=user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log the activity
    client_ip = request.client.host
    activity_log = ActivityLogCreate(
        user_id=current_user.id,
        action="profile_updated",
        details=f"Profile updated by user",
        ip_address=client_ip
    )
    crud.create_activity_log(db=db, log=activity_log)
    
    return updated_user

@router.get("/profile/{username}", response_model=schemas.UserProfile)
async def get_user_profile(
    username: str,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.PROFILE_READ))
):
    """
    Get a user's public profile by username.
    Requires profile:read scope.
    """
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found"
        )
    
    logger.info(f"Profile viewed for user: {username}")
    return user

@router.get("/", response_model=List[schemas.UserList])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.ADMIN_READ, Scopes.USER_READ))
):
    """
    Get a list of all users.
    Requires admin:read and user:read scopes.
    """
    # Check if the current user has admin role
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to list all users")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to list users"
        )
    
    # Get all users with pagination and filtering
    users = crud.get_users(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        role=role,
        is_active=is_active
    )
    logger.info(f"Admin {current_user.username} retrieved {len(users)} users")
    return users

@router.get("/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.USER_READ))
):
    """
    Get a single user by ID.
    Users can access their own data, admins can access any user.
    Requires user:read scope.
    """
    # Check if user is requesting their own data or is an admin
    if user_id != current_user.id and Scopes.ADMIN_READ not in get_user_scopes(current_user):
        logger.warning(f"User {current_user.username} tried to access data for user ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
        
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    logger.info(f"User data retrieved for ID {user_id} by {current_user.username}")
    return user

@router.post("/", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.USER_WRITE))
):
    """
    Create a new user.
    Requires user:write scope.
    """
    # Check if the current user has admin role
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user {current_user.username} attempted to create a user")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create users"
        )
    
    # Check if user with same email already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if user with same username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create the user
    new_user = crud.create_user(db=db, user=user)
    
    # Log the activity
    client_ip = request.client.host
    activity_log = ActivityLogCreate(
        user_id=current_user.id,
        action="user_created",
        details=f"User {new_user.username} created by admin {current_user.username}",
        ip_address=client_ip
    )
    crud.create_activity_log(db=db, log=activity_log)
    
    logger.info(f"Admin {current_user.username} created user {new_user.username}")
    return new_user

@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.USER_WRITE))
):
    """
    Update a user's details.
    Requires user:write scope.
    """
    # Only admins can update other users
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        logger.warning(f"User {current_user.username} attempted to update user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions"
        )
    
    # Check if the user exists
    db_user = crud.get_user(db=db, user_id=user_id)
    if not db_user:
        logger.warning(f"User {current_user.username} attempted to update non-existent user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    # Update the user
    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user_update)
    
    # Log the activity
    client_ip = request.client.host
    activity_log = ActivityLogCreate(
        user_id=current_user.id,
        action="user_updated",
        details=f"User {user_id} updated by {current_user.username}",
        ip_address=client_ip
    )
    crud.create_activity_log(db=db, log=activity_log)
    
    logger.info(f"User {current_user.username} updated user {user_id}")
    return updated_user

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: schemas.PasswordChange,
    request: Request,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.USER_WRITE))
):
    """
    Change the current user's password.
    Requires user:write scope.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        logger.warning(f"Failed password change attempt for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash the new password
    hashed_password = get_password_hash(password_data.new_password)
    
    # Update the password
    current_user.hashed_password = hashed_password
    db.add(current_user)
    db.commit()
    
    # Log the activity
    client_ip = request.client.host
    activity_log = ActivityLogCreate(
        user_id=current_user.id,
        action="password_changed",
        details=f"User {current_user.username} changed their password",
        ip_address=client_ip
    )
    crud.create_activity_log(db=db, log=activity_log)
    
    logger.info(f"Password changed for user: {current_user.username}")
    return None

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.USER_DELETE))
):
    """
    Delete a user.
    Users can delete their own account, admins can delete any user.
    Requires user:delete scope.
    """
    # Check if user is deleting their own account or is an admin
    if user_id != current_user.id and Scopes.ADMIN_DELETE not in get_user_scopes(current_user):
        logger.warning(f"User {current_user.username} tried to delete user ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    username = user.username
    
    crud.delete_user(db=db, user_id=user_id)
    
    # Log the activity (separate from user record since user will be deleted)
    client_ip = request.client.host
    logger.info(f"Deleted user: {username} from {client_ip}")
    
    return None

@router.get("/{user_id}/logs", response_model=List[schemas.ActivityLog])
async def read_user_logs(
    user_id: int, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_user_with_scopes(Scopes.LOGS_READ))
):
    """
    Get a user's activity logs.
    Users can access their own logs, admins can access any user's logs.
    Requires logs:read scope.
    """
    # Check if user is requesting their own logs or is an admin
    if user_id != current_user.id and Scopes.ADMIN_READ not in get_user_scopes(current_user):
        logger.warning(f"User {current_user.username} tried to access logs for user ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # First check if user exists
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logs = crud.get_user_activity_logs(db, user_id=user_id, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(logs)} activity logs for user {user_id}")
    return logs 
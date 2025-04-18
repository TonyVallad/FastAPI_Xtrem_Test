from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, desc, or_
import uuid

from api.db.models import User, ActivityLog, UserRole, RefreshToken
from api.users.schemas import UserCreate, UserUpdate, RefreshTokenCreate, ActivityLogCreate
from api.auth.security import get_password_hash, verify_password, ensure_timezone
from api.logs.logger import logger

# User operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username"""
    return db.query(User).filter(User.username == username).first()

def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
) -> List[User]:
    """
    Retrieve a list of users with optional filtering
    """
    query = db.query(User)
    
    # Apply filters if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.full_name.ilike(search_term))
        )
    
    if role is not None:
        query = query.filter(User.role == role)
        
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    # Check if user with same email or username already exists
    if get_user_by_email(db, user.email):
        logger.warning(f"Attempted to create user with existing email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    if get_user_by_username(db, user.username):
        logger.warning(f"Attempted to create user with existing username: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user object
    hashed_password = get_password_hash(user.password)
    
    # Handle role properly
    if user.role:
        if isinstance(user.role, str):
            # Convert string role to enum
            if user.role.upper() == "USER":
                role = UserRole.USER
            elif user.role.upper() == "MODERATOR":
                role = UserRole.MODERATOR
            elif user.role.upper() == "ADMIN":
                role = UserRole.ADMIN
            else:
                role = UserRole.USER  # Default to USER if unknown role
        else:
            role = user.role
    else:
        role = UserRole.USER
    
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=role,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Add to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log the creation
    create_activity_log(
        db,
        ActivityLogCreate(
            user_id=db_user.id,
            action="user_created",
            details=f"User {db_user.username} created",
            ip_address=None
        )
    )
    
    logger.info(f"Created new user: {db_user.username} (ID: {db_user.id})")
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    Update user information
    """
    db_user = get_user(db, user_id)
    if not db_user:
        logger.warning(f"Attempted to update non-existent user ID: {user_id}")
        return None
        
    # Check if new email already exists
    if user_update.email and user_update.email != db_user.email:
        existing_user = get_user_by_email(db, user_update.email)
        if existing_user and existing_user.id != user_id:
            logger.warning(f"Attempted to update user to existing email: {user_update.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if new username already exists
    if user_update.username and user_update.username != db_user.username:
        existing_user = get_user_by_username(db, user_update.username)
        if existing_user and existing_user.id != user_id:
            logger.warning(f"Attempted to update user to existing username: {user_update.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Update timestamp
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # Apply updates
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"Updated user ID: {db_user.id}")
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user"""
    db_user = get_user(db, user_id)
    if not db_user:
        logger.warning(f"Attempted to delete non-existent user ID: {user_id}")
        return False
    
    # Store username for logging
    username = db_user.username
    
    # Delete user
    db.delete(db_user)
    db.commit()
    
    logger.info(f"Deleted user: {username} (ID: {user_id})")
    return True

def update_user_login(db: Session, user_id: int) -> User:
    """
    Update the last login timestamp for a user
    """
    db_user = get_user(db, user_id)
    
    if not db_user:
        return None
    
    db_user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def count_users(db: Session) -> int:
    """Count total number of users"""
    return db.query(User).count()

def count_active_users(db: Session) -> int:
    """Count active users"""
    return db.query(User).filter(User.is_active == True).count()

def count_admin_users(db: Session) -> int:
    """Count admin users"""
    return db.query(User).filter(User.role == "admin").count()

def get_recent_users(db: Session, limit: int = 5) -> List[User]:
    """Get the most recently registered users"""
    return db.query(User).order_by(User.created_at.desc()).limit(limit).all()

# Activity log operations
def create_activity_log(db: Session, log: ActivityLogCreate) -> ActivityLog:
    """
    Create an activity log in the database
    
    Args:
        db (Session): Database session
        log (ActivityLogCreate): Activity log data
        
    Returns:
        ActivityLog: Created activity log
    """
    db_log = ActivityLog(
        user_id=log.user_id,
        action=log.action,
        details=log.details,
        ip_address=log.ip_address,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_user_activity_logs(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ActivityLog]:
    """Get activity logs for a specific user"""
    return db.query(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()

def get_recent_activity_logs(db: Session, limit: int = 50) -> List[ActivityLog]:
    """Get recent activity logs across all users"""
    return db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()

# Admin dashboard operations
def get_user_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get dashboard statistics"""
    total_users = count_users(db)
    active_users = count_active_users(db)
    admin_users = count_admin_users(db)
    moderator_users = db.query(User).filter(User.role == "moderator").count()
    
    # Count registrations in the last 7 days
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_registrations = db.query(User).filter(User.created_at >= one_week_ago).count()
    
    # Stats dictionary
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "moderator_users": moderator_users,
        "recent_registrations": recent_registrations,
    }

def get_admin_dashboard(db: Session) -> Dict[str, Any]:
    """Get all data needed for the admin dashboard"""
    stats = get_user_dashboard_stats(db)
    recent_users = get_users(db, limit=10)  # Last 10 users
    recent_activity = get_recent_activity_logs(db, limit=20)  # Last 20 activities
    
    return {
        "user_stats": stats,
        "recent_users": recent_users,
        "recent_activity": recent_activity
    }

# Refresh token operations
def create_refresh_token(db: Session, token_data: RefreshTokenCreate) -> RefreshToken:
    """Create a new refresh token"""
    # Ensure expires_at has timezone information
    expires_at = token_data.expires_at
    if expires_at and not expires_at.tzinfo:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    db_token = RefreshToken(
        token=token_data.token,
        user_id=token_data.user_id,
        expires_at=expires_at,
        issued_by=token_data.issued_by,
        device_info=token_data.device_info
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """Get a refresh token by token string"""
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    
    # Ensure token dates have timezone information
    if db_token:
        if db_token.expires_at:
            db_token.expires_at = ensure_timezone(db_token.expires_at)
            
        if db_token.created_at:
            db_token.created_at = ensure_timezone(db_token.created_at)
            
        if db_token.revoked_at:
            db_token.revoked_at = ensure_timezone(db_token.revoked_at)
            
        db.commit()
        db.refresh(db_token)
        
    return db_token

def get_user_refresh_tokens(db: Session, user_id: int) -> List[RefreshToken]:
    """Get all refresh tokens for a user that are still valid"""
    return db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).all()

def revoke_refresh_token(db: Session, token_id: int) -> RefreshToken:
    """Revoke a refresh token"""
    db_token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    
    if not db_token:
        return None
    
    db_token.revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_token)
    
    return db_token

def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoke all refresh tokens for a user"""
    tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    ).all()
    
    count = 0
    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        count += 1
    
    db.commit()
    return count

def cleanup_expired_tokens(db: Session) -> int:
    """Delete expired tokens that are older than 30 days"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    result = db.query(RefreshToken).filter(
        RefreshToken.expires_at < cutoff_date
    ).delete()
    
    db.commit()
    return result

def is_token_valid(db: Session, refresh_token: str) -> bool:
    """Check if a refresh token is valid and not expired"""
    
    # Get current time with timezone
    current_time = datetime.now(timezone.utc)
    
    # Get the token
    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    
    # If token doesn't exist, it's not valid
    if not db_token:
        return False
    
    # Ensure expires_at has timezone
    if db_token.expires_at:
        db_token.expires_at = ensure_timezone(db_token.expires_at)
    
    # Check if it's revoked or expired
    if db_token.revoked or (db_token.expires_at and db_token.expires_at < current_time):
        return False
        
    return True

def revoke_token(db: Session, token_string: str) -> bool:
    """Revoke a refresh token"""
    
    # Find the token
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token_string).first()
    
    if not db_token:
        return False
        
    # Revoke the token
    db_token.revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return True 
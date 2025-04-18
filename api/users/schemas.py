from pydantic import BaseModel, EmailStr, Field, field_validator, HttpUrl
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum

# Enum for user roles
class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

# Enum for theme preferences
class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

# Base User Schema
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

# Schema for creating a user
class UserCreate(UserBase):
    password: str
    profile_picture: Optional[str] = None
    role: Optional[Union[UserRole, str]] = UserRole.USER
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, str):
            try:
                return UserRole(v)
            except ValueError:
                return UserRole.USER
        return v

# Schema for password change
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def passwords_match(cls, v, values):
        if 'current_password' in values.data and v == values.data['current_password']:
            raise ValueError('New password must be different from current password')
        return v

# Schema for updating a user
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    profile_picture: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[Union[UserRole, str]] = None
    bio: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
        
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return UserRole(v)
            except ValueError:
                return UserRole.USER
        return v

# Schema for profile updates by non-admin users
class ProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

# Schema for admin updating a user
class AdminUserUpdate(UserUpdate):
    role: Optional[UserRole] = None
    is_admin: Optional[bool] = None

# Schema for returning a user
class UserInDB(UserBase):
    id: int
    is_active: bool
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    profile_picture: Optional[str] = None
    
    class Config:
        from_attributes = True

# Aliases for backward compatibility
User = UserInDB
UserRead = UserInDB

# Schema for user list display (abbreviated data)
class UserList(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    is_admin: bool
    
    class Config:
        from_attributes = True

# Schema for user profile display
class UserProfile(BaseModel):
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    theme_preference: Theme
    created_at: datetime
    
    class Config:
        from_attributes = True

# Admin dashboard user stats
class UserStats(BaseModel):
    total_users: int
    active_users: int
    admins: int
    moderators: int
    recent_registrations: int
    recent_users: Optional[List[UserInDB]] = None

class AdminDashboard(BaseModel):
    user_stats: UserStats
    recent_users: List[UserList]
    recent_activity: List["ActivityLog"]

# Activity Log schemas
class ActivityLogBase(BaseModel):
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None

class ActivityLogCreate(ActivityLogBase):
    user_id: int

class ActivityLog(ActivityLogBase):
    id: int
    user_id: int
    timestamp: datetime
    user: Optional[UserList] = None
    
    class Config:
        from_attributes = True

# Login schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: int = 1800  # Default 30 minutes in seconds

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: List[str] = []

class RefreshTokenCreate(BaseModel):
    user_id: int
    token: str
    expires_at: datetime
    issued_by: Optional[str] = None
    device_info: Optional[str] = None

class RefreshTokenDB(RefreshTokenCreate):
    id: int
    created_at: datetime
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TokenRefresh(BaseModel):
    refresh_token: str

# Fix circular reference
AdminDashboard.update_forward_refs() 
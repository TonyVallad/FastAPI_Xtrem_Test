from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from .database import Base

def generate_uuid():
    """Generate a string UUID"""
    return str(uuid.uuid4())

class UserRole(enum.Enum):
    """Enum for user roles with increasing privileges"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

class Theme(enum.Enum):
    """Theme preferences"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

class User(Base):
    """User model for authentication and profile information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile information
    full_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Preferences
    theme_preference = Column(Enum(Theme), default=Theme.SYSTEM)
    email_notifications = Column(Boolean, default=True)
    
    # Role and active status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Legacy field, use role instead for new code
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    logs = relationship("ActivityLog", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"
        
class ActivityLog(Base):
    """Activity log for user actions"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="logs")
    
    def __repr__(self):
        return f"<ActivityLog {self.action} by User {self.user_id}>"

class RefreshToken(Base):
    """Refresh token for JWT authentication"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional fields for security tracking
    issued_by = Column(String, nullable=True)  # IP or device that requested the token
    device_info = Column(String, nullable=True)  # Information about the requesting device/browser
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def is_valid(self):
        """Check if the refresh token is still valid"""
        current_time = func.now()
        return not self.revoked and self.expires_at > current_time
    
    def __repr__(self):
        return f"<RefreshToken {self.id} for User {self.user_id}>" 
"""
Tests for the scope-based authorization system.
"""
import pytest
from fastapi import FastAPI, Depends, HTTPException, security
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.users.schemas import UserCreate, User as UserSchema
from api.db.models import User, UserRole
from api.auth.scopes import Scopes, get_user_scopes, get_user_with_scopes
from api.auth.security import create_access_token
from api.users import crud

# Test data
test_user_data = {
    "user": {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "role": "user"
    },
    "moderator": {
        "username": "testmod",
        "email": "testmod@example.com",
        "password": "testpassword",
        "role": "moderator"
    },
    "admin": {
        "username": "testadmin",
        "email": "testadmin@example.com",
        "password": "testpassword",
        "role": "admin"
    }
}

def create_test_token(username, role):
    """Helper function to create a test token with appropriate scopes"""
    # Create a mock user with the given role
    user = User(username=username, role=role)
    
    # Get scopes for this role
    scopes = get_user_scopes(user)
    
    # Create token with scopes
    token = create_access_token(
        data={
            "sub": username,
            "scopes": scopes
        }
    )
    return token

def test_user_scopes():
    """Test that users have the expected scopes"""
    # Create test users with different roles
    user = User(username="testuser", role=UserRole.USER)
    moderator = User(username="testmod", role=UserRole.MODERATOR)
    admin = User(username="testadmin", role=UserRole.ADMIN)
    
    # Get and verify scopes
    user_scopes = get_user_scopes(user)
    mod_scopes = get_user_scopes(moderator)
    admin_scopes = get_user_scopes(admin)
    
    # Basic user should have limited scopes
    assert Scopes.USER_READ in user_scopes
    assert Scopes.PROFILE_READ in user_scopes
    assert Scopes.PROFILE_WRITE in user_scopes
    assert Scopes.USER_DELETE not in user_scopes  # Regular users can't delete others
    assert Scopes.ADMIN_READ not in user_scopes   # Regular users don't have admin access
    
    # Moderators should have more scopes
    assert Scopes.USER_READ in mod_scopes
    assert Scopes.PROFILE_READ in mod_scopes
    assert Scopes.STATS_READ in mod_scopes
    assert Scopes.LOGS_READ in mod_scopes
    assert Scopes.ADMIN_READ not in mod_scopes  # Moderators don't have admin access
    
    # Admins should have all scopes
    assert Scopes.USER_READ in admin_scopes
    assert Scopes.USER_WRITE in admin_scopes
    assert Scopes.USER_DELETE in admin_scopes
    assert Scopes.PROFILE_READ in admin_scopes
    assert Scopes.PROFILE_WRITE in admin_scopes
    assert Scopes.ADMIN_READ in admin_scopes
    assert Scopes.ADMIN_WRITE in admin_scopes
    assert Scopes.ADMIN_DELETE in admin_scopes
    assert Scopes.STATS_READ in admin_scopes
    assert Scopes.LOGS_READ in admin_scopes

def test_token_with_scopes(client, test_db):
    """Test that tokens include the correct scopes"""
    # First create the test users in the database
    from api.users.auth import get_password_hash
    
    # Create test users
    test_user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        role=UserRole.USER,
        is_active=True
    )
    
    test_admin = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    
    # Add users to the database
    test_db.add(test_user)
    test_db.add(test_admin)
    test_db.commit()
    test_db.refresh(test_user)
    test_db.refresh(test_admin)
    
    # Create tokens for different user roles
    user_token = create_access_token(
        data={
            "sub": test_user.username,
            "scopes": get_user_scopes(test_user),
            "user_id": test_user.id
        }
    )
    
    admin_token = create_access_token(
        data={
            "sub": test_admin.username,
            "scopes": get_user_scopes(test_admin),
            "user_id": test_admin.id
        }
    )
    
    # Test user endpoint access
    user_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Regular user should be able to access their profile
    assert user_response.status_code == 200
    
    # Regular user should not be able to access admin endpoints
    user_admin_response = client.get(
        "/admin/dashboard",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert user_admin_response.status_code == 403 
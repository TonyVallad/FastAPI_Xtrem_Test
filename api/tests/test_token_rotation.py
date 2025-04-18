"""
Tests for the refresh token rotation system.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from api.users.schemas import UserCreate, TokenRefresh
from api.db.models import User, RefreshToken
from api.users import crud
from api.auth.security import verify_password, get_password_hash, ensure_timezone

# Test data
test_user = {
    "username": "rotationtest",
    "email": "rotationtest@example.com",
    "password": "testpassword",
}

def create_test_user(db: Session):
    """Helper function to create a test user"""
    # Check if user already exists
    user = crud.get_user_by_username(db, username=test_user["username"])
    if user:
        return user
        
    # Create a new user
    user_data = UserCreate(
        username=test_user["username"],
        email=test_user["email"],
        password=test_user["password"]
    )
    return crud.create_user(db=db, user=user_data)

def fix_token_timezone(db: Session, token_string: str):
    """Fix timezone information for token in database"""
    token = db.query(RefreshToken).filter(RefreshToken.token == token_string).first()
    if token:
        # Add timezone info to expires_at if missing
        if token.expires_at:
            token.expires_at = ensure_timezone(token.expires_at)
            
        # Add timezone info to created_at if missing
        if token.created_at:
            token.created_at = ensure_timezone(token.created_at)
            
        # Add timezone info to revoked_at if missing
        if token.revoked_at:
            token.revoked_at = ensure_timezone(token.revoked_at)
            
        db.commit()
        db.refresh(token)
    return token

def test_login_returns_refresh_token(client, test_db):
    """Test that login endpoint returns both access and refresh tokens."""
    user = create_test_user(test_db)
    
    response = client.post(
        "/users/token",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Check response
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] > 0
    
    # Check that the refresh token was stored in the database
    refresh_token = token_data["refresh_token"]
    
    # Fix token timezone in database
    fix_token_timezone(test_db, refresh_token)
    
    db_token = test_db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    assert db_token is not None
    assert db_token.user_id == user.id
    assert not db_token.revoked

def test_refresh_token_rotation(client, test_db):
    """Test that using a refresh token returns new access and refresh tokens."""
    user = create_test_user(test_db)
    
    login_response = client.post(
        "/users/token",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Get the refresh token
    first_token_data = login_response.json()
    first_refresh_token = first_token_data["refresh_token"]
    
    # Fix token timezone in database
    fix_token_timezone(test_db, first_refresh_token)
    
    # Use the refresh token to get a new access token
    refresh_response = client.post(
        "/users/refresh-token",
        json={"refresh_token": first_refresh_token}
    )
    
    # Check the response
    assert refresh_response.status_code == 200
    second_token_data = refresh_response.json()
    assert "access_token" in second_token_data
    assert "refresh_token" in second_token_data
    assert second_token_data["refresh_token"] != first_refresh_token
    
    # Check that the old token was revoked
    old_db_token = test_db.query(RefreshToken).filter(RefreshToken.token == first_refresh_token).first()
    assert old_db_token is not None
    assert old_db_token.revoked
    assert old_db_token.revoked_at is not None
    
    # Check that the new token is in the database
    new_db_token = test_db.query(RefreshToken).filter(RefreshToken.token == second_token_data["refresh_token"]).first()
    assert new_db_token is not None
    assert new_db_token.user_id == user.id
    assert not new_db_token.revoked
    
    # Try to use the old token again - should fail
    reuse_response = client.post(
        "/users/refresh-token",
        json={"refresh_token": first_refresh_token}
    )
    assert reuse_response.status_code == 401

def test_revoke_token(client, test_db):
    """Test that a refresh token can be revoked."""
    user = create_test_user(test_db)
    
    login_response = client.post(
        "/users/token",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Get the refresh token
    token_data = login_response.json()
    refresh_token = token_data["refresh_token"]
    access_token = token_data["access_token"]
    
    # Fix token timezone in database
    fix_token_timezone(test_db, refresh_token)
    
    # Revoke the refresh token
    revoke_response = client.post(
        "/users/revoke-token",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Check the response
    assert revoke_response.status_code == 204
    
    # Check that the token was revoked
    db_token = test_db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    assert db_token is not None
    assert db_token.revoked
    assert db_token.revoked_at is not None
    
    # Try to use the revoked token - should fail
    refresh_response = client.post(
        "/users/refresh-token",
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 401 
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
import base64
import json
from datetime import datetime, timedelta

from api.users.schemas import UserCreate
from api.auth.security import get_password_hash
from api.tests.conftest import create_test_user
from api.db.models import UserRole

def test_login_for_access_token(client: TestClient, test_db: Session):
    """Test login and token generation"""
    # Create a test user with a hashed password
    user_data = UserCreate(
        email="auth_test@example.com",
        username="auth_test_user",
        password="test_password123"
    )
    
    # Create with properly hashed password
    create_test_user(
        db=test_db, 
        username=user_data.username, 
        email=user_data.email
    )
    
    # Login with the user
    login_data = {
        "username": user_data.username,
        "password": "password123",
    }
    
    response = client.post("/users/token", data=login_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0

def test_login_wrong_password(client: TestClient, test_db: Session):
    """Test login with wrong password"""
    # Create a test user with a hashed password
    user_data = UserCreate(
        email="wrong_pw_test@example.com",
        username="wrong_pw_user",
        password="test_password123"
    )
    
    # Create with properly hashed password
    create_test_user(
        db=test_db, 
        username=user_data.username, 
        email=user_data.email
    )
    
    # Login with wrong password
    login_data = {
        "username": user_data.username,
        "password": "wrong_password",
    }
    
    response = client.post("/users/token", data=login_data)
    
    # Check response
    assert response.status_code == 401
    assert "detail" in response.json()

def test_me_endpoint(client: TestClient, test_db: Session):
    """Test the /me endpoint with authentication"""
    # Create a test user with a hashed password
    user_data = UserCreate(
        email="me_test@example.com",
        username="me_test_user",
        password="test_password123"
    )
    
    # Create user
    user = create_test_user(
        db=test_db, 
        username=user_data.username, 
        email=user_data.email
    )
    
    # Login with the user
    login_data = {
        "username": user_data.username,
        "password": "password123",
    }
    
    login_response = client.post("/users/token", data=login_data)
    token = login_response.json()["access_token"]
    
    # Access /me endpoint with token
    response = client.get(
        "/users/me", 
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email
    
def test_unauthorized_access(client: TestClient):
    """Test accessing protected endpoint without authentication"""
    # Try to access /me endpoint without token
    response = client.get("/users/me")
    
    # Check response
    assert response.status_code == 401
    
def test_admin_only_access(client: TestClient, test_db: Session):
    """Test admin-only access control"""
    # Create a regular user
    regular_user = UserCreate(
        email="regular@example.com",
        username="regular_user",
        password="test_password123"
    )
    created_user = create_test_user(
        db=test_db, 
        username=regular_user.username, 
        email=regular_user.email
    )
    
    # Create an admin user
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123",
        role="admin"  # Explicitly set role to admin
    )
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )
    
    # Login as regular user
    login_response = client.post("/users/token", data={
        "username": regular_user.username,
        "password": "password123",
    })
    regular_token = login_response.json()["access_token"]
    
    # Login as admin user
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    admin_token = login_response.json()["access_token"]
    
    # Try to access users list as regular user (should fail)
    response = client.get(
        "/users/", 
        headers={"Authorization": f"Bearer {regular_token}"}
    )
    assert response.status_code == 403
    
    # Try to access users list as admin (should succeed)
    response = client.get(
        "/users/", 
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2 
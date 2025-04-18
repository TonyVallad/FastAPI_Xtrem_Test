from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from fastapi import status
import json

from api.users.crud import create_user
from api.users.schemas import UserCreate, UserUpdate
from api.auth.security import get_password_hash
from api.tests.conftest import create_test_user
from api.db.models import UserRole, User

def test_create_user(client: TestClient, test_db: Session):
    """Test creating a new user"""
    # Create an admin user for authentication
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123"
    )
    hashed_password = get_password_hash(admin_user.password)
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )
    
    # Set admin role and permissions
    admin.is_admin = True
    test_db.commit()
    
    # Login as admin
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    assert login_response.status_code == 200
    admin_token = login_response.json()["access_token"]
    
    # Create a new user
    user_data = {
        "email": "new_user@example.com",
        "username": "new_user",
        "password": "new_password123",
        "full_name": "New User"
    }
    
    response = client.post(
        "/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]
    assert "password" not in data
    
    # Verify user was created in DB
    created_user = test_db.query(User).filter(User.email == user_data["email"]).first()
    assert created_user is not None
    assert created_user.email == user_data["email"]
    assert created_user.username == user_data["username"]
    
def test_create_user_duplicate_email(client: TestClient, test_db: Session):
    """Test creating a user with an email that already exists"""
    # Create a user first
    user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    create_test_user(
        db=test_db, 
        username=user.username, 
        email=user.email
    )
    
    # Create an admin user for authentication
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123"
    )
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )
    
    # Set admin role
    admin.is_admin = True
    test_db.commit()
    
    # Login as admin
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    admin_token = login_response.json()["access_token"]
    
    # Try to create user with same email
    response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "different_user",
            "password": "password123"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response indicates duplicate email
    assert response.status_code == 400
    assert "Email already registered" in response.text
    
def test_read_users(client: TestClient, test_db: Session):
    """Test getting a list of users"""
    # Create some test users
    user1 = UserCreate(
        email="user1@example.com",
        username="user1",
        password="password123"
    )
    user2 = UserCreate(
        email="user2@example.com",
        username="user2",
        password="password123"
    )

    create_test_user(
        db=test_db, 
        username=user1.username, 
        email=user1.email
    )
    
    create_test_user(
        db=test_db, 
        username=user2.username, 
        email=user2.email
    )
    
    # Create an admin user for authentication
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123"
    )
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )
    
    # Set admin role
    admin.is_admin = True
    test_db.commit()
    
    # Login as admin
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    admin_token = login_response.json()["access_token"]
    
    # Get users
    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # Should have at least our two test users
    
def test_read_user(client: TestClient, test_db: Session):
    """Test getting a specific user"""
    # Create a test user
    user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Test User",
        bio="This is a test user"
    )

    created_user = create_test_user(
        db=test_db, 
        username=user.username, 
        email=user.email
    )
    
    # Set bio field directly since it's not in UserCreate
    created_user.bio = "This is a test user"
    test_db.commit()

    # Create an admin user for authentication
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123"
    )
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )
    
    # Set admin role
    admin.is_admin = True
    test_db.commit()
    
    # Login as admin
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    admin_token = login_response.json()["access_token"]
    
    # Get user
    response = client.get(
        f"/users/{created_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["username"] == user.username
    assert data["full_name"] == user.full_name
    if "bio" in data:
        assert data["bio"] == "This is a test user"
    
def test_read_user_not_found(client: TestClient, test_db: Session):
    """Test getting a user that doesn't exist"""
    # Create an admin user for authentication
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123"
    )
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )
    
    # Set admin role
    admin.is_admin = True
    test_db.commit()
    
    # Login as admin
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    admin_token = login_response.json()["access_token"]
    
    # Get nonexistent user
    response = client.get(
        "/users/999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 404 
    
def test_update_user(client: TestClient, test_db: Session):
    """Test updating a user"""
    # Create a test user
    user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Original Name"
    )

    created_user = create_test_user(
        db=test_db, 
        username=user.username, 
        email=user.email
    )

    # Create an admin user for authentication
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123"
    )
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )

    # Set admin role
    admin.is_admin = True
    test_db.commit()

    # Login as admin
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    admin_token = login_response.json()["access_token"]

    # Update user
    update_data = {
        "full_name": "Updated Name",
        "bio": "Updated bio"
    }

    response = client.put(
        f"/users/{created_user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    
    # Refresh the created_user from database to see changes
    test_db.refresh(created_user)
    assert created_user.full_name == update_data["full_name"]
    
def test_delete_user(client: TestClient, test_db: Session):
    """Test deleting a user"""
    # Create a test user
    user = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    created_user = create_test_user(
        db=test_db, 
        username=user.username, 
        email=user.email
    )
    
    # Create an admin user for authentication
    admin_user = UserCreate(
        email="admin@example.com",
        username="admin_user",
        password="admin_password123"
    )
    admin = create_test_user(
        db=test_db, 
        username=admin_user.username, 
        email=admin_user.email,
        role=UserRole.ADMIN
    )
    
    # Set admin role
    admin.is_admin = True
    test_db.commit()
    
    # Login as admin
    login_response = client.post("/users/token", data={
        "username": admin_user.username,
        "password": "password123",
    })
    admin_token = login_response.json()["access_token"]
    
    # Delete user
    response = client.delete(
        f"/users/{created_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Check response
    assert response.status_code == 204
    
    # Verify user was deleted
    deleted_user = test_db.query(User).filter(User.id == created_user.id).first()
    assert deleted_user is None 
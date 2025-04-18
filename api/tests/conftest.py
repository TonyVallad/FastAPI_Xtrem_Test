import pytest
from fastapi.testclient import TestClient
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

from api.db.database import Base, get_db
from api.db.models import User, UserRole
from api.users.schemas import UserCreate
from datetime import datetime, timezone
from api.auth.security import get_password_hash

from api.main import app

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create a test SessionLocal
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh database for each test.
    """
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a db session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a test client for FastAPI with the test database.
    """
    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Reset the overrides
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def test_user(test_db):
    """
    Create and return a test user.
    """
    return create_test_user(test_db)

@pytest.fixture(scope="function")
def admin_user(test_db):
    """
    Create and return an admin user.
    """
    return create_test_user(test_db, username="admin", email="admin@example.com", role=UserRole.ADMIN)

def create_test_user(db: Session, username: str = "testuser", email: str = "test@example.com", role: UserRole = UserRole.USER) -> User:
    """Create a test user with the given attributes"""
    hashed_password = get_password_hash("password123")
    
    # Create a user object
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name="Test User",
        role=role,
        is_active=True,
        is_admin=(role == UserRole.ADMIN),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Add to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user 
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

def test_db_status(client: TestClient, test_db: Session):
    """Test the database status endpoint"""
    response = client.get("/db/status")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert "type" in data
    
    # For SQLite test database
    if data["type"].lower() == "sqlite":
        assert "file" in data
    else:
        assert "host" in data
        assert "database" in data

def test_db_health(client: TestClient, test_db: Session):
    """Test the database health endpoint"""
    response = client.get("/db/health")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "health" in data
    assert "latency_ms" in data
    assert "tables_count" in data
    assert "database_type" in data
    
    # Latency should be a non-negative number
    assert data["latency_ms"] >= 0
    
    # Tables count should include the test tables we've created
    # In our case, users and activity_logs at minimum
    assert data["tables_count"] >= 2 
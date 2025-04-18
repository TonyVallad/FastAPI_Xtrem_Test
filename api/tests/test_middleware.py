from fastapi.testclient import TestClient
import pytest

def test_request_logging_middleware(client: TestClient):
    """Test that the request logging middleware properly handles requests"""
    # Make a request that should be logged
    response = client.get("/")
    assert response.status_code == 200
    
    # The test passes if no exception is raised during the request
    # The actual logging is verified indirectly since we can't easily check the log files

def test_middleware_error_handling(client: TestClient):
    """Test that the middleware properly handles errors"""
    # Make a request to a non-existent endpoint to trigger a 404
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    
    # The middleware should still handle this gracefully without exceptions
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

def test_middleware_headers(client: TestClient):
    """Test that CORS middleware adds appropriate headers"""
    # Make a preflight request
    headers = {
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
        "Origin": "http://testclient.example.com"
    }
    response = client.options("/", headers=headers)
    
    # Check CORS headers
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers 
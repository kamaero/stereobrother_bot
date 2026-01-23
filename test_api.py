#!/usr/bin/env python3
"""
Minimal API test script for StereoBrother Bot.
This is a simplified version for testing purposes.
"""

import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.main import app


def test_health_endpoint():
    """Test the health endpoint."""
    print("Testing health endpoint...")

    # Create a test client
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Make request
    response = client.get("/health")

    # Check response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data["status"] == "healthy", f"Expected 'healthy', got {data.get('status')}"
    assert "version" in data, "Response should contain 'version'"
    assert "environment" in data, "Response should contain 'environment'"

    print("✓ Health endpoint test passed")
    return True


def test_root_endpoint():
    """Test the root endpoint."""
    print("Testing root endpoint...")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "message" in data, "Response should contain 'message'"
    assert "version" in data, "Response should contain 'version'"

    print("✓ Root endpoint test passed")
    return True


def test_user_profile_endpoint():
    """Test the user profile endpoint (requires authentication)."""
    print("Testing user profile endpoint...")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    # This endpoint requires authentication
    # For testing, we'll skip the actual authentication
    response = client.get("/api/user/profile")

    # Should return 401 Unauthorized without token
    assert response.status_code == 401, (
        f"Expected 401 without auth, got {response.status_code}"
    )

    print("✓ User profile endpoint test passed (correctly requires auth)")
    return True


def test_audio_endpoints():
    """Test audio processing endpoints."""
    print("Testing audio endpoints...")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test endpoints that require authentication
    endpoints = [
        ("/api/audio/upload", "POST"),
        ("/api/audio/enhance", "POST"),
        ("/api/audio/denoise", "POST"),
        ("/api/audio/separate", "POST"),
        ("/api/audio/master", "POST"),
    ]

    for endpoint, method in endpoints:
        if method == "POST":
            response = client.post(endpoint, json={})
        else:
            response = client.get(endpoint)

        # All should return 401 without authentication
        assert response.status_code == 401, (
            f"Expected 401 for {endpoint}, got {response.status_code}"
        )

    print("✓ Audio endpoints test passed (all require auth)")
    return True


def test_auth_endpoints():
    """Test authentication endpoints."""
    print("Testing auth endpoints...")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test registration
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
        },
    )

    assert response.status_code == 200, (
        f"Expected 200 for registration, got {response.status_code}"
    )
    data = response.json()
    assert "user_id" in data, "Registration response should contain 'user_id'"

    # Test login
    response = client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "testpass123"}
    )

    assert response.status_code == 200, (
        f"Expected 200 for login, got {response.status_code}"
    )
    data = response.json()
    assert "access_token" in data, "Login response should contain 'access_token'"

    print("✓ Auth endpoints test passed")
    return True


def test_subscription_endpoints():
    """Test subscription endpoints."""
    print("Testing subscription endpoints...")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test subscription creation (requires auth)
    response = client.post("/api/subscription/create", json={})
    assert response.status_code == 401, (
        f"Expected 401 for subscription create, got {response.status_code}"
    )

    # Test subscription status (requires auth)
    response = client.get("/api/subscription/status")
    assert response.status_code == 401, (
        f"Expected 401 for subscription status, got {response.status_code}"
    )

    print("✓ Subscription endpoints test passed (require auth)")
    return True


def test_task_endpoints():
    """Test task endpoints."""
    print("Testing task endpoints...")

    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Test task status (requires auth)
    response = client.get("/api/task/test_task_123")
    assert response.status_code == 401, (
        f"Expected 401 for task status, got {response.status_code}"
    )

    # Test history (requires auth)
    response = client.get("/api/history")
    assert response.status_code == 401, (
        f"Expected 401 for history, got {response.status_code}"
    )

    print("✓ Task endpoints test passed (require auth)")
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running StereoBrother Bot API Tests")
    print("=" * 60)

    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("User Profile Endpoint", test_user_profile_endpoint),
        ("Audio Endpoints", test_audio_endpoints),
        ("Auth Endpoints", test_auth_endpoints),
        ("Subscription Endpoints", test_subscription_endpoints),
        ("Task Endpoints", test_task_endpoints),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                print(f"  ✓ PASSED")
                passed += 1
            else:
                print(f"  ✗ FAILED")
                failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install test dependencies: pip install pytest httpx")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

"""Shared pytest fixtures for the CrossCurrent Finance API test suite."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read from frontend .env
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.strip().split("=", 1)[1].rstrip("/")
                    break
    except FileNotFoundError:
        pass

ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="session")
def base_url():
    """Base URL for all API calls."""
    assert BASE_URL, "REACT_APP_BACKEND_URL not set"
    return BASE_URL


@pytest.fixture(scope="session")
def admin_token(base_url):
    """Master admin JWT token, obtained once per session."""
    resp = requests.post(f"{base_url}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """Authorization headers for master admin."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def admin_user(base_url, admin_headers):
    """Full admin user object from /api/auth/me."""
    resp = requests.get(f"{base_url}/api/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    return resp.json()

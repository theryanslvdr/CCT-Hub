"""Comprehensive tests for /api/auth/* endpoints (auth_routes.py)."""
import pytest
import requests


class TestAuthLogin:
    """POST /api/auth/login"""

    def test_login_success(self, base_url):
        resp = requests.post(f"{base_url}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "iam@ryansalvador.com"
        assert data["user"]["role"] == "master_admin"
        assert "id" in data["user"]
        assert "full_name" in data["user"]

    def test_login_wrong_password(self, base_url):
        resp = requests.post(f"{base_url}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401
        assert "detail" in resp.json()

    def test_login_nonexistent_email(self, base_url):
        resp = requests.post(f"{base_url}/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "whatever",
        })
        assert resp.status_code in [401, 404]

    def test_login_missing_fields(self, base_url):
        resp = requests.post(f"{base_url}/api/auth/login", json={})
        assert resp.status_code == 422  # validation error


class TestAuthMe:
    """GET /api/auth/me"""

    def test_me_authenticated(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "iam@ryansalvador.com"
        assert data["role"] == "master_admin"
        assert "id" in data

    def test_me_no_token(self, base_url):
        resp = requests.get(f"{base_url}/api/auth/me")
        assert resp.status_code in [401, 403]

    def test_me_invalid_token(self, base_url):
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        resp = requests.get(f"{base_url}/api/auth/me", headers=headers)
        assert resp.status_code == 401


class TestAuthVerifyPassword:
    """POST /api/auth/verify-password"""

    def test_verify_correct_password(self, base_url, admin_headers):
        resp = requests.post(
            f"{base_url}/api/auth/verify-password",
            headers=admin_headers,
            json={"password": "admin123"},
        )
        assert resp.status_code == 200

    def test_verify_wrong_password(self, base_url, admin_headers):
        resp = requests.post(
            f"{base_url}/api/auth/verify-password",
            headers=admin_headers,
            json={"password": "wrong"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False


class TestAuthForgotPassword:
    """POST /api/auth/forgot-password — just validates it doesn't crash."""

    def test_forgot_password_nonexistent(self, base_url):
        resp = requests.post(
            f"{base_url}/api/auth/forgot-password",
            json={"email": "nonexistent@test.com"},
        )
        # Should return 200 (not leak user existence) or 404
        assert resp.status_code in [200, 404]

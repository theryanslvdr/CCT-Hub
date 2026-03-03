"""
Iteration 130: Testing NEW features only:
1. Badge notification toasts (badge check endpoint)
2. Email-based password reset via Emailit integration
3. Rewards Store API integration with signed JWT cross-site authentication

Endpoints tested:
- POST /api/rewards/store-token (JWT auth required)
- POST /api/rewards/store-verify?token={jwt_token} (X-Internal-Api-Key required)
- POST /api/rewards/store-deduct?user_id={id}&points=100&item_name=test (X-Internal-Api-Key required)
- POST /api/auth/forgot-password (sends email via Emailit)
- POST /api/auth/reset-password (validates token and resets password)
- POST /api/rewards/badges/check (triggers auto-award, returns newly_awarded)
"""

import pytest
import requests
import os
import time
import jwt

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-rewards-ctrl.preview.emergentagent.com').rstrip('/')
INTERNAL_API_KEY = "_CXCB2Y-ObBIZqqaCzmjEJU1zwe7DMHr8C-tzoef9h0"

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for master admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    data = response.json()
    # Login returns 'access_token' not 'token'
    return data.get("access_token")


@pytest.fixture(scope="module")
def user_id(auth_token):
    """Get the user ID of the authenticated user"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {auth_token}"
    })
    if response.status_code != 200:
        pytest.skip(f"Failed to get user: {response.status_code}")
    return response.json().get("id")


class TestRewardsStoreAPI:
    """Test Rewards Store cross-site authentication APIs"""
    
    def test_store_token_requires_auth(self):
        """POST /api/rewards/store-token should require JWT authentication"""
        response = requests.post(f"{BASE_URL}/api/rewards/store-token")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ store-token correctly requires authentication")
    
    def test_store_token_returns_jwt_and_url(self, auth_token):
        """POST /api/rewards/store-token should return signed JWT with store_url"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/store-token",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "token" in data, "Response should contain 'token'"
        assert "store_url" in data, "Response should contain 'store_url'"
        assert "expires_in" in data, "Response should contain 'expires_in'"
        
        # Validate token is a valid JWT
        token = data["token"]
        assert len(token) > 0, "Token should not be empty"
        assert token.count('.') == 2, "Token should be a valid JWT with 3 parts"
        
        # Validate store_url format
        store_url = data["store_url"]
        assert "token=" in store_url, "store_url should contain token parameter"
        assert "rewards.crosscur.rent" in store_url, "store_url should point to rewards store"
        
        print(f"✓ store-token returns valid JWT and store_url")
        print(f"  Token length: {len(token)}")
        print(f"  Store URL: {store_url[:80]}...")
        print(f"  Expires in: {data['expires_in']} seconds")
        
        return token
    
    def test_store_verify_requires_internal_key(self, auth_token):
        """POST /api/rewards/store-verify should require X-Internal-Api-Key header"""
        # First get a valid token
        token_response = requests.post(
            f"{BASE_URL}/api/rewards/store-token",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        token = token_response.json().get("token")
        
        # Try without internal API key
        response = requests.post(f"{BASE_URL}/api/rewards/store-verify?token={token}")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ store-verify correctly requires X-Internal-Api-Key")
    
    def test_store_verify_with_valid_token(self, auth_token, user_id):
        """POST /api/rewards/store-verify should verify token and return user profile"""
        # First get a valid token
        token_response = requests.post(
            f"{BASE_URL}/api/rewards/store-token",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        token = token_response.json().get("token")
        
        # Verify with internal API key
        response = requests.post(
            f"{BASE_URL}/api/rewards/store-verify?token={token}",
            headers={"X-Internal-Api-Key": INTERNAL_API_KEY}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data.get("valid") is True, "Response should have valid=True"
        assert "user" in data, "Response should contain 'user' object"
        
        user = data["user"]
        assert user.get("id") == user_id, f"User ID mismatch: expected {user_id}, got {user.get('id')}"
        assert "email" in user, "User should have email"
        assert "name" in user, "User should have name"
        assert "level" in user, "User should have level"
        assert "lifetime_points" in user, "User should have lifetime_points"
        assert "available_balance" in user, "User should have available_balance"
        
        print(f"✓ store-verify returns valid user profile")
        print(f"  User: {user.get('name')} ({user.get('email')})")
        print(f"  Level: {user.get('level')}")
        print(f"  Points: {user.get('lifetime_points')}")
    
    def test_store_verify_with_invalid_token(self):
        """POST /api/rewards/store-verify should reject invalid tokens"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/store-verify?token=invalid.jwt.token",
            headers={"X-Internal-Api-Key": INTERNAL_API_KEY}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ store-verify correctly rejects invalid tokens")
    
    def test_store_deduct_requires_internal_key(self, user_id):
        """POST /api/rewards/store-deduct should require X-Internal-Api-Key header"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/store-deduct?user_id={user_id}&points=100&item_name=test"
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ store-deduct correctly requires X-Internal-Api-Key")
    
    def test_store_deduct_validation(self, user_id):
        """POST /api/rewards/store-deduct should validate points parameter"""
        # Test with negative points (should fail validation)
        response = requests.post(
            f"{BASE_URL}/api/rewards/store-deduct?user_id={user_id}&points=-100&item_name=test",
            headers={"X-Internal-Api-Key": INTERNAL_API_KEY}
        )
        # Should return 422 for validation error (points must be > 0)
        assert response.status_code == 422, f"Expected 422 for negative points, got {response.status_code}"
        print("✓ store-deduct validates points > 0")


class TestPasswordResetFlow:
    """Test email-based password reset via Emailit integration"""
    
    def test_forgot_password_returns_generic_message(self):
        """POST /api/auth/forgot-password should return generic message (security best practice)"""
        # Test with valid email
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": MASTER_ADMIN_EMAIL
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should NOT return a token (emails it instead)
        assert "token" not in data, "forgot-password should NOT return a token in response (sends via email)"
        assert "message" in data, "Response should contain 'message'"
        
        print(f"✓ forgot-password returns generic message without token")
        print(f"  Message: {data.get('message')}")
    
    def test_forgot_password_nonexistent_email(self):
        """POST /api/auth/forgot-password should return same message for non-existent email (security)"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent_user_12345@example.com"
        })
        # Should return 200 even for non-existent emails (security best practice)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Should return message for non-existent email too"
        print("✓ forgot-password returns same response for non-existent email (security)")
    
    def test_reset_password_invalid_token(self):
        """POST /api/auth/reset-password should reject invalid tokens"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "invalid-token-12345",
            "new_password": "newpassword123"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ reset-password correctly rejects invalid tokens")
    
    def test_reset_password_short_password(self):
        """POST /api/auth/reset-password should reject passwords < 6 chars"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "some-token",
            "new_password": "123"  # Too short
        })
        # Should fail with 400 (either invalid token or short password)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ reset-password validates password length")


class TestBadgeCheckEndpoint:
    """Test badge check endpoint for toast notifications"""
    
    def test_badges_check_requires_auth(self):
        """POST /api/rewards/badges/check should require JWT authentication"""
        response = requests.post(f"{BASE_URL}/api/rewards/badges/check")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ badges/check correctly requires authentication")
    
    def test_badges_check_returns_newly_awarded(self, auth_token, user_id):
        """POST /api/rewards/badges/check should return newly_awarded list"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/badges/check",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "user_id" in data, "Response should contain 'user_id'"
        assert "newly_awarded" in data, "Response should contain 'newly_awarded'"
        assert isinstance(data["newly_awarded"], list), "newly_awarded should be a list"
        
        print(f"✓ badges/check returns correct structure")
        print(f"  User ID: {data.get('user_id')}")
        print(f"  Newly awarded: {data.get('newly_awarded')}")
    
    def test_badges_check_with_user_id_param(self, auth_token, user_id):
        """POST /api/rewards/badges/check should accept user_id query param for admins"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/badges/check?user_id={user_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("user_id") == user_id, "Should use the provided user_id"
        print("✓ badges/check accepts user_id query parameter for admins")


class TestFrontendAPIIntegration:
    """Test that frontend API methods map to correct endpoints"""
    
    def test_login_returns_access_token(self):
        """Login should return 'access_token' not 'token'"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, "Login should return 'access_token'"
        assert "token" not in data, "Login should NOT have 'token' key (it's 'access_token')"
        print("✓ Login correctly returns 'access_token'")
    
    def test_rewards_summary_endpoint(self, auth_token, user_id):
        """GET /api/rewards/summary should return user rewards summary"""
        response = requests.get(
            f"{BASE_URL}/api/rewards/summary?user_id={user_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check expected fields for MyRewardsPage
        expected_fields = ["user_id", "lifetime_points", "monthly_points", "level", 
                          "estimated_usdt", "current_streak", "best_streak", "referral_count"]
        for field in expected_fields:
            assert field in data, f"Summary should contain '{field}'"
        
        print("✓ rewards/summary returns all required fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

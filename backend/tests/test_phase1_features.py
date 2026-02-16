"""
Test Phase 1 Features: Trading Signal Blocking + Version Banner
- GET /api/version: returns build_version
- GET /api/trade/signal-block-status: returns blocked status for members
- POST /api/admin/members/{user_id}/unblock-signal: admin unblock
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"

@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for authenticated requests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin login failed - cannot run tests")

class TestVersionEndpoint:
    """Test GET /api/version endpoint (no auth required)"""
    
    def test_version_returns_build_version(self):
        """Version endpoint should return build_version without authentication"""
        response = requests.get(f"{BASE_URL}/api/version")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "build_version" in data, f"Response missing 'build_version': {data}"
        assert isinstance(data["build_version"], str), f"build_version should be string: {data}"
        assert len(data["build_version"]) > 0, f"build_version should not be empty: {data}"
        
        print(f"✓ Version endpoint working - build_version: {data['build_version'][:8]}...")


class TestSignalBlockStatus:
    """Test GET /api/trade/signal-block-status endpoint"""
    
    def test_signal_block_status_requires_auth(self):
        """Signal block status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/trade/signal-block-status")
        
        # Should return 403 (Forbidden) or 401 (Unauthorized) without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Signal block status requires authentication")
    
    def test_admin_not_blocked(self, admin_token):
        """Admin users should never be blocked from viewing signals"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/signal-block-status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "blocked" in data, f"Response missing 'blocked': {data}"
        assert data["blocked"] == False, f"Admin should NOT be blocked: {data}"
        
        # Admin response should indicate reason is None (not blocked)
        assert data.get("missing_days", 0) == 0, f"Admin should have 0 missing days: {data}"
        
        print(f"✓ Admin signal block status: blocked={data['blocked']}, reason={data.get('reason')}")


class TestAdminUnblockSignal:
    """Test POST /api/admin/members/{user_id}/unblock-signal endpoint"""
    
    def test_unblock_signal_requires_auth(self):
        """Unblock signal endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/members/fake-user-id/unblock-signal")
        
        # Should return 403 (Forbidden) or 401 (Unauthorized) without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Admin unblock signal requires authentication")
    
    def test_unblock_signal_requires_admin(self, admin_token):
        """Unblock signal endpoint requires admin role - test with admin user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a member user to test with
        members_response = requests.get(f"{BASE_URL}/api/admin/members?role=member&limit=1", headers=headers)
        
        if members_response.status_code != 200:
            pytest.skip("Could not fetch members list")
        
        members_data = members_response.json()
        if not members_data.get("members"):
            pytest.skip("No members found to test unblock with")
        
        member_id = members_data["members"][0]["id"]
        
        # Admin should be able to unblock
        response = requests.post(
            f"{BASE_URL}/api/admin/members/{member_id}/unblock-signal",
            headers=headers,
            params={"days": 7}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, f"Response missing 'message': {data}"
        assert "unblocked_until" in data, f"Response missing 'unblocked_until': {data}"
        
        print(f"✓ Admin unblock signal working: {data['message']}")
    
    def test_unblock_signal_user_not_found(self, admin_token):
        """Unblock signal should return 404 for non-existent user"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/members/non-existent-user-id/unblock-signal",
            headers=headers,
            params={"days": 7}
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent user, got {response.status_code}"
        print("✓ Admin unblock signal returns 404 for non-existent user")


class TestAuthEndpoints:
    """Test authentication endpoints used by the app"""
    
    def test_login_returns_access_token(self):
        """Login should return access_token (not just 'token')"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "access_token" in data, f"Response missing 'access_token': {data}"
        assert "user" in data, f"Response missing 'user': {data}"
        assert data["user"]["role"] in ["master_admin", "super_admin", "admin", "basic_admin"], f"User should be admin: {data['user']}"
        
        print(f"✓ Login working - user role: {data['user']['role']}")
    
    def test_me_endpoint(self, admin_token):
        """GET /api/auth/me should return current user info"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, f"Response missing 'id': {data}"
        assert "email" in data, f"Response missing 'email': {data}"
        assert "role" in data, f"Response missing 'role': {data}"
        
        print(f"✓ GET /api/auth/me working - email: {data['email']}, role: {data['role']}")


class TestFrontendAPIIntegration:
    """Test that the API functions used by frontend are working"""
    
    def test_api_version_no_cors_issues(self):
        """Version API should be accessible without CORS issues"""
        response = requests.get(f"{BASE_URL}/api/version")
        
        assert response.status_code == 200
        
        # Check Content-Type header
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, f"Expected JSON response, got: {content_type}"
        
        print("✓ Version API accessible and returns JSON")
    
    def test_trade_signal_block_status_structure(self, admin_token):
        """Signal block status should return expected structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/signal-block-status", headers=headers)
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields for frontend
        assert "blocked" in data, "Missing 'blocked' field"
        assert "missing_days" in data, "Missing 'missing_days' field"
        
        # Type checks
        assert isinstance(data["blocked"], bool), f"'blocked' should be boolean: {type(data['blocked'])}"
        assert isinstance(data["missing_days"], int), f"'missing_days' should be int: {type(data['missing_days'])}"
        
        print(f"✓ Signal block status structure correct: blocked={data['blocked']}, missing_days={data['missing_days']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

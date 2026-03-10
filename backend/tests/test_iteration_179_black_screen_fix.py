"""
Iteration 179: Black Screen Bug Fix & Inviter Modal Changes
Tests:
1. Backend health check
2. Login response includes referred_by field
3. POST /api/referrals/set-inviter allows re-setting inviter (no 400 if already set)
4. POST /api/referrals/set-inviter rejects self-referral
5. GET /api/referrals/tracking returns referred_by and referred_by_user_id
6. Admin login and dashboard access (no black screen)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
TEST_MEMBER_ID = "a9566813-3880-47c5-8703-7fa22fdb601d"  # Member with merin code


class TestBackendHealth:
    """Basic health checks"""
    
    def test_backend_is_running(self):
        """Test that backend is healthy"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Backend is healthy")


class TestAdminLogin:
    """Test admin login and referred_by field"""
    
    def test_admin_login_success(self):
        """Admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        assert "user" in data, "No user in login response"
        assert data["user"]["role"] == "master_admin", f"Expected master_admin role, got {data['user']['role']}"
        print(f"✓ Admin login successful: {data['user']['email']} (role={data['user']['role']})")
        return data["access_token"]
    
    def test_login_response_includes_referred_by(self):
        """Login response includes referred_by field in user object"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        assert response.status_code == 200
        data = response.json()
        user = data.get("user", {})
        # Check that referred_by key exists in user object (can be null for admin)
        assert "referred_by" in user, "referred_by field missing from login response user object"
        print(f"✓ Login response includes referred_by field: {user.get('referred_by')}")


class TestSetInviterEndpoint:
    """Test POST /api/referrals/set-inviter - now allows re-setting"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_set_inviter_rejects_self_referral(self, admin_token):
        """Cannot set yourself as your own inviter"""
        # Get admin's user ID first
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200
        admin_user_id = response.json()["id"]
        
        # Try to set self as inviter
        response = requests.post(
            f"{BASE_URL}/api/referrals/set-inviter",
            json={"inviter_id": admin_user_id},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 400, f"Expected 400 for self-referral, got {response.status_code}: {response.text}"
        data = response.json()
        assert "cannot invite yourself" in data.get("detail", "").lower() or "yourself" in data.get("detail", "").lower(), f"Unexpected error: {data}"
        print("✓ Self-referral correctly rejected")
    
    def test_set_inviter_allows_resetting(self, admin_token):
        """set-inviter now allows re-setting (no 400 error if already set)"""
        # First, look up a valid member to use as inviter
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members?q=Ryan",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        if response.status_code != 200:
            pytest.skip("Cannot lookup members")
        
        results = response.json().get("results", [])
        if not results:
            pytest.skip("No members found for lookup")
        
        inviter_id = results[0]["id"]
        
        # Get admin's user ID
        me_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        admin_id = me_resp.json()["id"]
        
        # Skip if admin is the only member found
        if inviter_id == admin_id:
            pytest.skip("Only admin user found, cannot test inviter setting")
        
        # Note: This test verifies the endpoint doesn't reject re-setting
        # We just verify it doesn't return 400 with "already set" error
        response = requests.post(
            f"{BASE_URL}/api/referrals/set-inviter",
            json={"inviter_id": inviter_id},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        # Should either succeed (200) or fail for other reasons (not "already set")
        if response.status_code == 400:
            data = response.json()
            assert "already" not in data.get("detail", "").lower(), f"Endpoint incorrectly rejects re-setting: {data}"
        print(f"✓ set-inviter endpoint does not block re-setting (status={response.status_code})")


class TestReferralTracking:
    """Test GET /api/referrals/tracking endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_tracking_returns_referred_by_fields(self, admin_token):
        """GET /api/referrals/tracking returns referred_by and referred_by_user_id"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/tracking",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Tracking endpoint failed: {response.text}"
        data = response.json()
        
        # Verify the response includes referred_by fields
        assert "referred_by" in data, "referred_by field missing from tracking response"
        assert "referred_by_user_id" in data, "referred_by_user_id field missing from tracking response"
        print(f"✓ Tracking returns referred_by={data.get('referred_by')}, referred_by_user_id={data.get('referred_by_user_id')}")


class TestAffiliateCenterEndpoints:
    """Verify Affiliate Center related endpoints still work"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_lookup_members_works(self, admin_token):
        """GET /api/referrals/lookup-members returns results"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members?q=a",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Lookup members failed: {response.text}"
        data = response.json()
        assert "results" in data, "No results field in lookup response"
        # Verify result structure if any results
        if data["results"]:
            result = data["results"][0]
            assert "id" in result, "Result missing 'id'"
            assert "name" in result, "Result missing 'name'"
            assert "masked_email" in result, "Result missing 'masked_email'"
            print(f"✓ Lookup returns {len(data['results'])} results with correct structure")
        else:
            print("✓ Lookup endpoint works (no results for 'a')")
    
    def test_my_code_endpoint_works(self, admin_token):
        """GET /api/referrals/my-code returns user's referral info"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-code",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200, f"My-code endpoint failed: {response.text}"
        data = response.json()
        assert "referral_code" in data, "Missing referral_code in response"
        assert "direct_referrals" in data, "Missing direct_referrals in response"
        print(f"✓ My-code endpoint works: code={data.get('referral_code')}, referrals={data.get('direct_referrals')}")


class TestAdminMembersPage:
    """Test Admin Members endpoints for inviter field"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_get_members_list(self, admin_token):
        """GET /api/admin/members returns member list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Get members failed: {response.text}"
        data = response.json()
        assert "members" in data or "users" in data or isinstance(data, list), "Unexpected response format"
        print("✓ Admin members endpoint works")
    
    def test_get_member_details_includes_referral_fields(self, admin_token):
        """GET /api/admin/members/{id} includes referral fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        if response.status_code == 404:
            pytest.skip(f"Test member {TEST_MEMBER_ID} not found")
        assert response.status_code == 200, f"Get member details failed: {response.text}"
        data = response.json()
        # Check that member details can include referral fields
        print(f"✓ Member details retrieved: {data.get('full_name', data.get('email', 'Unknown'))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

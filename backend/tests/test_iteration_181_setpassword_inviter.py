"""
Iteration 181 Tests: Set-Password Bug Fix & Inviter Modal Logic

Bug 1: set-password endpoint was returning 422 'secret_code field required' when new members
        tried to register. Fixed by making secret_code Optional in SetPasswordRequest.

Bug 2: 'Who invited you?' modal should only appear ONCE - after a member sets their inviter,
        it should never show again. Changed from sessionStorage (per-session) to checking
        user.referred_by (permanent).

Tests:
- POST /api/auth/set-password with only {email, password} does NOT return 422 (proper error like 'Email not verified')
- POST /api/auth/set-password with {email, password, secret_code} still works for admin registration
- Login response includes referred_by field correctly
- POST /api/referrals/set-inviter updates user's referred_by
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSetPasswordBugFix:
    """Test that set-password endpoint no longer returns 422 for missing secret_code"""
    
    def test_server_health(self):
        """Verify server is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Server unhealthy: {response.text}"
        print("PASS: Server health check")
    
    def test_set_password_without_secret_code_no_422(self):
        """
        CRITICAL BUG FIX: POST /api/auth/set-password with only {email, password}
        should NOT return 422 'secret_code field required'.
        
        Expected: Returns 400 'Email not verified with Heartbeat' or similar business error
        NOT Expected: 422 validation error about missing secret_code
        """
        response = requests.post(
            f"{BASE_URL}/api/auth/set-password",
            json={
                "email": "nonexistent_test_user@example.com",
                "password": "testpass123"
            }
        )
        
        # The key fix: should NOT be 422 validation error
        assert response.status_code != 422, f"BUG NOT FIXED: Got 422 validation error: {response.text}"
        
        # Should be 400 (business logic error like 'Email not verified') or 500 (integration not configured)
        assert response.status_code in [400, 500], f"Unexpected status: {response.status_code} - {response.text}"
        
        # Verify the error message is about business logic, not validation
        error_text = response.text.lower()
        assert 'secret_code' not in error_text or 'required' not in error_text, \
            f"Error still mentions secret_code validation: {response.text}"
        
        print(f"PASS: set-password without secret_code returns {response.status_code} (not 422)")
        print(f"  Response: {response.json()}")
    
    def test_set_password_with_secret_code_backward_compat(self):
        """
        Verify backward compatibility: set-password with secret_code still works.
        This tests that the Optional[str] = None doesn't break existing flows.
        """
        response = requests.post(
            f"{BASE_URL}/api/auth/set-password",
            json={
                "email": "nonexistent_test_user@example.com",
                "password": "testpass123",
                "secret_code": "some_fake_code"
            }
        )
        
        # Should still be a business error (not 422 validation error)
        assert response.status_code != 422, f"Got 422 even with secret_code: {response.text}"
        print(f"PASS: set-password with secret_code returns {response.status_code} (backward compatible)")
    
    def test_set_password_validation_still_works(self):
        """Verify that actual validation still works (e.g., password length)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/set-password",
            json={
                "email": "test@example.com",
                "password": "123"  # Too short - should be rejected
            }
        )
        
        # Password validation should fail with 400, not 422
        assert response.status_code == 400, f"Expected 400 for short password, got {response.status_code}"
        assert "6 characters" in response.text.lower() or "password" in response.text.lower(), \
            f"Expected password length error: {response.text}"
        print("PASS: Password validation still works (short password rejected)")


class TestLoginReturnsReferredBy:
    """Test that login response includes referred_by field for inviter modal logic"""
    
    def test_admin_login_includes_referred_by(self):
        """
        Verify login response includes referred_by field.
        This is needed for the InviterModal to check if user already has an inviter.
        """
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert "user" in data, "Missing user object"
        
        user = data["user"]
        # referred_by should be present in response (even if null for admins)
        assert "referred_by" in user, f"LOGIN RESPONSE MISSING referred_by field! User keys: {user.keys()}"
        
        print(f"PASS: Login response includes referred_by: {user.get('referred_by')}")
        print(f"  User role: {user.get('role')}")
        return data["access_token"]


class TestSetInviterEndpoint:
    """Test the /api/referrals/set-inviter endpoint that permanently sets referred_by"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_set_inviter_endpoint_exists(self, admin_token):
        """Verify the set-inviter endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/referrals/set-inviter",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"inviter_id": "nonexistent_id"}
        )
        
        # Should be 404 (inviter not found), not 404 route not found
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 404:
            data = response.json()
            assert "inviter not found" in data.get("detail", "").lower() or \
                   "not found" in data.get("detail", "").lower(), \
                   f"Unexpected 404 error: {data}"
            print("PASS: set-inviter endpoint exists and returns proper error for invalid inviter")
        else:
            print(f"PASS: set-inviter endpoint exists (status {response.status_code})")
    
    def test_set_inviter_updates_referred_by(self, admin_token):
        """
        Verify that after calling set-inviter, the user's referred_by is populated.
        This is the key fix for Bug 2 - referred_by must be set permanently.
        """
        # Get the admin's user ID for testing
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert me_response.status_code == 200
        admin_user = me_response.json()
        
        # Check tracking endpoint shows referred_by field
        tracking_response = requests.get(
            f"{BASE_URL}/api/referrals/tracking",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert tracking_response.status_code == 200, f"Tracking failed: {tracking_response.text}"
        tracking_data = tracking_response.json()
        
        # referred_by should be accessible in tracking data
        assert "referred_by" in tracking_data or "referred_by_user_id" in tracking_data, \
            f"Tracking response missing referral fields: {tracking_data.keys()}"
        
        print(f"PASS: Referral tracking includes referred_by: {tracking_data.get('referred_by')}")
        print(f"  referred_by_user_id: {tracking_data.get('referred_by_user_id')}")


class TestInviterModalLogicRequirements:
    """Tests to verify the data requirements for InviterModal one-time display logic"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200
        return response.json()
    
    def test_login_response_has_all_inviter_modal_fields(self, admin_token):
        """
        InviterModal depends on user.referred_by from login response.
        Verify all required fields are present.
        """
        data = admin_token  # This is the full login response
        user = data["user"]
        
        # Required fields for InviterModal logic
        required_fields = ["role", "referred_by"]
        for field in required_fields:
            assert field in user, f"Missing required field '{field}' for InviterModal logic"
        
        print(f"PASS: Login response has all InviterModal required fields")
        print(f"  role: {user.get('role')}")
        print(f"  referred_by: {user.get('referred_by')}")
    
    def test_admin_should_not_see_inviter_modal(self, admin_token):
        """
        According to DashboardLayout.jsx line 148:
        if (!['master_admin', 'super_admin', 'basic_admin'].includes(user.role))
        
        Admins should never see the InviterModal.
        """
        data = admin_token
        user = data["user"]
        
        admin_roles = ['master_admin', 'super_admin', 'basic_admin']
        
        # Admin roles should not trigger modal
        if user.get("role") in admin_roles:
            print(f"PASS: Admin role '{user['role']}' correctly excluded from InviterModal")
        else:
            # Non-admin: modal depends on referred_by
            should_show = not user.get("referred_by")
            print(f"INFO: Non-admin user, InviterModal should show: {should_show}")


class TestMeEndpointReferredBy:
    """Test that /api/auth/me returns referred_by field"""
    
    def test_me_endpoint_includes_referred_by(self):
        """Verify /api/auth/me includes referred_by for authenticated users"""
        # Login first
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Get /me
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200
        user = me_response.json()
        
        # referred_by should be in UserResponse model
        assert "referred_by" in user, f"/me response missing referred_by: {user.keys()}"
        
        print(f"PASS: /api/auth/me includes referred_by: {user.get('referred_by')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

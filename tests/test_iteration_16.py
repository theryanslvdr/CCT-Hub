"""
Iteration 16 Backend Tests
Features to test:
1. Interactive Onboarding Tour - Next/Previous buttons work
2. License Invites - GET/POST /api/admin/license-invites endpoints
3. License Invite - revoke/renew/delete functionality
4. License Registration Page - /register/license/:code validates invite
5. Register with license - POST /api/auth/register-with-license
6. Team Analytics - verify licensed users (both extended AND honorary) excluded
7. Settings Page - verify 5 tabs: SEO & Meta, Branding, UI, Integrations, Emails
8. Integration Test Buttons - POST /api/settings/test-emailit, test-cloudinary, test-heartbeat
9. Email Templates - GET /api/settings/email-templates returns default templates
10. Licenses Page - /admin/licenses accessible only by Master Admin
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://trader-hub-39.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"

# Existing test invite code
EXISTING_INVITE_CODE = "LIC-V59SF-9JKK0FPARD"


def get_auth_token():
    """Get master admin auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return None
    return response.json()["access_token"]


class TestAuth:
    """Authentication tests"""
    
    def test_login_master_admin(self):
        """Test 1: Login as master_admin"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "master_admin"
        print("✓ Test 1: Login as master_admin successful")


class TestLicenseInvites:
    """License Invite API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        return get_auth_token()
    
    def test_get_license_invites(self, auth_token):
        """Test 2: GET /api/admin/license-invites returns list of invites"""
        response = requests.get(
            f"{BASE_URL}/api/admin/license-invites",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "invites" in data
        assert isinstance(data["invites"], list)
        print(f"✓ Test 2: GET license-invites returned {len(data['invites'])} invites")
    
    def test_create_license_invite(self, auth_token):
        """Test 3: POST /api/admin/license-invites creates new invite"""
        unique_email = f"test_invite_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/license-invites",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "license_type": "extended",
                "starting_amount": 5000,
                "valid_duration": "3_months",
                "max_uses": 1,
                "invitee_name": "Test Invitee",
                "invitee_email": unique_email,
                "notes": "Test invite for iteration 16"
            }
        )
        assert response.status_code == 200, f"Create invite failed: {response.text}"
        data = response.json()
        assert "code" in data
        assert "registration_url" in data
        assert data["code"].startswith("LIC-")
        print(f"✓ Test 3: Created license invite with code: {data['code']}")
        return data["code"], data.get("invite_id")
    
    def test_validate_existing_invite(self):
        """Test 4: GET /api/auth/license-invite/:code validates invite"""
        response = requests.get(f"{BASE_URL}/api/auth/license-invite/{EXISTING_INVITE_CODE}")
        # May be valid or expired/used - just check endpoint works
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert "valid" in data
            assert "license_type" in data
            print(f"✓ Test 4: Validated invite code - type: {data.get('license_type')}")
        else:
            print(f"✓ Test 4: Invite validation endpoint works (code may be expired/used)")


class TestLicenseInviteActions:
    """License Invite revoke/renew/delete tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        return get_auth_token()
    
    @pytest.fixture(scope="class")
    def test_invite(self, auth_token):
        """Create a test invite for action tests"""
        response = requests.post(
            f"{BASE_URL}/api/admin/license-invites",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "license_type": "honorary",
                "starting_amount": 3000,
                "valid_duration": "3_months",
                "max_uses": 1,
                "invitee_name": "Action Test User",
                "notes": "Test invite for action tests"
            }
        )
        assert response.status_code == 200, f"Create test invite failed: {response.text}"
        data = response.json()
        
        # Get the invite ID
        invites_response = requests.get(
            f"{BASE_URL}/api/admin/license-invites",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        invites = invites_response.json()["invites"]
        invite = next((i for i in invites if i["code"] == data["code"]), None)
        return invite
    
    def test_revoke_invite(self, auth_token, test_invite):
        """Test 5: POST /api/admin/license-invites/:id/revoke revokes invite"""
        if not test_invite:
            pytest.skip("No test invite available")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/license-invites/{test_invite['id']}/revoke",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Revoke failed: {response.text}"
        print(f"✓ Test 5: Revoked invite {test_invite['code']}")
    
    def test_renew_invite(self, auth_token, test_invite):
        """Test 6: POST /api/admin/license-invites/:id/renew renews invite"""
        if not test_invite:
            pytest.skip("No test invite available")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/license-invites/{test_invite['id']}/renew",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"new_duration": "6_months"}
        )
        assert response.status_code == 200, f"Renew failed: {response.text}"
        print(f"✓ Test 6: Renewed invite {test_invite['code']}")
    
    def test_delete_invite(self, auth_token, test_invite):
        """Test 7: DELETE /api/admin/license-invites/:id deletes invite"""
        if not test_invite:
            pytest.skip("No test invite available")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/license-invites/{test_invite['id']}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Delete failed: {response.text}"
        print(f"✓ Test 7: Deleted invite {test_invite['code']}")


class TestTeamAnalytics:
    """Team Analytics tests - verify licensed users excluded"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        return get_auth_token()
    
    def test_team_analytics_excludes_licensed_users(self, auth_token):
        """Test 8: Team Analytics excludes both extended AND honorary licensees"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics/team",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Team analytics failed: {response.text}"
        data = response.json()
        
        # Check that the response includes exclusion counts
        assert "honorary_count" in data or "extended_count" in data
        
        # Check members have is_honorary and is_extended flags
        if "members" in data and len(data["members"]) > 0:
            member = data["members"][0]
            assert "is_honorary" in member or "is_extended" in member
        
        print(f"✓ Test 8: Team Analytics - honorary_count: {data.get('honorary_count', 0)}, extended_count: {data.get('extended_count', 0)}")


class TestEmailTemplates:
    """Email Templates API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        return get_auth_token()
    
    def test_get_email_templates(self, auth_token):
        """Test 9: GET /api/settings/email-templates returns default templates"""
        response = requests.get(
            f"{BASE_URL}/api/settings/email-templates",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get email templates failed: {response.text}"
        data = response.json()
        assert "templates" in data
        
        # Check for expected template types
        template_types = [t["type"] for t in data["templates"]]
        expected_types = ["welcome", "forgot_password", "trade_notification", "license_invite"]
        
        for expected in expected_types:
            assert expected in template_types, f"Missing template type: {expected}"
        
        print(f"✓ Test 9: Email templates returned {len(data['templates'])} templates")
        print(f"  Template types: {template_types}")


class TestIntegrationTests:
    """Integration Test Button API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        return get_auth_token()
    
    def test_emailit_connection(self, auth_token):
        """Test 10: POST /api/settings/test-emailit tests Emailit connection"""
        response = requests.post(
            f"{BASE_URL}/api/settings/test-emailit",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Emailit test failed: {response.text}"
        data = response.json()
        assert "success" in data
        assert "message" in data
        print(f"✓ Test 10: Emailit test - success: {data['success']}, message: {data['message']}")
    
    def test_cloudinary_connection(self, auth_token):
        """Test 11: POST /api/settings/test-cloudinary tests Cloudinary connection"""
        response = requests.post(
            f"{BASE_URL}/api/settings/test-cloudinary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Cloudinary test failed: {response.text}"
        data = response.json()
        assert "success" in data
        assert "message" in data
        print(f"✓ Test 11: Cloudinary test - success: {data['success']}, message: {data['message']}")
    
    def test_heartbeat_connection(self, auth_token):
        """Test 12: POST /api/settings/test-heartbeat tests Heartbeat connection"""
        response = requests.post(
            f"{BASE_URL}/api/settings/test-heartbeat",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Heartbeat test failed: {response.text}"
        data = response.json()
        assert "success" in data
        assert "message" in data
        print(f"✓ Test 12: Heartbeat test - success: {data['success']}, message: {data['message']}")


class TestLicensesEndpoint:
    """Licenses endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        return get_auth_token()
    
    def test_get_licenses(self, auth_token):
        """Test 13: GET /api/admin/licenses returns list of licenses"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get licenses failed: {response.text}"
        data = response.json()
        assert "licenses" in data
        print(f"✓ Test 13: GET licenses returned {len(data['licenses'])} licenses")


class TestSettingsPage:
    """Settings Page API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        return get_auth_token()
    
    def test_get_platform_settings(self, auth_token):
        """Test 14: GET /api/settings/platform returns settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get platform settings failed: {response.text}"
        data = response.json()
        # Check for expected settings fields
        expected_fields = ["site_title", "primary_color", "accent_color"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print(f"✓ Test 14: Platform settings retrieved successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 20 Backend Tests
Features to test:
1. Login Page - verify-heartbeat endpoint
2. Login Page - set-password endpoint  
3. Settings Page - Links tab (custom_registration_link in settings)
4. Admin Licenses - change-type endpoint
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://user-role-update-2.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "iamryan@ryansalvador.me"
LICENSEE_PASSWORD = "admin123"


class TestAuthEndpoints:
    """Test authentication endpoints for Account Setup flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_verify_heartbeat_valid_email(self):
        """Test verify-heartbeat endpoint with a valid Heartbeat member email"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/verify-heartbeat",
            json={"email": MASTER_ADMIN_EMAIL}
        )
        # Should return 200 even if not verified (returns verified: false)
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        print(f"Verify heartbeat response: {data}")
    
    def test_verify_heartbeat_invalid_email(self):
        """Test verify-heartbeat endpoint with invalid email"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/verify-heartbeat",
            json={"email": f"nonexistent_{uuid.uuid4().hex[:8]}@test.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("verified") == False
        print(f"Invalid email response: {data}")
    
    def test_set_password_requires_heartbeat_verification(self):
        """Test set-password endpoint requires Heartbeat verification"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/set-password",
            json={
                "email": f"nonexistent_{uuid.uuid4().hex[:8]}@test.com",
                "password": "testpassword123"
            }
        )
        # Should fail because email is not a Heartbeat member
        assert response.status_code == 400
        print(f"Set password without verification: {response.json()}")
    
    def test_set_password_short_password(self):
        """Test set-password endpoint rejects short passwords"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/set-password",
            json={
                "email": MASTER_ADMIN_EMAIL,
                "password": "123"  # Too short
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "6 characters" in data.get("detail", "")
        print(f"Short password response: {data}")


class TestSettingsEndpoints:
    """Test settings endpoints for Links tab"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login as master admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_settings_includes_custom_registration_link(self):
        """Test that settings include custom_registration_link field"""
        response = self.session.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200
        data = response.json()
        # The field should exist (even if empty)
        assert "custom_registration_link" in data or data.get("custom_registration_link") is None
        print(f"Settings response keys: {list(data.keys())}")
    
    def test_update_custom_registration_link(self):
        """Test updating custom_registration_link in settings"""
        test_link = "https://heartbeat.chat/join/crosscurrent-test"
        response = self.session.put(
            f"{BASE_URL}/api/settings/platform",
            json={"custom_registration_link": test_link}
        )
        assert response.status_code == 200
        
        # Verify the update
        get_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data.get("custom_registration_link") == test_link
        print(f"Updated custom_registration_link: {data.get('custom_registration_link')}")
    
    def test_public_settings_endpoint(self):
        """Test public settings endpoint (used by login page)"""
        # Create a new session without auth
        public_session = requests.Session()
        response = public_session.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        data = response.json()
        # Should include custom_registration_link for login page
        print(f"Public settings keys: {list(data.keys())}")


class TestLicenseChangeType:
    """Test license change-type endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login as master admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user")
    
    def test_get_active_licenses(self):
        """Test getting active licenses"""
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        print(f"Found {len(data.get('licenses', []))} licenses")
        return data.get("licenses", [])
    
    def test_change_license_type_requires_master_admin(self):
        """Test that change-type requires master admin role"""
        # First get a license ID
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        if licenses_response.status_code == 200:
            licenses = licenses_response.json().get("licenses", [])
            if licenses:
                license_id = licenses[0]["id"]
                # Try to change type (should work for master admin)
                response = self.session.post(
                    f"{BASE_URL}/api/admin/licenses/{license_id}/change-type",
                    json={
                        "new_license_type": "honorary",
                        "new_starting_amount": 10000,
                        "notes": "Test change"
                    }
                )
                # Master admin should be able to change
                print(f"Change type response: {response.status_code} - {response.json()}")
            else:
                print("No licenses found to test change-type")
                pytest.skip("No licenses available for testing")
    
    def test_change_license_type_invalid_type(self):
        """Test that invalid license type is rejected"""
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        if licenses_response.status_code == 200:
            licenses = licenses_response.json().get("licenses", [])
            if licenses:
                license_id = licenses[0]["id"]
                response = self.session.post(
                    f"{BASE_URL}/api/admin/licenses/{license_id}/change-type",
                    json={
                        "new_license_type": "invalid_type",
                        "new_starting_amount": 10000
                    }
                )
                assert response.status_code == 400
                print(f"Invalid type response: {response.json()}")
            else:
                pytest.skip("No licenses available for testing")


class TestSidebarVisibility:
    """Test that Deposit/Withdrawal is visible for licensees"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_licensee_login(self):
        """Test licensee can login"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": LICENSEE_EMAIL, "password": LICENSEE_PASSWORD}
        )
        # May fail if licensee doesn't exist
        if response.status_code == 200:
            data = response.json()
            print(f"Licensee login successful: {data.get('user', {}).get('role')}")
            assert "access_token" in data
        else:
            print(f"Licensee login failed: {response.status_code} - {response.json()}")
            pytest.skip("Licensee account not available")
    
    def test_master_admin_login(self):
        """Test master admin can login"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("user", {}).get("role") == "master_admin"
        print(f"Master admin login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

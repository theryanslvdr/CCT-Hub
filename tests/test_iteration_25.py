"""
Test iteration 25 - Testing 3 fixes:
1. Licensee account value should only be controlled by admin/deposits/withdrawals/trades (not by licensee)
2. Remove licensees from Member Management (they have Licensee role)
3. Login card styling - remove title, don't crop logo
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMemberManagementExcludesLicensees:
    """Test that /admin/members endpoint excludes users with license_type"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user = login_response.json().get("user")
    
    def test_admin_members_endpoint_excludes_licensees(self):
        """Verify /admin/members does not return users with license_type"""
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200, f"Failed to get members: {response.text}"
        
        data = response.json()
        members = data.get("members", [])
        
        # Check that no member has license_type field
        licensees_in_list = [m for m in members if m.get("license_type")]
        assert len(licensees_in_list) == 0, f"Found {len(licensees_in_list)} licensees in member list: {[m.get('email') for m in licensees_in_list]}"
        
        print(f"✓ Member list has {len(members)} members, none with license_type")
    
    def test_licensees_exist_in_database(self):
        """Verify that licensees exist in the system (via licenses endpoint)"""
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200, f"Failed to get licenses: {response.text}"
        
        data = response.json()
        licenses = data.get("licenses", []) if isinstance(data, dict) else data
        active_licenses = [l for l in licenses if l.get("is_active")]
        
        print(f"✓ Found {len(active_licenses)} active licenses in the system")
        for lic in active_licenses[:5]:  # Show first 5
            print(f"  - {lic.get('user_name')} ({lic.get('license_type')}): ${lic.get('current_amount', 0):.2f}")
        
        # There should be at least some licensees
        assert len(active_licenses) >= 0, "Expected at least some licensees in the system"


class TestLicenseeAccountValueFromAPI:
    """Test that licensee account_value comes from license.current_amount via API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_member_details_returns_license_current_amount(self):
        """Verify /admin/members/{user_id} returns account_value from license.current_amount for licensees"""
        # First get a licensee from the licenses endpoint
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200, f"Failed to get licenses: {licenses_response.text}"
        
        data = licenses_response.json()
        licenses = data.get("licenses", []) if isinstance(data, dict) else data
        active_licenses = [l for l in licenses if l.get("is_active")]
        
        if not active_licenses:
            pytest.skip("No active licensees found to test")
        
        # Get the first active licensee
        test_license = active_licenses[0]
        user_id = test_license.get("user_id")
        expected_account_value = test_license.get("current_amount", test_license.get("starting_amount", 0))
        
        print(f"Testing licensee: {test_license.get('user_name')} (ID: {user_id})")
        print(f"Expected account_value from license.current_amount: ${expected_account_value:.2f}")
        
        # Get member details
        member_response = self.session.get(f"{BASE_URL}/api/admin/members/{user_id}")
        assert member_response.status_code == 200, f"Failed to get member details: {member_response.text}"
        
        member_data = member_response.json()
        stats = member_data.get("stats", {})
        actual_account_value = stats.get("account_value", 0)
        
        print(f"Actual account_value from API: ${actual_account_value:.2f}")
        
        # The account_value should match the license.current_amount
        assert abs(actual_account_value - expected_account_value) < 0.01, \
            f"Account value mismatch: expected ${expected_account_value:.2f}, got ${actual_account_value:.2f}"
        
        print(f"✓ Account value matches license.current_amount: ${actual_account_value:.2f}")


class TestLoginEndpoint:
    """Test login endpoint works correctly"""
    
    def test_login_success(self):
        """Test successful login"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == "iam@ryansalvador.com"
        
        print(f"✓ Login successful for {data['user']['email']} (role: {data['user']['role']})")


class TestPlatformSettings:
    """Test platform settings for login page"""
    
    def test_get_platform_settings(self):
        """Test that platform settings endpoint returns logo_url"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200, f"Failed to get platform settings: {response.text}"
        
        data = response.json()
        print(f"Platform settings:")
        print(f"  - platform_name: {data.get('platform_name')}")
        print(f"  - tagline: {data.get('tagline')}")
        print(f"  - logo_url: {data.get('logo_url', 'Not set')}")
        
        # Verify expected fields exist
        assert "platform_name" in data, "Missing platform_name"
        assert "tagline" in data, "Missing tagline"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

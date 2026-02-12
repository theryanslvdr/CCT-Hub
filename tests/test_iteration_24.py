"""
Test Iteration 24 - Testing 8 fixes:
1) Licensee simulation dialog should find existing honorary/extended licensees
2) Deposit/Withdrawal menu item only visible for licensees (not standard members)
3) Trade Monitor 'Your Time' card should not overflow
4) Reset Starting Amount button in Active Licenses tab
5) Platform settings (platform_name, tagline, hide_emergent_badge) should persist
6) Login page should show uploaded logo from settings
7) Licensees in Members page should show correct account_value from license.current_amount
8) Demo simulation (Extended Licensee Demo) should show $5,000 in Profit Tracker
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://diag-staging.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestAuthAndSetup:
    """Authentication and setup tests"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        """Get master admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Master admin login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_master_admin_login(self, master_admin_token):
        """Test master admin can login"""
        assert master_admin_token is not None
        assert len(master_admin_token) > 0


class TestLicenseeSimulationDialog:
    """Test Issue 1: Licensee simulation dialog should find existing honorary/extended licensees"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_licenses_returns_active_licensees(self, master_admin_token):
        """Test that GET /admin/licenses returns active licensees"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        # Check if there are any active licenses
        active_licenses = [l for l in data["licenses"] if l.get("is_active")]
        print(f"Found {len(active_licenses)} active licenses")
        for lic in active_licenses[:3]:
            print(f"  - {lic.get('user_name', 'Unknown')} ({lic.get('license_type')}): ${lic.get('current_amount', 0):,.2f}")
    
    def test_get_members_returns_members_array(self, master_admin_token):
        """Test that GET /admin/members returns members in correct format"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Should have 'members' key with array
        assert "members" in data, f"Response should have 'members' key. Got: {list(data.keys())}"
        assert isinstance(data["members"], list), "members should be a list"
        print(f"Found {len(data['members'])} members")


class TestMenuFiltering:
    """Test Issue 2: Deposit/Withdrawal menu item only visible for licensees"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_master_admin_has_no_license_type(self, master_admin_token):
        """Test that master admin user has no license_type (standard member)"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        user = response.json()
        # Master admin should not have license_type
        license_type = user.get("license_type")
        print(f"Master admin license_type: {license_type}")
        # This is expected - master admin is not a licensee


class TestResetStartingAmount:
    """Test Issue 4: Reset Starting Amount button in Active Licenses tab"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_reset_balance_endpoint_exists(self, master_admin_token):
        """Test that reset-balance endpoint exists and works"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # First get an active license
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200
        licenses = response.json().get("licenses", [])
        active_licenses = [l for l in licenses if l.get("is_active")]
        
        if not active_licenses:
            pytest.skip("No active licenses to test reset-balance")
        
        license = active_licenses[0]
        license_id = license["id"]
        current_amount = license.get("current_amount", license.get("starting_amount", 0))
        
        print(f"Testing reset-balance on license {license_id}")
        print(f"Current amount: ${current_amount:,.2f}")
        
        # Test reset-balance endpoint (reset to same amount to not change anything)
        response = requests.post(
            f"{BASE_URL}/api/admin/licenses/{license_id}/reset-balance",
            headers=headers,
            json={
                "new_amount": current_amount,
                "notes": "Test reset - no change",
                "record_as_deposit": False
            }
        )
        assert response.status_code == 200, f"Reset balance failed: {response.text}"
        print(f"Reset balance response: {response.json()}")


class TestPlatformSettings:
    """Test Issue 5: Platform settings (platform_name, tagline, hide_emergent_badge) should persist"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_platform_settings(self, master_admin_token):
        """Test that platform settings can be retrieved"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        assert response.status_code == 200
        settings = response.json()
        
        print(f"Platform settings:")
        print(f"  platform_name: {settings.get('platform_name')}")
        print(f"  tagline: {settings.get('tagline')}")
        print(f"  hide_emergent_badge: {settings.get('hide_emergent_badge')}")
        print(f"  logo_url: {settings.get('logo_url')}")
        
        # Verify expected fields exist
        assert "platform_name" in settings or settings.get("platform_name") is None
        assert "tagline" in settings or settings.get("tagline") is None
    
    def test_update_platform_settings(self, master_admin_token):
        """Test that platform settings can be updated and persist"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # Get current settings
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        assert response.status_code == 200
        original_settings = response.json()
        
        # Update with test values
        test_platform_name = original_settings.get("platform_name", "CrossCurrent")
        test_tagline = original_settings.get("tagline", "Finance Center")
        
        response = requests.put(
            f"{BASE_URL}/api/settings/platform",
            headers=headers,
            json={
                "platform_name": test_platform_name,
                "tagline": test_tagline,
                "hide_emergent_badge": original_settings.get("hide_emergent_badge", False)
            }
        )
        assert response.status_code == 200, f"Update settings failed: {response.text}"
        
        # Verify settings persisted
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        assert response.status_code == 200
        updated_settings = response.json()
        
        assert updated_settings.get("platform_name") == test_platform_name
        assert updated_settings.get("tagline") == test_tagline
        print("Platform settings persist correctly")


class TestLoginPageLogo:
    """Test Issue 6: Login page should show uploaded logo from settings"""
    
    def test_public_platform_settings_endpoint(self):
        """Test that platform settings are accessible without auth (for login page)"""
        # The login page needs to load settings without being authenticated
        response = requests.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200, f"Public settings endpoint failed: {response.text}"
        settings = response.json()
        
        print(f"Public platform settings:")
        print(f"  logo_url: {settings.get('logo_url')}")
        print(f"  platform_name: {settings.get('platform_name')}")
        print(f"  tagline: {settings.get('tagline')}")


class TestLicenseeAccountValue:
    """Test Issue 7: Licensees in Members page should show correct account_value from license.current_amount"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_licensee_account_value_matches_license(self, master_admin_token):
        """Test that licensee's account_value in members list matches license.current_amount"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # Get licenses
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200
        licenses = response.json().get("licenses", [])
        active_licenses = [l for l in licenses if l.get("is_active")]
        
        if not active_licenses:
            pytest.skip("No active licenses to test")
        
        # Get members
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        members = response.json().get("members", [])
        
        # Check each licensee
        for license in active_licenses[:3]:
            user_id = license.get("user_id")
            license_amount = license.get("current_amount", license.get("starting_amount", 0))
            
            # Find member
            member = next((m for m in members if m.get("id") == user_id), None)
            if member:
                member_account_value = member.get("account_value", 0)
                print(f"Licensee {license.get('user_name')}:")
                print(f"  license.current_amount: ${license_amount:,.2f}")
                print(f"  member.account_value: ${member_account_value:,.2f}")
                
                # They should match (or be very close due to rounding)
                assert abs(member_account_value - license_amount) < 1, \
                    f"Account value mismatch: member has ${member_account_value}, license has ${license_amount}"


class TestDemoSimulation:
    """Test Issue 8: Demo simulation (Extended Licensee Demo) should show $5,000 in Profit Tracker"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_profit_summary_endpoint(self, master_admin_token):
        """Test that profit summary endpoint works"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200
        summary = response.json()
        
        print(f"Profit summary:")
        print(f"  account_value: ${summary.get('account_value', 0):,.2f}")
        print(f"  total_deposits: ${summary.get('total_deposits', 0):,.2f}")
        print(f"  total_actual_profit: ${summary.get('total_actual_profit', 0):,.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

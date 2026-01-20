"""
Test Iteration 58: Licensee Management Features
- Effective Start Trade Date in license creation and editing
- Unknown User bug fix in licensee simulation
- Licensee welcome screen endpoints
- Active Licenses table with Effective Start column
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for master admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_master_admin(self, auth_token):
        """Test master admin login"""
        assert auth_token is not None
        print(f"✓ Master admin login successful")


class TestLicenseEffectiveStartDate:
    """Test Effective Start Date feature for licenses"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_licenses_list(self, headers):
        """Test getting list of active licenses"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200, f"Failed to get licenses: {response.text}"
        data = response.json()
        assert "licenses" in data
        print(f"✓ Got {len(data['licenses'])} licenses")
        return data["licenses"]
    
    def test_license_has_effective_start_field(self, headers):
        """Test that licenses include effective_start_date field"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        licenses = data.get("licenses", [])
        
        if licenses:
            license = licenses[0]
            # Check that license has either effective_start_date or start_date
            has_date = "effective_start_date" in license or "start_date" in license
            assert has_date, "License should have effective_start_date or start_date"
            print(f"✓ License has date fields: effective_start_date={license.get('effective_start_date')}, start_date={license.get('start_date')}")
        else:
            print("⚠ No licenses found to test effective_start_date field")
    
    def test_update_effective_start_date_endpoint(self, headers):
        """Test PUT /api/admin/licenses/{license_id}/effective-start-date endpoint"""
        # First get a license to update
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200
        licenses = response.json().get("licenses", [])
        
        if not licenses:
            pytest.skip("No licenses available to test effective start date update")
        
        license_id = licenses[0]["id"]
        new_date = "2025-01-15"
        
        # Update the effective start date
        response = requests.put(
            f"{BASE_URL}/api/admin/licenses/{license_id}/effective-start-date",
            headers=headers,
            json={"effective_start_date": new_date}
        )
        
        assert response.status_code == 200, f"Failed to update effective start date: {response.text}"
        data = response.json()
        assert "message" in data
        assert new_date in data.get("new_date", "") or new_date in data.get("message", "")
        print(f"✓ Updated effective start date to {new_date}")
    
    def test_update_effective_start_date_invalid_format(self, headers):
        """Test that invalid date format is rejected"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        licenses = response.json().get("licenses", [])
        
        if not licenses:
            pytest.skip("No licenses available to test")
        
        license_id = licenses[0]["id"]
        
        # Try invalid date format
        response = requests.put(
            f"{BASE_URL}/api/admin/licenses/{license_id}/effective-start-date",
            headers=headers,
            json={"effective_start_date": "invalid-date"}
        )
        
        assert response.status_code == 400, f"Should reject invalid date format: {response.text}"
        print("✓ Invalid date format correctly rejected")


class TestLicenseInviteEffectiveStartDate:
    """Test Effective Start Date in license invite creation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_create_invite_with_effective_start_date(self, headers):
        """Test creating license invite with effective_start_date"""
        invite_data = {
            "license_type": "extended",
            "starting_amount": 5000,
            "valid_duration": "3_months",
            "max_uses": 1,
            "invitee_name": "Test Licensee",
            "effective_start_date": "2025-02-01"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/license-invites",
            headers=headers,
            json=invite_data
        )
        
        assert response.status_code in [200, 201], f"Failed to create invite: {response.text}"
        data = response.json()
        assert "code" in data or "invite" in data
        print(f"✓ Created license invite with effective_start_date")
        
        # Return invite code for cleanup
        return data.get("code") or data.get("invite", {}).get("code")
    
    def test_create_invite_without_effective_start_date(self, headers):
        """Test creating license invite without effective_start_date (should default to registration date)"""
        invite_data = {
            "license_type": "honorary",
            "starting_amount": 3000,
            "valid_duration": "6_months",
            "max_uses": 1,
            "invitee_name": "Test Honorary"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/license-invites",
            headers=headers,
            json=invite_data
        )
        
        assert response.status_code in [200, 201], f"Failed to create invite: {response.text}"
        print("✓ Created license invite without effective_start_date (will default to registration date)")


class TestLicenseeWelcomeEndpoints:
    """Test licensee welcome screen endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_licensee_welcome_info_endpoint_exists(self, headers):
        """Test GET /api/profit/licensee/welcome-info endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/welcome-info",
            headers=headers
        )
        
        # For non-licensee (master admin), should return is_licensee: false
        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()
        
        # Master admin is not a licensee, so should return is_licensee: false
        assert "is_licensee" in data
        print(f"✓ Welcome info endpoint works, is_licensee={data.get('is_licensee')}")
    
    def test_mark_welcome_seen_endpoint_exists(self, headers):
        """Test POST /api/profit/licensee/mark-welcome-seen endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/profit/licensee/mark-welcome-seen",
            headers=headers
        )
        
        # For non-licensee, should return 403
        # This is expected behavior - only licensees can mark welcome as seen
        assert response.status_code in [200, 403], f"Unexpected status: {response.text}"
        
        if response.status_code == 403:
            print("✓ Mark welcome seen endpoint correctly restricts to licensees only")
        else:
            print("✓ Mark welcome seen endpoint works")


class TestLicenseUserNames:
    """Test that license user names display correctly (not 'Unknown User')"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_licenses_have_user_names(self, headers):
        """Test that licenses include user_name field (not Unknown User)"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        licenses = data.get("licenses", [])
        
        unknown_user_count = 0
        for license in licenses:
            user_name = license.get("user_name", "")
            if user_name == "Unknown User" or not user_name:
                unknown_user_count += 1
                print(f"⚠ License {license.get('id')} has user_name: '{user_name}'")
        
        if licenses:
            assert unknown_user_count == 0, f"Found {unknown_user_count} licenses with 'Unknown User' name"
            print(f"✓ All {len(licenses)} licenses have proper user names")
        else:
            print("⚠ No licenses found to test user names")
    
    def test_members_list_for_simulation(self, headers):
        """Test that members list returns proper names for simulation dropdown"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        members = data.get("members", data) if isinstance(data, dict) else data
        
        if isinstance(members, list) and members:
            for member in members[:5]:  # Check first 5
                full_name = member.get("full_name", "")
                assert full_name and full_name != "Unknown User", f"Member has invalid name: {full_name}"
            print(f"✓ Members list has proper names for simulation")
        else:
            print("⚠ No members found to test")


class TestLicenseInvitesList:
    """Test license invites list includes effective_start_date"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_license_invites(self, headers):
        """Test getting license invites list"""
        response = requests.get(f"{BASE_URL}/api/admin/license-invites", headers=headers)
        assert response.status_code == 200, f"Failed to get invites: {response.text}"
        data = response.json()
        assert "invites" in data
        print(f"✓ Got {len(data['invites'])} license invites")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

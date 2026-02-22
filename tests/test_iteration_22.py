"""
Test Iteration 22: Licensee Features and Heartbeat API Verification

Features to test:
1. Heartbeat API verification works with real emails (hello@hyperdrivemg.co should return verified:true)
2. Login endpoint returns license_type for licensees
3. /api/auth/me endpoint returns license_type
4. Extended licensee login (hello@hyperdrivemg.co / test123) returns license_type: extended
5. Master Admin simulation of specific member includes license_type
6. Trade Monitor should be hidden for licensees in sidebar (frontend test)
7. Profit Tracker simulation/record/reset buttons hidden for licensees (frontend test)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://family-member-patch.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
EXTENDED_LICENSEE_EMAIL = "hello@hyperdrivemg.co"
EXTENDED_LICENSEE_PASSWORD = "test123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def master_admin_token(api_client):
    """Get master admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Master admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def licensee_token(api_client):
    """Get extended licensee authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": EXTENDED_LICENSEE_EMAIL,
        "password": EXTENDED_LICENSEE_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Licensee authentication failed: {response.status_code} - {response.text}")


class TestHeartbeatAPIVerification:
    """Test Heartbeat API verification with real emails"""
    
    def test_heartbeat_verify_real_email(self, api_client):
        """Test that hello@hyperdrivemg.co returns verified:true from Heartbeat API"""
        response = api_client.post(f"{BASE_URL}/api/auth/verify-heartbeat", json={
            "email": EXTENDED_LICENSEE_EMAIL
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return verified: true for a real Heartbeat member
        assert "verified" in data, f"Response missing 'verified' field: {data}"
        assert data["verified"] == True, f"Expected verified:true for {EXTENDED_LICENSEE_EMAIL}, got: {data}"
        
        # Should also return user info
        if data.get("user"):
            assert data["user"]["email"] == EXTENDED_LICENSEE_EMAIL.lower()
            print(f"✓ Heartbeat verification successful for {EXTENDED_LICENSEE_EMAIL}")
            print(f"  User info: {data['user']}")
    
    def test_heartbeat_verify_fake_email(self, api_client):
        """Test that a non-Heartbeat email returns verified:false"""
        response = api_client.post(f"{BASE_URL}/api/auth/verify-heartbeat", json={
            "email": "fake_nonexistent_user_12345@example.com"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return verified: false for non-member
        assert data.get("verified") == False, f"Expected verified:false for fake email, got: {data}"
        print("✓ Heartbeat correctly returns verified:false for non-member email")


class TestLoginLicenseType:
    """Test that login endpoint returns license_type for licensees"""
    
    def test_licensee_login_returns_license_type(self, api_client):
        """Test that extended licensee login returns license_type: extended"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": EXTENDED_LICENSEE_EMAIL,
            "password": EXTENDED_LICENSEE_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Check that user object contains license_type
        assert "user" in data, f"Response missing 'user' field: {data}"
        user = data["user"]
        
        assert "license_type" in user, f"User object missing 'license_type' field: {user}"
        assert user["license_type"] == "extended", f"Expected license_type='extended', got: {user['license_type']}"
        
        print(f"✓ Login returns license_type: {user['license_type']} for {EXTENDED_LICENSEE_EMAIL}")
    
    def test_master_admin_login_no_license_type(self, api_client):
        """Test that master admin login returns null/None license_type"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        
        user = data.get("user", {})
        # Master admin should have no license_type or null
        license_type = user.get("license_type")
        assert license_type is None, f"Master admin should have no license_type, got: {license_type}"
        
        print(f"✓ Master admin login correctly returns license_type: None")


class TestMeEndpointLicenseType:
    """Test that /api/auth/me endpoint returns license_type"""
    
    def test_me_endpoint_returns_license_type_for_licensee(self, api_client, licensee_token):
        """Test that /me endpoint returns license_type for licensee"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {licensee_token}"}
        )
        
        assert response.status_code == 200, f"Me endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "license_type" in data, f"Response missing 'license_type' field: {data}"
        assert data["license_type"] == "extended", f"Expected license_type='extended', got: {data['license_type']}"
        
        print(f"✓ /me endpoint returns license_type: {data['license_type']} for licensee")
    
    def test_me_endpoint_returns_null_license_type_for_admin(self, api_client, master_admin_token):
        """Test that /me endpoint returns null license_type for admin"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {master_admin_token}"}
        )
        
        assert response.status_code == 200, f"Me endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        
        license_type = data.get("license_type")
        assert license_type is None, f"Admin should have no license_type, got: {license_type}"
        
        print(f"✓ /me endpoint returns license_type: None for admin")


class TestMasterAdminSimulation:
    """Test Master Admin simulation includes license_type"""
    
    def test_get_members_list(self, api_client, master_admin_token):
        """Test that admin can get members list"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/members",
            headers={"Authorization": f"Bearer {master_admin_token}"}
        )
        
        assert response.status_code == 200, f"Get members failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "members" in data, f"Response missing 'members' field: {data}"
        assert len(data["members"]) > 0, "No members found"
        
        print(f"✓ Admin can get members list ({len(data['members'])} members)")
        return data["members"]
    
    def test_find_licensee_member(self, api_client, master_admin_token):
        """Find the licensee member in the members list"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/members?search={EXTENDED_LICENSEE_EMAIL}",
            headers={"Authorization": f"Bearer {master_admin_token}"}
        )
        
        assert response.status_code == 200, f"Search failed: {response.status_code} - {response.text}"
        data = response.json()
        
        members = data.get("members", [])
        licensee = None
        for m in members:
            if m.get("email", "").lower() == EXTENDED_LICENSEE_EMAIL.lower():
                licensee = m
                break
        
        assert licensee is not None, f"Licensee {EXTENDED_LICENSEE_EMAIL} not found in members"
        print(f"✓ Found licensee member: {licensee.get('full_name')} (ID: {licensee.get('id')})")
        return licensee
    
    def test_simulate_member_view_includes_license_type(self, api_client, master_admin_token):
        """Test that simulating a member view includes license_type"""
        # First find the licensee
        search_response = api_client.get(
            f"{BASE_URL}/api/admin/members?search={EXTENDED_LICENSEE_EMAIL}",
            headers={"Authorization": f"Bearer {master_admin_token}"}
        )
        
        assert search_response.status_code == 200
        members = search_response.json().get("members", [])
        
        licensee = None
        for m in members:
            if m.get("email", "").lower() == EXTENDED_LICENSEE_EMAIL.lower():
                licensee = m
                break
        
        if not licensee:
            pytest.skip(f"Licensee {EXTENDED_LICENSEE_EMAIL} not found")
        
        # Now simulate the member view
        simulate_response = api_client.get(
            f"{BASE_URL}/api/admin/members/{licensee['id']}/simulate",
            headers={"Authorization": f"Bearer {master_admin_token}"}
        )
        
        assert simulate_response.status_code == 200, f"Simulate failed: {simulate_response.status_code} - {simulate_response.text}"
        data = simulate_response.json()
        
        # Check that member data includes license_type
        member = data.get("member", {})
        assert "license_type" in member or member.get("license_type") is not None or "license_type" in str(data), \
            f"Simulation data should include license_type info: {data}"
        
        print(f"✓ Simulation data retrieved for {licensee.get('full_name')}")
        print(f"  Account value: ${data.get('account_value', 0):.2f}")
        print(f"  LOT size: {data.get('lot_size', 0):.2f}")
        
        # Check if member has license_type field
        if member.get("license_type"):
            print(f"  License type: {member.get('license_type')}")


class TestLicenseEndpoints:
    """Test license-related endpoints"""
    
    def test_get_licenses(self, api_client, master_admin_token):
        """Test that admin can get licenses list"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/licenses",
            headers={"Authorization": f"Bearer {master_admin_token}"}
        )
        
        assert response.status_code == 200, f"Get licenses failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "licenses" in data, f"Response missing 'licenses' field: {data}"
        
        # Find the extended licensee
        extended_licenses = [l for l in data["licenses"] if l.get("license_type") == "extended"]
        print(f"✓ Found {len(extended_licenses)} extended licenses")
        
        for lic in extended_licenses:
            print(f"  - {lic.get('user_name')}: ${lic.get('current_amount', 0):.2f}")


class TestUserResponseModel:
    """Test that UserResponse model includes license_type field"""
    
    def test_user_response_has_license_type_field(self, api_client, licensee_token):
        """Verify UserResponse model includes license_type"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {licensee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all expected fields in UserResponse
        expected_fields = ["id", "email", "full_name", "role", "created_at", "license_type"]
        for field in expected_fields:
            assert field in data, f"UserResponse missing field: {field}"
        
        print(f"✓ UserResponse model includes all expected fields including license_type")
        print(f"  Fields present: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

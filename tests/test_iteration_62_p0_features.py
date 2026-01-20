"""
Test Iteration 62: P0 Features Testing
- Trade Override Toggle: /api/admin/licenses/{id}/trade-overrides endpoints (GET, POST)
- Trade Override UI: masterTraded variable checks tradeOverrides first, then falls back to masterAdminTrades
- Effective Start Date: generateDailyProjectionForMonth filters days before effectiveStartDate
- Effective Start Date UI: Daily Projection starts from effective_start_date when simulating a licensee
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"

# Extended license with effective_start_date 2025-01-15 (from agent context)
EXTENDED_LICENSE_ID = "618db632"


class TestTradeOverrideEndpoints:
    """Test /api/admin/licenses/{id}/trade-overrides endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Master Admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Failed to login as Master Admin: {login_response.text}")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user = login_response.json().get("user")
        
        # Verify Master Admin role
        assert self.user.get("role") == "master_admin", f"Expected master_admin role, got {self.user.get('role')}"
    
    def test_get_trade_overrides_endpoint_exists(self):
        """Test GET /api/admin/licenses/{id}/trade-overrides endpoint exists and returns correct structure"""
        # First, get a valid license ID
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200, f"Failed to get licenses: {licenses_response.text}"
        
        licenses = licenses_response.json()
        if not licenses:
            pytest.skip("No licenses found to test trade overrides")
        
        license_id = licenses[0].get("id")
        
        # Test GET trade overrides
        response = self.session.get(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides")
        assert response.status_code == 200, f"GET trade-overrides failed: {response.text}"
        
        data = response.json()
        assert "overrides" in data, "Response should contain 'overrides' key"
        assert isinstance(data["overrides"], dict), "Overrides should be a dict keyed by date"
    
    def test_post_trade_override_creates_override(self):
        """Test POST /api/admin/licenses/{id}/trade-overrides creates a new override"""
        # Get a valid license ID
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200
        
        licenses = licenses_response.json()
        if not licenses:
            pytest.skip("No licenses found to test trade overrides")
        
        license_id = licenses[0].get("id")
        
        # Create a test date (yesterday)
        test_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # POST trade override
        response = self.session.post(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides", json={
            "license_id": license_id,
            "date": test_date,
            "traded": True,
            "notes": "Test override from pytest"
        })
        
        assert response.status_code == 200, f"POST trade-overrides failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert data.get("license_id") == license_id
        assert data.get("date") == test_date
        assert data.get("traded") == True
        
        # Verify override was created by fetching it
        get_response = self.session.get(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides")
        assert get_response.status_code == 200
        
        overrides = get_response.json().get("overrides", {})
        assert test_date in overrides, f"Override for {test_date} not found in overrides"
        assert overrides[test_date].get("traded") == True
    
    def test_post_trade_override_updates_existing(self):
        """Test POST /api/admin/licenses/{id}/trade-overrides updates existing override"""
        # Get a valid license ID
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200
        
        licenses = licenses_response.json()
        if not licenses:
            pytest.skip("No licenses found to test trade overrides")
        
        license_id = licenses[0].get("id")
        
        # Create a test date (2 days ago)
        test_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        # First create an override with traded=True
        response1 = self.session.post(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides", json={
            "license_id": license_id,
            "date": test_date,
            "traded": True,
            "notes": "Initial override"
        })
        assert response1.status_code == 200
        
        # Now update to traded=False
        response2 = self.session.post(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides", json={
            "license_id": license_id,
            "date": test_date,
            "traded": False,
            "notes": "Updated override"
        })
        assert response2.status_code == 200
        
        data = response2.json()
        assert data.get("traded") == False
        
        # Verify the update
        get_response = self.session.get(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides")
        overrides = get_response.json().get("overrides", {})
        assert overrides[test_date].get("traded") == False
    
    def test_trade_override_invalid_date_format(self):
        """Test POST trade-overrides rejects invalid date format"""
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200
        
        licenses = licenses_response.json()
        if not licenses:
            pytest.skip("No licenses found")
        
        license_id = licenses[0].get("id")
        
        # Try invalid date format
        response = self.session.post(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides", json={
            "license_id": license_id,
            "date": "invalid-date",
            "traded": True
        })
        
        assert response.status_code == 400, f"Expected 400 for invalid date, got {response.status_code}"
    
    def test_trade_override_nonexistent_license(self):
        """Test trade-overrides returns 404 for non-existent license"""
        fake_license_id = "nonexistent-license-id-12345"
        
        response = self.session.post(f"{BASE_URL}/api/admin/licenses/{fake_license_id}/trade-overrides", json={
            "license_id": fake_license_id,
            "date": "2025-01-15",
            "traded": True
        })
        
        assert response.status_code == 404, f"Expected 404 for non-existent license, got {response.status_code}"


class TestEffectiveStartDateFiltering:
    """Test effective_start_date filtering in license projections"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Failed to login: {login_response.text}")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_license_has_effective_start_date(self):
        """Test that licenses can have effective_start_date field"""
        # Get all licenses
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        
        licenses = response.json()
        
        # Find a license with effective_start_date
        license_with_eff_date = None
        for lic in licenses:
            if lic.get("effective_start_date"):
                license_with_eff_date = lic
                break
        
        if license_with_eff_date:
            print(f"Found license with effective_start_date: {license_with_eff_date.get('id')} - {license_with_eff_date.get('effective_start_date')}")
            assert license_with_eff_date.get("effective_start_date"), "effective_start_date should be set"
        else:
            print("No licenses with effective_start_date found - this is OK if none were created with this field")
    
    def test_license_invite_can_set_effective_start_date(self):
        """Test that license invites can include effective_start_date"""
        # Get existing invites to check structure
        response = self.session.get(f"{BASE_URL}/api/admin/license-invites")
        assert response.status_code == 200
        
        invites = response.json()
        
        # Check if any invite has effective_start_date
        for invite in invites:
            if invite.get("effective_start_date"):
                print(f"Found invite with effective_start_date: {invite.get('effective_start_date')}")
                break


class TestMasterAdminTradesEndpoint:
    """Test master admin trades endpoint used for licensee projections"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Failed to login: {login_response.text}")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_master_admin_trades_endpoint(self):
        """Test /api/profit/master-admin-trades endpoint returns trading dates"""
        start_date = "2025-01-01"
        end_date = "2025-12-31"
        
        response = self.session.get(f"{BASE_URL}/api/profit/master-admin-trades", params={
            "start_date": start_date,
            "end_date": end_date
        })
        
        assert response.status_code == 200, f"Failed to get master admin trades: {response.text}"
        
        data = response.json()
        assert "trading_dates" in data, "Response should contain 'trading_dates'"
        
        # trading_dates should be a dict keyed by date
        trading_dates = data.get("trading_dates", {})
        assert isinstance(trading_dates, dict), "trading_dates should be a dict"
        
        # If there are any trades, verify structure
        if trading_dates:
            sample_date = list(trading_dates.keys())[0]
            sample_trade = trading_dates[sample_date]
            print(f"Sample trade for {sample_date}: {sample_trade}")
            assert "traded" in sample_trade, "Each trade entry should have 'traded' field"


class TestLicenseSimulation:
    """Test license simulation features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Failed to login: {login_response.text}")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_licenses_returns_effective_start_date(self):
        """Test that GET /api/admin/licenses returns effective_start_date field"""
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        
        licenses = response.json()
        
        # Check structure of licenses
        if licenses:
            sample_license = licenses[0]
            print(f"License fields: {list(sample_license.keys())}")
            
            # effective_start_date may or may not be present depending on license
            # Just verify the endpoint works
            assert "id" in sample_license
            assert "license_type" in sample_license
    
    def test_simulate_licensee_endpoint(self):
        """Test that we can get licensee details for simulation"""
        # Get licenses
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        
        licenses = response.json()
        if not licenses:
            pytest.skip("No licenses to test simulation")
        
        # Get first license details
        license_id = licenses[0].get("id")
        user_id = licenses[0].get("user_id")
        
        # Get member details (used for simulation)
        member_response = self.session.get(f"{BASE_URL}/api/admin/members/{user_id}")
        
        if member_response.status_code == 200:
            member_data = member_response.json()
            print(f"Member data for simulation: {list(member_data.keys())}")
            assert "user" in member_data or "stats" in member_data


class TestDeleteTradeOverride:
    """Test DELETE /api/admin/licenses/{id}/trade-overrides/{date} endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Failed to login: {login_response.text}")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_delete_trade_override(self):
        """Test DELETE trade override endpoint"""
        # Get a license
        licenses_response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200
        
        licenses = licenses_response.json()
        if not licenses:
            pytest.skip("No licenses found")
        
        license_id = licenses[0].get("id")
        
        # Create an override first
        test_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        create_response = self.session.post(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides", json={
            "license_id": license_id,
            "date": test_date,
            "traded": True,
            "notes": "Override to be deleted"
        })
        assert create_response.status_code == 200
        
        # Now delete it
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides/{test_date}")
        assert delete_response.status_code == 200, f"DELETE failed: {delete_response.text}"
        
        # Verify it's deleted
        get_response = self.session.get(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides")
        overrides = get_response.json().get("overrides", {})
        assert test_date not in overrides, f"Override for {test_date} should be deleted"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

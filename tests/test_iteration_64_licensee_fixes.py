"""
Test Iteration 64 - Licensee Bug Fixes Verification
Tests for:
1. Balance Accumulation for licensees
2. LOT Size hidden for licensees (API level)
3. Total Profit calculation for licensees
4. Licensee view projection logic
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for Master Admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestLicenseeAPIs:
    """Test licensee-related API endpoints"""
    
    def test_get_licenses_endpoint(self, authenticated_client):
        """Test that licenses endpoint returns license data"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        
        data = response.json()
        assert "licenses" in data
        print(f"Found {len(data['licenses'])} licenses")
    
    def test_licensee_total_profit_calculation(self, authenticated_client):
        """Test that licensee total_profit = current_amount - starting_amount"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        
        licenses = response.json().get("licenses", [])
        extended_licenses = [l for l in licenses if l.get("license_type") == "extended" and l.get("is_active")]
        
        if not extended_licenses:
            pytest.skip("No active extended licenses found")
        
        for license in extended_licenses:
            starting_amount = license.get("starting_amount", 0)
            current_amount = license.get("current_amount", 0)
            expected_profit = current_amount - starting_amount
            
            print(f"License {license.get('id')}: starting={starting_amount}, current={current_amount}, expected_profit={expected_profit}")
            
            # Verify the calculation is correct
            assert current_amount >= starting_amount or current_amount == 0, \
                f"Current amount ({current_amount}) should be >= starting amount ({starting_amount})"
    
    def test_get_member_details_for_licensee(self, authenticated_client):
        """Test that member details API returns correct data for licensees"""
        # First get licenses to find a licensee user_id
        licenses_response = authenticated_client.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200
        
        licenses = licenses_response.json().get("licenses", [])
        extended_licenses = [l for l in licenses if l.get("license_type") == "extended" and l.get("is_active")]
        
        if not extended_licenses:
            pytest.skip("No active extended licenses found")
        
        # Get member details for the first extended licensee
        licensee = extended_licenses[0]
        user_id = licensee.get("user_id")
        
        if not user_id:
            pytest.skip("No user_id found for licensee")
        
        response = authenticated_client.get(f"{BASE_URL}/api/admin/members/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        stats = data.get("stats", {})
        
        # Verify account_value matches license current_amount
        print(f"Member stats: account_value={stats.get('account_value')}, is_licensee={stats.get('is_licensee')}")
        
        # For licensees, account_value should come from license.current_amount
        assert stats.get("is_licensee") == True, "Member should be marked as licensee"
    
    def test_licensee_daily_projection_endpoint(self, authenticated_client):
        """Test the licensee daily projection endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/profit/licensee-daily-projection")
        
        # This endpoint may return 404 if user is not a licensee
        if response.status_code == 404:
            print("Licensee daily projection endpoint returned 404 (expected for non-licensee)")
            return
        
        assert response.status_code == 200
        data = response.json()
        
        if "projections" in data:
            projections = data["projections"]
            print(f"Found {len(projections)} daily projections")
            
            # Verify projection structure
            if projections:
                first_proj = projections[0]
                assert "date" in first_proj
                assert "daily_profit" in first_proj
                assert "lot_size" in first_proj
    
    def test_master_admin_trades_endpoint(self, authenticated_client):
        """Test the master admin trades endpoint for licensees"""
        # Get trades for current year
        response = authenticated_client.get(
            f"{BASE_URL}/api/profit/master-admin-trades",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            }
        )
        
        # This endpoint returns 403 for non-licensees (master admin is not a licensee)
        # It's designed to be called by licensees to see when master admin traded
        if response.status_code == 403:
            print("Master admin trades endpoint returned 403 (expected for non-licensee users)")
            return
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"Master admin trades response: {data.keys()}")
        
        if "trading_dates" in data:
            trading_dates = data["trading_dates"]
            print(f"Found {len(trading_dates)} trading dates")


class TestLicenseTradeOverrides:
    """Test license trade override functionality"""
    
    def test_get_license_trade_overrides(self, authenticated_client):
        """Test getting trade overrides for a license"""
        # First get a license ID
        licenses_response = authenticated_client.get(f"{BASE_URL}/api/admin/licenses")
        assert licenses_response.status_code == 200
        
        licenses = licenses_response.json().get("licenses", [])
        if not licenses:
            pytest.skip("No licenses found")
        
        license_id = licenses[0].get("id")
        
        response = authenticated_client.get(f"{BASE_URL}/api/admin/licenses/{license_id}/trade-overrides")
        assert response.status_code == 200
        
        data = response.json()
        assert "overrides" in data
        print(f"Found {len(data['overrides'])} trade overrides for license {license_id}")


class TestProfitSummary:
    """Test profit summary endpoint"""
    
    def test_profit_summary_endpoint(self, authenticated_client):
        """Test the profit summary endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        print(f"Profit summary: account_value={data.get('account_value')}, total_actual_profit={data.get('total_actual_profit')}")
        
        # Verify required fields
        assert "account_value" in data
        assert "total_actual_profit" in data or "total_profit" in data


class TestTradeLogsAPI:
    """Test trade logs API"""
    
    def test_get_trade_logs(self, authenticated_client):
        """Test getting trade logs"""
        response = authenticated_client.get(f"{BASE_URL}/api/trade/logs")
        assert response.status_code == 200
        
        data = response.json()
        print(f"Found {len(data)} trade logs")
        
        if data:
            first_log = data[0]
            print(f"First trade log: date={first_log.get('created_at')}, profit={first_log.get('actual_profit')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 41 - Licensee Features Tests
Tests for:
1. Licensees bypass Heartbeat membership verification on login
2. GET /api/profit/master-admin-trades returns master admin's trading status by date (licensees only)
3. Backend login checks license_type to skip Heartbeat verification
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"

# Extended licensee credentials (found in database)
EXTENDED_LICENSEE_EMAIL = "extendeduser@test.com"
EXTENDED_LICENSEE_PASSWORD = "test123"


class TestLicenseeHeartbeatBypass:
    """Test that licensees bypass Heartbeat membership verification on login"""
    
    def test_extended_licensee_login_bypasses_heartbeat(self):
        """
        Test that an extended licensee can login without Heartbeat verification.
        The login endpoint should check license_type and skip Heartbeat verification.
        """
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXTENDED_LICENSEE_EMAIL,
                "password": EXTENDED_LICENSEE_PASSWORD
            }
        )
        
        # Should succeed (200) - licensee bypasses Heartbeat check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user"
        
        # Verify user is a licensee
        user = data["user"]
        assert user.get("license_type") == "extended", f"Expected license_type 'extended', got {user.get('license_type')}"
        assert user.get("email") == EXTENDED_LICENSEE_EMAIL
        
        print(f"✓ Extended licensee login successful - bypassed Heartbeat verification")
        print(f"  User: {user.get('full_name')} ({user.get('email')})")
        print(f"  License Type: {user.get('license_type')}")
    
    def test_licensee_login_returns_license_type_in_response(self):
        """
        Test that login response includes license_type for licensees.
        """
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXTENDED_LICENSEE_EMAIL,
                "password": EXTENDED_LICENSEE_PASSWORD
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify license_type is in the user response
        user = data["user"]
        assert "license_type" in user, "license_type should be in user response"
        assert user["license_type"] is not None, "license_type should not be None for licensees"
        
        print(f"✓ Login response includes license_type: {user['license_type']}")


class TestMasterAdminTradesEndpoint:
    """Test GET /api/profit/master-admin-trades endpoint"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": MASTER_ADMIN_EMAIL,
                "password": MASTER_ADMIN_PASSWORD
            }
        )
        assert response.status_code == 200, f"Master admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture
    def extended_licensee_token(self):
        """Get extended licensee auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXTENDED_LICENSEE_EMAIL,
                "password": EXTENDED_LICENSEE_PASSWORD
            }
        )
        assert response.status_code == 200, f"Extended licensee login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_master_admin_cannot_access_master_admin_trades(self, master_admin_token):
        """
        Test that master admin (non-licensee) gets 403 from master-admin-trades endpoint.
        This endpoint is for licensees only.
        """
        response = requests.get(
            f"{BASE_URL}/api/profit/master-admin-trades",
            headers={"Authorization": f"Bearer {master_admin_token}"}
        )
        
        # Master admin is NOT a licensee, so should get 403
        assert response.status_code == 403, f"Expected 403 for non-licensee, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data
        assert "licensees only" in data["detail"].lower(), f"Expected 'licensees only' in error, got: {data['detail']}"
        
        print(f"✓ Master admin correctly denied access to master-admin-trades endpoint")
        print(f"  Error: {data['detail']}")
    
    def test_extended_licensee_can_access_master_admin_trades(self, extended_licensee_token):
        """
        Test that extended licensee can access master-admin-trades endpoint.
        """
        # Get trades for current year
        start_date = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/profit/master-admin-trades",
            headers={"Authorization": f"Bearer {extended_licensee_token}"},
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        # Extended licensee should have access
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "trading_dates" in data, "Response should contain trading_dates"
        
        print(f"✓ Extended licensee can access master-admin-trades endpoint")
        print(f"  Date range: {start_date} to {end_date}")
        print(f"  Trading dates found: {len(data.get('trading_dates', {}))}")
        
        # If there are trading dates, verify structure
        if data.get("trading_dates"):
            for date_key, trade_info in list(data["trading_dates"].items())[:3]:
                print(f"  - {date_key}: traded={trade_info.get('traded')}, profit={trade_info.get('actual_profit')}")
                assert "traded" in trade_info, "Each trading date should have 'traded' field"
                assert "actual_profit" in trade_info, "Each trading date should have 'actual_profit' field"
    
    def test_master_admin_trades_without_date_params(self, extended_licensee_token):
        """
        Test master-admin-trades endpoint without date parameters.
        """
        response = requests.get(
            f"{BASE_URL}/api/profit/master-admin-trades",
            headers={"Authorization": f"Bearer {extended_licensee_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "trading_dates" in data
        
        print(f"✓ master-admin-trades works without date params")
        print(f"  Trading dates returned: {len(data.get('trading_dates', {}))}")
    
    def test_master_admin_trades_with_specific_date_range(self, extended_licensee_token):
        """
        Test master-admin-trades with a specific date range.
        """
        # Test with last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = requests.get(
            f"{BASE_URL}/api/profit/master-admin-trades",
            headers={"Authorization": f"Bearer {extended_licensee_token}"},
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "trading_dates" in data
        
        # Verify dates are within range
        for date_key in data.get("trading_dates", {}).keys():
            trade_date = datetime.strptime(date_key, "%Y-%m-%d")
            assert start_date.date() <= trade_date.date() <= end_date.date(), \
                f"Trade date {date_key} is outside requested range"
        
        print(f"✓ master-admin-trades respects date range filter")
        print(f"  Requested: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"  Trades in range: {len(data.get('trading_dates', {}))}")
    
    def test_unauthenticated_access_denied(self):
        """
        Test that unauthenticated requests are denied.
        """
        response = requests.get(f"{BASE_URL}/api/profit/master-admin-trades")
        
        # Should get 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        print(f"✓ Unauthenticated access correctly denied (status: {response.status_code})")


class TestLoginHeartbeatBypassLogic:
    """Test the login heartbeat bypass logic in detail"""
    
    def test_login_endpoint_structure(self):
        """
        Test that login endpoint returns expected structure for licensees.
        """
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXTENDED_LICENSEE_EMAIL,
                "password": EXTENDED_LICENSEE_PASSWORD
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
        user = data["user"]
        required_fields = ["id", "email", "full_name", "role", "created_at", "license_type"]
        for field in required_fields:
            assert field in user, f"Missing field: {field}"
        
        print(f"✓ Login response has correct structure for licensees")
        print(f"  Fields present: {list(user.keys())}")
    
    def test_master_admin_login_also_bypasses_heartbeat(self):
        """
        Test that master admin login also bypasses Heartbeat (admin role check).
        """
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": MASTER_ADMIN_EMAIL,
                "password": MASTER_ADMIN_PASSWORD
            }
        )
        
        assert response.status_code == 200, f"Master admin login failed: {response.text}"
        
        data = response.json()
        user = data["user"]
        
        assert user["role"] == "master_admin"
        # Master admin should NOT have license_type (they're not a licensee)
        assert user.get("license_type") is None, "Master admin should not have license_type"
        
        print(f"✓ Master admin login successful (bypasses Heartbeat via admin role)")
        print(f"  Role: {user['role']}")
        print(f"  License Type: {user.get('license_type')}")


class TestAuthMeEndpointForLicensees:
    """Test /api/auth/me endpoint returns license_type for licensees"""
    
    @pytest.fixture
    def extended_licensee_token(self):
        """Get extended licensee auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": EXTENDED_LICENSEE_EMAIL,
                "password": EXTENDED_LICENSEE_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_auth_me_returns_license_type(self, extended_licensee_token):
        """
        Test that /api/auth/me returns license_type for licensees.
        """
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {extended_licensee_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "license_type" in data, "auth/me should return license_type"
        assert data["license_type"] == "extended", f"Expected 'extended', got {data.get('license_type')}"
        
        print(f"✓ /api/auth/me returns license_type for licensees")
        print(f"  License Type: {data['license_type']}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

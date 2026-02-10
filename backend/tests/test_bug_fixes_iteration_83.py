"""
Test cases for Bug Fixes - Iteration 83
Testing 7 bugs:
1. 'Did Not Trade' error on fresh days
2. Reset Tracker password for simulated members should use Master Admin's password
3. Merin iframe should be responsive (frontend test)
4. Lysha onboarding not updating values (frontend test)
5. Mobile sticky signal should show LOT and Exit (frontend test)
6. Mobile disclaimer overlap (frontend test)
7. Trade History pagination with current month filter and 'Past Trades' button
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
SIMULATED_MEMBER_ID = "07062f66-d9ea-49ba-8fed-86ac6628b4e8"  # J J


class TestAuthentication:
    """Test authentication and get token"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_master_admin(self, auth_token):
        """Test Master Admin login"""
        assert auth_token is not None
        print(f"Master Admin login successful, token obtained")


class TestDidNotTrade:
    """Test Bug #1: 'Did Not Trade' error on fresh days"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_did_not_trade_endpoint_exists(self, auth_token):
        """Test that the did-not-trade endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try with a past date that likely has no trade
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # This should either succeed or fail with a specific error (not 500)
        response = requests.post(
            f"{BASE_URL}/api/trade/did-not-trade",
            params={"date": yesterday},
            headers=headers
        )
        
        # Should not be 500 (server error)
        assert response.status_code != 500, f"Server error: {response.text}"
        
        # Should be 200 (success) or 400 (trade already exists or invalid date)
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"Did not trade endpoint response: {response.status_code} - {response.json()}")
    
    def test_did_not_trade_future_date_rejected(self, auth_token):
        """Test that future dates are rejected"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try with a future date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/trade/did-not-trade",
            params={"date": tomorrow},
            headers=headers
        )
        
        # Should be 400 (bad request - can't mark future dates)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"Future date correctly rejected: {response.json()}")


class TestResetTracker:
    """Test Bug #2: Reset Tracker with simulation support"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_verify_password_endpoint(self, auth_token):
        """Test that verify-password endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test with correct password
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-password",
            json={"password": MASTER_ADMIN_PASSWORD},
            headers=headers
        )
        
        assert response.status_code == 200, f"Verify password failed: {response.text}"
        data = response.json()
        assert data.get("valid") == True, f"Password should be valid: {data}"
        print(f"Password verification successful: {data}")
    
    def test_verify_password_wrong(self, auth_token):
        """Test that wrong password is rejected"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test with wrong password
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-password",
            json={"password": "wrongpassword123"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Verify password endpoint failed: {response.text}"
        data = response.json()
        assert data.get("valid") == False, f"Wrong password should be invalid: {data}"
        print(f"Wrong password correctly rejected: {data}")
    
    def test_reset_endpoint_accepts_user_id(self, auth_token):
        """Test that reset endpoint accepts user_id parameter for simulation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test that the endpoint accepts user_id parameter (don't actually reset)
        # Just verify the endpoint structure
        response = requests.delete(
            f"{BASE_URL}/api/profit/reset",
            params={"user_id": "test-user-id-that-does-not-exist"},
            headers=headers
        )
        
        # Should work (even if user doesn't exist, it should process the request)
        # The endpoint should accept the parameter
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"Reset endpoint accepts user_id parameter: {response.status_code}")


class TestTradeHistory:
    """Test Bug #7: Trade History pagination with current month filter"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_trade_history_default_current_month(self, auth_token):
        """Test that trade history defaults to current month only"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/trade/history",
            headers=headers
        )
        
        assert response.status_code == 200, f"Trade history failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "trades" in data, f"Missing 'trades' in response: {data}"
        assert "total" in data, f"Missing 'total' in response: {data}"
        assert "total_pages" in data, f"Missing 'total_pages' in response: {data}"
        
        # Verify all trades are from current month
        current_month = datetime.now().strftime("%Y-%m")
        for trade in data["trades"]:
            trade_date = trade.get("created_at", "")
            if isinstance(trade_date, str):
                assert trade_date.startswith(current_month), f"Trade not from current month: {trade_date}"
        
        print(f"Trade history (current month): {len(data['trades'])} trades, total: {data['total']}")
    
    def test_trade_history_all_time(self, auth_token):
        """Test that trade history can fetch all-time trades"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/trade/history",
            params={"current_month_only": "false"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Trade history failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "trades" in data, f"Missing 'trades' in response: {data}"
        
        print(f"Trade history (all time): {len(data['trades'])} trades, total: {data['total']}")
    
    def test_trade_history_pagination(self, auth_token):
        """Test trade history pagination"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get page 1
        response = requests.get(
            f"{BASE_URL}/api/trade/history",
            params={"page": 1, "page_size": 5},
            headers=headers
        )
        
        assert response.status_code == 200, f"Trade history failed: {response.text}"
        data = response.json()
        
        assert "trades" in data
        assert "total_pages" in data
        assert len(data["trades"]) <= 5, f"Page size not respected: {len(data['trades'])}"
        
        print(f"Trade history pagination: page 1 has {len(data['trades'])} trades, total pages: {data['total_pages']}")


class TestStreakCalculation:
    """Test that streak calculation still includes all-time trades"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_streak_endpoint(self, auth_token):
        """Test streak endpoint returns valid data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/trade/streak",
            headers=headers
        )
        
        assert response.status_code == 200, f"Streak endpoint failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "streak" in data, f"Missing 'streak' in response: {data}"
        assert isinstance(data["streak"], int), f"Streak should be integer: {data}"
        
        print(f"Current streak: {data['streak']}, type: {data.get('streak_type')}")


class TestMemberSimulation:
    """Test member simulation functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_member_simulation_data(self, auth_token):
        """Test getting simulation data for a member"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{SIMULATED_MEMBER_ID}/simulation",
            headers=headers
        )
        
        # Should return 200 or 404 (if member doesn't exist)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"Member simulation data: account_value={data.get('account_value')}, lot_size={data.get('lot_size')}")
        else:
            print(f"Member {SIMULATED_MEMBER_ID} not found (expected if test data not seeded)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 146 Tests: Signal Deactivation Bug Fix + ProfitTrackerPage Refactoring

Tests:
1. Signal deactivation via PUT /api/admin/signals/{id} with {is_active: false}
2. Signal reactivation via PUT /api/admin/signals/{id} with {is_active: true}
3. Auth endpoints (login, me)
4. Health endpoint
5. Profit tracker summary endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://finance-flow-staging.preview.emergentagent.com')
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"
TEST_SIGNAL_ID = "4121c573-9099-4acf-b3f8-03efae3bb70e"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"Health check passed: {data}")
    
    def test_auth_login_success(self):
        """Test POST /api/auth/login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"Login success: token obtained for {data['user']['email']}")
    
    def test_auth_me_endpoint(self):
        """Test GET /api/auth/me with valid token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=10)
        token = login_response.json()["access_token"]
        
        # Then test /me endpoint
        response = requests.get(f"{BASE_URL}/api/auth/me", 
            headers={"Authorization": f"Bearer {token}"},
            timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("email") == TEST_EMAIL
        print(f"Auth /me passed: {data.get('email')}")


class TestSignalDeactivation:
    """Tests for the signal deactivation bug fix"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=10)
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_signals_list(self):
        """Test GET /api/admin/signals returns signals list"""
        response = requests.get(f"{BASE_URL}/api/admin/signals", 
            headers=self.headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Signals list: {len(data)} signals found")
    
    def test_signal_deactivation(self):
        """Test PUT /api/admin/signals/{id} with is_active: false - THE BUG FIX"""
        response = requests.put(f"{BASE_URL}/api/admin/signals/{TEST_SIGNAL_ID}",
            headers=self.headers,
            json={"is_active": False},
            timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("is_active") == False
        print(f"Signal deactivation SUCCESS: is_active={data.get('is_active')}")
    
    def test_signal_reactivation(self):
        """Test PUT /api/admin/signals/{id} with is_active: true"""
        response = requests.put(f"{BASE_URL}/api/admin/signals/{TEST_SIGNAL_ID}",
            headers=self.headers,
            json={"is_active": True},
            timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("is_active") == True
        print(f"Signal reactivation SUCCESS: is_active={data.get('is_active')}")


class TestProfitTracker:
    """Tests for Profit Tracker endpoints (to verify refactoring didn't break anything)"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=10)
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_profit_summary(self):
        """Test GET /api/profit/summary returns account data"""
        response = requests.get(f"{BASE_URL}/api/profit/summary",
            headers=self.headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "account_value" in data
        assert "total_deposits" in data
        print(f"Profit summary: account_value=${data.get('account_value')}")
    
    def test_profit_deposits(self):
        """Test GET /api/profit/deposits returns deposits list"""
        response = requests.get(f"{BASE_URL}/api/profit/deposits",
            headers=self.headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Deposits: {len(data)} records found")
    
    def test_trade_logs(self):
        """Test GET /api/trade/logs returns trade history"""
        response = requests.get(f"{BASE_URL}/api/trade/logs",
            headers=self.headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Trade logs: {len(data)} records found")


class TestAdminTransactions:
    """Tests for Admin Transactions page endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=10)
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_transactions_list(self):
        """Test GET /api/admin/transactions returns transactions"""
        response = requests.get(f"{BASE_URL}/api/admin/transactions",
            headers=self.headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        # Should return a dict with transactions list or pagination info
        assert "transactions" in data or isinstance(data, list)
        print(f"Admin transactions endpoint working")
    
    def test_admin_members_list(self):
        """Test GET /api/admin/members returns members"""
        response = requests.get(f"{BASE_URL}/api/admin/members",
            headers=self.headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        print(f"Admin members: {len(data.get('members', []))} found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

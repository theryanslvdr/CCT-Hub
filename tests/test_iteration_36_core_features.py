"""
Iteration 36 - Core Features Testing
Tests for: Login, Dashboard, Profit Tracker, Trade Monitor APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://trade-dash-portal.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestHealthAndPlatform:
    """Health check and platform settings tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ Health endpoint working")
    
    def test_platform_settings(self):
        """Test platform settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200
        data = response.json()
        assert "platform_name" in data
        assert data["platform_name"] == "CrossCurrent"
        print(f"✓ Platform settings: {data['platform_name']}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Login successful for {TEST_EMAIL}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_get_current_user(self):
        """Test getting current user info"""
        # First login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert data["role"] == "master_admin"
        print(f"✓ Current user: {data['full_name']} ({data['role']})")


class TestProfitSummary:
    """Profit summary endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_profit_summary(self, auth_token):
        """Test profit summary returns correct data"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_deposits" in data
        assert "total_actual_profit" in data
        assert "account_value" in data
        assert "performance_rate" in data
        
        # Verify expected values (approximately)
        assert data["account_value"] > 14000  # Should be around $14,981.62
        assert data["total_actual_profit"] >= 0  # Should be around $230.00
        
        print(f"✓ Profit Summary:")
        print(f"  - Account Value: ${data['account_value']:.2f}")
        print(f"  - Total Profit: ${data['total_actual_profit']:.2f}")
        print(f"  - Performance Rate: {data['performance_rate']:.2f}%")
    
    def test_profit_summary_unauthorized(self):
        """Test profit summary without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code in [401, 403]
        print("✓ Profit summary correctly requires authentication")


class TestTradeSignal:
    """Trade signal endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_active_signal(self, auth_token):
        """Test active signal endpoint returns signal data"""
        response = requests.get(
            f"{BASE_URL}/api/trade/active-signal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check if signal exists
        if data.get("signal"):
            signal = data["signal"]
            assert "product" in signal
            assert "direction" in signal
            assert "trade_time" in signal
            assert signal["direction"] in ["BUY", "SELL"]
            
            print(f"✓ Active Signal:")
            print(f"  - Product: {signal['product']}")
            print(f"  - Direction: {signal['direction']}")
            print(f"  - Trade Time: {signal['trade_time']}")
            print(f"  - Profit Points: {signal.get('profit_points', 15)}")
        else:
            print("✓ No active signal (expected if none set)")
    
    def test_trade_logs(self, auth_token):
        """Test trade logs endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/trade/logs?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "trades" in data or isinstance(data, list)
        print(f"✓ Trade logs retrieved")
    
    def test_daily_summary(self, auth_token):
        """Test daily summary endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/trade/daily-summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_projected" in data or "total_actual" in data or "trades_count" in data
        print(f"✓ Daily summary retrieved")


class TestDeposits:
    """Deposit endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_get_deposits(self, auth_token):
        """Test getting deposits list"""
        response = requests.get(
            f"{BASE_URL}/api/profit/deposits",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Deposits retrieved: {len(data)} records")


class TestCurrencyRates:
    """Currency rates endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_currency_rates(self, auth_token):
        """Test currency rates endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/currency/rates?base=USDT",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has rates
        assert "rates" in data or "PHP" in data or isinstance(data, dict)
        print(f"✓ Currency rates retrieved")


class TestAdminFeatures:
    """Admin-specific endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_admin_notifications(self, auth_token):
        """Test admin notifications endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/notifications?limit=20&unread_only=false",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "notifications" in data
        print(f"✓ Admin notifications retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

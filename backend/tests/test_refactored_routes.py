"""
Test refactored route modules after major backend decomposition.
Backend server.py (10,302 lines) was split into:
- routes/auth_routes.py (705 lines)
- routes/profit_routes.py (2241 lines)
- routes/trade_routes.py (1246 lines)
- routes/admin_routes.py (4510 lines)
- routes/general_routes.py (472 lines)
- helpers.py (shared functions)
- deps.py (auth dependencies)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


class TestRefactoredRoutes:
    """Test all critical API endpoints after route extraction"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "master_admin"
        return data["access_token"]

    # ─── Auth Routes Tests (auth_routes.py) ───
    
    def test_auth_login(self):
        """Test POST /api/auth/login - returns access_token and user object"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "master_admin"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert "id" in data["user"]
        assert "full_name" in data["user"]
    
    def test_auth_login_invalid_credentials(self):
        """Test POST /api/auth/login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_auth_me(self, auth_token):
        """Test GET /api/auth/me - returns user details with Bearer token"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert response.status_code == 200, f"Get me failed: {response.text}"
        data = response.json()
        
        # Verify user details
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "master_admin"
        assert "id" in data
        assert "full_name" in data
    
    def test_auth_me_no_token(self):
        """Test GET /api/auth/me without token - should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Should require auth: {response.text}"

    # ─── Profit Routes Tests (profit_routes.py) ───
    
    def test_profit_summary(self, auth_token):
        """Test GET /api/profit/summary - returns financial summary"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200, f"Profit summary failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "total_deposits" in data
        assert "total_projected_profit" in data
        assert "total_actual_profit" in data
        assert "account_value" in data
        assert "total_trades" in data
        assert "performance_rate" in data
    
    def test_profit_deposits(self, auth_token):
        """Test GET /api/profit/deposits - returns array of deposit records"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/deposits", headers=headers)
        
        assert response.status_code == 200, f"Deposits failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
    
    def test_profit_withdrawals(self, auth_token):
        """Test GET /api/profit/withdrawals - returns array of withdrawal records"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/withdrawals", headers=headers)
        
        assert response.status_code == 200, f"Withdrawals failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)

    # ─── Trade Routes Tests (trade_routes.py) ───
    
    def test_trade_logs(self, auth_token):
        """Test GET /api/trade/logs - returns array of trade log records"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/logs", headers=headers)
        
        assert response.status_code == 200, f"Trade logs failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
    
    def test_trade_active_signal(self, auth_token):
        """Test GET /api/trade/active-signal - check active signal endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        
        assert response.status_code == 200, f"Active signal failed: {response.text}"
        data = response.json()
        
        # Response can have signal or message
        assert "signal" in data or "message" in data
    
    def test_trade_streak(self, auth_token):
        """Test GET /api/trade/streak - returns streak info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/streak", headers=headers)
        
        assert response.status_code == 200, f"Trade streak failed: {response.text}"
        data = response.json()
        
        # Verify streak fields
        assert "streak" in data
        assert isinstance(data["streak"], int)
        assert "total_trades" in data
    
    def test_trade_history(self, auth_token):
        """Test GET /api/trade/history - returns paginated trade history"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=headers)
        
        assert response.status_code == 200, f"Trade history failed: {response.text}"
        data = response.json()
        
        # Verify pagination structure
        assert "trades" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_trade_global_holidays(self, auth_token):
        """Test GET /api/trade/global-holidays - returns global holidays for authenticated user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/global-holidays", headers=headers)
        
        assert response.status_code == 200, f"Global holidays failed: {response.text}"
        data = response.json()
        
        assert "holidays" in data
        assert isinstance(data["holidays"], list)

    # ─── Admin Routes Tests (admin_routes.py) ───
    
    def test_admin_members(self, auth_token):
        """Test GET /api/admin/members - returns paginated members list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        
        assert response.status_code == 200, f"Admin members failed: {response.text}"
        data = response.json()
        
        # Verify pagination structure
        assert "members" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["members"], list)
    
    def test_admin_transactions(self, auth_token):
        """Test GET /api/admin/transactions - returns paginated transactions"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/transactions", headers=headers)
        
        assert response.status_code == 200, f"Admin transactions failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data
        assert "total" in data
        assert isinstance(data["transactions"], list)
    
    def test_admin_signals(self, auth_token):
        """Test GET /api/admin/signals - returns trading signals list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/signals", headers=headers)
        
        assert response.status_code == 200, f"Admin signals failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
    
    def test_admin_global_holidays(self, auth_token):
        """Test GET /api/admin/global-holidays - returns global holidays (admin)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/global-holidays", headers=headers)
        
        assert response.status_code == 200, f"Admin global holidays failed: {response.text}"
        data = response.json()
        
        assert "holidays" in data
        assert isinstance(data["holidays"], list)
    
    def test_admin_trading_products(self, auth_token):
        """Test GET /api/admin/trading-products - returns trading products"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/trading-products", headers=headers)
        
        assert response.status_code == 200, f"Trading products failed: {response.text}"
        data = response.json()
        
        assert "products" in data
        assert isinstance(data["products"], list)
    
    def test_admin_analytics_team(self, auth_token):
        """Test GET /api/admin/analytics/team - returns team analytics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics/team", headers=headers)
        
        assert response.status_code == 200, f"Team analytics failed: {response.text}"
        data = response.json()
        
        # Verify analytics fields
        assert "total_account_value" in data
        assert "total_profit" in data
        assert "total_traders" in data
        assert "total_trades" in data

    # ─── General Routes Tests (general_routes.py) ───
    
    def test_health_check(self):
        """Test GET /api/health - returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        
        # Verify health response
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_root_endpoint(self):
        """Test GET /api/ - returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        
        assert response.status_code == 200, f"Root endpoint failed: {response.text}"
        data = response.json()
        
        # Verify API response
        assert "message" in data
        assert "CrossCurrent" in data["message"]
    
    def test_build_version(self):
        """Test GET /api/version - returns build version"""
        response = requests.get(f"{BASE_URL}/api/version")
        
        assert response.status_code == 200, f"Version endpoint failed: {response.text}"
        data = response.json()
        
        assert "build_version" in data
    
    def test_notifications(self, auth_token):
        """Test GET /api/notifications - returns user notifications"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        
        assert response.status_code == 200, f"Notifications failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "notifications" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)

    # ─── Forum Routes Tests ───
    
    def test_forum_posts(self, auth_token):
        """Test GET /api/forum/posts - returns paginated forum posts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/forum/posts", headers=headers)
        
        assert response.status_code == 200, f"Forum posts failed: {response.text}"
        data = response.json()
        
        # Verify pagination structure
        assert "posts" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["posts"], list)

    # ─── Additional Feature Tests ───
    
    def test_my_recent_transactions(self, auth_token):
        """Test GET /api/profit/my-recent-transactions - member self-edit feature"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/my-recent-transactions", headers=headers)
        
        assert response.status_code == 200, f"My recent transactions failed: {response.text}"
        data = response.json()
        
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
    
    def test_balance_on_date(self, auth_token):
        """Test GET /api/profit/balance-on-date - historical balance lookup"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/profit/balance-on-date",
            headers=headers,
            params={"date": today}
        )
        
        assert response.status_code == 200, f"Balance on date failed: {response.text}"
        data = response.json()
        
        assert "balance_on_date" in data
        assert "lot_size" in data
        assert "date" in data


class TestDepsModule:
    """Test that deps.py auth dependencies work correctly"""
    
    def test_token_validation(self):
        """Test that tokens are properly validated"""
        # Login to get valid token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Use valid token
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Use invalid token
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 401


class TestHelperFunctions:
    """Test helper functions via API endpoints that use them"""
    
    def test_calculate_exit_value(self, auth_token):
        """Test calculate_exit_value via profit/summary"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200
        # The summary uses helpers.truncate_lot_size and calculate_exit_value internally
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["access_token"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 89 - Backend Refactoring & Data Health Badge Tests

Tests for:
1. Extracted debt routes (GET /api/debt)
2. Extracted goals routes (GET /api/goals)
3. Extracted currency routes (GET /api/currency/rates)
4. Regression check for existing endpoints (GET /api/profit/sync-validation, POST /api/profit/balance-override)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestExtractedRoutes:
    """Test the refactored routes (debt, goals, currency)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Login response missing access_token"
        return data["access_token"]

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authenticated headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    def test_debt_endpoint_returns_user_debts(self, auth_headers):
        """GET /api/debt - should return user's debts (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/debt", headers=auth_headers)
        assert response.status_code == 200, f"Debt endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Debt endpoint should return a list"
        # Each debt should have required fields
        if len(data) > 0:
            debt = data[0]
            required_fields = ["id", "user_id", "name", "total_amount", "remaining_amount", "minimum_payment"]
            for field in required_fields:
                assert field in debt, f"Debt missing required field: {field}"
        print(f"✓ GET /api/debt returns {len(data)} debts")

    def test_goals_endpoint_returns_user_goals(self, auth_headers):
        """GET /api/goals - should return user's goals (extracted route)"""
        response = requests.get(f"{BASE_URL}/api/goals", headers=auth_headers)
        assert response.status_code == 200, f"Goals endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Goals endpoint should return a list"
        # Each goal should have required fields
        if len(data) > 0:
            goal = data[0]
            required_fields = ["id", "user_id", "name", "target_amount", "current_amount", "progress_percentage"]
            for field in required_fields:
                assert field in goal, f"Goal missing required field: {field}"
        print(f"✓ GET /api/goals returns {len(data)} goals")

    def test_currency_rates_usd(self, auth_headers):
        """GET /api/currency/rates?base=USD - should return exchange rates"""
        response = requests.get(f"{BASE_URL}/api/currency/rates?base=USD", headers=auth_headers)
        assert response.status_code == 200, f"Currency rates endpoint failed: {response.text}"
        data = response.json()
        assert "base" in data, "Response missing 'base' field"
        assert "rates" in data, "Response missing 'rates' field"
        assert data["base"] == "USD", f"Expected base='USD', got {data['base']}"
        assert isinstance(data["rates"], dict), "Rates should be a dictionary"
        print(f"✓ GET /api/currency/rates?base=USD returns rates with {len(data['rates'])} currencies")

    def test_currency_rates_usdt(self, auth_headers):
        """GET /api/currency/rates?base=USDT - should return USDT rates"""
        response = requests.get(f"{BASE_URL}/api/currency/rates?base=USDT", headers=auth_headers)
        assert response.status_code == 200, f"Currency USDT rates endpoint failed: {response.text}"
        data = response.json()
        assert "base" in data, "Response missing 'base' field"
        assert "rates" in data, "Response missing 'rates' field"
        assert data["base"] == "USDT", f"Expected base='USDT', got {data['base']}"
        assert isinstance(data["rates"], dict), "Rates should be a dictionary"
        # USDT should have USD conversion
        assert "USD" in data["rates"], "USDT rates should include USD"
        print(f"✓ GET /api/currency/rates?base=USDT returns {len(data['rates'])} currencies, USD rate: {data['rates'].get('USD')}")


class TestRegressionEndpoints:
    """Regression tests for existing endpoints that were NOT extracted"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data["access_token"]

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authenticated headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    def test_sync_validation_endpoint(self, auth_headers):
        """GET /api/profit/sync-validation - regression check (not extracted)"""
        response = requests.get(f"{BASE_URL}/api/profit/sync-validation", headers=auth_headers)
        assert response.status_code == 200, f"Sync validation endpoint failed: {response.text}"
        data = response.json()
        # Check for expected fields in sync validation response
        expected_fields = ["can_sync", "summary"]
        for field in expected_fields:
            assert field in data, f"Sync validation missing field: {field}"
        # Verify summary structure
        summary = data.get("summary", {})
        summary_fields = ["total_trading_days", "reported_days", "missing_days"]
        for field in summary_fields:
            assert field in summary, f"Summary missing field: {field}"
        print(f"✓ GET /api/profit/sync-validation works - can_sync: {data['can_sync']}, missing_days: {summary.get('missing_days')}")

    def test_balance_override_endpoint(self, auth_headers):
        """POST /api/profit/balance-override - regression check (not extracted)"""
        # Use a reasonable test value
        response = requests.post(
            f"{BASE_URL}/api/profit/balance-override",
            headers=auth_headers,
            json={
                "actual_balance": 1000.00,
                "reason": "Test override from iteration 89"
            }
        )
        assert response.status_code == 200, f"Balance override endpoint failed: {response.text}"
        data = response.json()
        assert "message" in data, "Response missing 'message' field"
        assert "override" in data, "Response missing 'override' field"
        print(f"✓ POST /api/profit/balance-override works - message: {data['message']}")

    def test_profit_summary_endpoint(self, auth_headers):
        """GET /api/profit/summary - verify account value and other stats"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200, f"Profit summary endpoint failed: {response.text}"
        data = response.json()
        expected_fields = ["total_deposits", "account_value", "total_trades"]
        for field in expected_fields:
            assert field in data, f"Summary missing field: {field}"
        print(f"✓ GET /api/profit/summary works - account_value: {data['account_value']}")


class TestAuthEndpoints:
    """Basic auth endpoint tests"""

    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert "user" in data, "Response missing user"
        assert data["user"]["email"] == "iam@ryansalvador.com"
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Login successful for {data['user']['email']} with role {data['user']['role']}")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401, f"Expected 401 for invalid login, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected with 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

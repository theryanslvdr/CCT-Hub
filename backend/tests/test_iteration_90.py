"""
Iteration 90 - Regression Testing After Refactoring

Tests for:
1. Health endpoint (GET /api/health)
2. Auth endpoints (POST /api/auth/login)
3. Profit summary and sync-validation (regression)
4. Extracted debt routes (GET /api/debt)
5. Extracted goals routes (GET /api/goals)
6. Extracted currency routes (GET /api/currency/rates)
7. API Center webhook endpoint (POST /api/api-center/receive) - NEWLY EXTRACTED
8. Platform settings (GET /api/settings/platform)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthEndpoint:
    """Test basic health endpoint"""
    
    def test_health_returns_healthy(self):
        """GET /api/health - should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy", f"Expected healthy status, got: {data}"
        print(f"✓ Health endpoint returns 'healthy' status")


class TestAuthEndpoints:
    """Authentication endpoint tests"""

    def test_login_success(self):
        """POST /api/auth/login - valid credentials should return access_token"""
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
        """POST /api/auth/login - invalid credentials should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401, f"Expected 401 for invalid login, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected with 401")


class TestProfitEndpoints:
    """Profit tracker endpoint tests (regression)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_profit_summary_returns_account_data(self, auth_headers):
        """GET /api/profit/summary - should return account data (regression)"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200, f"Profit summary failed: {response.text}"
        data = response.json()
        expected_fields = ["total_deposits", "account_value", "total_trades", "total_actual_profit"]
        for field in expected_fields:
            assert field in data, f"Summary missing field: {field}"
        print(f"✓ GET /api/profit/summary works - account_value: {data['account_value']}, trades: {data['total_trades']}")

    def test_sync_validation_returns_validation_data(self, auth_headers):
        """GET /api/profit/sync-validation - should return validation data (regression)"""
        response = requests.get(f"{BASE_URL}/api/profit/sync-validation", headers=auth_headers)
        assert response.status_code == 200, f"Sync validation failed: {response.text}"
        data = response.json()
        assert "can_sync" in data, "Response missing 'can_sync'"
        assert "summary" in data, "Response missing 'summary'"
        summary = data.get("summary", {})
        summary_fields = ["total_trading_days", "reported_days", "missing_days"]
        for field in summary_fields:
            assert field in summary, f"Summary missing field: {field}"
        print(f"✓ GET /api/profit/sync-validation works - can_sync: {data['can_sync']}, missing_days: {summary.get('missing_days')}")


class TestExtractedRoutes:
    """Test the extracted routes (debt, goals, currency)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_debt_endpoint_returns_debts(self, auth_headers):
        """GET /api/debt - should return debts (extracted route, regression)"""
        response = requests.get(f"{BASE_URL}/api/debt", headers=auth_headers)
        assert response.status_code == 200, f"Debt endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Debt endpoint should return a list"
        print(f"✓ GET /api/debt returns {len(data)} debts")

    def test_goals_endpoint_returns_goals(self, auth_headers):
        """GET /api/goals - should return goals (extracted route, regression)"""
        response = requests.get(f"{BASE_URL}/api/goals", headers=auth_headers)
        assert response.status_code == 200, f"Goals endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Goals endpoint should return a list"
        print(f"✓ GET /api/goals returns {len(data)} goals")

    def test_currency_rates_returns_rates(self, auth_headers):
        """GET /api/currency/rates - should return exchange rates (extracted route, regression)"""
        response = requests.get(f"{BASE_URL}/api/currency/rates?base=USD", headers=auth_headers)
        assert response.status_code == 200, f"Currency rates failed: {response.text}"
        data = response.json()
        assert "base" in data, "Response missing 'base'"
        assert "rates" in data, "Response missing 'rates'"
        assert data["base"] == "USD"
        print(f"✓ GET /api/currency/rates returns {len(data['rates'])} currencies")


class TestAPICenterRoutes:
    """Test the API Center routes (NEWLY EXTRACTED)"""
    
    def test_receive_webhook_accepts_payload(self):
        """POST /api/api-center/receive - should accept webhook payload (extracted route)"""
        response = requests.post(
            f"{BASE_URL}/api/api-center/receive",
            json={
                "action": "test",
                "data": {"message": "Test webhook from iteration 90"}
            }
        )
        assert response.status_code == 200, f"Webhook receive failed: {response.text}"
        data = response.json()
        assert data.get("received") == True, "Response should have received=True"
        assert "webhook_id" in data, "Response should have webhook_id"
        print(f"✓ POST /api/api-center/receive works - webhook_id: {data['webhook_id']}")


class TestSettingsEndpoints:
    """Test settings endpoints"""
    
    def test_platform_settings_returns_settings(self):
        """GET /api/settings/platform - should return platform settings"""
        response = requests.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200, f"Platform settings failed: {response.text}"
        data = response.json()
        expected_fields = ["platform_name", "tagline", "site_title"]
        for field in expected_fields:
            assert field in data, f"Settings missing field: {field}"
        print(f"✓ GET /api/settings/platform returns settings - platform_name: {data.get('platform_name')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

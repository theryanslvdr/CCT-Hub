"""
CrossCurrent Hub - Backend Regression Test Suite
Run: cd /app/backend && python -m pytest tests/ -v
"""
import pytest
import httpx
import os

BASE_URL = os.environ.get("TEST_API_URL", "https://dark-theme-overhaul-4.preview.emergentagent.com")
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="session")
def api_url():
    return BASE_URL


@pytest.fixture(scope="session")
def auth_token(api_url):
    """Get auth token for the test session."""
    resp = httpx.post(
        f"{api_url}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15.0,
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data.keys()}"
    return token


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealth:
    def test_health_endpoint(self, api_url):
        resp = httpx.get(f"{api_url}/api/health", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"

    def test_version_endpoint(self, api_url):
        resp = httpx.get(f"{api_url}/api/version", timeout=10.0)
        assert resp.status_code == 200
        assert "build_version" in resp.json()


class TestAuth:
    def test_login_success(self, api_url):
        resp = httpx.post(
            f"{api_url}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=15.0,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data or "token" in data
        assert data["user"]["role"] == "master_admin"

    def test_login_wrong_password(self, api_url):
        resp = httpx.post(
            f"{api_url}/api/auth/login",
            json={"email": TEST_EMAIL, "password": "wrongpassword"},
            timeout=10.0,
        )
        assert resp.status_code in [401, 400]

    def test_me_endpoint(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/auth/me", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == TEST_EMAIL
        assert data["role"] == "master_admin"

    def test_me_no_auth(self, api_url):
        resp = httpx.get(f"{api_url}/api/auth/me", timeout=10.0)
        assert resp.status_code in [401, 403]


class TestProfitRoutes:
    def test_summary(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/profit/summary", headers=auth_headers, timeout=15.0)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_deposits" in data

    def test_deposits(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/profit/deposits", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_withdrawals(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/profit/withdrawals", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_daily_balances_requires_params(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/profit/daily-balances", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 422  # Missing required params

    def test_daily_balances_with_params(self, api_url, auth_headers):
        resp = httpx.get(
            f"{api_url}/api/profit/daily-balances",
            headers=auth_headers,
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
            timeout=15.0,
        )
        assert resp.status_code == 200


class TestTradeRoutes:
    def test_trade_logs(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/trade/logs", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_trade_streak(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/trade/streak", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert "current_streak" in data


class TestAdminRoutes:
    def test_admin_members(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/admin/members", headers=auth_headers, timeout=15.0)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data or isinstance(data, list)

    def test_admin_transactions(self, api_url, auth_headers):
        resp = httpx.get(
            f"{api_url}/api/admin/transactions",
            headers=auth_headers,
            params={"limit": 5},
            timeout=15.0,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data or "total" in data

    def test_admin_analytics_team(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/admin/analytics/team", headers=auth_headers, timeout=15.0)
        assert resp.status_code == 200

    def test_admin_signals(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/admin/signals", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_admin_global_holidays(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/admin/global-holidays", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_admin_trading_products(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/admin/trading-products", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestSystemHealth:
    def test_system_health_master_admin(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/admin/system-health", headers=auth_headers, timeout=15.0)
        assert resp.status_code == 200
        data = resp.json()
        assert "uptime" in data
        assert "system" in data
        assert "database" in data
        assert "websockets" in data
        assert "route_latencies" in data
        assert "external_services" in data
        assert "users" in data
        assert "build" in data

    def test_system_health_db_ping(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/admin/system-health/db-ping", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["ping_ms"] > 0

    def test_system_health_no_auth(self, api_url):
        resp = httpx.get(f"{api_url}/api/admin/system-health", timeout=10.0)
        assert resp.status_code in [401, 403]


class TestForumRoutes:
    def test_forum_posts(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/forum/posts", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert "posts" in data
        assert "total" in data

    def test_forum_categories(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/forum/categories", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200


class TestRewardsRoutes:
    def test_rewards_leaderboard(self, api_url, auth_headers):
        resp = httpx.get(f"{api_url}/api/rewards/leaderboard", headers=auth_headers, timeout=10.0)
        assert resp.status_code == 200

"""Comprehensive tests for /api/trade/* endpoints (trade_routes.py)."""
import pytest
import requests


class TestTradeLogs:
    """GET /api/trade/logs"""

    def test_trade_logs(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/logs", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_trade_logs_no_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/trade/logs")
        assert resp.status_code in [401, 403]


class TestTradeHistory:
    """GET /api/trade/history"""

    def test_trade_history_default(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/history", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "trades" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["trades"], list)

    def test_trade_history_pagination(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/trade/history",
            headers=admin_headers,
            params={"page": 1, "page_size": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestTradeStreak:
    """GET /api/trade/streak"""

    def test_trade_streak(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/streak", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "streak" in data
        assert isinstance(data["streak"], int)
        assert "total_trades" in data


class TestActiveSignal:
    """GET /api/trade/active-signal"""

    def test_active_signal(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/active-signal", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Can have signal or message
        assert "signal" in data or "message" in data


class TestDailySummary:
    """GET /api/trade/daily-summary"""

    def test_daily_summary(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/daily-summary", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestMissedTradeStatus:
    """GET /api/trade/missed-trade-status"""

    def test_missed_trade_status(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/missed-trade-status", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestGlobalHolidays:
    """GET /api/trade/global-holidays"""

    def test_global_holidays(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/global-holidays", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "holidays" in data
        assert isinstance(data["holidays"], list)


class TestTradingProducts:
    """GET /api/trade/trading-products"""

    def test_trading_products(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/trading-products", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        assert isinstance(data["products"], list)


class TestUserHolidays:
    """GET /api/trade/holidays"""

    def test_user_holidays(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/holidays", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))


class TestSignalBlockStatus:
    """GET /api/trade/signal-block-status"""

    def test_signal_block_status(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/trade/signal-block-status", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

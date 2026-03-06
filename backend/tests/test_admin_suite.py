"""Comprehensive tests for /api/admin/* endpoints (admin_routes.py)."""
import pytest
import requests


class TestAdminMembers:
    """GET /api/admin/members"""

    def test_members_list(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/members", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "members" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["members"], list)

    def test_members_pagination(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/admin/members",
            headers=admin_headers,
            params={"page": 1, "limit": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["members"]) <= 3

    def test_members_search(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/admin/members",
            headers=admin_headers,
            params={"search": "ryan"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["members"], list)

    def test_members_no_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/admin/members")
        assert resp.status_code in [401, 403]


class TestAdminMemberDetail:
    """GET /api/admin/members/{user_id}"""

    def test_member_detail(self, base_url, admin_headers, admin_user):
        user_id = admin_user["id"]
        resp = requests.get(
            f"{base_url}/api/admin/members/{user_id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Response structure: { user: {...}, stats: {...}, recent_deposits: [...], recent_trades: [...] }
        assert "user" in data
        assert "stats" in data

    def test_member_detail_not_found(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/admin/members/nonexistent_id_xyz",
            headers=admin_headers,
        )
        assert resp.status_code == 404


class TestAdminMemberDeposits:
    """GET /api/admin/members/{user_id}/deposits"""

    def test_member_deposits(self, base_url, admin_headers, admin_user):
        resp = requests.get(
            f"{base_url}/api/admin/members/{admin_user['id']}/deposits",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAdminMemberWithdrawals:
    """GET /api/admin/members/{user_id}/withdrawals"""

    def test_member_withdrawals(self, base_url, admin_headers, admin_user):
        resp = requests.get(
            f"{base_url}/api/admin/members/{admin_user['id']}/withdrawals",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAdminTransactions:
    """GET /api/admin/transactions"""

    def test_transactions(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/transactions", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data
        assert "total" in data
        assert isinstance(data["transactions"], list)

    def test_transactions_stats(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/transactions/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestAdminSignals:
    """GET /api/admin/signals"""

    def test_signals_list(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/signals", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_signals_history(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/signals/history", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_signals_archive(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/signals/archive", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestAdminGlobalHolidays:
    """GET /api/admin/global-holidays"""

    def test_global_holidays(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/global-holidays", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "holidays" in data
        assert isinstance(data["holidays"], list)


class TestAdminTradingProducts:
    """GET /api/admin/trading-products"""

    def test_trading_products(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/trading-products", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        assert isinstance(data["products"], list)


class TestAdminAnalytics:
    """GET /api/admin/analytics/*"""

    def test_team_analytics(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/analytics/team", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        for field in ["total_account_value", "total_profit", "total_traders", "total_trades"]:
            assert field in data, f"Missing field: {field}"

    def test_today_stats(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/analytics/today-stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_missed_trades_analytics(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/analytics/missed-trades", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_growth_data(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/analytics/growth-data", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_recent_trades(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/analytics/recent-trades", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_member_analytics(self, base_url, admin_headers, admin_user):
        resp = requests.get(
            f"{base_url}/api/admin/analytics/member/{admin_user['id']}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestAdminNotifications:
    """GET /api/admin/notifications"""

    def test_notifications(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/notifications", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))


class TestAdminLicenses:
    """GET /api/admin/licenses"""

    def test_licenses_list(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/licenses", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestAdminTradeChangeRequests:
    """GET /api/admin/trade-change-requests"""

    def test_trade_change_requests(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/trade-change-requests", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

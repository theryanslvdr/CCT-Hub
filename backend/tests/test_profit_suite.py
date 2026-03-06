"""Comprehensive tests for /api/profit/* endpoints (profit_routes.py)."""
import pytest
import requests
from datetime import datetime


class TestProfitSummary:
    """GET /api/profit/summary"""

    def test_summary_authenticated(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/summary", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        for field in ["total_deposits", "total_projected_profit", "total_actual_profit",
                       "account_value", "total_trades", "performance_rate"]:
            assert field in data, f"Missing field: {field}"

    def test_summary_no_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/profit/summary")
        assert resp.status_code in [401, 403]


class TestProfitDeposits:
    """GET /api/profit/deposits"""

    def test_deposits_list(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/deposits", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_deposits_no_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/profit/deposits")
        assert resp.status_code in [401, 403]


class TestProfitWithdrawals:
    """GET /api/profit/withdrawals"""

    def test_withdrawals_list(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/withdrawals", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestProfitCommissions:
    """GET /api/profit/commissions"""

    def test_commissions_list(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/commissions", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestBalanceOnDate:
    """GET /api/profit/balance-on-date"""

    def test_balance_on_date_today(self, base_url, admin_headers):
        today = datetime.now().strftime("%Y-%m-%d")
        resp = requests.get(
            f"{base_url}/api/profit/balance-on-date",
            headers=admin_headers,
            params={"date": today},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "balance_on_date" in data
        assert "lot_size" in data
        assert "date" in data

    def test_balance_on_date_missing_param(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/profit/balance-on-date",
            headers=admin_headers,
        )
        assert resp.status_code == 422  # missing required query param


class TestDailyBalances:
    """GET /api/profit/daily-balances"""

    def test_daily_balances(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/profit/daily-balances",
            headers=admin_headers,
            params={"start_date": "2025-01-01", "end_date": "2025-01-31"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_daily_balances_missing_params(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/daily-balances", headers=admin_headers)
        assert resp.status_code == 422


class TestMyRecentTransactions:
    """GET /api/profit/my-recent-transactions"""

    def test_my_recent_transactions(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/profit/my-recent-transactions",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data
        assert isinstance(data["transactions"], list)


class TestCalculateExit:
    """POST /api/profit/calculate-exit?lot_size=..."""

    def test_calculate_exit(self, base_url):
        resp = requests.post(
            f"{base_url}/api/profit/calculate-exit",
            params={"lot_size": 0.5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "exit_value" in data
        assert "lot_size" in data


class TestSimulateWithdrawal:
    """POST /api/profit/simulate-withdrawal"""

    def test_simulate_withdrawal(self, base_url, admin_headers):
        resp = requests.post(
            f"{base_url}/api/profit/simulate-withdrawal",
            headers=admin_headers,
            json={"amount": 100.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should return simulation details
        assert data is not None


class TestVSD:
    """GET /api/profit/vsd — Visual Summary Data"""

    def test_vsd(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/vsd", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestSyncValidation:
    """GET /api/profit/sync-validation"""

    def test_sync_validation(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/sync-validation", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestOnboardingStatus:
    """GET /api/profit/onboarding-status"""

    def test_onboarding_status(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/profit/onboarding-status", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestLicenseProjections:
    """GET /api/profit/license-projections"""

    def test_license_projections(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/profit/license-projections",
            headers=admin_headers,
        )
        # Might return 200 or 404 if no licenses
        assert resp.status_code in [200, 404]


class TestMasterAdminTrades:
    """GET /api/profit/master-admin-trades — licensees only."""

    def test_master_admin_trades_non_licensee(self, base_url, admin_headers):
        """Non-licensee (admin) should get 403."""
        resp = requests.get(
            f"{base_url}/api/profit/master-admin-trades",
            headers=admin_headers,
        )
        assert resp.status_code == 403


class TestBalanceOverride:
    """GET /api/profit/balance-override"""

    def test_get_balance_override(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/profit/balance-override",
            headers=admin_headers,
        )
        assert resp.status_code == 200

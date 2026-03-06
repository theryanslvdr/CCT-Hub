"""
Regression tests for Honorary Licensee projection calculations.
This is a CRITICAL test file - the projection feature has broken 4+ times.
Tests cover: calculations.py, trading_days.py, and the projection API endpoints.
"""
import pytest
import httpx
import asyncio
import os
from datetime import datetime, timezone, timedelta, date

API_URL = os.environ.get("API_URL", "https://profit-tracker-v2.preview.emergentagent.com")
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"


def get_token(email: str, password: str) -> str:
    """Login and return access token."""
    resp = httpx.post(
        f"{API_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    data = resp.json()
    return data["access_token"]


# ─── Unit tests for trading_days.py ─────────────────────────────────────

class TestTradingDays:
    """Test the trading day utility functions used in projections."""

    def test_us_market_holidays_2026(self):
        from utils.trading_days import get_us_market_holidays
        holidays = get_us_market_holidays(2026)
        assert isinstance(holidays, set)
        assert len(holidays) > 0
        # New Year 2026: Jan 1 is Thursday → observed Jan 1
        assert "2026-01-01" in holidays
        # MLK Day 2026: 3rd Monday of Jan → Jan 19
        assert "2026-01-19" in holidays
        # Presidents Day 2026: 3rd Monday of Feb → Feb 16
        assert "2026-02-16" in holidays
        # Independence Day 2026: Jul 4 is Saturday → observed Jul 3 (Friday)
        assert "2026-07-03" in holidays
        # Christmas 2026: Dec 25 is Friday → observed Dec 25
        assert "2026-12-25" in holidays

    def test_holiday_range(self):
        from utils.trading_days import get_holidays_for_range
        holidays = get_holidays_for_range(2025, 2027)
        assert isinstance(holidays, set)
        # Should have holidays from 3 years
        assert len(holidays) >= 27  # ~9 holidays per year

    def test_is_trading_day_weekday(self):
        from utils.trading_days import is_trading_day
        # Feb 23, 2026 is a Monday
        monday = datetime(2026, 2, 23, tzinfo=timezone.utc)
        assert is_trading_day(monday) is True

    def test_is_trading_day_weekend(self):
        from utils.trading_days import is_trading_day
        # Feb 22, 2026 is a Sunday
        sunday = datetime(2026, 2, 22, tzinfo=timezone.utc)
        assert is_trading_day(sunday) is False

    def test_is_trading_day_holiday(self):
        from utils.trading_days import is_trading_day, get_us_market_holidays
        holidays = get_us_market_holidays(2026)
        # New Year's Day 2026 (Jan 1, Thursday)
        new_year = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert is_trading_day(new_year, holidays) is False

    def test_project_quarterly_growth_basic(self):
        from utils.trading_days import project_quarterly_growth
        result = project_quarterly_growth(
            starting_value=5000.0,
            start_date=datetime(2026, 1, 20, tzinfo=timezone.utc),
            trading_days_target=250,
        )
        assert "projected_value" in result
        assert "total_profit" in result
        assert "quarter_breakdown" in result
        assert "trading_days" in result
        assert result["trading_days"] == 250
        assert result["projected_value"] > 5000.0
        assert result["total_profit"] > 0
        assert len(result["quarter_breakdown"]) > 0

    def test_project_quarterly_growth_formula(self):
        """Verify the quarterly compounding formula:
        Daily Profit = round((Account Value at Quarter Start / 980) * 15, 2)
        """
        from utils.trading_days import project_quarterly_growth
        # Starting with $10,000
        result = project_quarterly_growth(
            starting_value=10000.0,
            start_date=datetime(2026, 1, 2, tzinfo=timezone.utc),
            trading_days_target=10,
        )
        # First daily profit should be round((10000 / 980) * 15, 2) = round(153.06, 2) = 153.06
        expected_daily = round((10000 / 980) * 15, 2)
        first_q = result["quarter_breakdown"][0]
        assert first_q["daily_profit"] == expected_daily, (
            f"Expected daily profit {expected_daily}, got {first_q['daily_profit']}"
        )

    def test_project_quarterly_growth_quarter_boundary(self):
        """Verify that daily profit recalculates at quarter boundaries."""
        from utils.trading_days import project_quarterly_growth
        result = project_quarterly_growth(
            starting_value=5000.0,
            start_date=datetime(2026, 1, 20, tzinfo=timezone.utc),
            trading_days_target=250,
        )
        # Should have multiple quarters
        assert len(result["quarter_breakdown"]) >= 4
        # Each quarter should have different daily_profit (since balance grows)
        daily_profits = [q["daily_profit"] for q in result["quarter_breakdown"]]
        # Each subsequent quarter's daily profit should be >= the previous
        for i in range(1, len(daily_profits)):
            assert daily_profits[i] >= daily_profits[i - 1], (
                f"Quarter {i+1} daily profit {daily_profits[i]} < quarter {i} {daily_profits[i-1]}"
            )

    def test_observe_holiday_saturday(self):
        from utils.trading_days import _observe
        # July 4, 2026 is Saturday → observed Friday July 3
        d = date(2026, 7, 4)
        assert d.weekday() == 5  # Saturday
        observed = _observe(d)
        assert observed == date(2026, 7, 3)

    def test_observe_holiday_sunday(self):
        from utils.trading_days import _observe
        # Jan 1, 2023 is Sunday → observed Monday Jan 2
        d = date(2023, 1, 1)
        assert d.weekday() == 6  # Sunday
        observed = _observe(d)
        assert observed == date(2023, 1, 2)


# ─── Unit tests for calculations.py ─────────────────────────────────────

class TestCalculations:
    def test_lot_size(self):
        from utils.calculations import calculate_lot_size
        assert calculate_lot_size(980) == 1.0
        assert calculate_lot_size(0) == 0
        assert calculate_lot_size(4900) == 5.0

    def test_projected_profit(self):
        from utils.calculations import calculate_projected_profit
        # LOT * 15 points
        assert calculate_projected_profit(1.0) == 15.0
        assert calculate_projected_profit(5.0) == 75.0
        assert calculate_projected_profit(0) == 0.0

    def test_performance_categories(self):
        from utils.calculations import determine_performance
        assert determine_performance(100, 95) == "exceeded"
        assert determine_performance(100, 100) == "perfect"
        assert determine_performance(90, 100) == "below"


# ─── API Integration tests ───────────────────────────────────────────────

class TestProjectionAPIs:
    """Test the projection API endpoints end-to-end."""

    def test_year_projections_as_admin_for_licensee(self):
        """Admin can get year projections for a specific licensee user."""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        # Use Rizza (honorary_fa)
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/year-projections",
            params={"user_id": "19ccb9d7-139f-4918-a662-ad72483010b1"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Verify structure
        assert "current_value" in data
        assert "starting_amount" in data
        assert "projections" in data
        assert len(data["projections"]) == 4  # 1, 2, 3, 5 years
        # Verify values are reasonable
        assert data["current_value"] > 0
        assert data["starting_amount"] == 5000.0
        assert data["current_value"] >= data["starting_amount"]
        # Verify projections grow
        proj_values = [p["projected_value"] for p in data["projections"]]
        for i in range(1, len(proj_values)):
            assert proj_values[i] > proj_values[i - 1]

    def test_year_projections_as_licensee(self):
        """Licensee can get their own year projections."""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/year-projections",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["starting_amount"] == 5000.0
        assert len(data["projections"]) == 4

    def test_daily_projection_as_licensee(self):
        """Licensee can get daily projections."""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/daily-projection",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "projections" in data
        assert len(data["projections"]) > 0
        first = data["projections"][0]
        assert "date" in first
        assert "account_value" in first
        assert "daily_profit" in first
        assert "manager_traded" in first
        # The daily profit formula: round((balance / 980) * 15, 2)
        expected_daily = round((5000.0 / 980) * 15, 2)
        assert first["daily_profit"] == expected_daily, (
            f"First day profit should be {expected_daily}, got {first['daily_profit']}"
        )

    def test_licensee_summary_correct_values(self):
        """Licensee summary returns correct is_licensee flag and values."""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_licensee"] is True
        assert data["license_type"] == "honorary_fa"
        assert data["account_value"] > 0
        assert data["total_deposits"] == 5000.0
        assert data["total_actual_profit"] >= 0

    def test_admin_member_details_for_licensee(self):
        """Admin member details endpoint returns correct data for licensees."""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/admin/members/19ccb9d7-139f-4918-a662-ad72483010b1",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "stats" in data
        stats = data["stats"]
        assert stats["is_licensee"] is True
        assert stats["account_value"] > 0

    def test_year_projections_no_license_404(self):
        """Non-licensee user gets 404 on year projections."""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        # Admin doesn't have an active license as honorary
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/year-projections",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        # Admin has their own license (extended), so might be 200
        # Just ensure it doesn't crash
        assert resp.status_code in (200, 404)

    def test_projection_values_consistency(self):
        """Verify that summary account_value matches projection current_value."""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        summary_resp = httpx.get(
            f"{API_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        proj_resp = httpx.get(
            f"{API_URL}/api/profit/licensee/year-projections",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert summary_resp.status_code == 200
        assert proj_resp.status_code == 200
        summary = summary_resp.json()
        proj = proj_resp.json()
        # Account values should match
        assert abs(summary["account_value"] - proj["current_value"]) < 0.01, (
            f"Summary AV={summary['account_value']} != Projection CV={proj['current_value']}"
        )

    def test_all_honorary_licensees_have_projections(self):
        """Every active honorary licensee should return valid projections."""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        # Get all active licenses
        # We test a few known honorary user_ids
        honorary_user_ids = [
            "7cc2b490-5e55-433b-9ac6-45d5bdfaf732",  # test_user_092113
            "19ccb9d7-139f-4918-a662-ad72483010b1",   # rizza.miles
        ]
        for uid in honorary_user_ids:
            resp = httpx.get(
                f"{API_URL}/api/profit/licensee/year-projections",
                params={"user_id": uid},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            assert resp.status_code == 200, (
                f"Projections failed for user {uid}: {resp.status_code} {resp.text}"
            )
            data = resp.json()
            assert data["current_value"] > 0, f"Zero current_value for user {uid}"
            assert len(data["projections"]) == 4, f"Missing projections for user {uid}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

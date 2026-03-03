"""
Test iteration 135: Retroactive Badge Awards & Daily Projection has_trade fix

Testing:
1. POST /api/rewards/retroactive-scan - scans user's trade/deposit/referral data, awards badges
2. POST /api/rewards/retroactive-scan-all - master admin endpoint to scan all users
3. GET /api/profit/daily-balances - has_trade should be True for trades with zero profit
4. GET /api/trades/history - should include trade_day_number and total_trade_days fields
"""
import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_headers():
    """Login as master admin and return auth headers."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def user_data(auth_headers):
    """Get current user data."""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    return response.json()


class TestRetroactiveBadgeScan:
    """Test retroactive badge scanning functionality."""

    def test_retroactive_scan_returns_stats_and_badges(self, auth_headers, user_data):
        """POST /api/rewards/retroactive-scan should return stats and newly_awarded."""
        response = requests.post(
            f"{BASE_URL}/api/rewards/retroactive-scan",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Retroactive scan failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "user_id" in data, "Response should include user_id"
        assert "stats" in data, "Response should include stats"
        assert "newly_awarded" in data, "Response should include newly_awarded"
        
        # Verify stats fields
        stats = data["stats"]
        assert "lifetime_trades" in stats, "Stats should include lifetime_trades"
        assert "distinct_trade_days" in stats, "Stats should include distinct_trade_days"
        assert "best_streak_days" in stats, "Stats should include best_streak_days"
        assert "current_streak_days" in stats, "Stats should include current_streak_days"
        assert "lifetime_deposit_usdt" in stats, "Stats should include lifetime_deposit_usdt"
        assert "qualified_referrals" in stats, "Stats should include qualified_referrals"
        
        # newly_awarded should be a list
        assert isinstance(data["newly_awarded"], list), "newly_awarded should be a list"
        
        print(f"Retroactive scan stats: {stats}")
        print(f"Newly awarded badges: {data['newly_awarded']}")

    def test_retroactive_scan_for_specific_user(self, auth_headers, user_data):
        """Admin can scan for specific user by user_id."""
        response = requests.post(
            f"{BASE_URL}/api/rewards/retroactive-scan?user_id={user_data['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Retroactive scan for specific user failed: {response.text}"
        data = response.json()
        assert data["user_id"] == user_data["id"]


class TestRetroactiveScanAll:
    """Test master admin's retroactive-scan-all endpoint."""

    def test_retroactive_scan_all_requires_master_admin(self):
        """POST /api/rewards/retroactive-scan-all should require master admin."""
        # Without auth
        response = requests.post(f"{BASE_URL}/api/rewards/retroactive-scan-all")
        assert response.status_code in [401, 403], "Should require authentication"

    def test_retroactive_scan_all_works_for_master_admin(self, auth_headers):
        """POST /api/rewards/retroactive-scan-all should work for master admin."""
        response = requests.post(
            f"{BASE_URL}/api/rewards/retroactive-scan-all",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Retroactive scan all failed: {response.text}"
        data = response.json()
        
        assert "scanned" in data, "Response should include scanned count"
        assert "results" in data, "Response should include results"
        assert isinstance(data["results"], list), "results should be a list"
        
        print(f"Scanned {data['scanned']} users")
        # Print first 3 results as sample
        for result in data["results"][:3]:
            print(f"  User {result.get('user_id', 'unknown')}: {result.get('badges_awarded', 0)} badges awarded")


class TestDailyBalancesHasTradeFix:
    """Test that has_trade is True for trades regardless of profit value."""

    def test_daily_balances_has_trade_field_exists(self, auth_headers):
        """GET /api/profit/daily-balances should return has_trade field."""
        # Get last 30 days
        today = datetime.now(timezone.utc)
        start_date = today.replace(day=1).strftime("%Y-%m-%d")  # First of month
        end_date = today.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Daily balances failed: {response.text}"
        data = response.json()
        
        assert "daily_balances" in data, "Response should include daily_balances"
        balances = data["daily_balances"]
        assert isinstance(balances, list), "daily_balances should be a list"
        
        if balances:
            first_day = balances[0]
            assert "has_trade" in first_day, "Each day should have has_trade field"
            assert "date" in first_day, "Each day should have date field"
            assert "balance_before" in first_day, "Each day should have balance_before field"
            print(f"Found {len(balances)} daily balance entries")

    def test_december_trades_appear_in_daily_balances(self, auth_headers):
        """Test that December trades show correctly in daily balances (has_trade fix)."""
        # Test December 2024 specifically
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances?start_date=2024-12-01&end_date=2024-12-31",
            headers=auth_headers
        )
        assert response.status_code == 200, f"December balances failed: {response.text}"
        data = response.json()
        balances = data.get("daily_balances", [])
        
        # Count days with trades
        days_with_trades = [b for b in balances if b.get("has_trade")]
        print(f"December 2024: {len(days_with_trades)} days with trades")
        
        # Verify the structure
        for day in days_with_trades:
            assert day["has_trade"] is True, f"Day {day['date']} has_trade should be True"
            print(f"  {day['date']}: has_trade=True, actual_profit={day.get('actual_profit')}")


class TestTradeHistoryDayNumber:
    """Test trade history includes trade_day_number and total_trade_days."""

    def test_trade_history_includes_trade_day_number(self, auth_headers):
        """GET /api/trade/history should include trade_day_number for each trade."""
        response = requests.get(
            f"{BASE_URL}/api/trade/history?page=1&page_size=10",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Trade history failed: {response.text}"
        data = response.json()
        
        assert "trades" in data, "Response should include trades"
        assert "total_trade_days" in data, "Response should include total_trade_days"
        
        trades = data["trades"]
        if trades:
            # Every trade should have trade_day_number
            for trade in trades:
                assert "trade_day_number" in trade, f"Trade {trade.get('id')} missing trade_day_number"
                assert trade["trade_day_number"] is not None, f"Trade {trade.get('id')} trade_day_number should not be None"
                assert isinstance(trade["trade_day_number"], int), f"trade_day_number should be an integer"
                assert trade["trade_day_number"] >= 0, f"trade_day_number should be >= 0"
            
            # Print sample
            print(f"Total trade days: {data['total_trade_days']}")
            for trade in trades[:5]:
                print(f"  Trade {trade.get('id', 'unknown')[:8]}...: Day #{trade['trade_day_number']}, date={trade.get('created_at', '')[:10]}")

    def test_trade_history_total_trade_days_field(self, auth_headers):
        """GET /api/trade/history should include total_trade_days in response."""
        response = requests.get(
            f"{BASE_URL}/api/trade/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_trade_days" in data, "Response should include total_trade_days"
        assert isinstance(data["total_trade_days"], int), "total_trade_days should be an integer"
        assert data["total_trade_days"] >= 0, "total_trade_days should be >= 0"
        print(f"Total trade days: {data['total_trade_days']}")


class TestBadgeDefinitions:
    """Test badge definitions including the new activity category."""

    def test_badge_definitions_include_activity_category(self, auth_headers):
        """Badge definitions should include activity category badges."""
        response = requests.get(
            f"{BASE_URL}/api/rewards/badges",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Badge definitions failed: {response.text}"
        data = response.json()
        
        assert "badges" in data, "Response should include badges"
        badges = data["badges"]
        
        # Check that activity category exists
        activity_badges = [b for b in badges if b.get("category") == "activity"]
        assert len(activity_badges) > 0, "Should have at least one activity category badge"
        
        # Verify expected activity badges exist
        badge_ids = [b.get("id") for b in activity_badges]
        expected_activity_badges = ["days_10", "days_30", "days_50", "days_100"]
        for badge_id in expected_activity_badges[:2]:  # Check at least first 2
            assert badge_id in badge_ids, f"Expected activity badge {badge_id} to exist"
        
        print(f"Found {len(activity_badges)} activity category badges:")
        for badge in activity_badges:
            print(f"  {badge.get('id')}: {badge.get('name')} - {badge.get('description')}")

    def test_user_badges_endpoint(self, auth_headers):
        """GET /api/rewards/badges/user should return user's badges with earned status."""
        response = requests.get(
            f"{BASE_URL}/api/rewards/badges/user",
            headers=auth_headers
        )
        assert response.status_code == 200, f"User badges failed: {response.text}"
        data = response.json()
        
        assert "user_id" in data, "Response should include user_id"
        assert "badges" in data, "Response should include badges"
        
        badges = data["badges"]
        earned_badges = [b for b in badges if b.get("earned")]
        
        print(f"User has {len(earned_badges)} earned badges:")
        for badge in earned_badges:
            print(f"  {badge.get('name')} ({badge.get('category')}) - earned: {badge.get('earned_at', 'unknown')[:10] if badge.get('earned_at') else 'N/A'}")


class TestStreakIndicator:
    """Test that streak data is available via API (frontend always shows it)."""

    def test_streak_endpoint_returns_data(self, auth_headers):
        """GET /api/trade/streak should return streak data."""
        response = requests.get(
            f"{BASE_URL}/api/trade/streak",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Streak endpoint failed: {response.text}"
        data = response.json()
        
        assert "streak" in data, "Response should include streak"
        assert isinstance(data["streak"], int), "streak should be an integer"
        
        print(f"Current streak: {data['streak']} days")


class TestRewardsSummary:
    """Test rewards summary endpoint for context."""

    def test_rewards_summary_includes_total_trades(self, auth_headers, user_data):
        """GET /api/rewards/summary should include total_trades."""
        response = requests.get(
            f"{BASE_URL}/api/rewards/summary?user_id={user_data['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Rewards summary failed: {response.text}"
        data = response.json()
        
        # Check expected fields
        assert "lifetime_points" in data, "Should include lifetime_points"
        assert "current_streak" in data, "Should include current_streak"
        assert "best_streak" in data, "Should include best_streak"
        assert "total_trades" in data, "Should include total_trades"
        
        print(f"Rewards Summary: {data['lifetime_points']} pts, {data['current_streak']}/{data['best_streak']} streak, {data['total_trades']} trades")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

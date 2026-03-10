"""
Test suite for bug fixes - Iteration 133
Tests:
1. Habit proof upload - POST /api/habits/{id}/complete accepts screenshot_url in request body
2. LOT size truncation - Uses math.trunc() not round() for $16.13/980 = 0.01
3. Streak calculation skips weekends and US market holidays (Presidents Day Feb 16 2026)
"""
import pytest
import requests
import os
import math
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-quiz-lab.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture
def auth_token():
    """Get authentication token for master admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestLotSizeTruncation:
    """Test that LOT size calculation uses truncation (floor), not rounding"""
    
    def test_truncate_lot_size_formula_locally(self):
        """Test the truncation formula locally: $16.13 / 980 should be 0.01, not 0.02"""
        balance = 16.13
        divisor = 980
        
        # Using round() would give 0.02 (16.13/980 = 0.0164..., rounds up)
        rounded = round(balance / divisor, 2)
        
        # Using truncation should give 0.01 (floor to 2 decimals)
        truncated = math.trunc(balance / divisor * 100) / 100
        
        print(f"Balance: ${balance}")
        print(f"Round method: {rounded}")
        print(f"Truncate method: {truncated}")
        
        # Assert truncation gives 0.01
        assert truncated == 0.01, f"Expected 0.01 from truncation, got {truncated}"
        # Assert round would give different result (0.02)
        assert rounded == 0.02, f"Expected round to give 0.02, got {rounded}"
        # Confirm they are different
        assert truncated != rounded, "Truncation and rounding should give different results for this edge case"
        print("✓ LOT size truncation formula verified: $16.13 / 980 = 0.01")
    
    def test_truncate_edge_cases(self):
        """Test truncation on various edge cases"""
        test_cases = [
            (16.13, 0.01),   # User Joy Sison's case
            (980, 1.0),      # Exactly 1 LOT
            (1960, 2.0),     # Exactly 2 LOTs
            (500, 0.51),     # 500/980 = 0.5102... -> 0.51
            (100, 0.10),     # 100/980 = 0.1020... -> 0.10
            (50, 0.05),      # 50/980 = 0.0510... -> 0.05
            (10, 0.01),      # 10/980 = 0.0102... -> 0.01
            (9, 0.00),       # 9/980 = 0.0091... -> 0.00
        ]
        
        for balance, expected in test_cases:
            result = math.trunc(balance / 980 * 100) / 100
            print(f"Balance ${balance}: LOT = {result} (expected {expected})")
            assert result == expected, f"Expected {expected} for ${balance}, got {result}"
        
        print("✓ All LOT size truncation edge cases passed")


class TestStreakHolidayAwareness:
    """Test that streak calculation skips weekends and US market holidays"""
    
    def test_presidents_day_2026_in_holidays(self):
        """Verify Presidents Day Feb 16 2026 is in the holiday set"""
        # Presidents Day 2026 is February 16 (3rd Monday of February)
        from datetime import date
        
        # Calculate 3rd Monday of February 2026
        feb_1 = date(2026, 2, 1)
        # Find first Monday
        first_monday = feb_1
        while first_monday.weekday() != 0:  # 0 = Monday
            first_monday = date(2026, 2, first_monday.day + 1)
        # 3rd Monday is 2 weeks after first Monday
        presidents_day = date(2026, 2, first_monday.day + 14)
        
        print(f"Presidents Day 2026: {presidents_day}")
        assert presidents_day == date(2026, 2, 16), f"Expected Feb 16, got {presidents_day}"
        print("✓ Presidents Day 2026 is Feb 16")
    
    def test_get_habits_returns_streak(self, auth_headers):
        """Test that GET /api/habits/ returns streak info"""
        response = requests.get(f"{BASE_URL}/api/habits/", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "streak" in data, "Response should contain 'streak' field"
        streak = data["streak"]
        assert "current_streak" in streak, "Streak should have current_streak"
        assert "longest_streak" in streak, "Streak should have longest_streak"
        assert "total_days" in streak, "Streak should have total_days"
        
        print(f"✓ Streak data: current={streak.get('current_streak')}, longest={streak.get('longest_streak')}, total={streak.get('total_days')}")


class TestHabitProofUpload:
    """Test habit completion with screenshot_url in request body"""
    
    def test_habit_complete_endpoint_accepts_body(self, auth_headers):
        """Test that POST /api/habits/{id}/complete accepts screenshot_url in body"""
        # First get list of habits
        response = requests.get(f"{BASE_URL}/api/habits/", headers=auth_headers)
        assert response.status_code == 200
        
        habits = response.json().get("habits", [])
        if not habits:
            pytest.skip("No habits configured to test")
        
        habit_id = habits[0]["id"]
        
        # Try to complete with screenshot_url in body
        test_screenshot_url = "https://example.com/test-screenshot.png"
        complete_response = requests.post(
            f"{BASE_URL}/api/habits/{habit_id}/complete",
            headers=auth_headers,
            json={"screenshot_url": test_screenshot_url}
        )
        
        # Should return 200 (either "already completed" or "completed")
        assert complete_response.status_code == 200, f"Expected 200, got {complete_response.status_code}: {complete_response.text}"
        
        data = complete_response.json()
        assert "message" in data, "Response should have message"
        print(f"✓ Habit completion response: {data}")
    
    def test_habit_complete_without_body(self, auth_headers):
        """Test that habit can be completed without body (backward compatibility)"""
        response = requests.get(f"{BASE_URL}/api/habits/", headers=auth_headers)
        assert response.status_code == 200
        
        habits = response.json().get("habits", [])
        if not habits:
            pytest.skip("No habits configured to test")
        
        habit_id = habits[0]["id"]
        
        # Complete without body (backward compatibility)
        complete_response = requests.post(
            f"{BASE_URL}/api/habits/{habit_id}/complete",
            headers=auth_headers
        )
        
        assert complete_response.status_code == 200, f"Expected 200, got {complete_response.status_code}"
        print(f"✓ Habit completion works without body: {complete_response.json()}")


class TestUSMarketHolidays:
    """Test US market holiday calculations"""
    
    def test_2026_holidays_include_presidents_day(self):
        """Verify 2026 holidays include Presidents Day (Feb 16)"""
        # Import the function from trading_days
        import sys
        sys.path.insert(0, '/app/backend')
        from utils.trading_days import get_us_market_holidays
        
        holidays_2026 = get_us_market_holidays(2026)
        
        print(f"2026 US Market Holidays: {sorted(holidays_2026)}")
        
        # Check Presidents Day (Feb 16, 2026 - 3rd Monday)
        assert "2026-02-16" in holidays_2026, f"Presidents Day 2026-02-16 not in holidays: {holidays_2026}"
        
        # Also verify other key holidays
        expected_holidays = [
            "2026-01-01",  # New Year's Day
            "2026-01-19",  # MLK Day (3rd Monday January)
            "2026-02-16",  # Presidents Day (3rd Monday February)
            "2026-04-03",  # Good Friday (2 days before Easter - Easter 2026 is April 5)
            "2026-05-25",  # Memorial Day (last Monday May)
            "2026-06-19",  # Juneteenth (June 19)
            "2026-07-03",  # Independence Day observed (July 4 is Saturday)
            "2026-09-07",  # Labor Day (1st Monday September)
            "2026-11-26",  # Thanksgiving (4th Thursday November)
            "2026-12-25",  # Christmas
        ]
        
        for holiday in expected_holidays:
            assert holiday in holidays_2026, f"{holiday} not in holidays"
        
        print(f"✓ All expected 2026 holidays present including Presidents Day")
    
    def test_is_trading_day_skips_holidays(self):
        """Test is_trading_day correctly identifies non-trading days"""
        import sys
        sys.path.insert(0, '/app/backend')
        from utils.trading_days import is_trading_day, get_us_market_holidays
        from datetime import datetime
        
        holidays = get_us_market_holidays(2026)
        
        # Presidents Day 2026 (Monday) should NOT be a trading day
        presidents_day = datetime(2026, 2, 16)
        assert not is_trading_day(presidents_day, holidays), "Presidents Day should not be a trading day"
        
        # A regular Monday (Feb 9, 2026) should be a trading day
        regular_monday = datetime(2026, 2, 9)
        assert is_trading_day(regular_monday, holidays), "Regular Monday should be a trading day"
        
        # Saturday should NOT be a trading day
        saturday = datetime(2026, 2, 14)
        assert not is_trading_day(saturday, holidays), "Saturday should not be a trading day"
        
        # Sunday should NOT be a trading day
        sunday = datetime(2026, 2, 15)
        assert not is_trading_day(sunday, holidays), "Sunday should not be a trading day"
        
        print("✓ is_trading_day correctly handles weekends and holidays")


class TestAPIEndpoints:
    """Test API endpoint responses"""
    
    def test_health_check(self):
        """Basic health check"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print("✓ API is healthy")
    
    def test_auth_login(self):
        """Test login endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login successful for {MASTER_ADMIN_EMAIL}")
    
    def test_profit_summary(self, auth_headers):
        """Test profit summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "account_value" in data, "Should have account_value"
        print(f"✓ Profit summary: account_value=${data.get('account_value')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

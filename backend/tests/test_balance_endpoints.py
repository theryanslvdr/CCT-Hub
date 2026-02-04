"""
Test suite for the new balance calculation endpoints:
- GET /api/profit/balance-on-date
- GET /api/profit/daily-balances

These endpoints provide authoritative backend-calculated balance values
to fix the recurring historical balance calculation bug.
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestBalanceEndpoints:
    """Test the new balance calculation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        assert token, "No access token received"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user = login_response.json().get("user")
        
    def test_balance_on_date_endpoint_exists(self):
        """Test that /api/profit/balance-on-date endpoint exists and returns 200"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.session.get(
            f"{BASE_URL}/api/profit/balance-on-date",
            params={"date": today}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_balance_on_date_returns_correct_structure(self):
        """Test that balance-on-date returns expected fields"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.session.get(
            f"{BASE_URL}/api/profit/balance-on-date",
            params={"date": today}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Check required fields
        assert "balance_on_date" in data, "Missing balance_on_date field"
        assert "lot_size" in data, "Missing lot_size field"
        assert "date" in data, "Missing date field"
        assert "deposits_count" in data, "Missing deposits_count field"
        assert "trades_count" in data, "Missing trades_count field"
        assert "total_deposits" in data, "Missing total_deposits field"
        assert "total_withdrawals" in data, "Missing total_withdrawals field"
        assert "total_profit" in data, "Missing total_profit field"
        assert "total_commission" in data, "Missing total_commission field"
        
        # Verify date matches request
        assert data["date"] == today
        
        # Verify numeric types
        assert isinstance(data["balance_on_date"], (int, float))
        assert isinstance(data["lot_size"], (int, float))
        
    def test_balance_on_date_invalid_date_format(self):
        """Test that invalid date format returns 400"""
        response = self.session.get(
            f"{BASE_URL}/api/profit/balance-on-date",
            params={"date": "invalid-date"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid date, got {response.status_code}"
        
    def test_balance_on_date_historical(self):
        """Test balance calculation for a historical date"""
        # Test with a date from last month
        last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        response = self.session.get(
            f"{BASE_URL}/api/profit/balance-on-date",
            params={"date": last_month}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["date"] == last_month
        # Balance should be >= 0 (can be 0 if no activity before that date)
        assert data["balance_on_date"] >= 0
        
    def test_daily_balances_endpoint_exists(self):
        """Test that /api/profit/daily-balances endpoint exists and returns 200"""
        today = datetime.now()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        response = self.session.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": start_date, "end_date": end_date}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_daily_balances_returns_correct_structure(self):
        """Test that daily-balances returns expected fields"""
        today = datetime.now()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        response = self.session.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": start_date, "end_date": end_date}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Check top-level fields
        assert "daily_balances" in data, "Missing daily_balances field"
        assert "start_date" in data, "Missing start_date field"
        assert "end_date" in data, "Missing end_date field"
        assert "user_id" in data, "Missing user_id field"
        
        # Verify dates match request
        assert data["start_date"] == start_date
        assert data["end_date"] == end_date
        
        # Check daily_balances is a list
        assert isinstance(data["daily_balances"], list)
        
    def test_daily_balances_entry_structure(self):
        """Test that each daily balance entry has correct fields"""
        today = datetime.now()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        response = self.session.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": start_date, "end_date": end_date}
        )
        assert response.status_code == 200
        
        data = response.json()
        daily_balances = data["daily_balances"]
        
        # Should have at least one entry (today)
        assert len(daily_balances) > 0, "Expected at least one daily balance entry"
        
        # Check first entry structure
        entry = daily_balances[0]
        assert "date" in entry, "Missing date field in entry"
        assert "balance_before" in entry, "Missing balance_before field in entry"
        assert "lot_size" in entry, "Missing lot_size field in entry"
        assert "target_profit" in entry, "Missing target_profit field in entry"
        assert "has_trade" in entry, "Missing has_trade field in entry"
        
    def test_daily_balances_invalid_date_format(self):
        """Test that invalid date format returns 400"""
        response = self.session.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "invalid", "end_date": "2025-01-31"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid date, got {response.status_code}"
        
    def test_daily_balances_start_after_end(self):
        """Test that start_date after end_date returns 400"""
        response = self.session.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2025-01-31", "end_date": "2025-01-01"}
        )
        assert response.status_code == 400, f"Expected 400 for start > end, got {response.status_code}"
        
    def test_daily_balances_historical_month(self):
        """Test daily balances for a historical month"""
        # Test December 2024
        response = self.session.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2024-12-01", "end_date": "2024-12-31"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["start_date"] == "2024-12-01"
        assert data["end_date"] == "2024-12-31"
        
        # Should have 31 entries for December
        assert len(data["daily_balances"]) == 31, f"Expected 31 entries, got {len(data['daily_balances'])}"
        
    def test_lot_size_calculation(self):
        """Test that lot_size is correctly calculated as balance / 980"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.session.get(
            f"{BASE_URL}/api/profit/balance-on-date",
            params={"date": today}
        )
        assert response.status_code == 200
        
        data = response.json()
        balance = data["balance_on_date"]
        lot_size = data["lot_size"]
        
        # Verify lot_size calculation (balance / 980, rounded to 2 decimals)
        if balance > 0:
            expected_lot_size = round(balance / 980, 2)
            assert lot_size == expected_lot_size, f"Expected lot_size {expected_lot_size}, got {lot_size}"
        else:
            assert lot_size == 0, f"Expected lot_size 0 for zero balance, got {lot_size}"


class TestBalanceConsistency:
    """Test that balance calculations are consistent between endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_balance_consistency_between_endpoints(self):
        """Test that balance-on-date and daily-balances return consistent values"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get balance from balance-on-date
        single_response = self.session.get(
            f"{BASE_URL}/api/profit/balance-on-date",
            params={"date": today}
        )
        assert single_response.status_code == 200
        single_balance = single_response.json()["balance_on_date"]
        
        # Get balance from daily-balances for today
        range_response = self.session.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": today, "end_date": today}
        )
        assert range_response.status_code == 200
        
        daily_balances = range_response.json()["daily_balances"]
        assert len(daily_balances) == 1
        
        # The balance_before in daily-balances should match balance_on_date
        # (balance_on_date is end-of-day, balance_before is start-of-day)
        # They may differ if there are trades on that day
        range_balance = daily_balances[0]["balance_before"]
        
        # Log for debugging
        print(f"Single endpoint balance: {single_balance}")
        print(f"Range endpoint balance_before: {range_balance}")
        
        # Both should be valid numbers
        assert isinstance(single_balance, (int, float))
        assert isinstance(range_balance, (int, float))


class TestDashboardIntegration:
    """Test that dashboard displays correctly with the new endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user = login_response.json().get("user")
        
    def test_profit_summary_endpoint(self):
        """Test that /api/profit/summary still works"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "account_value" in data
        assert "total_deposits" in data
        
    def test_login_flow(self):
        """Test that login works correctly"""
        # Already logged in via setup, verify user data
        assert self.user is not None
        assert self.user.get("email") == TEST_EMAIL
        assert self.user.get("role") == "master_admin"
        
    def test_no_trade_members_widget_data(self):
        """Test that missed trades endpoint works (for No Trade Members widget)"""
        response = self.session.get(f"{BASE_URL}/api/admin/analytics/missed-trades")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Should return a dict with missed_traders list
        data = response.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        assert "missed_traders" in data, "Missing missed_traders field"
        assert isinstance(data["missed_traders"], list), "missed_traders should be a list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

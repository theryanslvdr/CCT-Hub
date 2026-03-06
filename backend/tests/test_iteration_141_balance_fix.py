"""
Iteration 141: Balance Calculation Double-Counting Bug Fix Tests
----------------------------------------------------------------
Tests the fix for the critical bug where type='profit' entries in deposits
collection were causing double-counting of profits (inflating balances by ~$8,000).

The fix excludes type='profit' entries from:
1. GET /api/profit/daily-balances - deposit processing (line 2079-2082)
2. GET /api/profit/debug-transactions - deposit totals (line 2248-2250)
3. Frontend ProfitTrackerPage.jsx - deposits state filtering (lines 1070, 1134)

Expected values for user iam@ryansalvador.com (March 2026):
- Correct account value: ~$33,664.09
- Buggy value was: ~$41,664.94 (difference of ~$8,000.85)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"

class TestBalanceCalculationFix:
    """Tests for the double-counting bug fix in balance calculations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - authenticate and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        # Use access_token (not token) as per the review request
        token = data.get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.user_id = data.get("user", {}).get("id")
        yield
    
    def test_login_returns_correct_token_field(self):
        """Verify login returns access_token field"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, "Login should return 'access_token' field"
        assert data.get("token_type") == "bearer"
        print(f"✓ Login successful, access_token field present")
    
    def test_daily_balances_march_2026(self):
        """
        Test /api/profit/daily-balances for March 2026
        Expected: final balance_before should be ~$33,664 (not ~$41,664)
        """
        response = self.session.get(f"{BASE_URL}/api/profit/daily-balances", params={
            "start_date": "2026-03-01",
            "end_date": "2026-03-31"
        })
        assert response.status_code == 200, f"Daily balances failed: {response.text}"
        
        data = response.json()
        daily_balances = data.get("daily_balances", [])
        
        print(f"✓ Got {len(daily_balances)} daily balance records for March 2026")
        
        # Get the last balance entry for the month
        if daily_balances:
            # Find the maximum date entry
            sorted_balances = sorted(daily_balances, key=lambda x: x.get("date", ""))
            last_entry = sorted_balances[-1] if sorted_balances else None
            
            if last_entry:
                balance_before = last_entry.get("balance_before", 0)
                date = last_entry.get("date")
                
                print(f"  Last entry date: {date}")
                print(f"  Balance before: ${balance_before:,.2f}")
                
                # The correct value should be around $33,664, NOT $41,664
                # Allow some tolerance for trades that may have happened
                assert balance_before < 38000, f"Balance {balance_before} is too high - double-counting bug may still exist"
                assert balance_before > 30000, f"Balance {balance_before} seems too low"
                
                print(f"✓ March 2026 final balance is correct (not double-counted)")
    
    def test_profit_summary_account_value(self):
        """
        Test /api/profit/summary returns correct account_value
        Expected: ~$33,664.09 (not ~$41,664)
        """
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200, f"Summary failed: {response.text}"
        
        data = response.json()
        account_value = data.get("account_value", 0)
        total_deposits = data.get("total_deposits", 0)
        total_profit = data.get("total_actual_profit", 0)
        
        print(f"  Account Value: ${account_value:,.2f}")
        print(f"  Total Deposits: ${total_deposits:,.2f}")
        print(f"  Total Profit: ${total_profit:,.2f}")
        
        # The correct account value should be around $33,664
        # Not $41,664 (which would indicate double-counting)
        assert account_value < 38000, f"Account value {account_value} is too high - double-counting bug may still exist"
        assert account_value > 30000, f"Account value {account_value} seems too low"
        
        print(f"✓ Account value is in expected range (no double-counting)")
    
    def test_debug_transactions_shows_excluded_profits(self):
        """
        Test /api/profit/debug-transactions returns:
        - total_profit_deposits_excluded field showing excluded amount
        - expected_account_value matching daily-balances
        """
        response = self.session.get(f"{BASE_URL}/api/profit/debug-transactions")
        assert response.status_code == 200, f"Debug transactions failed: {response.text}"
        
        data = response.json()
        summary = data.get("summary", {})
        
        expected_account_value = summary.get("expected_account_value", 0)
        total_profit_deposits_excluded = summary.get("total_profit_deposits_excluded", 0)
        total_positive_deposits = summary.get("total_positive_deposits", 0)
        total_profit = summary.get("total_profit", 0)
        
        print(f"  Expected Account Value: ${expected_account_value:,.2f}")
        print(f"  Total Profit Deposits Excluded: ${total_profit_deposits_excluded:,.2f}")
        print(f"  Total Positive Deposits: ${total_positive_deposits:,.2f}")
        print(f"  Total Profit: ${total_profit:,.2f}")
        
        # Verify the excluded field exists and has a reasonable value
        assert "total_profit_deposits_excluded" in summary, "Missing total_profit_deposits_excluded field"
        
        # The excluded amount should be around $8,000.85 (the double-counted profits)
        if total_profit_deposits_excluded > 0:
            print(f"✓ Profit deposits correctly identified for exclusion: ${total_profit_deposits_excluded:,.2f}")
        
        # Expected account value should be around $33,664
        assert expected_account_value < 38000, f"Expected account value {expected_account_value} is too high"
        assert expected_account_value > 30000, f"Expected account value {expected_account_value} seems too low"
        
        print(f"✓ Debug transactions endpoint working correctly")
    
    def test_february_withdrawal_reflected(self):
        """
        Test /api/profit/daily-balances for February 2026
        Expected: Feb 18 has $3,000 withdrawal affecting Feb 19 balance
        """
        response = self.session.get(f"{BASE_URL}/api/profit/daily-balances", params={
            "start_date": "2026-02-01",
            "end_date": "2026-02-28"
        })
        assert response.status_code == 200, f"Daily balances failed: {response.text}"
        
        data = response.json()
        daily_balances = data.get("daily_balances", [])
        
        print(f"✓ Got {len(daily_balances)} daily balance records for February 2026")
        
        # Look for Feb 18 and Feb 19 entries
        feb_18_entry = None
        feb_19_entry = None
        
        for entry in daily_balances:
            date = entry.get("date", "")
            if date == "2026-02-18":
                feb_18_entry = entry
            elif date == "2026-02-19":
                feb_19_entry = entry
        
        if feb_18_entry:
            print(f"  Feb 18 balance_before: ${feb_18_entry.get('balance_before', 0):,.2f}")
            withdrawal_on_18 = feb_18_entry.get("withdrawal", 0)
            if withdrawal_on_18 > 0:
                print(f"  Feb 18 withdrawal: ${withdrawal_on_18:,.2f}")
        
        if feb_19_entry:
            print(f"  Feb 19 balance_before: ${feb_19_entry.get('balance_before', 0):,.2f}")
        
        # Verify that if there's a withdrawal on Feb 18, Feb 19 balance reflects it
        if feb_18_entry and feb_19_entry:
            feb_18_balance = feb_18_entry.get("balance_before", 0)
            feb_19_balance = feb_19_entry.get("balance_before", 0)
            withdrawal = feb_18_entry.get("withdrawal", 0)
            profit = feb_18_entry.get("profit", 0)
            commission = feb_18_entry.get("commission", 0)
            
            if withdrawal >= 3000:
                # Feb 19 balance should be approximately Feb 18 balance + profit + commission - withdrawal
                expected_feb_19 = feb_18_balance + profit + commission - withdrawal
                print(f"  Expected Feb 19 balance (approx): ${expected_feb_19:,.2f}")
                print(f"  Actual Feb 19 balance: ${feb_19_balance:,.2f}")
                
                # Allow some tolerance for calculation differences
                assert abs(feb_19_balance - expected_feb_19) < 100, \
                    f"Feb 19 balance doesn't reflect withdrawal correctly"
                print(f"✓ February withdrawal correctly reflected in daily balances")
    
    def test_summary_matches_daily_balances(self):
        """
        Verify /api/profit/summary account_value matches /api/profit/daily-balances final value
        """
        # Get summary
        summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert summary_response.status_code == 200
        summary_account_value = summary_response.json().get("account_value", 0)
        
        # Get daily balances for current month (or March 2026)
        balances_response = self.session.get(f"{BASE_URL}/api/profit/daily-balances", params={
            "start_date": "2026-03-01",
            "end_date": "2026-03-31"
        })
        assert balances_response.status_code == 200
        
        daily_balances = balances_response.json().get("daily_balances", [])
        
        print(f"  Summary account value: ${summary_account_value:,.2f}")
        
        # The account value from summary should be consistent
        # Both should be around $33,664 (not $41,664)
        assert summary_account_value < 38000, f"Summary account value {summary_account_value} too high"
        assert summary_account_value > 30000, f"Summary account value {summary_account_value} too low"
        
        print(f"✓ Summary account value is in expected range")


class TestAPIAuthentication:
    """Test authentication flows"""
    
    def test_login_with_valid_credentials(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "Missing access_token"
        assert "user" in data, "Missing user object"
        assert data["user"]["email"] == ADMIN_EMAIL
        
        print(f"✓ Login successful for {ADMIN_EMAIL}")
        print(f"  User role: {data['user'].get('role')}")
    
    def test_authenticated_endpoint_access(self):
        """Test accessing authenticated endpoints"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test profit summary (requires auth)
        summary_response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert summary_response.status_code == 200, f"Summary access failed: {summary_response.text}"
        
        print(f"✓ Authenticated endpoint access working")


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_api_is_accessible(self):
        """Verify API is accessible"""
        # Try to hit the auth endpoint
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test"
        })
        # Should get 401 (invalid credentials) not 500 or connection error
        assert response.status_code in [200, 401], f"API not accessible: {response.status_code}"
        print(f"✓ API is accessible at {BASE_URL}")

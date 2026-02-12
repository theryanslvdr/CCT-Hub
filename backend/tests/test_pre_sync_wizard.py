"""
Tests for Pre-Sync Validation Wizard feature
Testing: GET /api/profit/sync-validation, POST /api/profit/set-trading-start-date, POST /api/profit/balance-override
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestSyncValidationEndpoint:
    """Tests for GET /api/profit/sync-validation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    def test_sync_validation_returns_200(self):
        """Test GET /api/profit/sync-validation returns 200 OK"""
        response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: sync-validation returns 200")
    
    def test_sync_validation_response_structure(self):
        """Test sync-validation response has required fields"""
        response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "can_sync" in data, "Missing 'can_sync' field"
        assert "issues" in data, "Missing 'issues' field"
        assert "trading_start_date" in data, "Missing 'trading_start_date' field"
        assert "missing_trade_days" in data, "Missing 'missing_trade_days' field"
        assert "pre_start_trades" in data, "Missing 'pre_start_trades' field"
        assert "summary" in data, "Missing 'summary' field"
        
        print(f"SUCCESS: Response has all required fields")
        print(f"  can_sync: {data['can_sync']}")
        print(f"  trading_start_date: {data['trading_start_date']}")
        print(f"  missing_trade_days count: {len(data['missing_trade_days'])}")
        print(f"  pre_start_trades count: {len(data['pre_start_trades'])}")
    
    def test_sync_validation_summary_structure(self):
        """Test sync-validation summary has required fields"""
        response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        
        # Check summary fields
        assert "total_trading_days" in summary, "Missing 'total_trading_days' in summary"
        assert "reported_days" in summary, "Missing 'reported_days' in summary"
        assert "missing_days" in summary, "Missing 'missing_days' in summary"
        assert "pre_start_trade_count" in summary, "Missing 'pre_start_trade_count' in summary"
        
        print(f"SUCCESS: Summary has all required fields")
        print(f"  total_trading_days: {summary['total_trading_days']}")
        print(f"  reported_days: {summary['reported_days']}")
        print(f"  missing_days: {summary['missing_days']}")
        print(f"  pre_start_trade_count: {summary['pre_start_trade_count']}")
    
    def test_sync_validation_issues_array(self):
        """Test sync-validation issues is an array with proper structure"""
        response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        
        assert response.status_code == 200
        data = response.json()
        
        issues = data.get("issues", [])
        assert isinstance(issues, list), "'issues' should be an array"
        
        # If there are issues, check their structure
        for issue in issues:
            assert "type" in issue, "Issue missing 'type' field"
            assert "severity" in issue, "Issue missing 'severity' field"
            assert "message" in issue, "Issue missing 'message' field"
        
        print(f"SUCCESS: Issues array has correct structure ({len(issues)} issues)")
    
    def test_sync_validation_missing_trade_days_structure(self):
        """Test missing_trade_days array structure"""
        response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        
        assert response.status_code == 200
        data = response.json()
        
        missing_days = data.get("missing_trade_days", [])
        assert isinstance(missing_days, list), "'missing_trade_days' should be an array"
        
        # If there are missing days, check their structure
        for day in missing_days:
            assert "date" in day, "Missing day should have 'date' field"
            assert "status" in day, "Missing day should have 'status' field"
            # status should be 'no_entry' or 'incomplete'
            assert day["status"] in ["no_entry", "incomplete"], f"Invalid status: {day['status']}"
        
        print(f"SUCCESS: missing_trade_days has correct structure ({len(missing_days)} days)")
        if missing_days:
            print(f"  First missing day: {missing_days[0]['date']} ({missing_days[0]['status']})")


class TestSetTradingStartDateEndpoint:
    """Tests for POST /api/profit/set-trading-start-date endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    def test_set_trading_start_date_returns_200(self):
        """Test POST /api/profit/set-trading-start-date returns 200"""
        # First get current date from validation
        validation_response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        current_date = validation_response.json().get("trading_start_date", "2026-02-01")
        
        # Set the same date (to avoid changing state)
        response = self.session.post(
            f"{BASE_URL}/api/profit/set-trading-start-date",
            json={"trading_start_date": current_date}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"SUCCESS: set-trading-start-date returns 200")
        print(f"  Set date: {current_date}")
    
    def test_set_trading_start_date_invalid_format(self):
        """Test invalid date format returns 400"""
        response = self.session.post(
            f"{BASE_URL}/api/profit/set-trading-start-date",
            json={"trading_start_date": "not-a-date"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"SUCCESS: Invalid date format correctly rejected with 400")
    
    def test_set_trading_start_date_updates_validation(self):
        """Test that setting start date updates the validation response"""
        # Get current state
        validation_before = self.session.get(f"{BASE_URL}/api/profit/sync-validation").json()
        current_date = validation_before.get("trading_start_date")
        
        if current_date:
            # Set same date
            self.session.post(
                f"{BASE_URL}/api/profit/set-trading-start-date",
                json={"trading_start_date": current_date}
            )
            
            # Verify it's still set
            validation_after = self.session.get(f"{BASE_URL}/api/profit/sync-validation").json()
            assert validation_after["trading_start_date"] == current_date
            print(f"SUCCESS: Trading start date correctly persisted: {current_date}")
        else:
            print("SKIP: No trading start date set, cannot test persistence without changing state")


class TestBalanceOverrideEndpoint:
    """Tests for POST /api/profit/balance-override endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    def test_get_balance_override_returns_200(self):
        """Test GET /api/profit/balance-override returns 200"""
        response = self.session.get(f"{BASE_URL}/api/profit/balance-override")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "has_override" in data, "Missing 'has_override' field"
        print(f"SUCCESS: balance-override returns 200")
        print(f"  has_override: {data['has_override']}")
    
    def test_create_balance_override_returns_200(self):
        """Test POST /api/profit/balance-override returns 200"""
        # Get current summary to find reasonable balance value
        summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
        current_balance = summary_response.json().get("account_value", 10000)
        
        response = self.session.post(
            f"{BASE_URL}/api/profit/balance-override",
            json={
                "actual_balance": current_balance,
                "reason": "Test balance sync from pytest"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "message" in data, "Missing 'message' field"
        assert "override" in data, "Missing 'override' field"
        
        override = data["override"]
        assert "id" in override, "Override missing 'id'"
        assert "actual_balance" in override, "Override missing 'actual_balance'"
        assert "calculated_balance" in override, "Override missing 'calculated_balance'"
        assert "adjustment_amount" in override, "Override missing 'adjustment_amount'"
        
        print(f"SUCCESS: balance-override POST returns 200")
        print(f"  Override ID: {override['id']}")
        print(f"  Actual balance: {override['actual_balance']}")
        print(f"  Calculated balance: {override['calculated_balance']}")
        print(f"  Adjustment: {override['adjustment_amount']}")


class TestDidNotTradeEndpoint:
    """Tests for POST /api/trade/did-not-trade endpoint (used by wizard)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    def test_did_not_trade_endpoint_exists(self):
        """Test POST /api/trade/did-not-trade endpoint exists"""
        # Get a missing day from validation
        validation_response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        validation = validation_response.json()
        
        missing_days = validation.get("missing_trade_days", [])
        
        if not missing_days:
            print("SKIP: No missing days to test with")
            return
        
        test_date = missing_days[0]["date"]
        
        response = self.session.post(
            f"{BASE_URL}/api/trade/did-not-trade",
            params={"trade_date": test_date}
        )
        
        # Should be 200 or 400 (if already marked), but not 404
        assert response.status_code != 404, f"Endpoint not found: {response.text}"
        print(f"SUCCESS: did-not-trade endpoint exists")
        print(f"  Status: {response.status_code}")


class TestIntegrationFlow:
    """Integration tests for the complete wizard flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    def test_full_validation_flow(self):
        """Test the complete validation flow"""
        # Step 1: Get validation status
        validation_response = self.session.get(f"{BASE_URL}/api/profit/sync-validation")
        assert validation_response.status_code == 200
        validation = validation_response.json()
        
        print(f"Validation response:")
        print(f"  can_sync: {validation['can_sync']}")
        print(f"  trading_start_date: {validation['trading_start_date']}")
        print(f"  missing_trade_days: {len(validation['missing_trade_days'])}")
        print(f"  pre_start_trades: {len(validation['pre_start_trades'])}")
        
        # Step 2: If start date is set, verify summary is populated
        if validation['trading_start_date']:
            summary = validation['summary']
            assert summary['total_trading_days'] >= 0
            assert summary['reported_days'] >= 0
            print(f"  Summary OK - {summary['reported_days']}/{summary['total_trading_days']} days reported")
        
        print("SUCCESS: Full validation flow works correctly")
    
    def test_login_returns_correct_token_format(self):
        """Test login returns access_token (not token)"""
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        assert login_response.status_code == 200
        data = login_response.json()
        
        # Should have access_token, not token
        assert "access_token" in data, "Login should return 'access_token'"
        assert "user" in data, "Login should return 'user' object"
        
        print("SUCCESS: Login returns access_token correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

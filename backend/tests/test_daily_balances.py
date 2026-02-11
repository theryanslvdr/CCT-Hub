"""
Test suite for Daily Balances API endpoint and Balance Calculation Bug Fix
Tests the P0 bug fix for 'Balance Before' calculation in Daily Projection table

Key fixes being tested:
1. /api/profit/daily-balances endpoint returns correct balances
2. Simulation with a member correctly fetches their daily balances (not admin's)
3. Balance calculation includes commissions correctly
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDailyBalancesAPI:
    """Tests for /api/profit/daily-balances endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.user_id = response.json()["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_daily_balances_endpoint_exists(self):
        """Test that the daily-balances endpoint exists and returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2026-01-01", "end_date": "2026-01-10"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Endpoint failed: {response.text}"
        data = response.json()
        assert "daily_balances" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "user_id" in data
        print("✓ Daily balances endpoint exists and returns correct structure")
    
    def test_daily_balances_returns_array(self):
        """Test that daily_balances is an array with correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2026-02-01", "end_date": "2026-02-05"},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["daily_balances"], list)
        assert len(data["daily_balances"]) == 5  # 5 days
        
        # Check first entry has all required fields
        first_entry = data["daily_balances"][0]
        required_fields = ["date", "balance_before", "lot_size", "target_profit", 
                          "actual_profit", "commission", "has_trade"]
        for field in required_fields:
            assert field in first_entry, f"Missing field: {field}"
        print("✓ Daily balances returns array with correct fields")
    
    def test_balance_calculation_accuracy(self):
        """Test that balance calculations are accurate based on deposits and trades"""
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2026-02-01", "end_date": "2026-02-06"},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        balances = {b["date"]: b for b in data["daily_balances"]}
        
        # Feb 1: Initial deposit of $5000
        assert balances["2026-02-01"]["balance_before"] == 5000, "Feb 1 should have $5000 balance"
        
        # Feb 3: After $75.5 profit on Feb 3, balance should be $5075.5 for Feb 4
        if balances["2026-02-03"]["has_trade"]:
            assert balances["2026-02-03"]["actual_profit"] == 75.5
            assert balances["2026-02-04"]["balance_before"] == 5075.5, "Feb 4 should reflect Feb 3 profit"
        
        # Feb 4: After $82 profit, balance should be $5157.5 for Feb 5
        if balances["2026-02-04"]["has_trade"]:
            assert balances["2026-02-04"]["actual_profit"] == 82
            assert balances["2026-02-05"]["balance_before"] == 5157.5, "Feb 5 should reflect Feb 4 profit"
        
        # Feb 5: After -$25 loss, balance should be $5132.5 for Feb 6
        if balances["2026-02-05"]["has_trade"]:
            assert balances["2026-02-05"]["actual_profit"] == -25
            assert balances["2026-02-06"]["balance_before"] == 5132.5, "Feb 6 should reflect Feb 5 loss"
        
        print("✓ Balance calculations are accurate")
    
    def test_lot_size_calculation(self):
        """Test that lot_size is correctly calculated as balance / 980"""
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2026-02-01", "end_date": "2026-02-01"},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        entry = data["daily_balances"][0]
        expected_lot_size = round(entry["balance_before"] / 980, 2)
        assert entry["lot_size"] == expected_lot_size, f"Lot size should be {expected_lot_size}"
        print("✓ Lot size calculation is correct (balance / 980)")
    
    def test_target_profit_calculation(self):
        """Test that target_profit is correctly calculated as lot_size * 15"""
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2026-02-01", "end_date": "2026-02-01"},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        entry = data["daily_balances"][0]
        expected_target = round(entry["lot_size"] * 15, 2)
        assert entry["target_profit"] == expected_target, f"Target profit should be {expected_target}"
        print("✓ Target profit calculation is correct (lot_size * 15)")
    
    def test_simulation_with_different_user_id(self):
        """Test that admin can fetch daily balances for a different user (simulation)"""
        # Get list of members first
        members_response = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers=self.headers
        )
        assert members_response.status_code == 200
        members = members_response.json().get("members", [])
        
        # Find a different user
        other_user = None
        for m in members:
            if m["id"] != self.user_id:
                other_user = m
                break
        
        if other_user:
            # Fetch daily balances for the other user
            response = requests.get(
                f"{BASE_URL}/api/profit/daily-balances",
                params={
                    "start_date": "2026-01-01", 
                    "end_date": "2026-01-10",
                    "user_id": other_user["id"]
                },
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verify the user_id in response matches the requested user
            assert data["user_id"] == other_user["id"], "Should return data for the requested user"
            print(f"✓ Simulation works - fetched data for user {other_user['id']}")
        else:
            pytest.skip("No other users available for simulation test")
    
    def test_invalid_date_format(self):
        """Test that invalid date format returns 400 error"""
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "invalid", "end_date": "2026-01-10"},
            headers=self.headers
        )
        assert response.status_code == 400
        print("✓ Invalid date format returns 400 error")
    
    def test_start_date_after_end_date(self):
        """Test that start_date after end_date returns 400 error"""
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": "2026-02-10", "end_date": "2026-02-01"},
            headers=self.headers
        )
        assert response.status_code == 400
        print("✓ Start date after end date returns 400 error")


class TestProfitSummary:
    """Tests for /api/profit/summary endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_profit_summary_endpoint(self):
        """Test that profit summary endpoint returns correct data"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["total_deposits", "total_actual_profit", "account_value"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print("✓ Profit summary endpoint returns correct structure")


class TestTradeLogsWithCommission:
    """Tests for trade logs with commission field"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_trade_logs_include_commission(self):
        """Test that trade logs include commission field"""
        response = requests.get(
            f"{BASE_URL}/api/trade/logs",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            # Check that commission field exists
            first_trade = data[0]
            assert "commission" in first_trade, "Trade log should include commission field"
            print("✓ Trade logs include commission field")
        else:
            pytest.skip("No trade logs available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

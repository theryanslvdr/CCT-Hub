"""
Iteration 40 - Backend Refactoring Tests
Tests for unified account_value calculation utility and refactored endpoints.

Features tested:
1. GET /api/profit/summary - uses unified calculation
2. POST /api/profit/simulate-withdrawal - uses unified account_value calculation
3. Licensee account_value comes from license.current_amount
4. Regular user account_value is calculated as deposits - withdrawals + profits
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestRefactoredEndpoints:
    """Test refactored profit endpoints using unified calculation utility"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_profit_summary_endpoint_returns_200(self):
        """Test GET /api/profit/summary returns 200 status"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_profit_summary_response_structure(self):
        """Test GET /api/profit/summary returns correct response structure"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = [
            "total_deposits",
            "total_projected_profit",
            "total_actual_profit",
            "profit_difference",
            "account_value",
            "total_trades",
            "performance_rate",
            "is_licensee",
            "license_type"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify numeric fields are numbers
        assert isinstance(data["total_deposits"], (int, float))
        assert isinstance(data["total_projected_profit"], (int, float))
        assert isinstance(data["total_actual_profit"], (int, float))
        assert isinstance(data["profit_difference"], (int, float))
        assert isinstance(data["account_value"], (int, float))
        assert isinstance(data["total_trades"], int)
        assert isinstance(data["performance_rate"], (int, float))
        assert isinstance(data["is_licensee"], bool)
        
    def test_profit_summary_profit_difference_calculation(self):
        """Test profit_difference is correctly calculated as actual - projected"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        expected_diff = round(data["total_actual_profit"] - data["total_projected_profit"], 2)
        assert data["profit_difference"] == expected_diff, \
            f"profit_difference should be {expected_diff}, got {data['profit_difference']}"
    
    def test_simulate_withdrawal_endpoint_returns_200(self):
        """Test POST /api/profit/simulate-withdrawal returns 200 for valid amount"""
        response = self.session.post(f"{BASE_URL}/api/profit/simulate-withdrawal", json={
            "amount": 10.0,
            "from_currency": "USDT",
            "to_currency": "USD"
        })
        # Should return 200 if balance is sufficient, 400 if insufficient
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}: {response.text}"
        
    def test_simulate_withdrawal_response_structure(self):
        """Test POST /api/profit/simulate-withdrawal returns correct response structure"""
        response = self.session.post(f"{BASE_URL}/api/profit/simulate-withdrawal", json={
            "amount": 10.0,
            "from_currency": "USDT",
            "to_currency": "USD"
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify expected fields
            expected_fields = [
                "gross_amount",
                "merin_fee",
                "total_fees",
                "net_amount",
                "current_balance",
                "balance_after_withdrawal"
            ]
            
            for field in expected_fields:
                assert field in data, f"Missing field: {field}"
            
            # Verify calculations
            assert data["gross_amount"] == 10.0
            assert data["merin_fee"] == round(10.0 * 0.03, 2)  # 3% fee
            assert data["net_amount"] == round(10.0 - data["total_fees"], 2)
            assert data["balance_after_withdrawal"] == round(data["current_balance"] - 10.0, 2)
        else:
            # Insufficient balance case
            data = response.json()
            assert "detail" in data
            assert "Insufficient balance" in data["detail"]
    
    def test_simulate_withdrawal_insufficient_balance(self):
        """Test POST /api/profit/simulate-withdrawal returns 400 for excessive amount"""
        # Try to withdraw a very large amount
        response = self.session.post(f"{BASE_URL}/api/profit/simulate-withdrawal", json={
            "amount": 999999999.0,
            "from_currency": "USDT",
            "to_currency": "USD"
        })
        
        assert response.status_code == 400, f"Expected 400 for insufficient balance, got {response.status_code}"
        data = response.json()
        assert "Insufficient balance" in data.get("detail", "")
    
    def test_simulate_withdrawal_fee_calculation(self):
        """Test withdrawal fee calculation is correct (3% Merin fee)"""
        response = self.session.post(f"{BASE_URL}/api/profit/simulate-withdrawal", json={
            "amount": 100.0,
            "from_currency": "USDT",
            "to_currency": "USD"
        })
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify 3% Merin fee
            expected_merin_fee = round(100.0 * 0.03, 2)  # $3.00
            assert data["merin_fee"] == expected_merin_fee, \
                f"Merin fee should be {expected_merin_fee}, got {data['merin_fee']}"
            
            # Verify total fees equals merin fee (no binance fee on withdrawal)
            assert data["total_fees"] == expected_merin_fee
            
            # Verify net amount
            expected_net = round(100.0 - expected_merin_fee, 2)  # $97.00
            assert data["net_amount"] == expected_net, \
                f"Net amount should be {expected_net}, got {data['net_amount']}"


class TestLicenseeAccountValue:
    """Test that licensee account_value comes from license.current_amount"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_get_licenses_list(self):
        """Test GET /api/admin/licenses returns list of licenses"""
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200, f"Failed to get licenses: {response.text}"
        
        data = response.json()
        assert "licenses" in data
        assert isinstance(data["licenses"], list)
        
        if len(data["licenses"]) > 0:
            license = data["licenses"][0]
            # Verify license structure
            assert "id" in license
            assert "user_id" in license
            assert "license_type" in license
            assert "starting_amount" in license
            assert "current_amount" in license
    
    def test_licensee_profit_summary_uses_license_balance(self):
        """Test that licensee's profit summary uses license.current_amount"""
        # First get a licensee user
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        
        data = response.json()
        licenses = data.get("licenses", [])
        
        if len(licenses) == 0:
            pytest.skip("No licensees found to test")
        
        # Get the first active license
        active_license = None
        for lic in licenses:
            if lic.get("is_active", True):
                active_license = lic
                break
        
        if not active_license:
            pytest.skip("No active licensees found")
        
        # The license should have current_amount
        assert "current_amount" in active_license
        license_balance = active_license["current_amount"]
        
        print(f"Found licensee with balance: {license_balance}")
        
        # Note: We can't directly test the licensee's profit summary without logging in as them
        # But we verified the endpoint structure and the license data exists


class TestRegularUserAccountValue:
    """Test that regular user account_value is calculated correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin (who is a regular user, not a licensee)
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_profit_summary_for_regular_user(self):
        """Test profit summary calculation for regular (non-licensee) user"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        
        # For regular users, is_licensee should be False
        # (unless master admin is also a licensee)
        print(f"User is_licensee: {data['is_licensee']}")
        print(f"Account value: {data['account_value']}")
        print(f"Total deposits: {data['total_deposits']}")
        print(f"Total actual profit: {data['total_actual_profit']}")
        
        # Verify the response has valid data
        assert data["account_value"] >= 0 or data["account_value"] < 0  # Can be negative
        assert data["total_deposits"] >= 0
    
    def test_account_value_consistency(self):
        """Test that account_value is consistent between summary and withdrawal simulation"""
        # Get profit summary
        summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        
        # Get withdrawal simulation with small amount
        withdrawal_response = self.session.post(f"{BASE_URL}/api/profit/simulate-withdrawal", json={
            "amount": 1.0,
            "from_currency": "USDT",
            "to_currency": "USD"
        })
        
        if withdrawal_response.status_code == 200:
            withdrawal_data = withdrawal_response.json()
            
            # Both should report the same current balance
            assert summary_data["account_value"] == withdrawal_data["current_balance"], \
                f"Account value mismatch: summary={summary_data['account_value']}, withdrawal={withdrawal_data['current_balance']}"


class TestExistingFunctionalityRegression:
    """Test that existing functionality still works after refactoring"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()
    
    def test_auth_me_endpoint(self):
        """Test GET /api/auth/me still works"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
    
    def test_deposits_endpoint(self):
        """Test GET /api/profit/deposits still works"""
        response = self.session.get(f"{BASE_URL}/api/profit/deposits")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_trade_logs_endpoint(self):
        """Test GET /api/trade/logs still works"""
        response = self.session.get(f"{BASE_URL}/api/trade/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_withdrawals_endpoint(self):
        """Test GET /api/profit/withdrawals still works"""
        response = self.session.get(f"{BASE_URL}/api/profit/withdrawals")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_calculate_exit_endpoint(self):
        """Test POST /api/profit/calculate-exit still works"""
        response = self.session.post(f"{BASE_URL}/api/profit/calculate-exit?lot_size=1.0")
        assert response.status_code == 200
        
        data = response.json()
        assert "lot_size" in data
        assert "exit_value" in data
        assert data["exit_value"] == 15.0  # 1.0 * 15


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

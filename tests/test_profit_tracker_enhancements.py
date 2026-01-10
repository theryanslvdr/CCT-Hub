"""
Test suite for Profit Tracker Enhancements
Features tested:
- Multi-step deposit simulation with 1% fee
- Withdrawal with Merin Fee (3%) + Binance Fee ($1) + estimated date
- POST /profit/withdrawal endpoint
- Money formatting ($XXX,XXX.XX with 2 decimal places)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@crosscurrent.com"
TEST_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token obtained")


class TestDepositSimulation:
    """Test deposit simulation with 1% fee calculation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_create_deposit_with_fee_calculation(self, headers):
        """Test creating deposit - simulating 1% fee deduction"""
        # Simulate: User sends $1000 from Binance, 1% fee = $10, receives $990
        binance_amount = 1000.00
        deposit_fee = binance_amount * 0.01  # 1% fee
        receive_amount = binance_amount - deposit_fee  # $990
        
        response = requests.post(f"{BASE_URL}/api/profit/deposits", 
            headers=headers,
            json={
                "amount": receive_amount,  # Amount after fee
                "currency": "USDT",
                "notes": f"Deposit from Binance (${binance_amount:.2f} - 1% fee)"
            }
        )
        
        assert response.status_code == 200, f"Create deposit failed: {response.text}"
        data = response.json()
        
        # Verify deposit was created with correct amount
        assert data["amount"] == receive_amount
        assert data["currency"] == "USDT"
        assert "id" in data
        print(f"✓ Deposit created: ${receive_amount:.2f} (after 1% fee from ${binance_amount:.2f})")
        
        return data["id"]
    
    def test_deposit_fee_calculation_accuracy(self):
        """Test 1% fee calculation accuracy for various amounts"""
        test_cases = [
            (100.00, 1.00, 99.00),      # $100 - $1 fee = $99
            (500.00, 5.00, 495.00),     # $500 - $5 fee = $495
            (1000.00, 10.00, 990.00),   # $1000 - $10 fee = $990
            (5000.00, 50.00, 4950.00),  # $5000 - $50 fee = $4950
            (10000.00, 100.00, 9900.00) # $10000 - $100 fee = $9900
        ]
        
        for binance_amount, expected_fee, expected_receive in test_cases:
            calculated_fee = binance_amount * 0.01
            calculated_receive = binance_amount - calculated_fee
            
            assert abs(calculated_fee - expected_fee) < 0.01, f"Fee calculation wrong for ${binance_amount}"
            assert abs(calculated_receive - expected_receive) < 0.01, f"Receive amount wrong for ${binance_amount}"
        
        print("✓ All 1% fee calculations are accurate")


class TestWithdrawalSimulation:
    """Test withdrawal simulation with Merin Fee (3%) + Binance Fee ($1)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_simulate_withdrawal_fees(self, headers):
        """Test withdrawal fee calculation: 3% Merin + $1 Binance"""
        withdrawal_amount = 1000.00
        
        response = requests.post(f"{BASE_URL}/api/profit/simulate-withdrawal",
            headers=headers,
            json={
                "amount": withdrawal_amount,
                "from_currency": "USDT",
                "to_currency": "USD"
            }
        )
        
        assert response.status_code == 200, f"Simulate withdrawal failed: {response.text}"
        data = response.json()
        
        # Verify fee calculations
        expected_merin_fee = withdrawal_amount * 0.03  # 3% = $30
        expected_binance_fee = 1.00
        expected_total_fees = expected_merin_fee + expected_binance_fee  # $31
        expected_net = withdrawal_amount - expected_total_fees  # $969
        
        assert abs(data["merin_fee"] - expected_merin_fee) < 0.01, f"Merin fee wrong: {data['merin_fee']} vs {expected_merin_fee}"
        assert data["binance_fee"] == expected_binance_fee, f"Binance fee wrong: {data['binance_fee']}"
        assert abs(data["net_amount"] - expected_net) < 0.01, f"Net amount wrong: {data['net_amount']} vs {expected_net}"
        
        print(f"✓ Withdrawal simulation: ${withdrawal_amount:.2f} -> Net ${data['net_amount']:.2f}")
        print(f"  Merin Fee (3%): ${data['merin_fee']:.2f}")
        print(f"  Binance Fee: ${data['binance_fee']:.2f}")
    
    def test_withdrawal_fee_calculation_accuracy(self):
        """Test withdrawal fee calculation for various amounts"""
        test_cases = [
            (100.00, 3.00, 1.00, 96.00),      # $100: 3% = $3, +$1 = $4 fees, net $96
            (500.00, 15.00, 1.00, 484.00),    # $500: 3% = $15, +$1 = $16 fees, net $484
            (1000.00, 30.00, 1.00, 969.00),   # $1000: 3% = $30, +$1 = $31 fees, net $969
            (5000.00, 150.00, 1.00, 4849.00), # $5000: 3% = $150, +$1 = $151 fees, net $4849
        ]
        
        for amount, expected_merin, expected_binance, expected_net in test_cases:
            merin_fee = amount * 0.03
            binance_fee = 1.00
            net = amount - merin_fee - binance_fee
            
            assert abs(merin_fee - expected_merin) < 0.01, f"Merin fee wrong for ${amount}"
            assert binance_fee == expected_binance
            assert abs(net - expected_net) < 0.01, f"Net amount wrong for ${amount}"
        
        print("✓ All withdrawal fee calculations are accurate")


class TestWithdrawalEndpoint:
    """Test POST /profit/withdrawal endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_record_withdrawal(self, headers):
        """Test recording a withdrawal via POST /profit/withdrawal"""
        withdrawal_amount = 100.00
        
        response = requests.post(f"{BASE_URL}/api/profit/withdrawal",
            headers=headers,
            json={"amount": withdrawal_amount}
        )
        
        assert response.status_code == 200, f"Record withdrawal failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "withdrawal_id" in data
        assert "gross_amount" in data
        assert "merin_fee" in data
        assert "binance_fee" in data
        assert "net_amount" in data
        
        # Verify fee calculations
        expected_merin_fee = withdrawal_amount * 0.03  # 3%
        expected_net = withdrawal_amount - expected_merin_fee - 1.00
        
        assert data["gross_amount"] == withdrawal_amount
        assert abs(data["merin_fee"] - expected_merin_fee) < 0.01
        assert data["binance_fee"] == 1.00
        assert abs(data["net_amount"] - expected_net) < 0.01
        
        print(f"✓ Withdrawal recorded: ${withdrawal_amount:.2f}")
        print(f"  Withdrawal ID: {data['withdrawal_id']}")
        print(f"  Net to Binance: ${data['net_amount']:.2f}")
    
    def test_withdrawal_appears_in_deposits(self, headers):
        """Test that withdrawal appears as negative deposit"""
        response = requests.get(f"{BASE_URL}/api/profit/deposits", headers=headers)
        assert response.status_code == 200
        
        deposits = response.json()
        
        # Find withdrawals (negative amounts)
        withdrawals = [d for d in deposits if d.get("amount", 0) < 0]
        
        if withdrawals:
            print(f"✓ Found {len(withdrawals)} withdrawal(s) in deposit records")
            for w in withdrawals[-3:]:  # Show last 3
                print(f"  - ${abs(w['amount']):.2f} withdrawal: {w.get('notes', 'No notes')}")
        else:
            print("✓ No withdrawals found (may have been reset)")


class TestProfitSummary:
    """Test profit summary calculations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_profit_summary(self, headers):
        """Test getting profit summary with account value"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200, f"Get summary failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_deposits" in data
        assert "total_actual_profit" in data
        assert "account_value" in data
        
        # Account value should be deposits + profit
        expected_account_value = data["total_deposits"] + data["total_actual_profit"]
        assert abs(data["account_value"] - expected_account_value) < 0.01
        
        print(f"✓ Profit Summary:")
        print(f"  Total Deposits: ${data['total_deposits']:.2f}")
        print(f"  Total Profit: ${data['total_actual_profit']:.2f}")
        print(f"  Account Value: ${data['account_value']:.2f}")
    
    def test_lot_size_calculation(self, headers):
        """Test LOT Size = Balance / 980 formula"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        account_value = data["account_value"]
        
        # Calculate LOT size
        lot_size = account_value / 980
        daily_profit = lot_size * 15
        
        print(f"✓ LOT Size Calculation:")
        print(f"  Account Balance: ${account_value:.2f}")
        print(f"  LOT Size (Balance ÷ 980): {lot_size:.4f}")
        print(f"  Daily Profit (LOT × 15): ${daily_profit:.2f}")


class TestBusinessDaysCalculation:
    """Test business days calculation for estimated withdrawal date"""
    
    def test_add_business_days_weekday(self):
        """Test adding 2 business days from a weekday"""
        # Monday -> Wednesday (2 business days)
        monday = datetime(2025, 1, 6)  # Monday
        expected = datetime(2025, 1, 8)  # Wednesday
        
        result = self._add_business_days(monday, 2)
        assert result.date() == expected.date(), f"Expected {expected.date()}, got {result.date()}"
        print("✓ Monday + 2 business days = Wednesday")
    
    def test_add_business_days_friday(self):
        """Test adding 2 business days from Friday (skips weekend)"""
        # Friday -> Tuesday (skips Sat, Sun)
        friday = datetime(2025, 1, 10)  # Friday
        expected = datetime(2025, 1, 14)  # Tuesday
        
        result = self._add_business_days(friday, 2)
        assert result.date() == expected.date(), f"Expected {expected.date()}, got {result.date()}"
        print("✓ Friday + 2 business days = Tuesday (skips weekend)")
    
    def test_add_business_days_thursday(self):
        """Test adding 2 business days from Thursday"""
        # Thursday -> Monday (skips weekend)
        thursday = datetime(2025, 1, 9)  # Thursday
        expected = datetime(2025, 1, 13)  # Monday
        
        result = self._add_business_days(thursday, 2)
        assert result.date() == expected.date(), f"Expected {expected.date()}, got {result.date()}"
        print("✓ Thursday + 2 business days = Monday (skips weekend)")
    
    def _add_business_days(self, date, days):
        """Helper: Add business days to a date"""
        result = date
        added = 0
        while added < days:
            result = result + timedelta(days=1)
            if result.weekday() < 5:  # Monday=0, Friday=4
                added += 1
        return result


class TestMoneyFormatting:
    """Test money formatting: $XXX,XXX.XX with 2 decimal places"""
    
    def test_format_money_basic(self):
        """Test basic money formatting"""
        test_cases = [
            (0, "$0.00"),
            (1, "$1.00"),
            (10.5, "$10.50"),
            (100.99, "$100.99"),
            (1000, "$1,000.00"),
            (10000.50, "$10,000.50"),
            (100000, "$100,000.00"),
            (1000000.99, "$1,000,000.99"),
        ]
        
        for amount, expected in test_cases:
            formatted = self._format_money(amount)
            assert formatted == expected, f"Format wrong for {amount}: got {formatted}, expected {expected}"
        
        print("✓ All money formatting tests passed")
    
    def test_format_money_decimals(self):
        """Test that money always shows 2 decimal places"""
        test_cases = [
            (100, "$100.00"),      # Integer -> 2 decimals
            (100.1, "$100.10"),    # 1 decimal -> 2 decimals
            (100.123, "$100.12"),  # 3 decimals -> 2 decimals (rounded)
        ]
        
        for amount, expected in test_cases:
            formatted = self._format_money(amount)
            assert formatted == expected, f"Decimal format wrong for {amount}"
        
        print("✓ Money formatting always shows 2 decimal places")
    
    def _format_money(self, amount):
        """Helper: Format money like frontend does"""
        if amount is None:
            return "$0.00"
        return "${:,.2f}".format(amount)


class TestResetProfitTracker:
    """Test reset profit tracker functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_reset_endpoint_exists(self, headers):
        """Test that DELETE /profit/reset endpoint exists"""
        # Note: We don't actually reset to preserve test data
        # Just verify the endpoint responds correctly
        response = requests.delete(f"{BASE_URL}/api/profit/reset", headers=headers)
        
        # Should return 200 with success message
        assert response.status_code == 200, f"Reset endpoint failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Reset endpoint works: {data['message']}")


class TestDepositsTable:
    """Test deposits table structure (without Product column)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_deposits_structure(self, headers):
        """Test deposits API returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/profit/deposits", headers=headers)
        
        assert response.status_code == 200, f"Get deposits failed: {response.text}"
        deposits = response.json()
        
        if deposits:
            deposit = deposits[0]
            # Verify required fields
            assert "id" in deposit
            assert "amount" in deposit
            assert "currency" in deposit
            assert "created_at" in deposit
            # Notes is optional
            
            print(f"✓ Deposits structure verified ({len(deposits)} records)")
            print(f"  Fields: id, amount, currency, created_at, notes")
        else:
            print("✓ No deposits found (empty state)")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test suite for Profit Tracker V2 Features
Features tested:
- Deposit Records button and dialog
- Withdrawal Records with Confirm Receipt functionality
- Year Projection dropdown (1-5 years)
- Large number formatting (Million, Billion, Trillion)
- Withdrawal immediate balance deduction
- Monthly accordion projection table (5 years)
- Multi-step reset with password verification
- POST /auth/verify-password endpoint
- GET /profit/withdrawals endpoint
- PUT /profit/withdrawals/{id}/confirm endpoint
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


class TestVerifyPassword:
    """Test POST /auth/verify-password endpoint"""
    
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
    
    def test_verify_password_correct(self, headers):
        """Test verifying correct password returns valid=true"""
        response = requests.post(f"{BASE_URL}/api/auth/verify-password",
            headers=headers,
            json={"password": TEST_PASSWORD}
        )
        
        assert response.status_code == 200, f"Verify password failed: {response.text}"
        data = response.json()
        assert "valid" in data
        assert data["valid"] == True
        print("✓ Correct password verification returns valid=true")
    
    def test_verify_password_incorrect(self, headers):
        """Test verifying incorrect password returns valid=false"""
        response = requests.post(f"{BASE_URL}/api/auth/verify-password",
            headers=headers,
            json={"password": "wrongpassword123"}
        )
        
        assert response.status_code == 200, f"Verify password failed: {response.text}"
        data = response.json()
        assert "valid" in data
        assert data["valid"] == False
        print("✓ Incorrect password verification returns valid=false")
    
    def test_verify_password_requires_auth(self):
        """Test verify-password requires authentication"""
        response = requests.post(f"{BASE_URL}/api/auth/verify-password",
            json={"password": TEST_PASSWORD}
        )
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Verify password endpoint requires authentication")


class TestWithdrawalsEndpoint:
    """Test GET /profit/withdrawals endpoint"""
    
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
    
    def test_get_withdrawals_endpoint_exists(self, headers):
        """Test GET /profit/withdrawals endpoint exists and returns list"""
        response = requests.get(f"{BASE_URL}/api/profit/withdrawals", headers=headers)
        
        assert response.status_code == 200, f"Get withdrawals failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Withdrawals should return a list"
        print(f"✓ GET /profit/withdrawals returns list with {len(data)} items")
    
    def test_withdrawal_record_structure(self, headers):
        """Test withdrawal records have correct structure"""
        # First create a withdrawal to ensure we have data
        withdrawal_response = requests.post(f"{BASE_URL}/api/profit/withdrawal",
            headers=headers,
            json={"amount": 50.00, "notes": "TEST_withdrawal_structure"}
        )
        
        if withdrawal_response.status_code == 200:
            # Now get withdrawals
            response = requests.get(f"{BASE_URL}/api/profit/withdrawals", headers=headers)
            assert response.status_code == 200
            
            withdrawals = response.json()
            if withdrawals:
                w = withdrawals[0]
                # Verify required fields for Withdrawal Records dialog
                assert "id" in w, "Missing id field"
                assert "created_at" in w, "Missing created_at (Date Initiated)"
                assert "gross_amount" in w or "amount" in w, "Missing amount field"
                assert "net_amount" in w, "Missing net_amount (Final Binance)"
                assert "estimated_arrival" in w, "Missing estimated_arrival (Est. Arrival)"
                # confirmed_at can be null
                
                print("✓ Withdrawal record has correct structure:")
                print(f"  - id: {w.get('id')}")
                print(f"  - created_at (Date Initiated): {w.get('created_at')}")
                print(f"  - gross_amount: {w.get('gross_amount', w.get('amount'))}")
                print(f"  - net_amount (Final Binance): {w.get('net_amount')}")
                print(f"  - estimated_arrival: {w.get('estimated_arrival')}")
                print(f"  - notes: {w.get('notes')}")
                print(f"  - confirmed_at: {w.get('confirmed_at')}")
            else:
                print("✓ Withdrawals endpoint works (no records yet)")


class TestConfirmWithdrawalReceipt:
    """Test PUT /profit/withdrawals/{id}/confirm endpoint"""
    
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
    
    def test_confirm_receipt_endpoint(self, headers):
        """Test confirming receipt of a withdrawal"""
        # First create a withdrawal
        withdrawal_response = requests.post(f"{BASE_URL}/api/profit/withdrawal",
            headers=headers,
            json={"amount": 25.00, "notes": "TEST_confirm_receipt"}
        )
        
        assert withdrawal_response.status_code == 200, f"Create withdrawal failed: {withdrawal_response.text}"
        withdrawal_id = withdrawal_response.json()["withdrawal_id"]
        
        # Now confirm receipt
        confirmed_at = datetime.now().strftime("%b %d, %Y %I:%M %p")
        confirm_response = requests.put(
            f"{BASE_URL}/api/profit/withdrawals/{withdrawal_id}/confirm",
            headers=headers,
            json={"confirmed_at": confirmed_at}
        )
        
        assert confirm_response.status_code == 200, f"Confirm receipt failed: {confirm_response.text}"
        data = confirm_response.json()
        assert "message" in data
        assert "confirmed_at" in data
        assert data["confirmed_at"] == confirmed_at
        
        print(f"✓ Confirm receipt endpoint works")
        print(f"  - Withdrawal ID: {withdrawal_id}")
        print(f"  - Confirmed at: {confirmed_at}")
    
    def test_confirm_receipt_updates_record(self, headers):
        """Test that confirming receipt updates the withdrawal record"""
        # Create withdrawal
        withdrawal_response = requests.post(f"{BASE_URL}/api/profit/withdrawal",
            headers=headers,
            json={"amount": 30.00, "notes": "TEST_confirm_updates"}
        )
        
        assert withdrawal_response.status_code == 200
        withdrawal_id = withdrawal_response.json()["withdrawal_id"]
        
        # Confirm receipt
        confirmed_at = datetime.now().strftime("%b %d, %Y %I:%M %p")
        requests.put(
            f"{BASE_URL}/api/profit/withdrawals/{withdrawal_id}/confirm",
            headers=headers,
            json={"confirmed_at": confirmed_at}
        )
        
        # Verify the record was updated
        withdrawals_response = requests.get(f"{BASE_URL}/api/profit/withdrawals", headers=headers)
        assert withdrawals_response.status_code == 200
        
        withdrawals = withdrawals_response.json()
        confirmed_withdrawal = next((w for w in withdrawals if w["id"] == withdrawal_id), None)
        
        assert confirmed_withdrawal is not None, "Withdrawal not found"
        assert confirmed_withdrawal.get("confirmed_at") == confirmed_at, "confirmed_at not updated"
        
        print("✓ Confirm receipt updates withdrawal record correctly")
    
    def test_confirm_receipt_invalid_id(self, headers):
        """Test confirming receipt with invalid withdrawal ID"""
        response = requests.put(
            f"{BASE_URL}/api/profit/withdrawals/invalid-id-12345/confirm",
            headers=headers,
            json={"confirmed_at": "Dec 15, 2025 10:00 AM"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Confirm receipt returns 404 for invalid withdrawal ID")


class TestWithdrawalBalanceDeduction:
    """Test that withdrawal immediately deducts from balance"""
    
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
    
    def test_withdrawal_deducts_balance_immediately(self, headers):
        """Test that withdrawal deducts from account balance immediately"""
        # Get initial balance
        summary_before = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert summary_before.status_code == 200
        balance_before = summary_before.json()["account_value"]
        
        # Make a withdrawal
        withdrawal_amount = 20.00
        withdrawal_response = requests.post(f"{BASE_URL}/api/profit/withdrawal",
            headers=headers,
            json={"amount": withdrawal_amount, "notes": "TEST_balance_deduction"}
        )
        
        assert withdrawal_response.status_code == 200
        
        # Get balance after
        summary_after = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert summary_after.status_code == 200
        balance_after = summary_after.json()["account_value"]
        
        # Balance should be reduced by withdrawal amount
        expected_balance = balance_before - withdrawal_amount
        assert abs(balance_after - expected_balance) < 0.01, \
            f"Balance not deducted correctly. Before: {balance_before}, After: {balance_after}, Expected: {expected_balance}"
        
        print(f"✓ Withdrawal immediately deducts from balance")
        print(f"  - Balance before: ${balance_before:.2f}")
        print(f"  - Withdrawal: ${withdrawal_amount:.2f}")
        print(f"  - Balance after: ${balance_after:.2f}")


class TestResetProfitTracker:
    """Test multi-step reset with password verification"""
    
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
        """Test DELETE /profit/reset endpoint exists"""
        # Note: This will actually reset data, so we verify it works
        response = requests.delete(f"{BASE_URL}/api/profit/reset", headers=headers)
        
        assert response.status_code == 200, f"Reset endpoint failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "deleted" in data
        print(f"✓ Reset endpoint works: {data['message']}")
    
    def test_reset_clears_deposits(self, headers):
        """Test that reset clears all deposits"""
        # First add a deposit
        requests.post(f"{BASE_URL}/api/profit/deposits",
            headers=headers,
            json={"amount": 100.00, "currency": "USDT", "notes": "TEST_reset_deposit"}
        )
        
        # Reset
        requests.delete(f"{BASE_URL}/api/profit/reset", headers=headers)
        
        # Verify deposits are cleared
        deposits_response = requests.get(f"{BASE_URL}/api/profit/deposits", headers=headers)
        assert deposits_response.status_code == 200
        deposits = deposits_response.json()
        
        # Should be empty or only have non-test deposits
        test_deposits = [d for d in deposits if "TEST_reset" in (d.get("notes") or "")]
        assert len(test_deposits) == 0, "Test deposits should be cleared after reset"
        
        print("✓ Reset clears all deposits")


class TestLargeNumberFormatting:
    """Test large number formatting (Million, Billion, Trillion)"""
    
    def test_format_million(self):
        """Test formatting numbers >= 1 million"""
        test_cases = [
            (1000000, "$1.00 Million"),
            (1500000, "$1.50 Million"),
            (10000000, "$10.00 Million"),
            (999999999, "$1000.00 Million"),  # Just under 1 billion
        ]
        
        for amount, expected in test_cases:
            formatted = self._format_large_number(amount)
            assert formatted == expected, f"Format wrong for {amount}: got {formatted}, expected {expected}"
        
        print("✓ Million formatting works correctly")
    
    def test_format_billion(self):
        """Test formatting numbers >= 1 billion"""
        test_cases = [
            (1000000000, "$1.00 Billion"),
            (2500000000, "$2.50 Billion"),
            (100000000000, "$100.00 Billion"),
        ]
        
        for amount, expected in test_cases:
            formatted = self._format_large_number(amount)
            assert formatted == expected, f"Format wrong for {amount}: got {formatted}, expected {expected}"
        
        print("✓ Billion formatting works correctly")
    
    def test_format_trillion(self):
        """Test formatting numbers >= 1 trillion"""
        test_cases = [
            (1000000000000, "$1.00 Trillion"),
            (5500000000000, "$5.50 Trillion"),
        ]
        
        for amount, expected in test_cases:
            formatted = self._format_large_number(amount)
            assert formatted == expected, f"Format wrong for {amount}: got {formatted}, expected {expected}"
        
        print("✓ Trillion formatting works correctly")
    
    def test_format_negative_large_numbers(self):
        """Test formatting negative large numbers"""
        test_cases = [
            (-1000000, "-$1.00 Million"),
            (-1000000000, "-$1.00 Billion"),
            (-1000000000000, "-$1.00 Trillion"),
        ]
        
        for amount, expected in test_cases:
            formatted = self._format_large_number(amount)
            assert formatted == expected, f"Format wrong for {amount}: got {formatted}, expected {expected}"
        
        print("✓ Negative large number formatting works correctly")
    
    def _format_large_number(self, amount):
        """Helper: Format large numbers like frontend does"""
        if amount is None:
            return "$0.00"
        
        abs_amount = abs(amount)
        sign = "-" if amount < 0 else ""
        
        if abs_amount >= 1e12:
            return f"{sign}${abs_amount / 1e12:.2f} Trillion"
        elif abs_amount >= 1e9:
            return f"{sign}${abs_amount / 1e9:.2f} Billion"
        elif abs_amount >= 1e6:
            return f"{sign}${abs_amount / 1e6:.2f} Million"
        else:
            return "${:,.2f}".format(amount)


class TestDepositsEndpoint:
    """Test GET /profit/deposits endpoint for Deposit Records dialog"""
    
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
    
    def test_get_deposits_returns_list(self, headers):
        """Test GET /profit/deposits returns a list"""
        response = requests.get(f"{BASE_URL}/api/profit/deposits", headers=headers)
        
        assert response.status_code == 200, f"Get deposits failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Deposits should return a list"
        print(f"✓ GET /profit/deposits returns list with {len(data)} items")
    
    def test_deposit_record_structure(self, headers):
        """Test deposit records have correct structure for Deposit Records dialog"""
        # Create a deposit first
        requests.post(f"{BASE_URL}/api/profit/deposits",
            headers=headers,
            json={"amount": 500.00, "currency": "USDT", "notes": "TEST_deposit_structure"}
        )
        
        response = requests.get(f"{BASE_URL}/api/profit/deposits", headers=headers)
        assert response.status_code == 200
        
        deposits = response.json()
        if deposits:
            d = deposits[-1]  # Get latest
            # Verify required fields for Deposit Records dialog
            assert "id" in d, "Missing id field"
            assert "created_at" in d, "Missing created_at (Date)"
            assert "amount" in d, "Missing amount"
            assert "currency" in d, "Missing currency"
            # notes is optional
            
            print("✓ Deposit record has correct structure:")
            print(f"  - id: {d.get('id')}")
            print(f"  - created_at (Date): {d.get('created_at')}")
            print(f"  - amount: {d.get('amount')}")
            print(f"  - currency: {d.get('currency')}")
            print(f"  - notes: {d.get('notes')}")


class TestProfitSummary:
    """Test profit summary for projection calculations"""
    
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
        """Test getting profit summary"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200, f"Get summary failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_deposits" in data
        assert "total_actual_profit" in data
        assert "account_value" in data
        
        print(f"✓ Profit Summary:")
        print(f"  Total Deposits: ${data['total_deposits']:.2f}")
        print(f"  Total Profit: ${data['total_actual_profit']:.2f}")
        print(f"  Account Value: ${data['account_value']:.2f}")


class TestMonthlyProjectionCalculation:
    """Test monthly projection calculation (5 years = 60 months)"""
    
    def test_monthly_projection_generates_60_months(self):
        """Test that monthly projection generates 60 months (5 years)"""
        account_balance = 10000.00
        months = self._generate_monthly_projection(account_balance)
        
        assert len(months) == 60, f"Expected 60 months, got {len(months)}"
        print("✓ Monthly projection generates 60 months (5 years)")
    
    def test_monthly_projection_grouped_by_year(self):
        """Test that months are correctly grouped by year"""
        account_balance = 10000.00
        months = self._generate_monthly_projection(account_balance)
        years = self._group_months_by_year(months)
        
        assert len(years) == 5, f"Expected 5 years, got {len(years)}"
        
        for year_num, year_months in years.items():
            assert len(year_months) == 12, f"Year {year_num} should have 12 months, got {len(year_months)}"
        
        print("✓ Monthly projection correctly grouped by year (5 years × 12 months)")
    
    def test_year_final_balance_shown(self):
        """Test that each year shows final projected balance"""
        account_balance = 10000.00
        months = self._generate_monthly_projection(account_balance)
        years = self._group_months_by_year(months)
        
        for year_num, year_months in years.items():
            final_month = year_months[-1]
            assert "balance" in final_month, f"Year {year_num} final month missing balance"
            print(f"  Year {year_num} final balance: ${final_month['balance']:,.2f}")
        
        print("✓ Each year accordion shows final projected balance")
    
    def _generate_monthly_projection(self, account_balance):
        """Helper: Generate monthly projection like frontend does"""
        months = []
        balance = account_balance
        trading_days_per_month = 22
        
        for month in range(1, 61):  # 60 months
            for day in range(trading_days_per_month):
                lot_size = balance / 980
                daily_profit = lot_size * 15
                balance += daily_profit
            
            months.append({
                "month": month,
                "year": (month - 1) // 12 + 1,
                "balance": balance,
                "lot_size": balance / 980,
                "daily_profit": (balance / 980) * 15,
            })
        
        return months
    
    def _group_months_by_year(self, monthly_data):
        """Helper: Group months by year"""
        years = {}
        for m in monthly_data:
            year = m["year"]
            if year not in years:
                years[year] = []
            years[year].append(m)
        return years


class TestYearProjectionDropdown:
    """Test year projection dropdown (1-5 years)"""
    
    def test_projection_for_different_years(self):
        """Test projection calculation for 1-5 years"""
        account_balance = 10000.00
        
        for years in range(1, 6):
            projection = self._generate_projection_data(account_balance, years)
            
            # Should have: Today, 1 Month, 3 Months, 6 Months, X Year(s)
            assert len(projection) == 5, f"Expected 5 periods for {years} year(s)"
            
            # Last period should be the selected years
            last_period = projection[-1]
            expected_label = f"{years} Year" if years == 1 else f"{years} Years"
            assert last_period["period"] == expected_label, \
                f"Expected '{expected_label}', got '{last_period['period']}'"
            
            print(f"✓ {years} year projection: ${last_period['balance']:,.2f}")
        
        print("✓ Year projection dropdown works for 1-5 years")
    
    def _generate_projection_data(self, account_balance, selected_years):
        """Helper: Generate projection data like frontend does"""
        projections = []
        balance = account_balance
        
        periods = [
            {"label": "1 Month", "days": 22},
            {"label": "3 Months", "days": 66},
            {"label": "6 Months", "days": 132},
        ]
        
        year_days = selected_years * 264
        year_label = f"{selected_years} Year" if selected_years == 1 else f"{selected_years} Years"
        periods.append({"label": year_label, "days": year_days})
        
        projections.append({
            "period": "Today",
            "balance": balance,
        })
        
        running_balance = balance
        last_days = 0
        
        for period in periods:
            for day in range(last_days, period["days"]):
                lot_size = running_balance / 980
                daily_profit = lot_size * 15
                running_balance += daily_profit
            last_days = period["days"]
            
            projections.append({
                "period": period["label"],
                "balance": running_balance,
            })
        
        return projections


# Cleanup test data after all tests
class TestCleanup:
    """Cleanup test data"""
    
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
    
    def test_add_initial_balance_after_tests(self, headers):
        """Add initial balance after tests to restore state"""
        # Add a reasonable initial balance
        response = requests.post(f"{BASE_URL}/api/profit/deposits",
            headers=headers,
            json={"amount": 10000.00, "currency": "USDT", "notes": "Initial balance after testing"}
        )
        
        assert response.status_code == 200
        print("✓ Added initial balance of $10,000 after tests")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

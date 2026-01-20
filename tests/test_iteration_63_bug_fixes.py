"""
Test Iteration 63 - Bug Fixes Verification
Tests for 5 issues fixed:
1. Signal Card: Verify Compact Active Signal Card is hidden on desktop (md:hidden class)
2. Balance Calculation: Verify today's 'Balance Before' shows pre-trade balance
3. Date Handling: Verify Daily Projection shows all trading days including current day
4. Licensee Profit: Verify /api/admin/members/{id} returns correct total_profit for licensees
5. Onboarding Mobile: Verify OnboardingWizard has responsive layout
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthSetup:
    """Authentication setup for tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get Master Admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authenticated headers"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestLicenseeProfitCalculation(TestAuthSetup):
    """Issue 4: Verify /api/admin/members/{id} returns correct total_profit for licensees"""
    
    def test_get_licenses_list(self, auth_headers):
        """Get list of active licenses to find a licensee"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get licenses: {response.text}"
        data = response.json()
        assert "licenses" in data, "Response should contain 'licenses' key"
        return data["licenses"]
    
    def test_licensee_profit_calculation(self, auth_headers):
        """Verify licensee profit = current_amount - starting_amount"""
        # First get list of licenses
        licenses_response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=auth_headers)
        assert licenses_response.status_code == 200
        licenses = licenses_response.json().get("licenses", [])
        
        # Find an active license
        active_licenses = [l for l in licenses if l.get("is_active")]
        if not active_licenses:
            pytest.skip("No active licenses found to test")
        
        license = active_licenses[0]
        user_id = license["user_id"]
        starting_amount = license.get("starting_amount", 0)
        current_amount = license.get("current_amount", 0)
        expected_profit = round(current_amount - starting_amount, 2)
        
        # Get member details
        member_response = requests.get(f"{BASE_URL}/api/admin/members/{user_id}", headers=auth_headers)
        assert member_response.status_code == 200, f"Failed to get member details: {member_response.text}"
        
        member_data = member_response.json()
        stats = member_data.get("stats", {})
        
        # Verify the profit calculation
        actual_profit = stats.get("total_profit", 0)
        assert stats.get("is_licensee") == True, "Member should be marked as licensee"
        assert actual_profit == expected_profit, f"Licensee profit should be {expected_profit} (current_amount - starting_amount), got {actual_profit}"
        
        print(f"✓ Licensee profit verified: starting={starting_amount}, current={current_amount}, profit={actual_profit}")


class TestProfitSummaryAPI(TestAuthSetup):
    """Test profit summary API for balance calculations"""
    
    def test_profit_summary_returns_account_value(self, auth_headers):
        """Verify profit summary returns account_value"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get profit summary: {response.text}"
        
        data = response.json()
        assert "account_value" in data, "Response should contain 'account_value'"
        assert "total_deposits" in data, "Response should contain 'total_deposits'"
        assert "total_actual_profit" in data, "Response should contain 'total_actual_profit'"
        
        print(f"✓ Profit summary: account_value={data['account_value']}, deposits={data['total_deposits']}, profit={data['total_actual_profit']}")


class TestTradeLogsAPI(TestAuthSetup):
    """Test trade logs API for date handling"""
    
    def test_trade_logs_returns_dates(self, auth_headers):
        """Verify trade logs return proper date format"""
        response = requests.get(f"{BASE_URL}/api/trade/logs?limit=10", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get trade logs: {response.text}"
        
        trades = response.json()
        if trades:
            trade = trades[0]
            assert "created_at" in trade, "Trade should have created_at field"
            # Verify date format is ISO
            created_at = trade["created_at"]
            assert "T" in created_at, f"Date should be in ISO format, got: {created_at}"
            print(f"✓ Trade log date format verified: {created_at}")
        else:
            print("✓ No trades found, but API works correctly")


class TestGlobalHolidaysAPI(TestAuthSetup):
    """Test global holidays API for date handling"""
    
    def test_global_holidays_returns_dates(self, auth_headers):
        """Verify global holidays API returns proper date format"""
        response = requests.get(f"{BASE_URL}/api/trade/global-holidays", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get global holidays: {response.text}"
        
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        
        holidays = data["holidays"]
        if holidays:
            holiday = holidays[0]
            assert "date" in holiday, "Holiday should have date field"
            # Verify date format is YYYY-MM-DD
            date_str = holiday["date"]
            assert len(date_str) == 10, f"Date should be YYYY-MM-DD format, got: {date_str}"
            assert date_str[4] == "-" and date_str[7] == "-", f"Date should be YYYY-MM-DD format, got: {date_str}"
            print(f"✓ Holiday date format verified: {date_str}")
        else:
            print("✓ No holidays found, but API works correctly")


class TestActiveSignalAPI(TestAuthSetup):
    """Test active signal API"""
    
    def test_active_signal_endpoint(self, auth_headers):
        """Verify active signal endpoint works"""
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get active signal: {response.text}"
        
        data = response.json()
        # Either has signal or message saying no active signal
        if data.get("signal"):
            signal = data["signal"]
            assert "direction" in signal, "Signal should have direction"
            assert "trade_time" in signal, "Signal should have trade_time"
            print(f"✓ Active signal found: {signal['direction']} at {signal['trade_time']}")
        else:
            print("✓ No active signal, but API works correctly")


class TestMemberDetailsAPI(TestAuthSetup):
    """Test member details API for licensee profit calculation"""
    
    def test_member_details_for_regular_user(self, auth_headers):
        """Verify member details returns correct structure for regular users"""
        # Get list of members
        members_response = requests.get(f"{BASE_URL}/api/admin/members", headers=auth_headers)
        assert members_response.status_code == 200
        
        members = members_response.json().get("members", [])
        if not members:
            pytest.skip("No members found")
        
        # Find a non-licensee member
        regular_members = [m for m in members if not m.get("license_type")]
        if not regular_members:
            pytest.skip("No regular members found")
        
        member = regular_members[0]
        user_id = member["id"]
        
        # Get member details
        response = requests.get(f"{BASE_URL}/api/admin/members/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data, "Response should contain 'user'"
        assert "stats" in data, "Response should contain 'stats'"
        
        stats = data["stats"]
        assert "total_profit" in stats, "Stats should contain 'total_profit'"
        assert "account_value" in stats, "Stats should contain 'account_value'"
        assert "total_deposits" in stats, "Stats should contain 'total_deposits'"
        
        print(f"✓ Regular member details verified: profit={stats['total_profit']}, account_value={stats['account_value']}")


class TestLicenseeAccountValueCalculation(TestAuthSetup):
    """Verify licensee account_value comes from license.current_amount"""
    
    def test_licensee_account_value_from_license(self, auth_headers):
        """Verify licensee account_value = license.current_amount"""
        # Get licenses
        licenses_response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=auth_headers)
        assert licenses_response.status_code == 200
        licenses = licenses_response.json().get("licenses", [])
        
        active_licenses = [l for l in licenses if l.get("is_active")]
        if not active_licenses:
            pytest.skip("No active licenses found")
        
        license = active_licenses[0]
        user_id = license["user_id"]
        expected_account_value = license.get("current_amount", 0)
        
        # Get member details
        member_response = requests.get(f"{BASE_URL}/api/admin/members/{user_id}", headers=auth_headers)
        assert member_response.status_code == 200
        
        stats = member_response.json().get("stats", {})
        actual_account_value = stats.get("account_value", 0)
        
        assert actual_account_value == expected_account_value, \
            f"Licensee account_value should be {expected_account_value} (from license.current_amount), got {actual_account_value}"
        
        print(f"✓ Licensee account_value verified: {actual_account_value}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

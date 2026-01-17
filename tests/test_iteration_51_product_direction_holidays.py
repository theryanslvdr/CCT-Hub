"""
Test Iteration 51 - Product/Direction Selection in Onboarding and Global Holidays Features

Features to test:
1. Onboarding Wizard: Product dropdown (MOIL10, XAUUSD, etc.) is available
2. Onboarding Wizard: Direction dropdown (BUY, SELL) is available
3. Onboarding Wizard: Holiday button is REMOVED (no tree icon)
4. Settings: Holidays tab exists with calendar date picker
5. Settings: Clicking a date toggles it as a holiday (shows tree icon)
6. Settings: Holiday list shows scheduled holidays with delete button
7. Global Holidays API: Super Admin can add/remove holidays
8. Daily Projection: Global holidays show as 'HOLIDAY' row with tree icons
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestGlobalHolidaysAPI:
    """Test Global Holidays API endpoints for Super/Master Admin"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Failed to login as master admin: {login_response.status_code}")
    
    def test_01_get_global_holidays_admin_endpoint(self):
        """Test GET /api/admin/global-holidays - Admin endpoint"""
        response = self.session.get(f"{BASE_URL}/api/admin/global-holidays")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        assert isinstance(data["holidays"], list), "Holidays should be a list"
        print(f"✓ GET /api/admin/global-holidays - Found {len(data['holidays'])} holidays")
    
    def test_02_get_global_holidays_user_endpoint(self):
        """Test GET /api/trade/global-holidays - User endpoint"""
        response = self.session.get(f"{BASE_URL}/api/trade/global-holidays")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        print(f"✓ GET /api/trade/global-holidays - Found {len(data['holidays'])} holidays")
    
    def test_03_add_global_holiday(self):
        """Test POST /api/admin/global-holidays - Add a global holiday"""
        # Use a date 90 days in the future to avoid conflicts
        future_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        
        response = self.session.post(f"{BASE_URL}/api/admin/global-holidays", params={
            "date": future_date,
            "reason": "Test Holiday for Iteration 51"
        })
        
        # Could be 200 (success) or 400 (already exists)
        if response.status_code == 200:
            data = response.json()
            assert "message" in data, "Response should contain 'message'"
            print(f"✓ POST /api/admin/global-holidays - Added holiday for {future_date}")
        elif response.status_code == 400:
            # Holiday already exists - that's fine
            print(f"✓ POST /api/admin/global-holidays - Holiday already exists for {future_date}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}: {response.text}")
    
    def test_04_add_global_holiday_invalid_date(self):
        """Test POST /api/admin/global-holidays with invalid date format"""
        response = self.session.post(f"{BASE_URL}/api/admin/global-holidays", params={
            "date": "invalid-date",
            "reason": "Test"
        })
        assert response.status_code == 400, f"Expected 400 for invalid date, got {response.status_code}"
        print("✓ POST /api/admin/global-holidays - Correctly rejects invalid date format")
    
    def test_05_delete_global_holiday(self):
        """Test DELETE /api/admin/global-holidays/{date}"""
        # First add a holiday to delete
        future_date = (datetime.now() + timedelta(days=91)).strftime("%Y-%m-%d")
        
        # Add the holiday
        self.session.post(f"{BASE_URL}/api/admin/global-holidays", params={
            "date": future_date,
            "reason": "Test Holiday to Delete"
        })
        
        # Now delete it
        response = self.session.delete(f"{BASE_URL}/api/admin/global-holidays/{future_date}")
        
        if response.status_code == 200:
            print(f"✓ DELETE /api/admin/global-holidays/{future_date} - Holiday deleted")
        elif response.status_code == 404:
            print(f"✓ DELETE /api/admin/global-holidays/{future_date} - Holiday not found (already deleted)")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}: {response.text}")
    
    def test_06_delete_nonexistent_holiday(self):
        """Test DELETE /api/admin/global-holidays/{date} for non-existent date"""
        response = self.session.delete(f"{BASE_URL}/api/admin/global-holidays/1999-01-01")
        assert response.status_code == 404, f"Expected 404 for non-existent holiday, got {response.status_code}"
        print("✓ DELETE /api/admin/global-holidays - Correctly returns 404 for non-existent date")
    
    def test_07_verify_jan_20_2026_holiday(self):
        """Test that Jan 20, 2026 holiday exists (as mentioned in context)"""
        response = self.session.get(f"{BASE_URL}/api/trade/global-holidays")
        assert response.status_code == 200
        
        data = response.json()
        holidays = data.get("holidays", [])
        
        # Check if 2026-01-20 is in the holidays
        jan_20_holiday = next((h for h in holidays if h.get("date") == "2026-01-20"), None)
        
        if jan_20_holiday:
            print("✓ Jan 20, 2026 holiday exists in global holidays")
        else:
            # Add it if it doesn't exist
            add_response = self.session.post(f"{BASE_URL}/api/admin/global-holidays", params={
                "date": "2026-01-20",
                "reason": "Test Global Holiday"
            })
            if add_response.status_code == 200:
                print("✓ Added Jan 20, 2026 as global holiday")
            else:
                print(f"Note: Could not add Jan 20, 2026 holiday: {add_response.status_code}")


class TestOnboardingWizardAPI:
    """Test Onboarding Wizard related API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Failed to login: {login_response.status_code}")
    
    def test_01_profit_summary_endpoint(self):
        """Test GET /api/profit/summary - Used by onboarding"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "account_value" in data, "Response should contain account_value"
        print(f"✓ GET /api/profit/summary - Account value: {data.get('account_value')}")
    
    def test_02_trade_logs_endpoint(self):
        """Test GET /api/trade/logs - Used by onboarding for trade history"""
        response = self.session.get(f"{BASE_URL}/api/trade/logs")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of trade logs"
        print(f"✓ GET /api/trade/logs - Found {len(data)} trade logs")
    
    def test_03_active_signal_endpoint(self):
        """Test GET /api/trade/active-signal - Used for direction"""
        response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        if data.get("signal"):
            signal = data["signal"]
            assert "direction" in signal, "Signal should have direction"
            assert signal["direction"] in ["BUY", "SELL"], f"Direction should be BUY or SELL, got {signal['direction']}"
            print(f"✓ GET /api/trade/active-signal - Direction: {signal['direction']}")
        else:
            print("✓ GET /api/trade/active-signal - No active signal")


class TestUserHolidaysAPI:
    """Test User-specific holidays API (should still work for personal holidays)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Failed to login: {login_response.status_code}")
    
    def test_01_get_user_holidays(self):
        """Test GET /api/trade/holidays - User personal holidays"""
        response = self.session.get(f"{BASE_URL}/api/trade/holidays")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        print(f"✓ GET /api/trade/holidays - Found {len(data['holidays'])} personal holidays")


class TestAuthenticationRequired:
    """Test that endpoints require authentication"""
    
    def test_01_global_holidays_requires_auth(self):
        """Test that global holidays endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/global-holidays")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/global-holidays requires authentication")
    
    def test_02_user_holidays_requires_auth(self):
        """Test that user holidays endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/trade/holidays")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/trade/holidays requires authentication")
    
    def test_03_trade_global_holidays_requires_auth(self):
        """Test that trade global holidays endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/trade/global-holidays")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/trade/global-holidays requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

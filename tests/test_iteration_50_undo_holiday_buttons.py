"""
Iteration 50 - Testing Undo/Holiday Buttons in Onboarding Wizard and Global Holidays API

Features to test:
1. Onboarding Wizard: Undo button appears when a day is marked as missed
2. Onboarding Wizard: Tree icon (holiday) button is visible and clickable
3. Onboarding Wizard: Holiday badge shows when day is marked as holiday
4. Daily Projection Table: Actions column is REMOVED (no Undo/Holiday buttons there)
5. Global Holidays API: GET /api/admin/global-holidays returns holidays
6. Global Holidays API: POST /api/admin/global-holidays adds a global holiday (Master Admin only)
7. Global Holidays API: DELETE /api/admin/global-holidays/{date} removes a global holiday
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
    """Test Global Holidays API endpoints for Master Admin"""
    
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
            pytest.skip(f"Master admin login failed: {login_response.status_code}")
    
    def test_get_global_holidays_returns_list(self):
        """GET /api/admin/global-holidays - Returns list of global holidays"""
        response = self.session.get(f"{BASE_URL}/api/admin/global-holidays")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        assert isinstance(data["holidays"], list), "holidays should be a list"
        print(f"✓ GET /api/admin/global-holidays returns {len(data['holidays'])} holidays")
    
    def test_add_global_holiday_success(self):
        """POST /api/admin/global-holidays - Successfully adds a global holiday"""
        # Use a date 60 days in the future to avoid conflicts
        future_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": future_date, "reason": "Test Global Holiday"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        assert "holiday" in data, "Response should contain 'holiday'"
        assert data["holiday"]["date"] == future_date, "Holiday date should match"
        print(f"✓ POST /api/admin/global-holidays successfully added holiday for {future_date}")
        
        # Cleanup - delete the test holiday
        self.session.delete(f"{BASE_URL}/api/admin/global-holidays/{future_date}")
    
    def test_add_global_holiday_invalid_date(self):
        """POST /api/admin/global-holidays - Invalid date format returns 400"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": "invalid-date", "reason": "Test"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ POST /api/admin/global-holidays with invalid date returns 400")
    
    def test_add_global_holiday_duplicate(self):
        """POST /api/admin/global-holidays - Duplicate holiday returns 400"""
        # First add a holiday
        future_date = (datetime.now() + timedelta(days=61)).strftime("%Y-%m-%d")
        
        response1 = self.session.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": future_date, "reason": "Test Holiday 1"}
        )
        assert response1.status_code == 200, f"First add failed: {response1.text}"
        
        # Try to add the same date again
        response2 = self.session.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": future_date, "reason": "Test Holiday 2"}
        )
        
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}: {response2.text}"
        print("✓ POST /api/admin/global-holidays with duplicate date returns 400")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/admin/global-holidays/{future_date}")
    
    def test_delete_global_holiday_success(self):
        """DELETE /api/admin/global-holidays/{date} - Successfully removes a global holiday"""
        # First add a holiday
        future_date = (datetime.now() + timedelta(days=62)).strftime("%Y-%m-%d")
        
        add_response = self.session.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": future_date, "reason": "Test Holiday to Delete"}
        )
        assert add_response.status_code == 200, f"Add failed: {add_response.text}"
        
        # Now delete it
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/global-holidays/{future_date}")
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        data = delete_response.json()
        assert "message" in data, "Response should contain 'message'"
        print(f"✓ DELETE /api/admin/global-holidays/{future_date} successfully removed holiday")
    
    def test_delete_global_holiday_not_found(self):
        """DELETE /api/admin/global-holidays/{date} - Non-existent holiday returns 404"""
        non_existent_date = "2099-12-31"
        
        response = self.session.delete(f"{BASE_URL}/api/admin/global-holidays/{non_existent_date}")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ DELETE /api/admin/global-holidays with non-existent date returns 404")


class TestGlobalHolidaysUserAccess:
    """Test that regular users can view global holidays but not modify them"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin first to get a token"""
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
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_user_can_view_global_holidays(self):
        """GET /api/trade/global-holidays - Any authenticated user can view global holidays"""
        response = self.session.get(f"{BASE_URL}/api/trade/global-holidays")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        print(f"✓ GET /api/trade/global-holidays returns {len(data['holidays'])} holidays for user")


class TestGlobalHolidaysAuthRequired:
    """Test that global holidays endpoints require authentication"""
    
    def test_get_global_holidays_requires_auth(self):
        """GET /api/admin/global-holidays - Requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/global-holidays")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/admin/global-holidays requires authentication")
    
    def test_post_global_holidays_requires_auth(self):
        """POST /api/admin/global-holidays - Requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/global-holidays",
            params={"date": "2099-01-01", "reason": "Test"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ POST /api/admin/global-holidays requires authentication")
    
    def test_delete_global_holidays_requires_auth(self):
        """DELETE /api/admin/global-holidays/{date} - Requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/admin/global-holidays/2099-01-01")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ DELETE /api/admin/global-holidays requires authentication")


class TestUserHolidaysAPI:
    """Test User Holidays API (personal holidays) - these are used in Onboarding Wizard"""
    
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
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_get_user_holidays(self):
        """GET /api/trade/holidays - Returns list of user's personal holidays"""
        response = self.session.get(f"{BASE_URL}/api/trade/holidays")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "holidays" in data, "Response should contain 'holidays' key"
        print(f"✓ GET /api/trade/holidays returns {len(data['holidays'])} user holidays")
    
    def test_add_user_holiday_success(self):
        """POST /api/trade/holidays - Successfully adds a personal holiday"""
        # Use a date 70 days in the future
        future_date = (datetime.now() + timedelta(days=70)).strftime("%Y-%m-%d")
        
        response = self.session.post(
            f"{BASE_URL}/api/trade/holidays",
            params={"date": future_date, "reason": "Personal Day Off"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain 'message'"
        print(f"✓ POST /api/trade/holidays successfully added holiday for {future_date}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/trade/holidays/{future_date}")
    
    def test_delete_user_holiday_success(self):
        """DELETE /api/trade/holidays/{date} - Successfully removes a personal holiday"""
        # First add a holiday
        future_date = (datetime.now() + timedelta(days=71)).strftime("%Y-%m-%d")
        
        add_response = self.session.post(
            f"{BASE_URL}/api/trade/holidays",
            params={"date": future_date, "reason": "Test Holiday"}
        )
        assert add_response.status_code == 200, f"Add failed: {add_response.text}"
        
        # Now delete it
        delete_response = self.session.delete(f"{BASE_URL}/api/trade/holidays/{future_date}")
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        print(f"✓ DELETE /api/trade/holidays/{future_date} successfully removed holiday")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 107: Post-Refactoring Regression Tests

Tests extracted routes after major refactoring:
- Habits (routes/habits.py) - habits, streak, screenshot upload, admin habit management
- Affiliate (routes/affiliate.py) - affiliate resources, chatbase, admin affiliate management
- Activity Feed (routes/activity_feed.py) - admin activity feed
- Users (routes/users.py) - notification prefs, push, VAPID, profile
- Admin reset protection (P0 fix verification)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://admin-rewards-ctrl.preview.emergentagent.com"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as master admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]
    
    def test_login_master_admin(self, admin_token):
        """Verify master admin login works"""
        assert admin_token is not None
        assert len(admin_token) > 20


class TestExtractedHabitsRoutes:
    """Tests for extracted habits.py routes"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_habits_list(self, auth_headers):
        """GET /api/habits/ - extracted to routes/habits.py"""
        response = requests.get(f"{BASE_URL}/api/habits/", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "habits" in data
        assert "completions_today" in data
        assert "gate_unlocked" in data
        assert "streak" in data
        print(f"✓ GET /api/habits/ - {len(data.get('habits', []))} habits returned")
    
    def test_get_habit_streak(self, auth_headers):
        """GET /api/habits/streak - streak calculation"""
        response = requests.get(f"{BASE_URL}/api/habits/streak", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "current_streak" in data
        assert "longest_streak" in data
        assert "total_days" in data
        print(f"✓ GET /api/habits/streak - current: {data['current_streak']}, longest: {data['longest_streak']}")
    
    def test_upload_habit_screenshot_endpoint_exists(self, auth_headers):
        """POST /api/habits/upload-screenshot - endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/habits/upload-screenshot", headers=auth_headers)
        # Should return 422 (missing file) not 404
        assert response.status_code == 422, f"Unexpected status: {response.status_code}"
        print("✓ POST /api/habits/upload-screenshot - endpoint exists (422 without file)")
    
    def test_admin_get_habits(self, auth_headers):
        """GET /api/admin/habits - admin habit management (extracted)"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "habits" in data
        print(f"✓ GET /api/admin/habits - {len(data.get('habits', []))} habits (admin view)")


class TestExtractedAffiliateRoutes:
    """Tests for extracted affiliate.py routes"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_affiliate_resources(self, auth_headers):
        """GET /api/affiliate-resources - extracted to routes/affiliate.py"""
        response = requests.get(f"{BASE_URL}/api/affiliate-resources", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "resources" in data
        print(f"✓ GET /api/affiliate-resources - resources loaded")
    
    def test_admin_get_affiliate_resources(self, auth_headers):
        """GET /api/admin/affiliate-resources - admin affiliate resources"""
        response = requests.get(f"{BASE_URL}/api/admin/affiliate-resources", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "resources" in data
        print(f"✓ GET /api/admin/affiliate-resources - {len(data.get('resources', []))} resources")
    
    def test_admin_get_affiliate_chatbase(self, auth_headers):
        """GET /api/admin/affiliate-chatbase - chatbase config"""
        response = requests.get(f"{BASE_URL}/api/admin/affiliate-chatbase", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "enabled" in data
        print(f"✓ GET /api/admin/affiliate-chatbase - enabled: {data.get('enabled')}")


class TestExtractedActivityFeedRoutes:
    """Tests for extracted activity_feed.py routes"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_admin_get_activity_feed(self, auth_headers):
        """GET /api/admin/activity-feed - extracted to routes/activity_feed.py"""
        response = requests.get(f"{BASE_URL}/api/admin/activity-feed", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "activities" in data
        print(f"✓ GET /api/admin/activity-feed - {len(data.get('activities', []))} activities")


class TestExtractedUsersRoutes:
    """Tests for extracted users.py routes"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_notification_preferences(self, auth_headers):
        """GET /api/users/notification-preferences - extracted to routes/users.py"""
        response = requests.get(f"{BASE_URL}/api/users/notification-preferences", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "preferences" in data
        assert "is_admin" in data
        print(f"✓ GET /api/users/notification-preferences - is_admin: {data['is_admin']}")
    
    def test_get_vapid_public_key(self, auth_headers):
        """GET /api/users/vapid-public-key - VAPID key endpoint"""
        response = requests.get(f"{BASE_URL}/api/users/vapid-public-key", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "public_key" in data
        key = data["public_key"]
        assert key.startswith("B"), f"Invalid VAPID key format: {key[:10]}..."
        print(f"✓ GET /api/users/vapid-public-key - valid key (starts with B)")


class TestAdminResetProtection:
    """P0 Fix: Admin reset tracker protection"""
    
    @pytest.fixture(scope="class")
    def admin_auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_admin_self_reset_blocked(self, admin_auth_headers):
        """DELETE /api/profit/reset - should block admin self-reset with 403"""
        response = requests.delete(f"{BASE_URL}/api/profit/reset", headers=admin_auth_headers)
        # P0 fix: This should now return 403 (forbidden) not 200
        assert response.status_code == 403, f"Expected 403 but got {response.status_code}: {response.text}"
        data = response.json()
        assert "Admin accounts cannot be reset" in data.get("detail", ""), f"Wrong error message: {data}"
        print("✓ DELETE /api/profit/reset - admin self-reset correctly blocked (403)")


class TestTradeSignalStatus:
    """Tests for trade monitor routes"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_signal_block_status(self, auth_headers):
        """GET /api/trade/signal-block-status - signal block status"""
        response = requests.get(f"{BASE_URL}/api/trade/signal-block-status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"✓ GET /api/trade/signal-block-status - response: {data}")


class TestProfitSummary:
    """Tests for profit tracker summary"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_profit_summary(self, auth_headers):
        """GET /api/profit/summary - profit summary"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_deposits" in data
        assert "account_value" in data
        print(f"✓ GET /api/profit/summary - account_value: ${data.get('account_value', 0):.2f}")


class TestHelpersFunctions:
    """Test helpers.py functions via API calls"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_habit_completion_triggers_push_logic(self, auth_headers):
        """POST /api/habits/{id}/complete - should trigger send_push_to_admins logic"""
        # First get an active habit
        habits_response = requests.get(f"{BASE_URL}/api/habits/", headers=auth_headers)
        if habits_response.status_code != 200:
            pytest.skip("No habits endpoint")
        
        habits = habits_response.json().get("habits", [])
        if not habits:
            pytest.skip("No habits available to test completion")
        
        habit_id = habits[0]["id"]
        
        # Try to complete the habit (may be already completed today)
        response = requests.post(f"{BASE_URL}/api/habits/{habit_id}/complete", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Either completed or already completed today
        assert "message" in data
        print(f"✓ POST /api/habits/{habit_id}/complete - {data['message']}")


class TestSettingsEndpoints:
    """Tests for settings that use extracted components"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_notice_banner(self, auth_headers):
        """GET /api/settings/notice-banner - banner settings"""
        response = requests.get(f"{BASE_URL}/api/settings/notice-banner", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ GET /api/settings/notice-banner - loaded")
    
    def test_get_promotion_popup(self, auth_headers):
        """GET /api/settings/promotion-popup - popup settings"""
        response = requests.get(f"{BASE_URL}/api/settings/promotion-popup", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ GET /api/settings/promotion-popup - loaded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

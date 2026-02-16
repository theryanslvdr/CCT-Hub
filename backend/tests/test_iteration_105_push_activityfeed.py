# Iteration 105: Push Notification + Activity Feed Tests
# Tests: VAPID key endpoint, Activity feed API, Habit completion with admin push

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
HABIT_ID = "99306d6a-5ac8-4d24-98ed-542aefcabcfd"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    return response.json().get("access_token")


class TestVAPIDKey:
    """Test VAPID public key endpoint"""
    
    def test_get_vapid_public_key_returns_200(self):
        """GET /api/users/vapid-public-key returns 200"""
        response = requests.get(f"{BASE_URL}/api/users/vapid-public-key")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_vapid_public_key_has_valid_format(self):
        """VAPID key should be non-empty and valid format"""
        response = requests.get(f"{BASE_URL}/api/users/vapid-public-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data, "Response should contain 'public_key'"
        key = data["public_key"]
        assert key, "VAPID public key should not be empty"
        assert len(key) > 50, "VAPID key should be sufficiently long"
        # VAPID keys typically start with 'B' (base64url encoded)
        assert key.startswith("B"), f"VAPID key should start with 'B', got: {key[:10]}..."


class TestActivityFeedAPI:
    """Test Activity Feed endpoint"""
    
    def test_activity_feed_requires_auth(self):
        """GET /api/admin/activity-feed requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/activity-feed")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_activity_feed_returns_activities(self, admin_token):
        """GET /api/admin/activity-feed returns activities array with admin auth"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/activity-feed", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "activities" in data, "Response should contain 'activities'"
        assert isinstance(data["activities"], list), "Activities should be a list"
    
    def test_activity_feed_with_since_param(self, admin_token):
        """GET /api/admin/activity-feed?since=<timestamp> supports polling"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Use a timestamp from the past
        since = "2026-01-01T00:00:00"
        response = requests.get(
            f"{BASE_URL}/api/admin/activity-feed",
            params={"since": since},
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "activities" in data, "Response should contain 'activities'"
    
    def test_activity_feed_with_limit_param(self, admin_token):
        """GET /api/admin/activity-feed?limit=5 respects limit"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/activity-feed",
            params={"limit": 5},
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "activities" in data, "Response should contain 'activities'"
        # If there are activities, they should be at most 5
        if len(data["activities"]) > 0:
            assert len(data["activities"]) <= 5, "Should respect limit parameter"


class TestHabitCompletionPush:
    """Test habit completion triggers admin push (no crash)"""
    
    def test_habit_completion_endpoint_exists(self, admin_token):
        """POST /api/habits/{id}/complete endpoint exists and doesn't crash"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Complete the habit (may already be completed today - that's OK)
        response = requests.post(
            f"{BASE_URL}/api/habits/{HABIT_ID}/complete",
            headers=headers
        )
        # Should return 200 (success) or 404 (habit not found) - not 500
        assert response.status_code in [200, 404], f"Expected 200/404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            # Should have message field
            assert "message" in data, "Response should have 'message'"
            # Verify it didn't crash on push notification (no 500)
            print(f"Habit completion response: {data}")
    
    def test_habit_completion_with_unknown_id_returns_404(self, admin_token):
        """POST /api/habits/{unknown_id}/complete returns 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        unknown_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/habits/{unknown_id}/complete",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestPushSubscriptionEndpoints:
    """Test push subscription management endpoints"""
    
    def test_push_subscribe_endpoint_exists(self, admin_token):
        """POST /api/users/push-subscribe endpoint exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Minimal subscription payload (won't actually subscribe but tests endpoint)
        payload = {
            "endpoint": "https://test-endpoint.example.com/push/v1/test",
            "keys": {"p256dh": "test", "auth": "test"}
        }
        response = requests.post(
            f"{BASE_URL}/api/users/push-subscribe",
            json=payload,
            headers=headers
        )
        # Should be 200 (success) - endpoint exists
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

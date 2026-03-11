"""
Iteration 104: Member Activity Feed Feature Tests
Tests for: GET /api/admin/activity-feed endpoint and related functionality
"""
import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://system-restore-lab.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


class TestActivityFeed:
    """Test the admin activity feed endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Authenticate as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        assert token, "No access_token in login response"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
        
    def test_activity_feed_returns_200(self):
        """Test: GET /api/admin/activity-feed returns 200"""
        response = self.session.get(f"{BASE_URL}/api/admin/activity-feed")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "activities" in data, "Response should contain 'activities' key"
        assert isinstance(data["activities"], list), "activities should be a list"
        
        print(f"Activity feed returned {len(data['activities'])} activities")
        
    def test_activity_feed_structure(self):
        """Test: Activity items have correct structure (type, user_name, detail, timestamp)"""
        response = self.session.get(f"{BASE_URL}/api/admin/activity-feed")
        assert response.status_code == 200
        
        data = response.json()
        activities = data["activities"]
        
        if len(activities) > 0:
            activity = activities[0]
            # Verify required fields
            assert "type" in activity, "Activity should have 'type' field"
            assert "user_name" in activity, "Activity should have 'user_name' field"
            assert "detail" in activity, "Activity should have 'detail' field"
            assert "timestamp" in activity, "Activity should have 'timestamp' field"
            
            # Verify type is one of expected values
            valid_types = ["habit_completed", "trade_logged"]
            assert activity["type"] in valid_types, f"Activity type should be one of {valid_types}, got {activity['type']}"
            
            print(f"First activity: type={activity['type']}, user={activity['user_name']}, detail={activity['detail']}")
        else:
            print("No activities in database to verify structure")
            
    def test_activity_feed_since_parameter(self):
        """Test: GET /api/admin/activity-feed?since=<timestamp> filters activities"""
        # First get all activities to determine a timestamp
        response = self.session.get(f"{BASE_URL}/api/admin/activity-feed")
        assert response.status_code == 200
        
        # Use a future timestamp to get no results
        future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        response_filtered = self.session.get(
            f"{BASE_URL}/api/admin/activity-feed",
            params={"since": future_time}
        )
        assert response_filtered.status_code == 200
        
        filtered_data = response_filtered.json()
        assert len(filtered_data["activities"]) == 0, "Future timestamp should return no activities"
        
        print(f"Filter with future timestamp returned 0 activities (expected)")
        
    def test_activity_feed_limit_parameter(self):
        """Test: GET /api/admin/activity-feed?limit=5 respects limit"""
        response = self.session.get(
            f"{BASE_URL}/api/admin/activity-feed",
            params={"limit": 5}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["activities"]) <= 5, f"Limit=5 should return at most 5 activities, got {len(data['activities'])}"
        
        print(f"Limit=5 returned {len(data['activities'])} activities")
        
    def test_activity_feed_requires_admin_auth(self):
        """Test: Activity feed requires admin authentication"""
        # Create a new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.get(f"{BASE_URL}/api/admin/activity-feed")
        # Should return 403 Forbidden or 401 Unauthorized
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print(f"Without auth: status code {response.status_code} (expected)")
        
    def test_activity_feed_has_habit_or_trade_activities(self):
        """Test: Activity feed contains habit_completed or trade_logged activities"""
        response = self.session.get(f"{BASE_URL}/api/admin/activity-feed")
        assert response.status_code == 200
        
        data = response.json()
        activities = data["activities"]
        
        habit_activities = [a for a in activities if a["type"] == "habit_completed"]
        trade_activities = [a for a in activities if a["type"] == "trade_logged"]
        
        print(f"Found {len(habit_activities)} habit completions, {len(trade_activities)} trade logs")
        
        # Per agent context, there should be at least 1 habit_completed and several trade_logged
        if len(activities) > 0:
            assert len(habit_activities) > 0 or len(trade_activities) > 0, "Should have at least habit or trade activities"


class TestActivityFeedPolling:
    """Test polling behavior of activity feed"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Authenticate as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_polling_with_timestamp(self):
        """Test: Polling with a past timestamp returns newer activities only"""
        # Get a timestamp from a year ago
        past_time = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        
        response = self.session.get(
            f"{BASE_URL}/api/admin/activity-feed",
            params={"since": past_time}
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"Polling since {past_time[:10]} returned {len(data['activities'])} activities")
        
        # All returned activities should have timestamp > since
        for activity in data["activities"]:
            if activity["timestamp"]:
                assert activity["timestamp"] > past_time, "Activity timestamp should be after 'since' param"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

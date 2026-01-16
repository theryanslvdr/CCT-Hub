"""
Test Iteration 45: Notification Engine and Reset Tracker Fixes
Tests:
1. WebSocket connection endpoints
2. Notification CRUD endpoints (GET, POST mark-read, DELETE)
3. Reset tracker flow (simplified: warning -> password -> onboarding wizard)
4. Onboarding wizard 'New Trader / Start Fresh' text
"""

import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
    def test_login_master_admin(self):
        """Test master admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Master admin login successful, user_id: {data['user']['id']}")
        return data


class TestNotificationEndpoints:
    """Test notification CRUD endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_notifications(self):
        """Test GET /api/notifications returns notifications for user"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers,
            params={"limit": 50}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "notifications" in data, "Response should have 'notifications' key"
        assert "unread_count" in data, "Response should have 'unread_count' key"
        assert "total" in data, "Response should have 'total' key"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        assert isinstance(data["unread_count"], int), "unread_count should be int"
        assert isinstance(data["total"], int), "total should be int"
        
        print(f"✓ GET /api/notifications - Found {len(data['notifications'])} notifications, {data['unread_count']} unread")
        return data
    
    def test_get_notifications_unread_only(self):
        """Test GET /api/notifications with unread_only filter"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers,
            params={"limit": 50, "unread_only": True}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "notifications" in data
        print(f"✓ GET /api/notifications?unread_only=true - Found {len(data['notifications'])} unread notifications")
    
    def test_mark_notifications_read(self):
        """Test POST /api/notifications/mark-read marks all as read"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/mark-read",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "marked_read" in data, "Response should have 'marked_read' key"
        assert isinstance(data["marked_read"], int), "marked_read should be int"
        
        print(f"✓ POST /api/notifications/mark-read - Marked {data['marked_read']} as read")
        
        # Verify unread count is now 0
        verify_response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers,
            params={"limit": 50}
        )
        verify_data = verify_response.json()
        assert verify_data["unread_count"] == 0, "Unread count should be 0 after marking all read"
        print("✓ Verified unread_count is 0 after mark-read")
    
    def test_clear_notifications(self):
        """Test DELETE /api/notifications clears all notifications"""
        # First get current count
        get_response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers,
            params={"limit": 50}
        )
        initial_count = get_response.json()["total"]
        
        # Clear notifications
        response = requests.delete(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "deleted" in data, "Response should have 'deleted' key"
        assert isinstance(data["deleted"], int), "deleted should be int"
        
        print(f"✓ DELETE /api/notifications - Deleted {data['deleted']} notifications")
        
        # Verify notifications are cleared
        verify_response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers,
            params={"limit": 50}
        )
        verify_data = verify_response.json()
        assert verify_data["total"] == 0, "Total should be 0 after clearing"
        print("✓ Verified total is 0 after clear")


class TestWebSocketEndpoints:
    """Test WebSocket related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_websocket_status_endpoint(self):
        """Test GET /api/ws/status returns connection stats (admin only)"""
        response = requests.get(
            f"{BASE_URL}/api/ws/status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should return connection count info
        assert isinstance(data, dict), "Response should be a dict"
        print(f"✓ GET /api/ws/status - WebSocket status: {data}")


class TestResetTrackerFlow:
    """Test reset tracker flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_verify_password_endpoint(self):
        """Test POST /api/auth/verify-password for reset flow"""
        # Test with correct password
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-password",
            headers=self.headers,
            json={"password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["valid"] == True, "Password should be valid"
        print("✓ POST /api/auth/verify-password - Correct password verified")
        
        # Test with wrong password
        response_wrong = requests.post(
            f"{BASE_URL}/api/auth/verify-password",
            headers=self.headers,
            json={"password": "wrongpassword"}
        )
        assert response_wrong.status_code == 200
        data_wrong = response_wrong.json()
        assert data_wrong["valid"] == False, "Wrong password should be invalid"
        print("✓ POST /api/auth/verify-password - Wrong password rejected")
    
    def test_reset_endpoint_exists(self):
        """Test DELETE /api/profit/reset endpoint exists"""
        # We won't actually reset, just verify the endpoint exists
        # by checking it requires auth
        response_no_auth = requests.delete(f"{BASE_URL}/api/profit/reset")
        assert response_no_auth.status_code in [401, 403], "Should require auth"
        print("✓ DELETE /api/profit/reset - Endpoint exists and requires auth")


class TestOnboardingEndpoints:
    """Test onboarding related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_onboarding_status_endpoint(self):
        """Test GET /api/profit/onboarding-status"""
        response = requests.get(
            f"{BASE_URL}/api/profit/onboarding-status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "onboarding_completed" in data or "has_deposits" in data, "Should have onboarding status fields"
        print(f"✓ GET /api/profit/onboarding-status - Status: {data}")
    
    def test_complete_onboarding_endpoint_exists(self):
        """Test POST /api/profit/complete-onboarding endpoint exists"""
        # Test with minimal data to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/profit/complete-onboarding",
            headers=self.headers,
            json={
                "user_type": "new",
                "starting_balance": 0
            }
        )
        # Should either succeed or return validation error, not 404
        assert response.status_code != 404, "Endpoint should exist"
        print(f"✓ POST /api/profit/complete-onboarding - Endpoint exists (status: {response.status_code})")


class TestProfitSummary:
    """Test profit summary endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_profit_summary(self):
        """Test GET /api/profit/summary returns correct data"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "account_value" in data, "Should have account_value"
        assert "total_deposits" in data, "Should have total_deposits"
        assert "total_actual_profit" in data, "Should have total_actual_profit"
        
        print(f"✓ GET /api/profit/summary - Account value: ${data['account_value']:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test Suite for Iteration 74 - Testing 4 Issues:
1. Trade direction mismatch - signal history should be source of truth for trade history direction
2. Mobile app experience - bottom navigation, pull-to-refresh, haptic feedback
3. Notifications not recording - role-based visibility
4. Email deliverability - send_email function
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for master admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "master_admin"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test that login works with valid credentials"""
        assert auth_token is not None
        assert len(auth_token) > 0


class TestIssue1TradeDirection:
    """Issue #1: Trade direction - when logging a trade, direction should come from active signal"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_active_signal(self, auth_token):
        """Test that active signal endpoint returns signal with direction"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Signal may or may not be active
        if data.get("signal"):
            assert "direction" in data["signal"], "Signal should have direction field"
            assert data["signal"]["direction"] in ["BUY", "SELL"], "Direction should be BUY or SELL"
    
    def test_trade_history_has_direction(self, auth_token):
        """Test that trade history returns trades with direction from signal"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/history?page=1&page_size=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        # Check that trades have direction field
        for trade in data.get("trades", []):
            assert "direction" in trade, "Trade should have direction field"
            assert trade["direction"] in ["BUY", "SELL"], f"Direction should be BUY or SELL, got {trade['direction']}"
    
    def test_trade_history_signal_details(self, auth_token):
        """Test that trade history includes signal details with direction"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/history?page=1&page_size=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Check that trades with signal_id have signal_details
        for trade in data.get("trades", []):
            if trade.get("signal_id"):
                # Signal details may be present
                if trade.get("signal_details"):
                    assert "product" in trade["signal_details"]


class TestIssue3Notifications:
    """Issue #3: Notifications API - role-based visibility"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for master admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_notifications_endpoint_exists(self, auth_token):
        """Test that /api/notifications endpoint exists and returns data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200, f"Notifications endpoint failed: {response.text}"
        data = response.json()
        assert "notifications" in data, "Response should have notifications field"
        assert "unread_count" in data, "Response should have unread_count field"
        assert "is_admin" in data, "Response should have is_admin field"
    
    def test_admin_sees_admin_notifications(self, auth_token):
        """Test that admin users can see admin notifications"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] == True, "Master admin should be identified as admin"
        # Admin should be able to see admin notifications (source: admin)
        # Check if any notifications have source "admin"
        admin_notifications = [n for n in data["notifications"] if n.get("source") == "admin"]
        # It's okay if there are no admin notifications yet, just verify the structure
        print(f"Found {len(admin_notifications)} admin notifications")
    
    def test_notifications_have_source_field(self, auth_token):
        """Test that notifications have source field (personal, community, admin)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        for notification in data.get("notifications", []):
            assert "source" in notification, "Each notification should have source field"
            assert notification["source"] in ["personal", "community", "admin"], \
                f"Source should be personal, community, or admin, got {notification['source']}"
    
    def test_member_notifications_collection_used(self, auth_token):
        """Test that community notifications come from member_notifications collection"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Check for community notifications
        community_notifications = [n for n in data["notifications"] if n.get("source") == "community"]
        print(f"Found {len(community_notifications)} community notifications")
        # Verify community notifications have expected fields
        for n in community_notifications:
            assert "type" in n, "Community notification should have type"
            assert "title" in n, "Community notification should have title"
            assert "message" in n, "Community notification should have message"


class TestIssue4Email:
    """Issue #4: Email - check if send_email function works"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for master admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_send_simple_email_endpoint_exists(self, auth_token):
        """Test that send-email endpoint exists (admin only) - uses query params"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Test with a simple request - may fail due to domain verification but endpoint should exist
        # The endpoint uses query parameters: /api/send-email?to=...&subject=...&body=...
        response = requests.post(
            f"{BASE_URL}/api/send-email",
            headers=headers,
            params={
                "to": "test@example.com",
                "subject": "Test Email",
                "body": "This is a test email"
            }
        )
        # Endpoint should exist - may return 200 (success) or error due to email config
        # But should NOT return 404
        assert response.status_code != 404, "send-email endpoint should exist"
        print(f"Email endpoint response: {response.status_code} - {response.text[:200]}")
    
    def test_email_history_endpoint(self, auth_token):
        """Test that email history endpoint exists (under settings router)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/email-history", headers=headers)
        # Should return 200 or at least not 404
        assert response.status_code != 404, "Email history endpoint should exist"
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Email history should return a list"
    
    def test_test_emailit_endpoint(self, auth_token):
        """Test that test-emailit endpoint exists for testing email config"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/settings/test-emailit",
            headers=headers,
            json={"test_email": "test@example.com"}
        )
        # Endpoint should exist - may fail due to domain verification
        assert response.status_code != 404, "test-emailit endpoint should exist"
        print(f"Test emailit response: {response.status_code} - {response.text[:200]}")


class TestMobileFeatures:
    """Issue #2: Mobile features - verify API endpoints work for mobile app"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_trade_monitor_data_loads(self, auth_token):
        """Test that trade monitor data loads (for pull-to-refresh)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test active signal
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        assert response.status_code == 200
        
        # Test daily summary
        response = requests.get(f"{BASE_URL}/api/trade/daily-summary", headers=headers)
        assert response.status_code == 200
        
        # Test profit summary
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200
        
        # Test streak
        response = requests.get(f"{BASE_URL}/api/trade/streak", headers=headers)
        assert response.status_code == 200
    
    def test_trade_history_pagination(self, auth_token):
        """Test that trade history supports pagination (for mobile scrolling)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/history?page=1&page_size=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data


class TestAdminNotifications:
    """Test admin notification endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for master admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_admin_notifications_endpoint(self, auth_token):
        """Test that admin notifications endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/notifications", headers=headers)
        assert response.status_code == 200, f"Admin notifications failed: {response.text}"
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

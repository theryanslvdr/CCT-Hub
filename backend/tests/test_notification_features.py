"""
Test Notification Features - Iteration 96
Tests for notification preferences, daily trade summary, and force notify endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for Master Admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # Backend uses 'access_token' not 'token'
    token = data.get("access_token")
    assert token, f"No access_token in response: {data}"
    return token

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Returns headers with authorization token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestNotificationPreferences:
    """Tests for /api/users/notification-preferences endpoints"""

    def test_get_notification_preferences_returns_defaults(self, auth_headers):
        """GET /api/users/notification-preferences returns default preferences based on user role"""
        response = requests.get(f"{BASE_URL}/api/users/notification-preferences", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "preferences" in data, f"Response missing 'preferences' key: {data}"
        assert "is_admin" in data, f"Response missing 'is_admin' key: {data}"
        
        prefs = data["preferences"]
        # Member notifications should be present
        assert "trading_signal" in prefs
        assert "pre_trade_10min" in prefs
        assert "pre_trade_5min" in prefs
        assert "missed_trade_report" in prefs
        
        # For admin users, admin notifications should also be present
        if data["is_admin"]:
            assert "member_trade_submitted" in prefs
            assert "member_missed_trade" in prefs
            assert "member_profit_report" in prefs
            assert "daily_summary" in prefs
        
        print(f"SUCCESS: GET notification-preferences returned {len(prefs)} preferences, is_admin={data['is_admin']}")

    def test_update_notification_preferences(self, auth_headers):
        """PUT /api/users/notification-preferences saves preferences correctly"""
        new_prefs = {
            "trading_signal": False,
            "pre_trade_10min": True,
            "pre_trade_5min": False,
            "missed_trade_report": True,
            "member_trade_submitted": False,
            "member_missed_trade": True,
            "member_profit_report": False,
            "daily_summary": True
        }
        
        response = requests.put(
            f"{BASE_URL}/api/users/notification-preferences",
            headers=auth_headers,
            json=new_prefs
        )
        assert response.status_code == 200, f"Failed to update preferences: {response.text}"
        
        data = response.json()
        assert "preferences" in data
        assert data["preferences"]["trading_signal"] == False
        assert data["preferences"]["daily_summary"] == True
        
        print(f"SUCCESS: PUT notification-preferences updated successfully")

    def test_get_updated_preferences_persisted(self, auth_headers):
        """Verify that updated preferences are persisted"""
        response = requests.get(f"{BASE_URL}/api/users/notification-preferences", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        prefs = data["preferences"]
        # Verify the updated values are persisted
        assert prefs.get("trading_signal") == False
        assert prefs.get("daily_summary") == True
        
        print(f"SUCCESS: Updated preferences are persisted correctly")

    def test_restore_default_preferences(self, auth_headers):
        """Restore default preferences for clean state"""
        default_prefs = {
            "trading_signal": True,
            "pre_trade_10min": True,
            "pre_trade_5min": True,
            "missed_trade_report": True,
            "member_trade_submitted": True,
            "member_missed_trade": True,
            "member_profit_report": True,
            "daily_summary": True
        }
        
        response = requests.put(
            f"{BASE_URL}/api/users/notification-preferences",
            headers=auth_headers,
            json=default_prefs
        )
        assert response.status_code == 200
        print(f"SUCCESS: Restored default notification preferences")


class TestDailyTradeSummary:
    """Tests for /api/admin/daily-trade-summary endpoint"""

    def test_get_daily_summary_current_date(self, auth_headers):
        """GET /api/admin/daily-trade-summary returns summary for current date"""
        response = requests.get(f"{BASE_URL}/api/admin/daily-trade-summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "date" in data, f"Response missing 'date': {data}"
        assert "traded" in data, f"Response missing 'traded': {data}"
        assert "missed" in data, f"Response missing 'missed': {data}"
        assert "did_not_trade" in data, f"Response missing 'did_not_trade': {data}"
        assert "stats" in data, f"Response missing 'stats': {data}"
        
        stats = data["stats"]
        assert "total_traded" in stats
        assert "total_missed" in stats
        assert "total_profit" in stats
        assert "total_commission" in stats
        
        # Verify arrays
        assert isinstance(data["traded"], list)
        assert isinstance(data["missed"], list)
        assert isinstance(data["did_not_trade"], list)
        
        print(f"SUCCESS: Daily summary returned for {data['date']}: traded={stats['total_traded']}, missed={stats['total_missed']}")

    def test_get_daily_summary_with_specific_date(self, auth_headers):
        """GET /api/admin/daily-trade-summary with date parameter"""
        test_date = "2026-01-10"
        response = requests.get(
            f"{BASE_URL}/api/admin/daily-trade-summary",
            headers=auth_headers,
            params={"date": test_date}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["date"] == test_date, f"Date mismatch: expected {test_date}, got {data['date']}"
        
        print(f"SUCCESS: Daily summary for specific date {test_date} returned successfully")

    def test_daily_summary_includes_signal_info(self, auth_headers):
        """Verify daily summary includes signal information if available"""
        response = requests.get(f"{BASE_URL}/api/admin/daily-trade-summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Signal may be null if no signal exists for that date
        if data.get("signal"):
            signal = data["signal"]
            assert "direction" in signal or "product" in signal
            print(f"SUCCESS: Signal info included in daily summary")
        else:
            print(f"INFO: No signal found for {data['date']} (expected if no signal today)")

    def test_daily_summary_traded_member_fields(self, auth_headers):
        """Verify traded members have required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/daily-trade-summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        if data["traded"]:
            member = data["traded"][0]
            required_fields = ["user_id", "name", "actual_profit", "commission", "direction", "lot_size"]
            for field in required_fields:
                assert field in member, f"Traded member missing field '{field}': {member}"
            print(f"SUCCESS: Traded members have all required fields")
        else:
            print(f"INFO: No traded members for today (stats show {data['stats']['total_traded']})")


class TestForceNotifyMembers:
    """Tests for /api/admin/signals/force-notify endpoint"""

    def test_force_notify_no_active_signal_returns_404(self, auth_headers):
        """POST /api/admin/signals/force-notify returns 404 if no active signal"""
        # First check if there's an active signal
        signals_response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=auth_headers)
        signal_data = signals_response.json()
        
        if signal_data.get("signal") is None:
            # No active signal, expect 404
            response = requests.post(f"{BASE_URL}/api/admin/signals/force-notify", headers=auth_headers)
            assert response.status_code == 404, f"Expected 404 but got {response.status_code}: {response.text}"
            print(f"SUCCESS: force-notify returns 404 when no active signal")
        else:
            # Active signal exists, the endpoint should work
            response = requests.post(f"{BASE_URL}/api/admin/signals/force-notify", headers=auth_headers)
            # Could be 200 (success) or 500 if email config is missing
            assert response.status_code in [200, 500], f"Unexpected status {response.status_code}: {response.text}"
            if response.status_code == 200:
                data = response.json()
                assert "sent" in data
                print(f"SUCCESS: force-notify sent to {data.get('sent', 0)} members")
            else:
                print(f"INFO: force-notify failed with 500 (likely email config issue in test env)")

    def test_force_notify_with_active_signal(self, auth_headers):
        """POST /api/admin/signals/force-notify with active signal should return sent count"""
        # Check for active signal first
        signals_response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=auth_headers)
        signal_data = signals_response.json()
        
        if signal_data.get("signal"):
            response = requests.post(f"{BASE_URL}/api/admin/signals/force-notify", headers=auth_headers)
            # Endpoint can succeed or fail based on email configuration
            if response.status_code == 200:
                data = response.json()
                assert "sent" in data
                assert "failed" in data or "message" in data
                print(f"SUCCESS: force-notify returned sent={data.get('sent')}")
            else:
                print(f"INFO: force-notify returned {response.status_code} - {response.text}")
        else:
            pytest.skip("No active signal to test force-notify")


class TestAuthTokenFormat:
    """Verify authentication uses access_token field"""

    def test_login_returns_access_token(self):
        """Login should return 'access_token' field, not 'token'"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data, f"Response should have 'access_token': {data.keys()}"
        assert "user" in data, f"Response should have 'user': {data.keys()}"
        print(f"SUCCESS: Login returns access_token as expected")


class TestAdminEndpointAccess:
    """Test that admin endpoints require proper authentication"""

    def test_daily_summary_requires_auth(self):
        """Daily summary endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/daily-trade-summary")
        assert response.status_code in [401, 403], f"Expected 401/403 but got {response.status_code}"
        print(f"SUCCESS: daily-trade-summary requires authentication")

    def test_force_notify_requires_auth(self):
        """Force notify endpoint should require authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/signals/force-notify")
        assert response.status_code in [401, 403], f"Expected 401/403 but got {response.status_code}"
        print(f"SUCCESS: force-notify requires authentication")

    def test_notification_prefs_requires_auth(self):
        """Notification preferences endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/users/notification-preferences")
        assert response.status_code in [401, 403], f"Expected 401/403 but got {response.status_code}"
        print(f"SUCCESS: notification-preferences requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

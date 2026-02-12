"""
Iteration 98: Comprehensive Final Testing
Features tested:
1. GET /api/profit/summary - returns account_value
2. GET/PUT /api/users/notification-preferences - CRUD works
3. GET /api/users/vapid-public-key - returns key (no auth)
4. POST/DELETE /api/users/push-subscribe - works (auth required)
5. GET /api/admin/daily-trade-summary - returns summary with stats
6. POST /api/admin/push-notify-all - works (may fail delivery to test endpoints)
7. GET /api/settings/manifest.json - returns dynamic manifest
8. POST /api/trade/did-not-trade?date=YYYY-MM-DD - uses correct param name
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token - shared across all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code != 200:
        pytest.skip(f"Could not authenticate: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("access_token")
    assert token, "Should receive access_token"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Auth headers for requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestProfitSummary:
    """Test profit summary endpoint returns account_value"""
    
    def test_profit_summary_returns_account_value(self, auth_headers):
        """GET /api/profit/summary should return account_value in response"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "account_value" in data, "Response should contain 'account_value'"
        assert isinstance(data["account_value"], (int, float)), "account_value should be numeric"
        
        # Verify other expected fields
        assert "total_deposits" in data
        assert "total_actual_profit" in data
        assert "total_trades" in data
        
        print(f"Profit summary: account_value=${data['account_value']:.2f}, trades={data['total_trades']}")


class TestNotificationPreferences:
    """Test notification preferences GET/PUT endpoints"""
    
    def test_get_notification_preferences(self, auth_headers):
        """GET /api/users/notification-preferences should return preferences"""
        response = requests.get(
            f"{BASE_URL}/api/users/notification-preferences",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "preferences" in data, "Response should contain 'preferences'"
        assert "is_admin" in data, "Response should contain 'is_admin'"
        
        prefs = data["preferences"]
        
        # Member notification keys
        member_keys = ["trading_signal", "pre_trade_10min", "pre_trade_5min", "missed_trade_report"]
        for key in member_keys:
            assert key in prefs, f"Preferences should contain '{key}'"
        
        # Admin-only keys (since we're testing with admin account)
        if data["is_admin"]:
            admin_keys = ["member_trade_submitted", "member_missed_trade", "member_profit_report", "daily_summary"]
            for key in admin_keys:
                assert key in prefs, f"Admin preferences should contain '{key}'"
        
        print(f"Notification preferences retrieved. is_admin={data['is_admin']}, keys={len(prefs)}")
    
    def test_update_notification_preferences(self, auth_headers):
        """PUT /api/users/notification-preferences should update preferences"""
        # Get current preferences first
        get_response = requests.get(
            f"{BASE_URL}/api/users/notification-preferences",
            headers=auth_headers
        )
        original_prefs = get_response.json().get("preferences", {})
        
        # Update with new values
        new_prefs = {
            "trading_signal": True,
            "pre_trade_10min": True,
            "pre_trade_5min": True,
            "missed_trade_report": True,
            "member_trade_submitted": False,  # Toggle this
            "member_missed_trade": True,
            "member_profit_report": True,
            "daily_summary": True,
        }
        
        response = requests.put(
            f"{BASE_URL}/api/users/notification-preferences",
            json=new_prefs,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain success message"
        assert "preferences" in data, "Response should return updated preferences"
        
        # Verify the update took effect
        verify_response = requests.get(
            f"{BASE_URL}/api/users/notification-preferences",
            headers=auth_headers
        )
        updated = verify_response.json().get("preferences", {})
        assert updated.get("member_trade_submitted") == False, "Preference should be updated"
        
        # Restore original (set back to True)
        restore_prefs = original_prefs.copy()
        restore_prefs["member_trade_submitted"] = True
        requests.put(
            f"{BASE_URL}/api/users/notification-preferences",
            json=restore_prefs,
            headers=auth_headers
        )
        
        print(f"Notification preferences updated and verified")


class TestVapidPublicKey:
    """Test VAPID public key endpoint (no auth required)"""
    
    def test_get_vapid_public_key_returns_key(self):
        """GET /api/users/vapid-public-key should return VAPID public key without auth"""
        response = requests.get(f"{BASE_URL}/api/users/vapid-public-key")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "public_key" in data, "Response should contain 'public_key' field"
        assert data["public_key"] != "", "VAPID public key should not be empty"
        assert data["public_key"].startswith("B"), f"VAPID key should start with 'B', got: {data['public_key'][:10]}"
        
        print(f"VAPID public key retrieved: {data['public_key'][:20]}...")


class TestPushSubscription:
    """Test push subscription endpoints"""
    
    def test_push_subscribe_saves_subscription(self, auth_headers):
        """POST /api/users/push-subscribe should save push subscription"""
        test_subscription = {
            "endpoint": f"https://test-push-service.example.com/{uuid.uuid4()}",
            "keys": {
                "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
                "auth": "tBHItJI5svbpez7KI4CCXg"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/users/push-subscribe",
            json=test_subscription,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain success message"
        print(f"Push subscription saved: {data['message']}")
    
    def test_push_unsubscribe_removes_subscription(self, auth_headers):
        """DELETE /api/users/push-subscribe should remove push subscription"""
        test_subscription = {
            "endpoint": f"https://test-push-service.example.com/delete-{uuid.uuid4()}",
            "keys": {
                "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
                "auth": "tBHItJI5svbpez7KI4CCXg"
            }
        }
        
        # Create first
        create_response = requests.post(
            f"{BASE_URL}/api/users/push-subscribe",
            json=test_subscription,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        
        # Now delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/users/push-subscribe",
            json=test_subscription,
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert "message" in data
        print(f"Push subscription removed: {data['message']}")


class TestDailyTradeSummary:
    """Test daily trade summary endpoint"""
    
    def test_get_daily_trade_summary_returns_stats(self, auth_headers):
        """GET /api/admin/daily-trade-summary should return summary with stats"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/daily-trade-summary",
            params={"date": today},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Required fields
        assert "date" in data, "Response should contain 'date'"
        assert "traded" in data, "Response should contain 'traded' array"
        assert "missed" in data, "Response should contain 'missed' array"
        assert "did_not_trade" in data, "Response should contain 'did_not_trade' array"
        assert "stats" in data, "Response should contain 'stats'"
        
        # Stats structure
        stats = data["stats"]
        assert "total_traded" in stats
        assert "total_missed" in stats
        assert "total_profit" in stats
        assert "total_commission" in stats
        
        print(f"Daily summary: traded={stats['total_traded']}, missed={stats['total_missed']}, profit=${stats['total_profit']:.2f}")
    
    def test_daily_trade_summary_requires_admin(self):
        """GET /api/admin/daily-trade-summary without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/admin/daily-trade-summary")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"Correctly rejected unauthenticated request: {response.status_code}")


class TestPushNotifyAll:
    """Test admin push notify all endpoint"""
    
    def test_push_notify_all_works_for_admin(self, auth_headers):
        """POST /api/admin/push-notify-all should work for admin users"""
        notification_data = {
            "title": "Test Notification",
            "message": "This is a test notification from backend tests",
            "url": "/trade-monitor",
            "tag": "test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/push-notify-all",
            json=notification_data,
            headers=auth_headers
        )
        
        # Should succeed even if no subscribers (returns sent=0)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "sent" in data, "Response should contain 'sent' count"
        assert "failed" in data, "Response should contain 'failed' count"
        
        print(f"Push notify all: sent={data['sent']}, failed={data['failed']}")


class TestDynamicManifest:
    """Test dynamic PWA manifest endpoint"""
    
    def test_get_manifest_json_returns_valid_manifest(self):
        """GET /api/settings/manifest.json should return valid PWA manifest"""
        response = requests.get(f"{BASE_URL}/api/settings/manifest.json")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        manifest = response.json()
        
        # Required PWA manifest fields
        assert "name" in manifest
        assert "short_name" in manifest
        assert "icons" in manifest
        assert "start_url" in manifest
        assert "display" in manifest
        
        # Icons array
        assert isinstance(manifest["icons"], list)
        assert len(manifest["icons"]) >= 1
        
        print(f"Manifest validated: name={manifest['short_name']}, icons={len(manifest['icons'])}")


class TestDidNotTrade:
    """Test did-not-trade endpoint with date query param"""
    
    def test_did_not_trade_endpoint_uses_date_param(self, auth_headers):
        """POST /api/trade/did-not-trade?date=YYYY-MM-DD should use date query param"""
        # Use a past date that is unlikely to have a trade
        past_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/trade/did-not-trade",
            params={"date": past_date},
            headers=auth_headers
        )
        
        # May get 400 if trade already exists, which is also valid
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data or "message" in data
            print(f"Did not trade entry created for {past_date}")
        else:
            # 400 means trade exists or other validation - endpoint works
            print(f"Did not trade returned 400 (trade exists or validation): {response.text[:100]}")
    
    def test_did_not_trade_rejects_future_date(self, auth_headers):
        """POST /api/trade/did-not-trade should reject future dates"""
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/trade/did-not-trade",
            params={"date": future_date},
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400 for future date, got {response.status_code}"
        print(f"Correctly rejected future date: {response.status_code}")


class TestPwaIconUpload:
    """Test PWA icon upload endpoint exists"""
    
    def test_upload_pwa_icon_endpoint_exists(self, auth_headers):
        """POST /api/settings/upload-pwa-icon endpoint should exist"""
        # Test without file to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/settings/upload-pwa-icon",
            headers=auth_headers
        )
        
        # Should return 422 (validation error - no file) not 404
        assert response.status_code in [422, 400], f"Expected 422/400 (missing file), got {response.status_code}"
        print(f"PWA icon upload endpoint exists, returns {response.status_code} when no file provided")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test Push Notification Endpoints and Manifest for Iteration 97
Features tested:
- GET /api/users/vapid-public-key - returns VAPID public key (no auth required)
- POST /api/users/push-subscribe - saves push subscription (requires auth)
- DELETE /api/users/push-subscribe - removes push subscription (requires auth)
- POST /api/admin/push-notify-all - sends push to all subscribed devices (requires admin)
- GET /api/settings/manifest.json - returns dynamic PWA manifest (no auth required)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestVapidPublicKey:
    """Test VAPID public key endpoint (no auth required)"""
    
    def test_get_vapid_public_key_returns_key(self):
        """GET /api/users/vapid-public-key should return VAPID public key without auth"""
        response = requests.get(f"{BASE_URL}/api/users/vapid-public-key")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "public_key" in data, "Response should contain 'public_key' field"
        
        # VAPID keys start with 'B' and are base64url encoded
        assert data["public_key"] != "", "VAPID public key should not be empty"
        assert data["public_key"].startswith("B"), f"VAPID key should start with 'B', got: {data['public_key'][:10]}"
        print(f"VAPID public key retrieved: {data['public_key'][:20]}...")


class TestDynamicManifest:
    """Test dynamic PWA manifest endpoint (no auth required)"""
    
    def test_get_manifest_json_returns_valid_manifest(self):
        """GET /api/settings/manifest.json should return valid PWA manifest"""
        response = requests.get(f"{BASE_URL}/api/settings/manifest.json")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check content type
        content_type = response.headers.get('content-type', '')
        assert 'application/manifest+json' in content_type or 'application/json' in content_type, \
            f"Expected manifest+json content type, got: {content_type}"
        
        manifest = response.json()
        
        # Required PWA manifest fields
        assert "name" in manifest, "Manifest should have 'name'"
        assert "short_name" in manifest, "Manifest should have 'short_name'"
        assert "icons" in manifest, "Manifest should have 'icons'"
        assert "start_url" in manifest, "Manifest should have 'start_url'"
        assert "display" in manifest, "Manifest should have 'display'"
        
        # Check icons array
        assert isinstance(manifest["icons"], list), "Icons should be an array"
        assert len(manifest["icons"]) >= 1, "Should have at least one icon"
        
        # Check first icon has required fields
        icon = manifest["icons"][0]
        assert "src" in icon, "Icon should have 'src'"
        assert "sizes" in icon, "Icon should have 'sizes'"
        
        print(f"Manifest validated: name={manifest['name']}, icons={len(manifest['icons'])}")


class TestPushSubscriptionEndpoints:
    """Test push subscription endpoints (require auth)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Could not authenticate: {response.status_code} - {response.text}")
        
        token = response.json().get("access_token")
        assert token, "Should receive access_token"
        return token
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Auth headers for requests"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_push_subscribe_saves_subscription(self, auth_headers):
        """POST /api/users/push-subscribe should save push subscription"""
        # Create a mock push subscription
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
        
        # Store for cleanup
        self.test_endpoint = test_subscription["endpoint"]
        self.test_keys = test_subscription["keys"]
    
    def test_push_unsubscribe_removes_subscription(self, auth_headers):
        """DELETE /api/users/push-subscribe should remove push subscription"""
        # First create a subscription to delete
        test_subscription = {
            "endpoint": f"https://test-push-service.example.com/delete-test-{uuid.uuid4()}",
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
        assert create_response.status_code == 200, f"Failed to create subscription: {create_response.text}"
        
        # Now delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/users/push-subscribe",
            json=test_subscription,
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert "message" in data, "Response should contain success message"
        print(f"Push subscription removed: {data['message']}")
    
    def test_push_subscribe_without_auth_fails(self):
        """POST /api/users/push-subscribe without auth should fail"""
        test_subscription = {
            "endpoint": "https://test.example.com/no-auth",
            "keys": {"p256dh": "test", "auth": "test"}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/users/push-subscribe",
            json=test_subscription
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"Correctly rejected unauthenticated push-subscribe: {response.status_code}")


class TestAdminPushNotifyAll:
    """Test admin push notification endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Could not authenticate: {response.status_code}")
        
        return response.json().get("access_token")
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        """Admin auth headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_push_notify_all_works_for_admin(self, admin_headers):
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
            headers=admin_headers
        )
        
        # Should succeed even if no subscribers (returns sent=0)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "sent" in data, "Response should contain 'sent' count"
        assert "failed" in data, "Response should contain 'failed' count"
        assert "message" in data, "Response should contain 'message'"
        
        print(f"Push notify all result: sent={data['sent']}, failed={data['failed']}")
    
    def test_push_notify_all_without_auth_fails(self):
        """POST /api/admin/push-notify-all without auth should fail"""
        response = requests.post(
            f"{BASE_URL}/api/admin/push-notify-all",
            json={"title": "Test", "message": "Test"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"Correctly rejected unauthenticated push-notify-all: {response.status_code}")


class TestPwaIconUpload:
    """Test PWA icon upload endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Could not authenticate: {response.status_code}")
        
        return response.json().get("access_token")
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        """Admin auth headers"""
        return {"Authorization": f"Bearer {admin_token}"}
    
    def test_upload_pwa_icon_endpoint_exists(self, admin_headers):
        """POST /api/settings/upload-pwa-icon endpoint should exist"""
        # Test without file to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/settings/upload-pwa-icon",
            headers=admin_headers
        )
        
        # Should return 422 (validation error - no file) not 404
        # 422 means endpoint exists but requires file
        assert response.status_code in [422, 400], f"Expected 422/400 (missing file), got {response.status_code}"
        print(f"PWA icon upload endpoint exists, returns {response.status_code} when no file provided")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

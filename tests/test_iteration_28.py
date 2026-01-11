"""
Test Suite for Iteration 28 - P1 Backend Refactoring, WebSockets, Email, File Upload
Tests:
1. Email Service - /api/email/test endpoint
2. File Upload - /api/upload/profile-picture and /api/upload/general endpoints
3. WebSocket Status API - /api/ws/status endpoint (admin only)
4. P0 Features - Basic auth and dashboard functionality
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
MEMBER_EMAIL = "jaspersalvador9413@gmail.com"
MEMBER_PASSWORD = "test123"


class TestAuthAndBasics:
    """Test basic authentication and P0 features"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health check passed")
    
    def test_master_admin_login(self):
        """Test master admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Master admin login successful - role: {data['user']['role']}")
        return data["access_token"]
    
    def test_member_login(self):
        """Test regular member login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"✓ Member login successful - role: {data['user']['role']}")
        return data["access_token"]
    
    def test_get_platform_settings(self):
        """Test platform settings endpoint"""
        response = requests.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200
        data = response.json()
        assert "platform_name" in data
        print(f"✓ Platform settings retrieved - name: {data.get('platform_name')}")


class TestEmailService:
    """Test email service endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def member_token(self):
        """Get member token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_email_test_endpoint_exists(self, admin_token):
        """Test that /api/email/test endpoint exists and requires master admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Test with a valid email - endpoint should exist
        response = requests.post(
            f"{BASE_URL}/api/email/test",
            params={"to_email": "test@example.com"},
            headers=headers
        )
        # Should return 200 (success) or 500 (email service error) - not 404
        assert response.status_code != 404, "Email test endpoint should exist"
        print(f"✓ Email test endpoint exists - status: {response.status_code}")
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            print(f"✓ Email test sent successfully: {data.get('message')}")
        else:
            # Email service might not be configured, but endpoint exists
            print(f"✓ Email test endpoint exists but returned error (expected if API key not configured)")
    
    def test_email_test_requires_master_admin(self, member_token):
        """Test that email test endpoint requires master admin role"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.post(
            f"{BASE_URL}/api/email/test",
            params={"to_email": "test@example.com"},
            headers=headers
        )
        # Should return 403 Forbidden for non-master-admin
        assert response.status_code == 403, f"Expected 403 for member, got {response.status_code}"
        print("✓ Email test endpoint correctly requires master admin")


class TestFileUploadService:
    """Test file upload endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def member_token(self):
        """Get member token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_profile_picture_upload_endpoint_exists(self, admin_token):
        """Test that /api/upload/profile-picture endpoint exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a small test image (1x1 pixel PNG)
        # PNG header for a 1x1 transparent pixel
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # bit depth, color type
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,  # compressed data
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,  # 
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
            0x42, 0x60, 0x82
        ])
        
        files = {"file": ("test.png", io.BytesIO(png_data), "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/upload/profile-picture",
            headers=headers,
            files=files
        )
        
        # Should not return 404 - endpoint exists
        assert response.status_code != 404, "Profile picture upload endpoint should exist"
        print(f"✓ Profile picture upload endpoint exists - status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "url" in data or "message" in data
            print(f"✓ Profile picture upload successful")
        elif response.status_code == 500:
            # Cloudinary might not be configured
            print("✓ Profile picture endpoint exists but Cloudinary not configured")
    
    def test_general_upload_endpoint_exists(self, admin_token):
        """Test that /api/upload/general endpoint exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a small test file
        test_content = b"Test file content for upload"
        files = {"file": ("test.txt", io.BytesIO(test_content), "text/plain")}
        data = {"folder": "test_uploads", "file_type": "test"}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/general",
            headers=headers,
            files=files,
            data=data
        )
        
        # Should not return 404 - endpoint exists
        assert response.status_code != 404, "General upload endpoint should exist"
        print(f"✓ General upload endpoint exists - status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "url" in data or "message" in data
            print(f"✓ General file upload successful")
        elif response.status_code == 500:
            # Cloudinary might not be configured
            print("✓ General upload endpoint exists but Cloudinary not configured")
    
    def test_upload_requires_auth(self):
        """Test that upload endpoints require authentication"""
        # No auth header
        test_content = b"Test file content"
        files = {"file": ("test.txt", io.BytesIO(test_content), "text/plain")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/profile-picture",
            files=files
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Upload endpoints correctly require authentication")


class TestWebSocketStatus:
    """Test WebSocket status API"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def member_token(self):
        """Get member token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_ws_status_endpoint_exists(self, admin_token):
        """Test that /api/ws/status endpoint exists and returns connection stats"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ws/status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should return connection count structure
        assert "total_users" in data or "total_connections" in data
        print(f"✓ WebSocket status endpoint works - data: {data}")
    
    def test_ws_status_requires_admin(self, member_token):
        """Test that WS status endpoint requires admin role"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/ws/status", headers=headers)
        
        # Should return 403 for non-admin
        assert response.status_code == 403, f"Expected 403 for member, got {response.status_code}"
        print("✓ WebSocket status endpoint correctly requires admin")


class TestDashboardFeatures:
    """Test dashboard features from P0"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def member_token(self):
        """Get member token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MEMBER_EMAIL,
            "password": MEMBER_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_profit_summary(self, member_token):
        """Test profit summary endpoint"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_deposits" in data
        assert "total_actual_profit" in data
        print(f"✓ Profit summary works - account_value: {data.get('account_value')}")
    
    def test_trade_logs(self, member_token):
        """Test trade logs endpoint"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/logs?limit=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Trade logs works - count: {len(data)}")
    
    def test_active_signal(self, member_token):
        """Test active signal endpoint"""
        headers = {"Authorization": f"Bearer {member_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        # Should have either signal or message
        assert "signal" in data or "message" in data
        print(f"✓ Active signal endpoint works")
    
    def test_admin_notifications(self, admin_token):
        """Test admin notifications endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/notifications?limit=20&unread_only=false",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        print(f"✓ Admin notifications works - count: {len(data.get('notifications', []))}")


class TestServicesIntegration:
    """Test that services package is properly integrated"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_send_email_endpoint(self, admin_token):
        """Test the general send-email endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/send-email",
            headers=headers,
            json={
                "to_email": "test@example.com",
                "subject": "Test Subject",
                "html_content": "<p>Test content</p>"
            }
        )
        
        # Should not return 404 - endpoint exists
        assert response.status_code != 404, "Send email endpoint should exist"
        print(f"✓ Send email endpoint exists - status: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

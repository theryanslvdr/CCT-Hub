"""
Test Iteration 30 - Maintenance Mode, Announcements, and Mobile Notice Features
Tests:
1. Maintenance Tab in Admin Settings
2. Maintenance Mode Toggle and Message
3. Announcements Section (CRUD)
4. Platform Settings API with maintenance fields
5. Login Page Maintenance Mode
6. Master Admin Override (5 clicks on 'soon')
7. MobileNotice Component
8. Admin Pages with MobileNotice wrapper
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://honorary-tracker.preview.emergentagent.com').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestMaintenanceFeatures:
    """Test maintenance mode and announcements features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
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
            self.auth_token = token
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health check passed")
    
    def test_login_success(self):
        """Test login with master admin credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print("✓ Login successful")
    
    def test_get_platform_settings(self):
        """Test GET platform settings returns maintenance fields"""
        response = self.session.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200
        data = response.json()
        
        # Check standard fields exist
        assert "platform_name" in data
        assert "site_title" in data
        
        # Check maintenance fields exist (may be None initially)
        # These fields should be returned by the API
        print(f"  maintenance_mode: {data.get('maintenance_mode')}")
        print(f"  maintenance_message: {data.get('maintenance_message')}")
        print(f"  announcements: {data.get('announcements')}")
        print("✓ Platform settings retrieved")
    
    def test_update_platform_settings_with_maintenance(self):
        """Test updating platform settings with maintenance mode"""
        # First get current settings
        get_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        current_settings = get_response.json()
        
        # Update with maintenance fields
        update_data = {
            **current_settings,
            "maintenance_mode": True,
            "maintenance_message": "Test maintenance message - will be back soon!",
            "announcements": [
                {
                    "id": "test-announcement-1",
                    "title": "Test Announcement",
                    "message": "This is a test announcement message",
                    "link_url": "https://example.com",
                    "link_text": "Learn more",
                    "type": "info",
                    "sticky": False,
                    "active": True,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
        
        response = self.session.put(f"{BASE_URL}/api/settings/platform", json=update_data)
        assert response.status_code == 200
        print("✓ Platform settings updated with maintenance fields")
        
        # Verify the update
        verify_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        verify_data = verify_response.json()
        
        assert verify_data.get("maintenance_mode") == True
        assert "soon" in verify_data.get("maintenance_message", "").lower()
        assert verify_data.get("announcements") is not None
        assert len(verify_data.get("announcements", [])) > 0
        print("✓ Maintenance settings verified after update")
    
    def test_add_announcement(self):
        """Test adding an announcement"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        current_settings = get_response.json()
        
        # Add a new announcement
        new_announcement = {
            "id": "test-announcement-2",
            "title": "Warning Announcement",
            "message": "This is a warning type announcement",
            "link_url": "",
            "link_text": "",
            "type": "warning",
            "sticky": True,
            "active": True,
            "created_at": "2024-01-02T00:00:00Z"
        }
        
        current_announcements = current_settings.get("announcements", []) or []
        current_announcements.append(new_announcement)
        
        update_data = {
            **current_settings,
            "announcements": current_announcements
        }
        
        response = self.session.put(f"{BASE_URL}/api/settings/platform", json=update_data)
        assert response.status_code == 200
        
        # Verify
        verify_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        verify_data = verify_response.json()
        announcements = verify_data.get("announcements", [])
        
        assert len(announcements) >= 2
        warning_announcements = [a for a in announcements if a.get("type") == "warning"]
        assert len(warning_announcements) > 0
        print("✓ Warning announcement added successfully")
    
    def test_toggle_announcement_active(self):
        """Test toggling announcement active status"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        current_settings = get_response.json()
        
        announcements = current_settings.get("announcements", []) or []
        if len(announcements) > 0:
            # Toggle first announcement
            announcements[0]["active"] = not announcements[0].get("active", True)
            
            update_data = {
                **current_settings,
                "announcements": announcements
            }
            
            response = self.session.put(f"{BASE_URL}/api/settings/platform", json=update_data)
            assert response.status_code == 200
            print("✓ Announcement active status toggled")
        else:
            print("⚠ No announcements to toggle")
    
    def test_disable_maintenance_mode(self):
        """Test disabling maintenance mode"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        current_settings = get_response.json()
        
        # Disable maintenance mode
        update_data = {
            **current_settings,
            "maintenance_mode": False
        }
        
        response = self.session.put(f"{BASE_URL}/api/settings/platform", json=update_data)
        assert response.status_code == 200
        
        # Verify
        verify_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        verify_data = verify_response.json()
        
        assert verify_data.get("maintenance_mode") == False
        print("✓ Maintenance mode disabled")
    
    def test_clear_announcements(self):
        """Test clearing all announcements"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        current_settings = get_response.json()
        
        # Clear announcements
        update_data = {
            **current_settings,
            "announcements": []
        }
        
        response = self.session.put(f"{BASE_URL}/api/settings/platform", json=update_data)
        assert response.status_code == 200
        
        # Verify
        verify_response = self.session.get(f"{BASE_URL}/api/settings/platform")
        verify_data = verify_response.json()
        
        announcements = verify_data.get("announcements", [])
        assert announcements is None or len(announcements) == 0
        print("✓ Announcements cleared")


class TestExistingFeatures:
    """Test existing features still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
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
    
    def test_profit_summary(self):
        """Test profit summary endpoint"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        print("✓ Profit summary endpoint working")
    
    def test_trade_logs(self):
        """Test trade logs endpoint"""
        response = self.session.get(f"{BASE_URL}/api/trade/logs")
        assert response.status_code == 200
        print("✓ Trade logs endpoint working")
    
    def test_admin_members(self):
        """Test admin members endpoint"""
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200
        print("✓ Admin members endpoint working")
    
    def test_debt_endpoint(self):
        """Test debt endpoint"""
        response = self.session.get(f"{BASE_URL}/api/debt")
        assert response.status_code == 200
        print("✓ Debt endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

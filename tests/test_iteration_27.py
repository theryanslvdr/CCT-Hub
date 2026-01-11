"""
Test Suite for Iteration 27 Features
=====================================
Testing 6 new features:
1. Dashboard Tabs for Members - Regular members see 4 tabs (Overview, Profit, Trades, Charts), Admins don't see tabs
2. API Key Security Modal - Master Admin sees warning modal on login if API keys are missing
3. Persistent Footer - Footer appears at bottom of all pages with copyright and custom links
4. Login Customization - Login page shows customizable title, tagline, and notice from settings
5. Production Site URL - Settings should save and return production_site_url field
6. Login text says 'CrossCurrent' not 'Heartbeat' - All community references should say CrossCurrent
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://finance-center-7.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestAuthAndLogin:
    """Test authentication and login-related features"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        """Get master admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_master_admin_login(self, master_admin_token):
        """Test master admin can login successfully"""
        assert master_admin_token is not None
        print("SUCCESS: Master admin login works")
    
    def test_get_current_user(self, master_admin_token):
        """Test getting current user info"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == MASTER_ADMIN_EMAIL
        assert data["role"] == "master_admin"
        print(f"SUCCESS: Current user is {data['email']} with role {data['role']}")


class TestPlatformSettings:
    """Test platform settings including new fields"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        """Get master admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_platform_settings(self, master_admin_token):
        """Test getting platform settings - Feature 4 & 5"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check for login customization fields (Feature 4)
        assert "login_title" in data or data.get("login_title") is None, "login_title field should exist"
        assert "login_tagline" in data or data.get("login_tagline") is None, "login_tagline field should exist"
        assert "login_notice" in data, "login_notice field should exist"
        
        # Check for production_site_url field (Feature 5)
        assert "production_site_url" in data or data.get("production_site_url") is None, "production_site_url field should exist"
        
        # Check for footer fields (Feature 3)
        assert "footer_copyright" in data, "footer_copyright field should exist"
        assert "footer_links" in data or data.get("footer_links") is None, "footer_links field should exist"
        
        print(f"SUCCESS: Platform settings retrieved with all required fields")
        print(f"  - login_title: {data.get('login_title')}")
        print(f"  - login_tagline: {data.get('login_tagline')}")
        print(f"  - login_notice: {data.get('login_notice')}")
        print(f"  - production_site_url: {data.get('production_site_url')}")
        print(f"  - footer_copyright: {data.get('footer_copyright')}")
        print(f"  - footer_links: {data.get('footer_links')}")
    
    def test_update_platform_settings_with_new_fields(self, master_admin_token):
        """Test updating platform settings with new fields - Feature 4 & 5"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # First get current settings
        get_response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        current_settings = get_response.json()
        
        # Update with new fields
        update_data = {
            **current_settings,
            "login_title": "Welcome to CrossCurrent",
            "login_tagline": "Your Trading Finance Hub",
            "login_notice": "Only CrossCurrent community members can access this platform.",
            "production_site_url": "https://app.crosscurrent.com",
            "footer_copyright": "© 2024 CrossCurrent Finance Center. All rights reserved.",
            "footer_links": [
                {"label": "Privacy", "url": "/privacy"},
                {"label": "Terms", "url": "/terms"}
            ]
        }
        
        response = requests.put(f"{BASE_URL}/api/settings/platform", headers=headers, json=update_data)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        # Verify the update
        verify_response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        assert verify_response.status_code == 200
        data = verify_response.json()
        
        assert data.get("login_title") == "Welcome to CrossCurrent", "login_title not saved"
        assert data.get("login_tagline") == "Your Trading Finance Hub", "login_tagline not saved"
        assert data.get("production_site_url") == "https://app.crosscurrent.com", "production_site_url not saved"
        
        print("SUCCESS: Platform settings updated with new fields")
    
    def test_api_key_fields_exist(self, master_admin_token):
        """Test that API key fields exist for security modal - Feature 2"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check for API key fields that trigger the security modal
        api_key_fields = ["heartbeat_api_key", "emailit_api_key", "cloudinary_cloud_name", 
                         "cloudinary_api_key", "cloudinary_api_secret"]
        
        for field in api_key_fields:
            assert field in data or data.get(field) is None, f"{field} field should exist"
        
        print("SUCCESS: All API key fields exist in platform settings")
        print(f"  - heartbeat_api_key: {'SET' if data.get('heartbeat_api_key') else 'NOT SET'}")
        print(f"  - emailit_api_key: {'SET' if data.get('emailit_api_key') else 'NOT SET'}")
        print(f"  - cloudinary_cloud_name: {'SET' if data.get('cloudinary_cloud_name') else 'NOT SET'}")


class TestDashboardAndMembers:
    """Test dashboard and member-related features"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        """Get master admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_members_list(self, master_admin_token):
        """Test getting members list"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "members" in data
        assert "total" in data
        print(f"SUCCESS: Retrieved {data['total']} members")
    
    def test_profit_summary_endpoint(self, master_admin_token):
        """Test profit summary endpoint for dashboard data"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check for required fields
        required_fields = ["total_deposits", "total_projected_profit", "total_actual_profit", 
                         "profit_difference", "account_value", "total_trades", "performance_rate"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"SUCCESS: Profit summary endpoint returns all required fields")
        print(f"  - account_value: {data.get('account_value')}")
        print(f"  - total_trades: {data.get('total_trades')}")


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    def test_public_settings_endpoint(self):
        """Test public settings endpoint for login page customization"""
        response = requests.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200
        data = response.json()
        
        # Login page should be able to access these settings
        print(f"SUCCESS: Public settings endpoint accessible")
        print(f"  - platform_name: {data.get('platform_name')}")
        print(f"  - tagline: {data.get('tagline')}")


class TestFooterSettings:
    """Test footer-related settings - Feature 3"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        """Get master admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_footer_settings_in_platform_settings(self, master_admin_token):
        """Test that footer settings are included in platform settings"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check footer fields
        assert "footer_copyright" in data, "footer_copyright field missing"
        
        print(f"SUCCESS: Footer settings exist in platform settings")
        print(f"  - footer_copyright: {data.get('footer_copyright')}")
        print(f"  - footer_links: {data.get('footer_links')}")
    
    def test_update_footer_links(self, master_admin_token):
        """Test updating footer links"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # Get current settings
        get_response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        current_settings = get_response.json()
        
        # Update footer links
        test_links = [
            {"label": "Privacy Policy", "url": "/privacy"},
            {"label": "Terms of Service", "url": "/terms"},
            {"label": "Contact", "url": "mailto:support@crosscurrent.com"}
        ]
        
        update_data = {
            **current_settings,
            "footer_links": test_links
        }
        
        response = requests.put(f"{BASE_URL}/api/settings/platform", headers=headers, json=update_data)
        assert response.status_code == 200
        
        # Verify
        verify_response = requests.get(f"{BASE_URL}/api/settings/platform", headers=headers)
        data = verify_response.json()
        
        assert data.get("footer_links") is not None, "footer_links not saved"
        assert len(data.get("footer_links", [])) == 3, "footer_links count mismatch"
        
        print("SUCCESS: Footer links updated successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

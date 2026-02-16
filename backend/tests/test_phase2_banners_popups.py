"""
Test Phase 2 Features: Notice Banner & Promotion Popup
Tests for CrossCurrent Hub trading dashboard banner/popup configuration.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNoticeBannerAPI:
    """Test GET /api/settings/notice-banner - public endpoint"""
    
    def test_notice_banner_returns_200(self):
        """Notice banner endpoint returns 200 without auth"""
        response = requests.get(f"{BASE_URL}/api/settings/notice-banner")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: GET /api/settings/notice-banner returns 200")
    
    def test_notice_banner_structure_when_enabled(self):
        """When enabled, notice banner returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/settings/notice-banner")
        data = response.json()
        
        if data.get('enabled'):
            # Verify all expected fields exist
            assert 'text' in data, "Missing 'text' field"
            assert 'bg_color' in data, "Missing 'bg_color' field"
            assert 'text_color' in data, "Missing 'text_color' field"
            assert 'pages' in data, "Missing 'pages' field"
            
            # Verify pages is a list
            assert isinstance(data['pages'], list), "'pages' should be a list"
            
            # Verify colors are hex format
            assert data['bg_color'].startswith('#'), "bg_color should be hex format"
            assert data['text_color'].startswith('#'), "text_color should be hex format"
            
            print(f"PASS: Notice banner structure correct - text: '{data['text'][:30]}...', pages: {data['pages']}")
        else:
            assert data == {'enabled': False}, "When disabled, should return only {enabled: false}"
            print("PASS: Notice banner is disabled - returns {enabled: false}")
    
    def test_notice_banner_pages_configured(self):
        """Verify seeded banner shows on dashboard and trade_monitor"""
        response = requests.get(f"{BASE_URL}/api/settings/notice-banner")
        data = response.json()
        
        assert data.get('enabled'), "Notice banner should be enabled (seeded data)"
        assert 'dashboard' in data.get('pages', []), "Banner should be configured for dashboard"
        assert 'trade_monitor' in data.get('pages', []), "Banner should be configured for trade_monitor"
        print(f"PASS: Notice banner configured for pages: {data['pages']}")


class TestPromotionPopupAPI:
    """Test GET /api/settings/promotion-popup - public endpoint"""
    
    def test_promotion_popup_returns_200(self):
        """Promotion popup endpoint returns 200 without auth"""
        response = requests.get(f"{BASE_URL}/api/settings/promotion-popup")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: GET /api/settings/promotion-popup returns 200")
    
    def test_promotion_popup_structure_when_enabled(self):
        """When enabled, promotion popup returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/settings/promotion-popup")
        data = response.json()
        
        if data.get('enabled'):
            # Verify all expected fields exist
            assert 'preset' in data, "Missing 'preset' field"
            assert 'title' in data, "Missing 'title' field"
            assert 'body' in data, "Missing 'body' field"
            assert 'cta_text' in data, "Missing 'cta_text' field"
            assert 'frequency' in data, "Missing 'frequency' field"
            
            # Verify preset is valid
            valid_presets = ['announcement', 'promo', 'feature_update']
            assert data['preset'] in valid_presets, f"Invalid preset: {data['preset']}"
            
            # Verify frequency is valid
            valid_frequencies = ['once_per_session', 'once_per_day', 'always']
            assert data['frequency'] in valid_frequencies, f"Invalid frequency: {data['frequency']}"
            
            print(f"PASS: Promotion popup structure correct - preset: {data['preset']}, title: '{data['title']}'")
        else:
            assert data == {'enabled': False}, "When disabled, should return only {enabled: false}"
            print("PASS: Promotion popup is disabled - returns {enabled: false}")
    
    def test_promotion_popup_seeded_preset(self):
        """Verify seeded popup has 'announcement' preset"""
        response = requests.get(f"{BASE_URL}/api/settings/promotion-popup")
        data = response.json()
        
        assert data.get('enabled'), "Promotion popup should be enabled (seeded data)"
        assert data.get('preset') == 'announcement', f"Expected 'announcement' preset, got '{data.get('preset')}'"
        assert 'Signal Blocking' in data.get('title', ''), f"Expected 'Signal Blocking' in title, got '{data.get('title')}'"
        print(f"PASS: Promotion popup preset is '{data['preset']}' with title '{data['title']}'")


class TestPlatformSettingsWithBanners:
    """Test PUT /api/settings/platform saves banner/popup fields correctly"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_platform_settings_includes_banner_fields(self, admin_token):
        """Platform settings include notice_banner_* and promo_popup_* fields"""
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check notice banner fields
        assert 'notice_banner_enabled' in data, "Missing notice_banner_enabled"
        assert 'notice_banner_text' in data, "Missing notice_banner_text"
        assert 'notice_banner_bg_color' in data, "Missing notice_banner_bg_color"
        assert 'notice_banner_text_color' in data, "Missing notice_banner_text_color"
        assert 'notice_banner_pages' in data, "Missing notice_banner_pages"
        
        # Check promo popup fields
        assert 'promo_popup_enabled' in data, "Missing promo_popup_enabled"
        assert 'promo_popup_preset' in data, "Missing promo_popup_preset"
        assert 'promo_popup_title' in data, "Missing promo_popup_title"
        assert 'promo_popup_body' in data, "Missing promo_popup_body"
        assert 'promo_popup_frequency' in data, "Missing promo_popup_frequency"
        
        print("PASS: Platform settings include all banner/popup fields")
    
    def test_update_notice_banner_text(self, admin_token):
        """Test updating notice banner text"""
        # Get current settings
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        current_settings = response.json()
        
        # Update with modified banner text
        test_text = "TEST_Banner_Text_" + str(os.urandom(4).hex())
        current_settings['notice_banner_text'] = test_text
        
        update_response = requests.put(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=current_settings
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.status_code}"
        
        # Verify via public endpoint
        verify_response = requests.get(f"{BASE_URL}/api/settings/notice-banner")
        verify_data = verify_response.json()
        
        # Note: We should restore original text after test
        assert verify_data.get('text') == test_text, f"Banner text not updated: expected '{test_text}', got '{verify_data.get('text')}'"
        
        # Restore original text
        current_settings['notice_banner_text'] = "Trading hours updated to 3:00 PM starting Feb 20"
        requests.put(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=current_settings
        )
        
        print(f"PASS: Notice banner text updated and verified")
    
    def test_update_promo_popup_preset(self, admin_token):
        """Test updating promo popup preset"""
        # Get current settings
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        current_settings = response.json()
        original_preset = current_settings.get('promo_popup_preset')
        
        # Change preset
        new_preset = 'promo' if original_preset != 'promo' else 'feature_update'
        current_settings['promo_popup_preset'] = new_preset
        
        update_response = requests.put(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=current_settings
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.status_code}"
        
        # Verify via public endpoint
        verify_response = requests.get(f"{BASE_URL}/api/settings/promotion-popup")
        verify_data = verify_response.json()
        
        assert verify_data.get('preset') == new_preset, f"Preset not updated: expected '{new_preset}', got '{verify_data.get('preset')}'"
        
        # Restore original preset
        current_settings['promo_popup_preset'] = original_preset
        requests.put(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=current_settings
        )
        
        print(f"PASS: Promo popup preset updated from '{original_preset}' to '{new_preset}' and restored")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

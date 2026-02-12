"""
Test PWA implementation and backend route refactoring for iteration 94
- PWA: manifest.json, sw.js, offline.html, icons
- Backend: extracted BVE routes, extracted Settings routes
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


class TestPWAManifest:
    """Test PWA manifest.json"""
    
    def test_manifest_served(self):
        """Manifest.json is served at /manifest.json"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200, f"Manifest not found: {response.status_code}"
    
    def test_manifest_name(self):
        """Manifest has correct app name 'The CrossCurrent Hub'"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data.get("name") == "The CrossCurrent Hub", f"Got name: {data.get('name')}"
    
    def test_manifest_short_name(self):
        """Manifest has correct short_name 'CrossCurrent'"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data.get("short_name") == "CrossCurrent", f"Got short_name: {data.get('short_name')}"
    
    def test_manifest_theme_color(self):
        """Manifest has correct theme_color '#09090b'"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data.get("theme_color") == "#09090b", f"Got theme_color: {data.get('theme_color')}"
    
    def test_manifest_icons_count(self):
        """Manifest has 4 icons"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        icons = data.get("icons", [])
        assert len(icons) == 4, f"Expected 4 icons, got {len(icons)}"
    
    def test_manifest_has_192_icon(self):
        """Manifest has 192x192 icon"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        icons = data.get("icons", [])
        has_192 = any(i.get("sizes") == "192x192" for i in icons)
        assert has_192, "Missing 192x192 icon"
    
    def test_manifest_has_512_icon(self):
        """Manifest has 512x512 icon"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        icons = data.get("icons", [])
        has_512 = any(i.get("sizes") == "512x512" for i in icons)
        assert has_512, "Missing 512x512 icon"
    
    def test_manifest_display_standalone(self):
        """Manifest has display: standalone for PWA"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data.get("display") == "standalone", f"Got display: {data.get('display')}"


class TestPWAServiceWorker:
    """Test PWA service worker"""
    
    def test_sw_served(self):
        """Service worker is served at /sw.js"""
        response = requests.get(f"{BASE_URL}/sw.js")
        assert response.status_code == 200, f"SW not found: {response.status_code}"
    
    def test_sw_has_cache_name(self):
        """Service worker has proper cache name"""
        response = requests.get(f"{BASE_URL}/sw.js")
        assert response.status_code == 200
        content = response.text
        assert "crosscurrent-hub-v1" in content, "Missing cache name"
    
    def test_sw_has_install_handler(self):
        """Service worker has install event handler"""
        response = requests.get(f"{BASE_URL}/sw.js")
        assert response.status_code == 200
        content = response.text
        assert "self.addEventListener('install'" in content, "Missing install handler"
    
    def test_sw_has_fetch_handler(self):
        """Service worker has fetch event handler"""
        response = requests.get(f"{BASE_URL}/sw.js")
        assert response.status_code == 200
        content = response.text
        assert "self.addEventListener('fetch'" in content, "Missing fetch handler"


class TestPWAOfflinePage:
    """Test PWA offline fallback page"""
    
    def test_offline_served(self):
        """Offline page is served at /offline.html"""
        response = requests.get(f"{BASE_URL}/offline.html")
        assert response.status_code == 200, f"Offline page not found: {response.status_code}"
    
    def test_offline_title(self):
        """Offline page has correct title"""
        response = requests.get(f"{BASE_URL}/offline.html")
        assert response.status_code == 200
        content = response.text
        assert "The CrossCurrent Hub" in content, "Missing app name in title"
    
    def test_offline_theme_color(self):
        """Offline page has correct theme color meta tag"""
        response = requests.get(f"{BASE_URL}/offline.html")
        assert response.status_code == 200
        content = response.text
        assert 'content="#09090b"' in content, "Missing theme color meta"


class TestPWAIcons:
    """Test PWA icon files are served"""
    
    def test_icon_192(self):
        """192x192 icon is served at /icon-192.png"""
        response = requests.head(f"{BASE_URL}/icon-192.png")
        assert response.status_code == 200, f"icon-192.png not found: {response.status_code}"
    
    def test_icon_512(self):
        """512x512 icon is served at /icon-512.png"""
        response = requests.head(f"{BASE_URL}/icon-512.png")
        assert response.status_code == 200, f"icon-512.png not found: {response.status_code}"
    
    def test_apple_touch_icon(self):
        """Apple touch icon is served at /apple-touch-icon.png"""
        response = requests.head(f"{BASE_URL}/apple-touch-icon.png")
        assert response.status_code == 200, f"apple-touch-icon.png not found: {response.status_code}"


class TestIndexHTMLMeta:
    """Test index.html has correct PWA meta tags"""
    
    def test_index_loads(self):
        """Index page loads"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200, f"Index page failed: {response.status_code}"
    
    def test_page_title(self):
        """Page title is 'The CrossCurrent Hub'"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        assert "<title>The CrossCurrent Hub</title>" in content, "Missing correct page title"
    
    def test_manifest_link(self):
        """Has link to manifest.json"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        assert 'rel="manifest"' in content, "Missing manifest link"
    
    def test_apple_mobile_web_app_capable(self):
        """Has apple-mobile-web-app-capable meta"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        assert 'name="apple-mobile-web-app-capable"' in content, "Missing apple-mobile-web-app-capable"
    
    def test_theme_color_meta(self):
        """Has theme-color meta tag"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        content = response.text
        assert 'name="theme-color"' in content, "Missing theme-color meta"


class TestSettingsRoutes:
    """Test extracted Settings routes from routes/settings.py"""
    
    def test_get_platform_settings(self):
        """GET /api/settings/platform returns platform settings (public)"""
        response = requests.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200, f"Failed: {response.status_code}"
        data = response.json()
        # Verify it returns settings object
        assert "platform_name" in data or "site_title" in data, f"Missing expected fields: {list(data.keys())[:5]}"
    
    def test_get_email_templates_requires_auth(self, admin_token):
        """GET /api/settings/email-templates requires admin auth"""
        # Without auth should fail
        response = requests.get(f"{BASE_URL}/api/settings/email-templates")
        assert response.status_code == 401 or response.status_code == 403, f"Expected 401/403 without auth, got {response.status_code}"
        
        # With admin auth should succeed
        response = requests.get(
            f"{BASE_URL}/api/settings/email-templates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed with auth: {response.status_code}"
        data = response.json()
        assert "templates" in data, f"Missing templates key: {list(data.keys())}"


class TestBVERoutes:
    """Test extracted BVE routes from routes/bve.py"""
    
    def test_bve_active_signal_requires_admin(self, admin_token):
        """GET /api/bve/active-signal requires admin auth"""
        # Without auth should fail
        response = requests.get(f"{BASE_URL}/api/bve/active-signal")
        assert response.status_code == 401 or response.status_code == 403, f"Expected 401/403 without auth, got {response.status_code}"
        
        # With admin auth should succeed (may return empty signal)
        response = requests.get(
            f"{BASE_URL}/api/bve/active-signal",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 200 with signal (or None) or 400/403 if not in BVE session
        assert response.status_code in [200, 400, 403], f"Unexpected status: {response.status_code}"


class TestExistingRoutes:
    """Test existing routes still work after refactoring"""
    
    def test_login_works(self):
        """POST /api/auth/login still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data, "Missing access_token in response"
    
    def test_profit_summary(self, admin_token):
        """GET /api/profit/summary still works"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Profit summary failed: {response.status_code}"
        data = response.json()
        assert "account_value" in data, f"Missing account_value: {list(data.keys())}"
    
    def test_trade_active_signal(self, admin_token):
        """GET /api/trade/active-signal still works"""
        response = requests.get(
            f"{BASE_URL}/api/trade/active-signal",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Trade active signal failed: {response.status_code}"
    
    def test_admin_members(self, admin_token):
        """GET /api/admin/members still works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin members failed: {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of members"

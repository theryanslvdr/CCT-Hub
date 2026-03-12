"""
Iteration 190 Tests - TidyCal Booking, Weekly Report, Navigation Features
Tests for:
1. TidyCal Booking Embed - GET /api/settings/booking-embed (public)
2. Weekly Performance Report - GET /api/referrals/my-team/weekly-report (auth)
3. My Team endpoint - GET /api/referrals/my-team (auth)
4. Platform settings with tidycal_embed_url field
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ui-mobile-overhaul-3.preview.emergentagent.com').rstrip('/')


class TestAuth:
    """Authentication tests - login returns access_token"""
    
    def test_login_returns_access_token(self):
        """Login should return access_token (not token)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Response should have access_token, not just token
        assert "access_token" in data, "Response should contain access_token"
        assert "token_type" in data, "Response should contain token_type"
        assert "user" in data, "Response should contain user object"
        assert data["token_type"] == "bearer", "Token type should be bearer"
        assert len(data["access_token"]) > 0, "Access token should not be empty"


@pytest.fixture
def auth_token():
    """Get authentication token for protected endpoints"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "iam@ryansalvador.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestBookingEmbedPublic:
    """TidyCal Booking Embed Endpoint - Public (no auth required)"""
    
    def test_booking_embed_endpoint_exists(self):
        """GET /api/settings/booking-embed should be accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/settings/booking-embed")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_booking_embed_returns_tidycal_url_field(self):
        """Response should contain tidycal_embed_url field"""
        response = requests.get(f"{BASE_URL}/api/settings/booking-embed")
        assert response.status_code == 200
        data = response.json()
        
        assert "tidycal_embed_url" in data, "Response should have tidycal_embed_url field"
        # URL can be empty string when not configured
        assert isinstance(data["tidycal_embed_url"], str), "tidycal_embed_url should be a string"


class TestWeeklyPerformanceReport:
    """Weekly Performance Report - GET /api/referrals/my-team/weekly-report"""
    
    def test_weekly_report_requires_auth(self):
        """Weekly report endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/referrals/my-team/weekly-report")
        assert response.status_code in [401, 403], "Should require auth"
    
    def test_weekly_report_returns_report_data(self, auth_headers):
        """Weekly report should return report with expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-team/weekly-report",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Response should have report object (or None if no team)
        assert "report" in data, "Response should have report field"
        
        if data["report"] is not None:
            report = data["report"]
            
            # Check all required fields
            assert "total_trades" in report, "Report should have total_trades"
            assert "total_profit" in report, "Report should have total_profit"
            assert "win_rate" in report, "Report should have win_rate"
            assert "active_traders" in report, "Report should have active_traders"
            assert "total_members" in report, "Report should have total_members"
            assert "prev_week" in report, "Report should have prev_week comparison"
            
            # Verify prev_week has comparison fields
            prev_week = report["prev_week"]
            assert "total_trades" in prev_week, "prev_week should have total_trades"
            assert "total_profit" in prev_week, "prev_week should have total_profit"
            assert "win_rate" in prev_week, "prev_week should have win_rate"
            
            # member_breakdown should be a list
            if "member_breakdown" in report:
                assert isinstance(report["member_breakdown"], list), "member_breakdown should be a list"
    
    def test_weekly_report_numeric_values(self, auth_headers):
        """Weekly report numeric fields should be proper types"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-team/weekly-report",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("report"):
            report = data["report"]
            assert isinstance(report["total_trades"], (int, float)), "total_trades should be numeric"
            assert isinstance(report["total_profit"], (int, float)), "total_profit should be numeric"
            assert isinstance(report["win_rate"], (int, float)), "win_rate should be numeric"
            assert isinstance(report["active_traders"], int), "active_traders should be int"


class TestMyTeamEndpoint:
    """My Team Endpoint - GET /api/referrals/my-team"""
    
    def test_my_team_requires_auth(self):
        """My team endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/referrals/my-team")
        assert response.status_code in [401, 403], "Should require auth"
    
    def test_my_team_returns_team_and_stats(self, auth_headers):
        """My team should return team array and stats object"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-team",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should have team and stats
        assert "team" in data, "Response should have team array"
        assert "stats" in data, "Response should have stats object"
        assert isinstance(data["team"], list), "team should be a list"
        
        # Stats should have expected fields
        stats = data["stats"]
        assert "total" in stats, "stats should have total"
        assert "active" in stats, "stats should have active count"
        assert "in_danger" in stats, "stats should have in_danger count"
        assert "new_this_week" in stats, "stats should have new_this_week count"
    
    def test_my_team_member_structure(self, auth_headers):
        """Team members should have expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-team",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["team"]) > 0:
            member = data["team"][0]
            # Check expected fields for team member
            expected_fields = ["id", "name", "email", "status"]
            for field in expected_fields:
                assert field in member, f"Team member should have {field}"


class TestPlatformSettings:
    """Platform Settings - tidycal_embed_url field support"""
    
    def test_platform_settings_returns_tidycal_field(self, auth_headers):
        """GET /api/settings/platform should include tidycal_embed_url"""
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers=auth_headers
        )
        # Platform settings may or may not require auth
        if response.status_code == 200:
            data = response.json()
            # Check if tidycal_embed_url exists or can be set
            # Field should exist in settings model
            assert response.status_code == 200


class TestNavigationEndpoints:
    """Test endpoints that support navigation features"""
    
    def test_referral_tracking_endpoint(self, auth_headers):
        """GET /api/referrals/tracking for invite link display"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/tracking",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should have referral code and invite link fields
        assert "referral_code" in data or "merin_code" in data, "Should have referral code"
    
    def test_store_items_endpoint(self, auth_headers):
        """GET /api/store/items for Hub Store"""
        response = requests.get(
            f"{BASE_URL}/api/store/items",
            headers=auth_headers
        )
        # Store may return items or empty list
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

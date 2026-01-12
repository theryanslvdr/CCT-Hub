"""
Test Iteration 35 - Performance Report Generation Feature
Tests for image-based performance recap report generation (P2 feature)
"""

import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestReportGenerationAPI:
    """Test Performance Report Generation API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
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
            self.user = login_response.json().get("user")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
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
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Login successful as {data['user']['full_name']}")
    
    def test_report_base64_endpoint_daily(self):
        """Test GET /api/profit/report/base64 with daily period"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/base64", params={"period": "daily"})
        assert response.status_code == 200
        
        data = response.json()
        assert "image_base64" in data
        assert "period" in data
        assert "generated_at" in data
        assert "stats" in data
        
        # Verify it's valid base64
        assert len(data["image_base64"]) > 0
        try:
            decoded = base64.b64decode(data["image_base64"])
            # Check PNG magic bytes
            assert decoded[:8] == b'\x89PNG\r\n\x1a\n', "Not a valid PNG image"
        except Exception as e:
            pytest.fail(f"Invalid base64 image: {e}")
        
        assert data["period"] == "daily"
        print(f"✓ Daily report base64 generated - {len(data['image_base64'])} chars")
    
    def test_report_base64_endpoint_weekly(self):
        """Test GET /api/profit/report/base64 with weekly period"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/base64", params={"period": "weekly"})
        assert response.status_code == 200
        
        data = response.json()
        assert "image_base64" in data
        assert data["period"] == "weekly"
        
        # Verify stats structure
        stats = data.get("stats", {})
        assert "account_value" in stats
        assert "total_profit" in stats
        assert "total_trades" in stats
        assert "win_rate" in stats
        assert "avg_profit_per_trade" in stats
        assert "best_trade" in stats
        assert "worst_trade" in stats
        assert "streak" in stats
        print(f"✓ Weekly report base64 generated with stats: {stats}")
    
    def test_report_base64_endpoint_monthly(self):
        """Test GET /api/profit/report/base64 with monthly period (default)"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/base64", params={"period": "monthly"})
        assert response.status_code == 200
        
        data = response.json()
        assert "image_base64" in data
        assert data["period"] == "monthly"
        print(f"✓ Monthly report base64 generated")
    
    def test_report_base64_default_period(self):
        """Test GET /api/profit/report/base64 without period param (should default to monthly)"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/base64")
        assert response.status_code == 200
        
        data = response.json()
        assert data["period"] == "monthly"
        print(f"✓ Default period is monthly")
    
    def test_report_image_endpoint_daily(self):
        """Test GET /api/profit/report/image returns PNG file for daily period"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/image", params={"period": "daily"})
        assert response.status_code == 200
        
        # Check content type
        assert response.headers.get("Content-Type") == "image/png"
        
        # Check content disposition header for download
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition
        assert "performance_report_daily" in content_disposition
        assert ".png" in content_disposition
        
        # Verify PNG magic bytes
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n', "Not a valid PNG image"
        
        print(f"✓ Daily report image downloaded - {len(response.content)} bytes")
    
    def test_report_image_endpoint_weekly(self):
        """Test GET /api/profit/report/image returns PNG file for weekly period"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/image", params={"period": "weekly"})
        assert response.status_code == 200
        
        assert response.headers.get("Content-Type") == "image/png"
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n'
        
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "performance_report_weekly" in content_disposition
        print(f"✓ Weekly report image downloaded - {len(response.content)} bytes")
    
    def test_report_image_endpoint_monthly(self):
        """Test GET /api/profit/report/image returns PNG file for monthly period"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/image", params={"period": "monthly"})
        assert response.status_code == 200
        
        assert response.headers.get("Content-Type") == "image/png"
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n'
        
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "performance_report_monthly" in content_disposition
        print(f"✓ Monthly report image downloaded - {len(response.content)} bytes")
    
    def test_report_image_default_period(self):
        """Test GET /api/profit/report/image without period param"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/image")
        assert response.status_code == 200
        
        assert response.headers.get("Content-Type") == "image/png"
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "performance_report_monthly" in content_disposition
        print(f"✓ Default image period is monthly")
    
    def test_report_requires_authentication(self):
        """Test that report endpoints require authentication"""
        # Create a new session without auth
        no_auth_session = requests.Session()
        
        # Test base64 endpoint
        response = no_auth_session.get(f"{BASE_URL}/api/profit/report/base64")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        # Test image endpoint
        response = no_auth_session.get(f"{BASE_URL}/api/profit/report/image")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
        print("✓ Report endpoints require authentication")
    
    def test_report_stats_values_are_numeric(self):
        """Test that report stats contain numeric values"""
        response = self.session.get(f"{BASE_URL}/api/profit/report/base64", params={"period": "monthly"})
        assert response.status_code == 200
        
        stats = response.json().get("stats", {})
        
        # All stats should be numeric
        assert isinstance(stats.get("account_value"), (int, float))
        assert isinstance(stats.get("total_profit"), (int, float))
        assert isinstance(stats.get("total_trades"), int)
        assert isinstance(stats.get("win_rate"), (int, float))
        assert isinstance(stats.get("avg_profit_per_trade"), (int, float))
        assert isinstance(stats.get("best_trade"), (int, float))
        assert isinstance(stats.get("worst_trade"), (int, float))
        assert isinstance(stats.get("streak"), int)
        
        print(f"✓ All stats are numeric values")


class TestProfitTrackerSummary:
    """Test Profit Tracker summary endpoint (used by report)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_profit_summary_endpoint(self):
        """Test GET /api/profit/summary returns expected data"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_deposits" in data
        assert "account_value" in data
        print(f"✓ Profit summary: account_value={data.get('account_value')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

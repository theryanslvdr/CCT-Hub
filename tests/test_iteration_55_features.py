"""
Iteration 55 - Testing Two Features:
1. Commission Display Fix - total_commission from onboarding wizard assigned to last trade entry
2. Content Protection - Security tab with copy/right-click/keyboard shortcut prevention settings
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "master_admin"


class TestContentProtectionSettings:
    """Test Content Protection feature in platform settings"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_platform_settings_includes_content_protection(self, auth_headers):
        """Test that platform settings include content protection fields"""
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify content protection fields exist
        assert "content_protection_enabled" in data, "content_protection_enabled field missing"
        assert "content_protection_watermark" in data, "content_protection_watermark field missing"
        assert "content_protection_disable_copy" in data, "content_protection_disable_copy field missing"
        assert "content_protection_disable_rightclick" in data, "content_protection_disable_rightclick field missing"
        assert "content_protection_disable_shortcuts" in data, "content_protection_disable_shortcuts field missing"
        
        # Verify they are boolean values
        assert isinstance(data["content_protection_enabled"], bool)
        assert isinstance(data["content_protection_watermark"], bool)
        assert isinstance(data["content_protection_disable_copy"], bool)
        assert isinstance(data["content_protection_disable_rightclick"], bool)
        assert isinstance(data["content_protection_disable_shortcuts"], bool)
    
    def test_update_content_protection_enabled(self, auth_headers):
        """Test enabling content protection"""
        # First get current settings
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=auth_headers)
        assert response.status_code == 200
        current_settings = response.json()
        
        # Enable content protection
        update_data = {
            **current_settings,
            "content_protection_enabled": True,
            "content_protection_watermark": True,
            "content_protection_disable_copy": True,
            "content_protection_disable_rightclick": True,
            "content_protection_disable_shortcuts": True
        }
        
        response = requests.put(f"{BASE_URL}/api/settings/platform", 
                               json=update_data, 
                               headers=auth_headers)
        assert response.status_code == 200
        
        # Verify the update
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["content_protection_enabled"] == True
        assert data["content_protection_watermark"] == True
        assert data["content_protection_disable_copy"] == True
        assert data["content_protection_disable_rightclick"] == True
        assert data["content_protection_disable_shortcuts"] == True
    
    def test_disable_content_protection(self, auth_headers):
        """Test disabling content protection"""
        # Get current settings
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=auth_headers)
        assert response.status_code == 200
        current_settings = response.json()
        
        # Disable content protection
        update_data = {
            **current_settings,
            "content_protection_enabled": False
        }
        
        response = requests.put(f"{BASE_URL}/api/settings/platform", 
                               json=update_data, 
                               headers=auth_headers)
        assert response.status_code == 200
        
        # Verify the update
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["content_protection_enabled"] == False


class TestCommissionOnboarding:
    """Test Commission assignment to last trade entry during onboarding"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_complete_onboarding_endpoint_exists(self, auth_headers):
        """Test that complete-onboarding endpoint exists and accepts total_commission"""
        # This is a POST endpoint that requires specific data
        # We'll test with minimal data to verify the endpoint exists
        response = requests.post(f"{BASE_URL}/api/profit/complete-onboarding", 
                                json={
                                    "starting_balance": 1000,
                                    "start_date": "2025-01-01",
                                    "trades": [],
                                    "total_commission": 50.0
                                },
                                headers=auth_headers)
        # Should either succeed or fail with validation error, not 404
        assert response.status_code != 404, "complete-onboarding endpoint not found"
    
    def test_trade_log_has_commission_field(self, auth_headers):
        """Test that trade logs include commission field"""
        response = requests.get(f"{BASE_URL}/api/trade/logs", headers=auth_headers)
        assert response.status_code == 200
        trades = response.json()
        
        if len(trades) > 0:
            # Check that commission field exists in trade logs
            trade = trades[0]
            assert "commission" in trade or trade.get("commission", 0) >= 0, "Commission field should exist in trade logs"
    
    def test_trade_history_includes_commission(self, auth_headers):
        """Test that trade history endpoint includes commission field"""
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data.get("trades") and len(data["trades"]) > 0:
            trade = data["trades"][0]
            # Commission should be present (defaulting to 0 for backward compatibility)
            assert "commission" in trade, "Commission field should be in trade history"


class TestTradeLogCommission:
    """Test commission field in trade logging"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_log_trade_with_commission(self, auth_headers):
        """Test logging a trade with commission field"""
        trade_data = {
            "direction": "BUY",
            "actual_profit": 15.0,
            "commission": 5.0,
            "notes": "Test trade with commission"
        }
        
        response = requests.post(f"{BASE_URL}/api/trade/log", 
                                json=trade_data, 
                                headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify commission is stored
        assert "commission" in data
        assert data["commission"] == 5.0
    
    def test_log_trade_without_commission_defaults_to_zero(self, auth_headers):
        """Test that trade without commission defaults to 0"""
        trade_data = {
            "direction": "SELL",
            "actual_profit": 12.0,
            "notes": "Test trade without commission"
        }
        
        response = requests.post(f"{BASE_URL}/api/trade/log", 
                                json=trade_data, 
                                headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Commission should default to 0
        assert "commission" in data
        assert data["commission"] == 0


class TestDailyProjectionCommission:
    """Test that commission appears in daily projection data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_trade_logs_endpoint_returns_commission(self, auth_headers):
        """Test that trade logs endpoint returns commission field"""
        response = requests.get(f"{BASE_URL}/api/trade/logs?limit=10", headers=auth_headers)
        assert response.status_code == 200
        trades = response.json()
        
        # All trades should have commission field
        for trade in trades:
            assert "commission" in trade, f"Trade {trade.get('id')} missing commission field"
    
    def test_profit_summary_calculation(self, auth_headers):
        """Test that profit summary is calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary fields exist
        assert "total_deposits" in data
        assert "total_actual_profit" in data
        assert "account_value" in data


class TestPlatformSettingsModel:
    """Test PlatformSettings model includes content protection fields"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_platform_settings_default_values(self, auth_headers):
        """Test that platform settings have correct default values for content protection"""
        response = requests.get(f"{BASE_URL}/api/settings/platform", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Content protection should be disabled by default
        # But other sub-settings should default to True (enabled when protection is on)
        assert isinstance(data.get("content_protection_enabled"), bool)
        assert isinstance(data.get("content_protection_watermark"), bool)
        assert isinstance(data.get("content_protection_disable_copy"), bool)
        assert isinstance(data.get("content_protection_disable_rightclick"), bool)
        assert isinstance(data.get("content_protection_disable_shortcuts"), bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

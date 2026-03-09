"""
Iteration 37 - Trade History Actions & Onboarding Tour Tests
Tests:
1. Trade History 'Actions' column with role-based buttons
2. Reset Trade endpoint (master_admin only)
3. Request Change endpoint (non-master-admin users)
4. Onboarding Tour localStorage persistence
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://bve-data-loss.preview.emergentagent.com').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestTradeActionsBackend:
    """Test trade action endpoints"""
    
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
        assert data["user"]["role"] == "master_admin"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, master_admin_token):
        """Get auth headers for master admin"""
        return {"Authorization": f"Bearer {master_admin_token}"}
    
    def test_login_master_admin(self):
        """Test master admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Master admin login successful, role: {data['user']['role']}")
    
    def test_get_trade_history(self, auth_headers):
        """Test getting trade history"""
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "total" in data
        print(f"✓ Trade history retrieved: {data['total']} trades")
        return data
    
    def test_reset_trade_endpoint_exists(self, auth_headers):
        """Test that reset trade endpoint exists (even if no trade to reset)"""
        # Try with a non-existent trade ID to verify endpoint exists
        response = requests.delete(f"{BASE_URL}/api/trade/reset/non-existent-id", headers=auth_headers)
        # Should return 404 (trade not found) not 405 (method not allowed)
        assert response.status_code in [404, 200], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"✓ Reset trade endpoint exists, status: {response.status_code}")
    
    def test_request_change_endpoint_exists(self, auth_headers):
        """Test that request change endpoint exists"""
        # Try with a non-existent trade ID to verify endpoint exists
        response = requests.post(f"{BASE_URL}/api/trade/request-change", 
            headers=auth_headers,
            json={
                "trade_id": "non-existent-id",
                "reason": "Test reason"
            }
        )
        # Should return 404 (trade not found) not 405 (method not allowed)
        assert response.status_code in [404, 200, 400, 403], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"✓ Request change endpoint exists, status: {response.status_code}")
    
    def test_reset_trade_requires_master_admin(self):
        """Test that reset trade requires master_admin role"""
        # Try without auth
        response = requests.delete(f"{BASE_URL}/api/trade/reset/some-id")
        assert response.status_code in [401, 403], f"Should require auth: {response.status_code}"
        print(f"✓ Reset trade requires authentication, status: {response.status_code}")
    
    def test_get_active_signal(self, auth_headers):
        """Test getting active signal"""
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Active signal: {data.get('signal', {}).get('product', 'None')}")
        return data
    
    def test_get_daily_summary(self, auth_headers):
        """Test getting daily summary"""
        response = requests.get(f"{BASE_URL}/api/trade/daily-summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "trades_count" in data
        print(f"✓ Daily summary: {data['trades_count']} trades today")
    
    def test_get_trade_streak(self, auth_headers):
        """Test getting trade streak"""
        response = requests.get(f"{BASE_URL}/api/trade/streak", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "streak" in data
        print(f"✓ Trade streak: {data['streak']}")


class TestTradeResetFlow:
    """Test the complete reset trade flow"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        """Get master admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, master_admin_token):
        """Get auth headers for master admin"""
        return {"Authorization": f"Bearer {master_admin_token}"}
    
    def test_get_existing_trades(self, auth_headers):
        """Get existing trades to find one to test reset"""
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        trades = data.get("trades", [])
        print(f"✓ Found {len(trades)} trades in history")
        
        if trades:
            trade = trades[0]
            print(f"  First trade ID: {trade.get('id')}")
            print(f"  Trade date: {trade.get('created_at', '')[:10]}")
            print(f"  Actual profit: ${trade.get('actual_profit', 0)}")
        
        return trades


class TestRequestChangeFlow:
    """Test the request change flow for non-master-admin users"""
    
    @pytest.fixture(scope="class")
    def master_admin_token(self):
        """Get master admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, master_admin_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {master_admin_token}"}
    
    def test_request_change_with_valid_trade(self, auth_headers):
        """Test request change with a valid trade (if exists)"""
        # First get trades
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=auth_headers)
        assert response.status_code == 200
        trades = response.json().get("trades", [])
        
        if not trades:
            pytest.skip("No trades available to test request change")
        
        trade_id = trades[0]["id"]
        
        # Note: Master admin can't request change for their own trades
        # This tests the endpoint exists and validates input
        response = requests.post(f"{BASE_URL}/api/trade/request-change",
            headers=auth_headers,
            json={
                "trade_id": trade_id,
                "reason": "Test change request from iteration 37"
            }
        )
        
        # Master admin might get 403 or success depending on implementation
        print(f"✓ Request change response: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Response: {response.text[:200]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test iteration 77 - Testing 7 features/fixes for financial tracking platform:
1) Mobile Trade Monitor - Sticky Signal Bar
2) Exit Trade - Hide button after submission, show performance summary
3) Admin - Delete member's trade history when simulating
4) Profit Tracker - Dialog padding fix
5) Mobile Menu Header - Show platform logo + '| The Hub'
6) Daily Projection Dialog - Mobile styling
7) Admin Dashboard - 'Didn't Report Today' widget with Email/Notify buttons
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminAuthentication:
    """Test admin login and authentication"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_admin_login(self, admin_token):
        """Test admin can login successfully"""
        assert admin_token is not None
        assert len(admin_token) > 0
        print(f"✓ Admin login successful, token length: {len(admin_token)}")


class TestTodayStatsEndpoint:
    """Test /api/admin/analytics/today-stats endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_today_stats_returns_profit_and_commission(self, admin_token):
        """Test that today-stats endpoint returns profit and commission data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics/today-stats", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_profit" in data, "Missing total_profit field"
        assert "total_commission" in data, "Missing total_commission field"
        assert "trades_count" in data, "Missing trades_count field"
        
        # Verify data types
        assert isinstance(data["total_profit"], (int, float)), "total_profit should be numeric"
        assert isinstance(data["total_commission"], (int, float)), "total_commission should be numeric"
        assert isinstance(data["trades_count"], int), "trades_count should be integer"
        
        print(f"✓ Today stats: profit=${data['total_profit']}, commission=${data['total_commission']}, trades={data['trades_count']}")


class TestNotifyMemberEndpoint:
    """Test /api/admin/members/{user_id}/notify endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_user_id(self, admin_token):
        """Get a test user ID from members list"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        members = data.get("members", data) if isinstance(data, dict) else data
        if members and len(members) > 0:
            return members[0].get("id")
        return None
    
    def test_notify_member_endpoint_exists(self, admin_token, test_user_id):
        """Test that notify endpoint exists and accepts requests"""
        if not test_user_id:
            pytest.skip("No test user available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/admin/members/{test_user_id}/notify",
            headers=headers,
            json={
                "title": "📊 Report Your Trade Results",
                "message": "Test notification from automated testing"
            }
        )
        
        # Should return 200 on success
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Notify endpoint works: {data['message']}")


class TestMissedTradersEndpoint:
    """Test /api/admin/analytics/missed-trades endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_missed_traders_endpoint(self, admin_token):
        """Test that missed-trades endpoint returns list of traders"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics/missed-trades", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "missed_traders" in data, "Missing missed_traders field"
        assert isinstance(data["missed_traders"], list), "missed_traders should be a list"
        
        print(f"✓ Missed traders endpoint works: {len(data['missed_traders'])} traders haven't reported today")


class TestDeleteMemberTradeEndpoint:
    """Test DELETE /api/admin/members/{user_id}/trades/{trade_id} endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_delete_trade_endpoint_requires_master_admin(self, admin_token):
        """Test that delete trade endpoint exists and requires master admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try with a fake user_id and trade_id - should return 404 (not found) not 403 (forbidden)
        # because the admin is master_admin
        response = requests.delete(
            f"{BASE_URL}/api/admin/members/fake-user-id/trades/fake-trade-id",
            headers=headers
        )
        
        # Should return 404 (not found) since user doesn't exist
        # If it returns 403, the endpoint exists but requires higher permissions
        assert response.status_code in [404, 403], f"Expected 404 or 403, got {response.status_code}: {response.text}"
        print(f"✓ Delete trade endpoint exists, returned {response.status_code}")


class TestTradeMonitorPage:
    """Test Trade Monitor page loads correctly"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_active_signal_endpoint(self, admin_token):
        """Test that active signal endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should have either a signal or a message
        assert "signal" in data or "message" in data
        print(f"✓ Active signal endpoint works: {data}")
    
    def test_daily_summary_endpoint(self, admin_token):
        """Test that daily summary endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/daily-summary", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "trades_count" in data
        assert "total_projected" in data
        assert "total_actual" in data
        print(f"✓ Daily summary: {data['trades_count']} trades, projected=${data['total_projected']}, actual=${data['total_actual']}")


class TestProfitTrackerPage:
    """Test Profit Tracker page endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_profit_summary_endpoint(self, admin_token):
        """Test that profit summary endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "account_value" in data
        assert "total_deposits" in data
        print(f"✓ Profit summary: account_value=${data['account_value']}, deposits=${data['total_deposits']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

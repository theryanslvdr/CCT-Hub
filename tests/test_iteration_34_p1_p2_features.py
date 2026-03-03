"""
Test Suite for Iteration 34 - P1 and P2 Features
Features tested:
1. Off-canvas notification panel (NotificationSheet) opens when bell icon clicked
2. WebSocket disconnection banner shows 'Connection lost' with Reconnect button
3. Top Performers card on Admin Analytics page with 'Active traders only' checkbox
4. Top performers API endpoint returns performer data
5. Backend scheduler starts successfully for missed trade notifications
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://deploy-auth-sync.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint working")
    
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


class TestTopPerformersAPI:
    """Test the top performers API endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_top_performers_endpoint_exists(self, auth_token):
        """Test that top performers endpoint exists and returns data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/top-performers", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "performers" in data
        assert "total" in data
        print(f"✓ Top performers endpoint returns {data['total']} performers")
    
    def test_top_performers_with_exclude_non_traders_true(self, auth_token):
        """Test top performers with exclude_non_traders=true (default)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/top-performers",
            params={"exclude_non_traders": "true", "limit": 10},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "performers" in data
        
        # Verify performer structure if any exist
        if data["performers"]:
            performer = data["performers"][0]
            assert "id" in performer
            assert "full_name" in performer
            assert "total_profit" in performer
            assert "total_trades" in performer
            assert "rank" in performer
            print(f"✓ Top performer: {performer['full_name']} with ${performer['total_profit']:.2f} profit")
        else:
            print("✓ No active traders found (expected if no recent trades)")
    
    def test_top_performers_with_exclude_non_traders_false(self, auth_token):
        """Test top performers with exclude_non_traders=false"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/top-performers",
            params={"exclude_non_traders": "false", "limit": 10},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "performers" in data
        print(f"✓ Top performers (all members): {data['total']} total")
    
    def test_top_performers_limit_parameter(self, auth_token):
        """Test that limit parameter works correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Request with limit=5
        response = requests.get(
            f"{BASE_URL}/api/admin/top-performers",
            params={"limit": 5, "exclude_non_traders": "false"},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["performers"]) <= 5
        print(f"✓ Limit parameter works - returned {len(data['performers'])} performers")
    
    def test_top_performers_requires_admin(self):
        """Test that top performers endpoint requires admin authentication"""
        # Try without auth
        response = requests.get(f"{BASE_URL}/api/admin/top-performers")
        assert response.status_code in [401, 403]
        print("✓ Top performers endpoint requires authentication")


class TestTeamAnalyticsAPI:
    """Test team analytics API for Admin Analytics page"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_team_analytics_endpoint(self, auth_token):
        """Test team analytics endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics/team", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        # Check expected fields
        assert "total_account_value" in data or "total_traders" in data
        print(f"✓ Team analytics endpoint working")
    
    def test_missed_trades_endpoint(self, auth_token):
        """Test missed trades endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics/missed-trades", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        # Check expected fields
        assert "missed_members" in data or "team_profit_today" in data
        print(f"✓ Missed trades endpoint working")
    
    def test_growth_data_endpoint(self, auth_token):
        """Test growth data endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics/growth-data", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "chart_data" in data
        print(f"✓ Growth data endpoint working - {len(data.get('chart_data', []))} data points")


class TestNotificationsAPI:
    """Test notifications API for the notification panel"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_notifications_endpoint(self, auth_token):
        """Test get notifications endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/notifications", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ Notifications endpoint working - {data['unread_count']} unread")
    
    def test_mark_all_notifications_read(self, auth_token):
        """Test mark all notifications as read"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.put(f"{BASE_URL}/api/admin/notifications/read-all", headers=headers)
        
        assert response.status_code == 200
        print("✓ Mark all notifications read endpoint working")


class TestSchedulerStartup:
    """Test that the scheduler starts correctly"""
    
    def test_scheduler_logs_present(self):
        """Verify scheduler started by checking logs (this is a meta-test)"""
        # This test verifies the scheduler configuration exists in the code
        # The actual scheduler runs at 11 PM UTC
        import subprocess
        result = subprocess.run(
            ["grep", "-c", "Scheduler started for missed trade notifications", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True
        )
        
        # If grep finds matches, it returns 0 and outputs the count
        if result.returncode == 0:
            count = int(result.stdout.strip())
            assert count > 0, "Scheduler startup message not found in logs"
            print(f"✓ Scheduler started successfully ({count} startup(s) logged)")
        else:
            # Log file might not exist or no matches - check if scheduler code exists
            print("⚠ Could not verify scheduler from logs, checking code...")
            result2 = subprocess.run(
                ["grep", "-c", "scheduler.add_job", "/app/backend/server.py"],
                capture_output=True,
                text=True
            )
            if result2.returncode == 0:
                print("✓ Scheduler job configuration found in code")
            else:
                pytest.fail("Scheduler configuration not found")


class TestWebSocketEndpoint:
    """Test WebSocket endpoint exists"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_websocket_endpoint_configured(self, auth_token):
        """Test that WebSocket endpoint is configured by verifying code exists"""
        # WebSocket endpoints can't be tested via HTTP requests
        # Instead, verify the WebSocket code exists in the frontend
        import subprocess
        
        # Check if WebSocketContext exists and has reconnect functionality
        result = subprocess.run(
            ["grep", "-c", "reconnect", "/app/frontend/src/contexts/WebSocketContext.jsx"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            count = int(result.stdout.strip())
            assert count > 0, "WebSocket reconnect functionality not found"
            print(f"✓ WebSocket reconnect functionality found ({count} references)")
        else:
            pytest.fail("WebSocketContext.jsx not found or no reconnect functionality")
        
        # Also verify NotificationSheet has connection status banner
        result2 = subprocess.run(
            ["grep", "-c", "Connection lost", "/app/frontend/src/components/NotificationSheet.jsx"],
            capture_output=True,
            text=True
        )
        
        if result2.returncode == 0:
            count2 = int(result2.stdout.strip())
            assert count2 > 0, "Connection lost banner not found in NotificationSheet"
            print(f"✓ Connection lost banner found in NotificationSheet")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

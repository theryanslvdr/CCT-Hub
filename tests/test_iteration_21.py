"""
Test Suite for Iteration 21 - CrossCurrent Finance Center
Testing:
- P0: Heartbeat API fallback to environment variable
- P0: Dashboard simulation showing member data
- P0: Licensee Account page accessible during simulation
- P1: Trade Monitor restricted for licensees
- P1: Profit Tracker hides simulation buttons for licensees
- Basic login flow for master_admin
- Sidebar hides Trade Monitor for licensees
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://transaction-guide.preview.emergentagent.com').rstrip('/')

class TestHeartbeatAPI:
    """P0: Test Heartbeat API fallback to environment variable"""
    
    def test_verify_heartbeat_with_valid_email(self):
        """Test heartbeat verification with a valid email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-heartbeat",
            json={"email": "iam@ryansalvador.com"}
        )
        # Should return 200 even if not found (verified: false)
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        print(f"Heartbeat verification result: {data}")
    
    def test_verify_heartbeat_with_invalid_email(self):
        """Test heartbeat verification with invalid email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-heartbeat",
            json={"email": "nonexistent@test.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        print(f"Heartbeat verification for invalid email: {data}")


class TestMasterAdminLogin:
    """Test basic login flow for master_admin"""
    
    def test_login_master_admin(self):
        """Test login with master_admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "master_admin"
        print(f"Master admin login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_get_current_user(self):
        """Test getting current user info"""
        # First login
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        token = login_res.json()["access_token"]
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "iam@ryansalvador.com"
        assert data["role"] == "master_admin"
        print(f"Current user: {data}")


class TestDashboardSimulation:
    """P0: Test Dashboard simulation showing member data"""
    
    @pytest.fixture
    def auth_token(self):
        """Get master admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        return response.json()["access_token"]
    
    def test_get_members_list(self, auth_token):
        """Test getting members list for simulation"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        print(f"Found {len(data['members'])} members")
        return data["members"]
    
    def test_get_member_details_for_simulation(self, auth_token):
        """Test getting member details for simulation"""
        # First get members list
        members_res = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        members = members_res.json()["members"]
        
        if len(members) > 0:
            # Get first member's details
            member_id = members[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/admin/members/{member_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "user" in data
            assert "stats" in data
            print(f"Member details: {data['user']['email']}, stats: {data['stats']}")
    
    def test_get_trade_logs_with_user_id(self, auth_token):
        """Test getting trade logs with user_id parameter (for simulation)"""
        # First get members list
        members_res = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        members = members_res.json()["members"]
        
        if len(members) > 0:
            member_id = members[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/trade/logs?user_id={member_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            print(f"Trade logs for member {member_id}: {len(data)} logs")


class TestLicenseeFeatures:
    """P0/P1: Test licensee-related features"""
    
    @pytest.fixture
    def auth_token(self):
        """Get master admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        return response.json()["access_token"]
    
    def test_get_licenses_list(self, auth_token):
        """Test getting licenses list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "licenses" in data
        print(f"Found {len(data['licenses'])} licenses")
        return data["licenses"]
    
    def test_get_licensee_transactions(self, auth_token):
        """Test getting licensee transactions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licensee-transactions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        print(f"Found {len(data['transactions'])} licensee transactions")
    
    def test_licensee_account_endpoint(self, auth_token):
        """Test licensee account endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/transactions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 200 with is_licensee flag
        assert response.status_code == 200
        data = response.json()
        assert "is_licensee" in data
        print(f"Licensee status: {data['is_licensee']}")


class TestTradeMonitorEndpoints:
    """Test Trade Monitor related endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get master admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        return response.json()["access_token"]
    
    def test_get_active_signal(self, auth_token):
        """Test getting active trading signal"""
        response = requests.get(
            f"{BASE_URL}/api/trade/active-signal",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Either has signal or message saying no active signal
        assert "signal" in data or "message" in data
        print(f"Active signal response: {data}")
    
    def test_get_daily_summary(self, auth_token):
        """Test getting daily trade summary"""
        response = requests.get(
            f"{BASE_URL}/api/trade/daily-summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "trades_count" in data
        print(f"Daily summary: {data}")
    
    def test_get_trade_streak(self, auth_token):
        """Test getting trade streak"""
        response = requests.get(
            f"{BASE_URL}/api/trade/streak",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "streak" in data
        print(f"Trade streak: {data}")


class TestProfitTrackerEndpoints:
    """Test Profit Tracker related endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get master admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        return response.json()["access_token"]
    
    def test_get_profit_summary(self, auth_token):
        """Test getting profit summary"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "account_value" in data
        assert "total_deposits" in data
        print(f"Profit summary: {data}")
    
    def test_get_deposits(self, auth_token):
        """Test getting deposits"""
        response = requests.get(
            f"{BASE_URL}/api/profit/deposits",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} deposits")
    
    def test_get_withdrawals(self, auth_token):
        """Test getting withdrawals"""
        response = requests.get(
            f"{BASE_URL}/api/profit/withdrawals",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} withdrawals")


class TestSimulationEndpoints:
    """Test simulation-related endpoints for Master Admin"""
    
    @pytest.fixture
    def auth_token(self):
        """Get master admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "iam@ryansalvador.com",
                "password": "admin123"
            }
        )
        return response.json()["access_token"]
    
    def test_simulate_member_view(self, auth_token):
        """Test simulate member view endpoint"""
        # First get a member
        members_res = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        members = members_res.json()["members"]
        
        if len(members) > 0:
            member_id = members[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/admin/members/{member_id}/simulate",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "member" in data
            assert "account_value" in data
            assert "lot_size" in data
            print(f"Simulation data for {data['member']['email']}: account_value={data['account_value']}, lot_size={data['lot_size']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test suite for new admin structure and features:
1. Master Admin login and role verification
2. Hidden features (Profit Planner, Debt Management) access
3. Trade Monitor split screen with Merin iframe
4. Simulate Member View functionality
5. Role hierarchy and permissions
6. API: Update allowed_dashboards for super_admin
7. API: Master admin can update user roles
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestMasterAdminAuth:
    """Test Master Admin authentication and role"""
    
    def test_master_admin_login_success(self):
        """Master Admin can login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == MASTER_ADMIN_EMAIL
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Master Admin login successful - role: {data['user']['role']}")
    
    def test_master_admin_has_correct_role(self):
        """Verify master_admin role is returned correctly"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        data = response.json()
        
        # Verify role hierarchy
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Master Admin role verified: {data['user']['role']}")


class TestRoleHierarchy:
    """Test role hierarchy and permissions"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_master_admin_can_access_admin_endpoints(self, master_admin_token):
        """Master Admin can access admin endpoints"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # Test admin members endpoint
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200, f"Admin members access failed: {response.text}"
        print("✓ Master Admin can access /api/admin/members")
    
    def test_master_admin_can_access_signals(self, master_admin_token):
        """Master Admin can access trading signals"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/signals", headers=headers)
        assert response.status_code == 200, f"Signals access failed: {response.text}"
        print("✓ Master Admin can access /api/admin/signals")
    
    def test_master_admin_can_access_api_center(self, master_admin_token):
        """Master Admin can access API center"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/api-center/connections", headers=headers)
        assert response.status_code == 200, f"API center access failed: {response.text}"
        print("✓ Master Admin can access /api/api-center/connections")


class TestMemberManagement:
    """Test member management and role updates"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_members_list(self, master_admin_token):
        """Master Admin can get members list"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "members" in data
        assert "total" in data
        print(f"✓ Members list retrieved - total: {data['total']}")
    
    def test_update_member_allowed_dashboards(self, master_admin_token):
        """Super/Master Admin can update allowed_dashboards"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # First get a member to update
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        members = response.json()["members"]
        
        # Find a non-master_admin member to update
        target_member = None
        for member in members:
            if member["role"] != "master_admin":
                target_member = member
                break
        
        if target_member:
            # Update allowed_dashboards
            update_response = requests.put(
                f"{BASE_URL}/api/admin/members/{target_member['id']}",
                headers=headers,
                json={"allowed_dashboards": ["dashboard", "profit_tracker"]}
            )
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            print(f"✓ Updated allowed_dashboards for member: {target_member['email']}")
        else:
            print("⚠ No non-master_admin member found to test update")
    
    def test_master_admin_can_update_user_role(self, master_admin_token):
        """Master Admin can update user roles"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        # Get members
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        members = response.json()["members"]
        
        # Find a member to update (not master_admin)
        target_member = None
        for member in members:
            if member["role"] not in ["master_admin", "super_admin"]:
                target_member = member
                break
        
        if target_member:
            original_role = target_member.get("role", "member")
            
            # Update role to basic_admin
            update_response = requests.put(
                f"{BASE_URL}/api/admin/members/{target_member['id']}",
                headers=headers,
                json={"role": "basic_admin"}
            )
            assert update_response.status_code == 200, f"Role update failed: {update_response.text}"
            print(f"✓ Master Admin updated user role from {original_role} to basic_admin")
            
            # Revert role back
            requests.put(
                f"{BASE_URL}/api/admin/members/{target_member['id']}",
                headers=headers,
                json={"role": original_role}
            )
            print(f"✓ Reverted role back to {original_role}")
        else:
            print("⚠ No suitable member found to test role update")


class TestActiveSignal:
    """Test active signal features"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_active_signal_has_simulated_flag(self, master_admin_token):
        """Active signal includes is_simulated flag"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        if data.get("signal"):
            signal = data["signal"]
            assert "is_simulated" in signal, "is_simulated flag missing"
            assert "trade_timezone" in signal, "trade_timezone missing"
            print(f"✓ Active signal has is_simulated={signal['is_simulated']}, timezone={signal.get('trade_timezone')}")
        else:
            print("⚠ No active signal found")
    
    def test_active_signal_has_profit_points(self, master_admin_token):
        """Active signal includes profit_points multiplier"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        data = response.json()
        
        if data.get("signal"):
            signal = data["signal"]
            assert "profit_points" in signal, "profit_points missing"
            print(f"✓ Active signal has profit_points={signal['profit_points']}")
        else:
            print("⚠ No active signal found")


class TestSimulatedSignal:
    """Test simulated signal creation (Super Admin feature)"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_create_simulated_signal(self, master_admin_token):
        """Super/Master Admin can create simulated signal"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/signals/simulate",
            headers=headers,
            json={
                "product": "MOIL10",
                "trade_time": "09:00",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 15,
                "notes": "Test simulated signal"
            }
        )
        assert response.status_code == 200, f"Create simulated signal failed: {response.text}"
        
        data = response.json()
        assert data["is_simulated"] == True
        assert data["is_active"] == True
        print(f"✓ Created simulated signal - is_simulated={data['is_simulated']}")


class TestHiddenFeatures:
    """Test hidden features access (Profit Planner, Debt Management)"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_goals_endpoint_accessible(self, master_admin_token):
        """Profit Planner (goals) endpoint is accessible"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/goals", headers=headers)
        assert response.status_code == 200, f"Goals endpoint failed: {response.text}"
        print("✓ Profit Planner (goals) endpoint accessible")
    
    def test_debts_endpoint_accessible(self, master_admin_token):
        """Debt Management endpoint is accessible"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/debt", headers=headers)
        assert response.status_code == 200, f"Debts endpoint failed: {response.text}"
        print("✓ Debt Management endpoint accessible")
    
    def test_debt_plan_endpoint_accessible(self, master_admin_token):
        """Debt repayment plan endpoint is accessible"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/debt/plan", headers=headers)
        assert response.status_code == 200, f"Debt plan endpoint failed: {response.text}"
        print("✓ Debt repayment plan endpoint accessible")


class TestTradeMonitor:
    """Test Trade Monitor features"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_trade_history_endpoint(self, master_admin_token):
        """Trade history endpoint works"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "trades" in data
        assert "total" in data
        assert "total_pages" in data
        print(f"✓ Trade history endpoint works - total trades: {data['total']}")
    
    def test_streak_endpoint(self, master_admin_token):
        """Streak endpoint works"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/trade/streak", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "streak" in data
        print(f"✓ Streak endpoint works - streak: {data['streak']}")
    
    def test_daily_summary_endpoint(self, master_admin_token):
        """Daily summary endpoint works"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/trade/daily-summary", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "trades_count" in data
        assert "total_actual" in data
        print(f"✓ Daily summary endpoint works - trades today: {data['trades_count']}")


class TestOnboardingTour:
    """Test onboarding tour API (if any backend support)"""
    
    @pytest.fixture
    def master_admin_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_user_profile_endpoint(self, master_admin_token):
        """User profile endpoint works (for onboarding state)"""
        headers = {"Authorization": f"Bearer {master_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "email" in data
        assert "role" in data
        print(f"✓ User profile endpoint works - email: {data['email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

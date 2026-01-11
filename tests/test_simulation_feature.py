"""
Test Suite for Master Admin Simulation Feature
Tests the ability for master_admin to simulate a member's view with their actual account values
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSimulationFeature:
    """Test simulation feature for master_admin"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master_admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master_admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user")
            print(f"✓ Logged in as master_admin: {self.user.get('email')}")
        else:
            pytest.skip("Master admin login failed")
    
    def test_master_admin_login(self):
        """Test master_admin can login successfully"""
        assert self.user is not None
        assert self.user.get("role") == "master_admin"
        print(f"✓ Master admin role verified: {self.user.get('role')}")
    
    def test_get_members_list(self):
        """Test getting members list"""
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200
        
        data = response.json()
        assert "members" in data
        assert "total" in data
        print(f"✓ Members list retrieved: {data.get('total')} members")
        
        # Store a member for simulation testing
        members = data.get("members", [])
        self.test_member = None
        for member in members:
            if member.get("role") == "user" or member.get("role") == "member":
                self.test_member = member
                break
        
        if self.test_member:
            print(f"✓ Found test member: {self.test_member.get('full_name')} (ID: {self.test_member.get('id')})")
        return members
    
    def test_simulate_member_endpoint_exists(self):
        """Test that simulate member endpoint exists"""
        # First get a member
        members_response = self.session.get(f"{BASE_URL}/api/admin/members")
        members = members_response.json().get("members", [])
        
        test_member = None
        for member in members:
            if member.get("role") in ["user", "member"]:
                test_member = member
                break
        
        if not test_member:
            pytest.skip("No regular member found for simulation test")
        
        # Test simulation endpoint
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate")
        assert response.status_code == 200
        print(f"✓ Simulate endpoint exists and returns 200")
        
        return response.json()
    
    def test_simulate_returns_account_value(self):
        """Test that simulation returns account_value"""
        members_response = self.session.get(f"{BASE_URL}/api/admin/members")
        members = members_response.json().get("members", [])
        
        test_member = None
        for member in members:
            if member.get("role") in ["user", "member"]:
                test_member = member
                break
        
        if not test_member:
            pytest.skip("No regular member found")
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate")
        data = response.json()
        
        assert "account_value" in data
        print(f"✓ Simulation returns account_value: ${data.get('account_value', 0):.2f}")
        
        return data
    
    def test_simulate_returns_lot_size(self):
        """Test that simulation returns lot_size"""
        members_response = self.session.get(f"{BASE_URL}/api/admin/members")
        members = members_response.json().get("members", [])
        
        test_member = None
        for member in members:
            if member.get("role") in ["user", "member"]:
                test_member = member
                break
        
        if not test_member:
            pytest.skip("No regular member found")
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate")
        data = response.json()
        
        assert "lot_size" in data
        print(f"✓ Simulation returns lot_size: {data.get('lot_size', 0):.2f}")
        
        # Verify lot_size calculation (account_value / 980)
        account_value = data.get("account_value", 0)
        lot_size = data.get("lot_size", 0)
        expected_lot_size = account_value / 980 if account_value > 0 else 0
        
        # Allow small floating point differences
        assert abs(lot_size - expected_lot_size) < 0.01, f"LOT size mismatch: {lot_size} vs expected {expected_lot_size}"
        print(f"✓ LOT size calculation verified: {account_value} / 980 = {lot_size:.2f}")
        
        return data
    
    def test_simulate_returns_total_profit(self):
        """Test that simulation returns total_profit"""
        members_response = self.session.get(f"{BASE_URL}/api/admin/members")
        members = members_response.json().get("members", [])
        
        test_member = None
        for member in members:
            if member.get("role") in ["user", "member"]:
                test_member = member
                break
        
        if not test_member:
            pytest.skip("No regular member found")
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate")
        data = response.json()
        
        assert "total_profit" in data
        print(f"✓ Simulation returns total_profit: ${data.get('total_profit', 0):.2f}")
        
        return data
    
    def test_simulate_returns_summary(self):
        """Test that simulation returns summary with total_trades"""
        members_response = self.session.get(f"{BASE_URL}/api/admin/members")
        members = members_response.json().get("members", [])
        
        test_member = None
        for member in members:
            if member.get("role") in ["user", "member"]:
                test_member = member
                break
        
        if not test_member:
            pytest.skip("No regular member found")
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate")
        data = response.json()
        
        assert "summary" in data
        summary = data.get("summary", {})
        assert "total_trades" in summary
        print(f"✓ Simulation returns summary with total_trades: {summary.get('total_trades', 0)}")
        
        return data
    
    def test_simulate_returns_trades_list(self):
        """Test that simulation returns trades list"""
        members_response = self.session.get(f"{BASE_URL}/api/admin/members")
        members = members_response.json().get("members", [])
        
        test_member = None
        for member in members:
            if member.get("role") in ["user", "member"]:
                test_member = member
                break
        
        if not test_member:
            pytest.skip("No regular member found")
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate")
        data = response.json()
        
        assert "trades" in data
        trades = data.get("trades", [])
        print(f"✓ Simulation returns trades list: {len(trades)} trades")
        
        return data
    
    def test_members_table_has_account_value(self):
        """Test that members list includes account_value for master_admin"""
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        data = response.json()
        
        members = data.get("members", [])
        if len(members) > 0:
            # Check if account_value is present in member data
            first_member = members[0]
            assert "account_value" in first_member, "account_value should be in member data for master_admin"
            print(f"✓ Members list includes account_value: ${first_member.get('account_value', 0):.2f}")
        else:
            print("⚠ No members found to verify account_value")
    
    def test_analytics_archive_endpoint(self):
        """Test that analytics archive endpoint exists"""
        response = self.session.post(f"{BASE_URL}/api/admin/trades/archive")
        # Should return 200 even if no trades to archive
        assert response.status_code in [200, 201]
        print(f"✓ Archive endpoint works: {response.status_code}")


class TestProfitTrackerSimulation:
    """Test that Profit Tracker page uses simulated values"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master_admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master_admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user")
        else:
            pytest.skip("Master admin login failed")
    
    def test_profit_summary_endpoint(self):
        """Test profit summary endpoint returns data"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "account_value" in data
        print(f"✓ Profit summary returns account_value: ${data.get('account_value', 0):.2f}")
        
        return data


class TestTradeMonitorSimulation:
    """Test that Trade Monitor page uses simulated values"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master_admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master_admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user")
        else:
            pytest.skip("Master admin login failed")
    
    def test_active_signal_endpoint(self):
        """Test active signal endpoint"""
        response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        print(f"✓ Active signal endpoint works")
        
        return response.json()
    
    def test_daily_summary_endpoint(self):
        """Test daily summary endpoint"""
        response = self.session.get(f"{BASE_URL}/api/trade/daily-summary")
        assert response.status_code == 200
        print(f"✓ Daily summary endpoint works")
        
        return response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

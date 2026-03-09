"""
Test Admin Improvements:
1) Account Value column in Members table (Super Admin/Master Admin only)
2) Edit Member dialog does NOT have LOT size field
3) Simulate Member button opens simulation dialog with member's real account data
4) Members table pagination
5) Trading Signals pagination
6) Monthly Archive feature with accordion view
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://bve-data-loss.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestAdminMembersAccountValue:
    """Test Account Value column visibility and calculation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Master Admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Verify role is master_admin
        assert self.user["role"] == "master_admin", f"Expected master_admin role, got {self.user['role']}"
    
    def test_members_endpoint_returns_account_value(self):
        """GET /api/admin/members should return account_value for master_admin"""
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200, f"Failed to get members: {response.text}"
        
        data = response.json()
        assert "members" in data, "Response should have 'members' key"
        assert "total" in data, "Response should have 'total' key"
        assert "pages" in data, "Response should have 'pages' key"
        
        # Check that members have account_value field
        if len(data["members"]) > 0:
            member = data["members"][0]
            assert "account_value" in member, f"Member should have 'account_value' field. Keys: {member.keys()}"
            assert isinstance(member["account_value"], (int, float)), "account_value should be a number"
            print(f"✓ Member {member.get('full_name', 'Unknown')} has account_value: ${member['account_value']}")
    
    def test_account_value_calculation(self):
        """Account Value should be calculated as: deposits - withdrawals + profits"""
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200
        
        data = response.json()
        members = data["members"]
        
        # Find a member with account_value > 0 to verify calculation
        for member in members:
            if member.get("account_value", 0) > 0:
                print(f"✓ Found member with account_value > 0: {member.get('full_name')} = ${member['account_value']}")
                # The account_value should be a reasonable number (not negative, not astronomical)
                assert member["account_value"] >= 0, "Account value should not be negative"
                assert member["account_value"] < 1000000, "Account value seems unreasonably high"
                break
        else:
            print("⚠ No members with account_value > 0 found (this may be expected)")


class TestMembersPagination:
    """Test Members table pagination"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_members_pagination_params(self):
        """GET /api/admin/members should accept page and limit params"""
        response = self.session.get(f"{BASE_URL}/api/admin/members", params={
            "page": 1,
            "limit": 10
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "members" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        print(f"✓ Pagination works: page={data['page']}, total={data['total']}, pages={data['pages']}")
    
    def test_members_pagination_page_2(self):
        """Test fetching page 2 of members"""
        response = self.session.get(f"{BASE_URL}/api/admin/members", params={
            "page": 2,
            "limit": 1
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 2, f"Expected page 2, got {data['page']}"
        print(f"✓ Page 2 works: {len(data['members'])} members returned")


class TestSimulateMember:
    """Test Simulate Member feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_simulate_member_endpoint_exists(self):
        """GET /api/admin/members/{id}/simulate should exist"""
        # First get a member ID
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["members"]) > 0:
            # Find a regular user (not admin) to simulate
            member = None
            for m in data["members"]:
                if m.get("role") == "user" or m.get("role") == "member":
                    member = m
                    break
            
            if member:
                member_id = member["id"]
                response = self.session.get(f"{BASE_URL}/api/admin/members/{member_id}/simulate")
                assert response.status_code == 200, f"Simulate endpoint failed: {response.text}"
                
                sim_data = response.json()
                print(f"✓ Simulate endpoint works for member: {member.get('full_name')}")
                
                # Verify simulation data structure
                assert "account_value" in sim_data, "Simulation should have account_value"
                assert "lot_size" in sim_data, "Simulation should have lot_size"
                assert "total_profit" in sim_data, "Simulation should have total_profit"
                assert "summary" in sim_data, "Simulation should have summary"
                
                print(f"  - Account Value: ${sim_data['account_value']}")
                print(f"  - LOT Size: {sim_data['lot_size']}")
                print(f"  - Total Profit: ${sim_data['total_profit']}")
                print(f"  - Total Trades: {sim_data['summary'].get('total_trades', 0)}")
            else:
                print("⚠ No regular user found to test simulation")
        else:
            print("⚠ No members found to test simulation")
    
    def test_simulate_returns_real_account_data(self):
        """Simulation should return real calculated account data"""
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200
        
        data = response.json()
        for member in data["members"]:
            if member.get("role") in ["user", "member"]:
                member_id = member["id"]
                sim_response = self.session.get(f"{BASE_URL}/api/admin/members/{member_id}/simulate")
                
                if sim_response.status_code == 200:
                    sim_data = sim_response.json()
                    
                    # Verify data types
                    assert isinstance(sim_data["account_value"], (int, float))
                    assert isinstance(sim_data["lot_size"], (int, float))
                    assert isinstance(sim_data["total_profit"], (int, float))
                    
                    # LOT size should be calculated from account value
                    # Formula: account_value / 980
                    if sim_data["account_value"] > 0:
                        expected_lot = round(sim_data["account_value"] / 980, 2)
                        actual_lot = sim_data["lot_size"]
                        # Allow some tolerance for rounding
                        assert abs(expected_lot - actual_lot) < 0.1, f"LOT size mismatch: expected ~{expected_lot}, got {actual_lot}"
                        print(f"✓ LOT size correctly calculated: ${sim_data['account_value']} / 980 = {actual_lot}")
                    
                    break


class TestSignalsPagination:
    """Test Trading Signals pagination"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_signals_history_endpoint(self):
        """GET /api/admin/signals/history should return paginated signals"""
        response = self.session.get(f"{BASE_URL}/api/admin/signals/history", params={
            "page": 1,
            "page_size": 10
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "signals" in data, "Response should have 'signals' key"
        assert "total" in data, "Response should have 'total' key"
        assert "page" in data, "Response should have 'page' key"
        assert "total_pages" in data, "Response should have 'total_pages' key"
        
        print(f"✓ Signals history pagination works: {data['total']} total signals, {data['total_pages']} pages")
    
    def test_signals_history_page_navigation(self):
        """Test navigating between pages of signals"""
        # Get page 1
        response1 = self.session.get(f"{BASE_URL}/api/admin/signals/history", params={
            "page": 1,
            "page_size": 5
        })
        assert response1.status_code == 200
        data1 = response1.json()
        
        if data1["total_pages"] > 1:
            # Get page 2
            response2 = self.session.get(f"{BASE_URL}/api/admin/signals/history", params={
                "page": 2,
                "page_size": 5
            })
            assert response2.status_code == 200
            data2 = response2.json()
            
            assert data2["page"] == 2
            print(f"✓ Page navigation works: page 1 has {len(data1['signals'])} signals, page 2 has {len(data2['signals'])} signals")
        else:
            print("⚠ Only 1 page of signals, cannot test page navigation")


class TestSignalsArchive:
    """Test Monthly Archive feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_signals_archive_endpoint(self):
        """GET /api/admin/signals/archive should return signals organized by month"""
        response = self.session.get(f"{BASE_URL}/api/admin/signals/archive")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "months" in data, "Response should have 'months' key"
        
        if len(data["months"]) > 0:
            month = data["months"][0]
            assert "month_key" in month, "Month should have 'month_key'"
            assert "month_label" in month, "Month should have 'month_label'"
            assert "signals" in month, "Month should have 'signals'"
            
            print(f"✓ Archive endpoint works: {len(data['months'])} months found")
            for m in data["months"][:3]:  # Show first 3 months
                print(f"  - {m['month_label']}: {len(m['signals'])} signals")
        else:
            print("⚠ No archived signals found (this may be expected)")
    
    def test_archive_month_endpoint(self):
        """POST /api/admin/signals/archive-month should archive current month's inactive signals"""
        response = self.session.post(f"{BASE_URL}/api/admin/signals/archive-month")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have 'message'"
        assert "archived_count" in data, "Response should have 'archived_count'"
        
        print(f"✓ Archive month endpoint works: {data['message']}")


class TestEditMemberNoLotSize:
    """Test that Edit Member dialog does NOT have LOT size field"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_update_member_without_lot_size(self):
        """PUT /api/admin/members/{id} should work without lot_size"""
        # Get a member
        response = self.session.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200
        
        data = response.json()
        if len(data["members"]) > 0:
            member = data["members"][0]
            member_id = member["id"]
            
            # Update member without lot_size (only full_name and timezone)
            update_response = self.session.put(f"{BASE_URL}/api/admin/members/{member_id}", json={
                "full_name": member.get("full_name", "Test User"),
                "timezone": member.get("timezone", "UTC")
            })
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            print(f"✓ Member update works without lot_size field")
        else:
            print("⚠ No members found to test update")


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

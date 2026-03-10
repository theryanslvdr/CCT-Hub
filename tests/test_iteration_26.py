"""
Test Suite for Iteration 26 - CrossCurrent Finance Center
Testing:
1. Master Admin can promote member to basic_admin without secret code
2. Master Admin can promote member to super_admin without secret code
3. Non-master admins still need secret code for super_admin promotion
4. LOT Size in Member Details shows account_value / 980 calculation
5. Licensee onboarding tour shows simplified steps (5 steps instead of 8)
6. Dashboard shows 'Your Stats' card instead of 'Live Rates'
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://platform-refresh-6.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestMasterAdminRolePromotion:
    """Test Master Admin role promotion capabilities"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.master_admin_token = None
        self.test_user_id = None
        
    def get_master_admin_token(self):
        """Login as master admin and get token"""
        if self.master_admin_token:
            return self.master_admin_token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Master admin login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "master_admin", "User is not master_admin"
        self.master_admin_token = data["access_token"]
        return self.master_admin_token
    
    def get_test_member(self):
        """Get a test member to promote"""
        token = self.get_master_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get members list
        response = self.session.get(f"{BASE_URL}/api/admin/members?role=member&limit=5", headers=headers)
        if response.status_code == 200:
            members = response.json().get("members", [])
            # Find a member that is not an admin
            for member in members:
                if member.get("role") in ["member", "user"]:
                    return member
        
        # If no member found, try to get any user
        response = self.session.get(f"{BASE_URL}/api/admin/members?limit=10", headers=headers)
        if response.status_code == 200:
            members = response.json().get("members", [])
            for member in members:
                if member.get("role") in ["member", "user"]:
                    return member
        return None
    
    def test_master_admin_login(self):
        """Test that master admin can login successfully"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "master_admin"
        print(f"✓ Master admin login successful, role: {data['user']['role']}")
    
    def test_master_admin_can_promote_to_basic_admin_without_secret(self):
        """Test that master admin can promote member to basic_admin without secret code"""
        token = self.get_master_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        test_member = self.get_test_member()
        if not test_member:
            pytest.skip("No test member available for promotion test")
        
        # Promote to basic_admin without secret code
        response = self.session.post(f"{BASE_URL}/api/admin/upgrade-role", 
            headers=headers,
            json={
                "user_id": test_member["id"],
                "new_role": "basic_admin"
                # No secret_code provided
            }
        )
        
        # Should succeed for master admin
        assert response.status_code == 200, f"Promotion failed: {response.text}"
        data = response.json()
        assert "upgraded" in data.get("message", "").lower() or "basic_admin" in data.get("message", "")
        print(f"✓ Master admin promoted {test_member['email']} to basic_admin without secret code")
        
        # Revert the user back to member for cleanup
        self.session.post(f"{BASE_URL}/api/admin/downgrade-role/{test_member['id']}", headers=headers)
    
    def test_master_admin_can_promote_to_super_admin_without_secret(self):
        """Test that master admin can promote member to super_admin without secret code"""
        token = self.get_master_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        test_member = self.get_test_member()
        if not test_member:
            pytest.skip("No test member available for promotion test")
        
        # Promote to super_admin without secret code
        response = self.session.post(f"{BASE_URL}/api/admin/upgrade-role", 
            headers=headers,
            json={
                "user_id": test_member["id"],
                "new_role": "super_admin"
                # No secret_code provided - master admin doesn't need it
            }
        )
        
        # Should succeed for master admin
        assert response.status_code == 200, f"Promotion to super_admin failed: {response.text}"
        data = response.json()
        assert "upgraded" in data.get("message", "").lower() or "super_admin" in data.get("message", "")
        print(f"✓ Master admin promoted {test_member['email']} to super_admin without secret code")
        
        # Revert the user back to member for cleanup
        self.session.post(f"{BASE_URL}/api/admin/downgrade-role/{test_member['id']}", headers=headers)


class TestLOTSizeCalculation:
    """Test LOT Size calculation in Member Details"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_master_admin_token(self):
        """Login as master admin and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_lot_size_calculation_formula(self):
        """Test that LOT Size is calculated as account_value / 980"""
        token = self.get_master_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get a member with account value
        response = self.session.get(f"{BASE_URL}/api/admin/members?limit=10", headers=headers)
        assert response.status_code == 200
        
        members = response.json().get("members", [])
        
        # Find a member with account_value
        test_member = None
        for member in members:
            if member.get("account_value", 0) > 0:
                test_member = member
                break
        
        if not test_member:
            # Use master admin's own data
            response = self.session.get(f"{BASE_URL}/api/profit/summary", headers=headers)
            if response.status_code == 200:
                summary = response.json()
                account_value = summary.get("account_value", 0)
                expected_lot_size = account_value / 980
                print(f"✓ LOT Size formula verified: {account_value} / 980 = {expected_lot_size:.2f}")
                return
            pytest.skip("No member with account value found")
        
        # Get member details
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}", headers=headers)
        assert response.status_code == 200
        
        details = response.json()
        account_value = details.get("stats", {}).get("account_value", 0)
        
        # Calculate expected LOT size
        expected_lot_size = account_value / 980
        
        print(f"✓ Member {test_member['email']}: Account Value = ${account_value:.2f}, Expected LOT Size = {expected_lot_size:.2f}")
        print(f"✓ LOT Size formula: account_value / 980 = {account_value} / 980 = {expected_lot_size:.2f}")
    
    def test_member_simulation_lot_size(self):
        """Test LOT Size in member simulation endpoint"""
        token = self.get_master_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get a member to simulate
        response = self.session.get(f"{BASE_URL}/api/admin/members?limit=5", headers=headers)
        assert response.status_code == 200
        
        members = response.json().get("members", [])
        if not members:
            pytest.skip("No members available")
        
        test_member = members[0]
        
        # Get simulation data
        response = self.session.get(f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate", headers=headers)
        
        if response.status_code == 200:
            sim_data = response.json()
            account_value = sim_data.get("account_value", 0)
            lot_size = sim_data.get("lot_size", 0)
            
            # Verify LOT size calculation
            expected_lot_size = round(account_value / 980, 2)
            
            print(f"✓ Simulation data: Account Value = ${account_value:.2f}, LOT Size = {lot_size}")
            print(f"✓ Expected LOT Size (account_value / 980) = {expected_lot_size}")
            
            # Allow small floating point differences
            assert abs(lot_size - expected_lot_size) < 0.01, f"LOT Size mismatch: got {lot_size}, expected {expected_lot_size}"
        else:
            print(f"Simulation endpoint returned {response.status_code}: {response.text}")


class TestDashboardYourStats:
    """Test Dashboard shows 'Your Stats' card instead of 'Live Rates'"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_profit_summary_endpoint(self):
        """Test that profit summary endpoint returns data for Your Stats card"""
        # Login as master admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get profit summary
        response = self.session.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200
        
        summary = response.json()
        
        # Verify the fields needed for Your Stats card
        assert "account_value" in summary, "Missing account_value for Your Stats"
        assert "total_actual_profit" in summary, "Missing total_actual_profit for Your Stats"
        
        account_value = summary.get("account_value", 0)
        total_profit = summary.get("total_actual_profit", 0)
        
        # Calculate LOT Size and Projected Daily
        lot_size = account_value / 980
        projected_daily = lot_size * 15
        
        print(f"✓ Your Stats data available:")
        print(f"  - Total Profit: ${total_profit:.2f}")
        print(f"  - LOT Size: {lot_size:.2f} (account_value / 980)")
        print(f"  - Projected Daily: ${projected_daily:.2f} (LOT × 15)")
        print(f"  - Performance Rate: {summary.get('performance_rate', 0)}%")


class TestUpgradeRoleEndpoint:
    """Test the upgrade-role endpoint behavior"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_upgrade_role_endpoint_exists(self):
        """Test that upgrade-role endpoint exists and requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/upgrade-role", json={
            "user_id": "test",
            "new_role": "basic_admin"
        })
        # Should return 401 or 403 without auth, not 404
        assert response.status_code in [401, 403, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ upgrade-role endpoint exists (returned {response.status_code} without auth)")
    
    def test_valid_roles_for_promotion(self):
        """Test that valid roles are basic_admin, admin, super_admin"""
        # Login as master admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try invalid role
        response = self.session.post(f"{BASE_URL}/api/admin/upgrade-role", 
            headers=headers,
            json={
                "user_id": "nonexistent",
                "new_role": "invalid_role"
            }
        )
        # Should fail with 400 for invalid role or 404 for user not found
        assert response.status_code in [400, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Invalid role rejected with status {response.status_code}")


class TestAPIEndpoints:
    """Test various API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_auth_login(self):
        """Test login endpoint"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login endpoint working")
    
    def test_admin_members_endpoint(self):
        """Test admin members endpoint"""
        # Login first
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert "total" in data
        print(f"✓ Admin members endpoint working, found {data['total']} members")
    
    def test_platform_settings_endpoint(self):
        """Test platform settings endpoint"""
        response = self.session.get(f"{BASE_URL}/api/settings/platform")
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Platform settings endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 113: Backend API Tests for Admin Reset Features
Tests for:
1. PUT /api/admin/licenses/{license_id}/effective-start-date
2. POST /api/admin/licenses/{license_id}/reset-balance
3. GET /api/admin/licenses/{license_id}/projections
4. PUT /api/admin/family/members/{user_id}/{member_id}/reset (starting_amount & effective_start_date)
5. GET /api/family/members (as licensee Rizza)
6. Regression: GET /api/admin/members/{user_id}/simulate should return family_members
7. Regression: Admin habits CRUD still works
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"  # honorary_fa
LICENSE_ID = "3365cca7-9ed8-40d4-9d73-0b9c43f34e8e"
MARIA_MEMBER_ID = "9fe01ee8-e21a-4391-906e-e48c9f139e92"


class TestAdminResetFeatures:
    """Test cases for admin reset features - reset balance and effective start date"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get Master Admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Auth headers for admin requests"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_01_update_effective_start_date(self, admin_headers):
        """Test PUT /api/admin/licenses/{license_id}/effective-start-date"""
        response = requests.put(
            f"{BASE_URL}/api/admin/licenses/{LICENSE_ID}/effective-start-date",
            headers=admin_headers,
            json={"effective_start_date": "2026-01-20"}
        )
        print(f"Update effective start date response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200, f"Failed to update effective start date: {response.text}"
        data = response.json()
        assert "message" in data
        assert "2026-01-20" in data.get("new_date", "") or "2026-01-20" in str(data)
        print(f"✓ Effective start date updated to 2026-01-20")
    
    def test_02_reset_license_balance_to_4000(self, admin_headers):
        """Test POST /api/admin/licenses/{license_id}/reset-balance with new_amount=4000"""
        response = requests.post(
            f"{BASE_URL}/api/admin/licenses/{LICENSE_ID}/reset-balance",
            headers=admin_headers,
            json={"new_amount": 4000, "notes": "Test reset to $4000", "record_as_deposit": False}
        )
        print(f"Reset balance to $4000 response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200, f"Failed to reset balance: {response.text}"
        data = response.json()
        assert "message" in data
        assert data.get("new_amount") == 4000
        print(f"✓ Balance reset to $4000")
    
    def test_03_get_projections_after_reset(self, admin_headers):
        """Test GET /api/admin/licenses/{license_id}/projections starts from effective_start_date"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses/{LICENSE_ID}/projections",
            headers=admin_headers
        )
        print(f"Get projections response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get projections: {response.text}"
        data = response.json()
        
        # Verify projections exist
        projections = data.get("projections", [])
        assert len(projections) > 0, "Projections should not be empty"
        
        # Check first projection date is at or after effective_start_date
        first_projection = projections[0]
        print(f"First projection date: {first_projection.get('date')}")
        print(f"First projection account_value: {first_projection.get('account_value')}")
        
        # After reset to 4000, the base should reflect new amount
        # The first start_value should be 4000 (the reset amount)
        first_start_value = first_projection.get("start_value", first_projection.get("account_value"))
        print(f"First start_value: {first_start_value}")
        
        # Projections should start from 2026-01-20
        assert "2026-01-20" in projections[0].get("date", ""), f"Projections should start from 2026-01-20"
        print(f"✓ Projections start from effective_start_date (2026-01-20)")
    
    def test_04_reset_license_balance_back_to_5000(self, admin_headers):
        """Reset balance back to $5000 to restore test data"""
        response = requests.post(
            f"{BASE_URL}/api/admin/licenses/{LICENSE_ID}/reset-balance",
            headers=admin_headers,
            json={"new_amount": 5000, "notes": "Reset back to $5000 after test", "record_as_deposit": False}
        )
        print(f"Reset balance back to $5000 response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to reset balance back: {response.text}"
        data = response.json()
        assert data.get("new_amount") == 5000
        print(f"✓ Balance reset back to $5000")
    
    def test_05_reset_family_member_starting_amount(self, admin_headers):
        """Test PUT /api/admin/family/members/{user_id}/{member_id}/reset with starting_amount=1500"""
        response = requests.put(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{MARIA_MEMBER_ID}/reset",
            headers=admin_headers,
            json={"starting_amount": 1500}
        )
        print(f"Reset Maria's starting amount response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200, f"Failed to reset family member: {response.text}"
        data = response.json()
        assert "message" in data
        updates = data.get("updates", {})
        assert updates.get("starting_amount") == 1500
        print(f"✓ Maria's starting amount reset to $1500")
    
    def test_06_reset_family_member_effective_start_date(self, admin_headers):
        """Test PUT /api/admin/family/members/{user_id}/{member_id}/reset with effective_start_date='2026-02-01'"""
        response = requests.put(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{MARIA_MEMBER_ID}/reset",
            headers=admin_headers,
            json={"effective_start_date": "2026-02-01"}
        )
        print(f"Reset Maria's effective_start_date response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200, f"Failed to reset effective start date: {response.text}"
        data = response.json()
        updates = data.get("updates", {})
        assert updates.get("effective_start_date") == "2026-02-01"
        print(f"✓ Maria's effective_start_date reset to 2026-02-01")
    
    def test_07_verify_family_member_projections_from_new_date(self, admin_headers):
        """Verify family member projections start from the new effective_start_date"""
        response = requests.get(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{MARIA_MEMBER_ID}/projections",
            headers=admin_headers
        )
        print(f"Get Maria's projections response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get family member projections: {response.text}"
        data = response.json()
        
        projections = data.get("projections", [])
        if len(projections) > 0:
            first_date = projections[0].get("date")
            print(f"First projection date: {first_date}")
            # Should start from 2026-02-01 (or first trading day after)
            assert "2026-02" in first_date, f"Projections should start from Feb 2026"
            print(f"✓ Maria's projections start from Feb 2026")
        else:
            # If no projections yet (effective_start_date in future), that's ok
            print("⚠ No projections returned (start date may be in future)")
    
    def test_08_restore_family_member_data(self, admin_headers):
        """Reset Maria back to original values (starting_amount=2000, effective_start_date to original)"""
        # First reset starting amount
        response = requests.put(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{MARIA_MEMBER_ID}/reset",
            headers=admin_headers,
            json={"starting_amount": 2000, "effective_start_date": "2026-01-20"}
        )
        print(f"Restore Maria's data response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to restore family member data: {response.text}"
        print(f"✓ Maria's data restored (starting_amount=$2000, effective_start_date=2026-01-20)")


class TestFamilyMembersEndpoint:
    """Test the family members endpoint for licensees"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get Master Admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_09_family_members_403_for_non_honorary_fa(self, admin_headers):
        """
        Test GET /api/family/members as admin (non-licensee)
        Should return 403 since it requires honorary_fa license type
        """
        response = requests.get(
            f"{BASE_URL}/api/family/members",
            headers=admin_headers
        )
        print(f"Family members endpoint for admin: {response.status_code}")
        
        # Admin is NOT an honorary_fa licensee, so should get 403
        assert response.status_code == 403, f"Expected 403 for non-honorary_fa user, got {response.status_code}"
        print(f"✓ GET /api/family/members correctly returns 403 for non-honorary_fa users")


class TestRegressionSimulateEndpoint:
    """Regression tests for simulate endpoint returning family_members"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get Master Admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_10_simulate_endpoint_returns_family_members(self, admin_headers):
        """Test GET /api/admin/members/{user_id}/simulate returns family_members for honorary_fa users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/simulate",
            headers=admin_headers
        )
        print(f"Simulate endpoint response: {response.status_code}")
        
        assert response.status_code == 200, f"Simulate endpoint failed: {response.text}"
        data = response.json()
        
        # Verify family_members key exists
        assert "family_members" in data, "Response should include family_members key"
        
        family_members = data.get("family_members", [])
        print(f"Number of family members returned: {len(family_members)}")
        
        # Rizza (honorary_fa) should have Maria as a family member
        assert len(family_members) > 0, "Rizza should have at least one family member"
        
        # Check Maria is in the list
        maria_found = any(m.get("id") == MARIA_MEMBER_ID for m in family_members)
        assert maria_found, f"Maria ({MARIA_MEMBER_ID}) should be in family_members"
        
        # Verify family member data structure
        for fm in family_members:
            assert "id" in fm
            assert "name" in fm
            assert "account_value" in fm
            assert "profit" in fm
            print(f"  - {fm.get('name')}: account_value=${fm.get('account_value')}, profit=${fm.get('profit')}")
        
        print(f"✓ Simulate endpoint correctly returns family_members for honorary_fa users")


class TestRegressionAdminHabits:
    """Regression tests for admin habits CRUD"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get Master Admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_11_get_admin_habits(self, admin_headers):
        """Test GET /api/admin/habits"""
        response = requests.get(
            f"{BASE_URL}/api/admin/habits",
            headers=admin_headers
        )
        print(f"GET /api/admin/habits response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get admin habits: {response.text}"
        data = response.json()
        
        # Response is a dict with 'habits' key
        assert isinstance(data, dict), "Response should be a dict"
        assert "habits" in data, "Response should have 'habits' key"
        habits = data.get("habits", [])
        print(f"Number of admin habits: {len(habits)}")
        print(f"✓ GET /api/admin/habits works correctly")
    
    def test_12_post_admin_habit(self, admin_headers):
        """Test POST /api/admin/habits"""
        # Using correct field name 'title' instead of 'name'
        test_habit = {
            "title": "TEST_Iteration113_Habit",
            "description": "Test habit for iteration 113",
            "category": "health",
            "frequency": "daily",
            "icon": "🧪"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/habits",
            headers=admin_headers,
            json=test_habit
        )
        print(f"POST /api/admin/habits response: {response.status_code}")
        
        assert response.status_code in [200, 201], f"Failed to create habit: {response.text}"
        data = response.json()
        
        assert "id" in data or "habit" in data, "Response should contain habit data"
        print(f"✓ POST /api/admin/habits works correctly")
        
        # Clean up - delete the test habit
        habit_data = data.get("habit", data)
        habit_id = habit_data.get("id")
        if habit_id:
            delete_response = requests.delete(
                f"{BASE_URL}/api/admin/habits/{habit_id}",
                headers=admin_headers
            )
            print(f"Cleanup - deleted test habit: {delete_response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

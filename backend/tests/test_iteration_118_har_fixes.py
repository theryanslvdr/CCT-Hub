"""
Iteration 118: HAR File Reported Issues Tests
- Password Reset (Forgot Password) flow
- Family Member add/remove via admin endpoints when simulating
- Admin year projections with user_id parameter

Credentials:
- Admin: iam@ryansalvador.com / admin123
- Licensee (Rizza): rizza.miles@gmail.com / rizza123
- Rizza user_id: 19ccb9d7-139f-4918-a662-ad72483010b1
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://referral-rewards-34.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"


class TestForgotPasswordFlow:
    """Tests for forgot-password and reset-password endpoints"""
    
    def test_forgot_password_existing_user(self):
        """POST /api/auth/forgot-password returns 200 with token for existing user"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": LICENSEE_EMAIL
        })
        print(f"Forgot password response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "token" in data
        # For existing user, token should be returned (not None)
        assert data["token"] is not None
        assert len(data["token"]) > 0  # UUID format
        
        # Store token for next test
        self.reset_token = data["token"]
        return data["token"]
    
    def test_forgot_password_nonexisting_user(self):
        """POST /api/auth/forgot-password returns 200 with null token for non-existing user"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent@example.com"
        })
        print(f"Forgot password (nonexistent) response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Security best practice: don't reveal if email exists
        assert data["token"] is None
    
    def test_reset_password_valid_token(self):
        """POST /api/auth/reset-password resets password with valid token"""
        # First get a valid token
        forgot_response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": LICENSEE_EMAIL
        })
        assert forgot_response.status_code == 200
        token = forgot_response.json()["token"]
        assert token is not None
        
        # Reset password
        new_password = LICENSEE_PASSWORD  # Reset back to original
        reset_response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": token,
            "new_password": new_password
        })
        print(f"Reset password response status: {reset_response.status_code}")
        print(f"Response body: {reset_response.json()}")
        
        assert reset_response.status_code == 200
        data = reset_response.json()
        assert "message" in data
        assert "success" in data["message"].lower()
        
        # Verify login works with new password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": new_password
        })
        assert login_response.status_code == 200
    
    def test_reset_password_invalid_token(self):
        """POST /api/auth/reset-password returns 400 for invalid token"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "invalid-token-12345",
            "new_password": "newpassword123"
        })
        print(f"Reset with invalid token status: {response.status_code}")
        
        assert response.status_code == 400
    
    def test_reset_password_short_password(self):
        """POST /api/auth/reset-password rejects short passwords"""
        # Get a valid token
        forgot_response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": LICENSEE_EMAIL
        })
        token = forgot_response.json()["token"]
        
        # Try short password
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": token,
            "new_password": "123"
        })
        print(f"Reset with short password status: {response.status_code}")
        
        assert response.status_code == 400


class TestAdminFamilyMemberEndpoints:
    """Tests for admin family member endpoints (used during simulation)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        self.admin_token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_get_family_members(self):
        """GET /api/admin/family/members/{user_id} returns family members for Rizza"""
        response = requests.get(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=self.headers
        )
        print(f"Admin get family members status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "family_members" in data
        assert isinstance(data["family_members"], list)
        
        # Check existing family member (Maria Miles)
        if len(data["family_members"]) > 0:
            member = data["family_members"][0]
            assert "id" in member
            assert "name" in member
            assert "account_value" in member
            assert "profit" in member
    
    def test_admin_add_family_member(self):
        """POST /api/admin/family/members/{user_id} adds family member with deposit_date"""
        test_name = f"TEST_HarFix_{uuid.uuid4().hex[:8]}"
        test_data = {
            "name": test_name,
            "relationship": "sibling",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "starting_amount": 1500.00,
            "deposit_date": "2026-01-15"  # Wednesday
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=self.headers,
            json=test_data
        )
        print(f"Admin add family member status: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "member" in data
        member = data["member"]
        assert member["name"] == test_name
        assert member["starting_amount"] == 1500.00
        assert member["deposit_date"] == "2026-01-15"
        # Effective start should be next trading day (Thursday 2026-01-16)
        assert member["effective_start_date"] == "2026-01-16"
        
        # Store for cleanup
        self.test_member_id = member["id"]
        return member["id"]
    
    def test_admin_add_member_then_delete(self):
        """Full add -> delete cycle for admin family member endpoint"""
        # Add test member
        test_name = f"TEST_DeleteMe_{uuid.uuid4().hex[:8]}"
        add_response = requests.post(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=self.headers,
            json={
                "name": test_name,
                "relationship": "other",
                "starting_amount": 500.00,
                "deposit_date": "2026-01-20"
            }
        )
        assert add_response.status_code == 200
        member_id = add_response.json()["member"]["id"]
        
        # Verify GET returns the new member
        get_response = requests.get(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=self.headers
        )
        assert get_response.status_code == 200
        members = get_response.json()["family_members"]
        member_ids = [m["id"] for m in members]
        assert member_id in member_ids
        
        # Delete the member
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{member_id}",
            headers=self.headers
        )
        print(f"Admin delete family member status: {delete_response.status_code}")
        print(f"Response body: {delete_response.json()}")
        
        assert delete_response.status_code == 200
        
        # Verify member is no longer active
        get_after_response = requests.get(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=self.headers
        )
        members_after = get_after_response.json()["family_members"]
        member_ids_after = [m["id"] for m in members_after]
        assert member_id not in member_ids_after
    
    def test_admin_delete_nonexistent_member(self):
        """DELETE /api/admin/family/members/{user_id}/{member_id} returns 404 for nonexistent"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/nonexistent-id-12345",
            headers=self.headers
        )
        print(f"Delete nonexistent member status: {response.status_code}")
        
        assert response.status_code == 404


class TestAdminYearProjections:
    """Tests for admin year projections with user_id parameter"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        self.admin_token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_year_projections_with_user_id(self):
        """GET /api/profit/licensee/year-projections?user_id=xxx returns projections"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            headers=self.headers,
            params={"user_id": RIZZA_USER_ID}
        )
        print(f"Year projections status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Keys in response: {list(data.keys())}")
            if "projections" in data and data["projections"]:
                print(f"Sample projection: {data['projections'][0]}")
        
        assert response.status_code == 200
        data = response.json()
        assert "projections" in data
        assert isinstance(data["projections"], list)
        
        if len(data["projections"]) > 0:
            projection = data["projections"][0]
            # Year projections use 'years', 'projected_value', 'total_profit', 'growth_percent'
            assert "years" in projection
            assert "projected_value" in projection
            assert "total_profit" in projection


class TestCleanup:
    """Cleanup any test data created during testing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_response.status_code == 200:
            self.admin_token = login_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_cleanup_test_members(self):
        """Cleanup any TEST_ prefixed family members"""
        # Get all family members
        response = requests.get(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=self.headers
        )
        if response.status_code != 200:
            pytest.skip("Could not get family members for cleanup")
        
        members = response.json().get("family_members", [])
        test_members = [m for m in members if m["name"].startswith("TEST_")]
        
        for member in test_members:
            delete_response = requests.delete(
                f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{member['id']}",
                headers=self.headers
            )
            print(f"Cleaned up test member {member['name']}: {delete_response.status_code}")
        
        print(f"Cleanup complete: {len(test_members)} test members removed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

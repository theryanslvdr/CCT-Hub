"""
Iteration 119 Tests: Forgot Password Flow and Family Accounts Features
Tests both backend APIs and verifies integration for:
1. Forgot Password flow (email -> token -> reset)
2. Forgot Password edge case (non-existent email)
3. Family Accounts Page as licensee (Rizza Miles)
4. Add Family Member as licensee
5. Admin simulation flow for Family Accounts
6. Admin Add Family Member in simulation
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://licensee-profit-fix.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"


class TestForgotPasswordFlow:
    """Test the complete Forgot Password flow"""
    
    def test_forgot_password_valid_email(self):
        """Test forgot password with valid existing email returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": LICENSEE_EMAIL
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token field"
        assert data.get("token") is not None, "Token should not be None for existing user"
        assert "expires_in_minutes" in data, "Response should contain expiry info"
        print(f"✅ Forgot password for existing user: Token generated successfully")
        
    def test_forgot_password_invalid_email(self):
        """Test forgot password with non-existent email - should NOT return token"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent-user-xyz123@example.com"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("token") is None, "Token should be None for non-existing user"
        print(f"✅ Forgot password for non-existing user: No token returned (security best practice)")
        
    def test_reset_password_with_valid_token(self):
        """Test complete password reset flow with valid token"""
        # Step 1: Request reset token
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": LICENSEE_EMAIL
        })
        assert response.status_code == 200
        token = response.json().get("token")
        assert token is not None, "Should get a token for valid email"
        
        # Step 2: Reset password with token
        new_password = "rizza123"  # Using same password to not break other tests
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": token,
            "new_password": new_password
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✅ Password reset with valid token: Success")
        
        # Step 3: Verify can login with new password
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": new_password
        })
        assert response.status_code == 200, f"Login with new password failed: {response.text}"
        print(f"✅ Login with new password: Success")
        
    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token returns error"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "invalid-token-xyz",
            "new_password": "newpassword123"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✅ Password reset with invalid token: Correctly rejected")


class TestFamilyAccountsAsLicensee:
    """Test Family Accounts page as licensee (Rizza Miles)"""
    
    @pytest.fixture
    def licensee_token(self):
        """Get auth token for licensee"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        assert response.status_code == 200, f"Licensee login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_get_family_members_as_licensee(self, licensee_token):
        """Test that licensee can view their family members"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/family/members", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "family_members" in data, "Response should contain family_members"
        print(f"✅ Family members loaded: {len(data.get('family_members', []))} members found")
        
        # Check if Maria Miles exists (known family member)
        members = data.get("family_members", [])
        member_names = [m.get("name", "") for m in members]
        print(f"  Members: {member_names}")
        return members
        
    def test_add_family_member_as_licensee(self, licensee_token):
        """Test that licensee can add a new family member"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        
        # Add new family member
        today = datetime.now().strftime("%Y-%m-%d")
        new_member = {
            "name": "TEST_Iteration119_Member",
            "relationship": "sibling",
            "email": "test119@example.com",
            "starting_amount": 500.00,
            "deposit_date": today
        }
        
        response = requests.post(f"{BASE_URL}/api/family/members", headers=headers, json=new_member)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "member" in data, "Response should contain member"
        member_id = data.get("member", {}).get("id")
        assert member_id is not None, "New member should have an ID"
        print(f"✅ Family member added: {new_member['name']} (ID: {member_id})")
        
        # Cleanup - remove the test member
        response = requests.delete(f"{BASE_URL}/api/family/members/{member_id}", headers=headers)
        assert response.status_code == 200, f"Cleanup failed: {response.text}"
        print(f"✅ Test member cleaned up")


class TestAdminSimulationFamilyAccounts:
    """Test Admin simulation flow for Family Accounts"""
    
    @pytest.fixture
    def admin_token(self):
        """Get auth token for admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_admin_get_family_members_for_licensee(self, admin_token):
        """Test that admin can view family members for a specific licensee"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "family_members" in data, "Response should contain family_members"
        members = data.get("family_members", [])
        print(f"✅ Admin view family members for Rizza: {len(members)} members")
        for m in members:
            print(f"  - {m.get('name')}: ${m.get('account_value', 0):.2f}")
        return members
    
    def test_admin_add_family_member_simulation(self, admin_token):
        """Test that admin can add family member while simulating licensee view"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Add new family member via admin endpoint
        today = datetime.now().strftime("%Y-%m-%d")
        new_member = {
            "name": "TEST_AdminSim119_Member",
            "relationship": "child",
            "email": "testsim119@example.com",
            "starting_amount": 750.00,
            "deposit_date": today
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}", 
            headers=headers, 
            json=new_member
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "member" in data, "Response should contain member"
        member_id = data.get("member", {}).get("id")
        assert member_id is not None, "New member should have an ID"
        print(f"✅ Admin added family member via simulation: {new_member['name']} (ID: {member_id})")
        
        # Verify member appears in list
        response = requests.get(f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}", headers=headers)
        assert response.status_code == 200
        members = response.json().get("family_members", [])
        member_names = [m.get("name") for m in members]
        assert "TEST_AdminSim119_Member" in member_names, "New member should appear in list"
        print(f"✅ New member verified in family list")
        
        # Cleanup - remove the test member
        response = requests.delete(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{member_id}", 
            headers=headers
        )
        assert response.status_code == 200, f"Cleanup failed: {response.text}"
        print(f"✅ Test member cleaned up")
        
    def test_admin_update_family_member(self, admin_token):
        """Test that admin can update family member info while simulating"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First, get existing family members
        response = requests.get(f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}", headers=headers)
        assert response.status_code == 200
        members = response.json().get("family_members", [])
        
        if len(members) == 0:
            print("⚠️ No existing family members to test update - skipping")
            pytest.skip("No family members to update")
            
        # Create a test member to update
        today = datetime.now().strftime("%Y-%m-%d")
        new_member = {
            "name": "TEST_UpdateMe119",
            "relationship": "parent",
            "email": "updateme119@example.com",
            "starting_amount": 300.00,
            "deposit_date": today
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}", 
            headers=headers, 
            json=new_member
        )
        assert response.status_code == 200
        member_id = response.json().get("member", {}).get("id")
        
        # Update the member
        update_data = {
            "name": "TEST_UpdatedName119",
            "relationship": "other"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{member_id}",
            headers=headers,
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✅ Admin updated family member via simulation")
        
        # Verify update
        response = requests.get(f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}", headers=headers)
        members = response.json().get("family_members", [])
        updated = next((m for m in members if m.get("id") == member_id), None)
        assert updated is not None, "Updated member should exist"
        assert updated.get("name") == "TEST_UpdatedName119", "Name should be updated"
        print(f"✅ Update verified: {updated.get('name')}")
        
        # Cleanup
        response = requests.delete(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}/{member_id}", 
            headers=headers
        )
        assert response.status_code == 200
        print(f"✅ Test member cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

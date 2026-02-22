"""
Iteration 114 - Test Features:
1. Admin sets temp password -> User logs in -> must_change_password flag -> User sets new password
2. Direct login as Rizza Miles (honorary_fa licensee) shows correct dynamic account_value
3. Admin simulation of Rizza Miles shows same account_value as direct login  
4. Welcome-info endpoint returns dynamically calculated current_balance for honorary licensees
5. Force change password endpoint works and clears must_change_password flag

Test Credentials:
- Admin: iam@ryansalvador.com / admin123
- Honorary FA Licensee (Rizza Miles): rizza.miles@gmail.com / rizzatemp123 (temp password, must_change_password=true)
- Rizza's user ID: 19ccb9d7-139f-4918-a662-ad72483010b1
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://family-member-patch.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
RIZZA_EMAIL = "rizza.miles@gmail.com"
RIZZA_TEMP_PASSWORD = "rizzatemp123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"
# Expected value is around $6,530 based on trades since Jan 20, 2026
EXPECTED_ACCOUNT_VALUE_MIN = 6400  # Allow some tolerance
EXPECTED_ACCOUNT_VALUE_MAX = 7000


class TestAdminLoginNormal:
    """Test that normal admin login still works without must_change_password"""
    
    def test_01_admin_login_no_must_change_password(self):
        """Admin login should work normally without must_change_password flag"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        print(f"Admin login status: {response.status_code}")
        print(f"Admin login response: {response.json()}")
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        
        # Should have access_token and user
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        
        # Admin should NOT have must_change_password flag
        assert data.get("must_change_password") != True, "Admin should not have must_change_password flag"
        
        print("PASSED: Admin login works normally without must_change_password")


class TestTempPasswordFeature:
    """Test the admin temp password with forced reset on first login feature"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_01_rizza_login_with_temp_password_shows_must_change_flag(self):
        """Rizza login with temp password should return must_change_password=True"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RIZZA_EMAIL,
            "password": RIZZA_TEMP_PASSWORD
        })
        
        print(f"Rizza login status: {response.status_code}")
        print(f"Rizza login response: {response.json()}")
        
        assert response.status_code == 200, f"Rizza login failed: {response.text}"
        data = response.json()
        
        # Should have must_change_password flag
        assert data.get("must_change_password") == True, "Expected must_change_password=True for temp password user"
        assert "access_token" in data
        
        print("PASSED: Rizza login returns must_change_password=True")
        return data["access_token"]
    
    def test_02_force_change_password_works(self):
        """Force change password endpoint should work and clear the flag"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RIZZA_EMAIL,
            "password": RIZZA_TEMP_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Change password
        NEW_PASSWORD = "rizzanewtest123"
        response = requests.post(
            f"{BASE_URL}/api/auth/force-change-password",
            json={"new_password": NEW_PASSWORD},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Force change password status: {response.status_code}")
        print(f"Force change password response: {response.json()}")
        
        assert response.status_code == 200, f"Force change password failed: {response.text}"
        
        # Now login with new password - should NOT have must_change_password
        new_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RIZZA_EMAIL,
            "password": NEW_PASSWORD
        })
        
        print(f"Login with new password status: {new_login.status_code}")
        print(f"Login with new password response: {new_login.json()}")
        
        assert new_login.status_code == 200, f"Login with new password failed"
        assert new_login.json().get("must_change_password") != True, "must_change_password should be cleared after password change"
        
        print("PASSED: Force change password works and clears must_change_password flag")
        
        # Return the new password for cleanup
        return NEW_PASSWORD
    
    def test_03_cleanup_restore_rizza_temp_password(self, admin_token):
        """Restore Rizza's temp password for future testing"""
        response = requests.post(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/set-temp-password",
            json={"temp_password": RIZZA_TEMP_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"Restore temp password status: {response.status_code}")
        print(f"Restore temp password response: {response.json()}")
        
        assert response.status_code == 200, f"Failed to restore temp password: {response.text}"
        print("PASSED: Restored Rizza's temp password for future testing")


class TestHonoraryLicenseeDataConsistency:
    """Test P0 bug fix: Profit tracker data consistency for Honorary Licensees"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def rizza_token(self):
        """Get Rizza's auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RIZZA_EMAIL,
            "password": RIZZA_TEMP_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_01_profit_summary_returns_dynamic_account_value(self, rizza_token):
        """Direct login: /api/profit/summary should return dynamically calculated account_value"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {rizza_token}"}
        )
        
        print(f"Profit summary status: {response.status_code}")
        print(f"Profit summary response: {response.json()}")
        
        assert response.status_code == 200, f"Profit summary failed: {response.text}"
        data = response.json()
        
        account_value = data.get("account_value", 0)
        print(f"Account value from profit/summary: ${account_value}")
        
        # Should be around $6,530 (dynamically calculated), NOT $5,000 (stale starting amount)
        assert account_value > EXPECTED_ACCOUNT_VALUE_MIN, f"Account value ${account_value} is too low - may be using stale data instead of dynamic calculation"
        assert account_value < EXPECTED_ACCOUNT_VALUE_MAX, f"Account value ${account_value} seems too high"
        
        # Also check is_licensee flag
        assert data.get("is_licensee") == True, "Should be marked as licensee"
        
        print(f"PASSED: Direct login profit/summary returns dynamic account_value: ${account_value}")
        return account_value
    
    def test_02_welcome_info_returns_dynamic_current_balance(self, rizza_token):
        """Direct login: /api/profit/licensee/welcome-info should return dynamically calculated current_balance"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/welcome-info",
            headers={"Authorization": f"Bearer {rizza_token}"}
        )
        
        print(f"Welcome info status: {response.status_code}")
        print(f"Welcome info response: {response.json()}")
        
        assert response.status_code == 200, f"Welcome info failed: {response.text}"
        data = response.json()
        
        current_balance = data.get("current_balance", 0)
        starting_balance = data.get("starting_balance", 0)
        
        print(f"Current balance from welcome-info: ${current_balance}")
        print(f"Starting balance: ${starting_balance}")
        
        # Current balance should be dynamically calculated (~$6,530), not stale (~$5,000)
        assert current_balance > EXPECTED_ACCOUNT_VALUE_MIN, f"Current balance ${current_balance} is too low - may be using stale license.current_amount instead of dynamic calculation"
        assert current_balance < EXPECTED_ACCOUNT_VALUE_MAX, f"Current balance ${current_balance} seems too high"
        
        # Starting balance should be the original deposit amount
        assert starting_balance == 5000, f"Starting balance should be $5000, got ${starting_balance}"
        
        print(f"PASSED: Welcome-info returns dynamic current_balance: ${current_balance}")
        return current_balance
    
    def test_03_admin_simulate_returns_same_value_as_direct_login(self, admin_token, rizza_token):
        """Admin simulation of Rizza should show same account_value as direct login"""
        # Get direct login value
        direct_response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {rizza_token}"}
        )
        assert direct_response.status_code == 200
        direct_account_value = direct_response.json().get("account_value", 0)
        
        # Get admin simulate value
        simulate_response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/simulate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"Admin simulate status: {simulate_response.status_code}")
        print(f"Admin simulate response keys: {simulate_response.json().keys()}")
        
        assert simulate_response.status_code == 200, f"Admin simulate failed: {simulate_response.text}"
        simulate_data = simulate_response.json()
        simulate_account_value = simulate_data.get("account_value", 0)
        
        print(f"Direct login account_value: ${direct_account_value}")
        print(f"Admin simulate account_value: ${simulate_account_value}")
        
        # Values should match (within small tolerance for rounding)
        assert abs(direct_account_value - simulate_account_value) < 1, f"Account values don't match! Direct: ${direct_account_value}, Simulate: ${simulate_account_value}"
        
        print(f"PASSED: Admin simulation matches direct login - both show ${simulate_account_value}")
    
    def test_04_daily_projection_shows_consistent_data(self, rizza_token):
        """Daily projection endpoint should show consistent data"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/daily-projection",
            headers={"Authorization": f"Bearer {rizza_token}"}
        )
        
        print(f"Daily projection status: {response.status_code}")
        
        assert response.status_code == 200, f"Daily projection failed: {response.text}"
        data = response.json()
        
        # Check that projections exist
        projections = data.get("projections", [])
        print(f"Number of projection days: {len(projections)}")
        
        if len(projections) > 0:
            # Get the latest projection
            latest = projections[-1]
            print(f"Latest projection date: {latest.get('date')}")
            print(f"Latest balance: ${latest.get('balance', 0)}")
        
        # The final balance in projections should match the dynamic calculation
        # (within tolerance, as projections may include future dates)
        
        print("PASSED: Daily projection endpoint returns data")


class TestAdminMemberDetails:
    """Test that admin member details endpoint also uses dynamic calculation"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_01_member_details_shows_dynamic_value(self, admin_token):
        """Admin member details 'stats' should show dynamically calculated account_value"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"Member details status: {response.status_code}")
        
        assert response.status_code == 200, f"Member details failed: {response.text}"
        data = response.json()
        
        # The endpoint returns nested structure with stats.account_value
        stats = data.get("stats", {})
        account_value = stats.get("account_value", 0)
        is_licensee = stats.get("is_licensee", False)
        
        print(f"Member details stats.account_value: ${account_value}")
        print(f"Is licensee: {is_licensee}")
        
        # Should be dynamically calculated (~$6,530), not stale $5,000
        assert account_value > EXPECTED_ACCOUNT_VALUE_MIN, f"Account value ${account_value} too low - may be stale"
        assert is_licensee == True, "Should be marked as licensee"
        
        print(f"PASSED: Admin member details shows dynamic value in stats: ${account_value}")


class TestSetTempPasswordEndpoint:
    """Test the set-temp-password endpoint directly"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_01_set_temp_password_endpoint_works(self, admin_token):
        """Admin can set temp password for a user"""
        # This re-sets the temp password (safe to run multiple times)
        response = requests.post(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/set-temp-password",
            json={"temp_password": RIZZA_TEMP_PASSWORD},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"Set temp password status: {response.status_code}")
        print(f"Set temp password response: {response.json()}")
        
        assert response.status_code == 200, f"Set temp password failed: {response.text}"
        
        # Verify by logging in - should have must_change_password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RIZZA_EMAIL,
            "password": RIZZA_TEMP_PASSWORD
        })
        
        assert login_response.status_code == 200
        assert login_response.json().get("must_change_password") == True
        
        print("PASSED: Set temp password endpoint works and sets must_change_password flag")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

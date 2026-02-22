"""
Test Iteration 116: 7 Critical Bug Fixes Verification
=====================================================
Testing the following issues:
1. Issue 1, 3, 4 (P0): Stale Data - Rizza's dashboard shows dynamic account_value=$6530
2. Issue 2 (P0): Incorrect Profit - total_actual_profit > $0 for licensee
3. Issue 3 (P1): Incomplete Projection History - starts from effective_start_date (2026-01-20)
4. Issue 5 (P1): Dashboard stuck loading - Year projections endpoint works
5. Issue 4 (P1): Forgot Password - Full flow test
6. Issue 6 (P2): License Conversion Data Preservation - honorary<->honorary_fa in-place
7. Issue 7 (P2): Admin Add Family Member - functionality exists
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"
RIZZA_LICENSE_ID = "3365cca7-9ed8-40d4-9d73-0b9c43f34e8e"

class TestAuthentication:
    """Test that we can authenticate with provided credentials"""
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        print(f"Admin login response: {response.status_code}")
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in admin login response"
        assert data.get("user", {}).get("role") == "master_admin", "Admin should be master_admin"
        
    def test_licensee_login(self):
        """Test licensee (Rizza) can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        print(f"Licensee login response: {response.status_code}")
        assert response.status_code == 200, f"Licensee login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in licensee login response"


class TestIssue1_3_4_StaleData:
    """Issue 1, 3, 4 (P0): Verify dynamic account values instead of stale data"""
    
    @pytest.fixture
    def licensee_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        return response.json().get("token")
    
    def test_profit_summary_has_dynamic_values(self, licensee_token):
        """Verify /api/profit/summary returns dynamic account_value around $6530"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        print(f"Profit summary response: {response.status_code}")
        assert response.status_code == 200, f"Profit summary failed: {response.text}"
        
        data = response.json()
        print(f"Profit summary data: {data}")
        
        # Verify dynamic values (not stale $798.57 or static $5000)
        account_value = data.get("account_value", 0)
        total_profit = data.get("total_profit", 0)
        total_trades = data.get("total_trades", 0)
        is_licensee = data.get("is_licensee", False)
        
        print(f"Account Value: ${account_value}")
        print(f"Total Profit: ${total_profit}")
        print(f"Total Trades: {total_trades}")
        print(f"Is Licensee: {is_licensee}")
        
        # Key assertions for bug verification
        assert is_licensee == True, "Rizza should be marked as licensee"
        assert account_value > 5000, f"Account value should be > $5000 (got ${account_value})"
        assert account_value != 798.57, f"Account value should NOT be stale $798.57"
        assert total_profit > 0, f"Total profit should be > $0 for licensee (got ${total_profit})"
        assert total_trades > 0, f"Total trades should be > 0 (got {total_trades})"
        
        # Expected values approximately
        assert 6000 <= account_value <= 8000, f"Account value should be around $6530 (got ${account_value})"
        assert 1000 <= total_profit <= 3000, f"Total profit should be around $1530 (got ${total_profit})"
        

class TestIssue2_IncorrectProfit:
    """Issue 2 (P0): Verify total_actual_profit > $0"""
    
    @pytest.fixture
    def licensee_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        return response.json().get("token")
    
    def test_profit_summary_actual_profit_not_zero(self, licensee_token):
        """Verify total_actual_profit field is > $0 for licensee"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        total_actual_profit = data.get("total_actual_profit", 0)
        print(f"Total Actual Profit: ${total_actual_profit}")
        
        assert total_actual_profit > 0, f"total_actual_profit should be > $0 (got ${total_actual_profit})"
        assert total_actual_profit >= 1000, f"Expected around $1530, got ${total_actual_profit}"


class TestIssue3_ProjectionHistory:
    """Issue 3 (P1): Verify projection history starts from effective_start_date"""
    
    @pytest.fixture
    def licensee_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        return response.json().get("token")
    
    def test_daily_projection_starts_from_effective_date(self, licensee_token):
        """Verify /api/profit/licensee/daily-projection starts from 2026-01-20"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        print(f"Daily projection response: {response.status_code}")
        assert response.status_code == 200, f"Daily projection failed: {response.text}"
        
        data = response.json()
        projections = data.get("projections", [])
        effective_start_date = data.get("effective_start_date")
        
        print(f"Effective Start Date: {effective_start_date}")
        print(f"Number of projections: {len(projections)}")
        
        assert len(projections) > 0, "Should have projection data"
        
        # Check the first projection date
        first_projection = projections[0]
        first_date = first_projection.get("date")
        print(f"First projection date: {first_date}")
        
        # Should start from January, not just February
        assert first_date.startswith("2026-01"), f"Projections should start in January 2026, got {first_date}"
        # Should be around 2026-01-20 (effective_start_date)
        assert "2026-01-2" in first_date, f"First date should be around 2026-01-20, got {first_date}"


class TestIssue4_ForgotPassword:
    """Issue 4 (P1): Forgot Password Flow"""
    
    def test_forgot_password_endpoint_exists(self):
        """Test POST /api/auth/forgot-password returns a token"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": LICENSEE_EMAIL
        })
        
        print(f"Forgot password response: {response.status_code}")
        assert response.status_code == 200, f"Forgot password failed: {response.text}"
        
        data = response.json()
        print(f"Forgot password data: {data}")
        
        # Should return a reset token
        assert "token" in data, "Should return a token"
        assert "message" in data, "Should return a message"
        
        # Token should be a valid UUID
        token = data.get("token")
        if token:
            assert len(token) == 36, f"Token should be UUID format, got: {token}"
    
    def test_reset_password_with_token(self):
        """Test full forgot password -> reset password flow"""
        # Step 1: Request password reset
        forgot_response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": LICENSEE_EMAIL
        })
        assert forgot_response.status_code == 200
        
        token = forgot_response.json().get("token")
        if not token:
            pytest.skip("No token returned - email may not exist")
        
        # Step 2: Reset password with the token
        reset_response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": token,
            "new_password": "rizza123"  # Reset back to original password
        })
        
        print(f"Reset password response: {reset_response.status_code}")
        assert reset_response.status_code == 200, f"Reset password failed: {reset_response.text}"
        
        # Step 3: Verify login works with new password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": "rizza123"
        })
        
        print(f"Login after reset response: {login_response.status_code}")
        assert login_response.status_code == 200, "Login should work after password reset"
    
    def test_invalid_reset_token(self):
        """Test reset with invalid token returns 400"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "token": "invalid-fake-token-123",
            "new_password": "newpassword123"
        })
        
        print(f"Invalid token response: {response.status_code}")
        assert response.status_code == 400, "Invalid token should return 400"


class TestIssue5_YearProjections:
    """Issue 5 (P1): Dashboard stuck loading - Year projections endpoint works"""
    
    @pytest.fixture
    def licensee_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        return response.json().get("token")
    
    def test_year_projections_endpoint(self, licensee_token):
        """Verify /api/profit/licensee/year-projections returns data"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        print(f"Year projections response: {response.status_code}")
        assert response.status_code == 200, f"Year projections failed: {response.text}"
        
        data = response.json()
        print(f"Year projections data keys: {data.keys()}")
        
        # Should have projection data for 1yr, 2yr, 3yr, 5yr
        projections = data.get("projections", {})
        print(f"Projections: {projections}")
        
        # Verify we have year projection values
        assert "1_year" in projections or "year_1" in projections or len(projections) > 0, "Should have year projections"


class TestIssue6_LicenseConversion:
    """Issue 6 (P2): License Conversion Data Preservation"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json().get("token")
    
    def test_honorary_fa_to_honorary_conversion_preserves_data(self, admin_token):
        """Test that honorary_fa -> honorary conversion preserves all data in-place"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 1: Get current license state
        get_response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert get_response.status_code == 200
        
        licenses = get_response.json()
        rizza_license = None
        for lic in licenses:
            if lic.get("id") == RIZZA_LICENSE_ID:
                rizza_license = lic
                break
        
        if not rizza_license:
            pytest.skip(f"Rizza's license not found with ID {RIZZA_LICENSE_ID}")
        
        original_type = rizza_license.get("license_type")
        original_starting = rizza_license.get("starting_amount")
        original_current = rizza_license.get("current_amount")
        original_effective = rizza_license.get("effective_start_date")
        
        print(f"Original License State:")
        print(f"  Type: {original_type}")
        print(f"  Starting Amount: {original_starting}")
        print(f"  Current Amount: {original_current}")
        print(f"  Effective Start Date: {original_effective}")
        
        # Step 2: Convert to honorary (if currently honorary_fa)
        new_type = "honorary" if original_type == "honorary_fa" else "honorary_fa"
        
        convert_response = requests.post(
            f"{BASE_URL}/api/admin/licenses/{RIZZA_LICENSE_ID}/change-type",
            headers=headers,
            json={"new_license_type": new_type}
        )
        
        print(f"Convert response: {convert_response.status_code}")
        assert convert_response.status_code == 200, f"Conversion failed: {convert_response.text}"
        
        convert_data = convert_response.json()
        print(f"Convert data: {convert_data}")
        
        # Key assertion: license_id should be SAME (not a new one)
        returned_license_id = convert_data.get("new_license_id")
        assert returned_license_id == RIZZA_LICENSE_ID, f"License ID should be preserved! Got {returned_license_id}, expected {RIZZA_LICENSE_ID}"
        
        # Step 3: Verify data was preserved by getting the license again
        get_response2 = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        licenses2 = get_response2.json()
        
        updated_license = None
        for lic in licenses2:
            if lic.get("id") == RIZZA_LICENSE_ID:
                updated_license = lic
                break
        
        assert updated_license is not None, "License should still exist with same ID"
        assert updated_license.get("license_type") == new_type, "Type should be changed"
        assert updated_license.get("starting_amount") == original_starting, "Starting amount should be preserved"
        assert updated_license.get("effective_start_date") == original_effective, "Effective start date should be preserved"
        
        print(f"After conversion:")
        print(f"  Type: {updated_license.get('license_type')}")
        print(f"  Starting Amount: {updated_license.get('starting_amount')}")
        print(f"  Current Amount: {updated_license.get('current_amount')}")
        print(f"  Effective Start Date: {updated_license.get('effective_start_date')}")
        
        # Step 4: REVERT back to original type
        revert_response = requests.post(
            f"{BASE_URL}/api/admin/licenses/{RIZZA_LICENSE_ID}/change-type",
            headers=headers,
            json={"new_license_type": original_type}
        )
        
        print(f"Revert response: {revert_response.status_code}")
        assert revert_response.status_code == 200, f"Revert failed: {revert_response.text}"
        
        # Verify revert worked
        get_response3 = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        licenses3 = get_response3.json()
        
        final_license = None
        for lic in licenses3:
            if lic.get("id") == RIZZA_LICENSE_ID:
                final_license = lic
                break
        
        assert final_license is not None
        assert final_license.get("license_type") == original_type, "License type should be reverted"
        print(f"Reverted back to {final_license.get('license_type')}")


class TestIssue7_AdminFamilyMember:
    """Issue 7 (P2): Admin Add Family Member functionality"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json().get("token")
    
    def test_admin_can_add_family_member_endpoint_exists(self, admin_token):
        """Test POST /api/admin/family/members/{userId} endpoint exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with a dummy request to verify endpoint exists
        # Using a minimal payload - endpoint should return 400 for invalid data, not 404
        response = requests.post(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=headers,
            json={
                "member_email": "test.family@example.com",
                "member_name": "Test Family Member",
                "relationship": "spouse"
            }
        )
        
        print(f"Admin add family member response: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Endpoint should exist (not 404) - could be 200, 400, or 409 depending on state
        assert response.status_code != 404, f"Family member endpoint should exist, got 404"
        
        # If 422/400, that's fine - means endpoint exists but data validation failed
        # If 200, great - it worked
        # If 409, member may already exist


class TestTotalTradesCount:
    """Verify total_trades counts master admin trade days for licensees"""
    
    @pytest.fixture
    def licensee_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        return response.json().get("token")
    
    def test_total_trades_is_master_admin_trade_days(self, licensee_token):
        """Verify total_trades reflects master admin trading days"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        total_trades = data.get("total_trades", 0)
        print(f"Total trades for licensee: {total_trades}")
        
        # Should have some trades (expected ~20 based on context)
        assert total_trades > 0, f"Total trades should be > 0 for licensee"
        assert total_trades >= 10, f"Expected around 20 trades, got {total_trades}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

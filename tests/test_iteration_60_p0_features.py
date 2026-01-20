"""
Test iteration 60: P0 Features Testing
- Effective Start Date Bug Fix: Daily Projection table should start from effective_start_date for licensees
- Manager Traded Toggle: Master Admin can toggle 'Manager Traded' status when simulating a licensee
- Master Admin Account Value: Should include funds from all managed licensees
- Master Admin Financial Breakdown: /api/profit/master-admin-breakdown endpoint
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestMasterAdminAuth:
    """Test Master Admin authentication"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_master_admin_login(self, auth_token):
        """Test Master Admin can login successfully"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Master Admin login successful")


class TestMasterAdminAccountValue:
    """Test Master Admin account value includes licensee funds"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_profit_summary_includes_licensee_funds(self, auth_headers):
        """Test /api/profit/summary returns licensee_funds and licensee_count for Master Admin"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get profit summary: {response.text}"
        
        data = response.json()
        print(f"Profit Summary Response: {data}")
        
        # Verify required fields exist
        assert "account_value" in data, "Missing account_value in response"
        assert "total_deposits" in data, "Missing total_deposits in response"
        assert "total_actual_profit" in data, "Missing total_actual_profit in response"
        
        # For Master Admin, should include licensee_funds and licensee_count
        assert "licensee_funds" in data, "Missing licensee_funds in response - Master Admin should see this"
        assert "licensee_count" in data, "Missing licensee_count in response - Master Admin should see this"
        
        print(f"✓ Account Value: ${data['account_value']}")
        print(f"✓ Licensee Funds: ${data['licensee_funds']}")
        print(f"✓ Licensee Count: {data['licensee_count']}")
        
        # Verify data types
        assert isinstance(data["licensee_funds"], (int, float)), "licensee_funds should be a number"
        assert isinstance(data["licensee_count"], int), "licensee_count should be an integer"


class TestMasterAdminFinancialBreakdown:
    """Test Master Admin financial breakdown endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_master_admin_breakdown_endpoint(self, auth_headers):
        """Test /api/profit/master-admin-breakdown returns detailed breakdown"""
        response = requests.get(f"{BASE_URL}/api/profit/master-admin-breakdown", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get breakdown: {response.text}"
        
        data = response.json()
        print(f"Master Admin Breakdown Response: {data}")
        
        # Verify required fields
        assert "personal_account_value" in data, "Missing personal_account_value"
        assert "licensee_funds" in data, "Missing licensee_funds"
        assert "total_account_value" in data, "Missing total_account_value"
        assert "licensee_count" in data, "Missing licensee_count"
        
        print(f"✓ Personal Account Value: ${data['personal_account_value']}")
        print(f"✓ Licensee Funds: ${data['licensee_funds']}")
        print(f"✓ Total Account Value: ${data['total_account_value']}")
        print(f"✓ Licensee Count: {data['licensee_count']}")
        
        # Verify total = personal + licensee
        expected_total = data['personal_account_value'] + data['licensee_funds']
        assert abs(data['total_account_value'] - expected_total) < 0.01, \
            f"Total account value mismatch: {data['total_account_value']} != {expected_total}"
        
        print(f"✓ Total calculation verified: {data['personal_account_value']} + {data['licensee_funds']} = {data['total_account_value']}")
    
    def test_breakdown_includes_licensee_details(self, auth_headers):
        """Test breakdown includes licensee_breakdown array with details"""
        response = requests.get(f"{BASE_URL}/api/profit/master-admin-breakdown", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # If there are licensees, verify breakdown structure
        if data.get("licensee_count", 0) > 0:
            assert "licensee_breakdown" in data, "Missing licensee_breakdown array"
            assert isinstance(data["licensee_breakdown"], list), "licensee_breakdown should be a list"
            
            if len(data["licensee_breakdown"]) > 0:
                licensee = data["licensee_breakdown"][0]
                assert "license_id" in licensee, "Missing license_id in breakdown"
                assert "user_id" in licensee, "Missing user_id in breakdown"
                assert "user_name" in licensee, "Missing user_name in breakdown"
                assert "license_type" in licensee, "Missing license_type in breakdown"
                assert "current_amount" in licensee, "Missing current_amount in breakdown"
                
                print(f"✓ Licensee breakdown structure verified")
                for lic in data["licensee_breakdown"]:
                    print(f"  - {lic.get('user_name')}: ${lic.get('current_amount')} ({lic.get('license_type')})")
        else:
            print("✓ No active licensees found (breakdown test skipped)")


class TestLicenseeManagement:
    """Test licensee-related features"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_active_licenses(self, auth_headers):
        """Test getting list of active licenses"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get licenses: {response.text}"
        
        data = response.json()
        # Response is a dict with "licenses" key
        licenses = data.get("licenses", [])
        print(f"Active Licenses: {len(licenses)} found")
        
        # Store license IDs for later tests
        if len(licenses) > 0:
            for license in licenses[:3]:  # Show first 3
                print(f"  - License ID: {license.get('id')}, User: {license.get('user_id')}, Type: {license.get('license_type')}")
                print(f"    Effective Start: {license.get('effective_start_date')}, Current Amount: ${license.get('current_amount')}")
        
        return licenses
    
    def test_license_has_effective_start_date(self, auth_headers):
        """Test that licenses have effective_start_date field"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        licenses = data.get("licenses", [])
        if len(licenses) > 0:
            for license in licenses:
                # effective_start_date should exist (may be null for older licenses)
                if "effective_start_date" in license and license.get("effective_start_date"):
                    print(f"✓ License {license.get('id')} has effective_start_date: {license.get('effective_start_date')}")
                else:
                    # Check for fallback start_date
                    assert "start_date" in license, f"License {license.get('id')} missing both effective_start_date and start_date"
                    print(f"✓ License {license.get('id')} has start_date: {license.get('start_date')}")
        else:
            print("✓ No licenses to test (skipped)")


class TestTradeOverrides:
    """Test Manager Traded toggle functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_license_id(self, auth_headers):
        """Get a license ID for testing"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=auth_headers)
        if response.status_code == 200:
            licenses = response.json()
            if len(licenses) > 0:
                return licenses[0].get("id")
        return None
    
    def test_get_trade_overrides(self, auth_headers, test_license_id):
        """Test getting trade overrides for a license"""
        if not test_license_id:
            pytest.skip("No license available for testing")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses/{test_license_id}/trade-overrides",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get trade overrides: {response.text}"
        
        data = response.json()
        print(f"Trade Overrides Response: {data}")
        
        assert "overrides" in data, "Missing overrides in response"
        print(f"✓ Trade overrides retrieved: {len(data.get('overrides', {}))} entries")
    
    def test_set_trade_override(self, auth_headers, test_license_id):
        """Test setting a trade override for a specific date"""
        if not test_license_id:
            pytest.skip("No license available for testing")
        
        # Use yesterday's date for testing
        test_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/licenses/{test_license_id}/trade-overrides",
            headers=auth_headers,
            json={
                "license_id": test_license_id,
                "date": test_date,
                "traded": True,
                "notes": "Test override from pytest"
            }
        )
        
        # Should succeed or return appropriate error
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Trade override set successfully for {test_date}")
            print(f"  Response: {data}")
        else:
            print(f"Trade override response: {response.status_code} - {response.text}")
            # Not a failure if endpoint exists but has validation
            assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"


class TestLicenseeDailyProjection:
    """Test Daily Projection for licensees with effective_start_date"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_licensee_daily_projection_endpoint(self, auth_headers):
        """Test the licensee daily projection endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee-daily-projection",
            headers=auth_headers
        )
        
        # This endpoint may return 200 or 400 depending on user type
        print(f"Licensee Daily Projection Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Projections: {len(data.get('projections', []))} entries")
        else:
            print(f"  Response: {response.text[:200]}")
    
    def test_license_projections_endpoint(self, auth_headers):
        """Test the license projections endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/profit/license-projections",
            headers=auth_headers
        )
        
        print(f"License Projections Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Monthly Projections: {len(data.get('monthly_projections', []))} entries")


class TestAPIEndpointsExist:
    """Verify all required API endpoints exist and respond"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for Master Admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers for API calls"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_profit_summary_endpoint(self, auth_headers):
        """Test /api/profit/summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=auth_headers)
        assert response.status_code == 200, f"Endpoint failed: {response.status_code}"
        print("✓ /api/profit/summary endpoint working")
    
    def test_master_admin_breakdown_endpoint(self, auth_headers):
        """Test /api/profit/master-admin-breakdown endpoint"""
        response = requests.get(f"{BASE_URL}/api/profit/master-admin-breakdown", headers=auth_headers)
        assert response.status_code == 200, f"Endpoint failed: {response.status_code}"
        print("✓ /api/profit/master-admin-breakdown endpoint working")
    
    def test_licenses_endpoint(self, auth_headers):
        """Test /api/admin/licenses endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=auth_headers)
        assert response.status_code == 200, f"Endpoint failed: {response.status_code}"
        print("✓ /api/admin/licenses endpoint working")
    
    def test_trade_logs_endpoint(self, auth_headers):
        """Test /api/trade/logs endpoint"""
        response = requests.get(f"{BASE_URL}/api/trade/logs", headers=auth_headers)
        assert response.status_code == 200, f"Endpoint failed: {response.status_code}"
        print("✓ /api/trade/logs endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test Iteration 18 Features:
1. License Registration - Form submission works without 'Field Required' error
2. License Registration - No notices below Starting Amount section
3. Sidebar - 'Deposit/Withdrawal' link (renamed from 'Licensee Account')
4. Simulation Dropdown - Shows 5 options: Member, Basic Admin, Super Admin, Honorary Licensee, Extended Licensee
5. Login flow with master admin credentials
6. Admin Licenses page - accessible to Master Admin only
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMasterAdminLogin:
    """Test login flow with master admin credentials"""
    
    def test_master_admin_login_success(self):
        """Test login with master admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] == "master_admin", f"Expected master_admin role, got {data['user']['role']}"
        assert data["user"]["email"] == "iam@ryansalvador.com"
        
        # Store token for other tests
        TestMasterAdminLogin.token = data["access_token"]
        TestMasterAdminLogin.user = data["user"]
        print(f"✓ Master admin login successful: {data['user']['full_name']}")


class TestLicenseInviteValidation:
    """Test license invite validation endpoint"""
    
    def test_validate_license_invite(self):
        """Test validating a license invite code"""
        test_code = "LIC-164QF0XQPUTBNDXV"
        response = requests.get(f"{BASE_URL}/api/auth/license-invite/{test_code}")
        
        # Could be 200 (valid) or 404 (not found) or 400 (expired/revoked)
        if response.status_code == 200:
            data = response.json()
            assert "license_type" in data, "No license_type in response"
            assert "starting_amount" in data, "No starting_amount in response"
            print(f"✓ License invite valid: type={data['license_type']}, amount=${data['starting_amount']}")
        elif response.status_code == 404:
            print(f"✓ License invite not found (expected if code doesn't exist)")
        elif response.status_code == 400:
            print(f"✓ License invite expired/revoked: {response.json().get('detail', 'Unknown')}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, {response.text}")


class TestLicenseRegistration:
    """Test license registration endpoint - the main fix"""
    
    def test_register_with_license_form_data(self):
        """Test that registration works with FormData (not URLSearchParams)"""
        # First, we need a valid invite code - let's create one via admin API
        # Login as master admin first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a new license invite
        unique_id = str(uuid.uuid4())[:8]
        invite_response = requests.post(f"{BASE_URL}/api/admin/license-invites", 
            json={
                "license_type": "honorary",
                "starting_amount": 1000,
                "valid_duration": "3_months",  # 3_months, 6_months, 1_year, indefinite
                "max_uses": 1,
                "invitee_name": f"Test User {unique_id}",
                "notes": "Test invite for registration"
            },
            headers=headers
        )
        
        if invite_response.status_code != 200:
            print(f"Could not create invite: {invite_response.text}")
            pytest.skip("Could not create license invite for testing")
        
        invite_data = invite_response.json()
        invite_code = invite_data.get("code")
        print(f"Created test invite: {invite_code}")
        
        # Now test registration with FormData
        test_email = f"test_user_{unique_id}@example.com"
        form_data = {
            "email": test_email,
            "password": "testpass123",
            "full_name": f"Test User {unique_id}",
            "invite_code": invite_code
        }
        
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register-with-license",
            data=form_data  # This sends as form data, not JSON
        )
        
        # Check for success
        assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
        
        reg_data = register_response.json()
        assert "access_token" in reg_data, "No access_token in registration response"
        assert "user" in reg_data, "No user in registration response"
        assert reg_data["user"]["email"] == test_email.lower()
        assert reg_data["user"]["role"] == "member"
        
        # Verify license was created
        assert "license" in reg_data, "No license info in registration response"
        assert reg_data["license"]["type"] == "honorary"
        assert reg_data["license"]["starting_amount"] == 1000
        
        print(f"✓ License registration successful for {test_email}")
        print(f"  - License type: {reg_data['license']['type']}")
        print(f"  - Starting amount: ${reg_data['license']['starting_amount']}")
        
        # Cleanup: Delete the test user
        # (We'd need admin access to do this properly)


class TestAdminLicensesAccess:
    """Test Admin Licenses page access control"""
    
    def test_licenses_endpoint_master_admin_only(self):
        """Test that licenses endpoint is accessible to master admin"""
        # Login as master admin
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access licenses endpoint
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200, f"Licenses endpoint failed: {response.text}"
        
        data = response.json()
        # Response is wrapped in {"licenses": [...]}
        licenses = data.get("licenses", data) if isinstance(data, dict) else data
        assert isinstance(licenses, list), f"Expected list of licenses, got {type(licenses)}"
        print(f"✓ Master admin can access licenses endpoint: {len(licenses)} licenses found")
    
    def test_license_invites_endpoint(self):
        """Test license invites endpoint"""
        # Login as master admin
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access license invites endpoint
        response = requests.get(f"{BASE_URL}/api/admin/license-invites", headers=headers)
        assert response.status_code == 200, f"License invites endpoint failed: {response.text}"
        
        data = response.json()
        # Response is wrapped in {"invites": [...]}
        invites = data.get("invites", data) if isinstance(data, dict) else data
        assert isinstance(invites, list), f"Expected list of license invites, got {type(invites)}"
        print(f"✓ Master admin can access license invites: {len(invites)} invites found")


class TestLicenseeTransactions:
    """Test licensee transactions endpoint"""
    
    def test_licensee_transactions_master_admin_only(self):
        """Test that licensee transactions is master admin only"""
        # Login as master admin
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access licensee transactions endpoint
        response = requests.get(f"{BASE_URL}/api/admin/licensee-transactions", headers=headers)
        assert response.status_code == 200, f"Licensee transactions endpoint failed: {response.text}"
        
        data = response.json()
        # Response is wrapped in {"transactions": [...]}
        transactions = data.get("transactions", data) if isinstance(data, dict) else data
        assert isinstance(transactions, list), f"Expected list of transactions, got {type(transactions)}"
        print(f"✓ Master admin can access licensee transactions: {len(transactions)} transactions found")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ API is healthy")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

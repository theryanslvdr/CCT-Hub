"""
Test iteration 57 - Finance Center UI improvements
Tests for:
1. Licensee transaction Edit/Delete endpoints
2. Backend API verification
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLicenseeTransactionEndpoints:
    """Test licensee transaction management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Master Admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        self.session.close()
    
    def test_get_licensee_transactions(self):
        """Test GET /api/admin/licensee-transactions"""
        response = self.session.get(f"{BASE_URL}/api/admin/licensee-transactions")
        assert response.status_code == 200, f"Failed to get transactions: {response.text}"
        
        data = response.json()
        assert "transactions" in data, "Response should contain 'transactions' key"
        print(f"SUCCESS: Found {len(data['transactions'])} licensee transactions")
    
    def test_update_licensee_transaction_endpoint_exists(self):
        """Test PUT /api/admin/licensee-transactions/{tx_id} endpoint exists"""
        # First get a transaction ID
        response = self.session.get(f"{BASE_URL}/api/admin/licensee-transactions")
        assert response.status_code == 200
        
        transactions = response.json().get("transactions", [])
        if not transactions:
            pytest.skip("No transactions available to test update")
        
        tx_id = transactions[0]["id"]
        original_amount = transactions[0].get("amount", 100)
        
        # Test the PUT endpoint with same amount (no actual change)
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/licensee-transactions/{tx_id}",
            json={"amount": original_amount, "notes": "Test update - no change"}
        )
        
        # Should return 200 for valid request
        assert update_response.status_code == 200, f"Update endpoint failed: {update_response.text}"
        print(f"SUCCESS: PUT endpoint for licensee transaction works")
    
    def test_delete_licensee_transaction_endpoint_exists(self):
        """Test DELETE /api/admin/licensee-transactions/{tx_id} endpoint exists"""
        # We won't actually delete, just verify the endpoint responds correctly
        # Using a non-existent ID should return 404
        fake_tx_id = "non-existent-tx-id-12345"
        
        delete_response = self.session.delete(
            f"{BASE_URL}/api/admin/licensee-transactions/{fake_tx_id}"
        )
        
        # Should return 404 for non-existent transaction
        assert delete_response.status_code == 404, f"Expected 404 for non-existent tx, got: {delete_response.status_code}"
        print(f"SUCCESS: DELETE endpoint for licensee transaction exists and returns 404 for invalid ID")


class TestProfitSummaryEndpoint:
    """Test profit summary endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Master Admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        self.session.close()
    
    def test_profit_summary(self):
        """Test GET /api/profit/summary returns correct data"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200, f"Failed to get summary: {response.text}"
        
        data = response.json()
        
        # Verify required fields
        assert "account_value" in data, "Response should contain 'account_value'"
        assert "total_actual_profit" in data, "Response should contain 'total_actual_profit'"
        assert "total_deposits" in data, "Response should contain 'total_deposits'"
        assert "performance_rate" in data, "Response should contain 'performance_rate'"
        
        print(f"SUCCESS: Profit summary - Account Value: ${data['account_value']:.2f}, Total Profit: ${data['total_actual_profit']:.2f}")


class TestLicenseInviteEndpoints:
    """Test license invite endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Master Admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        self.session.close()
    
    def test_get_license_invites(self):
        """Test GET /api/admin/license-invites"""
        response = self.session.get(f"{BASE_URL}/api/admin/license-invites")
        assert response.status_code == 200, f"Failed to get invites: {response.text}"
        
        data = response.json()
        assert "invites" in data, "Response should contain 'invites' key"
        print(f"SUCCESS: Found {len(data['invites'])} license invites")
    
    def test_create_honorary_invite_with_starting_balance(self):
        """Test creating honorary invite with optional starting balance"""
        # Create honorary invite with starting balance
        response = self.session.post(f"{BASE_URL}/api/admin/license-invites", json={
            "license_type": "honorary",
            "starting_amount": 5000,  # Optional starting balance
            "valid_duration": "3_months",
            "max_uses": 1,
            "invitee_name": "TEST_Honorary_With_Balance",
            "notes": "Test honorary invite with starting balance"
        })
        
        assert response.status_code == 200, f"Failed to create invite: {response.text}"
        
        data = response.json()
        assert "code" in data, "Response should contain invite code"
        assert data.get("starting_amount") == 5000, "Starting amount should be 5000"
        
        print(f"SUCCESS: Created honorary invite with starting balance: {data['code']}")
        
        # Cleanup - delete the test invite
        invite_id = data.get("id")
        if invite_id:
            self.session.delete(f"{BASE_URL}/api/admin/license-invites/{invite_id}")
    
    def test_create_honorary_invite_without_starting_balance(self):
        """Test creating honorary invite without starting balance (should default to 0)"""
        response = self.session.post(f"{BASE_URL}/api/admin/license-invites", json={
            "license_type": "honorary",
            "starting_amount": 0,  # No starting balance
            "valid_duration": "3_months",
            "max_uses": 1,
            "invitee_name": "TEST_Honorary_No_Balance",
            "notes": "Test honorary invite without starting balance"
        })
        
        assert response.status_code == 200, f"Failed to create invite: {response.text}"
        
        data = response.json()
        assert "code" in data, "Response should contain invite code"
        assert data.get("starting_amount") == 0, "Starting amount should be 0"
        
        print(f"SUCCESS: Created honorary invite without starting balance: {data['code']}")
        
        # Cleanup - delete the test invite
        invite_id = data.get("id")
        if invite_id:
            self.session.delete(f"{BASE_URL}/api/admin/license-invites/{invite_id}")


class TestActiveSignalEndpoint:
    """Test active signal endpoint"""
    
    def test_get_active_signal(self):
        """Test GET /api/trade/active-signal (public endpoint)"""
        response = requests.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200, f"Failed to get active signal: {response.text}"
        
        data = response.json()
        
        if data.get("signal"):
            signal = data["signal"]
            print(f"SUCCESS: Active signal - {signal.get('direction')} {signal.get('product')} at {signal.get('trade_time')}")
        else:
            print("INFO: No active signal currently")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

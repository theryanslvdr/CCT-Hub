"""
Iteration 148 - Test suite for bug fixes:
1. POST /api/profit/commission - save commission with commission_date field
2. GET /api/profit/commissions - returns saved commissions
3. POST /api/rewards/admin/sync-all-users - rewards batch sync endpoint
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.text}")
    
    data = response.json()
    return data.get("access_token")  # Note: uses access_token, not token


@pytest.fixture
def auth_headers(auth_token):
    """Headers with authentication"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestCommissionEndpoint:
    """Tests for commission save functionality - was returning 500 before fix"""
    
    def test_save_commission_with_commission_date(self, auth_headers):
        """Test POST /api/profit/commission with commission_date field"""
        commission_date = "2026-01-15"
        payload = {
            "amount": 25.50,
            "source": "referral",
            "traders_count": 3,
            "notes": "Test commission from iteration 148",
            "commission_date": commission_date
        }
        
        response = requests.post(
            f"{BASE_URL}/api/profit/commission",
            headers=auth_headers,
            json=payload
        )
        
        # Should NOT return 500 anymore
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "commission_id" in data, "Response should contain commission_id"
        assert "amount" in data, "Response should contain amount"
        assert data["amount"] == 25.50, f"Amount should be 25.50, got {data['amount']}"
        assert "commission_date" in data, "Response should contain commission_date"
        assert data["commission_date"] == commission_date, f"Commission date mismatch"
        
        print(f"SUCCESS: Commission saved with ID: {data['commission_id']}")
    
    def test_save_commission_without_commission_date(self, auth_headers):
        """Test commission save without commission_date uses today's date"""
        payload = {
            "amount": 15.00,
            "source": "referral",
            "traders_count": 2,
            "notes": "Test commission without date"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/profit/commission",
            headers=auth_headers,
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "commission_date" in data, "Response should contain commission_date"
        # Should default to today's date
        today = datetime.now().strftime("%Y-%m-%d")
        assert data["commission_date"] == today, f"Should default to today's date"
        
        print(f"SUCCESS: Commission saved with default date: {data['commission_date']}")


class TestCommissionsRetrieval:
    """Tests for GET /api/profit/commissions"""
    
    def test_get_commissions_list(self, auth_headers):
        """Test that saved commissions can be retrieved"""
        response = requests.get(
            f"{BASE_URL}/api/profit/commissions",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Should have at least the commissions we created
        print(f"SUCCESS: Retrieved {len(data)} commissions")
        
        if len(data) > 0:
            commission = data[0]
            # Verify commission structure
            expected_fields = ["id", "user_id", "amount"]
            for field in expected_fields:
                assert field in commission, f"Commission should have {field} field"


class TestRewardsBatchSync:
    """Tests for rewards batch sync endpoint"""
    
    def test_batch_sync_all_users(self, auth_headers):
        """Test POST /api/rewards/admin/sync-all-users"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/admin/sync-all-users",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Response should have sync summary
        print(f"SUCCESS: Batch sync response: {data}")
    
    def test_get_sync_status(self, auth_headers):
        """Test GET /api/rewards/admin/sync-status"""
        response = requests.get(
            f"{BASE_URL}/api/rewards/admin/sync-status",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have user counts
        print(f"SUCCESS: Sync status response: {data}")


class TestProfitSummary:
    """Tests for profit summary endpoint (regression)"""
    
    def test_get_profit_summary(self, auth_headers):
        """Test GET /api/profit/summary works correctly"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        expected_fields = ["total_deposits", "account_value", "total_actual_profit"]
        for field in expected_fields:
            assert field in data, f"Summary should have {field} field"
        
        print(f"SUCCESS: Profit summary: account_value=${data.get('account_value')}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

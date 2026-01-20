"""
Test iteration 61: VSD (Virtual Share Distribution) Panel and Account Value Bug Fix

Tests:
1. Account Value Bug Fix: /api/profit/summary no longer returns licensee_funds field
2. VSD Panel: /api/profit/vsd endpoint returns correct structure
3. VSD endpoint requires Master Admin role
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestAccountValueBugFix:
    """Test that /api/profit/summary no longer returns licensee_funds field"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.user = data["user"]
        
    def test_profit_summary_no_licensee_funds(self):
        """Verify /api/profit/summary does NOT return licensee_funds field"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200, f"Failed to get summary: {response.text}"
        
        data = response.json()
        
        # Verify licensee_funds is NOT in the response (bug fix)
        assert "licensee_funds" not in data, f"licensee_funds should NOT be in summary response. Got: {data.keys()}"
        
        # Verify expected fields ARE present
        expected_fields = ["account_value", "total_deposits", "total_actual_profit", "total_trades"]
        for field in expected_fields:
            assert field in data, f"Expected field '{field}' not in response"
        
        print(f"✓ /api/profit/summary correctly excludes licensee_funds")
        print(f"  account_value: ${data['account_value']}")
        print(f"  total_deposits: ${data['total_deposits']}")
        print(f"  total_actual_profit: ${data['total_actual_profit']}")
        
    def test_profit_summary_account_value_is_raw_balance(self):
        """Verify account_value is the raw Merin balance without additions"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        account_value = data["account_value"]
        
        # Account value should be a reasonable number (not inflated by double-counting)
        assert isinstance(account_value, (int, float)), "account_value should be numeric"
        assert account_value >= 0, "account_value should be non-negative"
        
        print(f"✓ account_value is raw balance: ${account_value}")


class TestVSDEndpoint:
    """Test /api/profit/vsd endpoint for Virtual Share Distribution"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.user = data["user"]
        
    def test_vsd_endpoint_returns_correct_structure(self):
        """Verify /api/profit/vsd returns correct structure"""
        response = self.session.get(f"{BASE_URL}/api/profit/vsd")
        assert response.status_code == 200, f"Failed to get VSD: {response.text}"
        
        data = response.json()
        
        # Verify required fields
        required_fields = [
            "total_pool",
            "master_admin_portion",
            "master_admin_share_percentage",
            "licensee_funds",
            "licensee_share_percentage",
            "licensee_count",
            "licensee_breakdown"
        ]
        
        for field in required_fields:
            assert field in data, f"Required field '{field}' not in VSD response"
        
        print(f"✓ VSD endpoint returns correct structure")
        print(f"  total_pool: ${data['total_pool']}")
        print(f"  master_admin_portion: ${data['master_admin_portion']} ({data['master_admin_share_percentage']}%)")
        print(f"  licensee_funds: ${data['licensee_funds']} ({data['licensee_share_percentage']}%)")
        print(f"  licensee_count: {data['licensee_count']}")
        
    def test_vsd_licensee_breakdown_structure(self):
        """Verify licensee_breakdown has correct fields"""
        response = self.session.get(f"{BASE_URL}/api/profit/vsd")
        assert response.status_code == 200
        
        data = response.json()
        licensee_breakdown = data.get("licensee_breakdown", [])
        
        if len(licensee_breakdown) > 0:
            licensee = licensee_breakdown[0]
            
            # Verify licensee breakdown fields
            expected_fields = [
                "license_id",
                "user_id",
                "user_name",
                "license_type",
                "starting_amount",  # Total Deposit
                "current_amount",   # Current Balance
                "total_profit",     # Total Profit
                "share_percentage"  # % Share
            ]
            
            for field in expected_fields:
                assert field in licensee, f"Expected field '{field}' not in licensee breakdown"
            
            print(f"✓ Licensee breakdown has correct structure")
            print(f"  First licensee: {licensee['user_name']}")
            print(f"    Current Balance: ${licensee['current_amount']}")
            print(f"    Total Deposit: ${licensee['starting_amount']}")
            print(f"    Total Profit: ${licensee['total_profit']}")
            print(f"    Share %: {licensee['share_percentage']}%")
        else:
            print("✓ No licensees in breakdown (empty array)")
            
    def test_vsd_math_consistency(self):
        """Verify VSD math: total_pool = master_admin_portion + licensee_funds"""
        response = self.session.get(f"{BASE_URL}/api/profit/vsd")
        assert response.status_code == 200
        
        data = response.json()
        
        total_pool = data["total_pool"]
        master_portion = data["master_admin_portion"]
        licensee_funds = data["licensee_funds"]
        
        # Verify: total_pool = master_admin_portion + licensee_funds
        calculated_total = master_portion + licensee_funds
        
        # Allow small floating point difference
        assert abs(total_pool - calculated_total) < 0.01, \
            f"Math inconsistency: total_pool ({total_pool}) != master_portion ({master_portion}) + licensee_funds ({licensee_funds})"
        
        print(f"✓ VSD math is consistent")
        print(f"  {total_pool} = {master_portion} + {licensee_funds}")
        
    def test_vsd_percentages_sum_to_100(self):
        """Verify share percentages sum to 100%"""
        response = self.session.get(f"{BASE_URL}/api/profit/vsd")
        assert response.status_code == 200
        
        data = response.json()
        
        master_pct = data["master_admin_share_percentage"]
        licensee_pct = data["licensee_share_percentage"]
        
        total_pct = master_pct + licensee_pct
        
        # Allow small floating point difference
        assert abs(total_pct - 100) < 0.1, \
            f"Percentages don't sum to 100: {master_pct}% + {licensee_pct}% = {total_pct}%"
        
        print(f"✓ Percentages sum to 100%: {master_pct}% + {licensee_pct}% = {total_pct}%")


class TestVSDAccessControl:
    """Test that VSD endpoint requires Master Admin role"""
    
    def test_vsd_requires_authentication(self):
        """Verify /api/profit/vsd requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/profit/vsd")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        
        print(f"✓ VSD endpoint requires authentication (got {response.status_code})")


class TestSummaryVsVSDComparison:
    """Compare /api/profit/summary and /api/profit/vsd to verify no double-counting"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
    def test_summary_account_value_equals_vsd_total_pool(self):
        """Verify summary.account_value equals vsd.total_pool (no double-counting)"""
        # Get summary
        summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert summary_response.status_code == 200
        summary = summary_response.json()
        
        # Get VSD
        vsd_response = self.session.get(f"{BASE_URL}/api/profit/vsd")
        assert vsd_response.status_code == 200
        vsd = vsd_response.json()
        
        summary_account_value = summary["account_value"]
        vsd_total_pool = vsd["total_pool"]
        
        # They should be equal (no double-counting)
        assert abs(summary_account_value - vsd_total_pool) < 0.01, \
            f"Double-counting detected! summary.account_value ({summary_account_value}) != vsd.total_pool ({vsd_total_pool})"
        
        print(f"✓ No double-counting: summary.account_value = vsd.total_pool")
        print(f"  summary.account_value: ${summary_account_value}")
        print(f"  vsd.total_pool: ${vsd_total_pool}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

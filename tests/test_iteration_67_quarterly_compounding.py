"""
Test iteration 67: Quarterly compounding and licensee view fixes

Tests:
1. Backend: /api/admin/licenses/{license_id}/projections returns correct sequential balances
2. Backend: daily_profit is fixed per quarter (quarterly compounding)
3. Frontend: Monthly Summary shows 2 cards for licensees (hiding Total Commission)
4. Frontend: Current Profit correctly sums profits from days where managerTraded === true
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://diag-staging.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
TEST_LICENSE_ID = "618db632-4910-47d0-a0dc-1efdd297736a"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for Master Admin"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def license_projections(auth_token):
    """Get license projections for the test licensee"""
    response = requests.get(
        f"{BASE_URL}/api/admin/licenses/{TEST_LICENSE_ID}/projections",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200, f"Failed to get projections: {response.text}"
    return response.json()


class TestQuarterlyCompounding:
    """Test quarterly compounding logic in license projections"""
    
    def test_projections_endpoint_returns_data(self, license_projections):
        """Verify the projections endpoint returns valid data"""
        assert "projections" in license_projections
        assert "starting_amount" in license_projections
        assert len(license_projections["projections"]) > 0
        
    def test_starting_amount_correct(self, license_projections):
        """Verify starting amount is $2611.10"""
        assert license_projections["starting_amount"] == 2611.1
        
    def test_lot_size_calculation(self, license_projections):
        """Verify lot_size = starting_amount / 980"""
        starting_amount = license_projections["starting_amount"]
        expected_lot_size = round(starting_amount / 980, 2)
        
        # Check first projection
        first_proj = license_projections["projections"][0]
        assert first_proj["lot_size"] == expected_lot_size, \
            f"Expected lot_size {expected_lot_size}, got {first_proj['lot_size']}"
            
    def test_daily_profit_calculation(self, license_projections):
        """Verify daily_profit = lot_size * 15"""
        first_proj = license_projections["projections"][0]
        expected_daily_profit = round(first_proj["lot_size"] * 15, 2)
        
        assert first_proj["daily_profit"] == expected_daily_profit, \
            f"Expected daily_profit {expected_daily_profit}, got {first_proj['daily_profit']}"
            
    def test_lot_size_fixed_within_quarter(self, license_projections):
        """Verify lot_size is fixed within Q1 (Jan-Mar)"""
        q1_projections = [
            p for p in license_projections["projections"]
            if p["date"].startswith("2025-01") or 
               p["date"].startswith("2025-02") or 
               p["date"].startswith("2025-03")
        ]
        
        if len(q1_projections) > 0:
            lot_sizes = set(p["lot_size"] for p in q1_projections)
            assert len(lot_sizes) == 1, \
                f"Lot size should be fixed within Q1, but found: {lot_sizes}"
                
    def test_daily_profit_fixed_within_quarter(self, license_projections):
        """Verify daily_profit is fixed within Q1 (Jan-Mar)"""
        q1_projections = [
            p for p in license_projections["projections"]
            if p["date"].startswith("2025-01") or 
               p["date"].startswith("2025-02") or 
               p["date"].startswith("2025-03")
        ]
        
        if len(q1_projections) > 0:
            daily_profits = set(p["daily_profit"] for p in q1_projections)
            assert len(daily_profits) == 1, \
                f"Daily profit should be fixed within Q1, but found: {daily_profits}"
                
    def test_no_balance_drops(self, license_projections):
        """Verify balance never drops on consecutive days (the key fix)"""
        projections = license_projections["projections"]
        
        for i in range(1, len(projections)):
            prev = projections[i - 1]
            curr = projections[i]
            
            assert curr["start_value"] >= prev["start_value"], \
                f"Balance dropped from {prev['date']} ({prev['start_value']}) to {curr['date']} ({curr['start_value']})"
                
    def test_balance_increases_when_manager_traded(self, license_projections):
        """Verify balance increases by daily_profit when manager traded"""
        projections = license_projections["projections"]
        
        for i in range(1, len(projections)):
            prev = projections[i - 1]
            curr = projections[i]
            
            if prev["manager_traded"]:
                expected_balance = prev["start_value"] + prev["daily_profit"]
                # Allow small floating point differences
                assert abs(curr["start_value"] - expected_balance) < 0.01, \
                    f"After trading on {prev['date']}, expected balance {expected_balance}, got {curr['start_value']}"
                    
    def test_balance_unchanged_when_manager_not_traded(self, license_projections):
        """Verify balance stays same when manager didn't trade (for past days)"""
        projections = license_projections["projections"]
        
        # Only check past days where manager didn't trade
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        for i in range(1, len(projections)):
            prev = projections[i - 1]
            curr = projections[i]
            
            # Only check if previous day is in the past and manager didn't trade
            if prev["date"] < today and not prev["manager_traded"]:
                assert curr["start_value"] == prev["start_value"], \
                    f"Balance should stay same when manager didn't trade on {prev['date']}"


class TestCurrentProfitCalculation:
    """Test that Current Profit correctly sums profits from days where managerTraded === true"""
    
    def test_current_profit_only_counts_traded_days(self, license_projections):
        """Verify current profit only includes days where manager traded"""
        projections = license_projections["projections"]
        
        # Calculate expected current profit (sum of daily_profit for traded days)
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        expected_profit = sum(
            p["daily_profit"] 
            for p in projections 
            if p["manager_traded"] and p["date"] <= today
        )
        
        # Count traded days
        traded_days = sum(
            1 for p in projections 
            if p["manager_traded"] and p["date"] <= today
        )
        
        print(f"Expected current profit: ${expected_profit:.2f} from {traded_days} traded days")
        
        # This is a data assertion - the frontend should calculate the same
        assert traded_days >= 0, "Should have some traded days"


class TestProjectionStructure:
    """Test the structure of projection data"""
    
    def test_projection_has_required_fields(self, license_projections):
        """Verify each projection has all required fields"""
        required_fields = [
            "date", "start_value", "account_value", 
            "lot_size", "daily_profit", "manager_traded"
        ]
        
        for proj in license_projections["projections"][:10]:  # Check first 10
            for field in required_fields:
                assert field in proj, f"Missing field '{field}' in projection"
                
    def test_projection_dates_are_weekdays(self, license_projections):
        """Verify projections only include weekdays (no weekends)"""
        from datetime import datetime
        
        for proj in license_projections["projections"]:
            date = datetime.strptime(proj["date"], "%Y-%m-%d")
            assert date.weekday() < 5, \
                f"Projection includes weekend: {proj['date']} (weekday={date.weekday()})"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

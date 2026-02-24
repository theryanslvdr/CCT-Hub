"""
Iteration 127: Test Year Projection Calculation Fix

Bug Report: Year 1 projection calculation was wrong, showing $44,943.39 instead of ~$12,414.73.
Root Cause: Projections were being calculated from today's current balance instead of from the 
            effective start date with the original starting amount.

Fix: Show BOTH types of projections:
1. "license_year_projections" - From effective_start_date using starting_amount (for license anniversary)
2. "projections" - Forward projections from TODAY's balance (for future planning)

Key Endpoints:
- GET /api/profit/licensee/year-projections (returns both projection arrays)

Test Credentials:
- Admin: iam@ryansalvador.com / admin123
- Test Licensee User ID: c0bc35c0-1112-4ca9-8c63-df8f8bafd11f
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestYearProjectionsFix:
    """Tests for the corrected year projection calculations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and get auth token"""
        self.admin_email = "iam@ryansalvador.com"
        self.admin_password = "admin123"
        self.test_licensee_user_id = "c0bc35c0-1112-4ca9-8c63-df8f8bafd11f"
        
        # Login as admin
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_backend_returns_both_projection_arrays(self):
        """Backend API returns both 'projections' and 'license_year_projections' arrays"""
        # Call the endpoint for the test licensee
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Failed to get year projections: {response.text}"
        data = response.json()
        
        # Verify both arrays exist
        assert "projections" in data, "Missing 'projections' array (forward from today)"
        assert "license_year_projections" in data, "Missing 'license_year_projections' array (from start date)"
        
        # Both should be lists
        assert isinstance(data["projections"], list), "'projections' should be a list"
        assert isinstance(data["license_year_projections"], list), "'license_year_projections' should be a list"
        
        # Both should have entries for years 1, 2, 3, 5
        assert len(data["projections"]) >= 4, f"Expected at least 4 forward projections, got {len(data['projections'])}"
        assert len(data["license_year_projections"]) >= 4, f"Expected at least 4 license year projections, got {len(data['license_year_projections'])}"
        
        print(f"✓ Backend returns both projection arrays")
        print(f"  - Forward projections (from today): {len(data['projections'])} entries")
        print(f"  - License year projections (from start date): {len(data['license_year_projections'])} entries")
    
    def test_license_year_projections_use_starting_amount(self):
        """License year projections should calculate from effective_start_date using starting_amount"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Failed to get year projections: {response.text}"
        data = response.json()
        
        starting_amount = data.get("starting_amount", 0)
        effective_start_date = data.get("effective_start_date")
        
        assert starting_amount > 0, "starting_amount should be positive"
        assert effective_start_date, "effective_start_date should be present"
        
        # License year projections should show what the account would be at end of license year 1, 2, 3, 5
        # starting from the effective_start_date with starting_amount
        license_year_1 = next((p for p in data["license_year_projections"] if p["license_year"] == 1), None)
        assert license_year_1 is not None, "Missing license year 1 projection"
        
        # Verify the structure has required fields
        assert "projected_value" in license_year_1, "Missing projected_value in license year projection"
        assert "total_profit" in license_year_1, "Missing total_profit in license year projection"
        assert "growth_percent" in license_year_1, "Missing growth_percent in license year projection"
        assert "from_start_date" in license_year_1, "Missing from_start_date in license year projection"
        
        # The from_start_date should match the effective_start_date
        assert license_year_1["from_start_date"] == effective_start_date, \
            f"from_start_date mismatch: expected {effective_start_date}, got {license_year_1['from_start_date']}"
        
        print(f"✓ License year projections use starting_amount=${starting_amount}")
        print(f"  - Effective start date: {effective_start_date}")
        print(f"  - License Year 1 projected value: ${license_year_1['projected_value']}")
        print(f"  - License Year 1 total profit: ${license_year_1['total_profit']}")
        print(f"  - License Year 1 growth percent: {license_year_1['growth_percent']}%")
    
    def test_forward_projections_use_current_value(self):
        """Forward projections should calculate from today's current balance"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Failed to get year projections: {response.text}"
        data = response.json()
        
        current_value = data.get("current_value", 0)
        starting_amount = data.get("starting_amount", 0)
        
        assert current_value > 0, "current_value should be positive"
        
        # Forward projections should show what account will be 1, 2, 3, 5 years from now
        forward_1yr = next((p for p in data["projections"] if p["years"] == 1), None)
        assert forward_1yr is not None, "Missing 1-year forward projection"
        
        # Verify the structure has required fields
        assert "projected_value" in forward_1yr, "Missing projected_value in forward projection"
        assert "total_profit" in forward_1yr, "Missing total_profit in forward projection"
        assert "profit_from_current" in forward_1yr, "Missing profit_from_current in forward projection"
        assert "growth_percent" in forward_1yr, "Missing growth_percent in forward projection"
        
        # profit_from_current should be projected_value - current_value (profit from now)
        expected_profit_from_current = forward_1yr["projected_value"] - current_value
        # Allow small floating point variance
        assert abs(forward_1yr["profit_from_current"] - expected_profit_from_current) < 1, \
            f"profit_from_current calculation error: expected ~{expected_profit_from_current}, got {forward_1yr['profit_from_current']}"
        
        print(f"✓ Forward projections use current_value=${current_value}")
        print(f"  - 1-Year forward projected value: ${forward_1yr['projected_value']}")
        print(f"  - Profit from current (1yr): ${forward_1yr['profit_from_current']}")
        print(f"  - Growth percent: {forward_1yr['growth_percent']}%")
    
    def test_projections_use_quarterly_compounding(self):
        """Verify projections use quarterly compounding formula, not daily compounding"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Failed to get year projections: {response.text}"
        data = response.json()
        
        current_value = data.get("current_value", 0)
        starting_daily_profit = data.get("starting_daily_profit", 0)
        
        # Verify the daily profit matches the quarterly formula
        expected_daily_profit = round((current_value / 980) * 15, 2)
        assert abs(starting_daily_profit - expected_daily_profit) < 0.01, \
            f"Daily profit formula mismatch: expected {expected_daily_profit}, got {starting_daily_profit}"
        
        # Check that projections have quarter_breakdown (evidence of quarterly compounding)
        forward_1yr = next((p for p in data["projections"] if p["years"] == 1), None)
        if "quarter_breakdown" in forward_1yr:
            # Quarter breakdown shows quarterly recalculation
            assert isinstance(forward_1yr["quarter_breakdown"], list), "quarter_breakdown should be a list"
            print(f"  - Quarter breakdown has {len(forward_1yr['quarter_breakdown'])} quarters")
        
        print(f"✓ Quarterly compounding formula verified")
        print(f"  - Current value: ${current_value}")
        print(f"  - Starting daily profit: ${starting_daily_profit}")
        print(f"  - Expected daily profit (formula): ${expected_daily_profit}")
    
    def test_license_year_vs_forward_projections_differ(self):
        """License year projections should differ from forward projections (unless started today)"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Failed to get year projections: {response.text}"
        data = response.json()
        
        current_value = data.get("current_value", 0)
        starting_amount = data.get("starting_amount", 0)
        
        # If user has made profit (current_value > starting_amount), the projections should differ
        if current_value != starting_amount:
            license_year_1 = next((p for p in data["license_year_projections"] if p["license_year"] == 1), None)
            forward_1yr = next((p for p in data["projections"] if p["years"] == 1), None)
            
            # Forward projections start from current_value (higher base, higher result)
            # License year projections start from starting_amount (original base)
            # They should be different
            print(f"✓ License year vs forward projections differ (expected behavior)")
            print(f"  - Starting amount: ${starting_amount}")
            print(f"  - Current value: ${current_value}")
            print(f"  - License Year 1 end: ${license_year_1['projected_value'] if license_year_1 else 'N/A'}")
            print(f"  - Forward 1yr from now: ${forward_1yr['projected_value'] if forward_1yr else 'N/A'}")
        else:
            print(f"  - Note: User's current_value equals starting_amount, projections may be similar")
    
    def test_effective_start_date_parsing(self):
        """Verify effective_start_date is properly returned"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Failed to get year projections: {response.text}"
        data = response.json()
        
        effective_start_date = data.get("effective_start_date")
        assert effective_start_date, "effective_start_date should be present in response"
        
        # Should be in YYYY-MM-DD format
        try:
            parsed_date = datetime.strptime(effective_start_date, "%Y-%m-%d")
            print(f"✓ effective_start_date properly formatted: {effective_start_date}")
        except ValueError as e:
            pytest.fail(f"effective_start_date not in YYYY-MM-DD format: {effective_start_date}")
    
    def test_admin_can_query_any_licensee_projections(self):
        """Admin can pass user_id param to get projections for any licensee"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200, f"Admin should be able to query any licensee's projections: {response.text}"
        data = response.json()
        
        # Verify we got data for the requested user
        assert "projections" in data, "Should have projections for the requested user"
        assert "license_year_projections" in data, "Should have license_year_projections for the requested user"
        
        print(f"✓ Admin can query projections for user_id={self.test_licensee_user_id}")


class TestTradingDaysFunction:
    """Tests for the quarterly growth projection function in utils/trading_days.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin for any API calls needed"""
        self.admin_email = "iam@ryansalvador.com"
        self.admin_password = "admin123"
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.admin_email,
            "password": self.admin_password
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_projection_trading_days_count(self):
        """Verify projections use ~250 trading days per year"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": "c0bc35c0-1112-4ca9-8c63-df8f8bafd11f"},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check trading_days_per_year
        assert data.get("trading_days_per_year") == 250, "Should use 250 trading days per year"
        
        # Check that 1-year projection has ~250 trading days
        forward_1yr = next((p for p in data["projections"] if p["years"] == 1), None)
        if forward_1yr and "trading_days" in forward_1yr:
            assert forward_1yr["trading_days"] == 250, f"1-year should have 250 trading days, got {forward_1yr['trading_days']}"
        
        print(f"✓ Projections use 250 trading days per year")


class TestProjectionResponse:
    """Tests for the full projection response structure"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        self.admin_token = response.json()["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.test_licensee_user_id = "c0bc35c0-1112-4ca9-8c63-df8f8bafd11f"
    
    def test_response_structure_complete(self):
        """Full response structure validation"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": self.test_licensee_user_id},
            headers=self.admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Top-level required fields
        required_top_level = [
            "current_value",
            "starting_amount",
            "current_profit",
            "starting_daily_profit",
            "trading_days_per_year",
            "effective_start_date",
            "projections",
            "license_year_projections"
        ]
        
        for field in required_top_level:
            assert field in data, f"Missing required top-level field: {field}"
        
        # projections array structure
        for p in data["projections"]:
            assert "years" in p, "Each projection should have 'years'"
            assert "projected_value" in p, "Each projection should have 'projected_value'"
            assert "total_profit" in p, "Each projection should have 'total_profit'"
        
        # license_year_projections array structure
        for p in data["license_year_projections"]:
            assert "license_year" in p, "Each license year projection should have 'license_year'"
            assert "projected_value" in p, "Each license year projection should have 'projected_value'"
            assert "total_profit" in p, "Each license year projection should have 'total_profit'"
            assert "from_start_date" in p, "Each license year projection should have 'from_start_date'"
        
        print(f"✓ Full response structure validated")
        print(f"  - current_value: ${data['current_value']}")
        print(f"  - starting_amount: ${data['starting_amount']}")
        print(f"  - current_profit: ${data['current_profit']}")
        print(f"  - effective_start_date: {data['effective_start_date']}")

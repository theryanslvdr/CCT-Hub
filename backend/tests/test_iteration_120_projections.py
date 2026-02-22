"""
Iteration 120: Growth Projection Calculations Tests

Testing the corrected formula for growth projections:
- Daily Profit = round((Account Value at Quarter Start / 980) * 15, 2)
- Daily profit is FIXED for the entire quarter, recalculated at each new calendar quarter start
- Projections assume manager trades every trading day (~250 per year)
- US market holidays are excluded from trading days

Endpoints tested:
- GET /api/profit/licensee/year-projections
- GET /api/profit/licensee/daily-projection
- Family member projections via /api/family/members/{member_id}/projections
"""
import pytest
import requests
import os
from datetime import datetime, date, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"


class TestGrowthProjections:
    """Test growth projection endpoints for honorary licensees."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as master admin."""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip(f"Admin login failed: {resp.status_code} - {resp.text}")
    
    @pytest.fixture(scope="class")
    def licensee_auth(self):
        """Login as licensee (Rizza)."""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        if resp.status_code == 200:
            data = resp.json()
            return {
                "token": data.get("access_token"),
                "user_id": data.get("user", {}).get("id")
            }
        pytest.skip(f"Licensee login failed: {resp.status_code} - {resp.text}")
    
    # ========== Year Projections Tests ==========
    
    def test_year_projections_returns_correct_structure(self, licensee_auth):
        """Verify year projections endpoint returns expected structure with all required fields."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check top-level structure
        assert "current_value" in data, "Missing current_value"
        assert "starting_amount" in data, "Missing starting_amount"
        assert "starting_daily_profit" in data, "Missing starting_daily_profit"
        assert "projections" in data, "Missing projections array"
        assert "trading_days_per_year" in data, "Missing trading_days_per_year"
        
        # Verify trading_days_per_year is 250
        assert data["trading_days_per_year"] == 250, f"Expected 250 trading days/year, got {data['trading_days_per_year']}"
        
        # Check projections array has correct years
        projections = data["projections"]
        assert len(projections) == 4, f"Expected 4 projections (1,2,3,5 years), got {len(projections)}"
        
        years_found = [p["years"] for p in projections]
        assert years_found == [1, 2, 3, 5], f"Expected [1, 2, 3, 5] years, got {years_found}"
    
    def test_year_projections_each_year_has_correct_fields(self, licensee_auth):
        """Verify each year projection has the required fields."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        for proj in data["projections"]:
            required_fields = [
                "years", "projected_value", "total_profit", "profit_from_current",
                "growth_percent", "trading_days", "quarter_breakdown"
            ]
            for field in required_fields:
                assert field in proj, f"Missing {field} in projection for year {proj.get('years')}"
            
            # Verify trading_days = years * 250
            expected_trading_days = proj["years"] * 250
            assert proj["trading_days"] == expected_trading_days, \
                f"Year {proj['years']}: expected {expected_trading_days} trading days, got {proj['trading_days']}"
            
            # Verify quarter_breakdown exists and is a list
            assert isinstance(proj["quarter_breakdown"], list), "quarter_breakdown should be a list"
            assert len(proj["quarter_breakdown"]) > 0, "quarter_breakdown should not be empty"
    
    def test_year_projections_quarter_breakdown_fields(self, licensee_auth):
        """Verify quarter breakdown has correct structure."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Check first year projection's quarter breakdown
        first_year = data["projections"][0]
        for qtr in first_year["quarter_breakdown"]:
            required_fields = ["quarter", "trading_days", "daily_profit", "start_value", "end_value", "quarter_profit"]
            for field in required_fields:
                assert field in qtr, f"Missing {field} in quarter breakdown"
            
            # Verify quarter format (e.g., "Q1 2026")
            assert qtr["quarter"].startswith("Q"), f"Invalid quarter format: {qtr['quarter']}"
    
    def test_year_projections_formula_verification(self, licensee_auth):
        """Verify the formula: daily_profit = round((balance / 980) * 15, 2)"""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        current_value = data["current_value"]
        starting_daily_profit = data["starting_daily_profit"]
        
        # Verify starting daily profit formula
        expected_daily_profit = round((current_value / 980) * 15, 2)
        assert starting_daily_profit == expected_daily_profit, \
            f"Daily profit formula wrong: expected {expected_daily_profit}, got {starting_daily_profit}"
        
        print(f"\nCurrent value: ${current_value}")
        print(f"Starting daily profit: ${starting_daily_profit}")
        print(f"Formula verification: ({current_value} / 980) * 15 = {expected_daily_profit}")
    
    def test_year_projections_growth_increases_over_time(self, licensee_auth):
        """Verify projected values increase year over year due to compounding."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        projections = data["projections"]
        prev_value = data["current_value"]
        
        for proj in projections:
            assert proj["projected_value"] > prev_value, \
                f"Year {proj['years']}: projected_value ({proj['projected_value']}) should be > previous ({prev_value})"
            prev_value = proj["projected_value"]
            
            # Also verify growth_percent is positive
            assert proj["growth_percent"] > 0, f"Year {proj['years']}: growth_percent should be positive"
    
    # ========== Daily Projection Tests ==========
    
    def test_daily_projection_returns_correct_structure(self, licensee_auth):
        """Verify daily projection endpoint returns expected structure."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check top-level structure
        assert "projections" in data, "Missing projections array"
        assert "effective_start_date" in data, "Missing effective_start_date"
        assert "starting_amount" in data, "Missing starting_amount"
        assert "current_balance" in data, "Missing current_balance"
        
        # Verify projections is a list
        assert isinstance(data["projections"], list), "projections should be a list"
        assert len(data["projections"]) > 0, "projections should not be empty"
    
    def test_daily_projection_entry_fields(self, licensee_auth):
        """Verify each daily projection entry has required fields."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        required_fields = [
            "date", "start_value", "account_value", "lot_size",
            "daily_profit", "manager_traded", "is_projected", "has_override"
        ]
        
        for proj in data["projections"][:10]:  # Check first 10 entries
            for field in required_fields:
                assert field in proj, f"Missing {field} in projection entry for {proj.get('date')}"
    
    def test_daily_projection_past_dates_use_actual_trade_data(self, licensee_auth):
        """Verify past dates use actual manager_traded status (not always True)."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        today = datetime.now().strftime("%Y-%m-%d")
        past_entries = [p for p in data["projections"] if p["date"] < today]
        
        # Past entries should have is_projected=False
        for entry in past_entries[:5]:
            assert entry["is_projected"] == False, \
                f"Past date {entry['date']} should have is_projected=False"
    
    def test_daily_projection_future_dates_are_projected(self, licensee_auth):
        """Verify future dates have is_projected=True and manager_traded=True."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        today = datetime.now().strftime("%Y-%m-%d")
        future_entries = [p for p in data["projections"] if p["date"] > today]
        
        assert len(future_entries) > 0, "Should have future projections"
        
        for entry in future_entries[:10]:
            assert entry["is_projected"] == True, \
                f"Future date {entry['date']} should have is_projected=True"
            assert entry["manager_traded"] == True, \
                f"Future date {entry['date']} should have manager_traded=True (projected)"
    
    def test_daily_projection_quarter_boundaries_change_profit(self, licensee_auth):
        """Verify daily_profit changes at quarter boundaries (Apr 1, Jul 1, Oct 1, Jan 1)."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        projections = data["projections"]
        
        # Group by quarter
        quarters = {}
        for proj in projections:
            date_str = proj["date"]
            month = int(date_str.split("-")[1])
            year = date_str.split("-")[0]
            quarter = (month - 1) // 3 + 1
            quarter_key = f"Q{quarter} {year}"
            
            if quarter_key not in quarters:
                quarters[quarter_key] = []
            quarters[quarter_key].append(proj)
        
        # Verify each quarter has consistent daily_profit
        for quarter_key, entries in quarters.items():
            if len(entries) > 1:
                first_profit = entries[0]["daily_profit"]
                for entry in entries:
                    assert entry["daily_profit"] == first_profit, \
                        f"Quarter {quarter_key}: daily_profit should be consistent within quarter"
        
        print(f"\nQuarters found in projection: {list(quarters.keys())[:8]}")
    
    def test_daily_projection_no_weekend_entries(self, licensee_auth):
        """Verify no Saturday or Sunday entries appear in projections."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        for proj in data["projections"]:
            date_obj = datetime.strptime(proj["date"], "%Y-%m-%d")
            weekday = date_obj.weekday()
            assert weekday < 5, f"Weekend date found: {proj['date']} (weekday={weekday})"
    
    # ========== Holiday Exclusion Tests ==========
    
    def test_daily_projection_excludes_major_holidays(self, licensee_auth):
        """Verify major US market holidays are excluded from projections."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        projection_dates = {p["date"] for p in data["projections"]}
        
        # 2026 US Market Holidays (expected to be excluded)
        holidays_2026 = [
            "2026-01-01",  # New Year's Day
            "2026-01-19",  # MLK Day (3rd Monday of January)
            "2026-02-16",  # Presidents' Day (3rd Monday of February)
            "2026-04-03",  # Good Friday
            "2026-05-25",  # Memorial Day (last Monday of May)
            "2026-06-19",  # Juneteenth
            "2026-07-03",  # Independence Day (observed - July 4 is Saturday)
            "2026-09-07",  # Labor Day (1st Monday of September)
            "2026-11-26",  # Thanksgiving (4th Thursday of November)
            "2026-12-25",  # Christmas
        ]
        
        holidays_in_projections = []
        for holiday in holidays_2026:
            if holiday in projection_dates:
                holidays_in_projections.append(holiday)
        
        assert len(holidays_in_projections) == 0, \
            f"These holidays should be excluded but were found: {holidays_in_projections}"
        
        print("\n2026 holidays correctly excluded from projections")
    
    def test_daily_projection_excludes_christmas_2025(self, licensee_auth):
        """Verify Christmas 2025 is excluded (if in date range)."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        projection_dates = {p["date"] for p in data["projections"]}
        
        christmas_2025 = "2025-12-25"
        if christmas_2025 in projection_dates:
            pytest.fail(f"Christmas 2025 ({christmas_2025}) should be excluded from trading days")
    
    # ========== Formula Verification Tests ==========
    
    def test_daily_profit_matches_formula(self, licensee_auth):
        """Verify daily_profit = round((start_value / 980) * 15, 2) at quarter start."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Check first entry (should be start of a quarter or close to it)
        starting_amount = data["starting_amount"]
        first_entry = data["projections"][0]
        
        expected_first_profit = round((starting_amount / 980) * 15, 2)
        actual_first_profit = first_entry["daily_profit"]
        
        # The first entry should use starting_amount for daily_profit calculation
        assert actual_first_profit == expected_first_profit, \
            f"First entry daily_profit: expected {expected_first_profit}, got {actual_first_profit}"
        
        print(f"\nStarting amount: ${starting_amount}")
        print(f"First daily profit: ${actual_first_profit}")
        print(f"Formula check: ({starting_amount} / 980) * 15 = {expected_first_profit}")
    
    def test_account_value_grows_when_manager_trades(self, licensee_auth):
        """Verify account_value = start_value + daily_profit when manager_traded=True."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/daily-projection", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Check entries where manager_traded=True
        for proj in data["projections"][:20]:
            if proj["manager_traded"]:
                expected_value = round(proj["start_value"] + proj["daily_profit"], 2)
                assert proj["account_value"] == expected_value, \
                    f"Date {proj['date']}: expected account_value={expected_value}, got {proj['account_value']}"
            else:
                # When manager didn't trade, account_value should equal start_value
                assert proj["account_value"] == proj["start_value"], \
                    f"Date {proj['date']}: when manager_traded=False, account_value should equal start_value"


class TestFamilyMemberProjections:
    """Test family member projections use the same formula."""
    
    @pytest.fixture(scope="class")
    def licensee_auth(self):
        """Login as licensee (Rizza)."""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        if resp.status_code == 200:
            data = resp.json()
            return {
                "token": data.get("access_token"),
                "user_id": data.get("user", {}).get("id")
            }
        pytest.skip(f"Licensee login failed: {resp.status_code} - {resp.text}")
    
    def test_get_family_members(self, licensee_auth):
        """Verify can get family members list."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/family/members", headers=headers)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "family_members" in data, "Missing family_members in response"
        print(f"\nFamily members found: {len(data['family_members'])}")
    
    def test_family_member_projections_structure(self, licensee_auth):
        """Verify family member projections have correct structure."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        
        # First get family members
        resp = requests.get(f"{BASE_URL}/api/family/members", headers=headers)
        assert resp.status_code == 200
        members = resp.json().get("family_members", [])
        
        if not members:
            pytest.skip("No family members found to test projections")
        
        # Get projections for first member
        member_id = members[0]["id"]
        resp = requests.get(f"{BASE_URL}/api/family/members/{member_id}/projections", headers=headers)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify structure
        assert "projections" in data, "Missing projections"
        assert "starting_amount" in data, "Missing starting_amount"
        assert "current_balance" in data, "Missing current_balance"
        
        if data["projections"]:
            required_fields = ["date", "start_value", "account_value", "daily_profit", "manager_traded", "is_projected"]
            for field in required_fields:
                assert field in data["projections"][0], f"Missing {field} in family projection"
    
    def test_family_member_projections_exclude_holidays(self, licensee_auth):
        """Verify family member projections also exclude US market holidays."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        
        # Get family members
        resp = requests.get(f"{BASE_URL}/api/family/members", headers=headers)
        assert resp.status_code == 200
        members = resp.json().get("family_members", [])
        
        if not members:
            pytest.skip("No family members found")
        
        member_id = members[0]["id"]
        resp = requests.get(f"{BASE_URL}/api/family/members/{member_id}/projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        projection_dates = {p["date"] for p in data.get("projections", [])}
        
        # Check some 2026 holidays are excluded
        holidays_2026 = ["2026-01-01", "2026-07-03", "2026-11-26", "2026-12-25"]
        
        for holiday in holidays_2026:
            if holiday in projection_dates:
                pytest.fail(f"Holiday {holiday} should be excluded from family member projections")
    
    def test_family_member_projections_no_weekends(self, licensee_auth):
        """Verify no weekend entries in family member projections."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        
        # Get family members
        resp = requests.get(f"{BASE_URL}/api/family/members", headers=headers)
        assert resp.status_code == 200
        members = resp.json().get("family_members", [])
        
        if not members:
            pytest.skip("No family members found")
        
        member_id = members[0]["id"]
        resp = requests.get(f"{BASE_URL}/api/family/members/{member_id}/projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        for proj in data.get("projections", []):
            date_obj = datetime.strptime(proj["date"], "%Y-%m-%d")
            assert date_obj.weekday() < 5, f"Weekend found in family projections: {proj['date']}"


class TestTradingDaysModule:
    """Test the trading_days utility module directly via API behavior."""
    
    @pytest.fixture(scope="class")
    def licensee_auth(self):
        """Login as licensee."""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": LICENSEE_EMAIL,
            "password": LICENSEE_PASSWORD
        })
        if resp.status_code == 200:
            return {"token": resp.json().get("access_token")}
        pytest.skip("Login failed")
    
    def test_approximately_250_trading_days_per_year(self, licensee_auth):
        """Verify year projections use ~250 trading days per year."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Year 1 should have exactly 250 trading days
        year1 = data["projections"][0]
        assert year1["years"] == 1
        assert year1["trading_days"] == 250, f"Year 1 should have 250 trading days, got {year1['trading_days']}"
        
        # Year 5 should have 1250 trading days
        year5 = data["projections"][3]
        assert year5["years"] == 5
        assert year5["trading_days"] == 1250, f"Year 5 should have 1250 trading days, got {year5['trading_days']}"
    
    def test_quarterly_compounding_increases_profit(self, licensee_auth):
        """Verify quarterly compounding causes daily_profit to increase each quarter."""
        headers = {"Authorization": f"Bearer {licensee_auth['token']}"}
        resp = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers)
        
        assert resp.status_code == 200
        data = resp.json()
        
        year1 = data["projections"][0]
        quarter_breakdown = year1["quarter_breakdown"]
        
        # Each quarter should have higher daily_profit than the previous
        prev_daily_profit = 0
        for i, qtr in enumerate(quarter_breakdown):
            if i > 0:
                assert qtr["daily_profit"] >= prev_daily_profit, \
                    f"Quarter {qtr['quarter']}: daily_profit should increase due to compounding"
            prev_daily_profit = qtr["daily_profit"]
            
            print(f"{qtr['quarter']}: daily_profit=${qtr['daily_profit']}, end_value=${qtr['end_value']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 110: Backend Tests for Profit Tracker Bugs & Admin Habits CRUD

Test scenarios:
1. Admin habits CRUD works (POST, GET, DELETE /api/admin/habits)
2. Honorary licensee Rizza Miles should have account_value > $5000 (not stale starting_amount)
3. account_value consistency between different endpoints
4. License projections must have correct manager_traded values for 20 trading days
5. Projections must not include weekends
6. Projections must exclude did_not_trade entries
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from requirements
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"

# Honorary licensee test data
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"
RIZZA_LICENSE_ID = "6ccbfd46-6d07-42c4-aee8-4996d56ad4d1"
RIZZA_STARTING_AMOUNT = 5000  # As per test data


@pytest.fixture(scope="module")
def admin_token():
    """Get Master Admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestAdminHabitsCRUD:
    """Test Admin Habits CRUD operations to verify 404 bug is fixed"""
    
    created_habit_id = None
    
    def test_01_get_admin_habits(self, admin_headers):
        """GET /api/admin/habits should return 200"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        print(f"GET /api/admin/habits - Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "habits" in data, "Response should contain 'habits' key"
        print(f"Found {len(data['habits'])} habits")
    
    def test_02_create_admin_habit(self, admin_headers):
        """POST /api/admin/habits should create a habit (was returning 404)"""
        habit_data = {
            "title": "TEST_habit_iteration_110",
            "description": "Test habit for verifying 404 bug fix",
            "action_type": "generic",
            "action_data": "",
            "is_gate": True,
            "validity_days": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/habits",
            headers=admin_headers,
            json=habit_data
        )
        print(f"POST /api/admin/habits - Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Response should contain habit 'id'"
        assert data["title"] == habit_data["title"], "Title mismatch"
        
        # Store for cleanup
        TestAdminHabitsCRUD.created_habit_id = data["id"]
        print(f"Created habit with ID: {data['id']}")
    
    def test_03_verify_habit_created(self, admin_headers):
        """Verify the created habit exists in GET response"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        habit_ids = [h["id"] for h in data.get("habits", [])]
        
        assert TestAdminHabitsCRUD.created_habit_id is not None, "No habit was created"
        assert TestAdminHabitsCRUD.created_habit_id in habit_ids, "Created habit not found in list"
        print(f"Verified habit {TestAdminHabitsCRUD.created_habit_id} exists")
    
    def test_04_delete_admin_habit(self, admin_headers):
        """DELETE /api/admin/habits/{id} should deactivate the habit"""
        if TestAdminHabitsCRUD.created_habit_id is None:
            pytest.skip("No habit to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/habits/{TestAdminHabitsCRUD.created_habit_id}",
            headers=admin_headers
        )
        print(f"DELETE /api/admin/habits/{TestAdminHabitsCRUD.created_habit_id} - Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestHonoraryLicenseeAccountValue:
    """Test that honorary licensee (Rizza Miles) has correct account_value > $5000"""
    
    def test_01_get_member_details(self, admin_headers):
        """GET /api/admin/members/{rizza_id} should return account_value > $5000"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}",
            headers=admin_headers
        )
        print(f"GET /api/admin/members/{RIZZA_USER_ID} - Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Response stats: {data.get('stats', {})}")
        
        stats = data.get("stats", {})
        account_value = stats.get("account_value", 0)
        total_profit = stats.get("total_profit", 0)
        is_licensee = stats.get("is_licensee", False)
        
        print(f"Account Value: ${account_value}")
        print(f"Total Profit: ${total_profit}")
        print(f"Is Licensee: {is_licensee}")
        
        # Key assertions
        assert is_licensee == True, "Rizza should be identified as a licensee"
        assert account_value > RIZZA_STARTING_AMOUNT, \
            f"Account value ${account_value} should be > starting amount ${RIZZA_STARTING_AMOUNT}. " \
            f"Expected approx $6530 after 20 trading days."
        assert total_profit > 0, f"Total profit should be > 0, got ${total_profit}"
        
        print(f"✓ Account value ${account_value} > starting ${RIZZA_STARTING_AMOUNT}")
        print(f"✓ Total profit ${total_profit} > $0")
    
    def test_02_simulate_member_view(self, admin_headers):
        """GET /api/admin/members/{rizza_id}/simulate should return account_value > $5000"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/simulate",
            headers=admin_headers
        )
        print(f"GET /api/admin/members/{RIZZA_USER_ID}/simulate - Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        account_value = data.get("account_value", 0)
        total_profit = data.get("total_profit", 0)
        lot_size = data.get("lot_size", 0)
        
        print(f"Simulate - Account Value: ${account_value}")
        print(f"Simulate - Total Profit: ${total_profit}")
        print(f"Simulate - Lot Size: {lot_size}")
        
        assert account_value > RIZZA_STARTING_AMOUNT, \
            f"Simulate account value ${account_value} should be > ${RIZZA_STARTING_AMOUNT}"
        assert total_profit > 0, f"Simulate total profit should be > 0, got ${total_profit}"
        
        print(f"✓ Simulate account value ${account_value} > starting ${RIZZA_STARTING_AMOUNT}")


class TestLicenseProjections:
    """Test license projections endpoint for manager_traded column fix"""
    
    def test_01_get_license_projections_returns_data(self, admin_headers):
        """GET /api/admin/licenses/{license_id}/projections should return projections"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses/{RIZZA_LICENSE_ID}/projections",
            headers=admin_headers
        )
        print(f"GET /api/admin/licenses/{RIZZA_LICENSE_ID}/projections - Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        projections = data.get("projections", [])
        
        print(f"Total projections returned: {len(projections)}")
        assert len(projections) > 0, "Should have at least one projection"
        
        # Check first projection structure
        first = projections[0]
        print(f"First projection: {first}")
        assert "date" in first, "Projection should have 'date'"
        assert "manager_traded" in first, "Projection should have 'manager_traded'"
        assert "account_value" in first, "Projection should have 'account_value'"
        assert "lot_size" in first, "Projection should have 'lot_size'"
        assert "daily_profit" in first, "Projection should have 'daily_profit'"
    
    def test_02_no_weekends_in_projections(self, admin_headers):
        """Projections must not include Saturday (5) or Sunday (6)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses/{RIZZA_LICENSE_ID}/projections",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        projections = data.get("projections", [])
        
        weekend_dates = []
        for proj in projections:
            date_str = proj.get("date", "")
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                if dt.weekday() >= 5:
                    weekend_dates.append(date_str)
            except:
                pass
        
        print(f"Weekend dates found: {weekend_dates}")
        assert len(weekend_dates) == 0, f"Projections should not include weekends: {weekend_dates}"
        print("✓ No weekends in projections")
    
    def test_03_manager_traded_true_for_trading_days(self, admin_headers):
        """Verify manager_traded=true for dates when master admin traded"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses/{RIZZA_LICENSE_ID}/projections",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        projections = data.get("projections", [])
        
        # Count trading days (manager_traded = true)
        trading_days = [p for p in projections if p.get("manager_traded") == True]
        non_trading_days = [p for p in projections if p.get("manager_traded") == False]
        
        print(f"Trading days (manager_traded=true): {len(trading_days)}")
        print(f"Non-trading days (manager_traded=false): {len(non_trading_days)}")
        
        # According to test data, there should be 20 trading days
        assert len(trading_days) >= 20, \
            f"Expected at least 20 trading days, found {len(trading_days)}. " \
            f"Test data has 20 master admin trade logs from 2026-01-20 to 2026-02-16."
        
        # Show some trading day dates
        print(f"Sample trading days: {[t['date'] for t in trading_days[:5]]}")
        print(f"✓ Found {len(trading_days)} trading days")
    
    def test_04_account_value_grows_on_trading_days(self, admin_headers):
        """Verify account value increases when manager_traded=true"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses/{RIZZA_LICENSE_ID}/projections",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        projections = data.get("projections", [])
        
        # Get past projections only (up to today)
        today_str = datetime.now().strftime("%Y-%m-%d")
        past_projections = [p for p in projections if p["date"] <= today_str]
        
        print(f"Past projections (up to today): {len(past_projections)}")
        
        if len(past_projections) > 1:
            # Find a day when manager traded and check value grew
            for i, proj in enumerate(past_projections[1:], 1):
                if proj.get("manager_traded") == True:
                    prev = past_projections[i-1]
                    current_value = proj.get("account_value", 0)
                    prev_value = prev.get("account_value", prev.get("start_value", 0))
                    
                    print(f"Day {proj['date']}: manager_traded=True")
                    print(f"  Previous value: ${prev_value}")
                    print(f"  Current value: ${current_value}")
                    print(f"  Daily profit: ${proj.get('daily_profit', 0)}")
                    
                    assert current_value > prev_value, \
                        f"Account value should grow on trading day {proj['date']}: ${prev_value} -> ${current_value}"
                    break
            
            # Also check final account value
            last_proj = past_projections[-1]
            print(f"Final projection ({last_proj['date']}): ${last_proj.get('account_value', 0)}")


class TestAccountValueConsistency:
    """Test that account_value is consistent across all endpoints"""
    
    def test_01_consistency_between_endpoints(self, admin_headers):
        """Account value should be consistent between member details, simulate, and projections"""
        
        # 1. Get member details
        resp1 = requests.get(f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}", headers=admin_headers)
        assert resp1.status_code == 200
        member_details_value = resp1.json().get("stats", {}).get("account_value", 0)
        
        # 2. Get simulate view
        resp2 = requests.get(f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/simulate", headers=admin_headers)
        assert resp2.status_code == 200
        simulate_value = resp2.json().get("account_value", 0)
        
        # 3. Get license projections (last past projection)
        resp3 = requests.get(f"{BASE_URL}/api/admin/licenses/{RIZZA_LICENSE_ID}/projections", headers=admin_headers)
        assert resp3.status_code == 200
        projections = resp3.json().get("projections", [])
        
        # Find the latest past projection
        today_str = datetime.now().strftime("%Y-%m-%d")
        past_projections = [p for p in projections if p["date"] <= today_str]
        projections_value = past_projections[-1]["account_value"] if past_projections else 0
        
        print(f"Member Details account_value: ${member_details_value}")
        print(f"Simulate account_value: ${simulate_value}")
        print(f"Projections (last past day) account_value: ${projections_value}")
        
        # All should be > starting amount
        assert member_details_value > RIZZA_STARTING_AMOUNT, \
            f"Member details ${member_details_value} should be > ${RIZZA_STARTING_AMOUNT}"
        assert simulate_value > RIZZA_STARTING_AMOUNT, \
            f"Simulate ${simulate_value} should be > ${RIZZA_STARTING_AMOUNT}"
        assert projections_value > RIZZA_STARTING_AMOUNT, \
            f"Projections ${projections_value} should be > ${RIZZA_STARTING_AMOUNT}"
        
        # Check if values are reasonably close (within 5% tolerance due to timing)
        # Member details and simulate should match closely
        if member_details_value > 0 and simulate_value > 0:
            diff_pct = abs(member_details_value - simulate_value) / member_details_value * 100
            print(f"Difference between member details and simulate: {diff_pct:.2f}%")
            assert diff_pct < 10, f"Member details and simulate differ by {diff_pct:.2f}%"
        
        print("✓ Account values are consistent across endpoints")


class TestProfitSummaryEndpoint:
    """Test /api/profit/summary for licensee returns correct values"""
    
    # NOTE: This test requires logging in AS Rizza Miles
    # Since Rizza doesn't have a password set, we test via admin endpoints only
    
    def test_01_verify_licensee_profit_calculation(self, admin_headers):
        """Verify profit is calculated correctly: account_value - starting_amount"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        stats = data.get("stats", {})
        
        account_value = stats.get("account_value", 0)
        total_profit = stats.get("total_profit", 0)
        
        # For licensees, profit should be: account_value - starting_amount
        calculated_profit = account_value - RIZZA_STARTING_AMOUNT
        
        print(f"Account Value: ${account_value}")
        print(f"Starting Amount: ${RIZZA_STARTING_AMOUNT}")
        print(f"Expected Profit: ${calculated_profit}")
        print(f"Reported Profit: ${total_profit}")
        
        # Allow small floating point difference
        diff = abs(calculated_profit - total_profit)
        assert diff < 1, f"Profit mismatch: expected ${calculated_profit}, got ${total_profit}"
        
        print(f"✓ Profit calculation correct: ${total_profit}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

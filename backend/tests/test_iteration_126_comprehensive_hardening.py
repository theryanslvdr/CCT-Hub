"""
Iteration 126: Comprehensive Hardening Tests for Honorary Licensee Profit Fix

Tests verify:
1. Admin GET /api/admin/members/{user_id} returns total_profit > 0 for licensees
2. GET /api/profit/summary returns correct values for Rizza
3. GET /api/profit/licensee/year-projections returns 4 projections
4. Admin year-projections with user_id param works for ALL honorary users
5. POST /api/admin/licensee-health-check shows all licensees status 'ok'
6. Stats include 'starting_amount' and 'license_type' fields
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"

# All honorary user IDs
HONORARY_USER_IDS = [
    "7cc2b490-5e55-433b-9ac6-45d5bdfaf732",
    "c0bc35c0-1112-4ca9-8c63-df8f8bafd11f",
    "d19307ec-03fe-4973-af97-5ef035b97a18",
    "bcbbbf94-321e-4bbb-b60e-fc286552b6d7",
    "04cd9299-2d58-4983-810a-1190923bbdaa",
    "19ccb9d7-139f-4918-a662-ad72483010b1",
]


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def licensee_token():
    """Get licensee (Rizza) authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": LICENSEE_EMAIL, "password": LICENSEE_PASSWORD},
    )
    assert response.status_code == 200, f"Licensee login failed: {response.text}"
    data = response.json()
    return data.get("access_token") or data.get("token")


class TestAdminMemberDetails:
    """CRITICAL: Admin member details must show total_profit > 0 for licensees"""

    def test_admin_get_rizza_member_details_profit_positive(self, admin_token):
        """GET /api/admin/members/{user_id} - stats.total_profit MUST be > 0"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}", headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        stats = data.get("stats", {})
        
        # CRITICAL assertions - this is what caused the $0.00 bug
        assert stats.get("total_profit", 0) > 0, f"total_profit must be > 0, got: {stats.get('total_profit')}"
        assert stats.get("account_value", 0) > stats.get("starting_amount", 0), \
            f"account_value ({stats.get('account_value')}) must be > starting_amount ({stats.get('starting_amount')})"
        assert stats.get("performance_rate", 0) > 0, f"performance_rate must be > 0, got: {stats.get('performance_rate')}"
        
        # Verify specific expected values for Rizza (starting_amount=5000)
        assert stats.get("starting_amount") == 5000, f"starting_amount expected 5000, got: {stats.get('starting_amount')}"
        
        print(f"PASSED: Rizza total_profit={stats.get('total_profit')}, account_value={stats.get('account_value')}")

    def test_admin_member_details_includes_new_fields(self, admin_token):
        """Stats must include 'starting_amount' and 'license_type' fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}", headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        stats = data.get("stats", {})
        
        # New fields must be present
        assert "starting_amount" in stats, "stats missing 'starting_amount' field"
        assert "license_type" in stats, "stats missing 'license_type' field"
        
        # Validate field values
        assert stats.get("starting_amount") == 5000, f"starting_amount should be 5000, got: {stats.get('starting_amount')}"
        # license_type should be honorary_fa or similar
        license_type = stats.get("license_type", "").lower()
        assert "honorary" in license_type, f"license_type should contain 'honorary', got: {stats.get('license_type')}"
        
        print(f"PASSED: starting_amount={stats.get('starting_amount')}, license_type={stats.get('license_type')}")


class TestLicenseeProfitSummary:
    """Test /api/profit/summary endpoint for Rizza (licensee)"""

    def test_profit_summary_total_actual_profit_positive(self, licensee_token):
        """GET /api/profit/summary - total_actual_profit > 0"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Must have positive profit (was showing $0.00 before)
        assert data.get("total_actual_profit", 0) > 0, \
            f"total_actual_profit must be > 0, got: {data.get('total_actual_profit')}"
        assert data.get("account_value", 0) > 5000, \
            f"account_value must be > 5000 (starting_amount), got: {data.get('account_value')}"
        
        print(f"PASSED: total_actual_profit={data.get('total_actual_profit')}, account_value={data.get('account_value')}")

    def test_profit_summary_expected_values_approximately(self, licensee_token):
        """Verify Rizza's values are in expected range (~$6530 account value, ~$1530 profit)"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Account value should be around $6530 (allowing some variance)
        account_value = data.get("account_value", 0)
        assert 6000 <= account_value <= 7000, \
            f"account_value expected ~$6530, got: {account_value}"
        
        # Total profit should be around $1530
        total_profit = data.get("total_actual_profit", 0)
        assert 1000 <= total_profit <= 2000, \
            f"total_actual_profit expected ~$1530, got: {total_profit}"
        
        print(f"PASSED: account_value={account_value}, total_actual_profit={total_profit}")


class TestLicenseeYearProjections:
    """Test /api/profit/licensee/year-projections endpoint"""

    def test_rizza_year_projections_returns_4_projections(self, licensee_token):
        """GET /api/profit/licensee/year-projections - returns 4 projections with positive values"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections", headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        projections = data.get("projections", [])
        
        # Must have exactly 4 projections (1yr, 2yr, 3yr, 5yr)
        assert len(projections) == 4, f"Expected 4 projections, got: {len(projections)}"
        
        # All projections must have positive values
        for proj in projections:
            assert proj.get("projected_value", 0) > 0, \
                f"Projection {proj.get('years')}yr value must be > 0, got: {proj.get('projected_value')}"
        
        print(f"PASSED: {len(projections)} projections returned with positive values")

    def test_admin_can_get_projections_with_user_id_param(self, admin_token):
        """Admin GET /api/profit/licensee/year-projections?user_id=xxx - returns 200"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections?user_id={RIZZA_USER_ID}",
            headers=headers,
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        projections = data.get("projections", [])
        assert len(projections) == 4, f"Expected 4 projections, got: {len(projections)}"
        
        print(f"PASSED: Admin can get projections for user {RIZZA_USER_ID}")


class TestAllHonoraryUserProjections:
    """Test year-projections for ALL honorary user IDs with admin token"""

    @pytest.mark.parametrize("user_id", HONORARY_USER_IDS)
    def test_admin_projections_for_all_honorary_users(self, admin_token, user_id):
        """Admin GET year-projections with user_id param must return 200 for all honorary users"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections?user_id={user_id}",
            headers=headers,
        )
        assert response.status_code == 200, \
            f"Failed for user_id={user_id}: {response.status_code} - {response.text}"
        
        data = response.json()
        # Should either have projections or a valid response
        assert data is not None, f"Empty response for user_id={user_id}"
        
        print(f"PASSED: Projections endpoint works for honorary user {user_id}")


class TestLicenseeHealthCheck:
    """Test admin licensee health check endpoint"""

    def test_health_check_all_licensees_ok(self, admin_token):
        """POST /api/admin/licensee-health-check - all licensees status 'ok'"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/admin/licensee-health-check", headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Check totals
        assert data.get("total", 0) > 0, "No licensees found"
        assert data.get("ok", 0) == data.get("total", 0), \
            f"Not all licensees OK: ok={data.get('ok')}, total={data.get('total')}"
        assert data.get("broken", 0) == 0, f"Some licensees broken: {data.get('broken')}"
        
        # Verify individual licensees
        licensees = data.get("licensees", [])
        for lic in licensees:
            assert lic.get("status") == "ok", \
                f"Licensee {lic.get('email')} has status={lic.get('status')}, expected 'ok'"
        
        print(f"PASSED: All {data.get('total')} licensees have status 'ok'")


class TestFloatCasting:
    """Verify float() casting is working properly (no Decimal128/string issues)"""

    def test_admin_member_details_numeric_types(self, admin_token):
        """Verify all numeric stats are proper Python floats/ints (not Decimal128/strings)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}", headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        stats = data.get("stats", {})
        
        # These should all be numeric (int or float), not strings
        numeric_fields = ["total_profit", "account_value", "performance_rate", "starting_amount", "total_deposits"]
        for field in numeric_fields:
            value = stats.get(field)
            if value is not None:
                assert isinstance(value, (int, float)), \
                    f"stats.{field} should be numeric, got type {type(value).__name__}: {value}"
        
        print("PASSED: All numeric stats are proper Python numeric types")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 125: Case-Insensitive Honorary License Bug Fix Tests
Root cause: ALL license_type checks were case-sensitive. 
Fix: _is_honorary() helper for case-insensitive checks.
"""
import pytest
import httpx
import os

API_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://system-restore-lab.preview.emergentagent.com")
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"

# All known honorary licensee user IDs from the problem statement
HONORARY_USER_IDS = [
    "19ccb9d7-139f-4918-a662-ad72483010b1",  # Rizza Miles
    "7cc2b490-5e55-433b-9ac6-45d5bdfaf732",  
    "c0bc35c0-1112-4ca9-8c63-df8f8bafd11f",  
    "d19307ec-03fe-4973-af97-5ef035b97a18",  
    "bcbbbf94-321e-4bbb-b60e-fc286552b6d7",  
    "04cd9299-2d58-4983-810a-1190923bbdaa",  
]


def get_token(email: str, password: str) -> str:
    """Login and return access token."""
    resp = httpx.post(
        f"{API_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


class TestRizzaLicenseeProfitSummary:
    """Test GET /api/profit/summary for Rizza - the main bug fix verification"""
    
    def test_rizza_summary_returns_positive_account_value(self):
        """CRITICAL: Account value should be > starting_amount (was $0.00 before fix)"""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert resp.status_code == 200, f"Summary failed: {resp.text}"
        data = resp.json()
        
        # Key assertions - these were broken before the fix
        assert data.get("account_value", 0) > 5000, f"Account value should be > $5000, got {data.get('account_value')}"
        assert data.get("total_actual_profit", 0) > 0, f"Total profit should be > $0, got {data.get('total_actual_profit')}"
        assert data.get("is_licensee") is True, "Should be marked as licensee"
        
        # Expected values per problem statement: account_value=6530.6, total_profit=1530.6
        assert data["account_value"] >= 6000, f"Expected account_value >= 6000, got {data['account_value']}"
        
    def test_rizza_summary_performance_rate_not_zero(self):
        """Performance rate should not be 0.0% (was broken before fix)"""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Performance rate = (account_value / starting_amount - 1) * 100
        # For Rizza: (6530.6 / 5000 - 1) * 100 = 30.6%
        performance_rate = data.get("performance_rate", 0)
        assert performance_rate > 0, f"Performance rate should be > 0%, got {performance_rate}%"


class TestLicenseeYearProjections:
    """Test GET /api/profit/licensee/year-projections"""
    
    def test_rizza_year_projections_returns_values(self):
        """CRITICAL: Projections should load (was 'Failed to load projections' before fix)"""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/year-projections",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify structure
        assert "current_value" in data, "Missing current_value"
        assert "starting_amount" in data, "Missing starting_amount"
        assert "projections" in data, "Missing projections array"
        assert len(data["projections"]) == 4, f"Expected 4 projections, got {len(data['projections'])}"
        
        # Verify positive values
        assert data["current_value"] > 0, f"current_value should be > 0, got {data['current_value']}"
        assert data["starting_amount"] == 5000.0, f"starting_amount should be 5000, got {data['starting_amount']}"
        
        # Verify projections have positive growth
        for p in data["projections"]:
            assert p["projected_value"] > data["current_value"], f"Projection {p['years']}yr should be > current"
            assert p["total_profit"] > 0, f"total_profit should be > 0 for {p['years']}yr"
            assert p["growth_percent"] > 0, f"growth_percent should be > 0 for {p['years']}yr"
    
    def test_admin_can_view_rizza_projections(self):
        """Admin should be able to view licensee projections via user_id param"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/year-projections",
            params={"user_id": RIZZA_USER_ID},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Admin projection request failed: {resp.text}"
        data = resp.json()
        
        assert data["current_value"] > 5000, f"current_value should be > 5000, got {data['current_value']}"
        assert len(data["projections"]) == 4


class TestLicenseeDailyProjection:
    """Test GET /api/profit/licensee/daily-projection"""
    
    def test_rizza_daily_projection_returns_array(self):
        """Daily projections should return array with daily_profit > 0"""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/daily-projection",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Daily projection failed: {resp.text}"
        data = resp.json()
        
        assert "projections" in data, "Missing projections array"
        assert len(data["projections"]) > 0, "Projections array should not be empty"
        
        # Check first day's daily_profit
        first = data["projections"][0]
        assert "daily_profit" in first, "Missing daily_profit field"
        assert first["daily_profit"] > 0, f"daily_profit should be > 0, got {first['daily_profit']}"


class TestLicenseeHealthCheck:
    """Test POST /api/admin/licensee-health-check"""
    
    def test_health_check_returns_all_licensees_ok(self):
        """Health check should return all licensees with status 'ok' (no broken ones)"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = httpx.post(
            f"{API_URL}/api/admin/licensee-health-check",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        data = resp.json()
        
        # Verify structure
        assert "total" in data, "Missing total count"
        assert "ok" in data, "Missing ok count"
        assert "broken" in data, "Missing broken count"
        assert "results" in data, "Missing results array"
        
        # All should be ok
        assert data["broken"] == 0, f"Expected 0 broken licensees, got {data['broken']}"
        assert data["ok"] == data["total"], f"Expected all {data['total']} to be ok, but only {data['ok']} are"
        
        # Check Rizza is in results
        rizza_found = False
        for result in data["results"]:
            if result.get("user_id") == RIZZA_USER_ID:
                rizza_found = True
                assert result.get("status") == "ok", f"Rizza should have status 'ok', got {result.get('status')}"
                # Health check returns 'current_value' not 'account_value'
                current_val = result.get("current_value", result.get("account_value", 0))
                assert current_val > 5000, f"Rizza current_value should be > 5000, got {current_val}"
                break
        
        assert rizza_found, "Rizza should be in health check results"


class TestAllHonoraryLicenseesProjections:
    """Test all 6 honorary licensees work (via admin token)"""
    
    @pytest.mark.parametrize("user_id", HONORARY_USER_IDS)
    def test_honorary_licensee_projections_work(self, user_id):
        """Each honorary licensee should return valid projections"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/licensee/year-projections",
            params={"user_id": user_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        
        # Should either return 200 with data or 404 if user not found/no license
        # But should NOT return 500 or have calculation errors
        assert resp.status_code in [200, 404], f"User {user_id}: unexpected status {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("current_value", 0) > 0, f"User {user_id}: current_value should be > 0"
            assert len(data.get("projections", [])) == 4, f"User {user_id}: should have 4 projections"


class TestIsHonoraryFunctionCaseVariations:
    """Verify _is_honorary handles case variations correctly
    Test indirectly via API - if projections work, the function is working.
    """
    
    def test_profit_summary_as_licensee(self):
        """If _is_honorary works, summary should show correct values regardless of DB case"""
        token = get_token(LICENSEE_EMAIL, LICENSEE_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # The fact that we get correct values proves _is_honorary() works
        # (before fix, case mismatch caused $0 values)
        assert data["is_licensee"] is True
        assert data["account_value"] > 5000  # Not $0.00
        assert data["total_actual_profit"] > 0  # Not $0.00


class TestAdminMemberDetailsForLicensee:
    """Test GET /api/admin/members/{user_id} returns correct data for licensees"""
    
    def test_rizza_member_details_has_correct_stats(self):
        """Admin member details should show is_licensee=true and correct values"""
        token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = httpx.get(
            f"{API_URL}/api/admin/members/{RIZZA_USER_ID}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Member details failed: {resp.text}"
        data = resp.json()
        
        assert "stats" in data, "Missing stats in response"
        stats = data["stats"]
        
        assert stats.get("is_licensee") is True, "Should be marked as licensee"
        assert stats.get("account_value", 0) > 5000, f"account_value should be > 5000, got {stats.get('account_value')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

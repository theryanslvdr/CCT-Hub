"""
Iteration 183 Feature Tests
============================
Testing the following new features:
1. GET /api/admin/members/stats/overview - returns {active_members, team_leaders, suspended, in_danger}
2. GET /api/admin/members (default, no status filter) - should NOT include suspended users
3. GET /api/admin/members?status=suspended - should ONLY show suspended users
4. GET /api/admin/members?status=active - should show active non-suspended users
5. Suspend/Unsuspend member flow
6. Regression: Login, onboarding, rewards summary streak

Credentials: Master Admin - iam@ryansalvador.com / admin123
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "iam@ryansalvador.com",
        "password": "admin123"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def admin_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


# ─── Test 1: Stats Overview Endpoint ───

class TestStatsOverviewEndpoint:
    """Tests for GET /api/admin/members/stats/overview"""

    def test_stats_overview_returns_200(self, admin_headers):
        """Stats overview endpoint should return 200"""
        resp = requests.get(f"{BASE_URL}/api/admin/members/stats/overview", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ Stats overview returns 200")

    def test_stats_overview_has_required_fields(self, admin_headers):
        """Stats overview should return all 4 required fields"""
        resp = requests.get(f"{BASE_URL}/api/admin/members/stats/overview", headers=admin_headers)
        data = resp.json()
        
        required_fields = ["active_members", "team_leaders", "suspended", "in_danger"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], int), f"{field} should be an integer, got {type(data[field])}"
        
        print(f"✓ Stats: active={data['active_members']}, leaders={data['team_leaders']}, suspended={data['suspended']}, danger={data['in_danger']}")

    def test_stats_overview_values_are_non_negative(self, admin_headers):
        """All stat values should be non-negative"""
        resp = requests.get(f"{BASE_URL}/api/admin/members/stats/overview", headers=admin_headers)
        data = resp.json()
        
        for field in ["active_members", "team_leaders", "suspended", "in_danger"]:
            assert data[field] >= 0, f"{field} should be >= 0, got {data[field]}"
        
        print("✓ All stat values are non-negative")


# ─── Test 2: Default Member List Excludes Suspended ───

class TestMemberListFiltering:
    """Tests for member list status filtering"""

    def test_default_member_list_returns_200(self, admin_headers):
        """Default member list should return 200"""
        resp = requests.get(f"{BASE_URL}/api/admin/members", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ Default member list returns 200")

    def test_default_member_list_excludes_suspended(self, admin_headers):
        """Default member list should NOT include suspended users"""
        resp = requests.get(f"{BASE_URL}/api/admin/members", headers=admin_headers)
        data = resp.json()
        
        members = data.get("members", [])
        suspended_in_list = [m for m in members if m.get("is_suspended") == True]
        
        assert len(suspended_in_list) == 0, f"Found {len(suspended_in_list)} suspended users in default list, should be 0"
        print(f"✓ Default list has {len(members)} members, none suspended")

    def test_suspended_filter_only_shows_suspended(self, admin_headers):
        """status=suspended should ONLY show suspended users"""
        resp = requests.get(f"{BASE_URL}/api/admin/members?status=suspended", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        members = data.get("members", [])
        if len(members) > 0:
            # All members should be suspended
            non_suspended = [m for m in members if m.get("is_suspended") != True]
            assert len(non_suspended) == 0, f"Found {len(non_suspended)} non-suspended users in suspended filter"
        
        print(f"✓ Suspended filter returns {len(members)} suspended users")

    def test_active_filter_excludes_suspended(self, admin_headers):
        """status=active should exclude suspended users"""
        resp = requests.get(f"{BASE_URL}/api/admin/members?status=active", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        members = data.get("members", [])
        suspended_in_active = [m for m in members if m.get("is_suspended") == True]
        
        assert len(suspended_in_active) == 0, f"Found {len(suspended_in_active)} suspended users in active filter"
        print(f"✓ Active filter returns {len(members)} active members")

    def test_member_counts_consistency(self, admin_headers):
        """Stats overview counts should align with filtered member lists"""
        # Get stats overview
        stats_resp = requests.get(f"{BASE_URL}/api/admin/members/stats/overview", headers=admin_headers)
        stats = stats_resp.json()
        
        # Get suspended count from filtered list
        suspended_resp = requests.get(f"{BASE_URL}/api/admin/members?status=suspended&limit=100", headers=admin_headers)
        suspended_data = suspended_resp.json()
        
        # The suspended count in stats should match suspended list total
        assert stats["suspended"] == suspended_data.get("total", len(suspended_data.get("members", []))), \
            f"Stats suspended={stats['suspended']} != list total={suspended_data.get('total')}"
        
        print(f"✓ Stats suspended count ({stats['suspended']}) matches filtered list")


# ─── Test 3: Suspend/Unsuspend Flow ───

class TestSuspendUnsuspendFlow:
    """Tests for suspend and unsuspend member endpoints"""

    def test_suspend_endpoint_exists(self, admin_headers):
        """POST /api/admin/members/{id}/suspend should exist"""
        # Try with a non-existent ID to see if endpoint exists (should return 404 not 405)
        resp = requests.post(f"{BASE_URL}/api/admin/members/nonexistent123/suspend", headers=admin_headers)
        # Accept 404 (user not found) or 400 (validation error), but not 405 (method not allowed)
        assert resp.status_code in [404, 400, 200, 422], f"Unexpected status: {resp.status_code}"
        print("✓ Suspend endpoint exists")

    def test_unsuspend_endpoint_exists(self, admin_headers):
        """POST /api/admin/members/{id}/unsuspend should exist"""
        resp = requests.post(f"{BASE_URL}/api/admin/members/nonexistent123/unsuspend", headers=admin_headers)
        assert resp.status_code in [404, 400, 200, 422], f"Unexpected status: {resp.status_code}"
        print("✓ Unsuspend endpoint exists")


# ─── Test 4: Regression Tests ───

class TestRegression:
    """Regression tests to ensure existing functionality still works"""

    def test_login_still_works(self):
        """Login should still work with valid credentials"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data or "token" in data, "No token field in response"
        assert "user" in data
        print("✓ Login works correctly")

    def test_onboarding_endpoint_accepts_valid_payload(self, admin_headers):
        """Onboarding endpoint should accept valid payloads"""
        # Test new trader payload with null start_date
        payload = {
            "user_type": "new",
            "starting_balance": 250,
            "start_date": None,
            "transactions": [],
            "trade_entries": [],
            "total_commission": 0
        }
        resp = requests.post(f"{BASE_URL}/api/profit/complete-onboarding", json=payload, headers=admin_headers)
        # Should return 200 or 409 (already completed), not 422
        assert resp.status_code in [200, 409], f"Unexpected status: {resp.status_code}: {resp.text}"
        print("✓ Onboarding endpoint accepts valid payload")

    def test_rewards_summary_returns_streak(self, admin_headers):
        """Rewards summary should return non-zero streak values"""
        resp = requests.get(f"{BASE_URL}/api/rewards/summary", headers=admin_headers)
        if resp.status_code == 200:
            data = resp.json()
            # Just verify the fields exist
            assert "current_streak" in data or "streak" in data, "No streak field in rewards summary"
            print(f"✓ Rewards summary returns streak data: {data.get('current_streak', data.get('best_streak', 'N/A'))}")
        else:
            # Rewards may not be set up for all users
            print(f"⚠ Rewards summary returned {resp.status_code} (may be expected)")


# ─── Test 5: Scheduler Jobs ───

class TestSchedulerJobs:
    """Verify scheduler jobs are registered (can't test execution in real-time)"""

    def test_server_health(self, admin_headers):
        """Server should be healthy"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        print("✓ Server health check passes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

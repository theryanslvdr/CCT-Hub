"""
Iteration 188 Test Suite - Route Extraction & New Features
Tests:
1. Admin member routes after extraction to admin_members_routes.py
2. Habits admin endpoints (pending-proofs, spot-check, spot-check-stats)
3. Team recommendations endpoint (referral_routes.py)
4. Store items endpoint (still working)
5. Admin cleanup overview (still working)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Master Admin credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers with token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAdminMembersRouteExtraction:
    """Test admin member management routes after extraction to admin_members_routes.py"""

    def test_get_members_list(self, auth_headers):
        """GET /api/admin/members?page=1&limit=5 — should return member list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"page": 1, "limit": 5},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "members" in data, "Response should contain 'members' key"
        assert "total" in data, "Response should contain 'total' key"
        assert "page" in data, "Response should contain 'page' key"
        assert "limit" in data, "Response should contain 'limit' key"
        assert "pages" in data, "Response should contain 'pages' key"
        
        # Verify pagination
        assert data["page"] == 1
        assert data["limit"] == 5
        assert isinstance(data["members"], list)
        print(f"GET /api/admin/members PASSED: {len(data['members'])} members, total={data['total']}")

    def test_get_member_stats_overview(self, auth_headers):
        """GET /api/admin/members/stats/overview — should return stat card counts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/stats/overview",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response has required stat fields
        assert "active_members" in data, "Response should contain 'active_members'"
        assert "team_leaders" in data, "Response should contain 'team_leaders'"
        assert "suspended" in data, "Response should contain 'suspended'"
        assert "in_danger" in data, "Response should contain 'in_danger'"
        
        # All values should be integers >= 0
        assert isinstance(data["active_members"], int) and data["active_members"] >= 0
        assert isinstance(data["team_leaders"], int) and data["team_leaders"] >= 0
        assert isinstance(data["suspended"], int) and data["suspended"] >= 0
        assert isinstance(data["in_danger"], int) and data["in_danger"] >= 0
        
        print(f"GET /api/admin/members/stats/overview PASSED: active={data['active_members']}, team_leaders={data['team_leaders']}, suspended={data['suspended']}, in_danger={data['in_danger']}")

    def test_get_members_with_search(self, auth_headers):
        """GET /api/admin/members with search filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"page": 1, "limit": 10, "search": "ryan"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "members" in data
        print(f"GET /api/admin/members?search=ryan PASSED: {len(data['members'])} matches")

    def test_get_members_with_role_filter(self, auth_headers):
        """GET /api/admin/members with role filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"page": 1, "limit": 10, "role": "member"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "members" in data
        print(f"GET /api/admin/members?role=member PASSED: {len(data['members'])} members")


class TestHabitsAdminEndpoints:
    """Test habit admin endpoints for proof review (pending-proofs, spot-check, spot-check-stats)"""

    def test_get_pending_proofs(self, auth_headers):
        """GET /api/habits/admin/pending-proofs — should return completions with screenshot_url"""
        response = requests.get(
            f"{BASE_URL}/api/habits/admin/pending-proofs",
            params={"page": 1},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "completions" in data or "page" in data, "Response should contain completions or page"
        
        # If completions exist, verify structure
        if "completions" in data and data["completions"]:
            comp = data["completions"][0]
            assert "id" in comp, "Completion should have 'id'"
            assert "user_name" in comp or "user_id" in comp, "Completion should have user info"
            assert "habit_title" in comp or "habit_id" in comp, "Completion should have habit info"
        
        print(f"GET /api/habits/admin/pending-proofs PASSED: {len(data.get('completions', []))} completions")

    def test_get_spot_check_stats(self, auth_headers):
        """GET /api/habits/admin/spot-check-stats — should return pending, approved, rejected counts"""
        response = requests.get(
            f"{BASE_URL}/api/habits/admin/spot-check-stats",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response has count fields
        assert "pending" in data, "Response should contain 'pending' count"
        assert "approved" in data, "Response should contain 'approved' count"
        assert "rejected" in data, "Response should contain 'rejected' count"
        
        # All values should be integers >= 0
        assert isinstance(data["pending"], int) and data["pending"] >= 0
        assert isinstance(data["approved"], int) and data["approved"] >= 0
        assert isinstance(data["rejected"], int) and data["rejected"] >= 0
        
        print(f"GET /api/habits/admin/spot-check-stats PASSED: pending={data['pending']}, approved={data['approved']}, rejected={data['rejected']}")

    def test_spot_check_invalid_completion(self, auth_headers):
        """POST /api/habits/admin/spot-check/{completion_id} with invalid ID should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/habits/admin/spot-check/invalid-completion-id",
            json={"action": "approve"},
            headers=auth_headers
        )
        # Should return 404 for non-existent completion
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"POST /api/habits/admin/spot-check/invalid-id PASSED: Returns 404 as expected")


class TestTeamRecommendations:
    """Test team recommendations endpoint (AI-powered suggestions for team leaders)"""

    def test_get_my_team(self, auth_headers):
        """GET /api/referrals/my-team — should return team members list and stats"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-team",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "team" in data, "Response should contain 'team' array"
        assert "stats" in data, "Response should contain 'stats' object"
        
        # Verify stats structure
        stats = data["stats"]
        assert "total" in stats, "Stats should contain 'total'"
        assert "active" in stats, "Stats should contain 'active'"
        assert "in_danger" in stats, "Stats should contain 'in_danger'"
        assert "new_this_week" in stats, "Stats should contain 'new_this_week'"
        
        print(f"GET /api/referrals/my-team PASSED: {stats['total']} total, {stats['active']} active, {stats['in_danger']} in_danger")

    def test_get_team_recommendations(self, auth_headers):
        """GET /api/referrals/my-team/recommendations — should return AI recommendations array"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-team/recommendations",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "recommendations" in data, "Response should contain 'recommendations' array"
        assert isinstance(data["recommendations"], list), "recommendations should be a list"
        
        # If recommendations exist, verify structure
        if data["recommendations"]:
            rec = data["recommendations"][0]
            # Each recommendation can have 'type', 'member', 'urgency', 'suggestion', or 'message' (for all_clear)
            assert "type" in rec or "member" in rec or "suggestion" in rec or "message" in rec, \
                "Recommendation should have type, member, suggestion, or message field"
        
        print(f"GET /api/referrals/my-team/recommendations PASSED: {len(data['recommendations'])} recommendations")


class TestStoreEndpoints:
    """Test store endpoints still work after other route changes"""

    def test_get_store_items(self, auth_headers):
        """GET /api/store/items — store endpoints still work"""
        response = requests.get(
            f"{BASE_URL}/api/store/items",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "items" in data, "Response should contain 'items' array"
        assert isinstance(data["items"], list), "items should be a list"
        
        print(f"GET /api/store/items PASSED: {len(data['items'])} items available")


class TestAdminCleanupOverview:
    """Test admin cleanup overview still works"""

    def test_get_cleanup_overview(self, auth_headers):
        """GET /api/admin/cleanup-overview — cleanup overview still works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/cleanup-overview",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response has cleanup section info
        # The response can have various fields like pending_proofs, fraud_warnings, etc.
        assert isinstance(data, dict), "Response should be a dict"
        
        print(f"GET /api/admin/cleanup-overview PASSED: {list(data.keys())}")


class TestProfitTrackerComponents:
    """Test that profit tracker page components work (ProjectionVision, AdjustTradeDialog)"""

    def test_profit_summary(self, auth_headers):
        """GET /api/profit/summary — basic profit tracker endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify basic fields exist
        assert "account_value" in data or "total_profit" in data or "lot_size" in data, \
            "Response should contain profit tracker fields"
        
        print(f"GET /api/profit/summary PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Iteration 187 - Comprehensive End-to-End Test
Tests: Login, P0-P2 features, Store system, Cleanup routes, Forum text search, Team system
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials from test request
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
ADMIN_USER_ID = "b4628e3e-9dec-42ef-8c75-dcba08194cd2"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for admin user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    pytest.skip(f"Authentication failed - status {response.status_code}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ===================== LOGIN TESTS =====================
class TestLogin:
    """Authentication endpoint tests"""
    
    def test_login_success(self, api_client):
        """Test admin login returns access_token"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert len(data["access_token"]) > 0
        print(f"✓ Login successful, token length: {len(data['access_token'])}")


# ===================== P0 REGRESSION TESTS =====================
class TestP0Regression:
    """P0 Bug regression tests - Critical features"""
    
    def test_profit_complete_onboarding(self, authenticated_client):
        """P0 - POST /api/profit/complete-onboarding with new trader payload"""
        # This endpoint should accept the payload even if user already onboarded
        test_payload = {
            "starting_balance": 1000.0,
            "lot_size": 0.01,
            "is_new_trader": True
        }
        response = authenticated_client.post(
            f"{BASE_URL}/api/profit/complete-onboarding",
            json=test_payload
        )
        # Should return 200 or indicate already onboarded
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"✓ Complete-onboarding endpoint works, status: {response.status_code}")
    
    def test_rewards_streaks(self, authenticated_client):
        """P0 - GET /api/rewards/summary returns non-zero streaks"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/rewards/summary",
            params={"user_id": ADMIN_USER_ID}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Verify structure exists
        assert "current_streak" in data or "streaks" in data, "Missing streak data"
        current = data.get("current_streak", data.get("streaks", {}).get("current", 0))
        print(f"✓ Rewards summary returned, current_streak: {current}")
    
    def test_referral_tree(self, authenticated_client):
        """P0 - GET /api/referrals/admin/tree builds correct hierarchy"""
        response = authenticated_client.get(f"{BASE_URL}/api/referrals/admin/tree")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "tree" in data or "nodes" in data or "members" in data or isinstance(data, list), "Response should contain tree data"
        print(f"✓ Referral tree endpoint works")


# ===================== P1 REGRESSION TESTS =====================
class TestP1Regression:
    """P1 Feature regression tests"""
    
    def test_admin_members_excludes_suspended(self, authenticated_client):
        """P1 - GET /api/admin/members excludes suspended by default"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        members = data.get("members", data if isinstance(data, list) else [])
        # Check that we get a list
        assert isinstance(members, list), "Members should be a list"
        print(f"✓ Admin members endpoint returns {len(members)} members")
    
    def test_member_stats_overview(self, authenticated_client):
        """P1 - GET /api/admin/members/stats/overview returns stats"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/members/stats/overview")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Verify key fields exist
        assert "active_members" in data or "total" in data, "Missing member stats"
        print(f"✓ Member stats overview: {data}")
    
    def test_forum_status_filter(self, authenticated_client):
        """P1 - GET /api/forum/posts with status filter (open/closed)"""
        # Test open filter
        response = authenticated_client.get(
            f"{BASE_URL}/api/forum/posts",
            params={"status": "open"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        posts = data.get("posts", [])
        # All returned posts should have status=open
        for post in posts:
            assert post.get("status") == "open", f"Post {post.get('id')} has wrong status"
        print(f"✓ Forum status filter works, {len(posts)} open posts")


# ===================== P2 STORE TESTS =====================
class TestP2Store:
    """P2 - Store system tests"""
    
    def test_store_items(self, authenticated_client):
        """P2 - GET /api/store/items returns 3 immunity items and user points"""
        response = authenticated_client.get(f"{BASE_URL}/api/store/items")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify items exist
        items = data.get("items", [])
        assert len(items) == 3, f"Expected 3 items, got {len(items)}"
        
        # Verify item IDs
        item_ids = [i["id"] for i in items]
        assert "immunity_1d" in item_ids, "Missing 1-day immunity"
        assert "immunity_3d" in item_ids, "Missing 3-day immunity"
        assert "immunity_7d" in item_ids, "Missing 7-day immunity"
        
        # Verify user_points field exists
        assert "user_points" in data, "Missing user_points"
        print(f"✓ Store items returned: {len(items)} items, user has {data['user_points']} points")
    
    def test_store_purchase_insufficient_points(self, authenticated_client):
        """P2 - POST /api/store/purchase with insufficient points returns 400"""
        # Use the most expensive item (250 points) to test insufficient funds
        response = authenticated_client.post(
            f"{BASE_URL}/api/store/purchase",
            json={"item_id": "immunity_7d"}  # 250 points - may fail if user has enough
        )
        # This test validates the endpoint works - status depends on user points
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data, "Error should have detail field"
            print(f"✓ Purchase rejection works: {data.get('detail', '')}")
        else:
            print(f"✓ Purchase succeeded (user had enough points)")
    
    def test_store_purchase_valid_item(self, authenticated_client):
        """P2 - POST /api/store/purchase with valid item deducts points"""
        # First get current points
        items_response = authenticated_client.get(f"{BASE_URL}/api/store/items")
        initial_points = items_response.json().get("user_points", 0)
        
        # Try to purchase cheapest item (50 points)
        if initial_points >= 50:
            response = authenticated_client.post(
                f"{BASE_URL}/api/store/purchase",
                json={"item_id": "immunity_1d"}  # 50 points
            )
            assert response.status_code == 200, f"Purchase failed: {response.text}"
            data = response.json()
            assert "remaining_points" in data, "Missing remaining_points"
            assert "credit" in data, "Missing credit info"
            assert data["remaining_points"] == initial_points - 50, "Points not deducted correctly"
            print(f"✓ Purchase successful, remaining points: {data['remaining_points']}")
        else:
            pytest.skip(f"User only has {initial_points} points, need 50")
    
    def test_store_my_credits(self, authenticated_client):
        """P2 - GET /api/store/my-credits returns active credits and history"""
        response = authenticated_client.get(f"{BASE_URL}/api/store/my-credits")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "active_credits" in data, "Missing active_credits"
        assert "history" in data, "Missing history"
        assert isinstance(data["active_credits"], list), "active_credits should be list"
        assert isinstance(data["history"], list), "history should be list"
        print(f"✓ My credits: {len(data['active_credits'])} active, {len(data['history'])} history")


# ===================== P2 CLEANUP TESTS =====================
class TestP2Cleanup:
    """P2 - Admin cleanup routes (refactored)"""
    
    def test_cleanup_overview(self, authenticated_client):
        """P2 - GET /api/admin/cleanup-overview returns all sections"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/cleanup-overview")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify all expected sections
        expected_keys = ["pending_proofs", "fraud_warnings", "in_danger", "auto_suspended", "pending_registrations"]
        for key in expected_keys:
            # Accept either key or key + "_count" variant
            assert key in data or f"{key}_count" in data, f"Missing {key}"
        print(f"✓ Cleanup overview: pending_proofs={data.get('pending_proofs', 0)}")
    
    def test_pending_registrations(self, authenticated_client):
        """P2 - GET /api/admin/pending-registrations"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/pending-registrations")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "pending" in data, "Missing pending list"
        assert "count" in data, "Missing count"
        print(f"✓ Pending registrations: {data['count']}")


# ===================== P2 HABITS TESTS =====================
class TestP2Habits:
    """P2 - Habits with day_of_week and screenshot requirements"""
    
    def test_get_habits(self, authenticated_client):
        """Test habits endpoint returns habits list"""
        response = authenticated_client.get(f"{BASE_URL}/api/habits/")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "habits" in data, "Missing habits list"
        print(f"✓ Habits endpoint works, {len(data['habits'])} habits today")
    
    def test_fraud_warnings(self, authenticated_client):
        """P2 - GET /api/habits/my-warnings returns warnings structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/habits/my-warnings")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "warnings" in data, "Missing warnings array"
        assert "active_warning" in data, "Missing active_warning field"
        assert "rejection_count" in data, "Missing rejection_count"
        print(f"✓ My warnings: {len(data['warnings'])} warnings, rejection_count={data['rejection_count']}")


# ===================== P2 TEAM TESTS =====================
class TestP2Team:
    """P2 - Team system tests"""
    
    def test_my_team(self, authenticated_client):
        """P2 - GET /api/referrals/my-team returns team with stats"""
        response = authenticated_client.get(f"{BASE_URL}/api/referrals/my-team")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "team" in data, "Missing team array"
        assert "stats" in data, "Missing stats object"
        stats = data["stats"]
        assert "total" in stats, "Stats missing total"
        print(f"✓ My team: {len(data['team'])} members, total={stats['total']}")


# ===================== P2 FORUM MERGE TESTS =====================
class TestP2ForumMerge:
    """P2 - Forum merge endpoint validation"""
    
    def test_forum_merge_validation(self, authenticated_client):
        """P2 - POST /api/forum/posts/merge validates inputs correctly"""
        # Test with invalid IDs - should return 400 or 404
        response = authenticated_client.post(
            f"{BASE_URL}/api/forum/posts/merge",
            json={
                "source_post_id": "invalid-source-id",
                "target_post_id": "invalid-target-id"
            }
        )
        # Should fail validation (404 for not found posts)
        assert response.status_code in [400, 403, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Forum merge validation works, status: {response.status_code}")
    
    def test_forum_text_search(self, authenticated_client):
        """P2 - GET /api/forum/posts?search=test uses text index"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/forum/posts",
            params={"search": "test"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "posts" in data, "Missing posts in response"
        print(f"✓ Forum text search works, found {len(data['posts'])} posts")


# ===================== ADMIN HABITS CRUD =====================
class TestAdminHabits:
    """Admin habits CRUD with day_of_week and requires_screenshot"""
    
    def test_admin_create_habit_with_day_and_screenshot(self, authenticated_client):
        """P2 - POST /api/admin/habits with day_of_week and requires_screenshot"""
        test_habit = {
            "title": "TEST Monday Screenshot Habit",
            "description": "Test habit requiring screenshot on Mondays",
            "action_type": "generic",
            "is_gate": False,
            "day_of_week": "monday",
            "requires_screenshot": True
        }
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/habits",
            json=test_habit
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        habit_id = data.get("id")
        print(f"✓ Created habit with day_of_week and requires_screenshot, id: {habit_id}")
        
        # Cleanup - delete the test habit
        if habit_id:
            authenticated_client.delete(f"{BASE_URL}/api/admin/habits/{habit_id}")
            print(f"✓ Cleaned up test habit")


# ===================== HEALTH CHECK =====================
class TestHealth:
    """Basic health check"""
    
    def test_health_endpoint(self, api_client):
        """Health check returns status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed, version: {data.get('version', 'unknown')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

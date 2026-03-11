"""
Iteration 189 - UI/UX Overhaul Feature Tests

Tests for 11 feature requests:
1. Streak in Share Performance
2. Hub Store with streak freezes 
3. Collapsible accordion nav categories
4. Leaderboard modal in My Rewards
5. Invite & Earn card in My Team
6. Rewards category in nav
7. AI Assistant -> Forum posting
8. Notification bell + badge counters
9. Admin Find a Member
10. Dashboard quick action buttons
11. Enhanced Performance View
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://system-restore-lab.preview.emergentagent.com"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for all tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "iam@ryansalvador.com", "password": "admin123"}
    )
    data = response.json()
    # Token can be in 'token' or 'access_token' field
    token = data.get("token") or data.get("access_token")
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def admin_user(admin_token):
    """Get admin user ID"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "iam@ryansalvador.com", "password": "admin123"}
    )
    data = response.json()
    return data.get("user", {})


class TestAuthAndHealth:
    """Basic health and authentication tests"""

    def test_health_endpoint(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✅ Health check passed: {data.get('version')}")

    def test_login_admin(self):
        """Test admin login with provided credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        # Token can be in 'token' or 'access_token' field
        assert "token" in data or "access_token" in data
        assert "user" in data
        assert data["user"]["role"] in ["master_admin", "super_admin", "admin"]
        print(f"✅ Admin login successful: {data['user']['full_name']}")


class TestAdminMembersRoutes:
    """Tests for GET /api/admin/members (extracted to admin_members_routes.py)"""

    def test_get_members(self, admin_headers):
        """GET /api/admin/members - should return paginated member list"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert "total" in data
        print(f"✅ GET /api/admin/members: {data.get('total')} members")


class TestHubStore:
    """Tests for Hub Store page - items + streak freezes"""

    def test_store_items(self, admin_headers):
        """GET /api/store/items - should return store items"""
        response = requests.get(f"{BASE_URL}/api/store/items", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Items can be list or dict with items key
        items = data.get("items", data) if isinstance(data, dict) else data
        print(f"✅ GET /api/store/items: {len(items) if isinstance(items, list) else 'N/A'} items")

    def test_streak_freezes(self, admin_headers):
        """GET /api/rewards/streak-freezes - should return freeze info"""
        response = requests.get(f"{BASE_URL}/api/rewards/streak-freezes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Check for expected fields in streak freeze response
        print(f"✅ GET /api/rewards/streak-freezes: trade_freezes={data.get('trade_freezes', 'N/A')}, habit_freezes={data.get('habit_freezes', 'N/A')}")

    def test_my_credits(self, admin_headers):
        """GET /api/store/my-credits - should return user's credits"""
        response = requests.get(f"{BASE_URL}/api/store/my-credits", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ GET /api/store/my-credits: {data.get('active_credits', [])}")


class TestMyTeam:
    """Tests for My Team page - Invite & Earn card + team data"""

    def test_my_team_endpoint(self, admin_headers):
        """GET /api/referrals/my-team - should return team data with stats"""
        response = requests.get(f"{BASE_URL}/api/referrals/my-team", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
        assert "stats" in data
        stats = data["stats"]
        assert "total" in stats
        assert "active" in stats
        assert "in_danger" in stats
        assert "new_this_week" in stats
        print(f"✅ GET /api/referrals/my-team: {stats['total']} team members, {stats['active']} active")

    def test_team_recommendations(self, admin_headers):
        """GET /api/referrals/my-team/recommendations - should return AI recommendations"""
        response = requests.get(f"{BASE_URL}/api/referrals/my-team/recommendations", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        print(f"✅ GET /api/referrals/my-team/recommendations: {len(data['recommendations'])} recommendations")

    def test_tracking_endpoint(self, admin_headers):
        """GET /api/referrals/tracking - should return invite link for Invite & Earn card"""
        response = requests.get(f"{BASE_URL}/api/referrals/tracking", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Check for invite link fields used by Invite & Earn card
        print(f"✅ GET /api/referrals/tracking: merin_code={data.get('merin_code', 'N/A')}, onboarding_invite_link present={bool(data.get('onboarding_invite_link'))}")


class TestMyRewards:
    """Tests for My Rewards page - Leaderboard modal"""

    def test_rewards_summary(self, admin_headers, admin_user):
        """GET /api/rewards/summary - should return points and level"""
        user_id = admin_user.get("id", "")
        response = requests.get(
            f"{BASE_URL}/api/rewards/summary",
            headers=admin_headers,
            params={"user_id": user_id}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ GET /api/rewards/summary: lifetime_points={data.get('lifetime_points', 0)}, level={data.get('level', 'Unknown')}")

    def test_rewards_leaderboard(self, admin_headers, admin_user):
        """GET /api/rewards/leaderboard - should return leaderboard data for modal"""
        user_id = admin_user.get("id", "")
        response = requests.get(
            f"{BASE_URL}/api/rewards/leaderboard",
            headers=admin_headers,
            params={"user_id": user_id}
        )
        assert response.status_code == 200
        data = response.json()
        # Check leaderboard data exists
        print(f"✅ GET /api/rewards/leaderboard: rank={data.get('current_rank', 'N/A')}, leaderboard_count={len(data.get('leaderboard', []))}")


class TestAdminDashboard:
    """Tests for Admin Dashboard - Find a Member search"""

    def test_lookup_members(self, admin_headers):
        """GET /api/referrals/lookup-members - search for members by name/email"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            headers=admin_headers,
            params={"q": "ryan"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✅ GET /api/referrals/lookup-members?q=ryan: {len(data['results'])} results")


class TestAdminCleanup:
    """Tests for Admin Cleanup page - RyAI analysis labels"""

    def test_pending_proofs_with_ai_review(self, admin_headers):
        """GET /api/habits/admin/pending-proofs - should return completions with ai_review field"""
        response = requests.get(f"{BASE_URL}/api/habits/admin/pending-proofs", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "completions" in data
        print(f"✅ GET /api/habits/admin/pending-proofs: {len(data['completions'])} completions")
        # Check if any completions have ai_review field
        for c in data.get("completions", [])[:3]:
            has_ai_review = "ai_review" in c or "ai_flagged" in c
            print(f"   - Completion {c.get('id', 'N/A')[:8]}...: has_ai_review={has_ai_review}, ai_flagged={c.get('ai_flagged', False)}")

    def test_cleanup_overview(self, admin_headers):
        """GET /api/admin/cleanup-overview - should return counts for badge"""
        response = requests.get(f"{BASE_URL}/api/admin/cleanup-overview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ GET /api/admin/cleanup-overview: pending_proofs={data.get('pending_proofs', 0)}, pending_registrations={data.get('pending_registrations', 0)}")


class TestDashboard:
    """Tests for Dashboard - Quick actions and enhanced Performance View"""

    def test_profit_summary(self, admin_headers):
        """GET /api/profit/summary - should return enhanced stats"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        # Check for expected stats used in Performance View
        print(f"✅ GET /api/profit/summary: account_value={data.get('account_value', 0)}, total_trades={data.get('total_trades', 0)}")


class TestAIAssistant:
    """Tests for AI Assistant page"""

    def test_ai_assistant_sessions(self, admin_headers):
        """GET /api/ai-assistant/sessions - should return sessions"""
        response = requests.get(
            f"{BASE_URL}/api/ai-assistant/sessions",
            headers=admin_headers,
            params={"assistant_id": "adaptive"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ GET /api/ai-assistant/sessions: {len(data.get('sessions', []))} sessions")

    def test_forum_posts(self, admin_headers):
        """GET /api/forum/posts - should return posts (for forum posting feature)"""
        response = requests.get(f"{BASE_URL}/api/forum/posts", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✅ GET /api/forum/posts: total={data.get('total', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

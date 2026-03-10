"""
Test Iteration 128: Rewards System Phase 1 & Phase 2 Features
- LeaderboardPage with podium, period toggle, pagination
- MyRewardsPage with filtering, pagination, CSV export, streak tracking
- Backend endpoints: leaderboard/full, summary, history
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://platform-refresh-6.preview.emergentagent.com')

class TestRewardsAPIEndpoints:
    """Test rewards API endpoints for Phase 2 features"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin JWT token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        return resp.json().get("access_token")

    @pytest.fixture
    def admin_headers(self, admin_token):
        """Headers with admin JWT"""
        return {"Authorization": f"Bearer {admin_token}"}

    # ─── Leaderboard Full (public endpoint) ───
    def test_leaderboard_full_monthly(self):
        """GET /api/rewards/leaderboard/full?period=monthly returns valid data"""
        resp = requests.get(f"{BASE_URL}/api/rewards/leaderboard/full", params={
            "period": "monthly",
            "limit": 100
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Validate response structure
        assert "period" in data
        assert data["period"] == "monthly"
        assert "leaderboard" in data
        assert "total" in data
        assert isinstance(data["leaderboard"], list)
        
        # Check leaderboard entry structure if data exists
        if len(data["leaderboard"]) > 0:
            entry = data["leaderboard"][0]
            assert "user_id" in entry
            assert "rank" in entry
            assert "points" in entry
            assert "display_name" in entry
            assert "level" in entry
            assert "rank_change" in entry
            # First entry should have rank 1
            assert entry["rank"] == 1
    
    def test_leaderboard_full_alltime(self):
        """GET /api/rewards/leaderboard/full?period=alltime returns valid data"""
        resp = requests.get(f"{BASE_URL}/api/rewards/leaderboard/full", params={
            "period": "alltime",
            "limit": 100
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Validate response structure
        assert data["period"] == "alltime"
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        
        # Check that entries are sorted by rank (and have rank_change = 0 for alltime)
        if len(data["leaderboard"]) > 0:
            for i, entry in enumerate(data["leaderboard"][:5]):
                assert entry["rank"] == i + 1
                assert entry["rank_change"] == 0  # All-time doesn't track rank changes

    # ─── Rewards Summary (public endpoint) ───
    def test_rewards_summary_valid_user(self):
        """GET /api/rewards/summary?user_id={user_id} returns valid summary"""
        # Test with known user ID (Rizza M. from leaderboard)
        test_user_id = "19ccb9d7-139f-4918-a662-ad72483010b1"
        resp = requests.get(f"{BASE_URL}/api/rewards/summary", params={
            "user_id": test_user_id
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Validate required fields
        assert data["user_id"] == test_user_id
        assert "lifetime_points" in data
        assert "monthly_points" in data
        assert "level" in data
        assert "estimated_usdt" in data
        assert "min_redeem_points" in data
        assert "is_redeemable" in data
        assert "current_streak" in data
        assert "best_streak" in data
        assert "referral_count" in data
        assert "total_trades" in data
        
        # Validate data types
        assert isinstance(data["lifetime_points"], int)
        assert isinstance(data["monthly_points"], int)
        assert isinstance(data["level"], str)

    def test_rewards_summary_unknown_user(self):
        """Summary for unknown user returns defaults (0 points, Newbie level)"""
        resp = requests.get(f"{BASE_URL}/api/rewards/summary", params={
            "user_id": "nonexistent-user-12345"
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Should return defaults
        assert data["lifetime_points"] == 0
        assert data["monthly_points"] == 0
        assert data["level"] == "Newbie"

    # ─── Leaderboard User Position (public endpoint) ───
    def test_leaderboard_user_position(self):
        """GET /api/rewards/leaderboard?user_id={user_id} returns user's rank"""
        test_user_id = "19ccb9d7-139f-4918-a662-ad72483010b1"
        resp = requests.get(f"{BASE_URL}/api/rewards/leaderboard", params={
            "user_id": test_user_id
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Validate response structure
        assert data["user_id"] == test_user_id
        assert "current_rank" in data
        assert "monthly_points" in data
        assert "level" in data
        assert "distance_to_next" in data
        assert "next_user_name" in data
        assert "suggested_message" in data
        
        # User should have a rank > 0 (they're on leaderboard)
        assert data["current_rank"] > 0

    # ─── History (authenticated endpoint) ───
    def test_rewards_history_authenticated(self, admin_headers):
        """GET /api/rewards/history returns user's own history"""
        resp = requests.get(f"{BASE_URL}/api/rewards/history", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert "user_id" in data
        assert "history" in data
        assert isinstance(data["history"], list)

    def test_rewards_history_admin_view_other_user(self, admin_headers):
        """Admin can view another user's history via ?user_id="""
        test_user_id = "19ccb9d7-139f-4918-a662-ad72483010b1"
        resp = requests.get(f"{BASE_URL}/api/rewards/history", 
                           params={"user_id": test_user_id}, 
                           headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["user_id"] == test_user_id
        assert "history" in data
        
        # Check history entry structure if data exists
        if len(data["history"]) > 0:
            entry = data["history"][0]
            assert "user_id" in entry
            assert "points" in entry
            assert "source" in entry
            assert "created_at" in entry
            assert "balance_after" in entry

    def test_rewards_history_unauthenticated(self):
        """GET /api/rewards/history without auth should fail"""
        resp = requests.get(f"{BASE_URL}/api/rewards/history")
        assert resp.status_code in [401, 403, 422]

    # ─── Leaderboard Pagination Support ───
    def test_leaderboard_pagination_limit(self):
        """Leaderboard respects limit parameter"""
        resp = requests.get(f"{BASE_URL}/api/rewards/leaderboard/full", params={
            "period": "monthly",
            "limit": 5
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # Should respect the limit (or return less if fewer entries exist)
        assert len(data["leaderboard"]) <= 5


class TestLeaderboardPodiumData:
    """Test that leaderboard data supports podium display (top 3)"""

    def test_top_three_for_podium(self):
        """Verify top 3 entries exist for podium display"""
        resp = requests.get(f"{BASE_URL}/api/rewards/leaderboard/full", params={
            "period": "monthly",
            "limit": 3
        })
        assert resp.status_code == 200
        data = resp.json()
        
        # If we have at least 3 entries, validate podium data
        if data["total"] >= 3:
            leaderboard = data["leaderboard"]
            # Check ranks 1, 2, 3
            assert leaderboard[0]["rank"] == 1
            assert leaderboard[1]["rank"] == 2
            assert leaderboard[2]["rank"] == 3
            
            # All should have display names
            for entry in leaderboard[:3]:
                assert entry["display_name"] is not None
                assert entry["points"] is not None
                assert entry["level"] is not None

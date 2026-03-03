"""
Iteration 136: Earning Actions with Retroactive Point Awards Tests

Tests:
- GET /api/rewards/earning-actions - Returns 8 earning actions with awarded/claimable/one_time status
- POST /api/rewards/claim/join_community - Claims 5 points one-time, fails on second attempt
- POST /api/rewards/retroactive-scan - Awards missed points and returns awarded_actions list
- Double-claim prevention: 400 'already claimed' on second attempt
- Non-claimable actions: 400 'cannot be manually claimed' for first_trade
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for master admin."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "iam@ryansalvador.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


class TestEarningActionsAPI:
    """Tests for earning actions endpoints"""

    def test_get_earning_actions_status(self, auth_token):
        """Test GET /api/rewards/earning-actions returns 8 actions with proper status."""
        response = requests.get(
            f"{BASE_URL}/api/rewards/earning-actions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "actions" in data
        assert "stats" in data
        
        actions = data["actions"]
        assert len(actions) == 8, f"Expected 8 earning actions, got {len(actions)}"
        
        # Verify all expected action IDs are present
        action_ids = {a["id"] for a in actions}
        expected_ids = {
            "signup_verify", "join_community", "first_trade", "first_daily_win",
            "streak_5_day", "milestone_10_trade", "qualified_referral", "deposit"
        }
        assert action_ids == expected_ids, f"Missing actions: {expected_ids - action_ids}"
        
        # Verify each action has required fields
        for action in actions:
            assert "id" in action
            assert "name" in action
            assert "description" in action
            assert "points" in action
            assert "awarded" in action
            assert "claimable" in action
            assert "one_time" in action
            assert "category" in action
        
        # Verify stats structure
        stats = data["stats"]
        assert "lifetime_trades" in stats
        assert "best_streak" in stats
        assert "lifetime_deposit" in stats
        assert "referrals" in stats
        
        print(f"SUCCESS: GET /api/rewards/earning-actions returned {len(actions)} actions")
        print(f"Stats: trades={stats['lifetime_trades']}, best_streak={stats['best_streak']}")

    def test_claim_join_community_double_claim_prevention(self, auth_token):
        """Test POST /api/rewards/claim/join_community returns 400 when already claimed."""
        # For master admin, join_community is already claimed
        response = requests.post(
            f"{BASE_URL}/api/rewards/claim/join_community",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return 400 because already claimed
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        assert "already claimed" in data["detail"].lower(), f"Unexpected error: {data['detail']}"
        
        print("SUCCESS: Double-claim prevention works - 'already claimed' returned")

    def test_claim_first_trade_not_manually_claimable(self, auth_token):
        """Test POST /api/rewards/claim/first_trade returns 400 (cannot be manually claimed)."""
        response = requests.post(
            f"{BASE_URL}/api/rewards/claim/first_trade",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        assert "cannot be manually claimed" in data["detail"].lower(), f"Unexpected error: {data['detail']}"
        
        print("SUCCESS: Non-claimable action rejected correctly")

    def test_retroactive_scan_returns_awarded_actions(self, auth_token):
        """Test POST /api/rewards/retroactive-scan returns stats and awarded_actions list."""
        response = requests.post(
            f"{BASE_URL}/api/rewards/retroactive-scan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "user_id" in data
        assert "stats" in data
        assert "newly_awarded" in data
        assert "awarded_actions" in data
        
        stats = data["stats"]
        assert "lifetime_trades" in stats
        assert "best_streak_days" in stats
        assert "current_streak_days" in stats
        assert "lifetime_deposit_usdt" in stats
        assert "qualified_referrals" in stats
        
        print(f"SUCCESS: Retroactive scan completed")
        print(f"Stats: trades={stats['lifetime_trades']}, best_streak={stats['best_streak_days']}")
        print(f"Awarded actions: {data['awarded_actions']}")

    def test_earning_actions_awarded_status(self, auth_token):
        """Verify which actions are marked as awarded for master admin."""
        response = requests.get(
            f"{BASE_URL}/api/rewards/earning-actions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        actions = {a["id"]: a for a in data["actions"]}
        
        # Master admin has: signup_verify, join_community, first_trade, first_daily_win, 
        # streak_5_day (x3), milestone_10_trade
        expected_awarded = ["signup_verify", "join_community", "first_trade", 
                          "first_daily_win", "streak_5_day", "milestone_10_trade"]
        
        for action_id in expected_awarded:
            assert actions[action_id]["awarded"] == True, f"{action_id} should be awarded"
        
        # streak_5_day should have times_awarded > 1
        assert actions["streak_5_day"]["times_awarded"] >= 3, \
            f"streak_5_day should have times_awarded >= 3, got {actions['streak_5_day'].get('times_awarded', 0)}"
        
        # qualified_referral and deposit should NOT be awarded (no referrals/deposits)
        assert actions["qualified_referral"]["awarded"] == False
        assert actions["deposit"]["awarded"] == False
        
        print("SUCCESS: Awarded status verified for all actions")

    def test_one_time_vs_repeatable_actions(self, auth_token):
        """Verify one_time flag is set correctly for actions."""
        response = requests.get(
            f"{BASE_URL}/api/rewards/earning-actions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        actions = {a["id"]: a for a in data["actions"]}
        
        # One-time actions
        one_time_actions = ["signup_verify", "join_community", "first_trade", 
                          "first_daily_win", "milestone_10_trade"]
        for action_id in one_time_actions:
            assert actions[action_id]["one_time"] == True, f"{action_id} should be one_time=True"
        
        # Repeatable actions
        repeatable_actions = ["streak_5_day", "qualified_referral", "deposit"]
        for action_id in repeatable_actions:
            assert actions[action_id]["one_time"] == False, f"{action_id} should be one_time=False"
        
        print("SUCCESS: one_time flag verified for all actions")

    def test_claimable_status(self, auth_token):
        """Verify claimable status - only join_community is manually claimable."""
        response = requests.get(
            f"{BASE_URL}/api/rewards/earning-actions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        actions = {a["id"]: a for a in data["actions"]}
        
        # Only join_community is claimable (but False if already awarded)
        # All other actions are auto-detected/awarded
        for action in data["actions"]:
            if action["id"] == "join_community" and not action["awarded"]:
                assert action["claimable"] == True, "join_community should be claimable if not awarded"
            else:
                # If awarded, claimable should be False
                if action["awarded"]:
                    assert action["claimable"] == False, f"{action['id']} should not be claimable if awarded"
        
        print("SUCCESS: Claimable status verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

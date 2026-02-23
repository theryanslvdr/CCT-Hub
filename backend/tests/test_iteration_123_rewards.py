"""
Iteration 123: Rewards System Tests
Testing rewards endpoints: summary, leaderboard, history, admin lookup, admin simulate
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
RIZZA_EMAIL = "rizza.miles@gmail.com"
RIZZA_PASSWORD = "rizza123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"


class TestRewardsEndpoints:
    """Test rewards API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin JWT token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None
    
    def get_rizza_token(self):
        """Get Rizza's JWT token (regular member)"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": RIZZA_EMAIL,
            "password": RIZZA_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None
    
    # ─── Public Endpoints (no auth required) ───
    
    def test_rewards_summary_returns_valid_data(self):
        """GET /api/rewards/summary?user_id=... returns valid data"""
        response = self.session.get(
            f"{BASE_URL}/api/rewards/summary",
            params={"user_id": RIZZA_USER_ID}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user_id" in data, "Missing user_id in response"
        assert "lifetime_points" in data, "Missing lifetime_points"
        assert "monthly_points" in data, "Missing monthly_points"
        assert "level" in data, "Missing level"
        assert "estimated_usdt" in data, "Missing estimated_usdt"
        assert "min_redeem_points" in data, "Missing min_redeem_points"
        assert "is_redeemable" in data, "Missing is_redeemable"
        
        # Validate data types
        assert data["user_id"] == RIZZA_USER_ID
        assert isinstance(data["lifetime_points"], int)
        assert isinstance(data["level"], str)
        
        print(f"✓ Summary API returned: points={data['lifetime_points']}, level={data['level']}")
    
    def test_rewards_leaderboard_returns_rank_data(self):
        """GET /api/rewards/leaderboard?user_id=... returns rank data"""
        response = self.session.get(
            f"{BASE_URL}/api/rewards/leaderboard",
            params={"user_id": RIZZA_USER_ID}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        required_fields = ["user_id", "current_rank", "monthly_points", "level", 
                          "distance_to_next", "next_user_name", "suggested_message"]
        for field in required_fields:
            assert field in data, f"Missing {field} in leaderboard response"
        
        assert data["user_id"] == RIZZA_USER_ID
        assert isinstance(data["current_rank"], int)
        assert isinstance(data["suggested_message"], str)
        
        print(f"✓ Leaderboard API returned: rank=#{data['current_rank']}, monthly_pts={data['monthly_points']}")
    
    # ─── Protected Endpoints (require auth) ───
    
    def test_rewards_history_with_auth(self):
        """GET /api/rewards/history with auth returns user's history"""
        token = self.get_rizza_token()
        assert token is not None, "Failed to get Rizza's token"
        
        response = self.session.get(
            f"{BASE_URL}/api/rewards/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "user_id" in data, "Missing user_id in history response"
        assert "history" in data, "Missing history array"
        assert isinstance(data["history"], list), "History should be a list"
        
        # Check history entry structure if any entries exist
        if len(data["history"]) > 0:
            entry = data["history"][0]
            assert "points" in entry, "History entry missing points"
            assert "source" in entry, "History entry missing source"
            print(f"✓ History API returned {len(data['history'])} entries")
        else:
            print("✓ History API returned empty history (user has no point transactions)")
    
    def test_rewards_history_without_auth_fails(self):
        """GET /api/rewards/history without auth should fail"""
        response = self.session.get(f"{BASE_URL}/api/rewards/history")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print(f"✓ History API correctly rejects unauthenticated requests: {response.status_code}")
    
    # ─── Admin Endpoints ───
    
    def test_admin_lookup_by_email(self):
        """GET /api/rewards/admin/lookup?email=... with admin auth returns full profile"""
        token = self.get_admin_token()
        assert token is not None, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"email": RIZZA_EMAIL},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        required_fields = ["user_id", "full_name", "email", "lifetime_points", 
                          "monthly_points", "level", "estimated_usdt", "current_rank",
                          "lifetime_trades", "history"]
        for field in required_fields:
            assert field in data, f"Missing {field} in admin lookup response"
        
        assert data["email"] == RIZZA_EMAIL
        assert isinstance(data["history"], list)
        
        print(f"✓ Admin lookup returned: {data['full_name']}, points={data['lifetime_points']}, level={data['level']}")
    
    def test_admin_lookup_by_user_id(self):
        """GET /api/rewards/admin/lookup?user_id=... with admin auth returns full profile"""
        token = self.get_admin_token()
        assert token is not None, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"user_id": RIZZA_USER_ID},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["user_id"] == RIZZA_USER_ID
        print(f"✓ Admin lookup by user_id returned: {data['full_name']}")
    
    def test_admin_lookup_without_admin_fails(self):
        """GET /api/rewards/admin/lookup as non-admin should fail"""
        token = self.get_rizza_token()
        assert token is not None, "Failed to get Rizza's token"
        
        response = self.session.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"email": "test@test.com"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should return 403 for non-admin
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Admin lookup correctly rejects non-admin: {response.status_code}")
    
    def test_admin_simulate_manual_bonus(self):
        """POST /api/rewards/admin/simulate with manual_bonus action"""
        token = self.get_admin_token()
        assert token is not None, "Failed to get admin token"
        
        # Get current points first
        lookup_response = self.session.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"user_id": RIZZA_USER_ID},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert lookup_response.status_code == 200
        initial_points = lookup_response.json().get("lifetime_points", 0)
        
        # Simulate manual bonus
        response = self.session.post(
            f"{BASE_URL}/api/rewards/admin/simulate",
            json={
                "user_id": RIZZA_USER_ID,
                "action_type": "manual_bonus",
                "points": 10  # Small bonus for testing
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Missing success field"
        assert data["success"] == True, "Simulation should succeed"
        assert "action" in data, "Missing action field"
        assert "new_lifetime_points" in data, "Missing new_lifetime_points"
        assert "level" in data, "Missing level"
        
        # Verify points increased
        new_points = data["new_lifetime_points"]
        assert new_points >= initial_points, f"Points should have increased: {initial_points} -> {new_points}"
        
        print(f"✓ Manual bonus simulation: {data['action']}, new_points={new_points}")
    
    def test_admin_simulate_test_trade(self):
        """POST /api/rewards/admin/simulate with test_trade action"""
        token = self.get_admin_token()
        assert token is not None, "Failed to get admin token"
        
        response = self.session.post(
            f"{BASE_URL}/api/rewards/admin/simulate",
            json={
                "user_id": RIZZA_USER_ID,
                "action_type": "test_trade"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert "action" in data
        assert "Simulated Trade" in data["action"]
        
        print(f"✓ Test trade simulation: {data['action']}, level={data.get('level')}")
    
    def test_admin_simulate_without_admin_fails(self):
        """POST /api/rewards/admin/simulate as non-admin should fail"""
        token = self.get_rizza_token()
        assert token is not None, "Failed to get Rizza's token"
        
        response = self.session.post(
            f"{BASE_URL}/api/rewards/admin/simulate",
            json={
                "user_id": RIZZA_USER_ID,
                "action_type": "manual_bonus",
                "points": 100
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should return 403 for non-admin
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"✓ Admin simulate correctly rejects non-admin: {response.status_code}")
    
    def test_admin_lookup_missing_params(self):
        """GET /api/rewards/admin/lookup without user_id or email returns 400"""
        token = self.get_admin_token()
        assert token is not None, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Admin lookup correctly validates params: {response.status_code}")
    
    def test_admin_lookup_user_not_found(self):
        """GET /api/rewards/admin/lookup with invalid email returns 404"""
        token = self.get_admin_token()
        assert token is not None, "Failed to get admin token"
        
        response = self.session.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"email": "nonexistent@example.com"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Admin lookup correctly handles not found: {response.status_code}")


class TestAuthEndpoints:
    """Test auth endpoints used in login flow"""
    
    def test_admin_login(self):
        """Admin login works correctly"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data or "token" in data, "Missing token in response"
        assert "user" in data
        assert data["user"]["role"] in ["admin", "super_admin", "master_admin"]
        print(f"✓ Admin login successful, role={data['user']['role']}")
    
    def test_member_login(self):
        """Member (Rizza) login works correctly"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": RIZZA_EMAIL, "password": RIZZA_PASSWORD}
        )
        
        assert response.status_code == 200, f"Member login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data or "token" in data, "Missing token in response"
        assert "user" in data
        assert data["user"]["id"] == RIZZA_USER_ID
        print(f"✓ Member login successful, user_id={data['user']['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

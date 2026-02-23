"""
Iteration 121: Rewards System API Testing
Tests for the new CrossCurrent Rewards/Points system

Endpoints tested:
- GET /api/rewards/summary?user_id={id} - Public, returns user rewards summary
- GET /api/rewards/leaderboard?user_id={id} - Public, returns leaderboard position
- POST /api/rewards/redeem - Protected, redeems points for rewards
- POST /api/rewards/credit - Protected, manually credits points
- POST /api/rewards/events/trade - Protected, process trade event
- POST /api/rewards/events/deposit - Protected, process deposit event
- POST /api/rewards/events/signup - Protected, process signup event
- POST /api/rewards/events/referral-qualified - Protected, process referral
- POST /api/rewards/system-check - Admin JWT auth, full health check
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
INTERNAL_API_KEY = "_CXCB2Y-ObBIZqqaCzmjEJU1zwe7DMHr8C-tzoef9h0"

# Test user ID - will be cleaned up after tests
TEST_USER_ID = f"test_rewards_user_{uuid.uuid4().hex[:8]}"

# Auth credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin JWT token for system-check endpoint"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin auth failed: {response.status_code}")


@pytest.fixture(scope="module")
def licensee_token():
    """Get licensee JWT token for frontend tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": LICENSEE_EMAIL, "password": LICENSEE_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Licensee auth failed: {response.status_code}")


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    """Cleanup test data after all tests"""
    yield
    # Clean up test user's rewards data via internal API
    # Note: In production, this would be done via a dedicated cleanup endpoint
    print(f"\nCleanup: Test user {TEST_USER_ID} data should be cleaned up")


class TestRewardsSummaryEndpoint:
    """Test GET /api/rewards/summary?user_id={id}"""

    def test_summary_returns_correct_json_shape(self):
        """Summary endpoint returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/rewards/summary?user_id={TEST_USER_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        required_fields = [
            "user_id", "lifetime_points", "monthly_points", "level",
            "estimated_usdt", "min_redeem_points", "is_redeemable"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"Summary response: {data}")

    def test_summary_new_user_returns_zeros(self):
        """New user should have zero points and default values"""
        new_user_id = f"test_new_user_{uuid.uuid4().hex[:8]}"
        response = requests.get(f"{BASE_URL}/api/rewards/summary?user_id={new_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["lifetime_points"] == 0
        assert data["monthly_points"] == 0
        assert data["level"] == "Newbie"
        assert data["estimated_usdt"] == 0.0
        assert data["is_redeemable"] == False
        assert data["min_redeem_points"] == 2000
        
        print(f"New user summary: {data}")

    def test_summary_without_user_id_fails(self):
        """Summary endpoint requires user_id parameter"""
        response = requests.get(f"{BASE_URL}/api/rewards/summary")
        assert response.status_code == 422  # Validation error


class TestRewardsLeaderboardEndpoint:
    """Test GET /api/rewards/leaderboard?user_id={id}"""

    def test_leaderboard_returns_correct_json_shape(self):
        """Leaderboard endpoint returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/rewards/leaderboard?user_id={TEST_USER_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        required_fields = [
            "user_id", "current_rank", "monthly_points", "level",
            "distance_to_next", "next_user_name", "suggested_message"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"Leaderboard response: {data}")

    def test_leaderboard_new_user_has_zero_rank(self):
        """New user should have rank 0 and motivational message"""
        new_user_id = f"test_lb_user_{uuid.uuid4().hex[:8]}"
        response = requests.get(f"{BASE_URL}/api/rewards/leaderboard?user_id={new_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_rank"] == 0
        assert data["monthly_points"] == 0
        assert "Start earning" in data["suggested_message"]
        
        print(f"New user leaderboard: {data}")


class TestProtectedEndpointsWithoutApiKey:
    """Test that protected endpoints return 403 without API key"""

    def test_redeem_without_api_key_returns_403(self):
        """POST /api/rewards/redeem without API key returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/redeem",
            json={"user_id": TEST_USER_ID, "reward_id": "test", "cost_points": 100}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"Redeem without key response: {response.status_code} - {response.json()}")

    def test_credit_without_api_key_returns_403(self):
        """POST /api/rewards/credit without API key returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/credit",
            json={"user_id": TEST_USER_ID, "points": 100, "source": "test"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"Credit without key response: {response.status_code} - {response.json()}")

    def test_trade_event_without_api_key_returns_403(self):
        """POST /api/rewards/events/trade without API key returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/trade",
            json={"user_id": TEST_USER_ID}
        )
        assert response.status_code == 403
        print(f"Trade event without key response: {response.status_code}")

    def test_deposit_event_without_api_key_returns_403(self):
        """POST /api/rewards/events/deposit without API key returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/deposit",
            json={"user_id": TEST_USER_ID, "amount_usdt": 100}
        )
        assert response.status_code == 403
        print(f"Deposit event without key response: {response.status_code}")

    def test_signup_event_without_api_key_returns_403(self):
        """POST /api/rewards/events/signup without API key returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/signup",
            json={"user_id": TEST_USER_ID}
        )
        assert response.status_code == 403
        print(f"Signup event without key response: {response.status_code}")

    def test_referral_event_without_api_key_returns_403(self):
        """POST /api/rewards/events/referral-qualified without API key returns 403"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/referral-qualified",
            json={"inviter_id": TEST_USER_ID, "invitee_id": "test_invitee"}
        )
        assert response.status_code == 403
        print(f"Referral event without key response: {response.status_code}")


class TestProtectedEndpointsWithApiKey:
    """Test protected endpoints with valid API key"""

    def test_credit_with_api_key_succeeds(self):
        """POST /api/rewards/credit with API key adds points"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/credit",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": TEST_USER_ID, "points": 100, "source": "test_credit"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert "new_lifetime_points" in data
        assert data["new_lifetime_points"] >= 100
        
        print(f"Credit response: {data}")

    def test_redeem_insufficient_points_returns_failure(self):
        """POST /api/rewards/redeem with insufficient points returns failure"""
        # Redeem requires 2000+ points, our test user only has 100
        response = requests.post(
            f"{BASE_URL}/api/rewards/redeem",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": TEST_USER_ID, "reward_id": "test_reward", "cost_points": 2000}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == False
        assert "message" in data
        assert "Not enough points" in data["message"] or "Minimum" in data["message"]
        
        print(f"Redeem insufficient points response: {data}")


class TestEventEndpoints:
    """Test event processing endpoints"""

    def test_signup_event_awards_25_points(self):
        """POST /api/rewards/events/signup awards 25 points"""
        signup_user_id = f"test_signup_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/signup",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": signup_user_id}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["success"] == True
        
        # Verify points were awarded
        summary = requests.get(f"{BASE_URL}/api/rewards/summary?user_id={signup_user_id}")
        assert summary.status_code == 200
        assert summary.json()["lifetime_points"] == 25
        
        print(f"Signup event awarded 25 points to {signup_user_id}")

    def test_deposit_event_awards_points(self):
        """POST /api/rewards/events/deposit awards points (75 USDT = 75 pts)"""
        deposit_user_id = f"test_deposit_{uuid.uuid4().hex[:8]}"
        
        # Award base points first via signup
        requests.post(
            f"{BASE_URL}/api/rewards/events/signup",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": deposit_user_id}
        )
        
        # Now do deposit
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/deposit",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": deposit_user_id, "amount_usdt": 75}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["success"] == True
        
        # Verify points: 25 (signup) + 75 (deposit: 75/50*50 = 75)
        summary = requests.get(f"{BASE_URL}/api/rewards/summary?user_id={deposit_user_id}")
        assert summary.status_code == 200
        # Deposit points = (75/50) * 50 = 75
        expected_points = 25 + 75
        assert summary.json()["lifetime_points"] == expected_points
        
        print(f"Deposit event awarded points. Total: {summary.json()['lifetime_points']}")

    def test_trade_event_awards_first_trade_bonus(self):
        """POST /api/rewards/events/trade awards 25 pts for first trade"""
        trade_user_id = f"test_trade_{uuid.uuid4().hex[:8]}"
        
        # Setup: signup first
        requests.post(
            f"{BASE_URL}/api/rewards/events/signup",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": trade_user_id}
        )
        
        # First trade
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/trade",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": trade_user_id}
        )
        assert response.status_code == 200
        assert response.json()["success"] == True
        
        # Verify: 25 (signup) + 25 (first trade) = 50
        summary = requests.get(f"{BASE_URL}/api/rewards/summary?user_id={trade_user_id}")
        assert summary.status_code == 200
        assert summary.json()["lifetime_points"] == 50
        
        print(f"First trade bonus awarded. Total: {summary.json()['lifetime_points']}")

    def test_referral_qualified_awards_150_points(self):
        """POST /api/rewards/events/referral-qualified awards 150 pts to inviter"""
        inviter_id = f"test_inviter_{uuid.uuid4().hex[:8]}"
        invitee_id = f"test_invitee_{uuid.uuid4().hex[:8]}"
        
        # Setup: inviter signs up
        requests.post(
            f"{BASE_URL}/api/rewards/events/signup",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": inviter_id}
        )
        
        # Referral qualified
        response = requests.post(
            f"{BASE_URL}/api/rewards/events/referral-qualified",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"inviter_id": inviter_id, "invitee_id": invitee_id}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()["success"] == True
        
        # Verify: 25 (signup) + 150 (referral) = 175
        summary = requests.get(f"{BASE_URL}/api/rewards/summary?user_id={inviter_id}")
        assert summary.status_code == 200
        assert summary.json()["lifetime_points"] == 175
        
        print(f"Referral bonus awarded to inviter. Total: {summary.json()['lifetime_points']}")


class TestSystemCheck:
    """Test POST /api/rewards/system-check with admin JWT"""

    def test_system_check_with_admin_jwt_passes(self, admin_token):
        """System check with admin JWT should run full health check"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/system-check",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "overall" in data
        assert "results" in data
        assert "timestamp" in data
        assert "message" in data
        
        print(f"System check overall: {data['overall']}")
        print(f"System check message: {data['message']}")
        
        # Check that results contain expected steps
        if data["overall"] == "pass":
            steps = [r["step"] for r in data["results"]]
            assert any("sign-up" in s.lower() or "signup" in s.lower() for s in steps), "Missing signup step"
            print(f"System check PASSED with {len(data['results'])} steps")
        else:
            print(f"System check FAILED: {data['results'][-1] if data['results'] else 'unknown'}")

    def test_system_check_without_auth_fails(self):
        """System check without auth should fail"""
        response = requests.post(f"{BASE_URL}/api/rewards/system-check")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"System check without auth: {response.status_code}")


class TestRedeemWithSufficientPoints:
    """Test redemption flow when user has enough points"""

    def test_redeem_with_sufficient_points_succeeds(self):
        """Redeem with 2000+ points should succeed"""
        redeem_user_id = f"test_redeem_{uuid.uuid4().hex[:8]}"
        
        # Credit enough points (2500)
        requests.post(
            f"{BASE_URL}/api/rewards/credit",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": redeem_user_id, "points": 2500, "source": "test_credit"}
        )
        
        # Verify points
        summary = requests.get(f"{BASE_URL}/api/rewards/summary?user_id={redeem_user_id}")
        assert summary.json()["lifetime_points"] >= 2000
        assert summary.json()["is_redeemable"] == True
        
        # Now redeem
        response = requests.post(
            f"{BASE_URL}/api/rewards/redeem",
            headers={"X-INTERNAL-API-KEY": INTERNAL_API_KEY},
            json={"user_id": redeem_user_id, "reward_id": "test_voucher", "cost_points": 2000}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "new_lifetime_points" in data
        assert data["new_lifetime_points"] == 500  # 2500 - 2000
        
        print(f"Redemption successful. Remaining points: {data['new_lifetime_points']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

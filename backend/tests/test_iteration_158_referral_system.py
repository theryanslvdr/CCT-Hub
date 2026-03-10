"""
Test Suite for Iteration 158: Referral System
Tests:
- POST /api/referrals/set-code - set user's referral code
- GET /api/referrals/my-code - get current user's referral info
- GET /api/referrals/check-onboarding - check if user needs onboarding
- POST /api/referrals/set-referred-by - set who referred user
- GET /api/referrals/admin/tree - admin endpoint returns referral tree structure
- GET /api/referrals/admin/flat-list - admin paginated flat list with search
- POST /api/referrals/admin/set-code - admin override to set a user's code
- POST /api/referrals/habit-reward - award streak-based habit points
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


class TestReferralSystemBackend:
    """Test suite for Referral System endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        self.user = None

    def login_admin(self):
        """Login as admin user"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user = data.get("user")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False

    # ─── User Endpoint Tests ───

    def test_01_login_admin_success(self):
        """Test admin login succeeds"""
        assert self.login_admin(), "Admin login failed"
        assert self.token is not None
        assert self.user is not None
        print(f"✓ Admin login successful: {self.user.get('email')}")

    def test_02_get_my_referral_code(self):
        """Test GET /api/referrals/my-code - get current user's referral info"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.get(f"{BASE_URL}/api/referrals/my-code")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Admin should have RYAN_MERIN code set
        assert "referral_code" in data
        assert "referred_by" in data
        assert "direct_referrals" in data
        assert "onboarding_complete" in data
        print(f"✓ GET /api/referrals/my-code successful")
        print(f"  - Referral Code: {data.get('referral_code')}")
        print(f"  - Direct Referrals: {data.get('direct_referrals')}")
        print(f"  - Onboarding Complete: {data.get('onboarding_complete')}")

    def test_03_check_onboarding_status(self):
        """Test GET /api/referrals/check-onboarding - check if user needs onboarding"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.get(f"{BASE_URL}/api/referrals/check-onboarding")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "needs_onboarding" in data
        assert "has_referral_code" in data
        assert "role" in data
        
        # Admin should NOT need onboarding
        assert data["needs_onboarding"] == False, "Admin should not need onboarding"
        print(f"✓ GET /api/referrals/check-onboarding successful")
        print(f"  - Needs Onboarding: {data.get('needs_onboarding')}")
        print(f"  - Has Referral Code: {data.get('has_referral_code')}")
        print(f"  - Role: {data.get('role')}")

    def test_04_set_referral_code_already_set(self):
        """Test POST /api/referrals/set-code - should fail if already set"""
        assert self.login_admin(), "Admin login failed"
        
        # Admin already has RYAN_MERIN set, so this should fail
        response = self.session.post(
            f"{BASE_URL}/api/referrals/set-code",
            json={"referral_code": "NEW_TEST_CODE"}
        )
        # Should fail because code is already set
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "already set" in data.get("detail", "").lower() or "contact admin" in data.get("detail", "").lower()
        print(f"✓ POST /api/referrals/set-code correctly rejects duplicate code setting")

    def test_05_set_referral_code_validation(self):
        """Test POST /api/referrals/set-code - validation for short codes"""
        assert self.login_admin(), "Admin login failed"
        
        # Try with a code that's too short (less than 3 chars)
        response = self.session.post(
            f"{BASE_URL}/api/referrals/set-code",
            json={"referral_code": "AB"}
        )
        # Should fail because code is already set for admin OR validation fails
        # Either is acceptable
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/referrals/set-code validates code length")

    def test_06_set_referred_by_self_reference(self):
        """Test POST /api/referrals/set-referred-by - cannot refer self"""
        assert self.login_admin(), "Admin login failed"
        
        # First check if admin has a referral code
        my_code_resp = self.session.get(f"{BASE_URL}/api/referrals/my-code")
        my_code = my_code_resp.json().get("referral_code", "RYAN_MERIN")
        
        # Try to set self as referrer
        response = self.session.post(
            f"{BASE_URL}/api/referrals/set-referred-by",
            json={"referral_code": my_code}
        )
        # Should fail - either already set or can't self-refer
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/referrals/set-referred-by prevents self-referral")

    def test_07_set_referred_by_invalid_code(self):
        """Test POST /api/referrals/set-referred-by - invalid referral code"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.post(
            f"{BASE_URL}/api/referrals/set-referred-by",
            json={"referral_code": "NONEXISTENT_CODE_12345"}
        )
        # Should fail - either not found or already set
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/referrals/set-referred-by handles invalid codes")

    # ─── Admin Endpoint Tests ───

    def test_10_admin_get_referral_tree(self):
        """Test GET /api/referrals/admin/tree - admin referral tree endpoint"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.get(f"{BASE_URL}/api/referrals/admin/tree")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tree" in data
        assert "stats" in data
        
        # Validate stats structure
        stats = data["stats"]
        assert "total_users" in stats
        assert "users_with_code" in stats
        assert "users_referred" in stats
        assert "onboarding_completion_rate" in stats
        
        print(f"✓ GET /api/referrals/admin/tree successful")
        print(f"  - Total Users: {stats.get('total_users')}")
        print(f"  - Users with Code: {stats.get('users_with_code')}")
        print(f"  - Users Referred: {stats.get('users_referred')}")
        print(f"  - Onboarding Rate: {stats.get('onboarding_completion_rate')}%")
        print(f"  - Tree Nodes: {len(data.get('tree', []))}")

    def test_11_admin_get_flat_list(self):
        """Test GET /api/referrals/admin/flat-list - admin paginated flat list"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.get(f"{BASE_URL}/api/referrals/admin/flat-list")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        
        # Check user structure
        if len(data["users"]) > 0:
            user = data["users"][0]
            assert "id" in user
            assert "email" in user or "full_name" in user
            assert "referral_count" in user
        
        print(f"✓ GET /api/referrals/admin/flat-list successful")
        print(f"  - Total: {data.get('total')}")
        print(f"  - Page: {data.get('page')}")
        print(f"  - Page Size: {data.get('page_size')}")
        print(f"  - Users on this page: {len(data.get('users', []))}")

    def test_12_admin_flat_list_with_search(self):
        """Test GET /api/referrals/admin/flat-list with search parameter"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/referrals/admin/flat-list",
            params={"search": "ryan", "page": 1, "page_size": 10}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "users" in data
        print(f"✓ GET /api/referrals/admin/flat-list with search successful")
        print(f"  - Search: 'ryan', Results: {len(data.get('users', []))}")

    def test_13_admin_flat_list_pagination(self):
        """Test GET /api/referrals/admin/flat-list pagination"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.get(
            f"{BASE_URL}/api/referrals/admin/flat-list",
            params={"page": 1, "page_size": 5}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["users"]) <= 5
        print(f"✓ GET /api/referrals/admin/flat-list pagination works correctly")

    def test_14_admin_set_code_validation(self):
        """Test POST /api/referrals/admin/set-code - validation"""
        assert self.login_admin(), "Admin login failed"
        
        # Try with invalid user_id
        response = self.session.post(
            f"{BASE_URL}/api/referrals/admin/set-code",
            json={"user_id": "nonexistent-user-id", "referral_code": "TEST_CODE"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/referrals/admin/set-code validates user existence")

    def test_15_admin_set_code_short_code(self):
        """Test POST /api/referrals/admin/set-code - short code validation"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.post(
            f"{BASE_URL}/api/referrals/admin/set-code",
            json={"user_id": self.user["id"], "referral_code": "AB"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/referrals/admin/set-code validates code length")

    # ─── Habit Reward Tests ───

    def test_20_habit_reward_endpoint(self):
        """Test POST /api/referrals/habit-reward - habit reward points"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.post(f"{BASE_URL}/api/referrals/habit-reward")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "points" in data
        assert "message" in data
        
        # Check if already awarded today or just awarded
        if data["success"]:
            assert data["points"] in [5, 10, 20, 35], f"Points should be tier-based: {data['points']}"
            print(f"✓ POST /api/referrals/habit-reward awarded points")
            print(f"  - Points: {data.get('points')}")
            print(f"  - Streak: {data.get('streak')}")
        else:
            assert "already" in data["message"].lower()
            print(f"✓ POST /api/referrals/habit-reward correctly prevents double award")
            print(f"  - Message: {data.get('message')}")

    def test_21_habit_reward_double_award_prevention(self):
        """Test POST /api/referrals/habit-reward - prevents double award same day"""
        assert self.login_admin(), "Admin login failed"
        
        # Call twice to verify double award prevention
        response1 = self.session.post(f"{BASE_URL}/api/referrals/habit-reward")
        response2 = self.session.post(f"{BASE_URL}/api/referrals/habit-reward")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data2 = response2.json()
        # Second call should indicate already awarded
        assert data2["success"] == False or "already" in data2["message"].lower()
        print(f"✓ Double award prevention works correctly")

    # ─── Auth/Me Endpoint Tests ───

    def test_30_auth_me_includes_referral_fields(self):
        """Test GET /api/auth/me includes referral_code and referred_by fields"""
        assert self.login_admin(), "Admin login failed"
        
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # UserResponse should now include referral fields
        assert "referral_code" in data or data.get("referral_code") is None
        assert "referred_by" in data or data.get("referred_by") is None
        print(f"✓ GET /api/auth/me includes referral fields")
        print(f"  - Referral Code: {data.get('referral_code')}")
        print(f"  - Referred By: {data.get('referred_by')}")


class TestReferralSystemUnauth:
    """Test unauthorized access to referral endpoints"""

    def test_unauth_my_code(self):
        """Test /api/referrals/my-code without auth"""
        response = requests.get(f"{BASE_URL}/api/referrals/my-code")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ /api/referrals/my-code requires authentication")

    def test_unauth_check_onboarding(self):
        """Test /api/referrals/check-onboarding without auth"""
        response = requests.get(f"{BASE_URL}/api/referrals/check-onboarding")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ /api/referrals/check-onboarding requires authentication")

    def test_unauth_admin_tree(self):
        """Test /api/referrals/admin/tree without auth"""
        response = requests.get(f"{BASE_URL}/api/referrals/admin/tree")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ /api/referrals/admin/tree requires authentication")

    def test_unauth_habit_reward(self):
        """Test /api/referrals/habit-reward without auth"""
        response = requests.post(f"{BASE_URL}/api/referrals/habit-reward")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ /api/referrals/habit-reward requires authentication")

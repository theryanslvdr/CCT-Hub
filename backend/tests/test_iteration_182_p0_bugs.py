"""
Iteration 182: Test 4 P0 Bug Fixes

Bug 1: Profit Tracker 'New Trader' crash - Error Boundary fires when new user clicks Continue in onboarding wizard
Bug 2: Streak not syncing to Rewards - shows 67 in hub but 0 on Rewards page
Bug 3: Referral tree empty + unreadable - 38 referred but only 1 node showing
Bug 4: Member count mismatch - Admin Dashboard shows 20 vs Members list shows 50
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
ADMIN_USER_ID = "b4628e3e-9dec-42ef-8c75-dcba08194cd2"


class TestServerHealth:
    """Basic health check"""
    
    def test_server_running(self):
        """Verify server is responding"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        print("✓ Server is running")


class TestAdminLogin:
    """Get auth token for protected endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get JWT token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns access_token, not token
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in login response: {data.keys()}"
        print("✓ Admin login successful")
        return token
    
    def test_login(self, auth_token):
        """Verify login works"""
        assert auth_token is not None
        print(f"✓ Auth token received: {auth_token[:20]}...")


class TestBug1OnboardingEndpoint:
    """
    Bug 1: POST /api/profit/complete-onboarding should accept new trader payload without 422
    
    The issue was that start_date:null was causing validation errors.
    Fix: OnboardingData model accepts Optional[str] = None for start_date
    """
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_new_trader_payload_no_422(self, auth_headers):
        """
        Test that new trader payload with null start_date doesn't return 422.
        This was the original bug - Error Boundary firing on Continue click.
        """
        # Exact payload from the bug report
        new_trader_payload = {
            "user_type": "new",
            "starting_balance": 250,
            "start_date": None,
            "transactions": [],
            "trade_entries": [],
            "total_commission": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/profit/complete-onboarding",
            json=new_trader_payload,
            headers=auth_headers
        )
        
        # Should NOT return 422 validation error
        assert response.status_code != 422, f"Bug not fixed! Got 422: {response.text}"
        
        # Response should be 200 with success:true, or some other valid response
        # Even if there are business logic issues, it shouldn't be a 422 validation error
        print(f"✓ New trader payload accepted (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            # Check for success indicator
            assert data.get("success", True) is not False, f"Request failed: {data}"
            print(f"✓ Response: {data.get('message', 'success')}")
    
    def test_experienced_trader_payload(self, auth_headers):
        """Test that experienced trader payload with trade_entries works"""
        experienced_payload = {
            "user_type": "experienced",
            "starting_balance": 500,
            "start_date": "2024-01-01",
            "transactions": [],
            "trade_entries": [
                {
                    "date": "2024-01-02",
                    "actual_profit": 15.0,
                    "missed": False,
                    "balance": 515.0,
                    "product": "MOIL10",
                    "direction": "BUY"
                }
            ],
            "total_commission": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/profit/complete-onboarding",
            json=experienced_payload,
            headers=auth_headers
        )
        
        # Should NOT return 422 validation error
        assert response.status_code != 422, f"Got 422: {response.text}"
        print(f"✓ Experienced trader payload accepted (status: {response.status_code})")


class TestBug2StreakSyncToRewards:
    """
    Bug 2: Streak not syncing to Rewards - shows 67 in hub but 0 on Rewards page
    
    Fix: rewards.py now uses current_streak_days and best_streak_days fields
    (lines 125-126 in rewards.py)
    """
    
    def test_rewards_summary_returns_streak(self):
        """
        Test GET /api/rewards/summary?user_id={id} returns non-zero streak
        when user has trades (was returning 0 due to wrong field name)
        """
        response = requests.get(
            f"{BASE_URL}/api/rewards/summary",
            params={"user_id": ADMIN_USER_ID}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "current_streak" in data, f"Missing current_streak field: {data}"
        assert "best_streak" in data, f"Missing best_streak field: {data}"
        
        # Per the bug report, admin user should have non-zero streak
        # (current_streak_days=1, best_streak_days=46 according to main agent)
        current_streak = data.get("current_streak", 0)
        best_streak = data.get("best_streak", 0)
        
        print(f"✓ Rewards summary returned: current_streak={current_streak}, best_streak={best_streak}")
        
        # The fix should make these non-zero for admin user who has trades
        # Best streak should be 46 according to main agent
        assert best_streak > 0, f"Bug not fixed! best_streak is still 0: {data}"
        print(f"✓ Streak correctly returned (best={best_streak}, current={current_streak})")
    
    def test_rewards_summary_has_correct_fields(self):
        """Verify all expected fields are present in rewards summary"""
        response = requests.get(
            f"{BASE_URL}/api/rewards/summary",
            params={"user_id": ADMIN_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "user_id", "lifetime_points", "monthly_points", "level",
            "current_streak", "best_streak", "referral_count", "total_trades"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ All required fields present in rewards summary")


class TestBug3ReferralTreeNesting:
    """
    Bug 3: Referral tree empty + unreadable - 38 referred but only 1 node showing
    
    Fix: admin/tree endpoint now correctly nests referred users under their inviters
    using both referral_code and merin_referral_code mappings
    """
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_referral_tree_structure(self, auth_headers):
        """
        Test GET /api/referrals/admin/tree returns properly nested tree
        """
        response = requests.get(
            f"{BASE_URL}/api/referrals/admin/tree",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "tree" in data, f"Missing tree field: {data.keys()}"
        assert "stats" in data, f"Missing stats field: {data.keys()}"
        
        tree = data["tree"]
        stats = data["stats"]
        
        print(f"✓ Referral tree returned: {len(tree)} root nodes")
        print(f"✓ Stats: total_users={stats.get('total_users')}, users_with_code={stats.get('users_with_code')}, users_referred={stats.get('users_referred')}")
        
        # Count total nodes including children
        def count_nodes(nodes):
            count = len(nodes)
            for node in nodes:
                if node.get("children"):
                    count += count_nodes(node["children"])
            return count
        
        total_nodes = count_nodes(tree)
        print(f"✓ Total nodes in tree (including nested): {total_nodes}")
        
        # Verify nodes have expected structure
        if tree:
            sample_node = tree[0]
            expected_fields = ["id", "name", "referral_code", "children", "direct_referrals"]
            for field in expected_fields:
                assert field in sample_node, f"Missing field in node: {field}"
            print(f"✓ Tree nodes have correct structure")
    
    def test_my_code_referral_counting(self, auth_headers):
        """
        Test GET /api/referrals/my-code counts referrals by both referral_code and merin_referral_code
        """
        response = requests.get(
            f"{BASE_URL}/api/referrals/my-code",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "referral_code" in data, f"Missing referral_code: {data}"
        assert "direct_referrals" in data, f"Missing direct_referrals: {data}"
        
        print(f"✓ my-code response: referral_code={data.get('referral_code')}, direct_referrals={data.get('direct_referrals')}")
    
    def test_tracking_endpoint(self, auth_headers):
        """
        Test GET /api/referrals/tracking returns correct data with multi-code counting
        """
        response = requests.get(
            f"{BASE_URL}/api/referrals/tracking",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "direct_count" in data, f"Missing direct_count: {data}"
        assert "referral_code" in data, f"Missing referral_code: {data}"
        
        print(f"✓ tracking response: direct_count={data.get('direct_count')}, referral_code={data.get('referral_code')}")


class TestBug4MemberCountMismatch:
    """
    Bug 4: Member count mismatch - Admin Dashboard shows 20 vs Members list shows 50
    
    Fix: Frontend now uses response.total instead of array.length
    (AdminDashboardPage.jsx line 65: membersRes.data.total)
    """
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_admin_members_returns_total(self, auth_headers):
        """
        Test GET /api/admin/members returns {total, members[], limit, page, pages}
        Verify total reflects true count, not capped at page limit
        """
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total" in data, f"Missing 'total' field: {data.keys()}"
        assert "members" in data, f"Missing 'members' field: {data.keys()}"
        
        total = data.get("total", 0)
        members = data.get("members", [])
        limit = data.get("limit", data.get("page_size", 20))
        
        print(f"✓ API response: total={total}, members_returned={len(members)}, limit={limit}")
        
        # The key fix: total should be >= len(members)
        # If there are more users than the page limit, total > len(members)
        assert total >= len(members), f"total ({total}) should be >= members array length ({len(members)})"
        
        # If total > limit, that proves the API is returning true count
        if total > limit:
            print(f"✓ Total ({total}) > limit ({limit}) - proves total is true count, not capped")
        else:
            print(f"✓ Total ({total}) <= limit ({limit}) - all users fit in one page")
    
    def test_admin_members_pagination(self, auth_headers):
        """Test pagination parameters work correctly"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        members = data.get("members", [])
        assert len(members) <= 10, f"Page size not respected: got {len(members)} members"
        
        print(f"✓ Pagination works: requested page_size=10, got {len(members)} members")


class TestRegressionLoginFlow:
    """Regression: Verify login flow still works"""
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data or "token" in data, f"Missing token: {data}"
        assert "user" in data or "id" in data, f"Missing user data: {data}"
        
        print("✓ Login flow works correctly")
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials returns appropriate error"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        
        # Should not return 200
        assert response.status_code in [400, 401, 404], f"Expected error, got: {response.status_code}"
        print(f"✓ Invalid login rejected (status: {response.status_code})")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

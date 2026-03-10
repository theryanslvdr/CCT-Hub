"""
Iteration 176 - Testing New Features:
1. Admin update member endpoint (PUT /api/admin/members/{user_id}) with merin_referral_code and trading_start_date fields
2. Referral tracking API (GET /api/referrals/tracking) returns both invite_link and onboarding_invite_link fields
3. Forum post merge_info enrichment for merged posts
4. Onboarding invite link format: https://crosscur.rent/onboarding?merin_code={CODE}
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_MEMBER_ID = "a9566813-3880-47c5-8703-7fa22fdb601d"

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_check(self):
        """Verify backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("✓ Backend health check passed")
    
    def test_login_master_admin(self):
        """Login as master admin and get access_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert "user" in data, "Response missing user object"
        print(f"✓ Login successful, got access_token")
        return data["access_token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for authenticated requests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "iam@ryansalvador.com", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


class TestAdminMemberUpdate:
    """Test PUT /api/admin/members/{user_id} endpoint with merin_referral_code and trading_start_date"""
    
    def test_update_merin_referral_code(self, auth_token):
        """Verify merin_referral_code can be updated via admin endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Update merin_referral_code
        test_code = "TESTCODE176"
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            json={"merin_referral_code": test_code},
            headers=headers
        )
        assert response.status_code == 200, f"Update failed: {response.status_code} - {response.text}"
        print(f"✓ merin_referral_code update returned 200")
        
        # Verify the update via GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            headers=headers
        )
        assert get_response.status_code == 200, f"GET member failed: {get_response.status_code}"
        data = get_response.json()
        user = data.get("user", {})
        # Code should be uppercase
        assert user.get("merin_referral_code") == test_code.upper(), f"merin_referral_code not updated correctly: {user.get('merin_referral_code')}"
        print(f"✓ merin_referral_code verified via GET: {user.get('merin_referral_code')}")
    
    def test_update_trading_start_date(self, auth_token):
        """Verify trading_start_date can be updated via admin endpoint (master_admin only)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        test_date = "2025-01-15"
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            json={"trading_start_date": test_date},
            headers=headers
        )
        assert response.status_code == 200, f"Update trading_start_date failed: {response.status_code} - {response.text}"
        print(f"✓ trading_start_date update returned 200")
        
        # Verify the update via GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            headers=headers
        )
        assert get_response.status_code == 200
        data = get_response.json()
        user = data.get("user", {})
        assert user.get("trading_start_date") == test_date, f"trading_start_date not updated: {user.get('trading_start_date')}"
        print(f"✓ trading_start_date verified via GET: {user.get('trading_start_date')}")
    
    def test_update_merin_code_empty_clears(self, auth_token):
        """Verify empty string clears merin_referral_code"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First set a code
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            json={"merin_referral_code": "TOBECLEARED"},
            headers=headers
        )
        assert response.status_code == 200
        
        # Now clear it with empty string
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            json={"merin_referral_code": ""},
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify it's cleared
        get_response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            headers=headers
        )
        data = get_response.json()
        user = data.get("user", {})
        # Empty string or None are both acceptable
        assert user.get("merin_referral_code") in ["", None], f"merin_referral_code should be cleared: {user.get('merin_referral_code')}"
        print(f"✓ merin_referral_code cleared with empty string")


class TestReferralTrackingAPI:
    """Test GET /api/referrals/tracking returns invite_link and onboarding_invite_link"""
    
    def test_referral_tracking_endpoint(self, auth_token):
        """Verify /api/referrals/tracking returns both invite_link and onboarding_invite_link"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/referrals/tracking",
            headers=headers
        )
        assert response.status_code == 200, f"Referral tracking failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Check required fields exist
        assert "referral_code" in data, "Missing referral_code field"
        assert "merin_code" in data, "Missing merin_code field"
        assert "direct_count" in data, "Missing direct_count field"
        assert "milestones" in data, "Missing milestones field"
        print(f"✓ Basic referral tracking fields present")
        
        # Check for invite_link (may be None if no merin_code set)
        merin_code = data.get("merin_code")
        if merin_code:
            assert "invite_link" in data, "Missing invite_link field"
            assert "onboarding_invite_link" in data, "Missing onboarding_invite_link field"
            
            # Verify onboarding_invite_link format
            onboarding_link = data.get("onboarding_invite_link")
            expected_format = f"https://crosscur.rent/onboarding?merin_code={merin_code}"
            assert onboarding_link == expected_format, f"onboarding_invite_link format incorrect: {onboarding_link}"
            print(f"✓ onboarding_invite_link format verified: {onboarding_link}")
            
            # Verify invite_link format (direct Merin link)
            invite_link = data.get("invite_link")
            assert "meringlobaltrading.com" in invite_link, f"invite_link should be Merin URL: {invite_link}"
            print(f"✓ invite_link (direct Merin) verified: {invite_link}")
        else:
            print("⚠ merin_code is null, invite links will be null (expected if user has no code)")
    
    def test_referral_tracking_returns_referrals_list(self, auth_token):
        """Verify referrals list is returned"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/referrals/tracking",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "referrals" in data, "Missing referrals field"
        assert isinstance(data["referrals"], list), "referrals should be a list"
        print(f"✓ referrals list present with {len(data['referrals'])} entries")
        
        assert "next_milestone" in data, "Missing next_milestone field"
        print(f"✓ next_milestone field present")


class TestForumMergeInfo:
    """Test forum post merge_info enrichment"""
    
    def test_forum_posts_list(self, auth_token):
        """Verify forum posts endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/forum/posts",
            headers=headers
        )
        assert response.status_code == 200, f"Forum posts failed: {response.status_code}"
        data = response.json()
        
        assert "posts" in data, "Missing posts field"
        assert "total" in data, "Missing total field"
        print(f"✓ Forum posts endpoint returned {data.get('total', 0)} posts")
        return data.get("posts", [])
    
    def test_non_merged_post_no_merge_info(self, auth_token):
        """Verify non-merged posts don't have merge_info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get list of posts
        response = requests.get(
            f"{BASE_URL}/api/forum/posts",
            headers=headers
        )
        assert response.status_code == 200
        posts = response.json().get("posts", [])
        
        if not posts:
            pytest.skip("No forum posts to test")
        
        # Find a non-merged post
        non_merged = None
        for post in posts:
            if not post.get("merged_from"):
                non_merged = post
                break
        
        if not non_merged:
            pytest.skip("All posts are merged, cannot test non-merged post")
        
        # Get full post details
        post_response = requests.get(
            f"{BASE_URL}/api/forum/posts/{non_merged['id']}",
            headers=headers
        )
        assert post_response.status_code == 200
        post_data = post_response.json()
        
        # Non-merged posts should not have merge_info
        assert post_data.get("merge_info") is None, "Non-merged post should not have merge_info"
        print(f"✓ Non-merged post '{non_merged.get('title', '')[:30]}...' has no merge_info (expected)")
    
    def test_merged_post_has_merge_info(self, auth_token):
        """Verify merged posts have merge_info with expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get list of posts
        response = requests.get(
            f"{BASE_URL}/api/forum/posts?page_size=50",
            headers=headers
        )
        assert response.status_code == 200
        posts = response.json().get("posts", [])
        
        # Find a merged post (has merged_from field)
        merged_post = None
        for post in posts:
            if post.get("merged_from"):
                merged_post = post
                break
        
        if not merged_post:
            pytest.skip("No merged posts in database to test merge_info")
        
        # Get full post details
        post_response = requests.get(
            f"{BASE_URL}/api/forum/posts/{merged_post['id']}",
            headers=headers
        )
        assert post_response.status_code == 200
        post_data = post_response.json()
        
        # Merged post should have merge_info
        merge_info = post_data.get("merge_info")
        assert merge_info is not None, "Merged post should have merge_info"
        
        # Check expected fields in merge_info
        expected_fields = ["source_title", "source_post_id", "merged_by_name", "merged_at", "comments_moved"]
        for field in expected_fields:
            assert field in merge_info, f"merge_info missing field: {field}"
        
        print(f"✓ Merged post has merge_info with all expected fields")
        print(f"  - source_title: {merge_info.get('source_title', '')[:30]}...")
        print(f"  - merged_by_name: {merge_info.get('merged_by_name')}")
        print(f"  - comments_moved: {merge_info.get('comments_moved')}")


class TestAdminMembersModel:
    """Test AdminUserUpdate model has required fields"""
    
    def test_admin_user_update_model_accepts_merin_code(self, auth_token):
        """Verify AdminUserUpdate accepts merin_referral_code"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # This is a model test - we verify by making the API call
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            json={"merin_referral_code": "MODELTEST"},
            headers=headers
        )
        # Should not get 422 validation error
        assert response.status_code != 422, f"merin_referral_code rejected by model: {response.text}"
        assert response.status_code == 200, f"Unexpected error: {response.status_code}"
        print("✓ AdminUserUpdate model accepts merin_referral_code field")
    
    def test_admin_user_update_model_accepts_trading_start_date(self, auth_token):
        """Verify AdminUserUpdate accepts trading_start_date"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/admin/members/{TEST_MEMBER_ID}",
            json={"trading_start_date": "2025-02-01"},
            headers=headers
        )
        assert response.status_code != 422, f"trading_start_date rejected by model: {response.text}"
        assert response.status_code == 200, f"Unexpected error: {response.status_code}"
        print("✓ AdminUserUpdate model accepts trading_start_date field")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

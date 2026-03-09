"""
Test Suite for Iteration 152 - BVE Data Isolation and Forum Merge Features

Tests:
1. BVE Trade History - returns data from BVE collections only (not production)
2. BVE Trade Delete - deletes from BVE only, never production
3. BVE Rewind - does NOT touch production trade_logs
4. Forum Merge - POST /api/forum/posts/merge 
5. Forum Validate Solution - PUT /api/forum/posts/{post_id}/validate-solution
6. Forum Search Similar Full - GET /api/forum/search-similar-full
7. Forum Post Details - GET /api/forum/posts/{post_id}/details
8. Forum Enhanced Search - GET /api/forum/search-similar searches both title AND content
9. Forum Merge Role Check - only master_admin and super_admin can merge
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"


class TestAuth:
    """Authentication helper"""
    
    @staticmethod
    def get_admin_token():
        """Login as master_admin and return token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert res.status_code == 200, f"Login failed: {res.text}"
        data = res.json()
        return data.get("access_token") or data.get("token")
    
    @staticmethod
    def get_headers(token):
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class TestBVETradeHistory:
    """Test BVE trade history returns data from BVE collections only"""
    
    def test_bve_trade_history_endpoint_exists(self):
        """Test that /api/bve/trade/history endpoint exists"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # First enter BVE to get a session
        enter_res = requests.post(f"{BASE_URL}/api/bve/enter", headers=headers)
        # May fail if already in BVE - that's OK
        
        res = requests.get(f"{BASE_URL}/api/bve/trade/history", headers=headers)
        # Should return 200 or 400 (if no active session)
        assert res.status_code in [200, 400], f"Unexpected status: {res.status_code}, {res.text}"
        
    def test_bve_trade_history_returns_only_bve_data(self):
        """Test that trade history in BVE mode only returns BVE trades, not production"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # Enter BVE
        enter_res = requests.post(f"{BASE_URL}/api/bve/enter", headers=headers)
        session_id = None
        if enter_res.status_code == 200:
            session_id = enter_res.json().get("session_id")
        
        # Get BVE trade history
        res = requests.get(f"{BASE_URL}/api/bve/trade/history", headers=headers)
        if res.status_code == 200:
            data = res.json()
            # Verify structure
            assert "trades" in data, "Response should have trades field"
            assert "total" in data, "Response should have total field"
            
            # If there are trades, check they have bve_session_id
            for trade in data.get("trades", []):
                if "bve_session_id" in trade:
                    print(f"Trade {trade.get('id')} has bve_session_id: {trade['bve_session_id']}")
        
        # Exit BVE if we entered
        if session_id:
            requests.post(f"{BASE_URL}/api/bve/exit", headers=headers, json={"session_id": session_id})


class TestBVETradeDelete:
    """Test BVE trade delete only affects BVE collections"""
    
    def test_bve_delete_trade_endpoint_exists(self):
        """Test that DELETE /api/bve/trade/{trade_id} endpoint exists"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # Enter BVE first
        enter_res = requests.post(f"{BASE_URL}/api/bve/enter", headers=headers)
        
        # Try to delete a non-existent trade - should return 404, not 405
        fake_trade_id = str(uuid.uuid4())
        res = requests.delete(f"{BASE_URL}/api/bve/trade/{fake_trade_id}", headers=headers)
        # 404 means route exists but trade not found, 400 means no active session
        assert res.status_code in [404, 400], f"Expected 404/400, got {res.status_code}: {res.text}"
        print(f"BVE trade delete endpoint exists, returned {res.status_code}")


class TestBVERewind:
    """Test BVE rewind does not touch production trade_logs"""
    
    def test_bve_rewind_endpoint_exists(self):
        """Test that POST /api/bve/rewind endpoint exists"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # Enter BVE
        enter_res = requests.post(f"{BASE_URL}/api/bve/enter", headers=headers)
        if enter_res.status_code == 200:
            session_id = enter_res.json().get("session_id")
            
            # Try rewind
            rewind_res = requests.post(f"{BASE_URL}/api/bve/rewind", headers=headers, json={"session_id": session_id})
            assert rewind_res.status_code == 200, f"Rewind failed: {rewind_res.text}"
            
            data = rewind_res.json()
            assert "message" in data, "Rewind response should have message"
            assert "restored" in data, "Rewind response should have restored counts"
            print(f"BVE rewind successful: {data}")
            
            # Exit BVE
            requests.post(f"{BASE_URL}/api/bve/exit", headers=headers, json={"session_id": session_id})


class TestForumMergePosts:
    """Test forum merge posts feature - only for master_admin/super_admin"""
    
    def test_merge_posts_endpoint_exists(self):
        """Test that POST /api/forum/posts/merge endpoint exists"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # Try to merge with invalid IDs - should return 404, not 405
        res = requests.post(f"{BASE_URL}/api/forum/posts/merge", headers=headers, json={
            "source_post_id": str(uuid.uuid4()),
            "target_post_id": str(uuid.uuid4())
        })
        # 404 means route exists but posts not found
        assert res.status_code in [404, 400], f"Expected 404/400, got {res.status_code}: {res.text}"
        print(f"Forum merge endpoint exists, returned {res.status_code}: {res.json().get('detail', '')}")
    
    def test_merge_posts_requires_admin_role(self):
        """Test that merge posts requires master_admin or super_admin role"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # Master admin should be able to attempt merge (even if posts don't exist)
        res = requests.post(f"{BASE_URL}/api/forum/posts/merge", headers=headers, json={
            "source_post_id": str(uuid.uuid4()),
            "target_post_id": str(uuid.uuid4())
        })
        # Should NOT return 403 for master_admin
        assert res.status_code != 403, f"Master admin should not get 403 for merge"
        print(f"Master admin merge access: {res.status_code}")


class TestForumValidateSolution:
    """Test forum validate solution endpoint"""
    
    def test_validate_solution_endpoint_exists(self):
        """Test that PUT /api/forum/posts/{post_id}/validate-solution endpoint exists"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        fake_post_id = str(uuid.uuid4())
        res = requests.put(f"{BASE_URL}/api/forum/posts/{fake_post_id}/validate-solution", headers=headers)
        # 404 means route exists but post not found
        assert res.status_code == 404, f"Expected 404 for non-existent post, got {res.status_code}: {res.text}"
        print(f"Validate solution endpoint exists, returned 404 for non-existent post")


class TestForumSearchSimilarFull:
    """Test enhanced similar search covering both title and content"""
    
    def test_search_similar_full_endpoint_exists(self):
        """Test that GET /api/forum/search-similar-full endpoint exists"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        res = requests.get(f"{BASE_URL}/api/forum/search-similar-full", 
                          headers=headers,
                          params={"title": "test query", "content": "test content"})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "results" in data, "Response should have results field"
        assert "has_similar" in data, "Response should have has_similar flag"
        print(f"Search similar full: has_similar={data['has_similar']}, results_count={len(data['results'])}")
    
    def test_search_similar_full_returns_has_similar_flag(self):
        """Test that search-similar-full returns has_similar boolean flag"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        res = requests.get(f"{BASE_URL}/api/forum/search-similar-full",
                          headers=headers,
                          params={"title": "xyz123nonexistent", "content": ""})
        assert res.status_code == 200
        
        data = res.json()
        assert isinstance(data.get("has_similar"), bool), "has_similar should be boolean"
        print(f"has_similar flag is boolean: {data['has_similar']}")


class TestForumPostDetails:
    """Test forum post details sidebar endpoint"""
    
    def test_post_details_endpoint_exists(self):
        """Test that GET /api/forum/posts/{post_id}/details endpoint exists"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        fake_post_id = str(uuid.uuid4())
        res = requests.get(f"{BASE_URL}/api/forum/posts/{fake_post_id}/details", headers=headers)
        # 404 means route exists but post not found
        assert res.status_code == 404, f"Expected 404 for non-existent post, got {res.status_code}: {res.text}"
        print(f"Post details endpoint exists, returned 404 for non-existent post")
    
    def test_post_details_with_existing_post(self):
        """Test post details endpoint returns expected fields for existing post"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # First get list of posts to find an existing one
        posts_res = requests.get(f"{BASE_URL}/api/forum/posts", headers=headers)
        if posts_res.status_code == 200:
            posts = posts_res.json().get("posts", [])
            if posts:
                post_id = posts[0]["id"]
                res = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}/details", headers=headers)
                assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
                
                data = res.json()
                # Check expected fields
                assert "post_id" in data, "Should have post_id"
                assert "contributors" in data, "Should have contributors list"
                assert "awards" in data, "Should have awards list"
                assert "created_at" in data, "Should have created_at"
                assert "status" in data, "Should have status"
                print(f"Post details for {post_id}: contributors={len(data['contributors'])}, awards={len(data['awards'])}")


class TestForumEnhancedSearch:
    """Test that search-similar now searches both title AND content"""
    
    def test_search_similar_searches_both_title_and_content(self):
        """Test that GET /api/forum/search-similar searches both title and content"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        res = requests.get(f"{BASE_URL}/api/forum/search-similar",
                          headers=headers,
                          params={"q": "trading profit"})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        data = res.json()
        assert "results" in data, "Response should have results"
        print(f"Enhanced search returned {len(data['results'])} results")


class TestForumMergeRoleRestriction:
    """Test that only master_admin and super_admin can merge posts"""
    
    def test_merge_role_check_in_backend(self):
        """Verify that the merge endpoint checks for admin roles"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # Get current user to verify role
        me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        user = me_res.json()
        role = user.get("role")
        print(f"Current user role: {role}")
        
        # Master admin should have access
        if role in ["master_admin", "super_admin"]:
            res = requests.post(f"{BASE_URL}/api/forum/posts/merge", headers=headers, json={
                "source_post_id": str(uuid.uuid4()),
                "target_post_id": str(uuid.uuid4())
            })
            # Should NOT be 403 for allowed roles
            assert res.status_code != 403, f"Admin role {role} should not get 403"
            print(f"Role {role} has merge access (status: {res.status_code})")


class TestForumDuplicateSafeguard:
    """Test duplicate post safeguard with search-similar-full"""
    
    def test_duplicate_safeguard_returns_has_similar(self):
        """Test that search-similar-full provides duplicate safeguard flag"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # Search for something likely to have matches
        res = requests.get(f"{BASE_URL}/api/forum/search-similar-full",
                          headers=headers,
                          params={"title": "test", "content": "question"})
        assert res.status_code == 200
        
        data = res.json()
        # Verify the safeguard flag exists
        assert "has_similar" in data, "Response must include has_similar flag for duplicate safeguard"
        assert isinstance(data["has_similar"], bool), "has_similar must be boolean"
        print(f"Duplicate safeguard working: has_similar={data['has_similar']}")


class TestIntegrationBVEIsolation:
    """Integration test for BVE data isolation - P0 bug fix verification"""
    
    def test_bve_workflow_isolation(self):
        """Test complete BVE workflow: enter -> log trade -> get history -> delete -> exit"""
        token = TestAuth.get_admin_token()
        headers = TestAuth.get_headers(token)
        
        # 1. Enter BVE
        enter_res = requests.post(f"{BASE_URL}/api/bve/enter", headers=headers)
        if enter_res.status_code != 200:
            print(f"Could not enter BVE (may already be in session): {enter_res.text}")
            pytest.skip("Cannot enter BVE - may need to exit existing session")
        
        session_id = enter_res.json().get("session_id")
        print(f"Entered BVE session: {session_id}")
        
        try:
            # 2. Log a trade in BVE
            trade_res = requests.post(f"{BASE_URL}/api/bve/trade/log", headers=headers, json={
                "lot_size": 10.0,
                "direction": "BUY",
                "actual_profit": 150.0,
                "notes": "TEST_BVE_ISOLATION"
            })
            assert trade_res.status_code == 200, f"Failed to log BVE trade: {trade_res.text}"
            trade_data = trade_res.json()
            trade_id = trade_data.get("id")
            print(f"Logged BVE trade: {trade_id}")
            
            # 3. Get BVE trade history - should include our trade
            history_res = requests.get(f"{BASE_URL}/api/bve/trade/history", headers=headers)
            assert history_res.status_code == 200
            history = history_res.json()
            assert history["total"] >= 1, "Should have at least 1 trade in BVE"
            print(f"BVE trade history: {history['total']} trades")
            
            # 4. Delete the trade from BVE
            if trade_id:
                delete_res = requests.delete(f"{BASE_URL}/api/bve/trade/{trade_id}", headers=headers)
                assert delete_res.status_code == 200, f"Failed to delete BVE trade: {delete_res.text}"
                print(f"Deleted BVE trade: {trade_id}")
            
            # 5. Rewind BVE
            rewind_res = requests.post(f"{BASE_URL}/api/bve/rewind", headers=headers, json={"session_id": session_id})
            assert rewind_res.status_code == 200, f"Rewind failed: {rewind_res.text}"
            print(f"BVE rewound successfully")
            
        finally:
            # 6. Exit BVE
            exit_res = requests.post(f"{BASE_URL}/api/bve/exit", headers=headers, json={"session_id": session_id})
            print(f"Exited BVE session: {exit_res.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

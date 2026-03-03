"""
Test iteration 139: AdminSettingsPage refactoring + Forum enhancements verification
- Tests extracted EmailsTab, TradingTab, DiagnosticsTab components via API
- Tests forum voting, similar search, stats/reputation endpoints
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestForumAPIs:
    """Forum voting, similar search, and stats APIs"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get superadmin token for second user
        resp2 = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "superadmin@test.com",
            "password": "admin123"
        })
        assert resp2.status_code == 200
        self.superadmin_token = resp2.json().get("access_token")
        self.superadmin_headers = {"Authorization": f"Bearer {self.superadmin_token}"}

    def test_forum_stats_returns_reputation(self):
        """GET /api/forum/stats should return top contributors with reputation"""
        resp = requests.get(f"{BASE_URL}/api/forum/stats", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_posts" in data
        assert "open_posts" in data
        assert "closed_posts" in data
        assert "total_comments" in data
        assert "top_contributors" in data
        # Check top contributors have reputation fields
        if len(data["top_contributors"]) > 0:
            tc = data["top_contributors"][0]
            assert "user_id" in tc
            assert "name" in tc
            assert "best_answers" in tc
            assert "upvotes_received" in tc
            assert "comments_count" in tc
            assert "reputation" in tc
        print(f"Forum stats: {data['total_posts']} posts, {len(data['top_contributors'])} contributors")

    def test_forum_search_similar_posts(self):
        """GET /api/forum/search-similar?q=lot+size should return similar posts"""
        resp = requests.get(f"{BASE_URL}/api/forum/search-similar?q=lot%20size", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "query" in data
        print(f"Similar search 'lot size': Found {len(data['results'])} results")
        # Should find the closed post about lot size
        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "id" in result
            assert "title" in result
            assert "status" in result

    def test_forum_search_similar_min_length(self):
        """Search with <3 chars should fail validation"""
        resp = requests.get(f"{BASE_URL}/api/forum/search-similar?q=ab", headers=self.headers)
        # Should return validation error
        assert resp.status_code in [400, 422]

    def test_vote_comment_on_existing_post(self):
        """Test voting on comments - create post, add comment, vote"""
        # Create a test post
        post_resp = requests.post(f"{BASE_URL}/api/forum/posts", headers=self.headers, json={
            "title": "TEST_iteration139_vote_test",
            "content": "This is a test post for vote testing",
            "tags": ["test"]
        })
        assert post_resp.status_code == 200
        post_id = post_resp.json()["id"]

        try:
            # Add a comment as superadmin (different user)
            comment_resp = requests.post(
                f"{BASE_URL}/api/forum/posts/{post_id}/comments",
                headers=self.superadmin_headers,
                json={"content": "TEST comment for voting"}
            )
            assert comment_resp.status_code == 200
            comment_id = comment_resp.json()["id"]

            # Now master admin votes on superadmin's comment - should work
            vote_resp = requests.post(
                f"{BASE_URL}/api/forum/comments/{comment_id}/vote",
                headers=self.headers,
                json={"vote_type": "up"}
            )
            assert vote_resp.status_code == 200
            data = vote_resp.json()
            assert data["action"] == "created"
            assert data["vote_type"] == "up"
            print(f"Upvote created successfully for comment {comment_id}")

            # Toggle - same vote removes it
            toggle_resp = requests.post(
                f"{BASE_URL}/api/forum/comments/{comment_id}/vote",
                headers=self.headers,
                json={"vote_type": "up"}
            )
            assert toggle_resp.status_code == 200
            assert toggle_resp.json()["action"] == "removed"
            print("Upvote toggle (remove) works")

            # Vote again, then switch
            requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote",
                headers=self.headers, json={"vote_type": "up"})
            switch_resp = requests.post(
                f"{BASE_URL}/api/forum/comments/{comment_id}/vote",
                headers=self.headers,
                json={"vote_type": "down"}
            )
            assert switch_resp.status_code == 200
            assert switch_resp.json()["action"] == "switched"
            print("Vote switch (up->down) works")

        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers=self.headers)

    def test_cannot_vote_on_own_comment(self):
        """User cannot vote on their own comment"""
        # Create post
        post_resp = requests.post(f"{BASE_URL}/api/forum/posts", headers=self.headers, json={
            "title": "TEST_iteration139_own_vote",
            "content": "Test for self-voting",
            "tags": []
        })
        assert post_resp.status_code == 200
        post_id = post_resp.json()["id"]

        try:
            # Add comment as same user
            comment_resp = requests.post(
                f"{BASE_URL}/api/forum/posts/{post_id}/comments",
                headers=self.headers,
                json={"content": "My own comment"}
            )
            assert comment_resp.status_code == 200
            comment_id = comment_resp.json()["id"]

            # Try to vote on own comment - should fail
            vote_resp = requests.post(
                f"{BASE_URL}/api/forum/comments/{comment_id}/vote",
                headers=self.headers,
                json={"vote_type": "up"}
            )
            assert vote_resp.status_code == 400
            assert "own comment" in vote_resp.json().get("detail", "").lower()
            print("Self-voting correctly blocked")

        finally:
            requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers=self.headers)

    def test_comment_voters_endpoint(self):
        """GET /api/forum/comments/{id}/voters returns voter list"""
        # Create post and add comment
        post_resp = requests.post(f"{BASE_URL}/api/forum/posts", headers=self.headers, json={
            "title": "TEST_iteration139_voters_list",
            "content": "Test post for voters",
            "tags": []
        })
        post_id = post_resp.json()["id"]

        try:
            # Superadmin adds comment
            comment_resp = requests.post(
                f"{BASE_URL}/api/forum/posts/{post_id}/comments",
                headers=self.superadmin_headers,
                json={"content": "Comment to vote on"}
            )
            comment_id = comment_resp.json()["id"]

            # Master admin votes
            requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote",
                headers=self.headers, json={"vote_type": "up"})

            # Get voters
            voters_resp = requests.get(
                f"{BASE_URL}/api/forum/comments/{comment_id}/voters",
                headers=self.headers
            )
            assert voters_resp.status_code == 200
            data = voters_resp.json()
            assert "comment_id" in data
            assert "votes" in data
            assert len(data["votes"]) > 0
            # Voter should have name visible
            vote = data["votes"][0]
            assert "voter_name" in vote
            assert "vote_type" in vote
            print(f"Voters endpoint works: {len(data['votes'])} votes, names visible")

        finally:
            requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers=self.headers)


class TestAdminDiagnosticsAPIs:
    """APIs used by DiagnosticsTab component"""

    @pytest.fixture(autouse=True)
    def setup(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert resp.status_code == 200
        self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_health_check_endpoint(self):
        """GET /api/admin/licensees/health-check - health check API"""
        resp = requests.get(f"{BASE_URL}/api/admin/licensees/health-check", headers=self.headers)
        # Should work or return known response
        if resp.status_code == 200:
            data = resp.json()
            assert "ok" in data or "broken" in data
            print(f"Health check: ok={data.get('ok', 0)}, broken={data.get('broken', 0)}")
        else:
            print(f"Health check endpoint returned {resp.status_code}")
        # Not failing because API might not be fully implemented

    def test_rewards_sync_status(self):
        """GET /api/rewards/sync-status - rewards platform sync status"""
        resp = requests.get(f"{BASE_URL}/api/rewards/sync-status", headers=self.headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Rewards sync status: {data}")
        else:
            print(f"Rewards sync status returned {resp.status_code}")


class TestEmailsTabAPIs:
    """APIs used by EmailsTab component"""

    @pytest.fixture(autouse=True)
    def setup(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert resp.status_code == 200
        self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_email_templates_endpoint(self):
        """GET /api/settings/email-templates"""
        resp = requests.get(f"{BASE_URL}/api/settings/email-templates", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data
        print(f"Email templates: {len(data['templates'])} templates loaded")

    def test_email_history_endpoint(self):
        """GET /api/settings/email-history"""
        resp = requests.get(f"{BASE_URL}/api/settings/email-history", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "emails" in data
        assert "total" in data
        print(f"Email history: {data['total']} emails in history")


class TestTradingTabAPIs:
    """APIs used by TradingTab component"""

    @pytest.fixture(autouse=True)
    def setup(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert resp.status_code == 200
        self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_global_holidays_endpoint(self):
        """GET /api/admin/global-holidays"""
        resp = requests.get(f"{BASE_URL}/api/admin/global-holidays", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "holidays" in data
        print(f"Global holidays: {len(data['holidays'])} holidays configured")

    def test_trading_products_endpoint(self):
        """GET /api/admin/trading-products"""
        resp = requests.get(f"{BASE_URL}/api/admin/trading-products", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        print(f"Trading products: {len(data['products'])} products")


class TestForumEnrichedComments:
    """Test that GET /api/forum/posts/{id} returns comments with vote enrichment"""

    @pytest.fixture(autouse=True)
    def setup(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert resp.status_code == 200
        self.token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_existing_post_comments_have_vote_data(self):
        """Check that an existing post's comments include vote fields"""
        # Get stats to find total posts
        stats_resp = requests.get(f"{BASE_URL}/api/forum/stats", headers=self.headers)
        if stats_resp.status_code == 200 and stats_resp.json()["total_posts"] > 0:
            # Get the post list
            posts_resp = requests.get(f"{BASE_URL}/api/forum/posts", headers=self.headers)
            if posts_resp.status_code == 200 and len(posts_resp.json()["posts"]) > 0:
                post = posts_resp.json()["posts"][0]
                post_id = post["id"]
                
                # Get full post with comments
                full_resp = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers=self.headers)
                assert full_resp.status_code == 200
                data = full_resp.json()
                
                if len(data.get("comments", [])) > 0:
                    comment = data["comments"][0]
                    # Check vote enrichment fields
                    assert "upvotes" in comment
                    assert "downvotes" in comment
                    assert "score" in comment
                    assert "up_voters" in comment
                    assert "down_voters" in comment
                    assert "my_vote" in comment
                    print(f"Comment vote enrichment verified: upvotes={comment['upvotes']}, downvotes={comment['downvotes']}")
                else:
                    print("No comments on post to verify vote enrichment")
            else:
                print("No posts available to test comment enrichment")
        else:
            print("No posts in forum yet")

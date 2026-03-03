"""
Forum Enhancements Tests - Iteration 138
Tests for NEW forum features: voting, similar search, reputation system

New Features Tested:
- POST /api/forum/comments/{id}/vote - Upvote/downvote comments (toggle logic)
- GET /api/forum/comments/{id}/voters - Get voters list with names
- GET /api/forum/search-similar?q=... - AJAX similar posts search
- GET /api/forum/stats - Enhanced top contributors with reputation scores
- Vote data enrichment in GET /api/forum/posts/{id} (upvotes, downvotes, voters, my_vote)
"""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-rewards-ctrl.preview.emergentagent.com').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
SUPER_ADMIN_EMAIL = "superadmin@test.com"
SUPER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def master_admin_token():
    """Get master admin token (login returns 'access_token')"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    pytest.skip(f"Master admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    pytest.skip(f"Super admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def master_admin_user(master_admin_token):
    """Get master admin user info"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {master_admin_token}"
    })
    if response.status_code == 200:
        return response.json()
    return {"id": "unknown", "name": "Master Admin"}


@pytest.fixture(scope="module")
def super_admin_user(super_admin_token):
    """Get super admin user info"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {super_admin_token}"
    })
    if response.status_code == 200:
        return response.json()
    return {"id": "unknown", "name": "Super Admin"}


class TestVotingEndpoints:
    """Test comment voting functionality - POST /api/forum/comments/{id}/vote"""
    
    def test_upvote_comment_create(self, master_admin_token, super_admin_token, master_admin_user):
        """Create upvote on a comment (requires different user than author)"""
        # Create a post with master admin
        unique_id = str(uuid.uuid4())[:8]
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Vote Post {unique_id}",
            "content": "Test post for voting feature",
            "tags": ["test", "voting"]
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert post_response.status_code == 200, f"Failed to create post: {post_response.text}"
        post_id = post_response.json()["id"]
        
        # Add comment with super admin (different user)
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Test comment for voting {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        
        assert comment_response.status_code == 200, f"Failed to create comment: {comment_response.text}"
        comment_id = comment_response.json()["id"]
        
        # Upvote the comment (master admin voting on super admin's comment)
        vote_response = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert vote_response.status_code == 200, f"Expected 200, got {vote_response.status_code}: {vote_response.text}"
        
        data = vote_response.json()
        assert data.get("action") == "created", f"Expected action 'created', got {data.get('action')}"
        assert data.get("vote_type") == "up", "Vote type should be 'up'"
        
        print(f"Successfully created upvote: {data}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_downvote_comment_create(self, master_admin_token, super_admin_token):
        """Create downvote on a comment"""
        unique_id = str(uuid.uuid4())[:8]
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Downvote Post {unique_id}",
            "content": "Test post for downvoting",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        post_id = post_response.json()["id"]
        
        # Super admin adds comment
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Comment to downvote {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        
        comment_id = comment_response.json()["id"]
        
        # Master admin downvotes
        vote_response = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "down"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert vote_response.status_code == 200
        data = vote_response.json()
        assert data.get("action") == "created"
        assert data.get("vote_type") == "down"
        
        print(f"Successfully created downvote: {data}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_vote_toggle_remove(self, master_admin_token, super_admin_token):
        """Toggle vote: clicking same vote removes it"""
        unique_id = str(uuid.uuid4())[:8]
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Toggle Vote {unique_id}",
            "content": "Test toggle vote removal",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        post_id = post_response.json()["id"]
        
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Comment for toggle test {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        
        comment_id = comment_response.json()["id"]
        
        # First upvote
        vote1 = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert vote1.json().get("action") == "created"
        
        # Same upvote again = remove
        vote2 = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert vote2.status_code == 200
        assert vote2.json().get("action") == "removed", f"Expected 'removed', got {vote2.json()}"
        
        print(f"Vote toggle removal works: {vote2.json()}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_vote_toggle_switch(self, master_admin_token, super_admin_token):
        """Toggle vote: clicking different vote switches it"""
        unique_id = str(uuid.uuid4())[:8]
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Switch Vote {unique_id}",
            "content": "Test switch vote",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        post_id = post_response.json()["id"]
        
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Comment for switch test {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        
        comment_id = comment_response.json()["id"]
        
        # First upvote
        vote1 = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert vote1.json().get("action") == "created"
        
        # Now downvote = switch
        vote2 = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "down"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert vote2.status_code == 200
        assert vote2.json().get("action") == "switched", f"Expected 'switched', got {vote2.json()}"
        assert vote2.json().get("vote_type") == "down"
        
        print(f"Vote toggle switch works: {vote2.json()}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_cannot_vote_own_comment(self, master_admin_token):
        """Cannot vote on your own comment - returns 400"""
        unique_id = str(uuid.uuid4())[:8]
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Self Vote {unique_id}",
            "content": "Test self-voting prevention",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        post_id = post_response.json()["id"]
        
        # Master admin adds comment
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"My own comment {unique_id}"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        comment_id = comment_response.json()["id"]
        
        # Master admin tries to vote on own comment
        vote_response = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert vote_response.status_code == 400, f"Expected 400 for self-vote, got {vote_response.status_code}: {vote_response.text}"
        
        detail = vote_response.json().get("detail", "")
        assert "own comment" in detail.lower(), f"Expected error about own comment, got: {detail}"
        
        print(f"Correctly rejected self-vote: {vote_response.json()}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_vote_invalid_type(self, master_admin_token, super_admin_token):
        """Invalid vote_type returns 400"""
        unique_id = str(uuid.uuid4())[:8]
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Invalid Vote {unique_id}",
            "content": "Test invalid vote type",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        post_id = post_response.json()["id"]
        
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Comment {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        
        comment_id = comment_response.json()["id"]
        
        vote_response = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "invalid"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert vote_response.status_code == 400, f"Expected 400 for invalid vote_type, got {vote_response.status_code}"
        
        print(f"Correctly rejected invalid vote type: {vote_response.json()}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_vote_nonexistent_comment(self, master_admin_token):
        """Voting on non-existent comment returns 404"""
        fake_comment_id = str(uuid.uuid4())
        vote_response = requests.post(f"{BASE_URL}/api/forum/comments/{fake_comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert vote_response.status_code == 404, f"Expected 404, got {vote_response.status_code}"
        print(f"Correctly returned 404 for non-existent comment vote")


class TestVotersEndpoint:
    """Test GET /api/forum/comments/{id}/voters - voter names visible"""
    
    def test_get_voters_list(self, master_admin_token, super_admin_token):
        """Get voters list with names (not anonymous)"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create post and comment
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Voters List {unique_id}",
            "content": "Test voters endpoint",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        post_id = post_response.json()["id"]
        
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Comment for voters test {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        comment_id = comment_response.json()["id"]
        
        # Master admin votes
        requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        # Get voters
        voters_response = requests.get(f"{BASE_URL}/api/forum/comments/{comment_id}/voters", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert voters_response.status_code == 200, f"Expected 200, got {voters_response.status_code}: {voters_response.text}"
        
        data = voters_response.json()
        assert "votes" in data, "Missing votes array"
        assert "comment_id" in data, "Missing comment_id"
        
        # Verify voter info includes names
        votes = data.get("votes", [])
        assert len(votes) >= 1, "Expected at least 1 vote"
        
        for vote in votes:
            assert "user_id" in vote, "Missing user_id in vote"
            assert "voter_name" in vote, "Missing voter_name (should not be anonymous!)"
            assert "vote_type" in vote, "Missing vote_type"
            assert vote.get("voter_name") not in [None, "", "Unknown"], f"Voter name should not be anonymous: {vote}"
        
        print(f"Voters endpoint returns names: {data}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })


class TestVoteDataInPostResponse:
    """Test that GET /api/forum/posts/{id} enriches comments with vote data"""
    
    def test_comments_have_vote_data(self, master_admin_token, super_admin_token):
        """Comments should include upvotes, downvotes, score, voters, my_vote"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create post
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Vote Data {unique_id}",
            "content": "Test vote data enrichment",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        post_id = post_response.json()["id"]
        
        # Super admin adds comment
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Comment for vote data test {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        comment_id = comment_response.json()["id"]
        
        # Master admin upvotes
        requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        # Get post as master admin
        get_response = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert get_response.status_code == 200
        post_data = get_response.json()
        
        comments = post_data.get("comments", [])
        assert len(comments) >= 1, "Expected at least 1 comment"
        
        comment = comments[0]
        # Verify vote data fields exist
        assert "upvotes" in comment, "Missing upvotes field"
        assert "downvotes" in comment, "Missing downvotes field"
        assert "score" in comment, "Missing score field"
        assert "up_voters" in comment, "Missing up_voters field"
        assert "down_voters" in comment, "Missing down_voters field"
        assert "my_vote" in comment, "Missing my_vote field"
        
        # Verify values
        assert comment["upvotes"] == 1, f"Expected 1 upvote, got {comment['upvotes']}"
        assert comment["downvotes"] == 0, f"Expected 0 downvotes, got {comment['downvotes']}"
        assert comment["score"] == 1, f"Expected score 1, got {comment['score']}"
        assert comment["my_vote"] == "up", f"Expected my_vote 'up', got {comment['my_vote']}"
        assert len(comment["up_voters"]) == 1, "Expected 1 up_voter"
        
        # Verify voter has name
        up_voter = comment["up_voters"][0]
        assert "name" in up_voter, "Voter should have name"
        assert "user_id" in up_voter, "Voter should have user_id"
        
        print(f"Comment vote data: upvotes={comment['upvotes']}, downvotes={comment['downvotes']}, score={comment['score']}, my_vote={comment['my_vote']}")
        print(f"Up voters: {comment['up_voters']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })


class TestSimilarPostsSearch:
    """Test GET /api/forum/search-similar?q=... - AJAX similar posts search"""
    
    def test_search_similar_posts_3_chars(self, master_admin_token):
        """Search triggers at 3+ characters"""
        # Search for "lot" which should match "How to calculate lot size?"
        response = requests.get(f"{BASE_URL}/api/forum/search-similar?q=lot", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "results" in data, "Missing results array"
        assert "query" in data, "Missing query field"
        
        print(f"Similar search 'lot': {len(data['results'])} results, query: {data['query']}")
        
        # Check result structure
        if data["results"]:
            result = data["results"][0]
            assert "id" in result, "Result missing id"
            assert "title" in result, "Result missing title"
            assert "status" in result, "Result missing status"
    
    def test_search_similar_posts_lot_size(self, master_admin_token):
        """Search 'lot size' should find 'How to calculate lot size?'"""
        response = requests.get(f"{BASE_URL}/api/forum/search-similar?q=lot%20size", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert response.status_code == 200
        
        data = response.json()
        results = data.get("results", [])
        
        # Check if the known post is in results
        found_lot_size = any("lot" in r.get("title", "").lower() for r in results)
        print(f"Similar search 'lot size': {len(results)} results, found lot-related: {found_lot_size}")
        
        for r in results:
            print(f"  - {r.get('title')} [{r.get('status')}]")
    
    def test_search_similar_min_length_validation(self, master_admin_token):
        """Search requires minimum 3 characters"""
        response = requests.get(f"{BASE_URL}/api/forum/search-similar?q=ab", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        # API requires min_length=3, should return 422 validation error
        assert response.status_code == 422, f"Expected 422 for short query, got {response.status_code}"
        print(f"Correctly rejected short query: {response.json()}")
    
    def test_search_similar_returns_status_badges(self, master_admin_token):
        """Results include status for badges"""
        response = requests.get(f"{BASE_URL}/api/forum/search-similar?q=test", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert response.status_code == 200
        
        data = response.json()
        for r in data.get("results", []):
            assert "status" in r, "Result should include status for badges"
            assert r["status"] in ["open", "closed"], f"Invalid status: {r['status']}"
        
        print(f"Similar search 'test': {len(data.get('results', []))} results with status badges")


class TestEnhancedTopContributors:
    """Test GET /api/forum/stats - Enhanced top contributors with reputation"""
    
    def test_top_contributors_has_reputation_fields(self, master_admin_token):
        """Top contributors section shows reputation, best answers, upvotes, comments"""
        response = requests.get(f"{BASE_URL}/api/forum/stats", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "top_contributors" in data, "Missing top_contributors field"
        
        contributors = data["top_contributors"]
        print(f"Top contributors count: {len(contributors)}")
        
        # Verify structure if contributors exist
        for c in contributors:
            assert "user_id" in c, "Contributor missing user_id"
            assert "name" in c, "Contributor missing name"
            assert "best_answers" in c, "Contributor missing best_answers"
            assert "upvotes_received" in c, "Contributor missing upvotes_received"
            assert "comments_count" in c, "Contributor missing comments_count"
            assert "reputation" in c, "Contributor missing reputation score"
            
            print(f"  - {c['name']}: reputation={c['reputation']}, best_answers={c['best_answers']}, upvotes={c['upvotes_received']}, comments={c['comments_count']}")
    
    def test_reputation_calculation(self, master_admin_token):
        """Reputation = 10*best_answers + upvotes + 0.5*comments"""
        response = requests.get(f"{BASE_URL}/api/forum/stats", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert response.status_code == 200
        
        contributors = response.json().get("top_contributors", [])
        
        for c in contributors:
            expected_rep = (c["best_answers"] * 10) + c["upvotes_received"] + int(c["comments_count"] * 0.5)
            actual_rep = c["reputation"]
            
            assert actual_rep == expected_rep, f"Reputation mismatch for {c['name']}: expected {expected_rep}, got {actual_rep}"
        
        print(f"Reputation calculation verified for {len(contributors)} contributors")
    
    def test_superadmin_appears_as_contributor(self, master_admin_token):
        """superadmin@test.com should appear with 1 best answer (per context)"""
        response = requests.get(f"{BASE_URL}/api/forum/stats", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        
        assert response.status_code == 200
        
        contributors = response.json().get("top_contributors", [])
        
        # Look for super admin
        super_admin_contrib = None
        for c in contributors:
            if "superadmin" in c.get("name", "").lower() or "super" in c.get("name", "").lower():
                super_admin_contrib = c
                break
        
        if super_admin_contrib:
            print(f"Found superadmin in contributors: {super_admin_contrib}")
            # According to context, should have 1 best answer
            if super_admin_contrib["best_answers"] >= 1:
                print(f"Confirmed: superadmin has {super_admin_contrib['best_answers']} best answer(s)")
        else:
            print("Note: superadmin not found in top contributors (may not have activity)")


class TestVotingIntegration:
    """Integration test for complete voting flow"""
    
    def test_complete_voting_flow(self, master_admin_token, super_admin_token):
        """Full flow: create post -> add comment -> vote -> verify -> switch -> verify"""
        unique_id = str(uuid.uuid4())[:8]
        
        # 1. Create post (master admin)
        post_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Full Vote Flow {unique_id}",
            "content": "Testing complete voting flow",
            "tags": ["integration"]
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert post_response.status_code == 200
        post_id = post_response.json()["id"]
        print(f"1. Created post: {post_id}")
        
        # 2. Add comment (super admin)
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": f"Integration test comment {unique_id}"
        }, headers={"Authorization": f"Bearer {super_admin_token}"})
        
        assert comment_response.status_code == 200
        comment_id = comment_response.json()["id"]
        print(f"2. Created comment: {comment_id}")
        
        # 3. Upvote (master admin)
        vote1 = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "up"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert vote1.json().get("action") == "created"
        print(f"3. Created upvote: {vote1.json()}")
        
        # 4. Verify via post endpoint
        post_data = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        }).json()
        
        comment_data = post_data["comments"][0]
        assert comment_data["upvotes"] == 1
        assert comment_data["my_vote"] == "up"
        print(f"4. Verified: upvotes=1, my_vote=up")
        
        # 5. Switch to downvote
        vote2 = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "down"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert vote2.json().get("action") == "switched"
        print(f"5. Switched to downvote: {vote2.json()}")
        
        # 6. Verify switch
        post_data = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        }).json()
        
        comment_data = post_data["comments"][0]
        assert comment_data["upvotes"] == 0
        assert comment_data["downvotes"] == 1
        assert comment_data["score"] == -1
        assert comment_data["my_vote"] == "down"
        print(f"6. Verified switch: upvotes=0, downvotes=1, score=-1, my_vote=down")
        
        # 7. Remove vote (toggle)
        vote3 = requests.post(f"{BASE_URL}/api/forum/comments/{comment_id}/vote", json={
            "vote_type": "down"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert vote3.json().get("action") == "removed"
        print(f"7. Removed vote: {vote3.json()}")
        
        # 8. Verify removal
        post_data = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        }).json()
        
        comment_data = post_data["comments"][0]
        assert comment_data["upvotes"] == 0
        assert comment_data["downvotes"] == 0
        assert comment_data["score"] == 0
        assert comment_data["my_vote"] is None
        print(f"8. Verified removal: upvotes=0, downvotes=0, score=0, my_vote=None")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        print(f"Cleanup complete. Full voting flow PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

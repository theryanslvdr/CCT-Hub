"""
Forum Feature Tests - Iteration 137
Tests for Community Forum ticketing system with Q&A and points awards
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
    """Get master admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    pytest.skip(f"Master admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def master_admin_user(master_admin_token):
    """Get master admin user info"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {master_admin_token}"
    })
    if response.status_code == 200:
        return response.json()
    return {"id": "unknown", "full_name": "Master Admin"}


class TestForumStats:
    """Test forum statistics endpoint"""
    
    def test_get_forum_stats(self, master_admin_token):
        """GET /api/forum/stats - Get forum statistics"""
        response = requests.get(f"{BASE_URL}/api/forum/stats", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total_posts" in data, "Missing total_posts field"
        assert "open_posts" in data, "Missing open_posts field"
        assert "closed_posts" in data, "Missing closed_posts field"
        assert "total_comments" in data, "Missing total_comments field"
        assert "top_contributors" in data, "Missing top_contributors field"
        
        print(f"Forum stats: {data['total_posts']} total posts, {data['open_posts']} open, {data['closed_posts']} closed")


class TestForumPostsList:
    """Test forum posts list endpoint"""
    
    def test_list_posts_no_filter(self, master_admin_token):
        """GET /api/forum/posts - List all posts without filter"""
        response = requests.get(f"{BASE_URL}/api/forum/posts", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "posts" in data, "Missing posts array"
        assert "total" in data, "Missing total count"
        assert "page" in data, "Missing page number"
        assert "page_size" in data, "Missing page_size"
        
        print(f"Listed {len(data['posts'])} posts, total: {data['total']}")
    
    def test_list_posts_filter_open(self, master_admin_token):
        """GET /api/forum/posts?status=open - List open posts only"""
        response = requests.get(f"{BASE_URL}/api/forum/posts?status=open", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        for post in data.get("posts", []):
            assert post.get("status") == "open", f"Expected open post, got {post.get('status')}"
        
        print(f"Listed {len(data['posts'])} open posts")
    
    def test_list_posts_filter_closed(self, master_admin_token):
        """GET /api/forum/posts?status=closed - List closed posts only"""
        response = requests.get(f"{BASE_URL}/api/forum/posts?status=closed", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        for post in data.get("posts", []):
            assert post.get("status") == "closed", f"Expected closed post, got {post.get('status')}"
        
        print(f"Listed {len(data['posts'])} closed posts")
    
    def test_list_posts_search(self, master_admin_token):
        """GET /api/forum/posts?search=test - Search posts"""
        response = requests.get(f"{BASE_URL}/api/forum/posts?search=trading", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Search results: {len(data['posts'])} posts matching 'trading'")


class TestForumPostCRUD:
    """Test forum post creation, retrieval, and deletion"""
    
    def test_create_post(self, master_admin_token):
        """POST /api/forum/posts - Create a new post"""
        unique_id = str(uuid.uuid4())[:8]
        post_data = {
            "title": f"TEST_Forum Post {unique_id}",
            "content": f"This is a test post created for automated testing. ID: {unique_id}",
            "tags": ["test", "automation"]
        }
        
        response = requests.post(f"{BASE_URL}/api/forum/posts", json=post_data, headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Missing post id"
        assert data["title"] == post_data["title"], "Title mismatch"
        assert data["content"] == post_data["content"], "Content mismatch"
        assert data["status"] == "open", "New post should be open"
        assert data.get("author_name"), "Missing author_name"
        
        print(f"Created post: {data['id']} - {data['title']}")
        return data
    
    def test_get_post_by_id(self, master_admin_token):
        """GET /api/forum/posts/{id} - Get post with comments"""
        # First create a post
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Get Post {unique_id}",
            "content": "Test content for retrieval",
            "tags": ["test"]
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert create_response.status_code == 200, f"Failed to create post: {create_response.text}"
        post_id = create_response.json()["id"]
        
        # Now get the post
        response = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["id"] == post_id, "Post ID mismatch"
        assert "comments" in data, "Missing comments array"
        assert "views" in data, "Missing views count"
        assert data.get("author_name"), "Missing author_name"
        
        print(f"Retrieved post: {data['id']} with {len(data.get('comments', []))} comments, {data.get('views')} views")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_delete_post(self, master_admin_token):
        """DELETE /api/forum/posts/{id} - Delete a post"""
        # First create a post
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Delete Post {unique_id}",
            "content": "Test content for deletion",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert create_response.status_code == 200, f"Failed to create post: {create_response.text}"
        post_id = create_response.json()["id"]
        
        # Delete the post
        response = requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing message in response"
        
        # Verify post is gone
        verify_response = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert verify_response.status_code == 404, f"Post should be deleted, got {verify_response.status_code}"
        
        print(f"Deleted post: {post_id}")


class TestForumComments:
    """Test forum comment functionality"""
    
    def test_add_comment_to_open_post(self, master_admin_token):
        """POST /api/forum/posts/{id}/comments - Add comment to open post"""
        # Create a post
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Comment Post {unique_id}",
            "content": "Test post for comments",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert create_response.status_code == 200, f"Failed to create post: {create_response.text}"
        post_id = create_response.json()["id"]
        
        # Add comment
        comment_data = {"content": f"This is a test comment. ID: {unique_id}"}
        response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json=comment_data, headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Missing comment id"
        assert data["content"] == comment_data["content"], "Content mismatch"
        assert data.get("author_name"), "Missing author_name"
        
        print(f"Added comment: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_cannot_comment_on_closed_post(self, master_admin_token):
        """Cannot add comments to closed posts"""
        # Create a post
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Closed Post {unique_id}",
            "content": "Test post to be closed",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert create_response.status_code == 200, f"Failed to create post: {create_response.text}"
        post_id = create_response.json()["id"]
        
        # Close the post
        close_response = requests.put(f"{BASE_URL}/api/forum/posts/{post_id}/close", json={
            "best_answer_id": None,
            "active_collaborator_ids": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert close_response.status_code == 200, f"Failed to close post: {close_response.text}"
        
        # Try to add comment
        response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": "This should fail"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert response.status_code == 400, f"Expected 400 for closed post comment, got {response.status_code}"
        
        print(f"Correctly rejected comment on closed post")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })


class TestForumBestAnswer:
    """Test best answer marking functionality"""
    
    def test_mark_best_answer(self, master_admin_token, master_admin_user):
        """PUT /api/forum/posts/{id}/best-answer/{comment_id} - Mark best answer"""
        # Create a post
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Best Answer {unique_id}",
            "content": "Test post for best answer feature",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert create_response.status_code == 200, f"Failed to create post: {create_response.text}"
        post = create_response.json()
        post_id = post["id"]
        author_id = post.get("author_id")
        
        # Add a comment (same user - will test that OP cannot mark own comment)
        comment_response = requests.post(f"{BASE_URL}/api/forum/posts/{post_id}/comments", json={
            "content": "Test answer"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert comment_response.status_code == 200, f"Failed to add comment: {comment_response.text}"
        comment_id = comment_response.json()["id"]
        comment_author_id = comment_response.json().get("author_id")
        
        # If the comment is from same user (OP), best answer should not work
        # Based on the code, OP's own comment cannot be best answer
        if comment_author_id == author_id:
            # This is expected - we're logged as master admin and posted comment as same user
            # Best answer API will work but points won't be awarded
            print(f"Note: Comment author is OP, best answer will be marked but no points awarded")
        
        # Mark as best answer
        response = requests.put(f"{BASE_URL}/api/forum/posts/{post_id}/best-answer/{comment_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing message in response"
        assert data.get("comment_id") == comment_id, "Comment ID mismatch"
        
        # Verify post has best_answer_id set
        get_response = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert get_response.status_code == 200
        assert get_response.json().get("best_answer_id") == comment_id, "best_answer_id not set on post"
        
        print(f"Marked best answer: {comment_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })


class TestForumClosePost:
    """Test post closing and points awarding"""
    
    def test_close_post(self, master_admin_token):
        """PUT /api/forum/posts/{id}/close - Close post with points awards"""
        # Create a post
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Close Post {unique_id}",
            "content": "Test post for closing",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert create_response.status_code == 200, f"Failed to create post: {create_response.text}"
        post_id = create_response.json()["id"]
        
        # Close the post
        response = requests.put(f"{BASE_URL}/api/forum/posts/{post_id}/close", json={
            "best_answer_id": None,
            "active_collaborator_ids": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing message in response"
        assert "points_awarded" in data, "Missing points_awarded array"
        
        # Verify post is closed
        get_response = requests.get(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert get_response.status_code == 200
        assert get_response.json().get("status") == "closed", "Post should be closed"
        
        print(f"Closed post: {post_id}, points awarded: {data.get('points_awarded')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
    
    def test_cannot_close_already_closed_post(self, master_admin_token):
        """Cannot close an already closed post"""
        # Create and close a post
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/forum/posts", json={
            "title": f"TEST_Double Close {unique_id}",
            "content": "Test post",
            "tags": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        
        assert create_response.status_code == 200, f"Failed to create post: {create_response.text}"
        post_id = create_response.json()["id"]
        
        # Close first time
        close_response = requests.put(f"{BASE_URL}/api/forum/posts/{post_id}/close", json={
            "best_answer_id": None,
            "active_collaborator_ids": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert close_response.status_code == 200, f"First close failed: {close_response.text}"
        
        # Try to close again
        response = requests.put(f"{BASE_URL}/api/forum/posts/{post_id}/close", json={
            "best_answer_id": None,
            "active_collaborator_ids": []
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert response.status_code == 400, f"Expected 400 for double close, got {response.status_code}"
        
        print(f"Correctly rejected double close attempt")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })


class TestForumPostNotFound:
    """Test error handling for non-existent posts"""
    
    def test_get_nonexistent_post(self, master_admin_token):
        """GET /api/forum/posts/{id} - Should return 404 for non-existent post"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/forum/posts/{fake_id}", headers={
            "Authorization": f"Bearer {master_admin_token}"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"Correctly returned 404 for non-existent post")
    
    def test_comment_nonexistent_post(self, master_admin_token):
        """POST /api/forum/posts/{id}/comments - Should return 404 for non-existent post"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/forum/posts/{fake_id}/comments", json={
            "content": "Test comment"
        }, headers={"Authorization": f"Bearer {master_admin_token}"})
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"Correctly returned 404 for comment on non-existent post")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

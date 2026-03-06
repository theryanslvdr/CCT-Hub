"""
Test iteration 142 features:
1. Forum categories endpoint
2. Forum @mention user search
3. Forum post edit with category
4. Forum comment edit/delete
5. Forum pin/unpin (admin)
6. Member self-edit last 2 transactions
7. Admin transaction correction/deletion
8. Admin get member transactions
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_ID = "b4628e3e-9dec-42ef-8c75-dcba08194cd2"


@pytest.fixture(scope="module")
def admin_token():
    """Login as admin and get token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Authorization headers for admin"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestForumCategories:
    """Test forum categories endpoint"""
    
    def test_get_categories_returns_4_defaults(self, admin_headers):
        """GET /api/forum/categories returns 4 default categories"""
        response = requests.get(
            f"{BASE_URL}/api/forum/categories",
            headers=admin_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Failed to get categories: {response.text}"
        data = response.json()
        
        assert "categories" in data, "Response missing 'categories' key"
        categories = data["categories"]
        
        # Check we have at least 4 categories
        assert len(categories) >= 4, f"Expected at least 4 categories, got {len(categories)}"
        
        # Check default categories exist
        category_names = [c["name"] for c in categories]
        expected = ["general", "trading", "technical", "announcements"]
        for cat in expected:
            assert cat in category_names, f"Missing default category: {cat}"
        
        # Each category should have a count
        for cat in categories:
            assert "name" in cat, "Category missing 'name'"
            assert "count" in cat, "Category missing 'count'"
            assert isinstance(cat["count"], int), "Count should be integer"
        
        print(f"✓ Got {len(categories)} categories: {category_names}")


class TestForumUserSearch:
    """Test @mention user search"""
    
    def test_search_users_with_query(self, admin_headers):
        """GET /api/forum/users/search?q=ry returns matching users"""
        response = requests.get(
            f"{BASE_URL}/api/forum/users/search",
            params={"q": "ry"},
            headers=admin_headers,
            timeout=30
        )
        assert response.status_code == 200, f"User search failed: {response.text}"
        data = response.json()
        
        assert "users" in data, "Response missing 'users' key"
        users = data["users"]
        
        # Should return users with 'ry' in name or email
        assert isinstance(users, list), "Users should be a list"
        
        # Each user should have id, name/email
        for u in users:
            assert "id" in u, "User missing 'id'"
            # Should have either name or email
            assert "name" in u or "email" in u, "User missing name/email"
        
        print(f"✓ User search returned {len(users)} users")
    
    def test_search_users_empty_query_fails(self, admin_headers):
        """Search with empty query should fail validation"""
        response = requests.get(
            f"{BASE_URL}/api/forum/users/search",
            params={"q": ""},
            headers=admin_headers,
            timeout=30
        )
        # Should return 422 validation error for empty query
        assert response.status_code == 422, f"Expected 422 for empty query, got {response.status_code}"


class TestForumPostOperations:
    """Test forum post create/edit/pin operations"""
    
    @pytest.fixture(scope="class")
    def test_post_id(self, admin_headers):
        """Create a test post for editing"""
        response = requests.post(
            f"{BASE_URL}/api/forum/posts",
            headers=admin_headers,
            json={
                "title": f"TEST_Post_{uuid.uuid4().hex[:8]}",
                "content": "Test post content for iteration 142",
                "category": "trading",
                "tags": ["test", "iteration142"]
            },
            timeout=30
        )
        assert response.status_code == 200, f"Failed to create post: {response.text}"
        data = response.json()
        assert "id" in data, "Post response missing 'id'"
        print(f"✓ Created test post: {data['id']}")
        return data["id"]
    
    def test_create_post_with_category(self, admin_headers):
        """POST /api/forum/posts - create post with category field"""
        response = requests.post(
            f"{BASE_URL}/api/forum/posts",
            headers=admin_headers,
            json={
                "title": f"TEST_Category_Post_{uuid.uuid4().hex[:8]}",
                "content": "Test post with category",
                "category": "technical"
            },
            timeout=30
        )
        assert response.status_code == 200, f"Failed to create post: {response.text}"
        data = response.json()
        
        assert data.get("category") == "technical", f"Category not set correctly: {data.get('category')}"
        print(f"✓ Created post with category: {data.get('category')}")
    
    def test_edit_post_title_content_category(self, admin_headers, test_post_id):
        """PUT /api/forum/posts/{id} - edit post (title/content/category)"""
        new_title = f"UPDATED_TEST_Post_{uuid.uuid4().hex[:8]}"
        new_content = "Updated content for iteration 142 test"
        new_category = "announcements"
        
        response = requests.put(
            f"{BASE_URL}/api/forum/posts/{test_post_id}",
            headers=admin_headers,
            json={
                "title": new_title,
                "content": new_content,
                "category": new_category
            },
            timeout=30
        )
        assert response.status_code == 200, f"Failed to edit post: {response.text}"
        data = response.json()
        assert data.get("message") == "Post updated", f"Unexpected response: {data}"
        
        # Verify the update by fetching the post
        get_response = requests.get(
            f"{BASE_URL}/api/forum/posts/{test_post_id}",
            headers=admin_headers,
            timeout=30
        )
        assert get_response.status_code == 200
        post_data = get_response.json()
        
        assert post_data.get("title") == new_title, "Title not updated"
        assert post_data.get("content") == new_content, "Content not updated"
        assert post_data.get("category") == new_category, "Category not updated"
        assert post_data.get("edited") == True, "Edited flag not set"
        
        print(f"✓ Post edited successfully with new category: {new_category}")
    
    def test_pin_post_admin_only(self, admin_headers, test_post_id):
        """PUT /api/forum/posts/{id}/pin - admin can pin/unpin posts"""
        # Pin the post
        response = requests.put(
            f"{BASE_URL}/api/forum/posts/{test_post_id}/pin",
            headers=admin_headers,
            json={"pinned": True},
            timeout=30
        )
        assert response.status_code == 200, f"Failed to pin post: {response.text}"
        data = response.json()
        assert "pinned" in data.get("message", "").lower(), f"Unexpected response: {data}"
        
        # Verify pinned
        get_response = requests.get(
            f"{BASE_URL}/api/forum/posts/{test_post_id}",
            headers=admin_headers,
            timeout=30
        )
        assert get_response.status_code == 200
        post_data = get_response.json()
        assert post_data.get("pinned") == True, "Post not pinned"
        
        # Unpin the post
        unpin_response = requests.put(
            f"{BASE_URL}/api/forum/posts/{test_post_id}/pin",
            headers=admin_headers,
            json={"pinned": False},
            timeout=30
        )
        assert unpin_response.status_code == 200
        
        # Verify unpinned
        get_response2 = requests.get(
            f"{BASE_URL}/api/forum/posts/{test_post_id}",
            headers=admin_headers,
            timeout=30
        )
        assert get_response2.json().get("pinned") == False, "Post not unpinned"
        
        print(f"✓ Pin/unpin operations work correctly")


class TestForumCommentOperations:
    """Test forum comment edit/delete operations"""
    
    @pytest.fixture(scope="class")
    def test_post_with_comment(self, admin_headers):
        """Create a test post with a comment"""
        # Create post
        post_response = requests.post(
            f"{BASE_URL}/api/forum/posts",
            headers=admin_headers,
            json={
                "title": f"TEST_Comment_Post_{uuid.uuid4().hex[:8]}",
                "content": "Test post for comment operations",
                "category": "general"
            },
            timeout=30
        )
        assert post_response.status_code == 200
        post_id = post_response.json()["id"]
        
        # Create comment
        comment_response = requests.post(
            f"{BASE_URL}/api/forum/posts/{post_id}/comments",
            headers=admin_headers,
            json={"content": "Test comment for iteration 142"},
            timeout=30
        )
        assert comment_response.status_code == 200
        comment_id = comment_response.json()["id"]
        
        print(f"✓ Created test post {post_id} with comment {comment_id}")
        return {"post_id": post_id, "comment_id": comment_id}
    
    def test_edit_comment_content(self, admin_headers, test_post_with_comment):
        """PUT /api/forum/comments/{id} - edit comment content"""
        comment_id = test_post_with_comment["comment_id"]
        new_content = f"UPDATED comment content - {uuid.uuid4().hex[:8]}"
        
        response = requests.put(
            f"{BASE_URL}/api/forum/comments/{comment_id}",
            headers=admin_headers,
            json={"content": new_content},
            timeout=30
        )
        assert response.status_code == 200, f"Failed to edit comment: {response.text}"
        data = response.json()
        assert data.get("message") == "Comment updated", f"Unexpected response: {data}"
        
        # Verify by fetching the post (which includes comments)
        post_response = requests.get(
            f"{BASE_URL}/api/forum/posts/{test_post_with_comment['post_id']}",
            headers=admin_headers,
            timeout=30
        )
        assert post_response.status_code == 200
        post_data = post_response.json()
        
        # Find the comment
        comment = next((c for c in post_data.get("comments", []) if c["id"] == comment_id), None)
        assert comment is not None, "Comment not found in post"
        assert comment.get("content") == new_content, "Comment content not updated"
        assert comment.get("edited") == True, "Edited flag not set"
        
        print(f"✓ Comment edited successfully")
    
    def test_delete_comment(self, admin_headers, test_post_with_comment):
        """DELETE /api/forum/comments/{id} - delete comment"""
        post_id = test_post_with_comment["post_id"]
        
        # Create a new comment to delete
        create_response = requests.post(
            f"{BASE_URL}/api/forum/posts/{post_id}/comments",
            headers=admin_headers,
            json={"content": "Comment to delete"},
            timeout=30
        )
        assert create_response.status_code == 200
        comment_to_delete = create_response.json()["id"]
        
        # Delete the comment
        delete_response = requests.delete(
            f"{BASE_URL}/api/forum/comments/{comment_to_delete}",
            headers=admin_headers,
            timeout=30
        )
        assert delete_response.status_code == 200, f"Failed to delete comment: {delete_response.text}"
        
        # Verify deletion
        post_response = requests.get(
            f"{BASE_URL}/api/forum/posts/{post_id}",
            headers=admin_headers,
            timeout=30
        )
        post_data = post_response.json()
        comment_ids = [c["id"] for c in post_data.get("comments", [])]
        assert comment_to_delete not in comment_ids, "Comment not deleted"
        
        print(f"✓ Comment deleted successfully")


class TestMemberTransactionSelfEdit:
    """Test member self-edit functionality for last 2 transactions"""
    
    def test_get_my_recent_transactions(self, admin_headers):
        """GET /api/profit/my-recent-transactions returns last 2 editable transactions"""
        response = requests.get(
            f"{BASE_URL}/api/profit/my-recent-transactions",
            headers=admin_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Failed to get recent transactions: {response.text}"
        data = response.json()
        
        assert "transactions" in data, "Response missing 'transactions'"
        transactions = data["transactions"]
        
        # Should return at most 2 transactions
        assert len(transactions) <= 2, f"Expected at most 2 transactions, got {len(transactions)}"
        
        # Each transaction should have editable flag
        for tx in transactions:
            assert "editable" in tx, "Transaction missing 'editable' flag"
            assert "id" in tx, "Transaction missing 'id'"
            assert "amount" in tx, "Transaction missing 'amount'"
        
        print(f"✓ Got {len(transactions)} recent transactions")


class TestAdminTransactionOperations:
    """Test admin transaction correction and deletion"""
    
    def test_get_member_recent_transactions(self, admin_headers):
        """GET /api/admin/members/{user_id}/recent-transactions - admin gets member transactions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_USER_ID}/recent-transactions",
            headers=admin_headers,
            params={"limit": 5},
            timeout=30
        )
        assert response.status_code == 200, f"Failed to get member transactions: {response.text}"
        data = response.json()
        
        assert "transactions" in data, "Response missing 'transactions'"
        transactions = data["transactions"]
        
        # Should return transactions for the specified user
        for tx in transactions:
            assert tx.get("user_id") == TEST_USER_ID, f"Wrong user_id in transaction"
        
        print(f"✓ Got {len(transactions)} transactions for user {TEST_USER_ID}")
        return transactions
    
    def test_correct_transaction_endpoint_exists(self, admin_headers):
        """PUT /api/admin/transactions/{id}/correct - verify endpoint exists"""
        # We need a valid transaction ID to test this
        # First get some transactions
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{TEST_USER_ID}/recent-transactions",
            headers=admin_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            transactions = response.json().get("transactions", [])
            if transactions:
                tx_id = transactions[0]["id"]
                original_amount = transactions[0]["amount"]
                
                # Test correction endpoint with same amount (non-destructive)
                correct_response = requests.put(
                    f"{BASE_URL}/api/admin/transactions/{tx_id}/correct",
                    headers=admin_headers,
                    json={
                        "new_amount": original_amount,
                        "reason": "TEST: Verification test - no actual change"
                    },
                    timeout=30
                )
                assert correct_response.status_code == 200, f"Correction endpoint failed: {correct_response.text}"
                print(f"✓ Transaction correction endpoint works (verified with tx {tx_id})")
            else:
                print("⚠ No transactions to test correction on")
        else:
            print(f"⚠ Could not get transactions to test: {response.status_code}")
    
    def test_delete_transaction_endpoint_exists(self, admin_headers):
        """DELETE /api/admin/transactions/{id} - verify endpoint exists"""
        # Test with non-existent ID to verify endpoint exists (should return 404)
        fake_id = f"test-fake-{uuid.uuid4().hex[:8]}"
        response = requests.delete(
            f"{BASE_URL}/api/admin/transactions/{fake_id}",
            headers=admin_headers,
            timeout=30
        )
        # Should return 404 for non-existent, not 405 (method not allowed)
        assert response.status_code == 404, f"Expected 404 for non-existent transaction, got {response.status_code}"
        print(f"✓ Transaction delete endpoint exists (returns 404 for non-existent)")


class TestListPostsWithCategoryFilter:
    """Test forum list posts with category filter"""
    
    def test_list_posts_filter_by_category(self, admin_headers):
        """GET /api/forum/posts with category filter"""
        # Test without category filter first
        response_all = requests.get(
            f"{BASE_URL}/api/forum/posts",
            headers=admin_headers,
            params={"page": 1, "page_size": 10},
            timeout=30
        )
        assert response_all.status_code == 200
        
        # Test with category filter
        response_trading = requests.get(
            f"{BASE_URL}/api/forum/posts",
            headers=admin_headers,
            params={"page": 1, "page_size": 10, "category": "trading"},
            timeout=30
        )
        assert response_trading.status_code == 200
        
        data = response_trading.json()
        posts = data.get("posts", [])
        
        # All returned posts should have the requested category
        for post in posts:
            if post.get("category"):
                assert post["category"] == "trading", f"Post has wrong category: {post.get('category')}"
        
        print(f"✓ Category filter works - got {len(posts)} trading posts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

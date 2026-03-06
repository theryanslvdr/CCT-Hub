"""Comprehensive tests for /api/forum/* endpoints (forum.py)."""
import pytest
import requests


class TestForumPosts:
    """GET /api/forum/posts"""

    def test_posts_list(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/forum/posts", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "posts" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["posts"], list)

    def test_posts_pagination(self, base_url, admin_headers):
        resp = requests.get(
            f"{base_url}/api/forum/posts",
            headers=admin_headers,
            params={"page": 1, "page_size": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["posts"]) <= 2

    def test_posts_no_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/forum/posts")
        assert resp.status_code in [401, 403]


class TestForumCRUD:
    """Create, read, update, delete forum posts."""

    def test_create_and_read_post(self, base_url, admin_headers):
        # Create a post
        resp = requests.post(
            f"{base_url}/api/forum/posts",
            headers=admin_headers,
            json={
                "title": "Pytest Test Post",
                "content": "This is an automated test post.",
                "tags": ["test"],
                "category": "general",
            },
        )
        assert resp.status_code in [200, 201], f"Create post failed: {resp.text}"
        post = resp.json()
        post_id = post.get("id") or post.get("post_id")
        assert post_id, "No post ID returned"

        # Read the post
        resp2 = requests.get(
            f"{base_url}/api/forum/posts/{post_id}",
            headers=admin_headers,
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data.get("title") == "Pytest Test Post" or data.get("post", {}).get("title") == "Pytest Test Post"

        # Cleanup — delete the post
        resp3 = requests.delete(
            f"{base_url}/api/forum/posts/{post_id}",
            headers=admin_headers,
        )
        assert resp3.status_code in [200, 204]

    def test_create_post_missing_fields(self, base_url, admin_headers):
        resp = requests.post(
            f"{base_url}/api/forum/posts",
            headers=admin_headers,
            json={},
        )
        assert resp.status_code == 422


class TestForumComments:
    """Comment operations on forum posts."""

    @pytest.fixture()
    def test_post_id(self, base_url, admin_headers):
        """Create a temporary post for comment tests."""
        resp = requests.post(
            f"{base_url}/api/forum/posts",
            headers=admin_headers,
            json={
                "title": "Comment Test Post",
                "content": "Temp post for comment testing.",
                "tags": ["test"],
                "category": "general",
            },
        )
        assert resp.status_code in [200, 201]
        post = resp.json()
        post_id = post.get("id") or post.get("post_id")
        yield post_id
        # Cleanup
        requests.delete(f"{base_url}/api/forum/posts/{post_id}", headers=admin_headers)

    def test_add_comment(self, base_url, admin_headers, test_post_id):
        resp = requests.post(
            f"{base_url}/api/forum/posts/{test_post_id}/comments",
            headers=admin_headers,
            json={"content": "This is a pytest comment."},
        )
        assert resp.status_code in [200, 201], f"Add comment failed: {resp.text}"
        comment = resp.json()
        assert comment.get("content") == "This is a pytest comment." or "id" in comment

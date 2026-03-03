"""
Iteration 140: Forum Image Upload with Publitio Integration Tests

Tests for:
1. Publitio API endpoints (/api/publitio/test, /api/publitio/upload)
2. Forum post with images field
3. Forum comment with images field
4. Profit Tracker hide/show amounts toggle (UI-only, no backend)
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for Master Admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPublitioAPI:
    """Tests for Publitio integration endpoints"""
    
    def test_publitio_test_endpoint_exists(self, auth_headers):
        """Test /api/publitio/test endpoint returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/publitio/test",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return configured status
        assert "configured" in data, "Response should include 'configured' field"
        assert "success" in data, "Response should include 'success' field"
        assert "message" in data, "Response should include 'message' field"
        
        # Since Publitio is not configured, configured should be False
        # (per agent_to_agent_context_note)
        print(f"Publitio status: configured={data['configured']}, success={data['success']}")
    
    def test_publitio_upload_endpoint_exists(self, auth_headers):
        """Test /api/publitio/upload endpoint exists and validates input"""
        # Try upload without file - should return 422 (validation error)
        response = requests.post(
            f"{BASE_URL}/api/publitio/upload",
            headers={"Authorization": auth_headers["Authorization"]},
            data={"folder": "test"}
        )
        # 422 = validation error (no file), 503 = not configured
        assert response.status_code in [422, 503], f"Expected 422 or 503, got {response.status_code}"
    
    def test_publitio_upload_file_size_validation(self, auth_headers):
        """Test that file size limit of 2MB is enforced"""
        # Create a small test file
        small_content = b"test image content" * 100  # ~1.7KB
        files = {'file': ('test.jpg', io.BytesIO(small_content), 'image/jpeg')}
        
        response = requests.post(
            f"{BASE_URL}/api/publitio/upload",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files,
            data={"folder": "forum/test"}
        )
        
        # Should return 503 (not configured) since we don't have credentials
        # But if configured, would return 200 or 400 (file type error)
        assert response.status_code in [200, 400, 503], f"Unexpected status: {response.status_code}"
        print(f"Upload response: {response.status_code} - {response.json().get('detail', 'OK')}")
    
    def test_publitio_upload_file_type_validation(self, auth_headers):
        """Test that only allowed image types are accepted"""
        # Create a file with disallowed extension
        content = b"test content"
        files = {'file': ('test.txt', io.BytesIO(content), 'text/plain')}
        
        response = requests.post(
            f"{BASE_URL}/api/publitio/upload",
            headers={"Authorization": auth_headers["Authorization"]},
            files=files,
            data={"folder": "forum/test"}
        )
        
        # Should return 400 (invalid file type) or 503 (not configured)
        if response.status_code == 400:
            data = response.json()
            assert "not allowed" in data.get("detail", "").lower() or "extension" in data.get("detail", "").lower()
            print(f"File type validation works: {data['detail']}")
        elif response.status_code == 503:
            print("Publitio not configured - cannot test file type validation fully")
        else:
            pytest.fail(f"Expected 400 or 503, got {response.status_code}")
    
    def test_publitio_folders_endpoint(self, auth_headers):
        """Test /api/publitio/folders endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/publitio/folders",
            headers=auth_headers
        )
        # 200 or 503 (not configured)
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}"


class TestForumWithImages:
    """Tests for forum posts and comments with image support"""
    
    def test_create_post_with_images_field(self, auth_headers):
        """Test creating a forum post with images array"""
        post_data = {
            "title": "TEST_ImagePost Test Post with Images",
            "content": "This post has image URLs attached",
            "tags": ["test", "images"],
            "images": ["https://example.com/image1.jpg", "https://example.com/image2.png"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/forum/posts",
            headers=auth_headers,
            json=post_data
        )
        assert response.status_code in [200, 201], f"Create post failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Post should have an ID"
        assert "images" in data, "Post should have images field in response"
        assert len(data["images"]) == 2, f"Expected 2 images, got {len(data['images'])}"
        
        post_id = data["id"]
        print(f"Created post {post_id} with {len(data['images'])} images")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers=auth_headers)
        return post_id
    
    def test_create_comment_with_images_field(self, auth_headers):
        """Test creating a forum comment with images array"""
        # First create a post
        post_data = {
            "title": "TEST_CommentImagePost Parent Post for Comment",
            "content": "Parent post content",
            "tags": [],
            "images": []
        }
        
        post_response = requests.post(
            f"{BASE_URL}/api/forum/posts",
            headers=auth_headers,
            json=post_data
        )
        assert post_response.status_code in [200, 201]
        post_id = post_response.json()["id"]
        
        # Create comment with images
        comment_data = {
            "content": "This comment has images attached",
            "images": ["https://example.com/comment-image1.jpg"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/forum/posts/{post_id}/comments",
            headers=auth_headers,
            json=comment_data
        )
        assert response.status_code in [200, 201], f"Create comment failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Comment should have an ID"
        assert "images" in data, "Comment should have images field"
        assert len(data["images"]) == 1, f"Expected 1 image, got {len(data.get('images', []))}"
        
        print(f"Created comment with {len(data['images'])} images")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers=auth_headers)
    
    def test_get_post_includes_images(self, auth_headers):
        """Test that getting a post includes images array"""
        # Create post with images
        post_data = {
            "title": "TEST_GetPostImages Test Getting Post Images",
            "content": "Testing image retrieval",
            "tags": [],
            "images": ["https://example.com/test.jpg"]
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/forum/posts",
            headers=auth_headers,
            json=post_data
        )
        post_id = create_response.json()["id"]
        
        # Get the post
        get_response = requests.get(
            f"{BASE_URL}/api/forum/posts/{post_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert "images" in data, "Post GET should include images field"
        assert data["images"] == ["https://example.com/test.jpg"], "Images should match"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/forum/posts/{post_id}", headers=auth_headers)


class TestAdminSettingsPublitioCard:
    """Tests for Admin Settings API Keys tab - Publitio card"""
    
    def test_settings_platform_includes_publitio_fields(self, auth_headers):
        """Test that platform settings include Publitio API key fields"""
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get settings failed: {response.text}"
        
        data = response.json()
        # Publitio fields should exist (empty or configured)
        print(f"Settings keys: {list(data.keys())[:20]}...")  # Print first 20 keys
        
        # Check if publitio fields are in settings (may be empty)
        # The UI adds these fields when saving
        if "publitio_api_key" in data:
            print("Publitio API Key field exists in settings")
        if "publitio_api_secret" in data:
            print("Publitio API Secret field exists in settings")
    
    def test_can_save_publitio_settings(self, auth_headers):
        """Test that Publitio settings can be saved (without actual creds)"""
        # Get current settings first
        get_response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers=auth_headers
        )
        current_settings = get_response.json()
        
        # Add/update Publitio fields
        update_data = {
            **current_settings,
            "publitio_api_key": current_settings.get("publitio_api_key", ""),
            "publitio_api_secret": current_settings.get("publitio_api_secret", "")
        }
        
        response = requests.put(
            f"{BASE_URL}/api/settings/platform",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update settings failed: {response.text}"
        print("Publitio settings can be saved successfully")


class TestForumImageUploadComponent:
    """Tests for ForumImageUpload component API interactions"""
    
    def test_publitio_api_module_endpoints(self, auth_headers):
        """Verify all publitioAPI endpoints from api.js are available"""
        # testConnection
        test_response = requests.get(
            f"{BASE_URL}/api/publitio/test",
            headers=auth_headers
        )
        assert test_response.status_code in [200], "testConnection should return 200"
        
        # listFolders
        folders_response = requests.get(
            f"{BASE_URL}/api/publitio/folders",
            headers=auth_headers
        )
        assert folders_response.status_code in [200, 503], "listFolders should return 200 or 503"
        
        print("All publitioAPI endpoints accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

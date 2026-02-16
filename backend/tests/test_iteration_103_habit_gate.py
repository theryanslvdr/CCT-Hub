"""
Iteration 103 Tests: Habit Gate Overlay, Affiliate Center Enhancements, Screenshot Upload

Features to test:
1. POST /api/habits/upload-screenshot - uploads file, returns data URL (auth required)
2. POST /api/habits/{id}/complete - accepts screenshot_url query param (auth required)
3. GET /api/affiliate-resources - accessible by all users
4. POST /api/admin/affiliate-resources - admin can create resources
5. DELETE /api/admin/affiliate-resources/{id} - admin can delete resources
6. GET /api/habits/ - members can access habits page
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"

# Existing habit for testing
EXISTING_HABIT_ID = "99306d6a-5ac8-4d24-98ed-542aefcabcfd"


class TestAuth:
    """Test authentication"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_returns_access_token(self, admin_token):
        """Verify login returns access_token"""
        assert admin_token is not None
        assert len(admin_token) > 10
        print(f"Login successful, token length: {len(admin_token)}")


class TestHabitScreenshotUpload:
    """Test POST /api/habits/upload-screenshot endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_upload_screenshot_returns_data_url(self, admin_token):
        """Test that uploading a screenshot returns a data URL"""
        # Create a simple test image (1x1 pixel PNG)
        # PNG header bytes for a 1x1 red pixel
        test_image = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xA3, 0x56, 0xA9,
            0x40, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {'file': ('test_screenshot.png', io.BytesIO(test_image), 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/api/habits/upload-screenshot",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "url" in data, "Response should contain 'url' field"
        assert data["url"].startswith("data:image/png;base64,"), "URL should be a data URL"
        print(f"Screenshot upload successful, data URL length: {len(data['url'])}")
    
    def test_upload_screenshot_requires_auth(self):
        """Test that upload-screenshot requires authentication"""
        test_image = bytes([0x89, 0x50, 0x4E, 0x47])  # Minimal PNG start
        files = {'file': ('test.png', io.BytesIO(test_image), 'image/png')}
        
        response = requests.post(
            f"{BASE_URL}/api/habits/upload-screenshot",
            files=files
        )
        
        assert response.status_code in [401, 403], f"Should require auth, got: {response.status_code}"
        print("Upload screenshot correctly requires authentication")


class TestHabitCompletionWithScreenshot:
    """Test POST /api/habits/{id}/complete with screenshot_url param"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_complete_habit_accepts_screenshot_url(self, admin_token):
        """Test that complete habit accepts screenshot_url query param"""
        test_screenshot_url = "data:image/png;base64,iVBORw0KGgo="
        
        response = requests.post(
            f"{BASE_URL}/api/habits/{EXISTING_HABIT_ID}/complete",
            params={"screenshot_url": test_screenshot_url},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Either 200 (completed) or 200 with already=True is acceptable
        assert response.status_code == 200, f"Complete habit failed: {response.text}"
        data = response.json()
        assert "message" in data, "Response should contain message"
        print(f"Habit completion response: {data}")
    
    def test_complete_habit_requires_auth(self):
        """Test that completing a habit requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/habits/{EXISTING_HABIT_ID}/complete"
        )
        
        assert response.status_code in [401, 403], f"Should require auth, got: {response.status_code}"
        print("Habit completion correctly requires authentication")


class TestHabitsEndpoint:
    """Test GET /api/habits/ endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_habits_returns_habits_list(self, admin_token):
        """Test that GET /api/habits/ returns habits and completion status"""
        response = requests.get(
            f"{BASE_URL}/api/habits/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get habits failed: {response.text}"
        data = response.json()
        assert "habits" in data, "Response should contain 'habits' field"
        assert "completions_today" in data, "Response should contain 'completions_today' field"
        print(f"Habits endpoint returned {len(data['habits'])} habits")
    
    def test_get_habits_requires_auth(self):
        """Test that GET /api/habits/ requires authentication"""
        response = requests.get(f"{BASE_URL}/api/habits/")
        
        assert response.status_code in [401, 403], f"Should require auth, got: {response.status_code}"
        print("GET habits correctly requires authentication")


class TestAffiliateCenter:
    """Test Affiliate Center endpoints - accessible to all logged-in users"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_affiliate_resources(self, admin_token):
        """Test GET /api/affiliate-resources returns resources grouped by category"""
        response = requests.get(
            f"{BASE_URL}/api/affiliate-resources",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get affiliate resources failed: {response.text}"
        data = response.json()
        assert "resources" in data, "Response should contain 'resources' field"
        # Resources should be dict grouped by category
        assert isinstance(data["resources"], dict), "Resources should be a dict"
        print(f"Affiliate resources categories: {list(data['resources'].keys())}")
    
    def test_get_affiliate_chatbase_public(self, admin_token):
        """Test GET /api/affiliate-chatbase-public returns chatbase config"""
        response = requests.get(
            f"{BASE_URL}/api/affiliate-chatbase-public",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get chatbase failed: {response.text}"
        data = response.json()
        assert "enabled" in data, "Response should contain 'enabled' field"
        print(f"Chatbase config: enabled={data.get('enabled')}")
    
    def test_affiliate_resources_requires_auth(self):
        """Test that affiliate resources requires authentication"""
        response = requests.get(f"{BASE_URL}/api/affiliate-resources")
        
        assert response.status_code in [401, 403], f"Should require auth, got: {response.status_code}"
        print("Affiliate resources correctly requires authentication")


class TestAdminAffiliateResources:
    """Test Admin Affiliate Resource management"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_admin_create_and_delete_resource(self, admin_token):
        """Test admin can create and delete affiliate resources"""
        # Create a test resource
        test_resource = {
            "title": "TEST_Resource_103",
            "content": "This is a test resource for iteration 103 testing",
            "category": "conversation_starters",
            "order": 0
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/affiliate-resources",
            json=test_resource,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        created = create_response.json()
        assert "id" in created, "Created resource should have 'id'"
        resource_id = created["id"]
        print(f"Created test resource with ID: {resource_id}")
        
        # Delete the resource
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/affiliate-resources/{resource_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"Successfully deleted test resource: {resource_id}")
    
    def test_admin_affiliate_resources_list(self, admin_token):
        """Test admin can list all affiliate resources"""
        response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"List failed: {response.text}"
        data = response.json()
        assert "resources" in data, "Response should contain 'resources' field"
        print(f"Admin affiliate resources: {len(data.get('resources', []))} items")


class TestHabitStreakEndpoint:
    """Test GET /api/habits/streak endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_habit_streak(self, admin_token):
        """Test GET /api/habits/streak returns streak data"""
        response = requests.get(
            f"{BASE_URL}/api/habits/streak",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get streak failed: {response.text}"
        data = response.json()
        assert "current_streak" in data, "Response should contain 'current_streak'"
        assert "longest_streak" in data, "Response should contain 'longest_streak'"
        assert "total_days" in data, "Response should contain 'total_days'"
        print(f"Habit streak: current={data['current_streak']}, longest={data['longest_streak']}, total={data['total_days']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

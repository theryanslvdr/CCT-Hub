"""
Phase 4 Testing: Habit Streaks Enhancement + Affiliate Center

Tests:
1. Habit Streaks API (GET /api/habits/streak)
2. Affiliate Resources API (GET /api/affiliate-resources)
3. Admin Affiliate Resources CRUD (POST/PUT/DELETE /api/admin/affiliate-resources)
4. Admin Chatbase Config (GET/PUT /api/admin/affiliate-chatbase)
5. Public Chatbase Status (GET /api/affiliate-chatbase-public)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuth:
    """Get authentication token for tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as master admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json().get("access_token")
        assert token, "No access_token in response"
        return token

    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Authorization headers"""
        return {"Authorization": f"Bearer {admin_token}"}


class TestHabitStreaks(TestAuth):
    """Test habit streaks enhancement (Phase 4 Feature 1)"""

    def test_get_habit_streak_endpoint(self, auth_headers):
        """GET /api/habits/streak - returns current_streak, longest_streak, total_days"""
        response = requests.get(
            f"{BASE_URL}/api/habits/streak",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "current_streak" in data, "Missing current_streak field"
        assert "longest_streak" in data, "Missing longest_streak field"
        assert "total_days" in data, "Missing total_days field"
        
        # Verify types
        assert isinstance(data["current_streak"], int), "current_streak should be int"
        assert isinstance(data["longest_streak"], int), "longest_streak should be int"
        assert isinstance(data["total_days"], int), "total_days should be int"
        
        print(f"Habit streak: current={data['current_streak']}, longest={data['longest_streak']}, total={data['total_days']}")

    def test_get_habits_includes_streak(self, auth_headers):
        """GET /api/habits/ includes streak field in response"""
        response = requests.get(
            f"{BASE_URL}/api/habits/",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response has streak
        assert "streak" in data, "Missing streak field in GET /api/habits/ response"
        streak = data["streak"]
        
        # Verify streak structure
        assert "current_streak" in streak, "Missing current_streak in streak"
        assert "longest_streak" in streak, "Missing longest_streak in streak"
        assert "total_days" in streak, "Missing total_days in streak"
        
        print(f"GET /api/habits/ includes streak: {streak}")


class TestAffiliateResources(TestAuth):
    """Test affiliate resources API (Phase 4 Feature 2)"""

    def test_get_affiliate_resources_public(self, auth_headers):
        """GET /api/affiliate-resources - returns grouped resources by category"""
        response = requests.get(
            f"{BASE_URL}/api/affiliate-resources",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response has resources field
        assert "resources" in data, "Missing resources field"
        resources = data["resources"]
        
        # Verify it's grouped by category (dict structure)
        assert isinstance(resources, dict), "Resources should be grouped by category"
        
        # Valid categories
        valid_categories = ['conversation_starters', 'story_templates', 'marketing', 'faqs']
        for category in resources:
            assert category in valid_categories, f"Invalid category: {category}"
            assert isinstance(resources[category], list), f"Category {category} should be a list"
        
        print(f"Affiliate resources categories: {list(resources.keys())}")

    def test_get_chatbase_public(self, auth_headers):
        """GET /api/affiliate-chatbase-public - returns chatbase status"""
        response = requests.get(
            f"{BASE_URL}/api/affiliate-chatbase-public",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response has enabled and bot_id fields
        assert "enabled" in data, "Missing enabled field"
        assert "bot_id" in data, "Missing bot_id field"
        assert isinstance(data["enabled"], bool), "enabled should be boolean"
        
        print(f"Chatbase public: enabled={data['enabled']}, bot_id={data['bot_id']}")


class TestAdminAffiliateResources(TestAuth):
    """Test admin affiliate resources CRUD (Phase 4 Feature 3)"""
    
    @pytest.fixture(scope="class")
    def test_resource_id(self, auth_headers):
        """Create a test resource for update/delete tests"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers=auth_headers,
            json={
                "title": f"TEST_Resource_{unique_id}",
                "content": f"Test content for resource {unique_id}",
                "category": "conversation_starters",
                "order": 99
            }
        )
        assert response.status_code == 200, f"Failed to create test resource: {response.text}"
        resource_id = response.json().get("id")
        yield resource_id
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/admin/affiliate-resources/{resource_id}", headers=auth_headers)
        except:
            pass

    def test_admin_get_affiliate_resources(self, auth_headers):
        """GET /api/admin/affiliate-resources - admin auth required"""
        response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "resources" in data, "Missing resources field"
        resources = data["resources"]
        assert isinstance(resources, list), "Resources should be a list for admin view"
        
        print(f"Admin affiliate resources count: {len(resources)}")

    def test_admin_create_affiliate_resource(self, auth_headers):
        """POST /api/admin/affiliate-resources - creates a resource"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers=auth_headers,
            json={
                "title": f"TEST_CreateResource_{unique_id}",
                "content": "This is a test conversation starter message.",
                "category": "conversation_starters",
                "order": 100
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert "id" in data, "Missing id in response"
        assert data["title"] == f"TEST_CreateResource_{unique_id}"
        assert data["category"] == "conversation_starters"
        
        resource_id = data["id"]
        print(f"Created resource: {resource_id}")
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        resources = get_response.json().get("resources", [])
        created = next((r for r in resources if r["id"] == resource_id), None)
        assert created is not None, "Created resource not found in list"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/affiliate-resources/{resource_id}", headers=auth_headers)

    def test_admin_update_affiliate_resource(self, auth_headers, test_resource_id):
        """PUT /api/admin/affiliate-resources/{id} - updates a resource"""
        response = requests.put(
            f"{BASE_URL}/api/admin/affiliate-resources/{test_resource_id}",
            headers=auth_headers,
            json={
                "title": "TEST_Updated_Title",
                "content": "Updated content for testing",
                "category": "faqs",
                "order": 50
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify update with GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers=auth_headers
        )
        resources = get_response.json().get("resources", [])
        updated = next((r for r in resources if r["id"] == test_resource_id), None)
        assert updated is not None, "Updated resource not found"
        assert updated["title"] == "TEST_Updated_Title", "Title not updated"
        assert updated["category"] == "faqs", "Category not updated"
        
        print(f"Updated resource: {test_resource_id}")

    def test_admin_delete_affiliate_resource(self, auth_headers):
        """DELETE /api/admin/affiliate-resources/{id} - deletes a resource"""
        # First create a resource to delete
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers=auth_headers,
            json={
                "title": f"TEST_ToDelete_{unique_id}",
                "content": "Will be deleted",
                "category": "marketing",
                "order": 0
            }
        )
        assert create_response.status_code == 200
        resource_id = create_response.json()["id"]
        
        # Delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/affiliate-resources/{resource_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Failed to delete: {delete_response.text}"
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-resources",
            headers=auth_headers
        )
        resources = get_response.json().get("resources", [])
        deleted = next((r for r in resources if r["id"] == resource_id), None)
        assert deleted is None, "Resource still exists after delete"
        
        print(f"Deleted resource: {resource_id}")


class TestAdminChatbaseConfig(TestAuth):
    """Test admin chatbase configuration (Phase 4 Feature 3)"""

    def test_admin_get_chatbase_config(self, auth_headers):
        """GET /api/admin/affiliate-chatbase - returns chatbase config"""
        response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-chatbase",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "enabled" in data, "Missing enabled field"
        assert "bot_id" in data, "Missing bot_id field"
        
        print(f"Admin chatbase config: enabled={data['enabled']}, bot_id={data['bot_id']}")

    def test_admin_update_chatbase_config(self, auth_headers):
        """PUT /api/admin/affiliate-chatbase - saves chatbase config"""
        # First get current config
        get_response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-chatbase",
            headers=auth_headers
        )
        original_config = get_response.json()
        
        # Update config
        test_bot_id = "test-bot-123"
        response = requests.put(
            f"{BASE_URL}/api/admin/affiliate-chatbase",
            headers=auth_headers,
            params={"bot_id": test_bot_id, "enabled": True}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify update
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/affiliate-chatbase",
            headers=auth_headers
        )
        updated_config = verify_response.json()
        assert updated_config["bot_id"] == test_bot_id, "bot_id not updated"
        assert updated_config["enabled"] == True, "enabled not updated"
        
        print(f"Updated chatbase config: {updated_config}")
        
        # Restore original config
        requests.put(
            f"{BASE_URL}/api/admin/affiliate-chatbase",
            headers=auth_headers,
            params={"bot_id": original_config.get("bot_id", ""), "enabled": original_config.get("enabled", False)}
        )


class TestUnauthorizedAccess:
    """Test that admin endpoints require authentication"""

    def test_affiliate_resources_requires_auth(self):
        """GET /api/affiliate-resources requires auth"""
        response = requests.get(f"{BASE_URL}/api/affiliate-resources")
        assert response.status_code == 403 or response.status_code == 401, "Should require auth"

    def test_habit_streak_requires_auth(self):
        """GET /api/habits/streak requires auth"""
        response = requests.get(f"{BASE_URL}/api/habits/streak")
        assert response.status_code == 403 or response.status_code == 401, "Should require auth"

    def test_admin_affiliate_requires_admin(self):
        """POST /api/admin/affiliate-resources requires admin auth"""
        response = requests.post(
            f"{BASE_URL}/api/admin/affiliate-resources",
            json={"title": "test", "content": "test", "category": "faqs"}
        )
        assert response.status_code == 403 or response.status_code == 401, "Should require admin auth"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 165: Test New Feature Integrations
1) GET /api/profit/daily-summary - Daily Profit Summary
2) GET /api/ai-assistant/popular-prompts - AI Smart Prompts
3) GET /api/users/member/{member_id}/public - Public Member Profile
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Auth failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(auth_token):
    """Session with auth header."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


@pytest.fixture(scope="module")
def user_id(auth_token):
    """Get current user's ID."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        # User ID can be in different places depending on response format
        if 'id' in user_data:
            return user_data.get("id")
        elif 'user' in user_data:
            return user_data.get("user", {}).get("id")
    # Fallback: use the admin user ID from login
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if login_resp.status_code == 200:
        return login_resp.json().get("user", {}).get("id")
    pytest.skip(f"Failed to get user ID")


class TestDailySummaryEndpoint:
    """Tests for /api/profit/daily-summary endpoint."""
    
    def test_daily_summary_returns_200(self, authenticated_client):
        """Test that daily summary endpoint returns 200."""
        response = authenticated_client.get(f"{BASE_URL}/api/profit/daily-summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_daily_summary_has_required_fields(self, authenticated_client):
        """Test that daily summary returns all required fields."""
        response = authenticated_client.get(f"{BASE_URL}/api/profit/daily-summary")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ['date', 'trade_count', 'total_profit', 'total_commission', 
                          'net_profit', 'account_value', 'current_streak', 'has_traded_today']
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    def test_daily_summary_data_types(self, authenticated_client):
        """Test that daily summary returns correct data types."""
        response = authenticated_client.get(f"{BASE_URL}/api/profit/daily-summary")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data['date'], str), "date should be a string"
        assert isinstance(data['trade_count'], int), "trade_count should be int"
        assert isinstance(data['total_profit'], (int, float)), "total_profit should be numeric"
        assert isinstance(data['net_profit'], (int, float)), "net_profit should be numeric"
        assert isinstance(data['account_value'], (int, float)), "account_value should be numeric"
        assert isinstance(data['current_streak'], int), "current_streak should be int"
        assert isinstance(data['has_traded_today'], bool), "has_traded_today should be bool"
    
    def test_daily_summary_without_auth(self):
        """Test that endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/profit/daily-summary")
        assert response.status_code in [401, 403], "Endpoint should require authentication"


class TestPopularPromptsEndpoint:
    """Tests for /api/ai-assistant/popular-prompts endpoint."""
    
    def test_popular_prompts_returns_200(self, authenticated_client):
        """Test that popular prompts endpoint returns 200."""
        response = authenticated_client.get(f"{BASE_URL}/api/ai-assistant/popular-prompts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_popular_prompts_has_prompts_array(self, authenticated_client):
        """Test that response contains prompts array."""
        response = authenticated_client.get(f"{BASE_URL}/api/ai-assistant/popular-prompts")
        assert response.status_code == 200
        
        data = response.json()
        assert 'prompts' in data, "Response should contain 'prompts' field"
        assert isinstance(data['prompts'], list), "prompts should be a list"
    
    def test_popular_prompts_with_assistant_id(self, authenticated_client):
        """Test popular prompts with specific assistant ID."""
        # Test with ryai assistant
        response = authenticated_client.get(f"{BASE_URL}/api/ai-assistant/popular-prompts?assistant_id=ryai")
        assert response.status_code == 200
        
        # Test with zxai assistant
        response = authenticated_client.get(f"{BASE_URL}/api/ai-assistant/popular-prompts?assistant_id=zxai")
        assert response.status_code == 200
    
    def test_popular_prompts_structure(self, authenticated_client):
        """Test that each prompt has expected structure."""
        response = authenticated_client.get(f"{BASE_URL}/api/ai-assistant/popular-prompts")
        assert response.status_code == 200
        
        data = response.json()
        prompts = data.get('prompts', [])
        
        # If there are prompts, check structure
        for prompt in prompts[:3]:  # Check first 3
            assert 'question' in prompt, "Each prompt should have 'question' field"
    
    def test_popular_prompts_without_auth(self):
        """Test that endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/ai-assistant/popular-prompts")
        assert response.status_code in [401, 403], "Endpoint should require authentication"


class TestPublicMemberProfileEndpoint:
    """Tests for /api/users/member/{member_id}/public endpoint."""
    
    def test_public_profile_returns_200(self, authenticated_client, user_id):
        """Test that public profile endpoint returns 200 for valid member."""
        response = authenticated_client.get(f"{BASE_URL}/api/users/member/{user_id}/public")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_public_profile_has_required_sections(self, authenticated_client, user_id):
        """Test that public profile returns all required sections."""
        response = authenticated_client.get(f"{BASE_URL}/api/users/member/{user_id}/public")
        assert response.status_code == 200
        
        data = response.json()
        assert 'profile' in data, "Response should contain 'profile' section"
        assert 'stats' in data, "Response should contain 'stats' section"
        assert 'badges' in data, "Response should contain 'badges' section"
    
    def test_public_profile_profile_fields(self, authenticated_client, user_id):
        """Test that profile section has expected fields."""
        response = authenticated_client.get(f"{BASE_URL}/api/users/member/{user_id}/public")
        assert response.status_code == 200
        
        profile = response.json().get('profile', {})
        expected_fields = ['id', 'full_name', 'role', 'created_at']
        
        for field in expected_fields:
            assert field in profile, f"Profile missing field: {field}"
    
    def test_public_profile_stats_fields(self, authenticated_client, user_id):
        """Test that stats section has expected fields."""
        response = authenticated_client.get(f"{BASE_URL}/api/users/member/{user_id}/public")
        assert response.status_code == 200
        
        stats = response.json().get('stats', {})
        expected_fields = ['level', 'lifetime_points', 'current_streak', 'longest_streak', 'forum_posts', 'forum_comments']
        
        for field in expected_fields:
            assert field in stats, f"Stats missing field: {field}"
    
    def test_public_profile_nonexistent_member(self, authenticated_client):
        """Test 404 for non-existent member."""
        response = authenticated_client.get(f"{BASE_URL}/api/users/member/nonexistent-user-id-12345/public")
        assert response.status_code == 404, "Should return 404 for non-existent member"
    
    def test_public_profile_without_auth(self):
        """Test that endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/users/member/some-user-id/public")
        assert response.status_code in [401, 403], "Endpoint should require authentication"


class TestHealthCheck:
    """Basic health check tests."""
    
    def test_api_accessible(self):
        """Test that API is accessible."""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"API health check failed: {response.status_code}"

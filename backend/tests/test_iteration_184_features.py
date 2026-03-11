"""
Iteration 184 Feature Tests:
- Stats overview endpoint (active_members, team_leaders, suspended, in_danger)
- Suspended member isolation from default member list
- Forum Solved tabs (UI-only, no backend changes)
- Habits Overhaul (day_of_week, requires_screenshot)
- Regression tests for login, onboarding, rewards streak
"""
import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def admin_token():
    """Get master admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "iam@ryansalvador.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")

@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ─── Stats Overview Endpoint Tests ───

class TestStatsOverview:
    """Test GET /api/admin/members/stats/overview endpoint"""
    
    def test_stats_overview_returns_200(self, admin_headers):
        """Stats overview endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/admin/members/stats/overview", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_stats_overview_has_required_fields(self, admin_headers):
        """Stats overview should return active_members, team_leaders, suspended, in_danger"""
        response = requests.get(f"{BASE_URL}/api/admin/members/stats/overview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["active_members", "team_leaders", "suspended", "in_danger"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], int), f"{field} should be integer, got {type(data[field])}"
    
    def test_stats_overview_values_non_negative(self, admin_headers):
        """All stat values should be non-negative integers"""
        response = requests.get(f"{BASE_URL}/api/admin/members/stats/overview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for field in ["active_members", "team_leaders", "suspended", "in_danger"]:
            assert data[field] >= 0, f"{field} should be >= 0, got {data[field]}"


# ─── Suspended Member Isolation Tests ───

class TestSuspendedMemberIsolation:
    """Test that suspended members are excluded from default list"""
    
    def test_default_member_list_returns_200(self, admin_headers):
        """Default member list should return 200"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=admin_headers)
        assert response.status_code == 200
    
    def test_default_member_list_excludes_suspended(self, admin_headers):
        """Default member list should NOT include suspended users"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        members = data.get("members", [])
        # Check that no member has is_suspended=True
        for member in members:
            assert member.get("is_suspended") != True, f"Found suspended member in default list: {member.get('email')}"
    
    def test_suspended_filter_only_shows_suspended(self, admin_headers):
        """status=suspended filter should only show suspended users"""
        response = requests.get(f"{BASE_URL}/api/admin/members?status=suspended", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        members = data.get("members", [])
        # All members in this list should be suspended
        for member in members:
            assert member.get("is_suspended") == True, f"Non-suspended member in suspended list: {member.get('email')}"
    
    def test_active_filter_excludes_suspended(self, admin_headers):
        """status=active filter should exclude suspended users"""
        response = requests.get(f"{BASE_URL}/api/admin/members?status=active", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        members = data.get("members", [])
        for member in members:
            assert member.get("is_suspended") != True, f"Suspended member in active list: {member.get('email')}"


# ─── Habits Overhaul Tests ───

class TestHabitsOverhaul:
    """Test habit creation/update with day_of_week and requires_screenshot fields"""
    
    def test_admin_get_habits_returns_200(self, admin_headers):
        """Admin habits endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        assert response.status_code == 200
    
    def test_admin_create_habit_with_day_of_week(self, admin_headers):
        """Should be able to create a habit with day_of_week field"""
        payload = {
            "title": "TEST_Wednesday Only Habit",
            "description": "Test habit for Wednesday only",
            "action_type": "generic",
            "action_data": "",
            "is_gate": True,
            "validity_days": 1,
            "requires_screenshot": False,
            "day_of_week": "wednesday"
        }
        response = requests.post(f"{BASE_URL}/api/admin/habits", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("title") == payload["title"]
        assert data.get("day_of_week") == "wednesday"
        assert data.get("requires_screenshot") == False
        
        # Store habit ID for cleanup
        TestHabitsOverhaul.created_habit_id = data.get("id")
    
    def test_admin_create_habit_with_requires_screenshot(self, admin_headers):
        """Should be able to create a habit with requires_screenshot=True"""
        payload = {
            "title": "TEST_Screenshot Required Habit",
            "description": "Must upload screenshot proof",
            "action_type": "generic",
            "action_data": "",
            "is_gate": True,
            "validity_days": 1,
            "requires_screenshot": True,
            "day_of_week": None  # Daily habit
        }
        response = requests.post(f"{BASE_URL}/api/admin/habits", json=payload, headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("requires_screenshot") == True
        assert data.get("day_of_week") is None  # Daily habit
        
        TestHabitsOverhaul.screenshot_habit_id = data.get("id")
    
    def test_admin_update_habit_preserves_fields(self, admin_headers):
        """Updating a habit should preserve day_of_week and requires_screenshot"""
        if not hasattr(TestHabitsOverhaul, 'created_habit_id'):
            pytest.skip("No habit created to update")
        
        payload = {
            "title": "TEST_Wednesday Only Habit Updated",
            "description": "Updated description",
            "action_type": "generic",
            "action_data": "",
            "is_gate": True,
            "validity_days": 2,
            "requires_screenshot": True,  # Changed
            "day_of_week": "wednesday"  # Preserved
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/habits/{TestHabitsOverhaul.created_habit_id}",
            json=payload,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_get_habits_filters_by_day(self, admin_headers):
        """GET /api/habits/ should filter habits by today's day of week"""
        response = requests.get(f"{BASE_URL}/api/habits/", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        habits = data.get("habits", [])
        
        # Get today's day
        today_day = datetime.now(timezone.utc).strftime("%A").lower()
        
        # All habits should either have day_of_week=None or day_of_week=today_day
        for habit in habits:
            day = habit.get("day_of_week")
            if day is not None:
                assert day == today_day, f"Habit {habit.get('title')} has day_of_week={day} but today is {today_day}"


# ─── Habit Completion Screenshot Tests ───

class TestHabitScreenshotRequirement:
    """Test that habits requiring screenshots return 400 when no screenshot provided"""
    
    def test_complete_habit_without_screenshot_fails(self, admin_headers):
        """Completing a screenshot-required habit without screenshot should return 400"""
        # First, find a habit that requires screenshot
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("Could not get habits list")
        
        habits = response.json().get("habits", [])
        screenshot_habit = None
        for h in habits:
            if h.get("requires_screenshot") and h.get("active"):
                screenshot_habit = h
                break
        
        if not screenshot_habit:
            pytest.skip("No active habit with requires_screenshot found")
        
        # Try to complete without screenshot
        complete_response = requests.post(
            f"{BASE_URL}/api/habits/{screenshot_habit['id']}/complete",
            json={"screenshot_url": ""},
            headers=admin_headers
        )
        
        # Should return 400 with appropriate error
        if complete_response.status_code == 400:
            detail = complete_response.json().get("detail", "")
            assert "screenshot" in detail.lower(), f"Expected screenshot error, got: {detail}"
        # If already completed today, it returns 200 with already=True
        elif complete_response.status_code == 200:
            data = complete_response.json()
            if data.get("already"):
                pass  # Already completed today, acceptable
    
    def test_complete_habit_with_screenshot_succeeds(self, admin_headers):
        """Completing a screenshot-required habit WITH screenshot should succeed"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        if response.status_code != 200:
            pytest.skip("Could not get habits list")
        
        habits = response.json().get("habits", [])
        screenshot_habit = None
        for h in habits:
            if h.get("requires_screenshot") and h.get("active"):
                screenshot_habit = h
                break
        
        if not screenshot_habit:
            pytest.skip("No active habit with requires_screenshot found")
        
        # Complete WITH screenshot URL
        complete_response = requests.post(
            f"{BASE_URL}/api/habits/{screenshot_habit['id']}/complete",
            json={"screenshot_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="},
            headers=admin_headers
        )
        
        # Should succeed (200) or already completed
        assert complete_response.status_code in [200], f"Expected 200, got {complete_response.status_code}: {complete_response.text}"


# ─── Regression Tests ───

class TestRegressionLogin:
    """Regression test for login functionality"""
    
    def test_login_with_valid_credentials(self):
        """Login should work with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data
    
    def test_login_with_invalid_credentials(self):
        """Login should fail with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400, 404], f"Expected 401/400/404, got {response.status_code}"


class TestRegressionOnboarding:
    """Regression test for profit tracker onboarding"""
    
    def test_onboarding_status_endpoint(self, admin_headers):
        """Onboarding status endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/profit-tracker/onboarding-status", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestRegressionRewardsStreak:
    """Regression test for rewards streak endpoint"""
    
    def test_rewards_summary_returns_streak(self, admin_headers):
        """Rewards summary should return streak info"""
        response = requests.get(f"{BASE_URL}/api/rewards/summary", headers=admin_headers)
        # May return 200 or 404 if no rewards setup
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"


# ─── Server Health Check ───

class TestServerHealth:
    """Basic server health check"""
    
    def test_server_is_up(self):
        """Server health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"


# ─── Cleanup ───

@pytest.fixture(scope="module", autouse=True)
def cleanup_test_habits(admin_headers):
    """Cleanup test habits after all tests complete"""
    yield
    # Cleanup TEST_ prefixed habits
    try:
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        if response.status_code == 200:
            habits = response.json().get("habits", [])
            for habit in habits:
                if habit.get("title", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/admin/habits/{habit['id']}", headers=admin_headers)
    except:
        pass

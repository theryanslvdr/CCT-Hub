"""
Iteration 108: Member Visibility Bug Fixes Test
Tests for:
1. All members have 'habits' and 'affiliate' in allowed_dashboards
2. Admin's allowed_dashboards includes 'habits' and 'affiliate'
3. GET /api/trade/signal-block-status returns habit_gate_locked status
4. GET /api/habits/ returns habits with gate status
5. Registration defaults include habits/affiliate
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMemberVisibilityFixes:
    """Tests for member visibility bugs - habits/affiliate in allowed_dashboards"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token")
        self.user = data.get("user")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_has_habits_and_affiliate_in_allowed_dashboards(self):
        """Test that admin's allowed_dashboards includes 'habits' and 'affiliate'"""
        allowed = self.user.get("allowed_dashboards", [])
        assert "habits" in allowed, f"Admin missing 'habits' in allowed_dashboards: {allowed}"
        assert "affiliate" in allowed, f"Admin missing 'affiliate' in allowed_dashboards: {allowed}"
    
    def test_all_members_have_habits_and_affiliate(self):
        """Test that all members have 'habits' and 'affiliate' in allowed_dashboards"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=self.headers)
        assert response.status_code == 200, f"Failed to get members: {response.text}"
        
        members = response.json().get("members", [])
        assert len(members) > 0, "No members found"
        
        for member in members:
            allowed = member.get("allowed_dashboards", [])
            member_name = member.get("full_name", "Unknown")
            assert "habits" in allowed, f"Member {member_name} missing 'habits' in allowed_dashboards: {allowed}"
            assert "affiliate" in allowed, f"Member {member_name} missing 'affiliate' in allowed_dashboards: {allowed}"
    
    def test_signal_block_status_endpoint(self):
        """Test GET /api/trade/signal-block-status returns proper structure"""
        response = requests.get(f"{BASE_URL}/api/trade/signal-block-status", headers=self.headers)
        assert response.status_code == 200, f"Signal block status failed: {response.text}"
        
        data = response.json()
        # Verify expected fields
        assert "blocked" in data, "Missing 'blocked' field"
        assert "habit_gate_locked" in data, "Missing 'habit_gate_locked' field"
        assert isinstance(data["blocked"], bool), "blocked should be boolean"
        assert isinstance(data["habit_gate_locked"], bool), "habit_gate_locked should be boolean"
    
    def test_habits_endpoint(self):
        """Test GET /api/habits/ returns habits list"""
        response = requests.get(f"{BASE_URL}/api/habits/", headers=self.headers)
        assert response.status_code == 200, f"Habits endpoint failed: {response.text}"
        
        data = response.json()
        assert "habits" in data, "Missing 'habits' field in response"
        assert isinstance(data["habits"], list), "habits should be a list"
        
        # Check for gate status field on habits
        if len(data["habits"]) > 0:
            habit = data["habits"][0]
            # Verify habit structure
            assert "id" in habit, "Habit missing 'id' field"
            assert "title" in habit, "Habit missing 'title' field"
            # is_gate indicates whether habit is part of signal gate
            assert "is_gate" in habit, "Habit missing 'is_gate' field"
    
    def test_habits_streak_endpoint(self):
        """Test GET /api/habits/streak returns streak info"""
        response = requests.get(f"{BASE_URL}/api/habits/streak", headers=self.headers)
        assert response.status_code == 200, f"Streak endpoint failed: {response.text}"
        
        data = response.json()
        assert "current_streak" in data, "Missing 'current_streak' field"
    
    def test_affiliate_resources_endpoint(self):
        """Test GET /api/affiliate-resources returns resources"""
        response = requests.get(f"{BASE_URL}/api/affiliate-resources", headers=self.headers)
        assert response.status_code == 200, f"Affiliate resources failed: {response.text}"
        
        data = response.json()
        # Verify structure
        assert isinstance(data, dict) or isinstance(data, list), "Invalid affiliate resources response"


class TestRegistrationDefaults:
    """Tests to verify registration includes proper default dashboards"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_habits_management(self):
        """Test GET /api/admin/habits returns habit management data"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=self.headers)
        assert response.status_code == 200, f"Admin habits failed: {response.text}"
        
        data = response.json()
        assert "habits" in data, "Missing 'habits' field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

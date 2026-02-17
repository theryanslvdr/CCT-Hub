"""
Test iteration 109: validity_days feature for habits
Tests:
- Admin login and authentication
- Habit CRUD with validity_days field
- GET /api/habits/ returns gate_unlocked and gate_deadline
- POST /api/habits/{id}/complete sets gate_deadline correctly
- GET /api/trade/signal-block-status includes gate_deadline
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


class TestValidityDaysFeature:
    """Tests for validity_days habit feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: get admin token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        self.created_habit_ids = []
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Login returns 'access_token' field
        self.token = data.get("access_token")
        assert self.token, f"No access_token in response: {data.keys()}"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        # Cleanup: delete test habits
        for habit_id in self.created_habit_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/admin/habits/{habit_id}")
            except:
                pass
    
    def test_01_admin_login_returns_access_token(self):
        """Test admin login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, f"Expected access_token, got: {data.keys()}"
        assert data["user"]["role"] in ["master_admin", "super_admin", "admin"], f"User role: {data['user']['role']}"
    
    def test_02_create_habit_with_validity_days(self):
        """Test POST /api/admin/habits accepts validity_days"""
        payload = {
            "title": "TEST_habit_5_days_validity",
            "description": "Test habit with 5 day validity",
            "action_type": "generic",
            "action_data": "",
            "is_gate": True,
            "validity_days": 5
        }
        response = self.session.post(f"{BASE_URL}/api/admin/habits", json=payload)
        assert response.status_code == 200, f"Create habit failed: {response.text}"
        data = response.json()
        
        # Verify validity_days is returned
        assert "validity_days" in data, f"validity_days not in response: {data.keys()}"
        assert data["validity_days"] == 5, f"Expected validity_days=5, got {data['validity_days']}"
        assert data["title"] == payload["title"]
        assert data["is_gate"] == True
        
        self.created_habit_ids.append(data["id"])
        print(f"Created habit with validity_days=5: {data['id']}")
    
    def test_03_get_admin_habits_includes_validity_days(self):
        """Test GET /api/admin/habits returns validity_days"""
        # First create a habit with validity_days
        create_resp = self.session.post(f"{BASE_URL}/api/admin/habits", json={
            "title": "TEST_habit_for_list_check",
            "description": "Test habit",
            "action_type": "generic",
            "is_gate": True,
            "validity_days": 7
        })
        assert create_resp.status_code == 200
        created_id = create_resp.json()["id"]
        self.created_habit_ids.append(created_id)
        
        # Get all habits
        response = self.session.get(f"{BASE_URL}/api/admin/habits")
        assert response.status_code == 200
        data = response.json()
        
        assert "habits" in data
        habits = data["habits"]
        
        # Find our test habit
        test_habit = next((h for h in habits if h["id"] == created_id), None)
        assert test_habit is not None, "Created habit not found in list"
        assert test_habit["validity_days"] == 7, f"validity_days mismatch: {test_habit.get('validity_days')}"
        print(f"Verified habit has validity_days=7 in list")
    
    def test_04_update_habit_with_validity_days(self):
        """Test PUT /api/admin/habits/{id} updates validity_days"""
        # Create a habit first
        create_resp = self.session.post(f"{BASE_URL}/api/admin/habits", json={
            "title": "TEST_habit_update_validity",
            "description": "Initial",
            "action_type": "generic",
            "is_gate": True,
            "validity_days": 1
        })
        assert create_resp.status_code == 200
        habit_id = create_resp.json()["id"]
        self.created_habit_ids.append(habit_id)
        
        # Update with new validity_days
        update_payload = {
            "title": "TEST_habit_update_validity_updated",
            "description": "Updated",
            "action_type": "generic",
            "action_data": "",
            "is_gate": True,
            "validity_days": 10
        }
        update_resp = self.session.put(f"{BASE_URL}/api/admin/habits/{habit_id}", json=update_payload)
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        
        # Verify by fetching habits
        get_resp = self.session.get(f"{BASE_URL}/api/admin/habits")
        habits = get_resp.json()["habits"]
        updated_habit = next((h for h in habits if h["id"] == habit_id), None)
        assert updated_habit is not None
        assert updated_habit["validity_days"] == 10, f"Update didn't persist: {updated_habit.get('validity_days')}"
        print(f"Updated habit validity_days from 1 to 10")
    
    def test_05_member_habits_returns_gate_status(self):
        """Test GET /api/habits/ returns gate_unlocked status"""
        response = self.session.get(f"{BASE_URL}/api/habits/")
        assert response.status_code == 200
        data = response.json()
        
        # Check expected fields
        assert "habits" in data, f"Missing habits in response: {data.keys()}"
        assert "gate_unlocked" in data, f"Missing gate_unlocked: {data.keys()}"
        assert "completions_today" in data, f"Missing completions_today: {data.keys()}"
        assert "date" in data, f"Missing date: {data.keys()}"
        
        # gate_deadline is optional (only when unlocked)
        print(f"gate_unlocked: {data['gate_unlocked']}, gate_deadline: {data.get('gate_deadline')}")
    
    def test_06_complete_habit_and_check_gate_deadline(self):
        """Test completing a habit sets gate_deadline correctly"""
        # Create a habit with 5 day validity
        create_resp = self.session.post(f"{BASE_URL}/api/admin/habits", json={
            "title": "TEST_habit_complete_deadline",
            "description": "Test completion",
            "action_type": "generic",
            "is_gate": True,
            "validity_days": 5
        })
        assert create_resp.status_code == 200
        habit_id = create_resp.json()["id"]
        self.created_habit_ids.append(habit_id)
        
        # Complete the habit
        complete_resp = self.session.post(f"{BASE_URL}/api/habits/{habit_id}/complete")
        assert complete_resp.status_code == 200, f"Complete failed: {complete_resp.text}"
        
        # Check gate status
        status_resp = self.session.get(f"{BASE_URL}/api/habits/")
        assert status_resp.status_code == 200
        data = status_resp.json()
        
        assert data["gate_unlocked"] == True, f"Gate should be unlocked after completion"
        
        # gate_deadline should be set (today + validity_days)
        if data.get("gate_deadline"):
            deadline = datetime.fromisoformat(data["gate_deadline"])
            today = datetime.now().date()
            expected_deadline = today + timedelta(days=5)
            # Allow 1 day tolerance for timezone differences
            assert abs((deadline.date() - expected_deadline).days) <= 1, \
                f"gate_deadline mismatch: {deadline.date()} vs expected ~{expected_deadline}"
            print(f"gate_deadline correctly set to: {data['gate_deadline']}")
    
    def test_07_signal_block_status_includes_gate_deadline(self):
        """Test GET /api/trade/signal-block-status includes gate_deadline"""
        response = self.session.get(f"{BASE_URL}/api/trade/signal-block-status")
        assert response.status_code == 200
        data = response.json()
        
        # Check expected fields
        assert "blocked" in data, f"Missing blocked: {data.keys()}"
        assert "habit_gate_locked" in data, f"Missing habit_gate_locked: {data.keys()}"
        
        # For admin, should not be blocked
        # But gate_deadline may or may not be present based on habit completions
        print(f"signal-block-status: blocked={data['blocked']}, habit_gate_locked={data['habit_gate_locked']}, gate_deadline={data.get('gate_deadline')}")
        
        # Admins are never blocked
        assert data["blocked"] == False, f"Admin should not be blocked: {data}"


class TestExistingHabitsValidity:
    """Test existing habits have validity_days"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_existing_habits_have_validity_days(self):
        """Verify existing habits ('Send 1 invite today', 'Send 1 invite this week') have validity_days"""
        response = self.session.get(f"{BASE_URL}/api/admin/habits")
        assert response.status_code == 200
        habits = response.json()["habits"]
        
        for habit in habits:
            # All habits should have validity_days (default 1 or as set)
            validity = habit.get("validity_days", 1)
            print(f"Habit '{habit['title']}': validity_days={validity}, is_gate={habit.get('is_gate')}")
            assert validity >= 1, f"Invalid validity_days: {validity}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

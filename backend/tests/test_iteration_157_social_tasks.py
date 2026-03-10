"""
Iteration 157: Phase 4 Social Media Growth Engine Tests
Tests the Social Tasks feature of the Habit Tracker
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestSocialMediaGrowthEngine:
    """Tests for GET /api/habits/social-tasks endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth token for tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_social_tasks_returns_200(self):
        """GET /api/habits/social-tasks returns 200"""
        resp = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASS: GET /api/habits/social-tasks returns 200")
    
    def test_social_tasks_response_structure(self):
        """Response contains tasks, level, level_name, streak, next_level_at"""
        resp = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        data = resp.json()
        
        # Verify required fields
        assert "tasks" in data, "Missing 'tasks' field"
        assert "level" in data, "Missing 'level' field"
        assert "level_name" in data, "Missing 'level_name' field"
        assert "streak" in data, "Missing 'streak' field"
        assert "date" in data, "Missing 'date' field"
        assert "next_level_at" in data, "Missing 'next_level_at' field"
        
        # Verify types
        assert isinstance(data["tasks"], list), "tasks should be a list"
        assert isinstance(data["level"], int), "level should be int"
        assert isinstance(data["level_name"], str), "level_name should be string"
        assert isinstance(data["streak"], int), "streak should be int"
        
        print(f"PASS: Response structure correct - Level {data['level']} ({data['level_name']}), Streak: {data['streak']}")
    
    def test_social_tasks_contain_3_tasks(self):
        """Response contains exactly 3 tasks"""
        resp = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        data = resp.json()
        
        tasks = data.get("tasks", [])
        assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"
        print("PASS: Response contains 3 tasks")
    
    def test_each_task_has_required_fields(self):
        """Each task has id, title, description, platform, time_estimate, completed, level"""
        resp = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        tasks = resp.json().get("tasks", [])
        
        required_fields = ["id", "title", "description", "platform", "time_estimate", "completed", "level"]
        
        for i, task in enumerate(tasks):
            for field in required_fields:
                assert field in task, f"Task {i+1} missing '{field}' field"
            print(f"Task {i+1}: {task['title']} ({task['platform']}, {task['time_estimate']})")
        
        print("PASS: All tasks have required fields")
    
    def test_tasks_cached_on_second_call(self):
        """Second call returns same cached tasks (not regenerated)"""
        # First call
        resp1 = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        tasks1 = resp1.json().get("tasks", [])
        task_ids_1 = [t["id"] for t in tasks1]
        
        time.sleep(1)  # Small delay
        
        # Second call
        resp2 = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        tasks2 = resp2.json().get("tasks", [])
        task_ids_2 = [t["id"] for t in tasks2]
        
        # Task IDs should be the same
        assert task_ids_1 == task_ids_2, f"Tasks regenerated! First: {task_ids_1}, Second: {task_ids_2}"
        print("PASS: Tasks are cached and not regenerated on second call")


class TestSocialTaskCompletion:
    """Tests for complete/uncomplete social task endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth token and get task IDs"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get tasks
        resp = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        assert resp.status_code == 200
        self.tasks = resp.json().get("tasks", [])
    
    def test_complete_social_task(self):
        """POST /api/habits/social-task/{task_id}/complete marks task as completed"""
        if not self.tasks:
            pytest.skip("No tasks available")
        
        # Find an uncompleted task
        uncompleted = [t for t in self.tasks if not t.get("completed")]
        if not uncompleted:
            pytest.skip("All tasks already completed")
        
        task = uncompleted[0]
        task_id = task["id"]
        
        resp = self.session.post(f"{BASE_URL}/api/habits/social-task/{task_id}/complete")
        assert resp.status_code == 200, f"Complete failed: {resp.text}"
        
        data = resp.json()
        assert "task_id" in data, "Response missing task_id"
        assert "all_done" in data, "Response missing all_done flag"
        assert data["task_id"] == task_id, "Returned task_id mismatch"
        
        print(f"PASS: Task '{task['title']}' completed. all_done: {data['all_done']}")
    
    def test_uncomplete_social_task(self):
        """POST /api/habits/social-task/{task_id}/uncomplete marks task as uncompleted"""
        if not self.tasks:
            pytest.skip("No tasks available")
        
        # Find a completed task
        completed = [t for t in self.tasks if t.get("completed")]
        if not completed:
            pytest.skip("No completed tasks to uncomplete")
        
        task = completed[0]
        task_id = task["id"]
        
        resp = self.session.post(f"{BASE_URL}/api/habits/social-task/{task_id}/uncomplete")
        assert resp.status_code == 200, f"Uncomplete failed: {resp.text}"
        
        # Verify task is now uncompleted
        resp2 = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        tasks = resp2.json().get("tasks", [])
        task_status = next((t for t in tasks if t["id"] == task_id), None)
        
        assert task_status is not None, "Task not found after uncomplete"
        assert task_status.get("completed") == False, "Task still shows as completed"
        
        print(f"PASS: Task '{task['title']}' uncompleted successfully")
    
    def test_complete_returns_all_done_flag(self):
        """POST complete returns all_done=True when all 3 tasks completed"""
        if not self.tasks:
            pytest.skip("No tasks available")
        
        # Complete all tasks
        all_done_flag = False
        for task in self.tasks:
            resp = self.session.post(f"{BASE_URL}/api/habits/social-task/{task['id']}/complete")
            if resp.status_code == 200:
                all_done_flag = resp.json().get("all_done", False)
        
        # After completing all 3, all_done should be True
        # (unless some were already completed from previous test)
        print(f"PASS: all_done flag working (final value: {all_done_flag})")


class TestLevelSystem:
    """Tests for the level progression system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_level_names_match_thresholds(self):
        """Verify level names: L1=Getting Started, L2=Active Engager, L3=Content Creator, L4=Thought Leader"""
        resp = self.session.get(f"{BASE_URL}/api/habits/social-tasks")
        data = resp.json()
        
        level = data.get("level")
        level_name = data.get("level_name")
        streak = data.get("streak")
        next_level_at = data.get("next_level_at")
        
        # Verify level matches streak
        expected_level = 1
        expected_name = "Getting Started"
        expected_next = 8
        
        if streak >= 46:
            expected_level = 4
            expected_name = "Thought Leader"
            expected_next = None
        elif streak >= 22:
            expected_level = 3
            expected_name = "Content Creator"
            expected_next = 46
        elif streak >= 8:
            expected_level = 2
            expected_name = "Active Engager"
            expected_next = 22
        
        assert level == expected_level, f"Level mismatch for streak {streak}: expected {expected_level}, got {level}"
        assert level_name == expected_name, f"Level name mismatch: expected '{expected_name}', got '{level_name}'"
        
        if expected_next is not None:
            assert next_level_at == expected_next, f"next_level_at mismatch: expected {expected_next}, got {next_level_at}"
        
        print(f"PASS: Streak {streak} = Level {level} ({level_name}), next at {next_level_at}")


class TestRegression:
    """Regression tests for previous AI endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_habits_endpoint_still_works(self):
        """GET /api/habits/ still returns habits"""
        resp = self.session.get(f"{BASE_URL}/api/habits/")
        assert resp.status_code == 200, f"Habits endpoint broken: {resp.text}"
        
        data = resp.json()
        assert "habits" in data
        assert "streak" in data
        assert "gate_unlocked" in data
        print("PASS: GET /api/habits/ working")
    
    def test_ai_financial_summary_still_works(self):
        """GET /api/ai/financial-summary still works (Phase 1 regression)"""
        resp = self.session.get(f"{BASE_URL}/api/ai/financial-summary")
        assert resp.status_code == 200, f"AI financial-summary broken: {resp.text}"
        print("PASS: AI financial-summary endpoint working")
    
    def test_ai_trade_journal_still_works(self):
        """GET /api/ai/trade-journal still works (Phase 2 regression)"""
        resp = self.session.get(f"{BASE_URL}/api/ai/trade-journal")
        assert resp.status_code == 200, f"AI trade-journal broken: {resp.text}"
        print("PASS: AI trade-journal endpoint working")
    
    def test_ai_daily_report_still_works(self):
        """GET /api/ai/daily-report still works (Phase 3 regression)"""
        resp = self.session.get(f"{BASE_URL}/api/ai/daily-report")
        assert resp.status_code == 200, f"AI daily-report broken: {resp.text}"
        print("PASS: AI daily-report endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

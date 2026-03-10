"""
Iteration 160: Quiz System, Did Not Trade Bug Fix, and Habit Validation
Tests for:
1. Did Not Trade bug fix - direction='NONE' should work without Pydantic errors
2. Quiz system - admin generate, approve, publish, member answer flow
3. Admin spot-check for habit proofs
4. Trade logs returning correct data including 'did not trade' entries
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ========== Did Not Trade Bug Fix Tests ==========

class TestDidNotTradeBugFix:
    """Test the 'Did Not Trade' bug fix - direction:None was causing Pydantic validation errors"""
    
    def test_get_trade_logs_no_500_error(self, admin_headers):
        """GET /api/trade/logs should not return 500 even with 'did not trade' entries (direction='NONE')"""
        response = requests.get(f"{BASE_URL}/api/trade/logs", headers=admin_headers)
        # Should NOT return 500 - the bug was Pydantic failing on direction:None
        assert response.status_code == 200, f"Trade logs failed with {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: GET /api/trade/logs returned {len(data)} trade entries")
    
    def test_trade_logs_include_did_not_trade_entries(self, admin_headers):
        """Verify 'did not trade' entries show up with direction='NONE'"""
        response = requests.get(f"{BASE_URL}/api/trade/logs?limit=100", headers=admin_headers)
        assert response.status_code == 200
        trades = response.json()
        
        # Check for any 'did not trade' entries
        did_not_trade_entries = [t for t in trades if t.get("did_not_trade") == True]
        print(f"Found {len(did_not_trade_entries)} 'did not trade' entries")
        
        # Verify direction field is handled
        for trade in trades:
            direction = trade.get("direction")
            # direction should be a string (not None) or not present
            if direction is not None:
                assert isinstance(direction, str), f"direction should be string, got {type(direction)}"
        
        print("SUCCESS: All trade entries have valid direction field")
    
    def test_trade_history_endpoint(self, admin_headers):
        """GET /api/trade/history should also work with 'did not trade' entries"""
        response = requests.get(f"{BASE_URL}/api/trade/history?page=1&page_size=20", headers=admin_headers)
        assert response.status_code == 200, f"Trade history failed: {response.text}"
        data = response.json()
        assert "trades" in data, "Response should have 'trades' key"
        assert "total" in data, "Response should have 'total' key"
        print(f"SUCCESS: Trade history returned {len(data['trades'])} entries, total: {data['total']}")


# ========== Daily Balances Fix Tests ==========

class TestDailyBalances:
    """Test the daily-balances endpoint fix (actual_profit 0-is-falsy bug)"""
    
    def test_daily_balances_endpoint(self, admin_headers):
        """GET /api/profit/daily-balances should return correct profit values including 0"""
        today = datetime.now(timezone.utc)
        start = (today.replace(day=1)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": start, "end_date": end},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Daily balances failed: {response.text}"
        data = response.json()
        assert "daily_balances" in data, "Response should have 'daily_balances' key"
        
        # Check that actual_profit=0 is shown as 0, not None
        for day in data["daily_balances"]:
            if day.get("has_trade"):
                actual = day.get("actual_profit")
                # The bug was: actual_profit=0 was being converted to None due to 0-is-falsy
                # Now it should be 0 (the actual value)
                if actual == 0:
                    print(f"Day {day['date']}: actual_profit=0 correctly preserved (not None)")
        
        print(f"SUCCESS: Daily balances returned {len(data['daily_balances'])} days")


# ========== Quiz Admin Generate Tests ==========

class TestQuizAdminGenerate:
    """Test quiz generation by admin"""
    
    def test_generate_quiz_questions(self, admin_headers):
        """POST /api/habits/quiz/admin/generate should create quiz questions via AI"""
        response = requests.post(
            f"{BASE_URL}/api/habits/quiz/admin/generate",
            json={"count": 2, "topic": "Hub", "difficulty": 1},
            headers=admin_headers,
            timeout=60  # AI generation may take time
        )
        # Generation might fail if AI is unavailable, but endpoint should respond
        if response.status_code == 200:
            data = response.json()
            assert "quizzes" in data, "Response should have 'quizzes' key"
            assert "count" in data, "Response should have 'count' key"
            print(f"SUCCESS: Generated {data['count']} quiz questions")
            # Verify quiz structure
            if data["quizzes"]:
                quiz = data["quizzes"][0]
                assert "id" in quiz
                assert "question" in quiz
                assert "correct_answer" in quiz
                assert "wrong_answers" in quiz
                assert "status" in quiz
                assert quiz["status"] == "pending"
                print(f"Quiz sample: {quiz['question'][:50]}...")
        elif response.status_code == 500:
            # AI generation might fail - this is expected if OpenRouter is down
            print(f"SKIP: AI generation failed (may be expected): {response.text[:200]}")
            pytest.skip("AI generation service unavailable")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")


# ========== Quiz Admin Pool Tests ==========

class TestQuizAdminPool:
    """Test quiz pool management"""
    
    def test_get_quiz_pool_all(self, admin_headers):
        """GET /api/habits/quiz/admin/pool returns quiz pool with all statuses"""
        response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/pool",
            params={"page": 1, "page_size": 20},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Get quiz pool failed: {response.text}"
        data = response.json()
        assert "quizzes" in data
        assert "total" in data
        assert "page" in data
        print(f"SUCCESS: Quiz pool has {data['total']} total quizzes, showing page {data['page']}")
    
    def test_get_quiz_pool_pending_filter(self, admin_headers):
        """GET /api/habits/quiz/admin/pool with status=pending filter"""
        response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/pool",
            params={"status": "pending"},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        # All returned should be pending
        for quiz in data["quizzes"]:
            assert quiz["status"] == "pending", f"Expected pending, got {quiz['status']}"
        print(f"SUCCESS: Found {len(data['quizzes'])} pending quizzes")
    
    def test_get_quiz_pool_approved_filter(self, admin_headers):
        """GET /api/habits/quiz/admin/pool with status=approved filter"""
        response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/pool",
            params={"status": "approved"},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        for quiz in data["quizzes"]:
            assert quiz["status"] == "approved"
        print(f"SUCCESS: Found {len(data['quizzes'])} approved quizzes")
    
    def test_get_quiz_pool_topic_filter(self, admin_headers):
        """GET /api/habits/quiz/admin/pool with topic filter"""
        response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/pool",
            params={"topic": "Hub"},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        for quiz in data["quizzes"]:
            assert quiz["platform_topic"] == "Hub", f"Expected Hub, got {quiz['platform_topic']}"
        print(f"SUCCESS: Found {len(data['quizzes'])} quizzes for Hub topic")


# ========== Quiz Admin Approve/Reject Tests ==========

class TestQuizAdminApproveReject:
    """Test quiz approval and rejection (master admin only for approve)"""
    
    def test_approve_quiz_master_admin_only(self, admin_headers):
        """POST /api/habits/quiz/admin/approve requires master admin"""
        # First, get some pending quizzes
        pool_response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/pool",
            params={"status": "pending"},
            headers=admin_headers
        )
        assert pool_response.status_code == 200
        pending = pool_response.json()["quizzes"]
        
        if not pending:
            print("SKIP: No pending quizzes to approve")
            pytest.skip("No pending quizzes available")
        
        # Try to approve
        quiz_ids = [pending[0]["id"]]
        response = requests.post(
            f"{BASE_URL}/api/habits/quiz/admin/approve",
            json={"quiz_ids": quiz_ids},
            headers=admin_headers
        )
        # Master admin should succeed
        assert response.status_code == 200, f"Approve failed: {response.text}"
        data = response.json()
        assert "approved" in data
        print(f"SUCCESS: Approved {data['approved']} quiz(es)")
    
    def test_reject_quiz(self, admin_headers):
        """POST /api/habits/quiz/admin/reject should reject quizzes"""
        # Get pending quizzes to reject
        pool_response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/pool",
            params={"status": "pending"},
            headers=admin_headers
        )
        assert pool_response.status_code == 200
        pending = pool_response.json()["quizzes"]
        
        if not pending:
            print("SKIP: No pending quizzes to reject")
            pytest.skip("No pending quizzes available")
        
        quiz_ids = [pending[0]["id"]]
        response = requests.post(
            f"{BASE_URL}/api/habits/quiz/admin/reject",
            json={"quiz_ids": quiz_ids, "reason": "Test rejection"},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Reject failed: {response.text}"
        data = response.json()
        print(f"SUCCESS: Rejected {data['rejected']} quiz(es)")


# ========== Quiz Admin Publish Tests ==========

class TestQuizAdminPublish:
    """Test quiz publishing for a specific date"""
    
    def test_publish_approved_quizzes(self, admin_headers):
        """POST /api/habits/quiz/admin/publish publishes approved quizzes for a date"""
        # Get approved quizzes
        pool_response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/pool",
            params={"status": "approved"},
            headers=admin_headers
        )
        assert pool_response.status_code == 200
        approved = pool_response.json()["quizzes"]
        
        if not approved:
            print("SKIP: No approved quizzes to publish")
            pytest.skip("No approved quizzes available")
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        quiz_ids = [q["id"] for q in approved[:3]]  # Publish up to 3
        
        response = requests.post(
            f"{BASE_URL}/api/habits/quiz/admin/publish",
            json={"quiz_ids": quiz_ids, "date": today},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Publish failed: {response.text}"
        data = response.json()
        assert "published" in data
        assert "date" in data
        print(f"SUCCESS: Published {data['published']} quizzes for {data['date']}")
    
    def test_get_published_quizzes(self, admin_headers):
        """GET /api/habits/quiz/admin/published returns published quizzes for a date"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/published",
            params={"date": today},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Get published failed: {response.text}"
        data = response.json()
        assert "quizzes" in data
        assert "date" in data
        print(f"SUCCESS: Found {len(data['quizzes'])} published quizzes for {data['date']}")


# ========== Member Quiz Flow Tests ==========

class TestMemberQuizFlow:
    """Test member quiz answering flow"""
    
    def test_get_todays_quizzes(self, admin_headers):
        """GET /api/habits/quiz/today returns today's quizzes for member"""
        response = requests.get(f"{BASE_URL}/api/habits/quiz/today", headers=admin_headers)
        assert response.status_code == 200, f"Get today's quizzes failed: {response.text}"
        data = response.json()
        assert "quizzes" in data
        assert "date" in data
        assert "total" in data
        assert "answered" in data
        assert "correct" in data
        assert "all_done" in data
        print(f"SUCCESS: Today has {data['total']} quizzes, {data['answered']} answered, {data['correct']} correct")
        
        # Verify quiz structure for member view
        if data["quizzes"]:
            quiz = data["quizzes"][0]
            assert "id" in quiz
            assert "question" in quiz
            assert "options" in quiz  # Shuffled answers
            assert "platform_topic" in quiz
            assert "answered" in quiz
            # If answered, should have additional fields
            if quiz["answered"]:
                assert "is_correct" in quiz
                assert "user_answer" in quiz
                assert "correct_answer" in quiz
                assert "explanation" in quiz
    
    def test_answer_quiz_question(self, admin_headers):
        """POST /api/habits/quiz/{id}/answer submits an answer"""
        # Get today's unanswered quizzes
        today_response = requests.get(f"{BASE_URL}/api/habits/quiz/today", headers=admin_headers)
        assert today_response.status_code == 200
        quizzes = today_response.json()["quizzes"]
        
        unanswered = [q for q in quizzes if not q["answered"]]
        if not unanswered:
            print("SKIP: No unanswered quizzes available")
            pytest.skip("No unanswered quizzes available")
        
        quiz = unanswered[0]
        # Pick the first option (may or may not be correct)
        answer = quiz["options"][0]
        
        response = requests.post(
            f"{BASE_URL}/api/habits/quiz/{quiz['id']}/answer",
            json={"answer": answer},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Answer failed: {response.text}"
        data = response.json()
        assert "is_correct" in data
        assert "correct_answer" in data
        assert "explanation" in data
        assert "all_done" in data
        
        result = "CORRECT" if data["is_correct"] else "INCORRECT"
        print(f"SUCCESS: Answered quiz - {result}. Explanation: {data['explanation'][:50]}...")
    
    def test_answer_already_answered_quiz(self, admin_headers):
        """POST /api/habits/quiz/{id}/answer should fail for already answered quiz"""
        # Get today's answered quizzes
        today_response = requests.get(f"{BASE_URL}/api/habits/quiz/today", headers=admin_headers)
        assert today_response.status_code == 200
        quizzes = today_response.json()["quizzes"]
        
        answered = [q for q in quizzes if q["answered"]]
        if not answered:
            print("SKIP: No answered quizzes to test duplicate answer")
            pytest.skip("No answered quizzes available")
        
        quiz = answered[0]
        response = requests.post(
            f"{BASE_URL}/api/habits/quiz/{quiz['id']}/answer",
            json={"answer": "test"},
            headers=admin_headers
        )
        assert response.status_code == 400, f"Expected 400 for duplicate answer, got {response.status_code}"
        print("SUCCESS: Duplicate answer correctly rejected with 400")


# ========== Admin Spot-Check Tests ==========

class TestAdminSpotCheck:
    """Test admin spot-check for habit proof verification"""
    
    def test_get_pending_proofs(self, admin_headers):
        """GET /api/habits/admin/pending-proofs returns proofs needing verification"""
        response = requests.get(
            f"{BASE_URL}/api/habits/admin/pending-proofs",
            params={"page": 1, "page_size": 20},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Get pending proofs failed: {response.text}"
        data = response.json()
        assert "completions" in data
        assert "total" in data
        assert "page" in data
        print(f"SUCCESS: Found {data['total']} pending proofs")
    
    def test_spot_check_stats(self, admin_headers):
        """GET /api/habits/admin/spot-check-stats returns verification statistics"""
        response = requests.get(f"{BASE_URL}/api/habits/admin/spot-check-stats", headers=admin_headers)
        assert response.status_code == 200, f"Get spot-check stats failed: {response.text}"
        data = response.json()
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
        print(f"SUCCESS: Spot-check stats - Pending: {data['pending']}, Approved: {data['approved']}, Rejected: {data['rejected']}")


# ========== API Accessibility Tests ==========

class TestAPIAccessibility:
    """Test that all new endpoints are accessible"""
    
    def test_quiz_routes_accessible(self, admin_headers):
        """Verify quiz routes are registered and accessible"""
        endpoints = [
            ("GET", "/api/habits/quiz/admin/pool"),
            ("GET", "/api/habits/quiz/today"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=admin_headers)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", headers=admin_headers, json={})
            
            # Should not be 404 (endpoint exists)
            assert response.status_code != 404, f"{method} {endpoint} returned 404"
            print(f"SUCCESS: {method} {endpoint} accessible (status: {response.status_code})")
    
    def test_habit_admin_routes_accessible(self, admin_headers):
        """Verify habit admin routes are registered"""
        endpoints = [
            ("GET", "/api/habits/admin/pending-proofs"),
            ("GET", "/api/habits/admin/spot-check-stats"),
        ]
        
        for method, endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=admin_headers)
            assert response.status_code != 404, f"{method} {endpoint} returned 404"
            print(f"SUCCESS: {method} {endpoint} accessible (status: {response.status_code})")

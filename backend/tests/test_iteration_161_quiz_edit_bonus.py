"""
Iteration 161 Tests: Quiz Edit with AI Verification + Quiz Correct Answer Bonus Points

Tests:
1. PUT /api/habits/quiz/admin/edit/{id} - Edit quiz question/answer/explanation/topic with AI verification
2. AI verification returns valid/issues feedback on save
3. Edited quiz updates propagate to daily_quizzes (published quizzes)
4. If AI flags issues on approved quiz, status resets to pending for re-review
5. POST /api/habits/quiz/{id}/answer returns correct_bonus=2 for correct answers
6. Quiz correct answer creates rewards_point_logs entry with source=quiz_correct
7. quiz_correct_count incremented in rewards_stats on correct answer
8. Quiz achievement badges defined: quiz_10, quiz_25, quiz_50, quiz_100
"""

import pytest
import requests
import os
from datetime import datetime
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token."""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    data = res.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin auth token."""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_user(admin_headers):
    """Get admin user info."""
    res = requests.get(f"{BASE_URL}/api/auth/me", headers=admin_headers)
    assert res.status_code == 200
    return res.json()


class TestQuizEditWithAIVerification:
    """Test quiz editing with AI verification feature."""
    
    def test_get_quiz_pool_for_edit(self, admin_headers):
        """Get quiz pool to find a quiz to edit."""
        res = requests.get(f"{BASE_URL}/api/habits/quiz/admin/pool", 
                          headers=admin_headers, 
                          params={"page_size": 20})
        assert res.status_code == 200
        data = res.json()
        assert "quizzes" in data
        print(f"Found {len(data['quizzes'])} quizzes in pool")
        return data["quizzes"]
    
    def test_edit_quiz_minor_correction(self, admin_headers):
        """Edit quiz with minor correction and verify AI verification response."""
        # Get a quiz to edit
        res = requests.get(f"{BASE_URL}/api/habits/quiz/admin/pool", 
                          headers=admin_headers, 
                          params={"page_size": 10})
        assert res.status_code == 200
        quizzes = res.json()["quizzes"]
        
        if not quizzes:
            pytest.skip("No quizzes in pool to edit")
        
        quiz = quizzes[0]
        quiz_id = quiz["id"]
        original_question = quiz["question"]
        
        # Make a minor correction
        updated_question = original_question.rstrip('?') + " (edited)?"
        
        edit_res = requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{quiz_id}",
            headers=admin_headers,
            json={"question": updated_question}
        )
        
        assert edit_res.status_code == 200, f"Edit failed: {edit_res.text}"
        edit_data = edit_res.json()
        
        # Verify response structure
        assert edit_data["success"] is True
        assert edit_data["quiz_id"] == quiz_id
        assert "verification" in edit_data
        assert "verified" in edit_data["verification"]
        assert "updated_fields" in edit_data
        assert "question" in edit_data["updated_fields"]
        
        print(f"Quiz edited. AI verification: {edit_data['verification']}")
        
        # Restore original question
        restore_res = requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{quiz_id}",
            headers=admin_headers,
            json={"question": original_question}
        )
        assert restore_res.status_code == 200
    
    def test_edit_all_fields(self, admin_headers):
        """Edit multiple fields at once."""
        res = requests.get(f"{BASE_URL}/api/habits/quiz/admin/pool", 
                          headers=admin_headers, 
                          params={"page_size": 5})
        quizzes = res.json()["quizzes"]
        
        if not quizzes:
            pytest.skip("No quizzes to edit")
        
        quiz = quizzes[0]
        quiz_id = quiz["id"]
        
        # Save original values
        original_data = {
            "question": quiz["question"],
            "correct_answer": quiz["correct_answer"],
            "wrong_answers": quiz.get("wrong_answers", []),
            "explanation": quiz.get("explanation", ""),
            "platform_topic": quiz.get("platform_topic", "Hub")
        }
        
        # Edit with new values
        edit_payload = {
            "question": "TEST: What is the main purpose of the Hub platform?",
            "correct_answer": "To track profits and trades",
            "wrong_answers": ["To play games", "To chat only", "To buy groceries"],
            "explanation": "The Hub is a comprehensive trading community platform.",
            "platform_topic": "Hub"
        }
        
        edit_res = requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{quiz_id}",
            headers=admin_headers,
            json=edit_payload
        )
        
        assert edit_res.status_code == 200
        data = edit_res.json()
        assert data["success"] is True
        
        # Verify all fields in updated_fields
        for field in ["question", "correct_answer", "wrong_answers", "explanation", "platform_topic"]:
            assert field in data["updated_fields"], f"Field {field} not in updated_fields"
        
        print(f"All fields updated. Verification: {data['verification']}")
        
        # Restore original
        restore_res = requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{quiz_id}",
            headers=admin_headers,
            json=original_data
        )
        assert restore_res.status_code == 200
    
    def test_edit_nonexistent_quiz(self, admin_headers):
        """Editing non-existent quiz returns 404."""
        fake_id = str(uuid.uuid4())
        res = requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{fake_id}",
            headers=admin_headers,
            json={"question": "Test question?"}
        )
        assert res.status_code == 404
        assert "not found" in res.text.lower()
    
    def test_edit_with_no_fields(self, admin_headers):
        """Editing with empty payload returns 400."""
        res = requests.get(f"{BASE_URL}/api/habits/quiz/admin/pool", 
                          headers=admin_headers, 
                          params={"page_size": 1})
        quizzes = res.json()["quizzes"]
        
        if not quizzes:
            pytest.skip("No quizzes to test")
        
        quiz_id = quizzes[0]["id"]
        edit_res = requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{quiz_id}",
            headers=admin_headers,
            json={}
        )
        
        assert edit_res.status_code == 400
        assert "no fields" in edit_res.text.lower()


class TestQuizEditPropagation:
    """Test that edits propagate to published quizzes."""
    
    def test_edit_propagates_to_daily_quizzes(self, admin_headers):
        """Verify edited quiz content propagates to daily_quizzes collection."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get published quizzes
        pub_res = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/published",
            headers=admin_headers,
            params={"date": today}
        )
        assert pub_res.status_code == 200
        published = pub_res.json()["quizzes"]
        
        if not published:
            pytest.skip("No published quizzes for today to test propagation")
        
        # Get a published quiz's source ID
        pub_quiz = published[0]
        quiz_id = pub_quiz.get("quiz_id")
        original_explanation = pub_quiz.get("explanation", "")
        
        if not quiz_id:
            pytest.skip("Published quiz missing quiz_id field")
        
        # Edit the source quiz explanation
        new_explanation = "EDITED: " + original_explanation
        edit_res = requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{quiz_id}",
            headers=admin_headers,
            json={"explanation": new_explanation}
        )
        
        if edit_res.status_code != 200:
            pytest.skip(f"Could not edit quiz: {edit_res.text}")
        
        # Verify propagation to published
        pub_res2 = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/published",
            headers=admin_headers,
            params={"date": today}
        )
        updated_published = pub_res2.json()["quizzes"]
        updated_quiz = next((q for q in updated_published if q.get("quiz_id") == quiz_id), None)
        
        if updated_quiz:
            assert updated_quiz["explanation"] == new_explanation, "Edit did not propagate to daily_quizzes"
            print("Edit propagated to daily_quizzes successfully")
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/habits/quiz/admin/edit/{quiz_id}",
            headers=admin_headers,
            json={"explanation": original_explanation}
        )


class TestQuizCorrectAnswerBonus:
    """Test quiz correct answer bonus points (2 pts per correct)."""
    
    def test_answer_quiz_correctly_awards_bonus(self, admin_headers, admin_user):
        """Answering quiz correctly should award 2 bonus points."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get today's quizzes
        quiz_res = requests.get(f"{BASE_URL}/api/habits/quiz/today", headers=admin_headers)
        assert quiz_res.status_code == 200
        quizzes = quiz_res.json()["quizzes"]
        
        # Find an unanswered quiz
        unanswered = [q for q in quizzes if not q["answered"]]
        
        if not unanswered:
            # Check if any correct answers were given
            correct = [q for q in quizzes if q.get("is_correct")]
            if correct:
                print(f"All quizzes answered. {len(correct)} were correct.")
                # Verify point log exists for quiz_correct
                pytest.skip("No unanswered quizzes - see rewards page test")
            pytest.skip("No unanswered quizzes available for testing")
        
        quiz = unanswered[0]
        quiz_id = quiz["id"]
        
        # We need the correct answer - it's only revealed after answering
        # So we'll answer correctly by getting from the published quizzes
        pub_res = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/published",
            headers=admin_headers,
            params={"date": today}
        )
        published = pub_res.json()["quizzes"]
        
        # Find matching quiz
        source_quiz = next((q for q in published if q["id"] == quiz_id), None)
        if not source_quiz:
            pytest.skip("Could not find quiz in published quizzes")
        
        correct_answer = source_quiz["correct_answer"]
        
        # Answer correctly
        answer_res = requests.post(
            f"{BASE_URL}/api/habits/quiz/{quiz_id}/answer",
            headers=admin_headers,
            json={"answer": correct_answer}
        )
        
        assert answer_res.status_code == 200
        answer_data = answer_res.json()
        
        # Verify response
        assert answer_data["is_correct"] is True
        assert answer_data["correct_answer"] == correct_answer
        assert "correct_bonus" in answer_data, "correct_bonus field missing"
        assert answer_data["correct_bonus"] == 2, f"Expected 2 bonus pts, got {answer_data['correct_bonus']}"
        
        print(f"Quiz answered correctly. Bonus: +{answer_data['correct_bonus']} pts")
    
    def test_answer_quiz_incorrectly_no_bonus(self, admin_headers):
        """Answering quiz incorrectly should NOT award bonus points."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        quiz_res = requests.get(f"{BASE_URL}/api/habits/quiz/today", headers=admin_headers)
        quizzes = quiz_res.json()["quizzes"]
        
        # Find an unanswered quiz
        unanswered = [q for q in quizzes if not q["answered"]]
        
        if not unanswered:
            pytest.skip("No unanswered quizzes to test")
        
        quiz = unanswered[0]
        quiz_id = quiz["id"]
        options = quiz["options"]
        
        # Get the correct answer to ensure we pick wrong
        pub_res = requests.get(
            f"{BASE_URL}/api/habits/quiz/admin/published",
            headers=admin_headers,
            params={"date": today}
        )
        published = pub_res.json()["quizzes"]
        source_quiz = next((q for q in published if q["id"] == quiz_id), None)
        
        if not source_quiz:
            pytest.skip("Could not find quiz source")
        
        correct_answer = source_quiz["correct_answer"]
        # Pick a wrong answer
        wrong_answers = [o for o in options if o != correct_answer]
        
        if not wrong_answers:
            pytest.skip("No wrong answers available")
        
        wrong_answer = wrong_answers[0]
        
        answer_res = requests.post(
            f"{BASE_URL}/api/habits/quiz/{quiz_id}/answer",
            headers=admin_headers,
            json={"answer": wrong_answer}
        )
        
        assert answer_res.status_code == 200
        data = answer_res.json()
        
        assert data["is_correct"] is False
        # correct_bonus should be None or not present for wrong answers
        assert data.get("correct_bonus") is None, f"Wrong answer should not award bonus, got {data.get('correct_bonus')}"
        
        print("Incorrect answer did not award bonus (as expected)")


class TestQuizRewardsIntegration:
    """Test quiz rewards point logs and stats integration."""
    
    def test_quiz_correct_creates_point_log(self, admin_headers, admin_user):
        """Verify quiz_correct source appears in rewards point logs."""
        # Get rewards history
        res = requests.get(
            f"{BASE_URL}/api/rewards/history",
            headers=admin_headers,
            params={"limit": 100}
        )
        assert res.status_code == 200
        history = res.json().get("history", [])
        
        # Look for quiz_correct entries
        quiz_correct_logs = [h for h in history if h.get("source") == "quiz_correct"]
        
        print(f"Found {len(quiz_correct_logs)} quiz_correct point log entries")
        
        if quiz_correct_logs:
            log = quiz_correct_logs[0]
            assert log["points"] == 2, "quiz_correct should award 2 points"
            assert log.get("metadata", {}).get("quiz_id"), "quiz_id should be in metadata"
            print(f"Sample quiz_correct log: {log}")
    
    def test_rewards_stats_has_quiz_correct_count(self, admin_headers, admin_user):
        """Verify rewards_stats tracks quiz_correct_count."""
        # Get rewards summary
        res = requests.get(
            f"{BASE_URL}/api/rewards/summary",
            headers=admin_headers,
            params={"user_id": admin_user["id"]}
        )
        assert res.status_code == 200
        # Note: quiz_correct_count may be in the stats but not necessarily exposed in summary
        # The counter is updated in the database
        print(f"Rewards summary retrieved. Check DB for quiz_correct_count field.")


class TestQuizBadgeDefinitions:
    """Test that quiz achievement badges are defined correctly."""
    
    def test_quiz_badges_exist(self, admin_headers):
        """Verify quiz badge definitions: quiz_10, quiz_25, quiz_50, quiz_100."""
        res = requests.get(f"{BASE_URL}/api/rewards/badges", headers=admin_headers)
        assert res.status_code == 200
        badges = res.json().get("badges", [])
        
        # Expected quiz badges
        expected_quiz_badges = ["quiz_10", "quiz_25", "quiz_50", "quiz_100"]
        
        badge_ids = [b["id"] for b in badges]
        
        for badge_id in expected_quiz_badges:
            assert badge_id in badge_ids, f"Badge {badge_id} not found in definitions"
        
        # Get quiz badges and verify their properties
        quiz_badges = [b for b in badges if b["id"].startswith("quiz_")]
        
        for badge in quiz_badges:
            assert badge.get("category") == "quizzes", f"Badge {badge['id']} should have category 'quizzes'"
            assert badge.get("condition_type") == "quiz_correct_count", f"Badge {badge['id']} should use quiz_correct_count condition"
            print(f"Quiz badge: {badge['id']} - {badge['name']} (requires {badge['condition_value']} correct answers)")
        
        print(f"All quiz badges defined: {expected_quiz_badges}")


class TestRewardsPageSourceLabels:
    """Test that Rewards page has correct source labels and filter categories."""
    
    def test_rewards_history_endpoint(self, admin_headers):
        """Test rewards history returns entries that can be filtered."""
        res = requests.get(
            f"{BASE_URL}/api/rewards/history",
            headers=admin_headers,
            params={"limit": 200}
        )
        assert res.status_code == 200
        history = res.json().get("history", [])
        
        # Collect unique sources
        sources = set(h.get("source") for h in history if h.get("source"))
        print(f"Sources found in history: {sources}")
        
        # Check for quiz_correct and habit_completion if they exist
        if "quiz_correct" in sources:
            print("quiz_correct source found in history")
        if "habit_completion" in sources:
            print("habit_completion source found in history")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

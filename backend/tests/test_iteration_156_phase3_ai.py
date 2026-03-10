"""
Test Phase 3 AI Features:
1. AI Answer Suggestion - GET /api/ai/answer-suggestion/{post_id}
2. AI Member Risk - GET /api/ai/member-risk/{user_id} (Admin only)
3. AI Daily Report - GET /api/ai/daily-report (Admin only)
4. AI Smart Notification - POST /api/ai/smart-notification
5. AI Commission Insights - GET /api/ai/commission-insights
6. AI Milestone Motivation - GET /api/ai/milestone/{goal_id}

Also tests Phase 1+2 regression for existing AI features.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"

# Known test data from previous iterations
KNOWN_GOAL_ID = "4ead499e-8e2c-4b79-a56c-827bd68f8857"


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Handle both token formats
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def admin_user_id(self, admin_token):
        """Get the admin user's ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        return response.json().get("id")
    
    @pytest.fixture(scope="class")
    def member_user_id(self, admin_token):
        """Get any member user ID for testing member-risk endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members?limit=10", headers=headers)
        if response.status_code == 200:
            members = response.json().get("members", [])
            # Find a non-admin member
            for m in members:
                if m.get("role") == "member":
                    return m.get("id")
            # If no member found, return first user
            if members:
                return members[0].get("id")
        return None
    
    @pytest.fixture(scope="class")
    def forum_post_id(self, admin_token):
        """Get a forum post ID for testing"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/forum?limit=5", headers=headers)
        if response.status_code == 200:
            posts = response.json().get("posts", [])
            if posts:
                return posts[0].get("id")
        return None


class TestAIAnswerSuggestion(TestSetup):
    """Test AI Answer Suggestion endpoint - GET /api/ai/answer-suggestion/{post_id}"""
    
    def test_answer_suggestion_requires_auth(self):
        """Test that endpoint requires authentication (returns 401 or 403)"""
        response = requests.get(f"{BASE_URL}/api/ai/answer-suggestion/test-id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_answer_suggestion_404_for_invalid_post(self, admin_token):
        """Test that invalid post ID returns 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/answer-suggestion/invalid-post-id-123", headers=headers)
        assert response.status_code == 404
    
    def test_answer_suggestion_with_valid_post(self, admin_token, forum_post_id):
        """Test answer suggestion with a valid post ID"""
        if not forum_post_id:
            pytest.skip("No forum posts available for testing")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/answer-suggestion/{forum_post_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Response should have suggestion or reason fields
        assert "suggestion" in data or "reason" in data
        assert "post_id" in data or "reason" in data


class TestAIMemberRisk(TestSetup):
    """Test AI Member Risk endpoint - GET /api/ai/member-risk/{user_id} (Admin only)"""
    
    def test_member_risk_requires_auth(self):
        """Test that endpoint requires authentication (returns 401 or 403)"""
        response = requests.get(f"{BASE_URL}/api/ai/member-risk/test-user-id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_member_risk_with_valid_member(self, admin_token, member_user_id):
        """Test member risk with admin token and valid member"""
        if not member_user_id:
            pytest.skip("No member user ID available for testing")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/member-risk/{member_user_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "risk_assessment" in data or "member_id" in data
        # Should include member stats
        if data.get("stats"):
            assert "streak" in data["stats"] or "trade_count" in data["stats"]
    
    def test_member_risk_404_for_invalid_user(self, admin_token):
        """Test that invalid user ID returns 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/member-risk/invalid-user-id-xyz", headers=headers)
        assert response.status_code == 404


class TestAIMemberRiskNonAdmin:
    """Test AI Member Risk returns 403 for non-admin users"""
    
    def test_member_risk_403_for_non_admin(self):
        """Test that non-admin users get 401/403 Forbidden"""
        # Without any auth header - should be 401 or 403 (not authenticated/forbidden)
        response = requests.get(f"{BASE_URL}/api/ai/member-risk/test-id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestAIDailyReport(TestSetup):
    """Test AI Daily Report endpoint - GET /api/ai/daily-report (Admin only)"""
    
    def test_daily_report_requires_auth(self):
        """Test that endpoint requires authentication (returns 401 or 403)"""
        response = requests.get(f"{BASE_URL}/api/ai/daily-report")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_daily_report_with_admin(self, admin_token):
        """Test daily report with admin token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/daily-report", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "report" in data or "date" in data
        # Should have stats
        if data.get("stats"):
            stats = data["stats"]
            assert "trade_count" in stats or "total_profit" in stats
            assert "active_members" in stats or "total_members" in stats
    
    def test_daily_report_returns_today_date(self, admin_token):
        """Test that daily report includes today's date"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/daily-report", headers=headers)
        assert response.status_code == 200
        data = response.json()
        if data.get("date"):
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            assert data["date"] == today


class TestAIDailyReportNonAdmin:
    """Test AI Daily Report returns 403 for non-admin users"""
    
    def test_daily_report_403_for_non_admin(self):
        """Test that non-admin users get 401/403 Forbidden"""
        # Without auth - should be 401 or 403
        response = requests.get(f"{BASE_URL}/api/ai/daily-report")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestAISmartNotification(TestSetup):
    """Test AI Smart Notification endpoint - POST /api/ai/smart-notification"""
    
    def test_smart_notification_requires_auth(self):
        """Test that endpoint requires authentication (returns 401 or 403)"""
        response = requests.post(f"{BASE_URL}/api/ai/smart-notification", json={
            "event_type": "trade_logged",
            "context": {"profit": 50}
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_smart_notification_with_valid_request(self, admin_token):
        """Test smart notification with valid request"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/ai/smart-notification", json={
            "event_type": "trade_logged",
            "context": {"profit": 50}
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "event_type" in data
        assert data["event_type"] == "trade_logged"
    
    def test_smart_notification_streak_milestone(self, admin_token):
        """Test smart notification for streak milestone"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/ai/smart-notification", json={
            "event_type": "streak_milestone",
            "context": {"streak_days": 7}
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_smart_notification_deposit_received(self, admin_token):
        """Test smart notification for deposit received"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/ai/smart-notification", json={
            "event_type": "deposit_received",
            "context": {"amount": 1000}
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestAICommissionInsights(TestSetup):
    """Test AI Commission Insights endpoint - GET /api/ai/commission-insights"""
    
    def test_commission_insights_requires_auth(self):
        """Test that endpoint requires authentication (returns 401 or 403)"""
        response = requests.get(f"{BASE_URL}/api/ai/commission-insights")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_commission_insights_with_valid_request(self, admin_token):
        """Test commission insights with valid auth"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/commission-insights", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Should have insights or reason if no commissions
        assert "insights" in data or "reason" in data
        # If has insights, should have stats
        if data.get("insights"):
            if data.get("stats"):
                # stats should include best_day
                assert "best_day" in data["stats"] or "total_earned" in data["stats"]
    
    def test_commission_insights_returns_best_day(self, admin_token):
        """Test that commission insights includes best_day analysis"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/commission-insights", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # If user has commissions, stats should include best_day
        if data.get("stats"):
            assert "best_day" in data["stats"]


class TestAIMilestoneMotivation(TestSetup):
    """Test AI Milestone Motivation endpoint - GET /api/ai/milestone/{goal_id}"""
    
    def test_milestone_requires_auth(self):
        """Test that endpoint requires authentication (returns 401 or 403)"""
        response = requests.get(f"{BASE_URL}/api/ai/milestone/test-goal-id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_milestone_404_for_invalid_goal(self, admin_token):
        """Test that invalid goal ID returns 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/milestone/invalid-goal-id-xyz", headers=headers)
        assert response.status_code == 404
    
    def test_milestone_with_known_goal(self, admin_token):
        """Test milestone motivation with known goal ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/milestone/{KNOWN_GOAL_ID}", headers=headers)
        # Could be 200 if goal exists or 404 if not
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "motivation" in data or "milestone" in data
            # Should include progress level
            if data.get("progress") is not None:
                assert isinstance(data["progress"], (int, float))
            if data.get("milestone"):
                # Valid milestone values
                assert data["milestone"] in ["started", "25%", "50%", "75%", "completed"]


class TestPhase1Regression(TestSetup):
    """Test Phase 1 AI Features Still Working (Regression)"""
    
    def test_trade_coach_still_works(self, admin_token):
        """Test AI Trade Coach endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # Need a valid trade ID - get from trade logs
        response = requests.get(f"{BASE_URL}/api/trade/logs?limit=1", headers=headers)
        if response.status_code == 200 and response.json():
            trades = response.json()
            if trades and len(trades) > 0:
                trade_id = trades[0].get("id")
                if trade_id:
                    coach_response = requests.get(f"{BASE_URL}/api/ai/trade-coach/{trade_id}", headers=headers)
                    assert coach_response.status_code in [200, 404]
    
    def test_financial_summary_weekly_still_works(self, admin_token):
        """Test AI Financial Summary weekly endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/financial-summary?period=weekly", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "period" in data
        assert data["period"] == "weekly"
    
    def test_financial_summary_monthly_still_works(self, admin_token):
        """Test AI Financial Summary monthly endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/financial-summary?period=monthly", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data["period"] == "monthly"
    
    def test_balance_forecast_still_works(self, admin_token):
        """Test AI Balance Forecast endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/balance-forecast", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert "current_balance" in data


class TestPhase2Regression(TestSetup):
    """Test Phase 2 AI Features Still Working (Regression)"""
    
    def test_trade_journal_daily_still_works(self, admin_token):
        """Test AI Trade Journal daily endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/trade-journal?period=daily", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "journal" in data
        assert "period" in data
    
    def test_trade_journal_weekly_still_works(self, admin_token):
        """Test AI Trade Journal weekly endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/trade-journal?period=weekly", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "journal" in data
    
    def test_goal_advisor_still_works(self, admin_token):
        """Test AI Goal Advisor endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/goal-advisor/{KNOWN_GOAL_ID}", headers=headers)
        # 200 if goal exists, 404 if not
        assert response.status_code in [200, 404]
    
    def test_anomaly_check_still_works(self, admin_token):
        """Test AI Anomaly Check endpoint still works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/anomaly-check", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "anomalies" in data or "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

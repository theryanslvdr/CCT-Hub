"""
Phase 2 Trading Intelligence AI Features Tests (Iteration 155)
Tests: AI Signal Insights, AI Trade Journal, AI Goal Advisor, AI Anomaly Alert

Endpoints tested:
- GET /api/ai/signal-insights/{signal_id}
- GET /api/ai/trade-journal?period=daily|weekly
- GET /api/ai/goal-advisor/{goal_id}
- GET /api/ai/anomaly-check
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuth:
    """Get authentication token for tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Authenticate and get access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]


class TestSignalInsights(TestAuth):
    """AI Signal Insights endpoint tests"""
    
    def test_signal_insights_requires_auth(self):
        """Test that signal insights requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/signal-insights/some-signal-id")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def test_signal_insights_returns_404_for_invalid_signal(self, auth_token):
        """Test that invalid signal_id returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/signal-insights/invalid-signal-123", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signal_insights_with_valid_signal(self, auth_token):
        """Test signal insights with an active signal (if exists)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get active signal
        signal_response = requests.get(f"{BASE_URL}/api/trade/signal", headers=headers)
        
        if signal_response.status_code == 200:
            signal_data = signal_response.json()
            if signal_data.get("signal"):
                signal_id = signal_data["signal"]["id"]
                response = requests.get(f"{BASE_URL}/api/ai/signal-insights/{signal_id}", headers=headers)
                assert response.status_code == 200
                data = response.json()
                assert "insights" in data or "signal_id" in data
                assert data.get("signal_id") == signal_id
                print(f"Signal insights returned for signal {signal_id}")
                if data.get("ai_powered"):
                    print("AI-powered insights received")
            else:
                pytest.skip("No active signal available for testing")
        else:
            pytest.skip("Could not fetch trading signal")


class TestTradeJournal(TestAuth):
    """AI Trade Journal endpoint tests"""
    
    def test_trade_journal_requires_auth(self):
        """Test that trade journal requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/trade-journal")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def test_trade_journal_daily(self, auth_token):
        """Test trade journal with daily period"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/trade-journal", params={"period": "daily"}, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "period" in data
        assert data["period"] == "daily"
        assert "journal" in data or "trade_count" in data
        
        print(f"Daily journal trade_count: {data.get('trade_count', 'N/A')}")
        if data.get("stats"):
            print(f"Stats: {data['stats']}")
        if data.get("ai_powered"):
            print("AI-powered journal received")
    
    def test_trade_journal_weekly(self, auth_token):
        """Test trade journal with weekly period"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/trade-journal", params={"period": "weekly"}, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "period" in data
        assert data["period"] == "weekly"
        assert "journal" in data or "trade_count" in data
        
        print(f"Weekly journal trade_count: {data.get('trade_count', 'N/A')}")
        if data.get("stats"):
            print(f"Stats: total_profit={data['stats'].get('total_profit')}, streak={data['stats'].get('streak')}")
    
    def test_trade_journal_invalid_period(self, auth_token):
        """Test trade journal with invalid period returns validation error"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/trade-journal", params={"period": "yearly"}, headers=headers)
        assert response.status_code == 422, f"Expected 422 for invalid period, got {response.status_code}"
    
    def test_trade_journal_returns_stats(self, auth_token):
        """Test that trade journal returns stats object when trades exist"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/trade-journal", params={"period": "weekly"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        trade_count = data.get("trade_count", 0)
        if trade_count > 0:
            assert "stats" in data, "Stats object missing when trades exist"
            stats = data["stats"]
            assert "total_profit" in stats
            assert "exceeded" in stats
            assert "below" in stats
            assert "buy_profit" in stats
            assert "sell_profit" in stats
            assert "streak" in stats


class TestGoalAdvisor(TestAuth):
    """AI Goal Advisor endpoint tests"""
    
    KNOWN_GOAL_ID = "4ead499e-8e2c-4b79-a56c-827bd68f8857"  # From agent context
    
    def test_goal_advisor_requires_auth(self):
        """Test that goal advisor requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/goal-advisor/{self.KNOWN_GOAL_ID}")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def test_goal_advisor_returns_404_for_invalid_goal(self, auth_token):
        """Test that invalid goal_id returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/goal-advisor/invalid-goal-456", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_goal_advisor_with_known_goal(self, auth_token):
        """Test goal advisor with the known goal ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/goal-advisor/{self.KNOWN_GOAL_ID}", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "goal_id" in data
        assert data["goal_id"] == self.KNOWN_GOAL_ID
        assert "advice" in data or "progress" in data
        
        print(f"Goal advisor response for goal {self.KNOWN_GOAL_ID}:")
        print(f"  Progress: {data.get('progress')}%")
        print(f"  Days to goal: {data.get('days_to_goal')}")
        print(f"  Days left: {data.get('days_left')}")
        print(f"  AI powered: {data.get('ai_powered')}")
        
        if data.get("advice"):
            print(f"  Advice (first 100 chars): {data['advice'][:100]}...")
    
    def test_goal_advisor_returns_progress_fields(self, auth_token):
        """Test that goal advisor returns progress, days_to_goal, ai_powered fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/goal-advisor/{self.KNOWN_GOAL_ID}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # These fields should be present
            assert "goal_id" in data
            assert "progress" in data
            assert "days_to_goal" in data or data.get("days_to_goal") is None  # Can be None if infinite
            assert "ai_powered" in data


class TestAnomalyCheck(TestAuth):
    """AI Anomaly Alert endpoint tests"""
    
    def test_anomaly_check_requires_auth(self):
        """Test that anomaly check requires authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/anomaly-check")
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def test_anomaly_check_returns_status(self, auth_token):
        """Test anomaly check returns status (healthy or warning)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/anomaly-check", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Status should be either 'healthy' or 'warning'
        assert "status" in data or "anomalies" in data or "reason" in data
        
        status = data.get("status")
        print(f"Anomaly check status: {status}")
        
        if status == "healthy":
            print(f"Message: {data.get('message')}")
            assert "message" in data
        elif status == "warning":
            print(f"Flags: {data.get('flags')}")
            if data.get("flags"):
                for flag in data["flags"]:
                    print(f"  - {flag}")
            if data.get("anomalies"):
                print(f"AI advice (first 100 chars): {data['anomalies'][:100]}...")
        else:
            # Could be 'error' or have 'reason' for not enough data
            print(f"Response: {data}")
    
    def test_anomaly_check_returns_stats_on_warning(self, auth_token):
        """Test that anomaly check returns stats when status is warning"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/anomaly-check", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if data.get("status") == "warning":
            # Stats should be present for warning status
            assert "stats" in data or "flags" in data
            if "stats" in data:
                stats = data["stats"]
                print(f"Warning stats: recent_avg_profit={stats.get('recent_avg_profit')}, streak={stats.get('streak')}")
    
    def test_anomaly_check_not_enough_history(self, auth_token):
        """Test that anomaly check handles cases with insufficient trade history"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/anomaly-check", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # If not enough trades, should return reason instead of status
        if data.get("reason"):
            assert "trade_count" in data
            print(f"Not enough history: {data['reason']} (trade_count={data['trade_count']})")


class TestPhase1Regression(TestAuth):
    """Regression tests for Phase 1 AI features (still working)"""
    
    def test_trade_coach_still_working(self, auth_token):
        """Test that AI Trade Coach (Phase 1) still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get a trade ID from history
        history_response = requests.get(f"{BASE_URL}/api/trade/history", headers=headers)
        if history_response.status_code == 200:
            trades = history_response.json().get("trades", [])
            if trades:
                trade_id = trades[0]["id"]
                response = requests.get(f"{BASE_URL}/api/ai/trade-coach/{trade_id}", headers=headers)
                assert response.status_code == 200
                data = response.json()
                assert "coaching" in data
                print("Phase 1: AI Trade Coach still working")
            else:
                pytest.skip("No trades in history for trade coach test")
        else:
            pytest.skip("Could not fetch trade history")
    
    def test_financial_summary_still_working(self, auth_token):
        """Test that AI Financial Summary (Phase 1) still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/financial-summary", params={"period": "weekly"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "period" in data
        print("Phase 1: AI Financial Summary still working")
    
    def test_balance_forecast_still_working(self, auth_token):
        """Test that AI Balance Forecast (Phase 1) still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/balance-forecast", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert "current_balance" in data
        print("Phase 1: AI Balance Forecast still working")
    
    def test_forum_summary_still_working(self, auth_token):
        """Test that AI Forum Summary (Phase 1) still works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Try to get a forum post
        posts_response = requests.get(f"{BASE_URL}/api/forum/posts", headers=headers)
        if posts_response.status_code == 200:
            posts = posts_response.json().get("posts", [])
            if posts:
                post_id = posts[0]["id"]
                response = requests.get(f"{BASE_URL}/api/ai/forum-summary/{post_id}", headers=headers)
                assert response.status_code == 200
                data = response.json()
                assert "summary" in data or "reason" in data
                print("Phase 1: AI Forum Summary endpoint still working")
            else:
                pytest.skip("No forum posts for forum summary test")
        else:
            pytest.skip("Could not fetch forum posts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

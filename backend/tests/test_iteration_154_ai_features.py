"""
Iteration 154: Phase 1 AI Features Testing
Tests for:
1. AI Trade Coach - GET /api/ai/trade-coach/{trade_id}
2. AI Financial Summary - GET /api/ai/financial-summary?period=weekly|monthly
3. AI Balance Forecast - GET /api/ai/balance-forecast
4. AI Forum Summary - GET /api/ai/forum-summary/{post_id}
5. AI Caching - Second calls should return cached responses
"""
import os
import pytest
import requests
import time

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for the test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # Token field is 'access_token' based on previous iteration notes
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data.keys()}"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAITradeCoach:
    """AI Trade Coach endpoint tests - GET /api/ai/trade-coach/{trade_id}"""
    
    def test_trade_coach_endpoint_requires_auth(self):
        """Trade coach should require authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/trade-coach/fake_trade_id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Trade coach endpoint requires authentication (returns 403)")
    
    def test_trade_coach_returns_404_for_invalid_trade(self, auth_headers):
        """Trade coach should return 404 for non-existent trade"""
        response = requests.get(
            f"{BASE_URL}/api/ai/trade-coach/nonexistent_trade_12345",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Trade coach returns 404 for invalid trade ID")
    
    def test_trade_coach_with_valid_trade(self, auth_headers):
        """Trade coach should return coaching for a valid trade"""
        # First get trade history to find a valid trade_id
        history_response = requests.get(
            f"{BASE_URL}/api/trade/history?page=1&page_size=5",
            headers=auth_headers
        )
        
        if history_response.status_code != 200:
            pytest.skip("Trade history endpoint not accessible")
        
        trades = history_response.json().get("trades", [])
        if not trades:
            pytest.skip("No trades available to test AI coach with")
        
        trade_id = trades[0].get("id")
        print(f"Testing AI Trade Coach with trade_id: {trade_id}")
        
        # Call trade coach endpoint
        response = requests.get(
            f"{BASE_URL}/api/ai/trade-coach/{trade_id}",
            headers=auth_headers,
            timeout=30  # AI calls may take longer
        )
        
        assert response.status_code == 200, f"Trade coach failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "coaching" in data, f"Missing 'coaching' field in response: {data.keys()}"
        assert isinstance(data["coaching"], str), "Coaching should be a string"
        assert len(data["coaching"]) > 0, "Coaching should not be empty"
        
        print(f"PASS: AI Trade Coach returned coaching feedback")
        print(f"  - Coaching length: {len(data['coaching'])} characters")
        print(f"  - First 100 chars: {data['coaching'][:100]}...")


class TestAIFinancialSummary:
    """AI Financial Summary endpoint tests - GET /api/ai/financial-summary"""
    
    def test_financial_summary_requires_auth(self):
        """Financial summary should require authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/financial-summary")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Financial summary endpoint requires authentication (returns 403)")
    
    def test_financial_summary_weekly(self, auth_headers):
        """Financial summary should return weekly analysis with stats"""
        response = requests.get(
            f"{BASE_URL}/api/ai/financial-summary?period=weekly",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Weekly summary failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "summary" in data, f"Missing 'summary' field: {data.keys()}"
        assert "period" in data, f"Missing 'period' field: {data.keys()}"
        assert "stats" in data, f"Missing 'stats' field: {data.keys()}"
        
        assert data["period"] == "weekly", f"Period should be 'weekly', got: {data['period']}"
        assert isinstance(data["stats"], dict), "Stats should be a dictionary"
        
        # Stats should contain trading metrics
        expected_stats_fields = ["trade_count", "total_profit"]
        for field in expected_stats_fields:
            assert field in data["stats"], f"Missing '{field}' in stats: {data['stats'].keys()}"
        
        print("PASS: AI Financial Summary (weekly) returned valid response")
        print(f"  - Period: {data['period']}")
        print(f"  - Stats: {data['stats']}")
        print(f"  - Summary length: {len(data['summary'])} chars")
    
    def test_financial_summary_monthly(self, auth_headers):
        """Financial summary should return monthly analysis (30 days)"""
        response = requests.get(
            f"{BASE_URL}/api/ai/financial-summary?period=monthly",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Monthly summary failed: {response.text}"
        data = response.json()
        
        assert data["period"] == "monthly", f"Period should be 'monthly', got: {data['period']}"
        assert "summary" in data
        assert "stats" in data
        
        print("PASS: AI Financial Summary (monthly) returned valid response")
        print(f"  - Period: {data['period']}")
        print(f"  - Stats keys: {list(data['stats'].keys())}")
    
    def test_financial_summary_invalid_period(self, auth_headers):
        """Financial summary should reject invalid period"""
        response = requests.get(
            f"{BASE_URL}/api/ai/financial-summary?period=invalid",
            headers=auth_headers
        )
        # Should be 422 (validation error) due to regex constraint
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Financial summary rejects invalid period parameter")


class TestAIBalanceForecast:
    """AI Balance Forecast endpoint tests - GET /api/ai/balance-forecast"""
    
    def test_balance_forecast_requires_auth(self):
        """Balance forecast should require authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/balance-forecast")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Balance forecast endpoint requires authentication (returns 403)")
    
    def test_balance_forecast_returns_projection(self, auth_headers):
        """Balance forecast should return AI-powered projection with 7/30/90 day forecasts"""
        response = requests.get(
            f"{BASE_URL}/api/ai/balance-forecast",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Balance forecast failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "forecast" in data, f"Missing 'forecast' field: {data.keys()}"
        assert "current_balance" in data, f"Missing 'current_balance' field: {data.keys()}"
        assert "ai_powered" in data, f"Missing 'ai_powered' flag: {data.keys()}"
        
        # Current balance should be a number
        assert isinstance(data["current_balance"], (int, float)), "current_balance should be numeric"
        
        # ai_powered flag indicates whether AI was used or fallback math
        assert isinstance(data["ai_powered"], bool), "ai_powered should be boolean"
        
        print("PASS: AI Balance Forecast returned valid response")
        print(f"  - Current balance: ${data['current_balance']:.2f}")
        print(f"  - AI powered: {data['ai_powered']}")
        print(f"  - Forecast length: {len(data['forecast'])} chars")
        print(f"  - Forecast preview: {data['forecast'][:150]}...")


class TestAIForumSummary:
    """AI Forum Summary endpoint tests - GET /api/ai/forum-summary/{post_id}"""
    
    def test_forum_summary_requires_auth(self):
        """Forum summary should require authentication"""
        response = requests.get(f"{BASE_URL}/api/ai/forum-summary/fake_post_id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Forum summary endpoint requires authentication (returns 403)")
    
    def test_forum_summary_returns_404_for_invalid_post(self, auth_headers):
        """Forum summary should return 404 for non-existent post"""
        response = requests.get(
            f"{BASE_URL}/api/ai/forum-summary/nonexistent_post_12345",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Forum summary returns 404 for invalid post ID")
    
    def test_forum_summary_with_valid_post(self, auth_headers):
        """Forum summary should return summary for posts with 3+ comments"""
        # First get a list of forum posts
        posts_response = requests.get(
            f"{BASE_URL}/api/forum/posts?page=1&page_size=10",
            headers=auth_headers
        )
        
        if posts_response.status_code != 200:
            pytest.skip("Forum posts endpoint not accessible")
        
        posts = posts_response.json().get("posts", [])
        if not posts:
            pytest.skip("No forum posts available to test AI summary with")
        
        # Find a post with 3+ comments
        post_with_comments = None
        for post in posts:
            comment_count = post.get("comment_count", 0)
            if comment_count >= 3:
                post_with_comments = post
                break
        
        if not post_with_comments:
            # Test with any post - it should return reason for short threads
            post_with_comments = posts[0]
            print(f"Testing with post that has {post_with_comments.get('comment_count', 0)} comments")
        
        post_id = post_with_comments.get("id")
        comment_count = post_with_comments.get("comment_count", 0)
        print(f"Testing AI Forum Summary with post_id: {post_id} ({comment_count} comments)")
        
        # Call forum summary endpoint
        response = requests.get(
            f"{BASE_URL}/api/ai/forum-summary/{post_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Forum summary failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "comment_count" in data, f"Missing 'comment_count' in response: {data.keys()}"
        
        if comment_count >= 3:
            # Should have summary or reason
            if data.get("summary"):
                print(f"PASS: AI Forum Summary returned summary")
                print(f"  - Summary length: {len(data['summary'])} chars")
            else:
                assert "reason" in data, f"Expected 'summary' or 'reason': {data.keys()}"
                print(f"PASS: AI Forum Summary returned reason: {data['reason']}")
        else:
            # Thread too short
            assert data.get("summary") is None or "reason" in data
            print(f"PASS: AI Forum Summary correctly handled short thread")
            print(f"  - Comment count: {data['comment_count']}")
            if "reason" in data:
                print(f"  - Reason: {data['reason']}")


class TestAICaching:
    """AI Caching tests - Second calls should return cached responses (faster)"""
    
    def test_financial_summary_caching(self, auth_headers):
        """Second call to financial summary should be faster (cached)"""
        # First call
        start1 = time.time()
        response1 = requests.get(
            f"{BASE_URL}/api/ai/financial-summary?period=weekly",
            headers=auth_headers,
            timeout=30
        )
        time1 = time.time() - start1
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Small delay
        time.sleep(0.5)
        
        # Second call (should be cached)
        start2 = time.time()
        response2 = requests.get(
            f"{BASE_URL}/api/ai/financial-summary?period=weekly",
            headers=auth_headers,
            timeout=30
        )
        time2 = time.time() - start2
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Both should return same summary content
        assert data1["summary"] == data2["summary"], "Cached response should match original"
        
        print(f"PASS: AI Caching test completed")
        print(f"  - First call: {time1:.2f}s")
        print(f"  - Second call (cached): {time2:.2f}s")
        
        # Note: We can't strictly assert time2 < time1 because network latency varies
        # but we verify both return same data (indicating cache hit)
    
    def test_balance_forecast_caching(self, auth_headers):
        """Second call to balance forecast should return cached response"""
        # First call
        response1 = requests.get(
            f"{BASE_URL}/api/ai/balance-forecast",
            headers=auth_headers,
            timeout=30
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Small delay
        time.sleep(0.5)
        
        # Second call (should be cached)
        response2 = requests.get(
            f"{BASE_URL}/api/ai/balance-forecast",
            headers=auth_headers,
            timeout=30
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Both should return same forecast content if AI was used
        if data1.get("ai_powered") and data2.get("ai_powered"):
            assert data1["forecast"] == data2["forecast"], "Cached response should match original"
            print("PASS: Balance forecast caching verified (same response)")
        else:
            print("PASS: Balance forecast returned (ai_powered may vary per call)")


class TestAIEndpointExists:
    """Verify all AI endpoints exist and are routed correctly"""
    
    def test_all_ai_endpoints_exist(self, auth_headers):
        """Verify all 4 AI endpoints are accessible"""
        endpoints = [
            ("/api/ai/trade-coach/test_id", 404),  # 404 expected for invalid trade
            ("/api/ai/financial-summary", 200),
            ("/api/ai/balance-forecast", 200),
            ("/api/ai/forum-summary/test_id", 404),  # 404 expected for invalid post
        ]
        
        for endpoint, expected_status in endpoints:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=auth_headers,
                timeout=30
            )
            # Allow 200 or expected 404 for invalid IDs
            assert response.status_code in [200, expected_status], \
                f"Endpoint {endpoint} returned {response.status_code}, expected {expected_status}"
            print(f"  - {endpoint}: {response.status_code} (expected: {expected_status})")
        
        print("PASS: All AI endpoints exist and are routed correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

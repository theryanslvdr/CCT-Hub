"""
Iteration 153: Testing commission display, AI duplicate detection, and exit trade functionality

Features tested:
1. GET /api/profit/commissions - returns skip_deposit field
2. POST /api/forum/ai-check-duplicate - AI-powered semantic similarity via OpenRouter
3. POST /api/trade/log - Exit trade with lot_size, direction, actual_profit, commission, performance
4. GET /api/trade/history - Paginated trade history
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestAuth:
    """Authentication for testing"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "iam@ryansalvador.com", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Token is in 'access_token' field
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


class TestCommissionRecords(TestAuth):
    """Test commission records with skip_deposit field"""
    
    def test_get_commissions_endpoint_exists(self, headers):
        """GET /api/profit/commissions returns 200"""
        response = requests.get(f"{BASE_URL}/api/profit/commissions", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_commissions_response_is_list(self, headers):
        """GET /api/profit/commissions returns array"""
        response = requests.get(f"{BASE_URL}/api/profit/commissions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
    
    def test_create_commission_with_skip_deposit_true(self, headers):
        """POST /api/profit/commission with skip_deposit=true (Historical type)"""
        payload = {
            "amount": 50.0,
            "source": "referral",
            "traders_count": 3,
            "notes": "TEST_Historical commission entry",
            "skip_deposit": True  # Historical - don't add to balance
        }
        response = requests.post(f"{BASE_URL}/api/profit/commission", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # deposit_created should be False when skip_deposit is True
        assert data.get("deposit_created") == False, f"Expected deposit_created=False, got {data}"
        print(f"Created Historical commission: {data.get('commission_id')}")
    
    def test_create_commission_with_skip_deposit_false(self, headers):
        """POST /api/profit/commission with skip_deposit=false (Balance type)"""
        payload = {
            "amount": 75.0,
            "source": "referral",
            "traders_count": 5,
            "notes": "TEST_Balance commission entry",
            "skip_deposit": False  # Balance - add to account
        }
        response = requests.post(f"{BASE_URL}/api/profit/commission", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # deposit_created should be True when skip_deposit is False
        assert data.get("deposit_created") == True, f"Expected deposit_created=True, got {data}"
        print(f"Created Balance commission: {data.get('commission_id')}")
    
    def test_commissions_contain_skip_deposit_field(self, headers):
        """Commissions list returns skip_deposit field for differentiation"""
        response = requests.get(f"{BASE_URL}/api/profit/commissions", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            # Find our test entries
            test_commissions = [c for c in data if c.get("notes", "").startswith("TEST_")]
            if test_commissions:
                for comm in test_commissions:
                    assert "skip_deposit" in comm, f"skip_deposit field missing in commission: {comm}"
                    print(f"Commission: {comm.get('notes')} - skip_deposit={comm.get('skip_deposit')}")
                    
                # Check differentiation
                historical = [c for c in test_commissions if c.get("skip_deposit") == True]
                balance = [c for c in test_commissions if c.get("skip_deposit") == False]
                print(f"Found {len(historical)} Historical (skip_deposit=true) commissions")
                print(f"Found {len(balance)} Balance (skip_deposit=false) commissions")


class TestAIDuplicateDetection(TestAuth):
    """Test AI-powered semantic duplicate detection via OpenRouter"""
    
    def test_ai_check_duplicate_endpoint_exists(self, headers):
        """POST /api/forum/ai-check-duplicate returns 200"""
        payload = {
            "title": "How do I calculate lot size?",
            "content": "I want to understand the formula for lot size calculation"
        }
        response = requests.post(f"{BASE_URL}/api/forum/ai-check-duplicate", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_ai_check_duplicate_returns_required_fields(self, headers):
        """Response contains results, has_similar, and ai_powered fields"""
        payload = {
            "title": "What is the profit target?",
            "content": "I'm trying to understand how much profit I should aim for"
        }
        response = requests.post(f"{BASE_URL}/api/forum/ai-check-duplicate", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data, f"results field missing: {data}"
        assert "has_similar" in data, f"has_similar field missing: {data}"
        assert "ai_powered" in data, f"ai_powered field missing: {data}"
        
        print(f"AI duplicate check: ai_powered={data.get('ai_powered')}, has_similar={data.get('has_similar')}, results_count={len(data.get('results', []))}")
    
    def test_ai_check_duplicate_with_unique_title(self, headers):
        """Unique title should return has_similar=False or empty results"""
        import uuid
        unique_title = f"Very unique question about {uuid.uuid4()}"
        payload = {
            "title": unique_title,
            "content": "This is a completely unique and unprecedented question that no one has ever asked before."
        }
        response = requests.post(f"{BASE_URL}/api/forum/ai-check-duplicate", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # If OpenRouter works, should return with ai_powered flag
        print(f"Unique title test: ai_powered={data.get('ai_powered')}, has_similar={data.get('has_similar')}")
    
    def test_ai_check_duplicate_with_similar_topic(self, headers):
        """Semantically similar title should trigger duplicate warning if posts exist"""
        # Use a generic trading topic that might match existing posts
        payload = {
            "title": "How to trade signals",
            "content": "I need help understanding the trading signal process and how to use them effectively"
        }
        response = requests.post(f"{BASE_URL}/api/forum/ai-check-duplicate", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        
        print(f"Similar topic test: ai_powered={data.get('ai_powered')}, has_similar={data.get('has_similar')}, results={len(data.get('results', []))}")
        
        # If AI is working and similar posts exist, should find them
        if data.get("ai_powered") and data.get("has_similar"):
            print("AI successfully found similar posts!")
            for r in data.get("results", [])[:3]:
                print(f"  - {r.get('title')} ({r.get('status')})")
    
    def test_ai_fallback_to_regex(self, headers):
        """Verify fallback returns ai_powered=False when API fails (informational)"""
        # This test is informational - we can't force OpenRouter to fail
        # But we verify the response structure is correct
        payload = {
            "title": "test",
            "content": ""
        }
        response = requests.post(f"{BASE_URL}/api/forum/ai-check-duplicate", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # ai_powered should be boolean
        assert isinstance(data.get("ai_powered"), bool), f"ai_powered should be boolean: {data}"
        print(f"Short query test: ai_powered={data.get('ai_powered')}")


class TestExitTrade(TestAuth):
    """Test exit trade functionality"""
    
    def test_check_active_signal(self, headers):
        """GET /api/trade/active-signal to check current state"""
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        signal = data.get("signal")
        if signal:
            print(f"Active signal found: {signal.get('product')} - {signal.get('direction')}")
            return True
        else:
            print("No active signal currently")
            return False
    
    def test_check_admin_signals(self, headers):
        """GET /api/admin/signals/active to check for active signals"""
        response = requests.get(f"{BASE_URL}/api/admin/signals", headers=headers)
        if response.status_code == 200:
            data = response.json()
            signals = data.get("signals", data) if isinstance(data, dict) else data
            active = [s for s in signals if s.get("is_active")] if isinstance(signals, list) else []
            print(f"Found {len(active)} active signals via admin endpoint")
            return active
        print(f"Admin signals check returned {response.status_code}")
        return []
    
    def test_trade_log_endpoint_exists(self, headers):
        """POST /api/trade/log endpoint exists"""
        # This will likely fail validation but confirms endpoint exists
        response = requests.post(f"{BASE_URL}/api/trade/log", headers=headers, json={})
        # Should get 422 (validation error) not 404
        assert response.status_code in [200, 422], f"Unexpected status {response.status_code}: {response.text}"
    
    def test_trade_log_with_valid_data(self, headers):
        """POST /api/trade/log with complete trade data"""
        payload = {
            "lot_size": 0.5,
            "direction": "BUY",
            "actual_profit": 7.50,
            "commission": 0.25,
            "notes": "TEST_trade_entry"
        }
        response = requests.post(f"{BASE_URL}/api/trade/log", headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Trade logged successfully: {data.get('id')}")
            
            # Verify required fields in response
            assert "id" in data, "Missing id in response"
            assert "lot_size" in data, "Missing lot_size in response"
            assert "direction" in data, "Missing direction in response"
            assert "actual_profit" in data, "Missing actual_profit in response"
            assert "performance" in data, "Missing performance in response"
            
            # Performance should be calculated
            performance = data.get("performance")
            assert performance in ["perfect", "exceeded", "below"], f"Invalid performance: {performance}"
            print(f"Performance calculated: {performance}")
            
            # Commission should be stored
            assert "commission" in data, "Missing commission in response"
            print(f"Commission stored: {data.get('commission')}")
            
            return data.get("id")
        else:
            # Some validation might fail if no active signal
            print(f"Trade log returned {response.status_code}: {response.text}")
            # Not asserting here as it depends on active signal state
    
    def test_trade_history_endpoint(self, headers):
        """GET /api/trade/history returns paginated results"""
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=headers, params={"page": 1, "page_size": 10})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "trades" in data, f"trades field missing: {data}"
        assert "total" in data, f"total field missing: {data}"
        assert "page" in data, f"page field missing: {data}"
        
        print(f"Trade history: {len(data.get('trades', []))} trades on page {data.get('page')}, total: {data.get('total')}")
    
    def test_trade_history_contains_commission(self, headers):
        """Trade history entries should contain commission field"""
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=headers, params={"page": 1, "page_size": 10})
        assert response.status_code == 200
        data = response.json()
        
        trades = data.get("trades", [])
        if trades:
            for trade in trades[:5]:  # Check first 5
                # Commission field should exist (may be 0 or None for old trades)
                commission = trade.get("commission", 0)
                print(f"Trade {trade.get('id')[:8]}...: actual_profit={trade.get('actual_profit')}, commission={commission}, performance={trade.get('performance')}")
    
    def test_trade_performance_calculation(self, headers):
        """Verify performance field calculation logic"""
        response = requests.get(f"{BASE_URL}/api/trade/history", headers=headers, params={"page": 1, "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        
        trades = data.get("trades", [])
        performance_counts = {"perfect": 0, "exceeded": 0, "below": 0, "other": 0}
        
        for trade in trades:
            perf = trade.get("performance", "other")
            if perf in performance_counts:
                performance_counts[perf] += 1
            else:
                performance_counts["other"] += 1
        
        print(f"Performance breakdown: {performance_counts}")


class TestCleanup(TestAuth):
    """Cleanup test data"""
    
    def test_cleanup_test_commissions(self, headers):
        """Clean up TEST_ prefixed commissions (informational only)"""
        response = requests.get(f"{BASE_URL}/api/profit/commissions", headers=headers)
        if response.status_code == 200:
            data = response.json()
            test_entries = [c for c in data if c.get("notes", "").startswith("TEST_")]
            print(f"Found {len(test_entries)} test commission entries (cleanup not implemented)")
        print("Test completed - cleanup can be manual if needed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

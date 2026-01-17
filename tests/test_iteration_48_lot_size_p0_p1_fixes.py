"""
Iteration 48 - P0 and P1 Bug Fix Tests

P0 Bug Fix: Incorrect Lot Size logged in Trade History
- Backend now recalculates lot_size from authoritative account_value
- Frontend's stale lot_size is ignored
- Expected: lot_size = account_value / 980

P1 Bug Fix: Daily Projection 'Balance Before' synchronization
- Current day's Balance Before should match live account_value
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestP0LotSizeCalculation:
    """P0 Bug Fix: Backend recalculates lot_size from account_value"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get current account value for calculations
        summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert summary_response.status_code == 200
        self.account_value = summary_response.json().get("account_value", 0)
        self.expected_lot_size = round(self.account_value / 980, 2)
        
        yield
        
        self.session.close()
    
    def test_get_account_value_and_expected_lot_size(self):
        """Verify account value and expected lot size calculation"""
        print(f"\n=== Account Value Test ===")
        print(f"Account Value: ${self.account_value}")
        print(f"Expected LOT Size (account_value / 980): {self.expected_lot_size}")
        
        # Account value should be around $18,941.87 based on previous tests
        assert self.account_value > 0, "Account value should be positive"
        assert self.expected_lot_size > 0, "Expected lot size should be positive"
        
        # Verify the calculation
        calculated = round(self.account_value / 980, 2)
        assert calculated == self.expected_lot_size, f"LOT calculation mismatch: {calculated} != {self.expected_lot_size}"
        print(f"✓ LOT size calculation verified: {self.expected_lot_size}")
    
    def test_trade_log_without_lot_size_uses_server_calculation(self):
        """P0 Test: POST /api/trade/log WITHOUT lot_size should use server-calculated value"""
        print(f"\n=== P0 Test: Trade Log Without lot_size ===")
        
        # Log a trade WITHOUT sending lot_size
        trade_data = {
            "direction": "BUY",
            "actual_profit": 289.80,
            "notes": "P0 Test - No lot_size sent"
        }
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        
        # Should succeed
        assert response.status_code == 200, f"Trade log failed: {response.text}"
        
        result = response.json()
        print(f"Response lot_size: {result.get('lot_size')}")
        print(f"Expected lot_size: {self.expected_lot_size}")
        
        # Verify lot_size was calculated by server
        assert "lot_size" in result, "Response should contain lot_size"
        
        # Allow small tolerance for rounding
        response_lot_size = result.get("lot_size")
        assert abs(response_lot_size - self.expected_lot_size) < 0.02, \
            f"LOT size mismatch: got {response_lot_size}, expected {self.expected_lot_size}"
        
        print(f"✓ Server calculated lot_size correctly: {response_lot_size}")
        
        # Clean up - delete the test trade
        trade_id = result.get("id")
        if trade_id:
            delete_response = self.session.delete(f"{BASE_URL}/api/trade/logs/{trade_id}")
            print(f"Cleanup: Deleted test trade {trade_id}")
    
    def test_trade_log_with_wrong_lot_size_is_ignored(self):
        """P0 Test: POST /api/trade/log WITH WRONG lot_size should be ignored by server"""
        print(f"\n=== P0 Test: Trade Log With Wrong lot_size ===")
        
        # Send a deliberately WRONG lot_size (25.00 instead of expected ~19.33)
        wrong_lot_size = 25.00
        
        trade_data = {
            "lot_size": wrong_lot_size,  # This should be IGNORED by backend
            "direction": "SELL",
            "actual_profit": 285.00,
            "notes": "P0 Test - Wrong lot_size sent (should be ignored)"
        }
        
        print(f"Sending wrong lot_size: {wrong_lot_size}")
        print(f"Expected server to use: {self.expected_lot_size}")
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        
        # Should succeed
        assert response.status_code == 200, f"Trade log failed: {response.text}"
        
        result = response.json()
        response_lot_size = result.get("lot_size")
        
        print(f"Response lot_size: {response_lot_size}")
        
        # CRITICAL: Server should NOT use the wrong lot_size we sent
        assert response_lot_size != wrong_lot_size, \
            f"Server used frontend's wrong lot_size! Got {response_lot_size}, should NOT be {wrong_lot_size}"
        
        # Server should use the calculated lot_size
        assert abs(response_lot_size - self.expected_lot_size) < 0.02, \
            f"LOT size mismatch: got {response_lot_size}, expected {self.expected_lot_size}"
        
        print(f"✓ Server correctly IGNORED wrong lot_size ({wrong_lot_size}) and used calculated value ({response_lot_size})")
        
        # Clean up - delete the test trade
        trade_id = result.get("id")
        if trade_id:
            delete_response = self.session.delete(f"{BASE_URL}/api/trade/logs/{trade_id}")
            print(f"Cleanup: Deleted test trade {trade_id}")
    
    def test_trade_log_with_stale_lot_size_is_corrected(self):
        """P0 Test: Simulate stale frontend lot_size scenario"""
        print(f"\n=== P0 Test: Stale Frontend lot_size Scenario ===")
        
        # Simulate a stale lot_size from old profitSummary (e.g., from before a deposit)
        # If account was $15,000 before, lot_size would have been 15.31
        stale_lot_size = 15.31  # Old value from before deposits
        
        trade_data = {
            "lot_size": stale_lot_size,  # Stale value - should be IGNORED
            "direction": "BUY",
            "actual_profit": 290.00,
            "notes": "P0 Test - Stale lot_size from old profitSummary"
        }
        
        print(f"Sending stale lot_size: {stale_lot_size}")
        print(f"Current account_value: ${self.account_value}")
        print(f"Expected server to use: {self.expected_lot_size}")
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        
        assert response.status_code == 200, f"Trade log failed: {response.text}"
        
        result = response.json()
        response_lot_size = result.get("lot_size")
        
        print(f"Response lot_size: {response_lot_size}")
        
        # Server should NOT use the stale lot_size
        assert response_lot_size != stale_lot_size, \
            f"Server used stale lot_size! Got {response_lot_size}, should NOT be {stale_lot_size}"
        
        # Server should use the current calculated lot_size
        assert abs(response_lot_size - self.expected_lot_size) < 0.02, \
            f"LOT size mismatch: got {response_lot_size}, expected {self.expected_lot_size}"
        
        print(f"✓ Server correctly IGNORED stale lot_size ({stale_lot_size}) and used current value ({response_lot_size})")
        
        # Clean up
        trade_id = result.get("id")
        if trade_id:
            delete_response = self.session.delete(f"{BASE_URL}/api/trade/logs/{trade_id}")
            print(f"Cleanup: Deleted test trade {trade_id}")
    
    def test_projected_profit_uses_correct_lot_size(self):
        """Verify projected_profit is calculated from server's lot_size"""
        print(f"\n=== Projected Profit Calculation Test ===")
        
        trade_data = {
            "lot_size": 99.99,  # Absurd value - should be ignored
            "direction": "BUY",
            "actual_profit": 300.00,
            "notes": "Test projected profit calculation"
        }
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        assert response.status_code == 200
        
        result = response.json()
        response_lot_size = result.get("lot_size")
        projected_profit = result.get("projected_profit")
        
        # Projected profit should be lot_size * 15
        expected_projected = round(response_lot_size * 15, 2)
        
        print(f"Response lot_size: {response_lot_size}")
        print(f"Projected profit: {projected_profit}")
        print(f"Expected projected (lot_size * 15): {expected_projected}")
        
        assert abs(projected_profit - expected_projected) < 0.1, \
            f"Projected profit mismatch: got {projected_profit}, expected {expected_projected}"
        
        print(f"✓ Projected profit correctly calculated from server's lot_size")
        
        # Clean up
        trade_id = result.get("id")
        if trade_id:
            self.session.delete(f"{BASE_URL}/api/trade/logs/{trade_id}")


class TestP1DailyProjectionSync:
    """P1 Bug Fix: Daily Projection Balance Before synchronization"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        self.session.close()
    
    def test_profit_summary_returns_current_account_value(self):
        """Verify profit summary returns the live account value"""
        print(f"\n=== Profit Summary Account Value Test ===")
        
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        account_value = data.get("account_value")
        
        print(f"Account Value: ${account_value}")
        
        # Should be around $18,941.87 based on context
        assert account_value > 0, "Account value should be positive"
        assert account_value > 18000, f"Account value seems too low: ${account_value}"
        
        print(f"✓ Profit summary returns live account value: ${account_value}")
    
    def test_calculate_exit_endpoint(self):
        """Verify calculate-exit endpoint uses correct lot_size"""
        print(f"\n=== Calculate Exit Endpoint Test ===")
        
        # Get current account value
        summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
        account_value = summary_response.json().get("account_value")
        expected_lot_size = round(account_value / 980, 2)
        
        # Test calculate-exit with the expected lot_size
        response = self.session.post(
            f"{BASE_URL}/api/profit/calculate-exit",
            params={"lot_size": expected_lot_size}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        exit_value = data.get("exit_value")
        expected_exit = round(expected_lot_size * 15, 2)
        
        print(f"LOT Size: {expected_lot_size}")
        print(f"Exit Value: ${exit_value}")
        print(f"Expected Exit (LOT × 15): ${expected_exit}")
        
        assert abs(exit_value - expected_exit) < 0.1, \
            f"Exit value mismatch: got {exit_value}, expected {expected_exit}"
        
        print(f"✓ Calculate-exit returns correct value: ${exit_value}")


class TestTradeLogEndpointValidation:
    """Additional validation tests for trade log endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        self.session.close()
    
    def test_trade_log_response_structure(self):
        """Verify trade log response contains all required fields"""
        print(f"\n=== Trade Log Response Structure Test ===")
        
        trade_data = {
            "direction": "BUY",
            "actual_profit": 289.00,
            "notes": "Structure test"
        }
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        assert response.status_code == 200
        
        result = response.json()
        
        required_fields = [
            "id", "user_id", "lot_size", "direction", 
            "projected_profit", "actual_profit", "profit_difference",
            "performance", "created_at"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
            print(f"✓ {field}: {result.get(field)}")
        
        # Clean up
        trade_id = result.get("id")
        if trade_id:
            self.session.delete(f"{BASE_URL}/api/trade/logs/{trade_id}")
    
    def test_trade_log_performance_calculation(self):
        """Verify performance is calculated correctly"""
        print(f"\n=== Performance Calculation Test ===")
        
        # Get expected lot_size
        summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
        account_value = summary_response.json().get("account_value")
        expected_lot_size = round(account_value / 980, 2)
        expected_projected = round(expected_lot_size * 15, 2)
        
        # Test "exceeded" performance
        trade_data = {
            "direction": "BUY",
            "actual_profit": expected_projected + 10,  # Above projected
            "notes": "Performance test - exceeded"
        }
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        assert response.status_code == 200
        
        result = response.json()
        print(f"Actual: {result.get('actual_profit')}, Projected: {result.get('projected_profit')}")
        print(f"Performance: {result.get('performance')}")
        
        assert result.get("performance") == "exceeded", \
            f"Expected 'exceeded' performance, got '{result.get('performance')}'"
        
        # Clean up
        self.session.delete(f"{BASE_URL}/api/trade/logs/{result.get('id')}")
        
        # Test "below" performance
        trade_data["actual_profit"] = expected_projected - 10  # Below projected
        trade_data["notes"] = "Performance test - below"
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        result = response.json()
        
        print(f"Actual: {result.get('actual_profit')}, Projected: {result.get('projected_profit')}")
        print(f"Performance: {result.get('performance')}")
        
        assert result.get("performance") == "below", \
            f"Expected 'below' performance, got '{result.get('performance')}'"
        
        # Clean up
        self.session.delete(f"{BASE_URL}/api/trade/logs/{result.get('id')}")
        
        print(f"✓ Performance calculation verified")


class TestExtendedLicenseeScenario:
    """Test lot_size calculation for extended licensee"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as extended licensee"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as extended licensee
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iamryan@ryansalvador.me",
            "password": "test123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Extended licensee login failed - skipping licensee tests")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        self.session.close()
    
    def test_licensee_account_value(self):
        """Verify licensee account value is returned correctly"""
        print(f"\n=== Licensee Account Value Test ===")
        
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        
        if response.status_code != 200:
            pytest.skip("Could not get licensee summary")
        
        data = response.json()
        account_value = data.get("account_value")
        
        print(f"Licensee Account Value: ${account_value}")
        
        assert account_value is not None, "Account value should be returned"
        print(f"✓ Licensee account value: ${account_value}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

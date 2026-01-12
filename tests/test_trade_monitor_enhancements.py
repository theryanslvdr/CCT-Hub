"""
Test Trade Monitor Page Enhancements (9 Features)
Tests for the Trade Monitor page enhancements including:
1. LOT Size card (from Profit Tracker)
2. Projected Exit Value card
3. Exit Value Calculator
4. Philippine Time prioritization
5. User local time and profit multiplier in signal banner
6. Removed 'Projected Total' from Today's Summary
7. 'Enter the Trade Now!' button text
8. Celebration popup after entering actual profit
9. Today's Summary with only Actual Total and P/L Difference
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://crossfin-hub.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "admin@crosscurrent.com"
TEST_PASSWORD = "admin123"


class TestTradeMonitorAPIs:
    """Test Trade Monitor related API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        self.session.close()
    
    def test_active_signal_endpoint(self):
        """Test /api/trade/active-signal returns signal with profit_points"""
        response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        
        data = response.json()
        if data.get("signal"):
            signal = data["signal"]
            # Verify signal has required fields for Trade Monitor
            assert "product" in signal
            assert "trade_time" in signal
            assert "direction" in signal
            assert "profit_points" in signal, "Signal should have profit_points (multiplier)"
            assert "trade_timezone" in signal, "Signal should have trade_timezone"
            
            # Verify profit_points is a number (multiplier)
            assert isinstance(signal["profit_points"], (int, float))
            print(f"✓ Active signal: {signal['product']} {signal['direction']} at {signal['trade_time']} (×{signal['profit_points']})")
        else:
            print("○ No active signal currently")
    
    def test_profit_summary_for_lot_size(self):
        """Test /api/profit/summary returns account_value for LOT Size calculation"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields for LOT Size card
        assert "account_value" in data, "Summary should have account_value for LOT calculation"
        assert "total_deposits" in data
        assert "total_actual_profit" in data
        
        # LOT Size = account_value / 980
        account_value = data["account_value"]
        lot_size = account_value / 980
        print(f"✓ Account Value: ${account_value:.2f}, LOT Size: {lot_size:.2f}")
    
    def test_daily_summary_endpoint(self):
        """Test /api/trade/daily-summary returns correct fields"""
        response = self.session.get(f"{BASE_URL}/api/trade/daily-summary")
        assert response.status_code == 200
        
        data = response.json()
        # Verify required fields for Today's Summary card
        assert "total_actual" in data, "Should have total_actual for Actual Total"
        assert "difference" in data, "Should have difference for P/L Difference"
        assert "trades_count" in data
        
        print(f"✓ Daily Summary: Actual Total=${data['total_actual']:.2f}, P/L Diff=${data['difference']:.2f}")
    
    def test_trade_log_endpoint(self):
        """Test /api/trade/log creates trade with performance calculation"""
        # Create a test trade
        trade_data = {
            "lot_size": 10.0,
            "direction": "BUY",
            "actual_profit": 160.0,  # Above projected (10 × 15 = 150)
            "notes": "TEST_trade_monitor_enhancement"
        }
        
        response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        assert response.status_code == 200
        
        data = response.json()
        # Verify trade response has required fields for celebration popup
        assert "id" in data
        assert "projected_profit" in data
        assert "actual_profit" in data
        assert "profit_difference" in data
        assert "performance" in data
        
        # Verify calculations
        expected_projected = 10.0 * 15  # LOT × 15
        assert data["projected_profit"] == expected_projected, f"Expected projected {expected_projected}, got {data['projected_profit']}"
        assert data["profit_difference"] == 160.0 - expected_projected
        assert data["performance"] == "exceeded", f"Expected 'exceeded' performance, got {data['performance']}"
        
        print(f"✓ Trade logged: Projected=${data['projected_profit']}, Actual=${data['actual_profit']}, Performance={data['performance']}")
        
        # Store trade ID for forward test
        self.test_trade_id = data["id"]
        return data["id"]
    
    def test_forward_to_profit_endpoint(self):
        """Test /api/trade/forward-to-profit forwards trade profit"""
        # First create a trade
        trade_data = {
            "lot_size": 5.0,
            "direction": "BUY",
            "actual_profit": 80.0,
            "notes": "TEST_forward_trade"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        assert create_response.status_code == 200
        trade_id = create_response.json()["id"]
        
        # Forward to profit tracker
        response = self.session.post(f"{BASE_URL}/api/trade/forward-to-profit", params={"trade_id": trade_id})
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "deposit_id" in data
        assert "amount" in data
        assert data["amount"] == 80.0
        
        print(f"✓ Trade forwarded to Profit Tracker: ${data['amount']}")
        
        # Verify duplicate forward is rejected
        duplicate_response = self.session.post(f"{BASE_URL}/api/trade/forward-to-profit", params={"trade_id": trade_id})
        assert duplicate_response.status_code == 400, "Should reject duplicate forward"
        print("✓ Duplicate forward correctly rejected")
    
    def test_calculate_exit_endpoint(self):
        """Test /api/profit/calculate-exit calculates LOT × 15"""
        lot_size = 10.0
        response = self.session.post(f"{BASE_URL}/api/profit/calculate-exit", params={"lot_size": lot_size})
        assert response.status_code == 200
        
        data = response.json()
        assert "exit_value" in data
        assert "lot_size" in data
        assert "formula" in data
        
        expected_exit = lot_size * 15
        assert data["exit_value"] == expected_exit, f"Expected {expected_exit}, got {data['exit_value']}"
        assert data["formula"] == "LOT Size × 15"
        
        print(f"✓ Exit calculation: LOT {lot_size} × 15 = ${data['exit_value']}")
    
    def test_trade_performance_levels(self):
        """Test trade performance categorization (exceeded, perfect, below)"""
        test_cases = [
            {"lot_size": 10.0, "actual": 160.0, "expected_perf": "exceeded"},  # Above projected
            {"lot_size": 10.0, "actual": 150.0, "expected_perf": "perfect"},   # Exactly projected
            {"lot_size": 10.0, "actual": 140.0, "expected_perf": "below"},     # Below projected
        ]
        
        for case in test_cases:
            trade_data = {
                "lot_size": case["lot_size"],
                "direction": "BUY",
                "actual_profit": case["actual"],
                "notes": f"TEST_performance_{case['expected_perf']}"
            }
            
            response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["performance"] == case["expected_perf"], \
                f"Expected {case['expected_perf']} for actual={case['actual']}, got {data['performance']}"
            
            print(f"✓ Performance '{case['expected_perf']}': Actual ${case['actual']} vs Projected ${data['projected_profit']}")


class TestSignalManagement:
    """Test admin signal management for Trade Monitor"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with admin authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        self.session.close()
    
    def test_create_signal_with_profit_points(self):
        """Test creating signal with custom profit_points (multiplier)"""
        signal_data = {
            "product": "MOIL10",
            "trade_time": "10:00",
            "trade_timezone": "Asia/Manila",
            "direction": "BUY",
            "profit_points": 20,  # Custom multiplier
            "notes": "TEST_signal_with_multiplier"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/signals", json=signal_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["profit_points"] == 20
        assert data["trade_timezone"] == "Asia/Manila"
        assert data["is_active"] == True
        
        print(f"✓ Signal created with multiplier ×{data['profit_points']}")
        
        # Cleanup - delete the test signal
        self.session.delete(f"{BASE_URL}/api/admin/signals/{data['id']}")
    
    def test_simulate_signal(self):
        """Test simulated signal creation (super admin only)"""
        signal_data = {
            "product": "MOIL10",
            "trade_time": "14:00",
            "trade_timezone": "Asia/Manila",
            "direction": "SELL",
            "profit_points": 15,
            "notes": "Test simulation"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/signals/simulate", json=signal_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_simulated"] == True
        assert "[SIMULATED]" in data["notes"]
        
        print(f"✓ Simulated signal created: {data['product']} {data['direction']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/admin/signals/{data['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

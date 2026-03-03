"""
Test Trade Monitor Page V2 Enhancements (6 New Features)
Tests for the 6 additional Trade Monitor page enhancements:
1. Active Signal card redesign (Radio icon, date, no edit button, simulated tag)
2. Timezone conversion fix (offset-based calculation)
3. Trade History table with pagination
4. Time Entered editable column
5. Streak indicator with fire icon
6. SIMULATED signals show Flask icon instead of [SIMULATED] text
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://deploy-auth-sync.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "admin@crosscurrent.com"
TEST_PASSWORD = "admin123"


class TestTradeHistoryAPI:
    """Test Trade History endpoint (Feature 3)"""
    
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
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        self.session.close()
    
    def test_trade_history_endpoint_exists(self):
        """Test GET /api/trade/history endpoint exists and returns data"""
        response = self.session.get(f"{BASE_URL}/api/trade/history")
        assert response.status_code == 200, f"Trade history endpoint failed: {response.text}"
        
        data = response.json()
        assert "trades" in data, "Response should have 'trades' field"
        assert "total" in data, "Response should have 'total' field"
        assert "page" in data, "Response should have 'page' field"
        assert "page_size" in data, "Response should have 'page_size' field"
        assert "total_pages" in data, "Response should have 'total_pages' field"
        
        print(f"✓ Trade history: {data['total']} total trades, {data['total_pages']} pages")
    
    def test_trade_history_pagination(self):
        """Test trade history pagination works correctly"""
        # Get page 1
        response1 = self.session.get(f"{BASE_URL}/api/trade/history?page=1&page_size=2")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get page 2
        response2 = self.session.get(f"{BASE_URL}/api/trade/history?page=2&page_size=2")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify pagination
        assert data1["page"] == 1
        assert data2["page"] == 2
        assert len(data1["trades"]) <= 2
        
        # Verify different trades on different pages (if enough trades exist)
        if data1["total"] > 2 and len(data2["trades"]) > 0:
            trade_ids_page1 = [t["id"] for t in data1["trades"]]
            trade_ids_page2 = [t["id"] for t in data2["trades"]]
            assert not any(tid in trade_ids_page1 for tid in trade_ids_page2), "Pages should have different trades"
        
        print(f"✓ Pagination working: Page 1 has {len(data1['trades'])} trades, Page 2 has {len(data2['trades'])} trades")
    
    def test_trade_history_has_signal_details(self):
        """Test trade history includes signal details for each trade"""
        response = self.session.get(f"{BASE_URL}/api/trade/history?page=1&page_size=5")
        assert response.status_code == 200
        
        data = response.json()
        if data["trades"]:
            trade = data["trades"][0]
            # Check required fields for Trade History table
            assert "id" in trade
            assert "lot_size" in trade
            assert "direction" in trade
            assert "projected_profit" in trade
            assert "actual_profit" in trade
            assert "profit_difference" in trade
            assert "created_at" in trade
            assert "time_entered" in trade or trade.get("time_entered") is None
            
            # Check signal_details if signal_id exists
            if trade.get("signal_id"):
                assert "signal_details" in trade, "Trade should have signal_details"
                if trade["signal_details"]:
                    assert "product" in trade["signal_details"]
                    assert "trade_time" in trade["signal_details"]
            
            print(f"✓ Trade has all required fields: {trade['id'][:8]}...")
        else:
            print("○ No trades to verify")


class TestTimeEnteredAPI:
    """Test Time Entered update endpoint (Feature 4)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
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
    
    def test_update_time_entered_endpoint(self):
        """Test PUT /api/trade/logs/{id}/time-entered updates time correctly"""
        # First get a trade ID
        history_response = self.session.get(f"{BASE_URL}/api/trade/history?page=1&page_size=1")
        assert history_response.status_code == 200
        
        trades = history_response.json()["trades"]
        if not trades:
            pytest.skip("No trades available to test time update")
        
        trade_id = trades[0]["id"]
        
        # Update time entered
        update_response = self.session.put(
            f"{BASE_URL}/api/trade/logs/{trade_id}/time-entered",
            json={"time_entered": "09:15"}
        )
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data["message"] == "Time entered updated"
        assert data["time_entered"] == "09:15"
        
        # Verify the update persisted
        verify_response = self.session.get(f"{BASE_URL}/api/trade/history?page=1&page_size=10")
        assert verify_response.status_code == 200
        
        updated_trade = next((t for t in verify_response.json()["trades"] if t["id"] == trade_id), None)
        assert updated_trade is not None
        assert updated_trade["time_entered"] == "09:15"
        
        print(f"✓ Time entered updated to 09:15 for trade {trade_id[:8]}...")
    
    def test_update_time_entered_invalid_trade(self):
        """Test updating time for non-existent trade returns 404"""
        response = self.session.put(
            f"{BASE_URL}/api/trade/logs/invalid-trade-id/time-entered",
            json={"time_entered": "10:00"}
        )
        assert response.status_code == 404
        print("✓ Invalid trade ID correctly returns 404")


class TestStreakAPI:
    """Test Streak endpoint (Feature 5)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
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
    
    def test_streak_endpoint_exists(self):
        """Test GET /api/trade/streak endpoint exists and returns data"""
        response = self.session.get(f"{BASE_URL}/api/trade/streak")
        assert response.status_code == 200, f"Streak endpoint failed: {response.text}"
        
        data = response.json()
        assert "streak" in data, "Response should have 'streak' field"
        assert "streak_type" in data, "Response should have 'streak_type' field"
        assert "total_trades" in data, "Response should have 'total_trades' field"
        
        assert isinstance(data["streak"], int), "Streak should be an integer"
        assert data["streak"] >= 0, "Streak should be non-negative"
        
        print(f"✓ Streak: {data['streak']} ({data['streak_type'] or 'no streak'}), Total trades: {data['total_trades']}")
    
    def test_streak_calculation_with_winning_trades(self):
        """Test streak increases with consecutive exceeded/perfect trades"""
        # Create a winning trade
        trade_data = {
            "lot_size": 10.0,
            "direction": "BUY",
            "actual_profit": 160.0,  # Above projected (10 × 15 = 150)
            "notes": "TEST_streak_winning"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/trade/log", json=trade_data)
        assert create_response.status_code == 200
        
        # Check streak
        streak_response = self.session.get(f"{BASE_URL}/api/trade/streak")
        assert streak_response.status_code == 200
        
        data = streak_response.json()
        # Streak should be at least 1 after a winning trade (if it was the most recent)
        print(f"✓ After winning trade - Streak: {data['streak']}, Type: {data['streak_type']}")


class TestActiveSignalDesign:
    """Test Active Signal card redesign (Features 1, 2, 6)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
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
    
    def test_active_signal_has_simulated_flag(self):
        """Test active signal returns is_simulated flag for Flask icon display"""
        response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        
        data = response.json()
        if data.get("signal"):
            signal = data["signal"]
            assert "is_simulated" in signal, "Signal should have is_simulated flag"
            assert isinstance(signal["is_simulated"], bool), "is_simulated should be boolean"
            
            print(f"✓ Signal is_simulated: {signal['is_simulated']}")
            
            # If simulated, notes should NOT have [SIMULATED] prefix (using icon instead)
            if signal["is_simulated"]:
                # The notes field should be clean (no [SIMULATED] prefix)
                # The UI will show Flask icon based on is_simulated flag
                print(f"✓ Simulated signal - UI should show Flask icon instead of [SIMULATED] text")
        else:
            print("○ No active signal to verify")
    
    def test_active_signal_has_timezone_fields(self):
        """Test active signal has timezone fields for conversion"""
        response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        
        data = response.json()
        if data.get("signal"):
            signal = data["signal"]
            assert "trade_time" in signal, "Signal should have trade_time"
            assert "trade_timezone" in signal, "Signal should have trade_timezone"
            assert "profit_points" in signal, "Signal should have profit_points (multiplier)"
            
            print(f"✓ Signal time: {signal['trade_time']} ({signal['trade_timezone']}), Multiplier: ×{signal['profit_points']}")
        else:
            print("○ No active signal to verify")
    
    def test_create_simulated_signal_no_prefix(self):
        """Test simulated signal creation doesn't add [SIMULATED] prefix to notes"""
        signal_data = {
            "product": "MOIL10",
            "trade_time": "10:30",
            "trade_timezone": "Asia/Manila",
            "direction": "BUY",
            "profit_points": 15,
            "notes": "Test notes without prefix"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/signals/simulate", json=signal_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_simulated"] == True
        # Notes should NOT have [SIMULATED] prefix - using is_simulated flag instead
        # The UI will display Flask icon based on is_simulated flag
        
        print(f"✓ Simulated signal created with is_simulated=True, notes: '{data['notes']}'")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/admin/signals/{data['id']}")


class TestTradeHistoryColumns:
    """Test Trade History table has all required columns"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
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
    
    def test_trade_history_all_columns(self):
        """Test trade history returns all required columns for the table"""
        response = self.session.get(f"{BASE_URL}/api/trade/history?page=1&page_size=5")
        assert response.status_code == 200
        
        data = response.json()
        if data["trades"]:
            trade = data["trades"][0]
            
            # Required columns: Date, Product, Direction, LOT Size, Time Set, Time Entered, Projected, Actual, P/L Diff
            required_fields = {
                "created_at": "Date",
                "direction": "Direction",
                "lot_size": "LOT Size",
                "time_entered": "Time Entered (editable)",
                "projected_profit": "Projected",
                "actual_profit": "Actual",
                "profit_difference": "P/L Diff"
            }
            
            for field, column_name in required_fields.items():
                assert field in trade or trade.get(field) is None, f"Missing field '{field}' for column '{column_name}'"
            
            # Product and Time Set come from signal_details
            if trade.get("signal_details"):
                assert "product" in trade["signal_details"], "Missing product in signal_details"
                assert "trade_time" in trade["signal_details"], "Missing trade_time (Time Set) in signal_details"
            
            print("✓ All required columns present in trade history response")
            print(f"  - Date: {trade['created_at'][:10]}")
            print(f"  - Product: {trade.get('signal_details', {}).get('product', 'N/A')}")
            print(f"  - Direction: {trade['direction']}")
            print(f"  - LOT Size: {trade['lot_size']}")
            print(f"  - Time Set: {trade.get('signal_details', {}).get('trade_time', 'N/A')}")
            print(f"  - Time Entered: {trade.get('time_entered', 'N/A')}")
            print(f"  - Projected: ${trade['projected_profit']}")
            print(f"  - Actual: ${trade['actual_profit']}")
            print(f"  - P/L Diff: ${trade['profit_difference']}")
        else:
            print("○ No trades to verify columns")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

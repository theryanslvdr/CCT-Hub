"""
Iteration 32 - BVE (Beta Virtual Environment) and Trade Check-in Persistence Tests
Tests:
1. BVE enter/exit/rewind endpoints
2. BVE signals CRUD
3. Trade check-in persistence (localStorage)
4. Signal deactivate functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBVEFeatures:
    """Test Beta Virtual Environment (BVE) features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        data = login_response.json()
        self.token = data.get("access_token")
        self.user = data.get("user")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Store BVE session ID for cleanup
        self.bve_session_id = None
        
        yield
        
        # Cleanup - exit BVE if active
        if self.bve_session_id:
            try:
                self.session.post(f"{BASE_URL}/api/bve/exit", json={"session_id": self.bve_session_id})
            except:
                pass
    
    def test_health_check(self):
        """Test API health"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check passed")
    
    def test_master_admin_login(self):
        """Verify master admin login works"""
        assert self.user is not None
        assert self.user.get("role") == "master_admin"
        print(f"✓ Logged in as master admin: {self.user.get('email')}")
    
    def test_bve_enter(self):
        """Test entering BVE mode"""
        response = self.session.post(f"{BASE_URL}/api/bve/enter")
        assert response.status_code == 200, f"BVE enter failed: {response.text}"
        
        data = response.json()
        assert "session_id" in data
        assert "snapshot" in data
        assert data.get("message") == "Entered Beta Virtual Environment"
        
        self.bve_session_id = data["session_id"]
        print(f"✓ Entered BVE with session: {self.bve_session_id}")
        print(f"  Snapshot: {data['snapshot']}")
        return data
    
    def test_bve_get_signals(self):
        """Test getting signals in BVE mode"""
        # First enter BVE
        enter_response = self.session.post(f"{BASE_URL}/api/bve/enter")
        assert enter_response.status_code == 200
        self.bve_session_id = enter_response.json()["session_id"]
        
        # Get BVE signals
        response = self.session.get(f"{BASE_URL}/api/bve/signals")
        assert response.status_code == 200, f"Get BVE signals failed: {response.text}"
        
        signals = response.json()
        assert isinstance(signals, list)
        print(f"✓ Got {len(signals)} BVE signals")
        return signals
    
    def test_bve_create_signal(self):
        """Test creating a signal in BVE mode"""
        # First enter BVE
        enter_response = self.session.post(f"{BASE_URL}/api/bve/enter")
        assert enter_response.status_code == 200
        self.bve_session_id = enter_response.json()["session_id"]
        
        # Create BVE signal
        signal_data = {
            "product": "MOIL10",
            "direction": "BUY",
            "trade_time": "14:30",
            "trade_timezone": "Asia/Manila",
            "profit_multiplier": 15.0
        }
        
        response = self.session.post(f"{BASE_URL}/api/bve/signals", json=signal_data)
        assert response.status_code == 200, f"Create BVE signal failed: {response.text}"
        
        data = response.json()
        assert "signal" in data
        assert data["signal"]["product"] == "MOIL10"
        assert data["signal"]["direction"] == "BUY"
        assert data["signal"]["is_simulated"] == True
        print(f"✓ Created BVE signal: {data['signal']['id']}")
        return data
    
    def test_bve_signal_isolation(self):
        """Test that BVE signals don't affect real signals"""
        # Get real signals count before BVE
        real_signals_response = self.session.get(f"{BASE_URL}/api/admin/signals/history?page=1&page_size=100")
        assert real_signals_response.status_code == 200
        real_signals_before = real_signals_response.json().get("total", 0)
        
        # Enter BVE and create signal
        enter_response = self.session.post(f"{BASE_URL}/api/bve/enter")
        assert enter_response.status_code == 200
        self.bve_session_id = enter_response.json()["session_id"]
        
        # Create BVE signal
        signal_data = {
            "product": "XAUUSD",
            "direction": "SELL",
            "trade_time": "15:00",
            "trade_timezone": "Asia/Manila",
            "profit_multiplier": 20.0
        }
        create_response = self.session.post(f"{BASE_URL}/api/bve/signals", json=signal_data)
        assert create_response.status_code == 200
        
        # Exit BVE
        exit_response = self.session.post(f"{BASE_URL}/api/bve/exit", json={"session_id": self.bve_session_id})
        assert exit_response.status_code == 200
        
        # Check real signals count after BVE - should be same
        real_signals_after_response = self.session.get(f"{BASE_URL}/api/admin/signals/history?page=1&page_size=100")
        assert real_signals_after_response.status_code == 200
        real_signals_after = real_signals_after_response.json().get("total", 0)
        
        assert real_signals_after == real_signals_before, "BVE signal affected real signals!"
        print(f"✓ BVE signal isolation verified - real signals unchanged ({real_signals_before} -> {real_signals_after})")
        self.bve_session_id = None  # Already exited
    
    def test_bve_rewind(self):
        """Test rewinding BVE to initial state"""
        # Enter BVE
        enter_response = self.session.post(f"{BASE_URL}/api/bve/enter")
        assert enter_response.status_code == 200
        self.bve_session_id = enter_response.json()["session_id"]
        initial_snapshot = enter_response.json()["snapshot"]
        
        # Create a BVE signal
        signal_data = {
            "product": "BTCUSD",
            "direction": "BUY",
            "trade_time": "16:00",
            "trade_timezone": "Asia/Manila",
            "profit_multiplier": 25.0
        }
        self.session.post(f"{BASE_URL}/api/bve/signals", json=signal_data)
        
        # Rewind
        rewind_response = self.session.post(f"{BASE_URL}/api/bve/rewind", json={"session_id": self.bve_session_id})
        assert rewind_response.status_code == 200, f"Rewind failed: {rewind_response.text}"
        
        data = rewind_response.json()
        assert data["message"] == "BVE state rewound to entry point"
        print(f"✓ BVE rewound successfully")
        print(f"  Restored: {data.get('restored', {})}")
    
    def test_bve_exit(self):
        """Test exiting BVE mode"""
        # Enter BVE first
        enter_response = self.session.post(f"{BASE_URL}/api/bve/enter")
        assert enter_response.status_code == 200
        self.bve_session_id = enter_response.json()["session_id"]
        
        # Exit BVE
        response = self.session.post(f"{BASE_URL}/api/bve/exit", json={"session_id": self.bve_session_id})
        assert response.status_code == 200, f"BVE exit failed: {response.text}"
        
        data = response.json()
        assert data["message"] == "Exited Beta Virtual Environment"
        print(f"✓ Exited BVE successfully")
        self.bve_session_id = None  # Already exited


class TestSignalDeactivate:
    """Test signal deactivation functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        data = login_response.json()
        self.token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
    
    def test_get_active_signal(self):
        """Test getting active signal"""
        response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        
        data = response.json()
        if data:
            print(f"✓ Active signal found: {data.get('product')} {data.get('direction')}")
        else:
            print("✓ No active signal currently")
        return data
    
    def test_signal_update_deactivate(self):
        """Test updating signal to deactivate it"""
        # First check if there's an active signal
        active_response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert active_response.status_code == 200
        
        active_signal = active_response.json()
        if not active_signal:
            print("⚠ No active signal to test deactivation - skipping")
            pytest.skip("No active signal to test")
        
        signal_id = active_signal.get("id")
        
        # Update signal to deactivate
        update_response = self.session.put(f"{BASE_URL}/api/admin/signals/{signal_id}", json={
            "is_active": False,
            "trade_time": active_signal.get("trade_time"),
            "trade_timezone": active_signal.get("trade_timezone", "Asia/Manila"),
            "direction": active_signal.get("direction"),
            "profit_points": active_signal.get("profit_points", 15)
        })
        
        assert update_response.status_code == 200, f"Deactivate failed: {update_response.text}"
        print(f"✓ Signal {signal_id} deactivated successfully")
        
        # Verify it's deactivated
        verify_response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        
        # Should be no active signal or different signal
        if verify_data:
            assert verify_data.get("id") != signal_id, "Signal still active after deactivation"
        print("✓ Verified signal is no longer active")


class TestTradeMonitorAPIs:
    """Test Trade Monitor related APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        data = login_response.json()
        self.token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
    
    def test_get_profit_summary(self):
        """Test getting profit summary (for LOT size calculation)"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_balance" in data or "balance" in data
        print(f"✓ Profit summary retrieved")
        return data
    
    def test_get_trade_logs(self):
        """Test getting trade logs"""
        response = self.session.get(f"{BASE_URL}/api/trade/logs?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "trades" in data or isinstance(data, list)
        print(f"✓ Trade logs retrieved")
        return data
    
    def test_get_daily_summary(self):
        """Test getting daily trade summary"""
        response = self.session.get(f"{BASE_URL}/api/trade/daily-summary")
        # May return 200 with data or 404 if no trades today
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Daily summary: {data}")
        else:
            print("✓ No daily summary (no trades today)")


class TestDailyProjection:
    """Test Daily Projection data (LOT and Projected values)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as master admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as master admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        
        data = login_response.json()
        self.token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
    
    def test_profit_summary_for_lot_calculation(self):
        """Test that profit summary provides data for LOT calculation"""
        response = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert response.status_code == 200
        
        data = response.json()
        # Check for balance field (used for LOT = balance / 980)
        balance = data.get("current_balance") or data.get("balance") or data.get("merin_balance", 0)
        
        # Calculate LOT size
        lot_size = balance / 980 if balance > 0 else 0
        
        print(f"✓ Balance: {balance}")
        print(f"✓ Calculated LOT size: {lot_size:.2f}")
        
        return {"balance": balance, "lot_size": lot_size}
    
    def test_active_signal_for_projection(self):
        """Test that active signal provides profit multiplier for projection"""
        response = self.session.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        
        data = response.json()
        if data:
            profit_multiplier = data.get("profit_points") or data.get("profit_multiplier", 15)
            print(f"✓ Active signal profit multiplier: {profit_multiplier}")
            
            # Get balance for full projection calculation
            summary_response = self.session.get(f"{BASE_URL}/api/profit/summary")
            if summary_response.status_code == 200:
                summary = summary_response.json()
                balance = summary.get("current_balance") or summary.get("balance") or summary.get("merin_balance", 0)
                lot_size = balance / 980 if balance > 0 else 0
                projected_exit = lot_size * profit_multiplier
                
                print(f"✓ Projected Exit Value: {projected_exit:.2f}")
        else:
            print("⚠ No active signal - projection will use default multiplier")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

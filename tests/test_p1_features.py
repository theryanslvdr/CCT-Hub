"""
P1 Features Backend Tests for CrossCurrent Finance Center
Tests for:
- Member Management: Search, filter, pagination, view details, edit, suspend/unsuspend, temp password
- Trading Signals: Create with profit_points, edit, simulate (super admin)
- Profit Tracker: Reset tracker, initial balance setup, deposits
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://finance-flow-staging.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@crosscurrent.com"
ADMIN_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests to get token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] in ["admin", "super_admin"]


class TestMemberManagement:
    """Member Management P1 Feature Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    # Test: Get members with pagination
    def test_get_members_pagination(self, auth_headers):
        """Test GET /admin/members with pagination"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"page": 1, "limit": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert data["page"] == 1
        print(f"Total members: {data['total']}, Pages: {data['pages']}")
    
    # Test: Search members by name
    def test_search_members_by_name(self, auth_headers):
        """Test GET /admin/members with search query"""
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"search": "admin"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        # Should find at least the admin user
        print(f"Found {len(data['members'])} members matching 'admin'")
    
    # Test: Filter members by role
    def test_filter_members_by_role(self, auth_headers):
        """Test GET /admin/members with role filter"""
        for role in ["user", "admin", "super_admin"]:
            response = requests.get(
                f"{BASE_URL}/api/admin/members",
                params={"role": role},
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            # All returned members should have the specified role
            for member in data["members"]:
                assert member["role"] == role, f"Expected role {role}, got {member['role']}"
            print(f"Found {len(data['members'])} members with role '{role}'")
    
    # Test: Filter members by status
    def test_filter_members_by_status(self, auth_headers):
        """Test GET /admin/members with status filter"""
        # Test active filter
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"status": "active"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for member in data["members"]:
            assert member.get("is_suspended") != True
        print(f"Found {len(data['members'])} active members")
        
        # Test suspended filter
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"status": "suspended"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    # Test: Get member details
    def test_get_member_details(self, auth_headers):
        """Test GET /admin/members/{user_id} returns detailed info"""
        # First get a member
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"limit": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        members = response.json()["members"]
        
        if len(members) > 0:
            member_id = members[0]["id"]
            
            # Get details
            response = requests.get(
                f"{BASE_URL}/api/admin/members/{member_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verify structure
            assert "user" in data
            assert "stats" in data
            assert "recent_trades" in data
            
            # Verify stats structure
            stats = data["stats"]
            assert "total_trades" in stats
            assert "total_profit" in stats
            assert "total_deposits" in stats
            assert "account_value" in stats
            
            print(f"Member details: {data['user']['full_name']}, Trades: {stats['total_trades']}")
    
    # Test: Edit member profile
    def test_edit_member_profile(self, auth_headers):
        """Test PUT /admin/members/{user_id} updates member"""
        # Get a non-admin member to edit
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"role": "user", "limit": 1},
            headers=auth_headers
        )
        
        if response.status_code == 200 and len(response.json()["members"]) > 0:
            member = response.json()["members"][0]
            member_id = member["id"]
            
            # Update member
            new_name = f"TEST_Updated_{uuid.uuid4().hex[:6]}"
            response = requests.put(
                f"{BASE_URL}/api/admin/members/{member_id}",
                json={
                    "full_name": new_name,
                    "timezone": "Asia/Manila",
                    "lot_size": 0.05
                },
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Verify update
            response = requests.get(
                f"{BASE_URL}/api/admin/members/{member_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            updated = response.json()["user"]
            assert updated["full_name"] == new_name
            assert updated["timezone"] == "Asia/Manila"
            assert updated["lot_size"] == 0.05
            print(f"Successfully updated member to: {new_name}")
        else:
            pytest.skip("No regular users available to test edit")
    
    # Test: Suspend and unsuspend member
    def test_suspend_unsuspend_member(self, auth_headers):
        """Test POST /admin/members/{user_id}/suspend and unsuspend"""
        # Get a non-admin member
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"role": "user", "limit": 1},
            headers=auth_headers
        )
        
        if response.status_code == 200 and len(response.json()["members"]) > 0:
            member = response.json()["members"][0]
            member_id = member["id"]
            
            # Suspend
            response = requests.post(
                f"{BASE_URL}/api/admin/members/{member_id}/suspend",
                headers=auth_headers
            )
            assert response.status_code == 200
            print(f"Suspended member {member_id}")
            
            # Verify suspended
            response = requests.get(
                f"{BASE_URL}/api/admin/members/{member_id}",
                headers=auth_headers
            )
            assert response.json()["user"]["is_suspended"] == True
            
            # Unsuspend
            response = requests.post(
                f"{BASE_URL}/api/admin/members/{member_id}/unsuspend",
                headers=auth_headers
            )
            assert response.status_code == 200
            print(f"Unsuspended member {member_id}")
            
            # Verify unsuspended
            response = requests.get(
                f"{BASE_URL}/api/admin/members/{member_id}",
                headers=auth_headers
            )
            assert response.json()["user"]["is_suspended"] == False
        else:
            pytest.skip("No regular users available to test suspend")
    
    # Test: Set temporary password
    def test_set_temp_password(self, auth_headers):
        """Test POST /admin/members/{user_id}/set-temp-password"""
        # Get a non-admin member
        response = requests.get(
            f"{BASE_URL}/api/admin/members",
            params={"role": "user", "limit": 1},
            headers=auth_headers
        )
        
        if response.status_code == 200 and len(response.json()["members"]) > 0:
            member = response.json()["members"][0]
            member_id = member["id"]
            
            # Set temp password
            response = requests.post(
                f"{BASE_URL}/api/admin/members/{member_id}/set-temp-password",
                json={"temp_password": "TempPass123!"},
                headers=auth_headers
            )
            assert response.status_code == 200
            assert "message" in response.json()
            print(f"Set temp password for member {member_id}")
        else:
            pytest.skip("No regular users available to test temp password")


class TestTradingSignals:
    """Trading Signals P1 Feature Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    # Test: Create signal with custom profit_points
    def test_create_signal_with_profit_points(self, auth_headers):
        """Test POST /admin/signals with custom profit_points multiplier"""
        response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            json={
                "product": "MOIL10",
                "trade_time": "14:30",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 20,  # Custom multiplier
                "notes": "TEST_Signal with custom profit points"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["product"] == "MOIL10"
        assert data["trade_time"] == "14:30"
        assert data["direction"] == "BUY"
        assert data["profit_points"] == 20
        assert data["is_active"] == True
        assert data["is_simulated"] == False
        
        print(f"Created signal with profit_points={data['profit_points']}")
        return data["id"]
    
    # Test: Get signals list
    def test_get_signals(self, auth_headers):
        """Test GET /admin/signals returns list with profit_points"""
        response = requests.get(
            f"{BASE_URL}/api/admin/signals",
            headers=auth_headers
        )
        assert response.status_code == 200
        signals = response.json()
        
        assert isinstance(signals, list)
        if len(signals) > 0:
            signal = signals[0]
            assert "profit_points" in signal
            assert "is_simulated" in signal
            print(f"Found {len(signals)} signals, first has profit_points={signal['profit_points']}")
    
    # Test: Edit signal
    def test_edit_signal(self, auth_headers):
        """Test PUT /admin/signals/{signal_id} updates signal"""
        # First create a signal
        create_response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            json={
                "product": "MOIL10",
                "trade_time": "10:00",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 15,
                "notes": "TEST_Signal to edit"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200
        signal_id = create_response.json()["id"]
        
        # Edit the signal
        response = requests.put(
            f"{BASE_URL}/api/admin/signals/{signal_id}",
            json={
                "trade_time": "11:30",
                "direction": "SELL",
                "profit_points": 25,
                "notes": "TEST_Updated signal"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        updated = response.json()
        
        assert updated["trade_time"] == "11:30"
        assert updated["direction"] == "SELL"
        assert updated["profit_points"] == 25
        print(f"Updated signal {signal_id}: direction=SELL, profit_points=25")
    
    # Test: Toggle signal active status
    def test_toggle_signal_active(self, auth_headers):
        """Test PUT /admin/signals/{signal_id} toggles is_active"""
        # Get signals
        response = requests.get(
            f"{BASE_URL}/api/admin/signals",
            headers=auth_headers
        )
        signals = response.json()
        
        if len(signals) > 0:
            signal = signals[0]
            signal_id = signal["id"]
            current_active = signal["is_active"]
            
            # Toggle
            response = requests.put(
                f"{BASE_URL}/api/admin/signals/{signal_id}",
                json={"is_active": not current_active},
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json()["is_active"] == (not current_active)
            print(f"Toggled signal {signal_id} active: {current_active} -> {not current_active}")
    
    # Test: Simulate signal (Super Admin only)
    def test_simulate_signal(self, auth_headers):
        """Test POST /admin/signals/simulate creates simulated signal"""
        response = requests.post(
            f"{BASE_URL}/api/admin/signals/simulate",
            json={
                "product": "MOIL10",
                "trade_time": "09:00",
                "trade_timezone": "Asia/Manila",
                "direction": "BUY",
                "profit_points": 15,
                "notes": "Test simulation"
            },
            headers=auth_headers
        )
        
        # Should succeed for super_admin
        if response.status_code == 200:
            data = response.json()
            assert data["is_simulated"] == True
            assert "[SIMULATED]" in data["notes"]
            assert data["is_active"] == True
            print(f"Created simulated signal: {data['id']}")
        elif response.status_code == 403:
            # Not super admin - expected for regular admin
            print("Simulate signal requires super_admin role")
        else:
            pytest.fail(f"Unexpected status: {response.status_code}")
    
    # Test: Delete signal
    def test_delete_signal(self, auth_headers):
        """Test DELETE /admin/signals/{signal_id}"""
        # Create a signal to delete
        create_response = requests.post(
            f"{BASE_URL}/api/admin/signals",
            json={
                "product": "MOIL10",
                "trade_time": "08:00",
                "trade_timezone": "Asia/Manila",
                "direction": "SELL",
                "profit_points": 15,
                "notes": "TEST_Signal to delete"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200
        signal_id = create_response.json()["id"]
        
        # Delete
        response = requests.delete(
            f"{BASE_URL}/api/admin/signals/{signal_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        print(f"Deleted signal {signal_id}")


class TestProfitTracker:
    """Profit Tracker P1 Feature Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    # Test: Create deposit (initial balance setup)
    def test_create_deposit_initial_balance(self, auth_headers):
        """Test POST /profit/deposits for initial balance setup"""
        response = requests.post(
            f"{BASE_URL}/api/profit/deposits",
            json={
                "amount": 100.0,
                "product": "MOIL10",
                "currency": "USDT",
                "notes": "TEST_Initial balance setup"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["amount"] == 100.0
        assert data["product"] == "MOIL10"
        assert data["currency"] == "USDT"
        assert "id" in data
        print(f"Created deposit: ${data['amount']} USDT")
    
    # Test: Get deposits
    def test_get_deposits(self, auth_headers):
        """Test GET /profit/deposits returns list"""
        response = requests.get(
            f"{BASE_URL}/api/profit/deposits",
            headers=auth_headers
        )
        assert response.status_code == 200
        deposits = response.json()
        
        assert isinstance(deposits, list)
        print(f"Found {len(deposits)} deposits")
    
    # Test: Get profit summary
    def test_get_profit_summary(self, auth_headers):
        """Test GET /profit/summary returns account summary"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_deposits" in data
        assert "total_projected_profit" in data
        assert "total_actual_profit" in data
        assert "account_value" in data
        assert "total_trades" in data
        
        print(f"Account value: ${data['account_value']}, Total deposits: ${data['total_deposits']}")
    
    # Test: Simulate withdrawal
    def test_simulate_withdrawal(self, auth_headers):
        """Test POST /profit/simulate-withdrawal calculates fees"""
        # First ensure there's balance
        requests.post(
            f"{BASE_URL}/api/profit/deposits",
            json={"amount": 200.0, "product": "MOIL10", "currency": "USDT", "notes": "TEST_For withdrawal test"},
            headers=auth_headers
        )
        
        response = requests.post(
            f"{BASE_URL}/api/profit/simulate-withdrawal",
            json={
                "amount": 50.0,
                "from_currency": "USDT",
                "to_currency": "USD"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "gross_amount" in data
        assert "merin_fee" in data
        assert "binance_fee" in data
        assert "net_amount" in data
        assert "current_balance" in data
        
        # Verify fee calculation: 3% Merin + $1 Binance
        assert data["merin_fee"] == 1.5  # 3% of 50
        assert data["binance_fee"] == 1.0
        assert data["net_amount"] == 47.5  # 50 - 1.5 - 1
        
        print(f"Withdrawal simulation: ${data['gross_amount']} -> ${data['net_amount']} (fees: ${data['merin_fee'] + data['binance_fee']})")
    
    # Test: Reset profit tracker
    def test_reset_profit_tracker(self, auth_headers):
        """Test DELETE /profit/reset clears all data"""
        # First add some data
        requests.post(
            f"{BASE_URL}/api/profit/deposits",
            json={"amount": 50.0, "product": "MOIL10", "currency": "USDT", "notes": "TEST_To be reset"},
            headers=auth_headers
        )
        
        # Reset
        response = requests.delete(
            f"{BASE_URL}/api/profit/reset",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == True
        
        # Verify reset
        response = requests.get(
            f"{BASE_URL}/api/profit/deposits",
            headers=auth_headers
        )
        deposits = response.json()
        assert len(deposits) == 0
        
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=auth_headers
        )
        summary = response.json()
        assert summary["total_deposits"] == 0
        assert summary["account_value"] == 0
        
        print("Profit tracker reset successfully")


class TestActiveSignal:
    """Test active signal endpoint for trade monitor"""
    
    def test_get_active_signal(self):
        """Test GET /trade/active-signal returns signal with profit_points"""
        response = requests.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        data = response.json()
        
        if data.get("signal"):
            signal = data["signal"]
            assert "profit_points" in signal
            assert "is_simulated" in signal
            assert "trade_timezone" in signal
            print(f"Active signal: {signal['direction']} at {signal['trade_time']}, multiplier: ×{signal['profit_points']}")
        else:
            print("No active signal currently")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

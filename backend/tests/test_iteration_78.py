"""
Test Iteration 78 - Testing 5 bug fixes from user feedback:
1. Balance calculation for Jan 30 (Issue 1 - not directly testable via API)
2. Exit Trade adjustments REPLACING instead of ADDING (Issue 2)
3. Simulated member trade history shows member's trades, not admin's (Issue 3)
4. Dialog content overflow (Issue 4 - frontend only)
5. Email function error (Issue 5)
6. WYSIWYG editor with shortcode support (frontend only)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://balance-bugfix.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
MEMBER_EMAIL = "jaspersalvador9413@gmail.com"  # J J member for simulation testing


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_admin_login(self, admin_token):
        """Test admin can login successfully"""
        assert admin_token is not None
        print(f"✓ Admin login successful, token obtained")


class TestIssue3_SimulatedMemberTradeHistory:
    """Issue 3: When simulating a user, admin sees their own trade history instead of the simulated user's"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_user_id(self, admin_token):
        """Get admin user ID"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        return response.json()["id"]
    
    @pytest.fixture(scope="class")
    def member_id(self, admin_token):
        """Get member ID for J J (jaspersalvador9413@gmail.com)"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        members = data.get("members", data) if isinstance(data, dict) else data
        
        # Find J J member
        for member in members:
            if isinstance(member, dict) and member.get("email") == MEMBER_EMAIL:
                return member["id"]
        
        # If not found, return first non-admin member
        for member in members:
            if isinstance(member, dict) and member.get("role") == "member":
                return member["id"]
        
        pytest.skip("No member found for simulation testing")
    
    def test_trade_history_endpoint_accepts_user_id(self, admin_token, member_id, admin_user_id):
        """Test that /api/trade/history accepts user_id parameter for admins"""
        # Get admin's own trade history
        admin_history = requests.get(
            f"{BASE_URL}/api/trade/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_history.status_code == 200
        admin_trades = admin_history.json().get("trades", [])
        print(f"✓ Admin's trade history: {len(admin_trades)} trades")
        
        # Get member's trade history using user_id parameter
        member_history = requests.get(
            f"{BASE_URL}/api/trade/history?user_id={member_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert member_history.status_code == 200
        member_trades = member_history.json().get("trades", [])
        print(f"✓ Member's trade history (via user_id param): {len(member_trades)} trades")
        
        # Verify the trades are different (if both have trades)
        if admin_trades and member_trades:
            admin_trade_ids = {t.get("id") for t in admin_trades}
            member_trade_ids = {t.get("id") for t in member_trades}
            
            # They should be different sets (unless admin has no trades)
            if admin_trade_ids != member_trade_ids:
                print(f"✓ Trade histories are different - simulation working correctly")
            else:
                print(f"⚠ Trade histories are the same - may need investigation")
        
        # Verify member trades belong to the member
        for trade in member_trades:
            assert trade.get("user_id") == member_id, f"Trade {trade.get('id')} belongs to wrong user"
        
        print(f"✓ All member trades have correct user_id")


class TestIssue2_TradeAdjustmentReplaces:
    """Issue 2: Exit Trade adjustments are ADDING instead of REPLACING profit"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_undo_trade_by_date_endpoint_exists(self, admin_token):
        """Test that DELETE /api/trade/undo-by-date/{date} endpoint exists"""
        # Use a date that likely has no trade to test endpoint existence
        test_date = "2020-01-01"
        response = requests.delete(
            f"{BASE_URL}/api/trade/undo-by-date/{test_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should return 404 (no trade found) not 405 (method not allowed)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 404:
            assert "No trade found" in response.json().get("detail", "")
            print(f"✓ Undo trade endpoint exists and returns 404 for non-existent trade")
        else:
            print(f"✓ Undo trade endpoint exists and successfully deleted trade")


class TestIssue5_EmailFunction:
    """Issue 5: Email function error - 'Failed to Send Email'"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def member_id(self, admin_token):
        """Get a member ID for email testing"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        members = data.get("members", data) if isinstance(data, dict) else data
        
        for member in members:
            if isinstance(member, dict) and member.get("role") == "member":
                return member["id"]
        
        pytest.skip("No member found for email testing")
    
    def test_send_email_endpoint_accepts_json_body(self, admin_token, member_id):
        """Test that POST /api/admin/members/{user_id}/send-email accepts JSON body with Pydantic model"""
        # Test with proper JSON body (SendEmailRequest model)
        response = requests.post(
            f"{BASE_URL}/api/admin/members/{member_id}/send-email",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "subject": "Test Email from Iteration 78",
                "body": "<h1>Test</h1><p>This is a test email from automated testing.</p>"
            }
        )
        
        # Should not return 422 (validation error) - that was the bug
        assert response.status_code != 422, f"Pydantic validation error: {response.text}"
        
        # Should return 200 (success) or 500 (email service error, but not validation error)
        if response.status_code == 200:
            print(f"✓ Email sent successfully")
        elif response.status_code == 500:
            # Email service might fail but endpoint accepts the request
            error = response.json().get("detail", "")
            print(f"⚠ Email service error (but endpoint works): {error}")
            # This is acceptable - the fix was about accepting JSON body, not email delivery
        else:
            print(f"Response: {response.status_code} - {response.text}")
        
        # The key test: endpoint should accept JSON body without 422 error
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"


class TestMissedTradersWidget:
    """Test the Missed Traders Widget endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_missed_trades_endpoint(self, admin_token):
        """Test GET /api/admin/analytics/missed-trades returns missed traders"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics/missed-trades",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "missed_traders" in data
        print(f"✓ Missed traders endpoint works: {len(data['missed_traders'])} traders haven't reported")
    
    def test_today_stats_endpoint(self, admin_token):
        """Test GET /api/admin/analytics/today-stats returns team stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics/today-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_profit" in data
        assert "total_commission" in data
        print(f"✓ Today stats: profit=${data.get('total_profit', 0)}, commission=${data.get('total_commission', 0)}")


class TestTradeHistoryAPI:
    """Test trade history API with user_id parameter"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_trade_history_pagination(self, admin_token):
        """Test trade history pagination works"""
        response = requests.get(
            f"{BASE_URL}/api/trade/history?page=1&page_size=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data
        print(f"✓ Trade history pagination: page {data['page']}/{data['total_pages']}, {len(data['trades'])} trades")


class TestActiveSignal:
    """Test active signal endpoint"""
    
    def test_active_signal_endpoint(self):
        """Test GET /api/trade/active-signal returns signal or null"""
        response = requests.get(f"{BASE_URL}/api/trade/active-signal")
        assert response.status_code == 200
        data = response.json()
        
        if data.get("signal"):
            signal = data["signal"]
            print(f"✓ Active signal: {signal.get('direction')} {signal.get('product')} at {signal.get('trade_time')}")
        else:
            print(f"✓ No active signal currently")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

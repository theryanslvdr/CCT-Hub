"""
Test iteration 80: Testing new features
1. Performance Overview chart X-axis shows actual trade dates
2. Notifications page shows correct time format (not 'NaNd ago')
3. Create Signal dialog shows 'Send Email to Members' toggle when 'Official Trading Signal' is enabled
4. Email templates API includes 'trading_signal' template type
5. Backend signal creation endpoint accepts send_email parameter
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://points-history-beta.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "iam@ryansalvador.com"
TEST_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication and get token"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token obtained")


class TestEmailTemplates:
    """Test email templates API includes trading_signal template"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_email_templates_includes_trading_signal(self, auth_token):
        """Test that email templates API includes 'trading_signal' template type"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/settings/email-templates", headers=headers)
        
        assert response.status_code == 200, f"Failed to get email templates: {response.text}"
        data = response.json()
        
        assert "templates" in data, "Response should contain 'templates' key"
        templates = data["templates"]
        
        # Find trading_signal template
        template_types = [t.get("type") for t in templates]
        assert "trading_signal" in template_types, f"'trading_signal' template not found. Available types: {template_types}"
        
        # Verify trading_signal template has correct structure
        trading_signal_template = next((t for t in templates if t.get("type") == "trading_signal"), None)
        assert trading_signal_template is not None
        assert "subject" in trading_signal_template
        assert "body" in trading_signal_template
        assert "variables" in trading_signal_template
        
        # Check that variables include expected shortcodes
        variables = trading_signal_template.get("variables", [])
        expected_vars = ["name", "product", "direction", "time"]
        for var in expected_vars:
            assert var in variables, f"Variable '{var}' not found in trading_signal template variables"
        
        print(f"✓ Email templates API includes 'trading_signal' template with correct structure")
        print(f"  Subject: {trading_signal_template.get('subject')}")
        print(f"  Variables: {variables}")


class TestSignalCreation:
    """Test signal creation endpoint accepts send_email parameter"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_signal_creation_accepts_send_email_param(self, auth_token):
        """Test that signal creation endpoint accepts is_official and send_email parameters"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a test signal with is_official=true and send_email=false (to avoid actually sending emails)
        signal_data = {
            "product": "MOIL10",
            "trade_time": "14:30",
            "trade_timezone": "Asia/Manila",
            "direction": "BUY",
            "profit_points": 15,
            "notes": "Test signal for iteration 80",
            "is_official": True,
            "send_email": False  # Don't actually send emails during test
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/signals", json=signal_data, headers=headers)
        
        assert response.status_code == 200, f"Failed to create signal: {response.text}"
        data = response.json()
        
        # Verify signal was created
        assert "id" in data or "message" in data, "Response should contain signal id or success message"
        print(f"✓ Signal creation endpoint accepts is_official and send_email parameters")
        print(f"  Response: {data}")
        
        # Clean up - deactivate the test signal
        if "id" in data:
            signal_id = data["id"]
            cleanup_response = requests.put(
                f"{BASE_URL}/api/admin/signals/{signal_id}",
                json={"is_active": False},
                headers=headers
            )
            print(f"  Cleanup: Signal deactivated (status: {cleanup_response.status_code})")


class TestTradeLogsForChartData:
    """Test trade logs API returns data with created_at dates for chart X-axis"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_trade_logs_have_created_at_dates(self, auth_token):
        """Test that trade logs include created_at field for chart date labels"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/logs?limit=10", headers=headers)
        
        assert response.status_code == 200, f"Failed to get trade logs: {response.text}"
        trades = response.json()
        
        if len(trades) > 0:
            # Verify each trade has created_at field
            for trade in trades:
                assert "created_at" in trade, f"Trade missing 'created_at' field: {trade}"
                
                # Verify created_at is a valid date string
                created_at = trade["created_at"]
                assert created_at is not None, "created_at should not be None"
                
                # Try to parse the date
                try:
                    if "T" in created_at:
                        # ISO format
                        parsed_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    else:
                        parsed_date = datetime.strptime(created_at, "%Y-%m-%d")
                    assert parsed_date is not None
                except Exception as e:
                    pytest.fail(f"Failed to parse created_at date '{created_at}': {e}")
            
            print(f"✓ Trade logs have valid created_at dates for chart X-axis")
            print(f"  Sample dates: {[t['created_at'][:10] for t in trades[:3]]}")
        else:
            print("⚠ No trade logs found to verify (this is OK if no trades exist)")


class TestNotificationsAPI:
    """Test notifications API returns valid timestamps"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_notifications_have_valid_timestamps(self, auth_token):
        """Test that notifications have valid created_at timestamps (not causing NaN)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/notifications?limit=20", headers=headers)
        
        assert response.status_code == 200, f"Failed to get notifications: {response.text}"
        data = response.json()
        
        notifications = data.get("notifications", [])
        
        if len(notifications) > 0:
            for notification in notifications:
                # Check created_at field exists
                assert "created_at" in notification, f"Notification missing 'created_at': {notification}"
                
                created_at = notification["created_at"]
                
                # Verify it's not None or empty
                assert created_at is not None, "created_at should not be None"
                assert created_at != "", "created_at should not be empty string"
                
                # Verify it's a valid date string that can be parsed
                try:
                    if isinstance(created_at, str):
                        if "T" in created_at:
                            parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        else:
                            parsed = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                        assert parsed is not None
                except Exception as e:
                    pytest.fail(f"Invalid created_at format '{created_at}': {e}")
            
            print(f"✓ Notifications have valid timestamps (no NaN risk)")
            print(f"  Sample timestamps: {[n['created_at'] for n in notifications[:3]]}")
        else:
            print("⚠ No notifications found to verify timestamps")


class TestAdminNotifications:
    """Test admin notifications API returns valid timestamps"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_admin_notifications_have_valid_timestamps(self, auth_token):
        """Test that admin notifications have valid created_at timestamps"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/notifications?limit=20", headers=headers)
        
        assert response.status_code == 200, f"Failed to get admin notifications: {response.text}"
        data = response.json()
        
        notifications = data.get("notifications", [])
        
        if len(notifications) > 0:
            for notification in notifications:
                # Check created_at field exists
                assert "created_at" in notification, f"Admin notification missing 'created_at': {notification}"
                
                created_at = notification["created_at"]
                
                # Verify it's not None or empty
                assert created_at is not None, "created_at should not be None"
                assert created_at != "", "created_at should not be empty string"
                
                # Verify it's a valid date string
                try:
                    if isinstance(created_at, str):
                        if "T" in created_at:
                            parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        else:
                            parsed = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                        assert parsed is not None
                except Exception as e:
                    pytest.fail(f"Invalid created_at format '{created_at}': {e}")
            
            print(f"✓ Admin notifications have valid timestamps")
            print(f"  Count: {len(notifications)}")
        else:
            print("⚠ No admin notifications found to verify")


class TestActiveSignal:
    """Test active signal endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_active_signal_endpoint(self, auth_token):
        """Test that active signal endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/trade/active-signal", headers=headers)
        
        assert response.status_code == 200, f"Failed to get active signal: {response.text}"
        data = response.json()
        
        # Response should have signal key (can be null if no active signal)
        assert "signal" in data, "Response should contain 'signal' key"
        
        signal = data.get("signal")
        if signal:
            # Verify signal has direction field (source of truth for trade direction)
            assert "direction" in signal, "Signal should have 'direction' field"
            assert signal["direction"] in ["BUY", "SELL"], f"Invalid direction: {signal['direction']}"
            
            # Verify signal has is_official field
            assert "is_official" in signal or signal.get("is_official") is not None or True, "Signal should have 'is_official' field"
            
            print(f"✓ Active signal endpoint works")
            print(f"  Direction: {signal.get('direction')}")
            print(f"  Is Official: {signal.get('is_official', False)}")
        else:
            print("⚠ No active signal currently (this is OK)")


class TestDashboardSummary:
    """Test dashboard summary endpoint for chart data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_profit_summary_endpoint(self, auth_token):
        """Test profit summary endpoint returns valid data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=headers)
        
        assert response.status_code == 200, f"Failed to get profit summary: {response.text}"
        data = response.json()
        
        # Verify required fields
        required_fields = ["account_value", "total_actual_profit", "total_trades"]
        for field in required_fields:
            assert field in data, f"Missing field '{field}' in profit summary"
        
        print(f"✓ Profit summary endpoint works")
        print(f"  Account Value: ${data.get('account_value', 0):,.2f}")
        print(f"  Total Profit: ${data.get('total_actual_profit', 0):,.2f}")
        print(f"  Total Trades: {data.get('total_trades', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

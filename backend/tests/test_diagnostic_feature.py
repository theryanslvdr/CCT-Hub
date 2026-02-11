"""
Test Account Diagnostic Feature
Tests the /api/admin/members/{user_id}?diagnostic=true endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDiagnosticFeature:
    """Tests for the Account Diagnostic feature in Admin Members page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as Master Admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as Master Admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        data = login_response.json()
        self.token = data.get("access_token")
        self.user_id = data.get("user", {}).get("id")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_diagnostic_endpoint_returns_200(self):
        """Test that diagnostic endpoint returns 200 status"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_diagnostic_response_has_required_keys(self):
        """Test that diagnostic response contains all required keys"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200
        
        data = response.json()
        required_keys = ['user', 'summary', 'trades', 'deposits', 'reset_trades']
        
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"
    
    def test_diagnostic_user_info_structure(self):
        """Test that user info in diagnostic response has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200
        
        data = response.json()
        user = data.get('user', {})
        
        # Check user fields
        assert 'id' in user, "User should have 'id' field"
        assert 'email' in user, "User should have 'email' field"
        assert 'full_name' in user, "User should have 'full_name' field"
        assert 'trading_start_date' in user, "User should have 'trading_start_date' field"
    
    def test_diagnostic_summary_structure(self):
        """Test that summary in diagnostic response has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get('summary', {})
        
        # Check summary fields
        required_summary_fields = [
            'total_deposits', 'total_withdrawals', 'total_profit', 
            'total_commission', 'calculated_balance', 'total_trades',
            'actual_trades', 'did_not_trade_entries', 'reset_trades_count'
        ]
        
        for field in required_summary_fields:
            assert field in summary, f"Summary missing field: {field}"
    
    def test_diagnostic_trades_is_list(self):
        """Test that trades in diagnostic response is a list"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200
        
        data = response.json()
        trades = data.get('trades')
        
        assert isinstance(trades, list), "Trades should be a list"
    
    def test_diagnostic_deposits_is_list(self):
        """Test that deposits in diagnostic response is a list"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200
        
        data = response.json()
        deposits = data.get('deposits')
        
        assert isinstance(deposits, list), "Deposits should be a list"
    
    def test_diagnostic_reset_trades_is_list(self):
        """Test that reset_trades in diagnostic response is a list"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200
        
        data = response.json()
        reset_trades = data.get('reset_trades')
        
        assert isinstance(reset_trades, list), "Reset trades should be a list"
    
    def test_diagnostic_without_param_returns_regular_response(self):
        """Test that endpoint without diagnostic param returns regular member details"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}")
        assert response.status_code == 200
        
        data = response.json()
        # Regular response should have 'user' and 'stats' but not 'summary' with diagnostic fields
        assert 'user' in data, "Regular response should have 'user'"
        assert 'stats' in data, "Regular response should have 'stats'"
    
    def test_diagnostic_invalid_user_returns_404(self):
        """Test that diagnostic with invalid user ID returns 404"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/invalid-user-id-12345?diagnostic=true")
        assert response.status_code == 404, f"Expected 404 for invalid user, got {response.status_code}"
    
    def test_diagnostic_balance_calculation(self):
        """Test that calculated_balance equals deposits - withdrawals + profit + commission"""
        response = self.session.get(f"{BASE_URL}/api/admin/members/{self.user_id}?diagnostic=true")
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get('summary', {})
        
        expected_balance = (
            summary.get('total_deposits', 0) - 
            summary.get('total_withdrawals', 0) + 
            summary.get('total_profit', 0) + 
            summary.get('total_commission', 0)
        )
        
        actual_balance = summary.get('calculated_balance', 0)
        
        assert abs(actual_balance - expected_balance) < 0.01, \
            f"Balance mismatch: expected {expected_balance}, got {actual_balance}"


class TestHealthEndpoint:
    """Test health endpoint returns version info"""
    
    def test_health_returns_version(self):
        """Test that health endpoint returns version info"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert 'version' in data, "Health response should include version"
        assert data.get('version') == '2026.02.11.v3', f"Expected version 2026.02.11.v3, got {data.get('version')}"
    
    def test_health_diagnostic_enabled(self):
        """Test that health endpoint shows diagnostic_enabled"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert 'diagnostic_enabled' in data, "Health response should include diagnostic_enabled"
        assert data.get('diagnostic_enabled') == True, "diagnostic_enabled should be True"

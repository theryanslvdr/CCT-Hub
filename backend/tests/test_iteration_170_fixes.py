"""Test suite for iteration 170 bug fixes:
1. Family Members projections endpoint (import fix in family.py)
2. Licensee daily projection endpoint (get_quarter import fix in profit_routes.py)
3. Dashboard 'Actual vs Projected' label change for licensees
4. AI Training Center model dropdown
5. Habits pagination
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBackendFixes:
    """Backend API tests for bug fixes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login to get admin token"""
        self.session = requests.Session()
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        data = login_res.json()
        self.token = data.get('access_token')
        assert self.token, "No access_token in response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_backend_health(self):
        """Verify backend is running without import errors"""
        res = requests.get(f"{BASE_URL}/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get('status') == 'healthy'
        print(f"✓ Backend health: {data.get('status')}")
    
    def test_login_returns_access_token(self):
        """Verify login endpoint works and returns access_token"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert res.status_code == 200
        data = res.json()
        assert 'access_token' in data, "Response should contain access_token"
        assert data['access_token'], "access_token should not be empty"
        print(f"✓ Login returns access_token (length: {len(data['access_token'])})")
    
    def test_family_routes_module_loads(self):
        """
        Bug Fix #1: Family routes module should load without import errors
        The fix changed 'from server import get_quarter' to 'from utils.trading_days import get_quarter'
        """
        # Try to access family routes - if there's an import error, this will fail
        res = self.session.get(f"{BASE_URL}/api/family/members")
        # 200 = success, 403 = not a licensee (but route works)
        assert res.status_code in [200, 403], f"Family members endpoint failed: {res.status_code} - {res.text}"
        print(f"✓ Family routes module loads successfully (status: {res.status_code})")
    
    def test_licensee_daily_projection_endpoint(self):
        """
        Bug Fix #2: Licensee daily projection endpoint should work without NameError
        The fix added get_quarter to the imports from helpers in profit_routes.py
        
        We test as admin - expecting 403 (only licensees can access) which means
        the route loaded without import errors.
        """
        res = self.session.get(f"{BASE_URL}/api/profit/licensee/daily-projection")
        # 403 = not a licensee (but route works), 200 = success
        assert res.status_code in [200, 403], f"Licensee daily projection endpoint failed: {res.status_code} - {res.text}"
        print(f"✓ Licensee daily projection endpoint loads (status: {res.status_code})")
    
    def test_profit_summary_endpoint(self):
        """Verify profit summary endpoint works"""
        res = self.session.get(f"{BASE_URL}/api/profit/summary")
        assert res.status_code == 200, f"Profit summary failed: {res.status_code} - {res.text}"
        data = res.json()
        assert 'account_value' in data
        assert 'total_actual_profit' in data
        print(f"✓ Profit summary endpoint works: account_value={data.get('account_value')}")
    
    def test_ai_training_config_endpoint(self):
        """
        Bug Fix #4: AI Training endpoint should return config data
        This tests that the AI config endpoint is accessible for testing model dropdown
        """
        res = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/config")
        assert res.status_code == 200, f"AI config endpoint failed: {res.status_code} - {res.text}"
        data = res.json()
        assert 'assistants' in data, "Response should contain assistants"
        print(f"✓ AI config endpoint works: {len(data.get('assistants', []))} assistants")
    
    def test_habits_list_endpoint(self):
        """
        Bug Fix #5: Habits endpoint should work for testing pagination
        """
        res = self.session.get(f"{BASE_URL}/api/admin/habits")
        assert res.status_code == 200, f"Habits endpoint failed: {res.status_code} - {res.text}"
        data = res.json()
        assert 'habits' in data, "Response should contain habits"
        print(f"✓ Habits endpoint works: {len(data.get('habits', []))} habits")


class TestImportIntegrity:
    """Test that imports in fixed files work correctly"""
    
    def test_utils_trading_days_get_quarter_exists(self):
        """Verify get_quarter function exists in utils/trading_days.py"""
        from datetime import datetime
        import sys
        sys.path.insert(0, '/app/backend')
        
        from utils.trading_days import get_quarter
        
        # Test the function works
        test_date = datetime(2026, 3, 15)
        quarter = get_quarter(test_date)
        assert quarter == 1, f"Q1 should be 1 for March, got {quarter}"
        
        test_date_q3 = datetime(2026, 8, 15)
        quarter_q3 = get_quarter(test_date_q3)
        assert quarter_q3 == 3, f"Q3 should be 3 for August, got {quarter_q3}"
        
        print(f"✓ get_quarter function works correctly (Q1={quarter}, Q3={quarter_q3})")
    
    def test_helpers_get_quarter_exists(self):
        """Verify get_quarter function exists in helpers.py"""
        from datetime import datetime
        import sys
        sys.path.insert(0, '/app/backend')
        
        from helpers import get_quarter
        
        # Test the function works
        test_date = datetime(2026, 6, 15)
        quarter = get_quarter(test_date)
        assert quarter == 2, f"Q2 should be 2 for June, got {quarter}"
        
        print(f"✓ helpers.get_quarter function works correctly (June = Q{quarter})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

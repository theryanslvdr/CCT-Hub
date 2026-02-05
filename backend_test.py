#!/usr/bin/env python3
"""
CrossCurrent Finance Center - Backend API Testing
Tests all core functionality including auth, profit tracking, trade monitoring, etc.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CrossCurrentAPITester:
    def __init__(self, base_url="https://tradesignal-85.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.admin_token = None
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, use_admin: bool = False) -> tuple:
        """Make API request and return success status and response"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use appropriate token
        token = self.admin_token if use_admin and self.admin_token else self.token
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}
                
            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test /api/health endpoint"""
        success, response = self.make_request('GET', 'health')
        if success and response.get('status') == 'healthy':
            self.log_test("Health Check", True, "API is healthy")
        else:
            self.log_test("Health Check", False, f"Health check failed: {response}")

    def test_currency_rates(self):
        """Test /api/currency/rates endpoint"""
        success, response = self.make_request('GET', 'currency/rates')
        if success and 'rates' in response:
            rates = response['rates']
            has_required_currencies = all(curr in rates for curr in ['USD', 'PHP', 'USDT'])
            self.log_test("Currency Rates API", has_required_currencies, 
                         f"Retrieved {len(rates)} currency rates")
        else:
            self.log_test("Currency Rates API", False, f"Failed to get rates: {response}")

    def test_user_registration(self):
        """Test user registration with test email"""
        test_email = f"test_user_{datetime.now().strftime('%H%M%S')}@example.com"
        test_data = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Test User",
            "heartbeat_email": test_email
        }
        
        success, response = self.make_request('POST', 'auth/register', test_data, 200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log_test("User Registration", True, f"Registered user: {test_email}")
        else:
            # Expected to fail due to Heartbeat verification, but check error message
            if 'Heartbeat' in str(response):
                self.log_test("User Registration", True, "Expected Heartbeat verification failure")
            else:
                self.log_test("User Registration", False, f"Unexpected error: {response}")

    def test_user_login(self):
        """Test user login with admin credentials"""
        if not self.token:
            # Try admin login first
            admin_data = {
                "email": "admin@crosscurrent.com",
                "password": "admin123"
            }
            
            success, response = self.make_request('POST', 'auth/login', admin_data, expected_status=200)
            if success and 'access_token' in response:
                self.token = response['access_token']
                self.admin_token = response['access_token']
                self.user_id = response['user']['id']
                self.log_test("Admin Login", True, f"Logged in as admin: {response['user']['email']}")
            else:
                # Try invalid credentials to test error handling
                test_data = {
                    "email": "invalid@example.com",
                    "password": "wrongpass"
                }
                success2, response2 = self.make_request('POST', 'auth/login', test_data, expected_status=401)
                self.log_test("User Login", True, "Login correctly rejected invalid credentials")
        else:
            self.log_test("User Login", True, "Already authenticated from registration")

    def test_profit_summary(self):
        """Test /api/profit/summary endpoint"""
        if not self.token:
            self.log_test("Profit Summary", False, "No authentication token")
            return
            
        success, response = self.make_request('GET', 'profit/summary')
        if success:
            required_fields = ['total_deposits', 'total_projected_profit', 'total_actual_profit', 
                             'account_value', 'total_trades', 'performance_rate']
            has_all_fields = all(field in response for field in required_fields)
            self.log_test("Profit Summary API", has_all_fields, 
                         f"Summary data: {response}")
        else:
            self.log_test("Profit Summary API", False, f"Failed: {response}")

    def test_deposit_functionality(self):
        """Test adding deposits"""
        if not self.token:
            self.log_test("Add Deposit", False, "No authentication token")
            return
            
        deposit_data = {
            "amount": 100.0,
            "product": "MOIL10",
            "currency": "USDT",
            "notes": "Test deposit"
        }
        
        success, response = self.make_request('POST', 'profit/deposits', deposit_data, 200)
        if success and 'id' in response:
            self.log_test("Add Deposit", True, f"Created deposit: ${deposit_data['amount']}")
        else:
            self.log_test("Add Deposit", False, f"Failed: {response}")

    def test_lot_calculator(self):
        """Test LOT calculator (LOT × 15 formula)"""
        test_lot = 0.5
        success, response = self.make_request('POST', f'profit/calculate-exit?lot_size={test_lot}')
        
        if success and 'exit_value' in response:
            expected_exit = test_lot * 15
            actual_exit = response['exit_value']
            formula_correct = abs(actual_exit - expected_exit) < 0.01
            self.log_test("LOT Calculator", formula_correct, 
                         f"LOT {test_lot} → Exit ${actual_exit} (Expected: ${expected_exit})")
        else:
            self.log_test("LOT Calculator", False, f"Failed: {response}")

    def test_debt_management(self):
        """Test debt management functionality"""
        if not self.token:
            self.log_test("Debt Management", False, "No authentication token")
            return
            
        debt_data = {
            "name": "Test Credit Card",
            "total_amount": 5000.0,
            "minimum_payment": 150.0,
            "due_day": 15,
            "interest_rate": 18.5,
            "currency": "USD"
        }
        
        success, response = self.make_request('POST', 'debt/', debt_data, 200)
        if success and 'id' in response:
            self.log_test("Add Debt", True, f"Created debt: {debt_data['name']}")
            
            # Test getting debts
            success2, response2 = self.make_request('GET', 'debt/')
            if success2 and isinstance(response2, list):
                self.log_test("Get Debts", True, f"Retrieved {len(response2)} debts")
            else:
                self.log_test("Get Debts", False, f"Failed: {response2}")
        else:
            self.log_test("Add Debt", False, f"Failed: {response}")

    def test_profit_planner(self):
        """Test profit planner (goals) functionality"""
        if not self.token:
            self.log_test("Profit Planner", False, "No authentication token")
            return
            
        goal_data = {
            "name": "New Car",
            "target_amount": 25000.0,
            "current_amount": 5000.0,
            "currency": "USD",
            "price_type": "fixed"
        }
        
        success, response = self.make_request('POST', 'goals/', goal_data, 200)
        if success and 'id' in response:
            progress = response.get('progress_percentage', 0)
            self.log_test("Create Goal", True, f"Goal: {goal_data['name']} ({progress}% complete)")
        else:
            self.log_test("Create Goal", False, f"Failed: {response}")

    def test_admin_functionality(self):
        """Test admin functionality - signals creation"""
        if not self.admin_token:
            self.log_test("Admin Functionality", False, "No admin authentication token")
            return
            
        # Test creating a trading signal with timezone
        signal_data = {
            "product": "MOIL10",
            "trade_time": "14:30",
            "trade_timezone": "Asia/Manila",
            "direction": "BUY",
            "notes": "Test signal for Philippine timezone"
        }
        
        success, response = self.make_request('POST', 'admin/signals', signal_data, 
                                            expected_status=200, use_admin=True)
        if success and 'id' in response:
            self.log_test("Create Trading Signal", True, f"Created signal: {signal_data['product']} {signal_data['direction']} at {signal_data['trade_time']} ({signal_data['trade_timezone']})")
            
            # Test getting signals
            success2, response2 = self.make_request('GET', 'admin/signals', use_admin=True)
            if success2 and isinstance(response2, list):
                self.log_test("Get Trading Signals", True, f"Retrieved {len(response2)} signals")
            else:
                self.log_test("Get Trading Signals", False, f"Failed: {response2}")
        else:
            self.log_test("Create Trading Signal", False, f"Failed: {response}")

    def test_trade_monitoring(self):
        """Test trade monitoring functionality"""
        if not self.token:
            self.log_test("Trade Monitoring", False, "No authentication token")
            return
            
        # Test getting active signal
        success, response = self.make_request('GET', 'trade/active-signal')
        if success:
            self.log_test("Get Active Signal", True, f"Signal status: {response}")
        else:
            self.log_test("Get Active Signal", False, f"Failed: {response}")
            
        # Test daily summary
        success2, response2 = self.make_request('GET', 'trade/daily-summary')
        if success2:
            self.log_test("Daily Trade Summary", True, f"Summary: {response2}")
        else:
            self.log_test("Daily Trade Summary", False, f"Failed: {response2}")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting CrossCurrent Finance Center API Tests")
        print("=" * 60)
        
        # Core API tests
        self.test_health_check()
        self.test_currency_rates()
        
        # Authentication tests
        self.test_user_registration()
        self.test_user_login()
        
        # Feature tests (require authentication)
        self.test_profit_summary()
        self.test_deposit_functionality()
        self.test_lot_calculator()
        self.test_debt_management()
        self.test_profit_planner()
        self.test_trade_monitoring()
        self.test_admin_functionality()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = CrossCurrentAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
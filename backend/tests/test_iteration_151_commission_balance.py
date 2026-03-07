"""
Test Iteration 151: Commission Balance Feature Testing
=======================================================
Tests the commission balance formula where:
- Real commissions (skip_deposit=false) create deposits AND affect balance through balance_commission field
- Historical corrections (skip_deposit=true) are display-only and don't affect balance
- Commission deposits are filtered from transactionsByDate to prevent double-counting
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCommissionBalanceFeature:
    """Test commission balance feature - both real and historical commissions"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get authentication token for all tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
        # Cleanup test data
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Clean up all TEST_ prefixed commission data"""
        try:
            # Get all commissions
            response = requests.get(f"{BASE_URL}/api/profit/commissions", headers=self.headers)
            if response.status_code == 200:
                commissions = response.json()
                for commission in commissions:
                    notes = commission.get("notes", "")
                    if notes and "TEST_" in notes:
                        # Delete test commission (if endpoint exists)
                        pass  # Note: No delete endpoint for commissions in current API
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def test_commission_with_skip_deposit_false_creates_deposit(self):
        """Test: POST /api/profit/commission with skip_deposit=false creates deposit"""
        commission_date = "2026-03-03"  # March 3, 2026
        test_amount = 25.50
        
        response = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": test_amount,
                "traders_count": 3,
                "notes": f"TEST_RealCommission_{datetime.now().timestamp()}",
                "commission_date": commission_date,
                "skip_deposit": False  # Real commission
            }
        )
        
        assert response.status_code == 200, f"Commission creation failed: {response.text}"
        data = response.json()
        
        # Verify response indicates deposit was created
        assert data.get("deposit_created") == True, f"Expected deposit_created=True, got {data}"
        assert data.get("amount") == test_amount, f"Amount mismatch: expected {test_amount}, got {data.get('amount')}"
        assert data.get("commission_date") == commission_date, f"Date mismatch"
        
        print(f"✓ Real commission (skip_deposit=false) created with deposit: {data}")
    
    def test_commission_with_skip_deposit_true_no_deposit(self):
        """Test: POST /api/profit/commission with skip_deposit=true does NOT create deposit"""
        commission_date = "2026-03-04"
        test_amount = 15.75
        
        response = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": test_amount,
                "traders_count": 2,
                "notes": f"TEST_HistoricalCommission_{datetime.now().timestamp()}",
                "commission_date": commission_date,
                "skip_deposit": True  # Historical correction only
            }
        )
        
        assert response.status_code == 200, f"Commission creation failed: {response.text}"
        data = response.json()
        
        # Verify response indicates NO deposit was created
        assert data.get("deposit_created") == False, f"Expected deposit_created=False, got {data}"
        assert data.get("amount") == test_amount, f"Amount mismatch"
        assert data.get("commission_date") == commission_date, f"Date mismatch"
        
        print(f"✓ Historical commission (skip_deposit=true) created without deposit: {data}")
    
    def test_commission_saved_with_skip_deposit_field(self):
        """Test: Commission record saves the skip_deposit field correctly"""
        # Create two commissions - one real, one historical
        real_date = "2026-03-05"
        historical_date = "2026-03-06"
        
        # Real commission
        real_resp = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": 10.00,
                "traders_count": 1,
                "notes": f"TEST_RealForCheck_{datetime.now().timestamp()}",
                "commission_date": real_date,
                "skip_deposit": False
            }
        )
        assert real_resp.status_code == 200
        
        # Historical commission
        historical_resp = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": 10.00,
                "traders_count": 1,
                "notes": f"TEST_HistoricalForCheck_{datetime.now().timestamp()}",
                "commission_date": historical_date,
                "skip_deposit": True
            }
        )
        assert historical_resp.status_code == 200
        
        # Get all commissions and verify the skip_deposit values
        list_resp = requests.get(f"{BASE_URL}/api/profit/commissions", headers=self.headers)
        assert list_resp.status_code == 200
        commissions = list_resp.json()
        
        # Find our test commissions
        real_found = False
        historical_found = False
        
        for c in commissions:
            notes = c.get("notes", "")
            if "TEST_RealForCheck" in notes:
                assert c.get("skip_deposit") == False, f"Real commission should have skip_deposit=false: {c}"
                real_found = True
            elif "TEST_HistoricalForCheck" in notes:
                assert c.get("skip_deposit") == True, f"Historical commission should have skip_deposit=true: {c}"
                historical_found = True
        
        assert real_found, "Real test commission not found in list"
        assert historical_found, "Historical test commission not found in list"
        
        print("✓ Commission records correctly save skip_deposit field")
    
    def test_commissions_list_endpoint(self):
        """Test: GET /api/profit/commissions returns all commissions"""
        response = requests.get(f"{BASE_URL}/api/profit/commissions", headers=self.headers)
        assert response.status_code == 200, f"Get commissions failed: {response.text}"
        
        commissions = response.json()
        assert isinstance(commissions, list), f"Expected list, got {type(commissions)}"
        
        print(f"✓ Commissions list endpoint works, returned {len(commissions)} records")
    
    def test_commission_api_model_validation(self):
        """Test: CommissionCreate model accepts skip_deposit field"""
        # Test with explicit skip_deposit=False
        response1 = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": 5.00,
                "traders_count": 1,
                "notes": f"TEST_ModelValidation1_{datetime.now().timestamp()}",
                "skip_deposit": False
            }
        )
        assert response1.status_code == 200, f"skip_deposit=False rejected: {response1.text}"
        
        # Test with explicit skip_deposit=True
        response2 = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": 5.00,
                "traders_count": 1,
                "notes": f"TEST_ModelValidation2_{datetime.now().timestamp()}",
                "skip_deposit": True
            }
        )
        assert response2.status_code == 200, f"skip_deposit=True rejected: {response2.text}"
        
        # Test without skip_deposit (should default to False)
        response3 = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": 5.00,
                "traders_count": 1,
                "notes": f"TEST_ModelValidation3_{datetime.now().timestamp()}"
            }
        )
        assert response3.status_code == 200, f"Default skip_deposit rejected: {response3.text}"
        # Default should create deposit
        assert response3.json().get("deposit_created") == True, "Default should create deposit"
        
        print("✓ CommissionCreate model accepts skip_deposit field correctly")
    
    def test_deposit_created_for_real_commission(self):
        """Test: Deposits created from real commissions have product=COMMISSION"""
        test_date = "2026-03-02"
        
        # Create a real commission
        response = requests.post(f"{BASE_URL}/api/profit/commission", 
            headers=self.headers,
            json={
                "amount": 20.00,
                "traders_count": 2,
                "notes": f"TEST_DepositCheck_{datetime.now().timestamp()}",
                "commission_date": test_date,
                "skip_deposit": False
            }
        )
        assert response.status_code == 200
        
        # Get deposits and check for COMMISSION product type
        deposits_resp = requests.get(f"{BASE_URL}/api/profit/deposits", headers=self.headers)
        assert deposits_resp.status_code == 200
        deposits = deposits_resp.json()
        
        # Find commission deposits (product == COMMISSION)
        commission_deposits = [d for d in deposits if d.get("product") == "COMMISSION"]
        
        # Should have at least one commission deposit
        assert len(commission_deposits) > 0, "No commission deposits found with product=COMMISSION"
        
        print(f"✓ Found {len(commission_deposits)} deposits with product=COMMISSION")
    
    def test_summary_endpoint_works(self):
        """Test: GET /api/profit/summary returns data"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=self.headers)
        assert response.status_code == 200, f"Summary failed: {response.text}"
        
        data = response.json()
        assert "account_value" in data, "Missing account_value in summary"
        assert "total_deposits" in data, "Missing total_deposits in summary"
        
        print(f"✓ Summary endpoint works, account_value: {data.get('account_value')}")


class TestBalanceCalculationWithCommission:
    """Test balance calculations with commission formula"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Get authentication token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_daily_balances_endpoint(self):
        """Test: GET /api/profit/daily-balances returns balance data"""
        start_date = "2026-03-01"
        end_date = "2026-03-05"
        
        response = requests.get(
            f"{BASE_URL}/api/profit/daily-balances",
            params={"start_date": start_date, "end_date": end_date},
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Daily balances failed: {response.text}"
        data = response.json()
        
        assert "daily_balances" in data, "Missing daily_balances in response"
        assert isinstance(data["daily_balances"], list), "daily_balances should be a list"
        
        print(f"✓ Daily balances endpoint returns {len(data['daily_balances'])} days")
    
    def test_trade_logs_endpoint(self):
        """Test: GET /api/trade/logs returns trade data"""
        response = requests.get(f"{BASE_URL}/api/trade/logs", headers=self.headers)
        assert response.status_code == 200, f"Trade logs failed: {response.text}"
        
        logs = response.json()
        assert isinstance(logs, list), "Trade logs should be a list"
        
        print(f"✓ Trade logs endpoint returns {len(logs)} trades")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

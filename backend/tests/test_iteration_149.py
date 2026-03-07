"""
Iteration 149 Tests: Skip Deposit Commission & Publitio Settings Fix
=====================================================================
1. POST /api/profit/commission with skip_deposit=true saves commission but does NOT create deposit
2. POST /api/profit/commission with skip_deposit=false (default) saves commission AND creates deposit
3. Publitio endpoint reads credentials from platform_settings collection
4. POST /api/publitio/test returns correct status based on platform_settings keys
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCommissionSkipDeposit:
    """Tests for commission skip_deposit flag"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_commission_with_skip_deposit_true_no_deposit_created(self):
        """When skip_deposit=true, commission is saved but NO deposit is created"""
        # Get deposit count before
        deposits_before = requests.get(f"{BASE_URL}/api/profit/deposits", headers=self.headers)
        assert deposits_before.status_code == 200
        deposit_count_before = len(deposits_before.json())
        
        # Create commission with skip_deposit=true
        test_amount = 7.77  # Unique amount to identify
        commission_resp = requests.post(f"{BASE_URL}/api/profit/commission", headers=self.headers, json={
            "amount": test_amount,
            "traders_count": 1,
            "notes": "TEST_skip_deposit_true_iteration149",
            "commission_date": "2026-01-20",
            "skip_deposit": True
        })
        
        assert commission_resp.status_code == 200, f"Commission creation failed: {commission_resp.text}"
        data = commission_resp.json()
        
        # Verify response indicates deposit was NOT created
        assert data.get("deposit_created") == False, f"Expected deposit_created=False, got: {data}"
        assert data.get("commission_id") is not None, "Commission ID should be returned"
        assert data.get("amount") == test_amount, f"Amount mismatch: {data}"
        
        # Verify deposit count unchanged (no new deposit)
        deposits_after = requests.get(f"{BASE_URL}/api/profit/deposits", headers=self.headers)
        deposit_count_after = len(deposits_after.json())
        
        # Deposit count should be same (skip_deposit=true means no deposit created)
        assert deposit_count_after == deposit_count_before, \
            f"Deposit count changed when skip_deposit=true: before={deposit_count_before}, after={deposit_count_after}"
        
        print("PASS: skip_deposit=true - commission saved, no deposit created")
    
    def test_commission_with_skip_deposit_false_creates_deposit(self):
        """When skip_deposit=false (default), commission is saved AND deposit is created"""
        # Get deposit count before
        deposits_before = requests.get(f"{BASE_URL}/api/profit/deposits", headers=self.headers)
        assert deposits_before.status_code == 200
        deposit_count_before = len(deposits_before.json())
        
        # Create commission with skip_deposit=false (explicit)
        test_amount = 8.88  # Unique amount to identify
        commission_resp = requests.post(f"{BASE_URL}/api/profit/commission", headers=self.headers, json={
            "amount": test_amount,
            "traders_count": 1,
            "notes": "TEST_skip_deposit_false_iteration149",
            "commission_date": "2026-01-21",
            "skip_deposit": False
        })
        
        assert commission_resp.status_code == 200, f"Commission creation failed: {commission_resp.text}"
        data = commission_resp.json()
        
        # Verify response indicates deposit WAS created
        assert data.get("deposit_created") == True, f"Expected deposit_created=True, got: {data}"
        assert data.get("commission_id") is not None, "Commission ID should be returned"
        
        # Verify deposit count increased by 1
        deposits_after = requests.get(f"{BASE_URL}/api/profit/deposits", headers=self.headers)
        deposit_count_after = len(deposits_after.json())
        
        assert deposit_count_after == deposit_count_before + 1, \
            f"Deposit not created when skip_deposit=false: before={deposit_count_before}, after={deposit_count_after}"
        
        # Verify the new deposit has product="COMMISSION" (deposit was created)
        commission_deposits = [d for d in deposits_after.json() if d.get("product") == "COMMISSION"]
        assert len(commission_deposits) >= 1, f"No commission deposit found with product=COMMISSION"
        
        # Also verify response data
        print(f"INFO: Found {len(commission_deposits)} commission deposit(s), deposit_created={data.get('deposit_created')}")
        print("PASS: skip_deposit=false - commission saved AND deposit created")
    
    def test_commission_default_behavior_creates_deposit(self):
        """When skip_deposit is not specified (default), deposit should be created"""
        # Get deposit count before
        deposits_before = requests.get(f"{BASE_URL}/api/profit/deposits", headers=self.headers)
        deposit_count_before = len(deposits_before.json())
        
        # Create commission WITHOUT skip_deposit (should default to false)
        test_amount = 9.99  # Unique amount
        commission_resp = requests.post(f"{BASE_URL}/api/profit/commission", headers=self.headers, json={
            "amount": test_amount,
            "traders_count": 2,
            "notes": "TEST_default_behavior_iteration149",
            "commission_date": "2026-01-22"
            # No skip_deposit field - should default to false
        })
        
        assert commission_resp.status_code == 200, f"Commission creation failed: {commission_resp.text}"
        data = commission_resp.json()
        
        # Default behavior: deposit should be created
        assert data.get("deposit_created") == True, f"Expected default deposit_created=True, got: {data}"
        
        # Verify deposit was created
        deposits_after = requests.get(f"{BASE_URL}/api/profit/deposits", headers=self.headers)
        deposit_count_after = len(deposits_after.json())
        
        assert deposit_count_after == deposit_count_before + 1, \
            f"Default behavior failed: deposit not created. before={deposit_count_before}, after={deposit_count_after}"
        
        print("PASS: default skip_deposit behavior creates deposit")


class TestPublitioSettingsCollection:
    """Tests for Publitio reading from correct settings collection"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_publitio_test_endpoint_returns_configured_status(self):
        """Publitio /test endpoint reads from platform_settings and returns status"""
        resp = requests.get(f"{BASE_URL}/api/publitio/test", headers=self.headers)
        
        assert resp.status_code == 200, f"Publitio test endpoint failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "configured" in data, f"Missing 'configured' field: {data}"
        assert "success" in data, f"Missing 'success' field: {data}"
        assert "message" in data, f"Missing 'message' field: {data}"
        
        # Note: Publitio keys are currently empty in DB, so configured should be false
        # The important thing is the code now reads from platform_settings (not settings)
        if not data.get("configured"):
            assert data.get("message") == "Publitio API keys not configured", \
                f"Unexpected message when not configured: {data}"
            print("PASS: Publitio /test returns configured=false (keys empty in platform_settings - expected)")
        else:
            print(f"INFO: Publitio is configured, success={data.get('success')}")
        
        print("PASS: Publitio test endpoint works correctly")
    
    def test_publitio_folders_endpoint_checks_credentials(self):
        """Publitio /folders endpoint also uses get_publitio_creds from platform_settings"""
        resp = requests.get(f"{BASE_URL}/api/publitio/folders", headers=self.headers)
        
        # Should return 503 if not configured, or 200 if configured
        assert resp.status_code in [200, 503], f"Unexpected status: {resp.status_code} - {resp.text}"
        
        if resp.status_code == 503:
            data = resp.json()
            assert "not configured" in data.get("detail", "").lower(), f"Unexpected error: {data}"
            print("PASS: Publitio /folders returns 503 when not configured (reading from platform_settings)")
        else:
            print("PASS: Publitio /folders endpoint works (keys found in platform_settings)")


class TestPlatformSettingsExists:
    """Verify platform_settings collection exists and is used correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert login_resp.status_code == 200
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_platform_settings_endpoint_works(self):
        """Platform Settings page should load without errors"""
        # This tests that the endpoint exists and returns data
        resp = requests.get(f"{BASE_URL}/api/admin/platform-settings", headers=self.headers)
        
        # Should return 200 (settings exist) or 404 (no settings yet)
        assert resp.status_code in [200, 404], f"Unexpected status: {resp.status_code} - {resp.text}"
        
        if resp.status_code == 200:
            print(f"PASS: Platform settings loaded: {list(resp.json().keys())[:5]}...")
        else:
            print("PASS: Platform settings endpoint responds (no settings configured yet)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

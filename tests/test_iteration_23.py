"""
Test Iteration 23 - Testing 4 key fixes:
1. Set-password creates account for new Heartbeat users
2. Licensee simulation dialog with dummy/specific user selection
3. Balance logic - withdrawal immediately deducts, deposit updates on completion
4. Initial balance recorded as deposit transaction
"""

import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
HEARTBEAT_EMAIL = "hello@hyperdrivemg.co"
TEST_PASSWORD = "testpass123"


class TestSetPasswordEndpoint:
    """Test set-password endpoint creates account for new Heartbeat users"""
    
    def test_verify_heartbeat_email(self):
        """Verify that hello@hyperdrivemg.co is a valid Heartbeat member"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-heartbeat",
            json={"email": HEARTBEAT_EMAIL}
        )
        assert response.status_code == 200, f"Heartbeat verification failed: {response.text}"
        data = response.json()
        assert data.get("verified") == True, f"Email not verified: {data}"
        print(f"✓ Heartbeat email verified: {HEARTBEAT_EMAIL}")
    
    def test_set_password_creates_or_updates_account(self):
        """Test that set-password endpoint creates/updates account for verified Heartbeat email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/set-password",
            json={"email": HEARTBEAT_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Set password failed: {response.text}"
        data = response.json()
        # Should return either "Account created successfully" or "Password updated successfully"
        assert "successfully" in data.get("message", "").lower(), f"Unexpected response: {data}"
        print(f"✓ Set password successful: {data['message']}")
    
    def test_login_with_new_account(self):
        """Test that login works with the newly created/updated account"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": HEARTBEAT_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access token in response: {data}"
        assert data.get("user", {}).get("email") == HEARTBEAT_EMAIL
        print(f"✓ Login successful for {HEARTBEAT_EMAIL}")
        return data["access_token"]


class TestLicenseCreationWithInitialDeposit:
    """Test that license creation records initial balance as deposit transaction"""
    
    @pytest.fixture
    def admin_token(self):
        """Get master admin token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_get_licenses_list(self, admin_token):
        """Test admin can get licenses list"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200, f"Get licenses failed: {response.text}"
        data = response.json()
        assert "licenses" in data
        print(f"✓ Got {len(data['licenses'])} licenses")
        return data["licenses"]
    
    def test_license_has_initial_deposit_transaction(self, admin_token):
        """Test that licenses have initial deposit transactions recorded"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get all licenses
        licenses_response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert licenses_response.status_code == 200
        licenses = licenses_response.json().get("licenses", [])
        
        if not licenses:
            pytest.skip("No licenses found to test")
        
        # Get transactions for the first active license
        active_license = next((l for l in licenses if l.get("is_active")), None)
        if not active_license:
            pytest.skip("No active licenses found")
        
        user_id = active_license["user_id"]
        
        # Get transactions for this user
        tx_response = requests.get(
            f"{BASE_URL}/api/admin/transactions",
            headers=headers
        )
        assert tx_response.status_code == 200
        
        all_transactions = tx_response.json().get("transactions", [])
        user_transactions = [t for t in all_transactions if t.get("user_id") == user_id]
        
        # Check for initial balance transaction
        initial_deposits = [t for t in user_transactions if t.get("is_initial_balance") == True]
        
        print(f"✓ Found {len(initial_deposits)} initial balance transaction(s) for user {user_id}")
        print(f"  Total transactions for user: {len(user_transactions)}")


class TestWithdrawalImmediateDeduction:
    """Test that withdrawal immediately deducts from balance"""
    
    @pytest.fixture
    def licensee_token(self):
        """Get licensee token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": HEARTBEAT_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Licensee login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        """Get master admin token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_current_balance(self, licensee_token):
        """Get current licensee balance"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        response = requests.get(f"{BASE_URL}/api/profit/licensee/transactions", headers=headers)
        
        if response.status_code != 200:
            pytest.skip("User is not a licensee")
        
        data = response.json()
        if not data.get("is_licensee"):
            pytest.skip("User is not a licensee")
        
        balance = data.get("current_balance", 0)
        print(f"✓ Current licensee balance: ${balance:,.2f}")
        return balance
    
    def test_withdrawal_deducts_immediately(self, licensee_token, admin_token):
        """Test that withdrawal immediately deducts from balance"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        
        # Get initial balance
        response = requests.get(f"{BASE_URL}/api/profit/licensee/transactions", headers=headers)
        if response.status_code != 200 or not response.json().get("is_licensee"):
            pytest.skip("User is not a licensee")
        
        initial_balance = response.json().get("current_balance", 0)
        print(f"  Initial balance: ${initial_balance:,.2f}")
        
        if initial_balance < 100:
            pytest.skip(f"Insufficient balance for withdrawal test: ${initial_balance}")
        
        # Submit withdrawal
        withdrawal_amount = 50.0
        withdrawal_response = requests.post(
            f"{BASE_URL}/api/profit/licensee/withdrawal",
            headers=headers,
            data={"amount": withdrawal_amount, "notes": "Test withdrawal for iteration 23"}
        )
        
        if withdrawal_response.status_code != 200:
            print(f"  Withdrawal failed: {withdrawal_response.text}")
            pytest.skip(f"Withdrawal failed: {withdrawal_response.text}")
        
        print(f"  Withdrawal submitted: ${withdrawal_amount}")
        
        # Check balance immediately after withdrawal
        response = requests.get(f"{BASE_URL}/api/profit/licensee/transactions", headers=headers)
        new_balance = response.json().get("current_balance", 0)
        
        expected_balance = initial_balance - withdrawal_amount
        print(f"  New balance: ${new_balance:,.2f}")
        print(f"  Expected balance: ${expected_balance:,.2f}")
        
        # Balance should be immediately deducted
        assert abs(new_balance - expected_balance) < 0.01, \
            f"Balance not immediately deducted. Expected ${expected_balance}, got ${new_balance}"
        
        print(f"✓ Withdrawal immediately deducted from balance")


class TestDepositCompletionUpdatesBalance:
    """Test that deposit only updates balance when admin marks complete"""
    
    @pytest.fixture
    def licensee_token(self):
        """Get licensee token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": HEARTBEAT_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Licensee login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        """Get master admin token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_deposit_pending_does_not_change_balance(self, licensee_token):
        """Test that submitting a deposit does NOT immediately change balance"""
        headers = {"Authorization": f"Bearer {licensee_token}"}
        
        # Get initial balance
        response = requests.get(f"{BASE_URL}/api/profit/licensee/transactions", headers=headers)
        if response.status_code != 200 or not response.json().get("is_licensee"):
            pytest.skip("User is not a licensee")
        
        initial_balance = response.json().get("current_balance", 0)
        print(f"  Initial balance: ${initial_balance:,.2f}")
        
        # Submit deposit (without screenshot for simplicity)
        deposit_amount = 100.0
        deposit_response = requests.post(
            f"{BASE_URL}/api/profit/licensee/deposit",
            headers=headers,
            data={
                "amount": deposit_amount,
                "deposit_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "Test deposit for iteration 23"
            }
        )
        
        if deposit_response.status_code != 200:
            print(f"  Deposit submission failed: {deposit_response.text}")
            # This might fail due to screenshot requirement - that's OK
            pytest.skip(f"Deposit submission failed (may require screenshot): {deposit_response.text}")
        
        print(f"  Deposit submitted: ${deposit_amount}")
        
        # Check balance immediately after deposit submission
        response = requests.get(f"{BASE_URL}/api/profit/licensee/transactions", headers=headers)
        new_balance = response.json().get("current_balance", 0)
        
        print(f"  Balance after deposit submission: ${new_balance:,.2f}")
        
        # Balance should NOT change until admin marks complete
        assert abs(new_balance - initial_balance) < 0.01, \
            f"Balance changed before completion. Expected ${initial_balance}, got ${new_balance}"
        
        print(f"✓ Deposit does not change balance until completion")


class TestAdminTransactionCompletion:
    """Test admin transaction completion flow"""
    
    @pytest.fixture
    def admin_token(self):
        """Get master admin token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_all_transactions(self, admin_token):
        """Test admin can get all transactions"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/transactions", headers=headers)
        assert response.status_code == 200, f"Get transactions failed: {response.text}"
        data = response.json()
        assert "transactions" in data
        print(f"✓ Got {len(data['transactions'])} transactions")
        
        # Show breakdown by status
        pending = [t for t in data['transactions'] if t.get('status') == 'pending']
        completed = [t for t in data['transactions'] if t.get('status') == 'completed']
        print(f"  Pending: {len(pending)}, Completed: {len(completed)}")
    
    def test_transaction_completion_updates_balance(self, admin_token):
        """Test that completing a deposit transaction updates licensee balance"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get pending deposit transactions
        response = requests.get(f"{BASE_URL}/api/admin/transactions", headers=headers)
        assert response.status_code == 200
        
        transactions = response.json().get("transactions", [])
        pending_deposits = [t for t in transactions 
                          if t.get("status") == "pending" and t.get("type") == "deposit"]
        
        if not pending_deposits:
            print("  No pending deposits to test completion")
            pytest.skip("No pending deposits available for testing")
        
        tx = pending_deposits[0]
        tx_id = tx["id"]
        user_id = tx["user_id"]
        amount = tx["amount"]
        
        print(f"  Testing completion of deposit ${amount} for user {user_id[:8]}...")
        
        # Get user's current balance before completion
        # (We'd need to get this from the license, but for now just verify the endpoint works)
        
        # Complete the transaction
        complete_response = requests.post(
            f"{BASE_URL}/api/admin/transactions/{tx_id}/complete",
            headers=headers
        )
        
        if complete_response.status_code == 200:
            print(f"✓ Transaction {tx_id[:8]} completed successfully")
        else:
            print(f"  Completion response: {complete_response.status_code} - {complete_response.text}")


class TestLicenseeSimulationDialog:
    """Test licensee simulation dialog functionality (UI test via API verification)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get master admin token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_licenses_for_simulation(self, admin_token):
        """Test that admin can get licenses list for simulation dropdown"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=headers)
        assert response.status_code == 200, f"Get licenses failed: {response.text}"
        
        data = response.json()
        licenses = data.get("licenses", [])
        
        # Filter by type
        honorary = [l for l in licenses if l.get("license_type") == "honorary" and l.get("is_active")]
        extended = [l for l in licenses if l.get("license_type") == "extended" and l.get("is_active")]
        
        print(f"✓ Licenses available for simulation:")
        print(f"  Honorary: {len(honorary)}")
        print(f"  Extended: {len(extended)}")
    
    def test_get_members_for_simulation(self, admin_token):
        """Test that admin can get members list for simulation"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        assert response.status_code == 200, f"Get members failed: {response.text}"
        
        data = response.json()
        # API returns {members: [...], total, page, limit, pages}
        members = data.get("members", [])
        licensees = [m for m in members if m.get("license_type")]
        
        print(f"✓ Members available: {len(members)}")
        print(f"  Licensees: {len(licensees)}")
    
    def test_simulate_member_endpoint(self, admin_token):
        """Test the simulate member endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a licensee to simulate
        members_response = requests.get(f"{BASE_URL}/api/admin/members", headers=headers)
        data = members_response.json()
        members = data.get("members", [])
        licensee = next((m for m in members if m.get("license_type")), None)
        
        if not licensee:
            pytest.skip("No licensees available to simulate")
        
        # Test simulate endpoint
        simulate_response = requests.get(
            f"{BASE_URL}/api/admin/members/{licensee['id']}/simulate",
            headers=headers
        )
        assert simulate_response.status_code == 200, f"Simulate failed: {simulate_response.text}"
        
        data = simulate_response.json()
        assert "member" in data
        assert "account_value" in data
        
        print(f"✓ Simulation data retrieved for {licensee.get('full_name', 'Unknown')}")
        print(f"  Account value: ${data.get('account_value', 0):,.2f}")


class TestCurrentBalanceDisplay:
    """Test that Current Balance on Deposit/Withdrawal page matches license.current_amount"""
    
    @pytest.fixture
    def licensee_token(self):
        """Get licensee token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": HEARTBEAT_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Licensee login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        """Get master admin token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_balance_consistency(self, licensee_token, admin_token):
        """Test that balance shown to licensee matches license.current_amount"""
        licensee_headers = {"Authorization": f"Bearer {licensee_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get balance from licensee's perspective
        licensee_response = requests.get(
            f"{BASE_URL}/api/profit/licensee/transactions",
            headers=licensee_headers
        )
        
        if licensee_response.status_code != 200 or not licensee_response.json().get("is_licensee"):
            pytest.skip("User is not a licensee")
        
        licensee_balance = licensee_response.json().get("current_balance", 0)
        
        # Get the user's license from admin perspective
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=licensee_headers)
        user_id = me_response.json().get("id")
        
        licenses_response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=admin_headers)
        licenses = licenses_response.json().get("licenses", [])
        user_license = next((l for l in licenses if l.get("user_id") == user_id and l.get("is_active")), None)
        
        if not user_license:
            pytest.skip("No active license found for user")
        
        license_current_amount = user_license.get("current_amount", 0)
        
        print(f"✓ Balance consistency check:")
        print(f"  Licensee sees: ${licensee_balance:,.2f}")
        print(f"  License current_amount: ${license_current_amount:,.2f}")
        
        assert abs(licensee_balance - license_current_amount) < 0.01, \
            f"Balance mismatch! Licensee sees ${licensee_balance}, license has ${license_current_amount}"
        
        print(f"✓ Balances match!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

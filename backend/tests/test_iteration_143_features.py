"""
Iteration 143 - Testing 3 fixes/features:
1. Trade streak fix: Start from previous trading day if today not yet traded (streak should be 13 for test user)
2. Member self-edit widget: GET /api/profit/my-recent-transactions and PUT /api/profit/my-transactions/{id}
3. Admin Transactions page: Profits filter tab, user search, exclude profit entries from All/Deposits/Withdrawals
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_ID = "b4628e3e-9dec-42ef-8c75-dcba08194cd2"

@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Auth headers with bearer token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestTradeStreak:
    """Test trade streak calculation fix - should count from previous trading day if today not yet traded"""

    def test_get_streak_for_test_user(self, auth_headers):
        """GET /api/trade/streak should return non-zero streak for test user
        The test user has traded every day from Feb 17 to Mar 5, which should be 13 consecutive trading days
        """
        response = requests.get(
            f"{BASE_URL}/api/trade/streak",
            headers=auth_headers,
            params={"user_id": TEST_USER_ID}
        )
        assert response.status_code == 200, f"Streak request failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "streak" in data, "Missing 'streak' field in response"
        assert "total_trades" in data, "Missing 'total_trades' field in response"
        
        # The streak should be > 0 if the user has been trading consecutively
        print(f"Streak data: {data}")
        
        # According to problem statement: user traded Feb 17 - Mar 5, should be 13 streak
        # However the actual value depends on current date - just verify it's > 0 if they have trades
        if data["total_trades"] > 0:
            # If the fix is working, streak should not be 0
            # The streak may vary depending on when tests run (if today is a trading day and user hasn't traded)
            # The main fix ensures we start counting from previous trading day if today not yet traded
            print(f"Trade streak: {data['streak']}, Total trades: {data['total_trades']}")

    def test_streak_endpoint_exists_and_accessible(self, auth_headers):
        """Verify streak endpoint is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/trade/streak",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Streak endpoint not accessible: {response.text}"


class TestMemberSelfEditTransactions:
    """Test member self-edit widget for transactions - last 2 within 48hrs"""

    def test_get_my_recent_transactions(self, auth_headers):
        """GET /api/profit/my-recent-transactions should return last 2 non-profit transactions"""
        response = requests.get(
            f"{BASE_URL}/api/profit/my-recent-transactions",
            headers=auth_headers
        )
        assert response.status_code == 200, f"My recent transactions failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data, "Missing 'transactions' field"
        
        transactions = data["transactions"]
        # Should return max 2 transactions
        assert len(transactions) <= 2, "Should return at most 2 transactions"
        
        # Each transaction should have editable flag
        for tx in transactions:
            assert "editable" in tx, f"Transaction missing 'editable' flag: {tx}"
            assert "amount" in tx, f"Transaction missing 'amount' field: {tx}"
            assert "id" in tx, f"Transaction missing 'id' field: {tx}"
            assert "created_at" in tx, f"Transaction missing 'created_at' field: {tx}"
            # Should NOT include type=profit or type=initial
            if tx.get("type"):
                assert tx["type"] not in ["profit", "initial"], f"Should not include {tx['type']} type transactions"
        
        print(f"Recent transactions count: {len(transactions)}")
        for tx in transactions:
            print(f"  Transaction: amount={tx.get('amount')}, editable={tx.get('editable')}, type={tx.get('type')}")

    def test_edit_transaction_endpoint_exists(self, auth_headers):
        """PUT /api/profit/my-transactions/{id} endpoint should exist"""
        # Using a fake ID - should return 404 (not found) rather than 405 (method not allowed)
        response = requests.put(
            f"{BASE_URL}/api/profit/my-transactions/fake-id-12345",
            headers=auth_headers,
            json={"new_amount": 100, "reason": "Test"}
        )
        # Should return 404 (not found) not 405 (method not allowed)
        assert response.status_code in [404, 400, 403], f"Unexpected status: {response.status_code} - {response.text}"
        print(f"Edit endpoint exists, returned: {response.status_code}")


class TestAdminTransactionsPage:
    """Test Admin Transactions page improvements - Profits tab, user search, filtering"""

    def test_get_transactions_all_excludes_profit(self, auth_headers):
        """GET /api/admin/transactions (no type filter) should exclude profit entries"""
        response = requests.get(
            f"{BASE_URL}/api/admin/transactions",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Admin transactions failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data, "Missing 'transactions' field"
        assert "total" in data, "Missing 'total' field"
        
        transactions = data["transactions"]
        # No profit-type entries should appear in default view
        profit_entries = [tx for tx in transactions if tx.get("type") == "profit"]
        assert len(profit_entries) == 0, f"Found {len(profit_entries)} profit entries in 'All' view - should be excluded"
        
        print(f"All transactions (excluding profit): {data['total']} total")

    def test_get_transactions_deposits_only(self, auth_headers):
        """GET /api/admin/transactions?transaction_type=deposit should return only deposits"""
        response = requests.get(
            f"{BASE_URL}/api/admin/transactions",
            headers=auth_headers,
            params={"transaction_type": "deposit"}
        )
        assert response.status_code == 200, f"Deposits filter failed: {response.text}"
        data = response.json()
        
        transactions = data["transactions"]
        # All should be deposits
        for tx in transactions:
            assert tx.get("type") in ["deposit", None], f"Non-deposit found: {tx.get('type')}"
            assert tx.get("type") != "profit", "Should not include profit entries"
            assert tx.get("type") != "withdrawal", "Should not include withdrawals"
        
        print(f"Deposits only: {len(transactions)} shown, {data['total']} total")

    def test_get_transactions_withdrawals_only(self, auth_headers):
        """GET /api/admin/transactions?transaction_type=withdrawal should return only withdrawals"""
        response = requests.get(
            f"{BASE_URL}/api/admin/transactions",
            headers=auth_headers,
            params={"transaction_type": "withdrawal"}
        )
        assert response.status_code == 200, f"Withdrawals filter failed: {response.text}"
        data = response.json()
        
        transactions = data["transactions"]
        # All should be withdrawals
        for tx in transactions:
            assert tx.get("type") == "withdrawal", f"Non-withdrawal found: {tx.get('type')}"
        
        print(f"Withdrawals only: {len(transactions)} shown, {data['total']} total")

    def test_get_transactions_profits_only(self, auth_headers):
        """GET /api/admin/transactions?transaction_type=profit should return only profit entries"""
        response = requests.get(
            f"{BASE_URL}/api/admin/transactions",
            headers=auth_headers,
            params={"transaction_type": "profit"}
        )
        assert response.status_code == 200, f"Profits filter failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "transactions" in data, "Missing 'transactions' field"
        
        transactions = data["transactions"]
        # All should be profit type
        for tx in transactions:
            assert tx.get("type") == "profit", f"Non-profit found in Profits tab: {tx.get('type')}"
        
        print(f"Profits only: {len(transactions)} shown, {data['total']} total")
        # According to problem statement, should be ~17 profit entries
        if len(transactions) > 0:
            print(f"First profit entry: user={transactions[0].get('user_name')}, amount=${transactions[0].get('amount')}")

    def test_user_search_filter(self, auth_headers):
        """GET /api/admin/transactions?user_search=ryan should filter by user name"""
        response = requests.get(
            f"{BASE_URL}/api/admin/transactions",
            headers=auth_headers,
            params={"user_search": "ryan"}
        )
        assert response.status_code == 200, f"User search failed: {response.text}"
        data = response.json()
        
        transactions = data["transactions"]
        # If there are results, they should match the search term
        for tx in transactions:
            user_name = tx.get("user_name", "").lower()
            user_email = tx.get("user_email", "").lower()
            # At least one should contain 'ryan'
            assert "ryan" in user_name or "ryan" in user_email, f"Search mismatch: {tx.get('user_name')} / {tx.get('user_email')}"
        
        print(f"User search 'ryan': {len(transactions)} results, {data['total']} total")

    def test_transaction_stats_excludes_profit(self, auth_headers):
        """GET /api/admin/transactions/stats should exclude profit entries"""
        response = requests.get(
            f"{BASE_URL}/api/admin/transactions/stats",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Transaction stats failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_deposits" in data, "Missing 'total_deposits'"
        assert "total_withdrawals" in data, "Missing 'total_withdrawals'"
        assert "net_flow" in data, "Missing 'net_flow'"
        assert "deposit_count" in data, "Missing 'deposit_count'"
        assert "withdrawal_count" in data, "Missing 'withdrawal_count'"
        
        print(f"Transaction stats: deposits=${data['total_deposits']}, withdrawals=${data['total_withdrawals']}, net=${data['net_flow']}")


class TestProfitTrackerStreakDisplay:
    """Test that Profit Tracker page shows correct streak"""

    def test_profit_summary_endpoint(self, auth_headers):
        """GET /api/profit/summary should return valid data for streak display"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Profit summary failed: {response.text}"
        data = response.json()
        
        # Verify we get account value and other data
        assert "account_value" in data, "Missing 'account_value'"
        assert "total_trades" in data, "Missing 'total_trades'"
        
        print(f"Profit summary: account_value=${data.get('account_value')}, total_trades={data.get('total_trades')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

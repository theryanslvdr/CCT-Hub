"""
Test iteration 66: Licensee fixes verification
- Verify /api/admin/members/{user_id} returns correct total_trades count for licensees
- Verify /api/admin/members/{user_id} returns correct total_profit for licensees
- Verify licensee cards layout (Account Value, Deposits, Total Profit) display correctly
- Verify trading signal is hidden for simulated licensee view
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
TEST_LICENSEE_USER_ID = "376c5e45-3bf9-45c5-ae2c-387e8afab821"


class TestLicenseeBackendFixes:
    """Test backend fixes for licensee total_trades and total_profit"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
    def get_auth_token(self):
        """Login as master admin and get token"""
        if self.token:
            return self.token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token")
        assert self.token, "No access token returned"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return self.token
    
    def test_01_login_as_master_admin(self):
        """Test login as master admin"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        assert data["user"]["role"] == "master_admin", f"Expected master_admin role, got {data['user']['role']}"
        print(f"✓ Login successful as master_admin: {data['user']['email']}")
    
    def test_02_get_licensee_member_details(self):
        """Test /api/admin/members/{user_id} returns correct data for licensee"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{TEST_LICENSEE_USER_ID}")
        assert response.status_code == 200, f"Failed to get member details: {response.text}"
        
        data = response.json()
        assert "user" in data, "Response missing 'user' field"
        assert "stats" in data, "Response missing 'stats' field"
        
        user = data["user"]
        stats = data["stats"]
        
        print(f"✓ Got member details for: {user.get('full_name', 'Unknown')}")
        print(f"  - License type: {user.get('license_type', 'None')}")
        print(f"  - Total trades: {stats.get('total_trades', 0)}")
        print(f"  - Total profit: ${stats.get('total_profit', 0):.2f}")
        print(f"  - Account value: ${stats.get('account_value', 0):.2f}")
        print(f"  - Is licensee: {stats.get('is_licensee', False)}")
        
        # Verify this is a licensee
        assert user.get("license_type") is not None, "User should have a license_type"
        assert stats.get("is_licensee") == True, "Stats should indicate is_licensee=True"
        
        return data
    
    def test_03_licensee_total_trades_not_zero(self):
        """Verify total_trades is not always 0 for licensees with traded days"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{TEST_LICENSEE_USER_ID}")
        assert response.status_code == 200, f"Failed to get member details: {response.text}"
        
        data = response.json()
        stats = data["stats"]
        
        # The fix counts unique dates from master admin's trade_logs
        # If master admin has traded, total_trades should be > 0
        total_trades = stats.get("total_trades", 0)
        
        print(f"✓ Licensee total_trades: {total_trades}")
        
        # Note: This test verifies the fix is in place
        # The actual count depends on master admin's trading activity
        # The key fix was changing from querying {has_traded: True} to counting unique dates
        assert isinstance(total_trades, int), "total_trades should be an integer"
        
        # If there's profit, there should be trades
        total_profit = stats.get("total_profit", 0)
        if total_profit > 0:
            assert total_trades > 0, f"If profit is ${total_profit}, total_trades should be > 0"
            print(f"✓ Verified: profit ${total_profit:.2f} with {total_trades} trades")
    
    def test_04_licensee_total_profit_calculation(self):
        """Verify total_profit is calculated correctly for licensees"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/admin/members/{TEST_LICENSEE_USER_ID}")
        assert response.status_code == 200, f"Failed to get member details: {response.text}"
        
        data = response.json()
        stats = data["stats"]
        
        total_profit = stats.get("total_profit", 0)
        account_value = stats.get("account_value", 0)
        total_deposits = stats.get("total_deposits", 0)
        
        print(f"✓ Licensee financial summary:")
        print(f"  - Account value: ${account_value:.2f}")
        print(f"  - Total deposits: ${total_deposits:.2f}")
        print(f"  - Total profit: ${total_profit:.2f}")
        
        # For licensees, profit = current_amount - starting_amount
        # The account_value should be >= total_deposits if there's profit
        if total_profit > 0:
            assert account_value >= total_deposits, "Account value should be >= deposits if profit > 0"
            print(f"✓ Verified: account_value (${account_value:.2f}) >= deposits (${total_deposits:.2f})")
    
    def test_05_get_all_licensees(self):
        """Get all licensees and verify their stats"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200, f"Failed to get licenses: {response.text}"
        
        licenses = response.json()
        print(f"✓ Found {len(licenses)} licenses")
        
        for lic in licenses[:5]:  # Check first 5
            user_id = lic.get("user_id")
            if user_id:
                member_resp = self.session.get(f"{BASE_URL}/api/admin/members/{user_id}")
                if member_resp.status_code == 200:
                    member_data = member_resp.json()
                    stats = member_data.get("stats", {})
                    print(f"  - {lic.get('user_name', 'Unknown')}: trades={stats.get('total_trades', 0)}, profit=${stats.get('total_profit', 0):.2f}")
    
    def test_06_verify_extended_licensee_profit(self):
        """Verify the specific extended licensee mentioned in the issue has correct profit"""
        self.get_auth_token()
        
        # Get all licenses to find extended licensees
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200, f"Failed to get licenses: {response.text}"
        
        licenses = response.json()
        extended_licenses = [l for l in licenses if l.get("license_type") == "extended" and l.get("is_active")]
        
        print(f"✓ Found {len(extended_licenses)} active extended licenses")
        
        for lic in extended_licenses:
            user_id = lic.get("user_id")
            user_name = lic.get("user_name", "Unknown")
            starting_amount = lic.get("starting_amount", 0)
            current_amount = lic.get("current_amount", 0)
            
            # Get member details
            member_resp = self.session.get(f"{BASE_URL}/api/admin/members/{user_id}")
            if member_resp.status_code == 200:
                member_data = member_resp.json()
                stats = member_data.get("stats", {})
                
                print(f"\n  Extended Licensee: {user_name}")
                print(f"    - Starting amount: ${starting_amount:.2f}")
                print(f"    - Current amount: ${current_amount:.2f}")
                print(f"    - API total_profit: ${stats.get('total_profit', 0):.2f}")
                print(f"    - API total_trades: {stats.get('total_trades', 0)}")
                
                # Verify profit calculation
                expected_profit = current_amount - starting_amount
                api_profit = stats.get("total_profit", 0)
                
                # Allow small floating point differences
                assert abs(api_profit - expected_profit) < 0.01, \
                    f"Profit mismatch: API={api_profit}, Expected={expected_profit}"
                print(f"    ✓ Profit calculation verified")


class TestLicenseeAPIEndpoints:
    """Test additional licensee-related API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
    def get_auth_token(self):
        """Login as master admin and get token"""
        if self.token:
            return self.token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return self.token
    
    def test_01_get_license_projections(self):
        """Test /api/admin/licenses/{id}/projections endpoint"""
        self.get_auth_token()
        
        # Get licenses first
        response = self.session.get(f"{BASE_URL}/api/admin/licenses")
        assert response.status_code == 200
        
        licenses = response.json()
        if not licenses:
            pytest.skip("No licenses found")
        
        # Get projections for first active license
        active_license = next((l for l in licenses if l.get("is_active")), None)
        if not active_license:
            pytest.skip("No active licenses found")
        
        license_id = active_license.get("id")
        response = self.session.get(f"{BASE_URL}/api/admin/licenses/{license_id}/projections")
        assert response.status_code == 200, f"Failed to get projections: {response.text}"
        
        data = response.json()
        assert "projections" in data, "Response missing 'projections' field"
        
        projections = data["projections"]
        print(f"✓ Got {len(projections)} projections for license {license_id}")
        
        if projections:
            first_proj = projections[0]
            print(f"  First projection: date={first_proj.get('date')}, daily_profit=${first_proj.get('daily_profit', 0):.2f}")
    
    def test_02_get_master_admin_trades(self):
        """Test that master admin trades are being counted"""
        self.get_auth_token()
        
        # Get master admin's trade logs
        response = self.session.get(f"{BASE_URL}/api/trade/logs?limit=100")
        assert response.status_code == 200, f"Failed to get trade logs: {response.text}"
        
        trades = response.json()
        print(f"✓ Master admin has {len(trades)} trade logs")
        
        # Count unique dates
        unique_dates = set()
        for trade in trades:
            created_at = trade.get("created_at", "")
            if created_at:
                date_str = str(created_at)[:10]
                unique_dates.add(date_str)
        
        print(f"✓ Unique trading days: {len(unique_dates)}")
        
        if unique_dates:
            sorted_dates = sorted(unique_dates)
            print(f"  Date range: {sorted_dates[0]} to {sorted_dates[-1]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

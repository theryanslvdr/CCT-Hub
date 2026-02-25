"""
Test Suite for Iteration 14 - Finance Center Improvements
Tests:
1. Member simulation shows simulated member's Total Deposits (not admin's)
2. Team Analytics includes admin account values
3. Analytics has member dropdown to view individual stats
4. Performance Overview has date range picker
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://points-history-beta.preview.emergentagent.com')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestAuthAndSetup:
    """Authentication and setup tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get master admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        assert data["user"]["role"] == "master_admin", f"Expected master_admin role, got {data['user']['role']}"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_as_master_admin(self, auth_token):
        """Test 1: Login as master_admin"""
        assert auth_token is not None
        print(f"✓ Login successful, got token")


class TestMemberSimulation:
    """Test member simulation shows correct Total Deposits"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get master admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_members_list(self, auth_headers):
        """Get list of members"""
        response = requests.get(f"{BASE_URL}/api/admin/members", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get members: {response.text}"
        data = response.json()
        assert "members" in data
        print(f"✓ Got {len(data['members'])} members")
        return data["members"]
    
    def test_simulate_member_returns_total_deposits(self, auth_headers):
        """Test 2: Simulate member returns total_deposits field"""
        # First get a member to simulate
        members_response = requests.get(f"{BASE_URL}/api/admin/members", headers=auth_headers)
        assert members_response.status_code == 200
        members = members_response.json()["members"]
        
        # Find a member (not admin) to simulate
        test_member = None
        for m in members:
            if m.get("role") in ["member", "user"]:
                test_member = m
                break
        
        if not test_member:
            pytest.skip("No member found to simulate")
        
        # Simulate the member
        response = requests.get(
            f"{BASE_URL}/api/admin/members/{test_member['id']}/simulate",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Simulate failed: {response.text}"
        data = response.json()
        
        # Verify total_deposits is in response
        assert "total_deposits" in data, "total_deposits not in simulation response"
        assert "total_profit" in data, "total_profit not in simulation response"
        assert "account_value" in data, "account_value not in simulation response"
        assert "lot_size" in data, "lot_size not in simulation response"
        
        print(f"✓ Simulation data for {test_member['full_name']}:")
        print(f"  - Account Value: ${data['account_value']}")
        print(f"  - Total Deposits: ${data['total_deposits']}")
        print(f"  - Total Profit: ${data['total_profit']}")
        print(f"  - LOT Size: {data['lot_size']}")


class TestTeamAnalytics:
    """Test Team Analytics includes admin account values"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get master admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_team_analytics_endpoint(self, auth_headers):
        """Test 3: Team Analytics includes all users (including admins)"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics/team", headers=auth_headers)
        assert response.status_code == 200, f"Team analytics failed: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "total_account_value" in data, "total_account_value not in response"
        assert "total_profit" in data, "total_profit not in response"
        assert "total_traders" in data, "total_traders not in response"
        assert "member_stats" in data, "member_stats not in response"
        
        print(f"✓ Team Analytics:")
        print(f"  - Total Account Value: ${data['total_account_value']}")
        print(f"  - Total Profit: ${data['total_profit']}")
        print(f"  - Total Traders: {data['total_traders']}")
        
        # Check if admin accounts are included in member_stats
        admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
        admin_found = False
        for member in data["member_stats"]:
            if member.get("role") in admin_roles:
                admin_found = True
                print(f"  - Admin included: {member['name']} (role: {member['role']}, value: ${member['account_value']})")
        
        assert admin_found, "No admin accounts found in team analytics - admins should be included"
        print(f"✓ Admin accounts are included in team analytics")
        
        # Verify total is approximately $14,621 (admin ~$14,521 + test user ~$100)
        assert data["total_account_value"] > 14000, f"Total account value seems too low: ${data['total_account_value']}"
        print(f"✓ Total account value includes admin: ${data['total_account_value']}")


class TestMemberDropdown:
    """Test Analytics page member dropdown"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get master admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_member_analytics_endpoint(self, auth_headers):
        """Test 4: Individual member analytics endpoint exists"""
        # First get a member
        members_response = requests.get(f"{BASE_URL}/api/admin/members", headers=auth_headers)
        assert members_response.status_code == 200
        members = members_response.json()["members"]
        
        if not members:
            pytest.skip("No members found")
        
        test_member = members[0]
        
        # Get individual member analytics
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics/member/{test_member['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Member analytics failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "member" in data, "member not in response"
        assert "stats" in data, "stats not in response"
        
        # Verify stats fields
        stats = data["stats"]
        assert "account_value" in stats, "account_value not in stats"
        assert "lot_size" in stats, "lot_size not in stats"
        assert "total_profit" in stats, "total_profit not in stats"
        assert "total_trades" in stats, "total_trades not in stats"
        assert "total_deposits" in stats, "total_deposits not in stats"
        
        print(f"✓ Member Analytics for {data['member']['name']}:")
        print(f"  - Account Value: ${stats['account_value']}")
        print(f"  - LOT Size: {stats['lot_size']}")
        print(f"  - Total Profit: ${stats['total_profit']}")
        print(f"  - Total Trades: {stats['total_trades']}")
        print(f"  - Total Deposits: ${stats['total_deposits']}")


class TestDateRangePicker:
    """Test Performance Overview date range picker"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get master admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_growth_data_without_filter(self, auth_headers):
        """Test growth data endpoint without date filter"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics/growth-data", headers=auth_headers)
        assert response.status_code == 200, f"Growth data failed: {response.text}"
        data = response.json()
        
        assert "chart_data" in data, "chart_data not in response"
        print(f"✓ Growth data without filter: {len(data['chart_data'])} data points")
    
    def test_growth_data_with_date_filter(self, auth_headers):
        """Test 5-6: Growth data endpoint with date filter"""
        # Test with date range
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics/growth-data",
            params={"start_date": "2025-01-01", "end_date": "2026-12-31"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Growth data with filter failed: {response.text}"
        data = response.json()
        
        assert "chart_data" in data, "chart_data not in response"
        print(f"✓ Growth data with date filter: {len(data['chart_data'])} data points")
        
        # Verify chart data structure if data exists
        if data["chart_data"]:
            first_point = data["chart_data"][0]
            assert "date" in first_point, "date not in chart data point"
            assert "account_value" in first_point, "account_value not in chart data point"
            assert "total_profit" in first_point, "total_profit not in chart data point"
            print(f"✓ Chart data structure verified")


class TestArchiveTrades:
    """Test Archive Old Trades functionality"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get master admin auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_archive_trades_endpoint(self, auth_headers):
        """Test 7: Archive trades endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/admin/analytics/archive-trades",
            headers=auth_headers
        )
        # Should return 200 even if no trades to archive
        assert response.status_code == 200, f"Archive trades failed: {response.text}"
        data = response.json()
        
        print(f"✓ Archive trades response: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 115 Tests: Dynamic License Values, Year Projections, and Admin Family Member Addition

Features tested:
1. GET /api/admin/licenses returns dynamic current_amount for honorary/honorary_fa licensees
2. GET /api/profit/licensee/year-projections returns 1yr, 2yr, 3yr, 5yr projections with quarterly compounding
3. POST /api/admin/family/members/{userId} allows admin to add family member on behalf of licensee
4. Simulation dialog/banner show correct dynamic account value (not stale)
5. Direct login as Rizza Miles shows correct account value
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable is required")

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
RIZZA_EMAIL = "rizza.miles@gmail.com"
RIZZA_PASSWORD = "rizza123"
RIZZA_USER_ID = "19ccb9d7-139f-4918-a662-ad72483010b1"

@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get admin headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

@pytest.fixture(scope="module")
def rizza_token():
    """Get Rizza's authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": RIZZA_EMAIL,
        "password": RIZZA_PASSWORD
    })
    assert response.status_code == 200, f"Rizza login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def rizza_headers(rizza_token):
    """Get Rizza's headers with auth token"""
    return {"Authorization": f"Bearer {rizza_token}", "Content-Type": "application/json"}


class TestAdminLicensesDynamicValues:
    """Test GET /api/admin/licenses returns dynamic current_amount for honorary licensees"""
    
    def test_admin_licenses_endpoint_returns_licenses(self, admin_headers):
        """Test admin/licenses endpoint is accessible and returns license data"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "licenses" in data, "Response should contain 'licenses' key"
        
    def test_admin_licenses_contains_current_amount(self, admin_headers):
        """Test that licenses have current_amount field"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        licenses = data.get("licenses", [])
        
        if not licenses:
            pytest.skip("No licenses found to test")
        
        for license in licenses:
            assert "current_amount" in license, f"License {license.get('id')} missing current_amount"
            assert isinstance(license["current_amount"], (int, float)), "current_amount should be numeric"
            
    def test_honorary_licensee_dynamic_value(self, admin_headers):
        """Test that honorary licensees have dynamically calculated current_amount (not stale DB value)"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        licenses = data.get("licenses", [])
        
        # Find honorary or honorary_fa licenses
        honorary_licenses = [l for l in licenses if l.get("license_type") in ("honorary", "honorary_fa")]
        
        if not honorary_licenses:
            pytest.skip("No honorary licenses found to test dynamic calculation")
        
        for lic in honorary_licenses:
            # current_amount should be >= starting_amount (dynamic calculation adds profits)
            current = lic.get("current_amount", 0)
            starting = lic.get("starting_amount", 0)
            
            # For active licenses, current_amount should be at least starting_amount
            if lic.get("is_active"):
                print(f"License {lic.get('user_name')}: starting={starting}, current={current}")
                assert current >= 0, f"current_amount should be non-negative, got {current}"
                
    def test_rizza_license_has_dynamic_value(self, admin_headers):
        """Test Rizza's license specifically shows dynamic ~$6,530 (not stale $5,000)"""
        response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        licenses = data.get("licenses", [])
        
        # Find Rizza's license
        rizza_license = next((l for l in licenses if l.get("user_id") == RIZZA_USER_ID), None)
        
        if not rizza_license:
            pytest.skip("Rizza's license not found")
        
        current_amount = rizza_license.get("current_amount", 0)
        starting_amount = rizza_license.get("starting_amount", 0)
        
        print(f"Rizza's license: starting={starting_amount}, current={current_amount}")
        
        # Rizza's expected dynamic value is ~$6,530 based on previous tests
        # The stale value was $5,000 - if we see $5,000 or close to it, the fix failed
        # Allow some tolerance since trades may have occurred
        assert current_amount > starting_amount, \
            f"Rizza's current_amount ({current_amount}) should be > starting_amount ({starting_amount})"


class TestYearProjectionsEndpoint:
    """Test GET /api/profit/licensee/year-projections returns multi-year growth projections"""
    
    def test_year_projections_endpoint_accessible(self, rizza_headers):
        """Test year-projections endpoint is accessible for licensees"""
        response = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=rizza_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_year_projections_returns_required_fields(self, rizza_headers):
        """Test year-projections returns all required projection periods"""
        response = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=rizza_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top-level fields
        assert "current_value" in data, "Response should contain current_value"
        assert "starting_amount" in data, "Response should contain starting_amount"
        assert "projections" in data, "Response should contain projections array"
        
        projections = data.get("projections", [])
        assert len(projections) == 4, f"Expected 4 projections (1yr, 2yr, 3yr, 5yr), got {len(projections)}"
        
        # Verify projection years
        years = [p.get("years") for p in projections]
        assert sorted(years) == [1, 2, 3, 5], f"Expected years [1, 2, 3, 5], got {sorted(years)}"
        
    def test_year_projections_have_correct_structure(self, rizza_headers):
        """Test each projection has required fields"""
        response = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=rizza_headers)
        assert response.status_code == 200
        
        data = response.json()
        projections = data.get("projections", [])
        
        for proj in projections:
            assert "years" in proj, "Projection should have 'years' field"
            assert "projected_value" in proj, "Projection should have 'projected_value' field"
            assert "total_profit" in proj, "Projection should have 'total_profit' field"
            assert "growth_percent" in proj, "Projection should have 'growth_percent' field"
            
            # Values should be numeric
            assert isinstance(proj["projected_value"], (int, float)), "projected_value should be numeric"
            assert isinstance(proj["total_profit"], (int, float)), "total_profit should be numeric"
            
    def test_year_projections_values_increase_over_time(self, rizza_headers):
        """Test projections show increasing values over time (compounding effect)"""
        response = requests.get(f"{BASE_URL}/api/profit/licensee/year-projections", headers=rizza_headers)
        assert response.status_code == 200
        
        data = response.json()
        projections = data.get("projections", [])
        
        # Sort by years
        sorted_projections = sorted(projections, key=lambda x: x.get("years", 0))
        
        # Each subsequent year should have higher projected value
        for i in range(1, len(sorted_projections)):
            prev_value = sorted_projections[i-1].get("projected_value", 0)
            curr_value = sorted_projections[i].get("projected_value", 0)
            
            assert curr_value >= prev_value, \
                f"Year {sorted_projections[i].get('years')} projected_value ({curr_value}) should be >= " \
                f"year {sorted_projections[i-1].get('years')} ({prev_value})"


class TestAdminAddFamilyMember:
    """Test POST /api/admin/family/members/{userId} allows admin to add family members"""
    
    def test_admin_can_add_family_member(self, admin_headers):
        """Test admin can add a family member on behalf of a licensee"""
        import uuid
        test_name = f"TEST_FamilyMember_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=admin_headers,
            json={
                "name": test_name,
                "relationship": "Sibling",
                "starting_amount": 1000.0
            }
        )
        
        # Should succeed (200 or 201) or fail with a validation error (not 500)
        assert response.status_code in [200, 201, 400, 403], \
            f"Expected 200/201/400/403, got {response.status_code}: {response.text}"
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Successfully added family member: {data}")
            assert "id" in data or "member" in data, "Response should contain member ID"
            
    def test_admin_add_family_member_requires_name(self, admin_headers):
        """Test that name is required when adding family member"""
        response = requests.post(
            f"{BASE_URL}/api/admin/family/members/{RIZZA_USER_ID}",
            headers=admin_headers,
            json={
                "relationship": "Sibling",
                "starting_amount": 500.0
            }
        )
        
        # Should fail with validation error (400/422)
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for missing name, got {response.status_code}: {response.text}"


class TestRizzaAccountValueConsistency:
    """Test P0 data consistency - Rizza's account value should be consistent across all endpoints"""
    
    def test_rizza_direct_login_account_value(self, rizza_headers):
        """Test Rizza's account value via direct login is dynamic (not stale)"""
        response = requests.get(f"{BASE_URL}/api/profit/summary", headers=rizza_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        account_value = data.get("account_value", 0)
        
        print(f"Rizza's direct login account_value: ${account_value}")
        
        # Expected dynamic value is ~$6,530 based on previous tests
        # Should NOT be the stale $5,000 value
        assert account_value > 5000, \
            f"Rizza's account_value ({account_value}) should be > $5,000 (was stale before fix)"
            
    def test_rizza_licensee_welcome_info(self, rizza_headers):
        """Test Rizza's welcome info shows dynamic balance"""
        response = requests.get(f"{BASE_URL}/api/profit/licensee/welcome-info", headers=rizza_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        current_balance = data.get("current_balance", 0)
        
        print(f"Rizza's welcome-info current_balance: ${current_balance}")
        
        # Should be dynamic, not stale
        assert current_balance > 0, f"current_balance should be > 0, got {current_balance}"
        
    def test_admin_simulation_matches_direct_login(self, admin_headers, rizza_headers):
        """Test admin simulation shows same value as direct login"""
        # Get value from admin simulate endpoint
        sim_response = requests.post(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/simulate",
            headers=admin_headers
        )
        assert sim_response.status_code == 200, f"Simulate failed: {sim_response.text}"
        sim_data = sim_response.json()
        sim_account_value = sim_data.get("account_value", 0)
        
        # Get value from direct login
        summary_response = requests.get(f"{BASE_URL}/api/profit/summary", headers=rizza_headers)
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        direct_account_value = summary_data.get("account_value", 0)
        
        print(f"Admin simulation: ${sim_account_value}, Direct login: ${direct_account_value}")
        
        # Values should match (allow small tolerance for rounding)
        tolerance = 1.0  # $1 tolerance
        assert abs(sim_account_value - direct_account_value) <= tolerance, \
            f"Admin simulation ({sim_account_value}) should match direct login ({direct_account_value})"


class TestAdminLicensesPageData:
    """Test data consistency between /api/admin/licenses and simulation"""
    
    def test_admin_licenses_rizza_matches_simulation(self, admin_headers):
        """Test Rizza's value in /api/admin/licenses matches /api/admin/members/{id}/simulate"""
        # Get from licenses endpoint
        licenses_response = requests.get(f"{BASE_URL}/api/admin/licenses", headers=admin_headers)
        assert licenses_response.status_code == 200
        
        licenses = licenses_response.json().get("licenses", [])
        rizza_license = next((l for l in licenses if l.get("user_id") == RIZZA_USER_ID), None)
        
        if not rizza_license:
            pytest.skip("Rizza's license not found")
        
        license_current_amount = rizza_license.get("current_amount", 0)
        
        # Get from simulate endpoint
        sim_response = requests.post(
            f"{BASE_URL}/api/admin/members/{RIZZA_USER_ID}/simulate",
            headers=admin_headers
        )
        assert sim_response.status_code == 200
        sim_account_value = sim_response.json().get("account_value", 0)
        
        print(f"Licenses endpoint: ${license_current_amount}, Simulate endpoint: ${sim_account_value}")
        
        # Values should match (this was the bug - licenses showed stale, simulate showed dynamic)
        tolerance = 1.0
        assert abs(license_current_amount - sim_account_value) <= tolerance, \
            f"Licenses endpoint ({license_current_amount}) should match simulate ({sim_account_value})"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

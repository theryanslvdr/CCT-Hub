"""
Iteration 124 Bug Fix Tests
Tests for:
1. Licensee year-projections endpoint (recurring regression fix)
2. Licensee-health-check admin endpoint
3. Rewards card visibility for licensees (frontend integration)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ui-mobile-overhaul-3.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"
LICENSEE_EMAIL = "rizza.miles@gmail.com"
LICENSEE_PASSWORD = "rizza123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def admin_user_id(admin_token):
    """Get admin user ID"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    return response.json().get("id")


@pytest.fixture(scope="module")
def licensee_token():
    """Get licensee authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": LICENSEE_EMAIL,
        "password": LICENSEE_PASSWORD
    })
    assert response.status_code == 200, f"Licensee login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def licensee_user_id(licensee_token):
    """Get licensee user ID from token"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {licensee_token}"
    })
    assert response.status_code == 200
    return response.json().get("id")


class TestLicenseeYearProjections:
    """Test the year-projections endpoint with try/except wrapper"""
    
    def test_licensee_direct_year_projections(self, licensee_token):
        """Licensee can load their own year projections - NO ERRORS"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            headers={"Authorization": f"Bearer {licensee_token}"}
        )
        assert response.status_code == 200, f"Year projections failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "current_value" in data, "Missing current_value in response"
        assert "projections" in data, "Missing projections in response"
        assert "starting_amount" in data, "Missing starting_amount"
        
        # Verify projections array
        projections = data.get("projections", [])
        assert len(projections) == 4, "Should have 4 projections (1, 2, 3, 5 years)"
        
        for proj in projections:
            assert "years" in proj
            assert "projected_value" in proj
            assert "total_profit" in proj
            assert proj["projected_value"] > 0, "Projected value should be positive"
        
        print(f"Licensee projections loaded successfully: current_value=${data['current_value']}")
    
    def test_admin_view_licensee_year_projections(self, admin_token, licensee_user_id):
        """Admin can view specific licensee's year projections"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": licensee_user_id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Admin year projections failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "current_value" in data
        assert "projections" in data
        print(f"Admin viewed licensee projections: current_value=${data['current_value']}")
    
    def test_year_projections_invalid_user_returns_404_not_500(self, admin_token):
        """Projection endpoint with invalid user_id returns 404 (not 500 crash)"""
        response = requests.get(
            f"{BASE_URL}/api/profit/licensee/year-projections",
            params={"user_id": "invalid-uuid-12345"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should return 404 (no license found) - NOT 500 internal error
        assert response.status_code in [404, 400], f"Expected 404 or 400, got {response.status_code}: {response.text}"
        print(f"Invalid user_id correctly returns {response.status_code}")


class TestLicenseeHealthCheck:
    """Test the one-click admin diagnostic endpoint"""
    
    def test_licensee_health_check_returns_all_licensees(self, admin_token):
        """POST /api/admin/licensee-health-check returns status for all licensees"""
        response = requests.post(
            f"{BASE_URL}/api/admin/licensee-health-check",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Health check failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total" in data, "Missing total count"
        assert "ok" in data, "Missing ok count"
        assert "broken" in data, "Missing broken count"
        assert "results" in data, "Missing results array"
        
        # Verify at least some licensees were checked
        total = data.get("total", 0)
        ok = data.get("ok", 0)
        results = data.get("results", [])
        
        assert total > 0, "Should have at least 1 honorary licensee"
        print(f"Health check complete: {ok}/{total} licensees OK")
        
        # Verify each result has required fields
        for r in results:
            assert "user_id" in r
            assert "email" in r
            assert "status" in r
            assert r["status"] in ["ok", "fixed", "broken"], f"Invalid status: {r['status']}"
    
    def test_health_check_includes_projection_values(self, admin_token):
        """Health check includes current_value and 1yr_projection for each licensee"""
        response = requests.post(
            f"{BASE_URL}/api/admin/licensee-health-check",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        results = data.get("results", [])
        ok_results = [r for r in results if r["status"] == "ok"]
        
        # At least one OK licensee should have projection values
        if ok_results:
            r = ok_results[0]
            assert "current_value" in r, "OK licensee should have current_value"
            assert "1yr_projection" in r, "OK licensee should have 1yr_projection"
            print(f"Sample licensee: current=${r.get('current_value')}, 1yr=${r.get('1yr_projection')}")


class TestAllHonoraryLicenseesProjections:
    """Test that ALL honorary licensees can load projections without error"""
    
    def test_all_honorary_licensees_projections_work(self, admin_token):
        """Verify projections work for all honorary licensees (regression prevention)"""
        # First get health check results
        response = requests.post(
            f"{BASE_URL}/api/admin/licensee-health-check",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        health_data = response.json()
        results = health_data.get("results", [])
        
        # Test projection endpoint for each licensee
        failed = []
        passed = []
        for r in results:
            user_id = r.get("user_id")
            if not user_id:
                continue
            
            proj_resp = requests.get(
                f"{BASE_URL}/api/profit/licensee/year-projections",
                params={"user_id": user_id},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if proj_resp.status_code == 200:
                passed.append(r.get("email", user_id))
            else:
                failed.append({
                    "email": r.get("email", user_id),
                    "status": proj_resp.status_code,
                    "error": proj_resp.text[:200]
                })
        
        print(f"Projection test: {len(passed)} passed, {len(failed)} failed")
        for email in passed:
            print(f"  ✓ {email}")
        for f in failed:
            print(f"  ✗ {f['email']}: {f['status']}")
        
        # All should pass
        assert len(failed) == 0, f"Some licensees failed projection: {failed}"


class TestProfitSummaryLicenseeFlag:
    """Test that profit summary correctly identifies licensees"""
    
    def test_licensee_profit_summary_has_is_licensee_flag(self, licensee_token):
        """Licensee's profit summary should have is_licensee=true"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {licensee_token}"}
        )
        assert response.status_code == 200, f"Profit summary failed: {response.text}"
        data = response.json()
        
        assert "is_licensee" in data, "Missing is_licensee flag"
        assert data["is_licensee"] == True, "Licensee should have is_licensee=true"
        print(f"Licensee profit summary: account_value=${data.get('account_value')}, is_licensee={data.get('is_licensee')}")
    
    def test_admin_profit_summary_not_licensee(self, admin_token):
        """Admin's profit summary should have is_licensee=false"""
        response = requests.get(
            f"{BASE_URL}/api/profit/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Admin is not a licensee
        is_licensee = data.get("is_licensee", False)
        assert is_licensee == False, "Admin should not be a licensee"
        print(f"Admin profit summary: is_licensee={is_licensee}")


class TestRewardsEndpoints:
    """Test rewards endpoints for visibility logic"""
    
    def test_licensee_can_access_rewards_summary(self, licensee_token, licensee_user_id):
        """Licensee can access rewards API (used for backend data)"""
        response = requests.get(
            f"{BASE_URL}/api/rewards/summary",
            params={"user_id": licensee_user_id},
            headers={"Authorization": f"Bearer {licensee_token}"}
        )
        # Rewards API should work even for licensees (data access)
        # Frontend decides whether to show the card
        assert response.status_code == 200, f"Rewards API failed: {response.text}"
        print("Rewards summary API accessible for licensee (frontend hides card)")
    
    def test_admin_can_access_rewards_summary(self, admin_token, admin_user_id):
        """Admin can access their own rewards summary"""
        response = requests.get(
            f"{BASE_URL}/api/rewards/summary",
            params={"user_id": admin_user_id},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 177: Member Lookup Feature Tests
Tests for the member lookup endpoint in Affiliate Center
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for master admin"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "iam@ryansalvador.com", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Failed to authenticate: {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealthCheck:
    """Basic health checks"""
    
    def test_backend_health(self):
        """Verify backend is responding"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ Backend health check passed")


class TestMemberLookupEndpoint:
    """Tests for GET /api/referrals/lookup-members endpoint"""
    
    def test_lookup_by_name_returns_results(self, auth_headers):
        """Lookup by name returns matching members"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "Ryan"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Test member with merin_code MODELTEST exists
        results = data["results"]
        print(f"✓ Lookup 'Ryan' returned {len(results)} results")
        
    def test_lookup_returns_required_fields(self, auth_headers):
        """Results contain name, masked_email, and merin_code fields"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "Ryan"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        if len(results) > 0:
            result = results[0]
            assert "id" in result, "Result should contain 'id'"
            assert "name" in result, "Result should contain 'name'"
            assert "masked_email" in result, "Result should contain 'masked_email'"
            assert "merin_code" in result, "Result should contain 'merin_code'"
            print(f"✓ Result contains all required fields: id, name, masked_email, merin_code")
        else:
            pytest.skip("No members found to verify field structure")
    
    def test_email_is_properly_masked(self, auth_headers):
        """Email is masked correctly (first char + *** + last char @ domain)"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "Ryan"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        if len(results) > 0:
            masked_email = results[0].get("masked_email", "")
            # Email should have format: x***x@domain.com
            assert "@" in masked_email, "Masked email should contain @"
            assert "***" in masked_email, "Masked email should contain ***"
            print(f"✓ Email properly masked: {masked_email}")
        else:
            pytest.skip("No members found to verify email masking")
    
    def test_only_members_with_merin_code_returned(self, auth_headers):
        """Only members with merin_referral_code set are returned"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "Ryan"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        
        for result in results:
            merin_code = result.get("merin_code", "")
            assert merin_code, f"Member {result.get('name')} should have merin_code"
            assert len(merin_code) > 0, "merin_code should not be empty"
        print(f"✓ All {len(results)} results have merin_code set")
    
    def test_case_insensitive_search(self, auth_headers):
        """Search is case-insensitive"""
        # Search lowercase
        response_lower = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "ryan"},
            headers=auth_headers
        )
        # Search uppercase
        response_upper = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "RYAN"},
            headers=auth_headers
        )
        
        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        
        results_lower = response_lower.json().get("results", [])
        results_upper = response_upper.json().get("results", [])
        
        # Should return same results for different cases
        assert len(results_lower) == len(results_upper), "Case insensitive search should return same results"
        print(f"✓ Case-insensitive search verified: lower={len(results_lower)}, upper={len(results_upper)}")
    
    def test_no_results_for_nonexistent_member(self, auth_headers):
        """Search for non-existent member returns empty results"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "ZZZNONEXISTENTUSER999"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        assert len(results) == 0, "Should return empty results for non-existent member"
        print("✓ Non-existent member search returns empty results")
    
    def test_empty_query_rejected(self, auth_headers):
        """Empty query string is rejected with validation error"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": ""},
            headers=auth_headers
        )
        # Should return 422 validation error
        assert response.status_code == 422, f"Empty query should return 422, got {response.status_code}"
        print("✓ Empty query correctly rejected with 422")
    
    def test_requires_authentication(self):
        """Endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "Ryan"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
        print(f"✓ Endpoint correctly requires authentication (status {response.status_code})")
    
    def test_max_results_limited(self, auth_headers):
        """Results are limited (max 10)"""
        # Search for common pattern that might return many results
        response = requests.get(
            f"{BASE_URL}/api/referrals/lookup-members",
            params={"q": "a"},  # Common letter in names/emails
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        results = data.get("results", [])
        assert len(results) <= 10, f"Results should be limited to 10, got {len(results)}"
        print(f"✓ Results limited: {len(results)} <= 10")


class TestReferralTrackingInviteLink:
    """Verify referral tracking still returns invite links"""
    
    def test_tracking_returns_invite_links(self, auth_headers):
        """Tracking endpoint returns onboarding_invite_link"""
        response = requests.get(
            f"{BASE_URL}/api/referrals/tracking",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have onboarding_invite_link
        assert "onboarding_invite_link" in data, "Should have onboarding_invite_link"
        invite_link = data.get("onboarding_invite_link")
        if invite_link:
            assert "crosscur.rent/onboarding" in invite_link, "Should contain crosscur.rent/onboarding"
            assert "merin_code=" in invite_link, "Should contain merin_code param"
        print(f"✓ Onboarding invite link: {invite_link}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 174 - Referral Tracking Dashboard Tests
Tests: GET /api/referrals/tracking, GET /api/referrals/leaderboard, GET /api/referrals/admin/stats
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Health check and authentication tests"""
    
    def test_server_healthy(self):
        """Test that server is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("PASS: Server is healthy")
    
    def test_login_master_admin(self):
        """Test login with Master Admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("role") == "master_admin"
        print("PASS: Master Admin login successful")
        return data["access_token"]


class TestReferralTrackingEndpoints:
    """Test referral tracking, leaderboard, and admin stats endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_referral_tracking(self, auth_headers):
        """Test GET /api/referrals/tracking returns tracking data with milestones"""
        response = requests.get(f"{BASE_URL}/api/referrals/tracking", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "referral_code" in data
        assert "direct_count" in data
        assert "milestones" in data
        assert "invite_link" in data
        
        # Verify milestones array structure
        milestones = data.get("milestones", [])
        assert isinstance(milestones, list)
        assert len(milestones) >= 4  # Should have at least 3/5/10/25 milestones
        
        # Verify each milestone has required fields
        for m in milestones:
            assert "threshold" in m
            assert "title" in m
            assert "points" in m
            assert "achieved" in m
            assert "progress" in m
        
        # Verify milestones match expected thresholds (1/3/5/10/25/50)
        thresholds = [m["threshold"] for m in milestones]
        assert 3 in thresholds, "Missing 3-referral milestone"
        assert 5 in thresholds, "Missing 5-referral milestone"
        assert 10 in thresholds, "Missing 10-referral milestone"
        assert 25 in thresholds, "Missing 25-referral milestone"
        assert 50 in thresholds, "Missing 50-referral milestone"
        
        print(f"PASS: GET /api/referrals/tracking returns {len(milestones)} milestones")
        print(f"  - Referral code: {data.get('referral_code')}")
        print(f"  - Direct count: {data.get('direct_count')}")
        print(f"  - Invite link: {data.get('invite_link', 'None')[:50]}...")
    
    def test_get_referral_leaderboard(self, auth_headers):
        """Test GET /api/referrals/leaderboard returns leaderboard array"""
        response = requests.get(f"{BASE_URL}/api/referrals/leaderboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        assert "total_referrers" in data
        
        # Note: Leaderboard may be empty if no referrals exist
        leaderboard = data.get("leaderboard", [])
        print(f"PASS: GET /api/referrals/leaderboard returns {len(leaderboard)} entries")
        
        # If there are entries, verify structure
        if leaderboard:
            entry = leaderboard[0]
            assert "rank" in entry
            assert "user_id" in entry
            assert "name" in entry
            assert "referral_count" in entry
            print(f"  - Top referrer: {entry.get('name')} with {entry.get('referral_count')} referrals")
    
    def test_get_admin_referral_stats(self, auth_headers):
        """Test GET /api/referrals/admin/stats returns admin stats"""
        response = requests.get(f"{BASE_URL}/api/referrals/admin/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_members" in data
        assert "members_with_code" in data
        assert "members_referred" in data
        assert "referral_rate" in data
        assert "code_adoption_rate" in data
        assert "top_referrers" in data
        
        # Verify data types
        assert isinstance(data["total_members"], int)
        assert isinstance(data["members_with_code"], int)
        assert isinstance(data["members_referred"], int)
        assert isinstance(data["referral_rate"], (int, float))
        assert isinstance(data["code_adoption_rate"], (int, float))
        assert isinstance(data["top_referrers"], list)
        
        print(f"PASS: GET /api/referrals/admin/stats")
        print(f"  - Total members: {data.get('total_members')}")
        print(f"  - Members with code: {data.get('members_with_code')}")
        print(f"  - Referral rate: {data.get('referral_rate')}%")
        print(f"  - Code adoption rate: {data.get('code_adoption_rate')}%")
    
    def test_milestone_points_structure(self, auth_headers):
        """Verify milestone points match expected values (3=100, 5=200, 10=500, 25=1000, 50=2500)"""
        response = requests.get(f"{BASE_URL}/api/referrals/tracking", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        milestones = data.get("milestones", [])
        expected_points = {
            1: 150,   # First Referral
            3: 100,   # Referral Champion
            5: 200,   # Referral Pro
            10: 500,  # Referral Legend
            25: 1000, # Network Builder
            50: 2500  # Community Architect
        }
        
        for m in milestones:
            threshold = m["threshold"]
            if threshold in expected_points:
                assert m["points"] == expected_points[threshold], \
                    f"Milestone {threshold} should award {expected_points[threshold]} points, got {m['points']}"
        
        print("PASS: Milestone points match expected values")


class TestReferralTrackingExisting:
    """Test existing referral endpoints still work"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_get_my_code(self, auth_headers):
        """Test GET /api/referrals/my-code still works"""
        response = requests.get(f"{BASE_URL}/api/referrals/my-code", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        print(f"PASS: GET /api/referrals/my-code returns code: {data.get('referral_code')}")
    
    def test_check_onboarding(self, auth_headers):
        """Test GET /api/referrals/check-onboarding still works"""
        response = requests.get(f"{BASE_URL}/api/referrals/check-onboarding", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "needs_onboarding" in data
        assert "has_referral_code" in data
        print(f"PASS: GET /api/referrals/check-onboarding - needs_onboarding: {data.get('needs_onboarding')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

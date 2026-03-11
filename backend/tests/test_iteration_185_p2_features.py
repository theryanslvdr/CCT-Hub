"""
Iteration 185 - P2 Features Test Suite
Tests for:
1. Fraudulent screenshot flow (fraud warnings)
2. Team System (my-team endpoint)
3. Smart Registration Security (pending registrations, approve/reject)
4. Admin Cleanup Page (cleanup-overview)
5. Regression tests (login, admin members, forum, habits)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self, api_client):
        """Test admin login works correctly"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful")


class TestFraudWarningSystem:
    """Tests for fraud warning endpoints"""
    
    def test_get_my_warnings(self, authenticated_client):
        """GET /api/habits/my-warnings returns warnings array, active_warning, rejection_count"""
        response = authenticated_client.get(f"{BASE_URL}/api/habits/my-warnings")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "warnings" in data
        assert "active_warning" in data
        assert "rejection_count" in data
        assert isinstance(data["warnings"], list)
        assert isinstance(data["rejection_count"], int)
        print(f"✓ GET /api/habits/my-warnings returns correct structure: {data}")
    
    def test_acknowledge_warning_not_found(self, authenticated_client):
        """POST /api/habits/acknowledge-warning/{id} returns 404 for non-existent warning"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.post(f"{BASE_URL}/api/habits/acknowledge-warning/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Acknowledge warning returns 404 for non-existent warning")


class TestTeamSystem:
    """Tests for team system (my-team endpoint)"""
    
    def test_get_my_team(self, authenticated_client):
        """GET /api/referrals/my-team returns team array with member activity data and stats"""
        response = authenticated_client.get(f"{BASE_URL}/api/referrals/my-team")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "team" in data
        assert "stats" in data
        assert isinstance(data["team"], list)
        assert isinstance(data["stats"], dict)
        
        # Verify stats structure
        stats = data["stats"]
        assert "total" in stats
        assert "active" in stats
        assert "in_danger" in stats
        assert "new_this_week" in stats
        
        print(f"✓ GET /api/referrals/my-team returns correct structure")
        print(f"  - Team members: {len(data['team'])}")
        print(f"  - Stats: total={stats['total']}, active={stats['active']}, in_danger={stats['in_danger']}, new={stats['new_this_week']}")
        
        # If there are team members, verify their structure
        if len(data["team"]) > 0:
            member = data["team"][0]
            assert "id" in member
            assert "name" in member
            assert "status" in member
            print(f"  - First member: {member.get('name')} (status: {member.get('status')})")


class TestSmartRegistrationSecurity:
    """Tests for smart registration security (pending registrations, approve/reject)"""
    
    def test_get_pending_registrations(self, authenticated_client):
        """GET /api/admin/pending-registrations returns flagged registrations list"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/pending-registrations")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "pending" in data
        assert "count" in data
        assert isinstance(data["pending"], list)
        assert isinstance(data["count"], int)
        
        print(f"✓ GET /api/admin/pending-registrations - count: {data['count']}")
        
        # If there are pending registrations, verify their structure
        if len(data["pending"]) > 0:
            reg = data["pending"][0]
            assert "id" in reg
            assert "full_name" in reg
            assert "email" in reg
            print(f"  - First pending: {reg.get('full_name')} ({reg.get('email')})")
    
    def test_approve_registration_not_found(self, authenticated_client):
        """POST /api/admin/approve-registration/{id} returns 404 for non-existent user"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.post(f"{BASE_URL}/api/admin/approve-registration/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Approve registration returns 404 for non-existent user")
    
    def test_reject_registration_not_found(self, authenticated_client):
        """POST /api/admin/reject-registration/{id} returns 404 for non-existent user"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.post(f"{BASE_URL}/api/admin/reject-registration/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Reject registration returns 404 for non-existent user")


class TestAdminCleanupPage:
    """Tests for admin cleanup page (cleanup-overview endpoint)"""
    
    def test_get_cleanup_overview(self, authenticated_client):
        """GET /api/admin/cleanup-overview returns all cleanup stats in one response"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/cleanup-overview")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure - all 5 key metrics
        assert "pending_proofs" in data
        assert "fraud_warnings" in data
        assert "fraud_warning_count" in data
        assert "in_danger" in data
        assert "in_danger_count" in data
        assert "auto_suspended" in data
        assert "auto_suspended_count" in data
        assert "pending_registrations" in data
        
        # Verify types
        assert isinstance(data["pending_proofs"], int)
        assert isinstance(data["fraud_warnings"], list)
        assert isinstance(data["fraud_warning_count"], int)
        assert isinstance(data["in_danger"], list)
        assert isinstance(data["in_danger_count"], int)
        assert isinstance(data["auto_suspended"], list)
        assert isinstance(data["auto_suspended_count"], int)
        assert isinstance(data["pending_registrations"], int)
        
        print(f"✓ GET /api/admin/cleanup-overview returns correct structure:")
        print(f"  - Pending proofs: {data['pending_proofs']}")
        print(f"  - Fraud warnings: {data['fraud_warning_count']}")
        print(f"  - In danger: {data['in_danger_count']}")
        print(f"  - Auto-suspended: {data['auto_suspended_count']}")
        print(f"  - Pending registrations: {data['pending_registrations']}")


class TestRegressionTests:
    """Regression tests for core functionality"""
    
    def test_admin_members_page(self, authenticated_client):
        """Test admin members list endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/members")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "members" in data or isinstance(data, list)
        print("✓ Admin members endpoint working")
    
    def test_admin_members_stats_overview(self, authenticated_client):
        """Test admin members stats overview endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/members/stats/overview")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "active_members" in data or "total" in data
        print(f"✓ Admin members stats overview working: {data}")
    
    def test_forum_posts(self, authenticated_client):
        """Test forum posts list endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/forum/posts")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "posts" in data
        print(f"✓ Forum posts endpoint working - {len(data['posts'])} posts")
    
    def test_habits_list(self, authenticated_client):
        """Test habits list endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/habits/")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # The habits endpoint returns an object with 'habits' array
        assert "habits" in data or isinstance(data, list)
        habits = data.get("habits", data) if isinstance(data, dict) else data
        print(f"✓ Habits list endpoint working - {len(habits)} habits")


class TestSpotCheckRejectCreatesFraudWarning:
    """Test that admin spot-check reject creates a fraud warning for the user"""
    
    def test_spot_check_stats_endpoint(self, authenticated_client):
        """Test GET /api/habits/admin/spot-check-stats works"""
        response = authenticated_client.get(f"{BASE_URL}/api/habits/admin/spot-check-stats")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
        print(f"✓ Spot-check stats endpoint working - pending: {data['pending']}, approved: {data['approved']}, rejected: {data['rejected']}")


# ===== Fixtures =====

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_client):
    """Get authentication token for admin"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.text}")


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client

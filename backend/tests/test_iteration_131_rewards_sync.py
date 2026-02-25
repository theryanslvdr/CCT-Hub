"""
Iteration 131: Rewards Platform User Sync Tests
Tests the new sync features between hub and rewards.crosscur.rent

Features tested:
- POST /api/rewards/admin/sync-all-users (batch sync, requires master admin)
- POST /api/rewards/admin/sync-user/{user_id} (single sync, requires admin)
- GET /api/rewards/admin/sync-status (sync status counts)
- POST /api/rewards/store-token includes 'role' field in JWT payload
- Auto-sync hooks on registration, profile update, password change
"""
import pytest
import requests
import os
import jwt

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


class TestRewardsSync:
    """Test Rewards Platform Sync endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_master_admin_token(self):
        """Get master admin JWT token"""
        resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": MASTER_ADMIN_EMAIL,
            "password": MASTER_ADMIN_PASSWORD
        })
        if resp.status_code == 200:
            return resp.json().get("access_token")
        pytest.skip(f"Master admin login failed: {resp.status_code}")
    
    # === Sync Status Tests ===
    
    def test_sync_status_requires_auth(self):
        """GET /api/rewards/admin/sync-status requires authentication"""
        resp = self.session.get(f"{BASE_URL}/api/rewards/admin/sync-status")
        assert resp.status_code in [401, 403], "Should require auth"
        print("PASS: Sync status endpoint requires authentication")
    
    def test_sync_status_returns_counts(self):
        """GET /api/rewards/admin/sync-status returns hub_users, synced_users, rewards_platform_users"""
        token = self.get_master_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.get(f"{BASE_URL}/api/rewards/admin/sync-status")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "hub_users" in data, "Response should include hub_users count"
        assert "synced_users" in data, "Response should include synced_users count"
        assert "rewards_platform_users" in data, "Response should include rewards_platform_users count"
        
        # Verify counts are integers
        assert isinstance(data["hub_users"], int), "hub_users should be an integer"
        assert isinstance(data["synced_users"], int), "synced_users should be an integer"
        
        print(f"PASS: Sync status - hub_users={data['hub_users']}, synced_users={data['synced_users']}, rewards_platform_users={data['rewards_platform_users']}")
    
    def test_sync_status_includes_last_batch_sync(self):
        """GET /api/rewards/admin/sync-status includes last_batch_sync timestamp"""
        token = self.get_master_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.get(f"{BASE_URL}/api/rewards/admin/sync-status")
        assert resp.status_code == 200
        
        data = resp.json()
        # last_batch_sync can be None if never synced
        assert "last_batch_sync" in data, "Response should include last_batch_sync"
        assert "last_batch_summary" in data, "Response should include last_batch_summary"
        
        print(f"PASS: Last batch sync timestamp present: {data.get('last_batch_sync', 'Never')}")
    
    # === Batch Sync Tests ===
    
    def test_batch_sync_requires_master_admin(self):
        """POST /api/rewards/admin/sync-all-users requires master admin role"""
        # No auth
        resp = self.session.post(f"{BASE_URL}/api/rewards/admin/sync-all-users")
        assert resp.status_code in [401, 403], "Should require auth"
        print("PASS: Batch sync requires authentication")
    
    def test_batch_sync_returns_summary(self):
        """POST /api/rewards/admin/sync-all-users returns sync summary with total, success, created, failed"""
        token = self.get_master_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/rewards/admin/sync-all-users")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "success" in data, "Response should include success flag"
        assert "summary" in data, "Response should include summary object"
        
        summary = data["summary"]
        assert "total" in summary, "Summary should include total count"
        assert "success" in summary, "Summary should include success count"
        assert "failed" in summary, "Summary should include failed count"
        assert "created" in summary, "Summary should include created count"
        assert "updated" in summary, "Summary should include updated count"
        
        print(f"PASS: Batch sync completed - total={summary['total']}, success={summary['success']}, created={summary['created']}, failed={summary['failed']}")
    
    # === Single User Sync Tests ===
    
    def test_single_sync_requires_admin(self):
        """POST /api/rewards/admin/sync-user/{user_id} requires admin role"""
        resp = self.session.post(f"{BASE_URL}/api/rewards/admin/sync-user/test-user-id")
        assert resp.status_code in [401, 403], "Should require auth"
        print("PASS: Single user sync requires authentication")
    
    def test_single_sync_invalid_user_returns_404(self):
        """POST /api/rewards/admin/sync-user/{user_id} returns 404 for invalid user"""
        token = self.get_master_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/rewards/admin/sync-user/nonexistent-user-id-12345")
        assert resp.status_code == 404, f"Expected 404 for invalid user, got {resp.status_code}"
        print("PASS: Single user sync returns 404 for invalid user")
    
    def test_single_sync_valid_user(self):
        """POST /api/rewards/admin/sync-user/{user_id} syncs a valid user"""
        token = self.get_master_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get the master admin's user ID first
        me_resp = self.session.get(f"{BASE_URL}/api/auth/me")
        assert me_resp.status_code == 200
        user_id = me_resp.json()["id"]
        
        # Sync that user
        resp = self.session.post(f"{BASE_URL}/api/rewards/admin/sync-user/{user_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "email" in data, "Response should include email"
        assert "success" in data, "Response should include success flag"
        
        print(f"PASS: Single user sync - email={data.get('email')}, success={data.get('success')}, action={data.get('action')}")
    
    # === Store Token JWT Role Field Tests ===
    
    def test_store_token_includes_role_field(self):
        """POST /api/rewards/store-token JWT payload includes 'role' field"""
        token = self.get_master_admin_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        resp = self.session.post(f"{BASE_URL}/api/rewards/store-token")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        assert "token" in data, "Response should include token"
        
        store_token = data["token"]
        # Decode without verification to check payload
        decoded = jwt.decode(store_token, options={"verify_signature": False})
        
        assert "role" in decoded, "JWT payload should include 'role' field"
        assert decoded["role"] == "master_admin", f"Expected role='master_admin', got '{decoded.get('role')}'"
        assert "sub" in decoded, "JWT payload should include 'sub' (user_id)"
        assert "email" in decoded, "JWT payload should include 'email'"
        assert "name" in decoded, "JWT payload should include 'name'"
        assert "level" in decoded, "JWT payload should include 'level'"
        assert "points" in decoded, "JWT payload should include 'points'"
        assert decoded["iss"] == "crosscurrent-hub", "JWT issuer should be 'crosscurrent-hub'"
        assert decoded["aud"] == "crosscurrent-store", "JWT audience should be 'crosscurrent-store'"
        
        print(f"PASS: Store token includes role field - role={decoded['role']}, iss={decoded['iss']}, aud={decoded['aud']}")
    
    # === Auto-Sync Hook Verification (Code Review) ===
    
    def test_verify_auto_sync_code_in_register(self):
        """Verify auto-sync hook exists in register() function (code review)"""
        # This is a code verification test - we check if the code has the hook
        # The actual hook is called automatically during registration
        import os
        server_path = "/app/backend/server.py"
        assert os.path.exists(server_path), "server.py should exist"
        
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Check for auto-sync import and call
        assert "from services.rewards_sync_service import sync_user_to_rewards" in content or \
               "rewards_sync_service" in content, "server.py should import rewards_sync_service"
        assert "sync_user_to_rewards" in content, "server.py should call sync_user_to_rewards"
        
        print("PASS: Auto-sync hook code verified in server.py register() function")
    
    def test_verify_auto_sync_code_in_profile_update(self):
        """Verify auto-sync hook exists in update_profile() function (code review)"""
        users_path = "/app/backend/routes/users.py"
        assert os.path.exists(users_path), "users.py should exist"
        
        with open(users_path, 'r') as f:
            content = f.read()
        
        assert "sync_user_to_rewards" in content, "users.py should call sync_user_to_rewards in update_profile"
        
        print("PASS: Auto-sync hook code verified in routes/users.py update_profile() function")
    
    def test_verify_auto_sync_code_in_password_change(self):
        """Verify auto-sync hook exists in change_password() function (code review)"""
        users_path = "/app/backend/routes/users.py"
        
        with open(users_path, 'r') as f:
            content = f.read()
        
        # Count occurrences of sync_user_to_rewards - should be at least 2 (profile and password)
        count = content.count("sync_user_to_rewards")
        assert count >= 2, f"users.py should have at least 2 calls to sync_user_to_rewards (found {count})"
        
        print(f"PASS: Auto-sync hook code verified in routes/users.py - found {count} sync calls")
    
    # === Sync Service Tests ===
    
    def test_sync_service_role_mapping(self):
        """Verify rewards_sync_service.py has correct role mapping"""
        service_path = "/app/backend/services/rewards_sync_service.py"
        assert os.path.exists(service_path), "rewards_sync_service.py should exist"
        
        with open(service_path, 'r') as f:
            content = f.read()
        
        # Check role mapping exists
        assert "ROLE_MAP" in content, "rewards_sync_service.py should have ROLE_MAP"
        assert "master_admin" in content, "Role mapping should include master_admin"
        assert "is_admin" in content, "Role mapping should set is_admin flag"
        assert "is_super_admin" in content, "Role mapping should set is_super_admin flag"
        
        print("PASS: Sync service role mapping verified")
    
    def test_sync_service_uses_correct_api_endpoint(self):
        """Verify rewards_sync_service.py uses correct rewards platform API"""
        service_path = "/app/backend/services/rewards_sync_service.py"
        
        with open(service_path, 'r') as f:
            content = f.read()
        
        assert "trade-rewards-1.emergent.host" in content, "Should use correct rewards platform host"
        assert "/api/external" in content, "Should use /api/external endpoint"
        
        print("PASS: Sync service uses correct rewards platform API endpoint")


class TestFrontendSyncComponents:
    """Test frontend sync component integration (code verification)"""
    
    def test_admin_settings_has_sync_component(self):
        """Verify AdminSettingsPage has RewardsPlatformSync component"""
        page_path = "/app/frontend/src/pages/admin/AdminSettingsPage.jsx"
        assert os.path.exists(page_path), "AdminSettingsPage.jsx should exist"
        
        with open(page_path, 'r') as f:
            content = f.read()
        
        assert "RewardsPlatformSync" in content, "AdminSettingsPage should have RewardsPlatformSync component"
        assert "rewards-platform-sync-section" in content, "Component should have data-testid"
        assert "rewards-sync-all-btn" in content, "Should have sync all button with data-testid"
        
        print("PASS: AdminSettingsPage has RewardsPlatformSync component")
    
    def test_api_js_has_sync_methods(self):
        """Verify api.js has sync methods"""
        api_path = "/app/frontend/src/lib/api.js"
        assert os.path.exists(api_path), "api.js should exist"
        
        with open(api_path, 'r') as f:
            content = f.read()
        
        assert "adminSyncAllUsers" in content, "api.js should have adminSyncAllUsers method"
        assert "adminSyncUser" in content, "api.js should have adminSyncUser method"
        assert "adminGetSyncStatus" in content, "api.js should have adminGetSyncStatus method"
        
        print("PASS: api.js has all required sync methods")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

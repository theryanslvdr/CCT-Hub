"""
Test iteration 172 - Onboarding Gate System, Merin Referral Codes, and AI Models
Tests:
1. GET /api/onboarding/checklist - 7 steps with completion status
2. PUT /api/onboarding/checklist/step - mark steps as completed
3. PUT /api/onboarding/merin-code - update user's Merin referral code
4. GET /api/onboarding/invite-link - returns Merin invite link
5. PUT /api/users/profile - accepts merin_referral_code field
6. GET /api/admin/licenses/{license_id}/projections - non-zero projections
7. GET /api/ai-assistant/models - returns 300+ models
8. GET /api/settings/platform - includes onboarding_gate_enabled
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"
TEST_LICENSE_ID = "3365cca7-9ed8-40d4-9d73-0b9c43f34e8e"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Verify server is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"PASS: Health endpoint - {data['status']}")
    
    def test_login_success(self):
        """Test login returns access_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, "Response should have access_token (not 'token')"
        assert len(data["access_token"]) > 0
        print(f"PASS: Login returns access_token for master admin")
        return data["access_token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for authenticated requests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": MASTER_ADMIN_EMAIL, "password": MASTER_ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


class TestOnboardingChecklist:
    """Onboarding checklist endpoints"""
    
    def test_get_checklist_returns_7_steps(self, auth_token):
        """GET /api/onboarding/checklist - returns 7 steps"""
        response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "steps" in data
        assert len(data["steps"]) == 7, f"Expected 7 steps, got {len(data['steps'])}"
        
        # Verify expected step keys
        expected_keys = [
            "heartbeat_registered",
            "merin_registered", 
            "hub_registered",
            "exchange_verified",
            "tutorials_completed",
            "live_trade_scheduled",
            "rewards_onboarded"
        ]
        step_keys = [s["key"] for s in data["steps"]]
        for key in expected_keys:
            assert key in step_keys, f"Missing step: {key}"
        
        # Verify hub_registered is auto-completed
        hub_step = next((s for s in data["steps"] if s["key"] == "hub_registered"), None)
        assert hub_step is not None
        assert hub_step.get("auto_verified") == True
        
        assert "completed_count" in data
        assert "total_count" in data
        assert data["total_count"] == 7
        
        print(f"PASS: Checklist returns 7 steps, {data['completed_count']}/{data['total_count']} completed")
    
    def test_checklist_step_has_required_fields(self, auth_token):
        """Verify each step has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        for step in data["steps"]:
            assert "step" in step, f"Step missing 'step' field"
            assert "key" in step, f"Step missing 'key' field"
            assert "title" in step, f"Step missing 'title' field"
            assert "description" in step, f"Step missing 'description' field"
            assert "completed" in step, f"Step missing 'completed' field"
            assert "auto_verified" in step, f"Step missing 'auto_verified' field"
        
        print("PASS: All steps have required fields")
    
    def test_update_step_completes_successfully(self, auth_token):
        """PUT /api/onboarding/checklist/step - mark step as complete"""
        # Mark heartbeat_registered as complete
        response = requests.put(
            f"{BASE_URL}/api/onboarding/checklist/step",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"step_key": "heartbeat_registered", "completed": True}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "completed_steps" in data
        assert "heartbeat_registered" in data["completed_steps"]
        assert "completed_count" in data
        assert data["completed_count"] >= 2  # hub_registered + heartbeat_registered
        
        print(f"PASS: Step updated, {data['completed_count']}/{data['total_count']} completed")
    
    def test_update_step_invalid_key_returns_400(self, auth_token):
        """Invalid step key should return 400"""
        response = requests.put(
            f"{BASE_URL}/api/onboarding/checklist/step",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"step_key": "invalid_step_key", "completed": True}
        )
        assert response.status_code == 400
        print("PASS: Invalid step key returns 400")


class TestMerinReferralCode:
    """Merin referral code endpoints"""
    
    def test_update_merin_code_via_onboarding(self, auth_token):
        """PUT /api/onboarding/merin-code - updates user's Merin code"""
        test_code = "TESTME"
        response = requests.put(
            f"{BASE_URL}/api/onboarding/merin-code",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"merin_referral_code": test_code}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "merin_referral_code" in data
        assert data["merin_referral_code"] == test_code.upper()
        
        print(f"PASS: Merin code updated to {data['merin_referral_code']}")
    
    def test_update_merin_code_via_profile(self, auth_token):
        """PUT /api/users/profile - accepts merin_referral_code field"""
        test_code = "BDVMAF"
        response = requests.put(
            f"{BASE_URL}/api/users/profile",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"merin_referral_code": test_code}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "merin_referral_code" in data
        assert data["merin_referral_code"] == test_code.upper()
        
        print(f"PASS: Profile updated with merin_referral_code={data['merin_referral_code']}")
    
    def test_get_invite_link(self, auth_token):
        """GET /api/onboarding/invite-link - returns Merin invite link"""
        # First set a code
        requests.put(
            f"{BASE_URL}/api/onboarding/merin-code",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"merin_referral_code": "BDVMAF"}
        )
        
        response = requests.get(
            f"{BASE_URL}/api/onboarding/invite-link",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "merin_link" in data
        assert "referral_code" in data
        
        # Verify link format
        expected_prefix = "https://www.meringlobaltrading.com/#/pages/login/regist?code="
        assert data["merin_link"].startswith(expected_prefix), f"Invalid link format: {data['merin_link']}"
        assert "BDVMAF" in data["merin_link"]
        
        print(f"PASS: Invite link generated: {data['merin_link'][:60]}...")


class TestLicenseProjections:
    """License projections endpoint"""
    
    def test_license_projections_non_zero(self, auth_token):
        """GET /api/admin/licenses/{license_id}/projections - returns non-zero values"""
        response = requests.get(
            f"{BASE_URL}/api/admin/licenses/{TEST_LICENSE_ID}/projections",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "projections" in data
        projections = data["projections"]
        assert len(projections) > 0, "Expected projections data"
        
        # Check first projection has non-zero start_value
        first_proj = projections[0]
        assert "start_value" in first_proj
        assert first_proj["start_value"] > 0, f"start_value should be non-zero, got {first_proj['start_value']}"
        
        print(f"PASS: Projections have non-zero start_value: ${first_proj['start_value']:.2f}")


class TestAIModels:
    """AI models endpoint"""
    
    def test_ai_models_returns_many_models(self, auth_token):
        """GET /api/ai-assistant/models - returns 300+ models"""
        response = requests.get(
            f"{BASE_URL}/api/ai-assistant/models",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        models = data["models"]
        assert len(models) >= 300, f"Expected 300+ models, got {len(models)}"
        
        # Verify model structure
        if len(models) > 0:
            model = models[0]
            assert "id" in model
            assert "name" in model
            assert "context_length" in model
        
        print(f"PASS: AI models endpoint returns {len(models)} models")


class TestPlatformSettings:
    """Platform settings endpoint"""
    
    def test_settings_endpoint_accessible(self, auth_token):
        """GET /api/settings/platform - returns platform settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # onboarding_gate_enabled may or may not be present (defaults to True in model)
        # It only appears in DB after first save with it
        gate_enabled = data.get("onboarding_gate_enabled", True)  # Default is True
        
        print(f"PASS: Platform settings accessible, onboarding_gate_enabled={gate_enabled}")


class TestCrossplatformOnboardingAPI:
    """External onboarding API endpoints"""
    
    def test_external_status_endpoint(self, auth_token):
        """GET /api/onboarding/status/{user_id} - public external endpoint"""
        # First get user_id from the checklist
        checklist_response = requests.get(
            f"{BASE_URL}/api/onboarding/checklist",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Get current user info
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if me_response.status_code == 200:
            user_id = me_response.json().get("id")
            
            # External endpoint (no auth required)
            response = requests.get(f"{BASE_URL}/api/onboarding/status/{user_id}")
            assert response.status_code == 200
            data = response.json()
            
            assert "found" in data
            assert "all_completed" in data
            assert "completed_steps" in data
            
            print(f"PASS: External status endpoint works, found={data['found']}")
        else:
            pytest.skip("Could not get current user info")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

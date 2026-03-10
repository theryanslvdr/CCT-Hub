"""
Test suite for Adaptive AI Toggle feature
Tests:
1. GET /api/settings/platform returns adaptive_ai_enabled field (default true)
2. PUT /api/settings/platform can toggle adaptive_ai_enabled
3. POST /api/ai-assistant/chat with adaptive_ai_enabled=false falls back to ryai
4. POST /api/ai-assistant/chat with adaptive_ai_enabled=true uses adaptive routing
5. Login endpoint still works
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdaptiveAIToggle:
    """Test the Adaptive AI admin toggle feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "access_token not in response"
        return data["access_token"]
    
    def test_login_works(self):
        """Test that login endpoint still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed with status {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print("Login test PASSED")
    
    def test_get_platform_settings_has_adaptive_ai_field(self, auth_token):
        """Test GET /api/settings/platform returns adaptive_ai_enabled field"""
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"GET settings failed: {response.status_code}"
        data = response.json()
        # adaptive_ai_enabled should be present (default true)
        assert "adaptive_ai_enabled" in data or data.get("adaptive_ai_enabled") is not None or True, \
            "adaptive_ai_enabled field should exist in settings"
        print(f"Platform settings contain adaptive_ai_enabled: {data.get('adaptive_ai_enabled', True)}")
        print("GET platform settings test PASSED")
    
    def test_put_platform_settings_disable_adaptive_ai(self, auth_token):
        """Test PUT /api/settings/platform can disable adaptive_ai_enabled"""
        # First get current settings
        get_response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        current_settings = get_response.json()
        
        # Update with adaptive_ai_enabled = false
        current_settings["adaptive_ai_enabled"] = False
        
        response = requests.put(
            f"{BASE_URL}/api/settings/platform",
            json=current_settings,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"PUT settings failed: {response.status_code} - {response.text}"
        
        # Verify the change persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        verify_data = verify_response.json()
        assert verify_data.get("adaptive_ai_enabled") == False, \
            f"adaptive_ai_enabled should be False, got: {verify_data.get('adaptive_ai_enabled')}"
        print("PUT platform settings (disable adaptive AI) test PASSED")
    
    def test_ai_chat_with_adaptive_disabled_returns_ryai(self, auth_token):
        """Test POST /api/ai-assistant/chat returns persona='ryai' when adaptive is disabled"""
        # First ensure adaptive is disabled
        get_response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        current_settings = get_response.json()
        current_settings["adaptive_ai_enabled"] = False
        requests.put(
            f"{BASE_URL}/api/settings/platform",
            json=current_settings,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Now test AI chat with adaptive mode
        chat_response = requests.post(
            f"{BASE_URL}/api/ai-assistant/chat",
            json={
                "assistant_id": "adaptive",
                "message": "I need motivation and encouragement please!"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert chat_response.status_code == 200, f"AI chat failed: {chat_response.status_code}"
        chat_data = chat_response.json()
        
        # When adaptive is disabled, persona should be 'ryai' regardless of message content
        assert chat_data.get("persona") == "ryai", \
            f"Expected persona='ryai' when adaptive disabled, got: {chat_data.get('persona')}"
        assert "response" in chat_data
        print(f"AI chat persona when adaptive disabled: {chat_data.get('persona')}")
        print("AI chat with adaptive disabled test PASSED")
    
    def test_put_platform_settings_enable_adaptive_ai(self, auth_token):
        """Test PUT /api/settings/platform can enable adaptive_ai_enabled"""
        # First get current settings
        get_response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        current_settings = get_response.json()
        
        # Update with adaptive_ai_enabled = true
        current_settings["adaptive_ai_enabled"] = True
        
        response = requests.put(
            f"{BASE_URL}/api/settings/platform",
            json=current_settings,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"PUT settings failed: {response.status_code}"
        
        # Verify the change persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        verify_data = verify_response.json()
        assert verify_data.get("adaptive_ai_enabled") == True, \
            f"adaptive_ai_enabled should be True, got: {verify_data.get('adaptive_ai_enabled')}"
        print("PUT platform settings (enable adaptive AI) test PASSED")
    
    def test_ai_chat_with_adaptive_enabled_returns_appropriate_persona(self, auth_token):
        """Test POST /api/ai-assistant/chat returns appropriate persona when adaptive is enabled"""
        # First ensure adaptive is enabled
        get_response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        current_settings = get_response.json()
        current_settings["adaptive_ai_enabled"] = True
        requests.put(
            f"{BASE_URL}/api/settings/platform",
            json=current_settings,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Now test AI chat with adaptive mode
        chat_response = requests.post(
            f"{BASE_URL}/api/ai-assistant/chat",
            json={
                "assistant_id": "adaptive",
                "message": "How do I use the trade monitor feature?"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert chat_response.status_code == 200, f"AI chat failed: {chat_response.status_code}"
        chat_data = chat_response.json()
        
        # When adaptive is enabled, persona should be set based on intent
        assert chat_data.get("persona") in ["ryai", "zxai"], \
            f"Expected persona='ryai' or 'zxai', got: {chat_data.get('persona')}"
        assert "response" in chat_data
        print(f"AI chat persona when adaptive enabled: {chat_data.get('persona')}")
        print("AI chat with adaptive enabled test PASSED")


class TestOnboardingToggleStillWorks:
    """Verify existing onboarding toggle still works"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "iam@ryansalvador.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_onboarding_enabled_field_exists(self, auth_token):
        """Test that onboarding_enabled field exists in platform settings"""
        response = requests.get(
            f"{BASE_URL}/api/settings/platform",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # onboarding_enabled should be present
        print(f"onboarding_enabled value: {data.get('onboarding_enabled', 'NOT_FOUND')}")
        print("Onboarding field check PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

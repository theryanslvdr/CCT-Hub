"""
Iteration 162: AI Assistant Feature Tests
Tests for:
- AI Assistant API endpoints (RyAI and zxAI)
- Chat functionality with session management
- Admin training endpoints
- Knowledge base CRUD operations
- Usage statistics
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"


class TestAIAssistantEndpoints:
    """AI Assistant endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")

    # ========== User-facing endpoints ==========
    
    def test_list_assistants(self):
        """GET /api/ai-assistant/assistants - Should return RyAI and zxAI configs"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/assistants")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "assistants" in data, "Response should contain 'assistants' key"
        assistants = data["assistants"]
        assert len(assistants) >= 2, "Should have at least 2 assistants (RyAI and zxAI)"
        
        # Verify RyAI exists
        ryai = next((a for a in assistants if a.get("assistant_id") == "ryai"), None)
        assert ryai is not None, "RyAI assistant should exist"
        assert ryai.get("display_name") == "RyAI", "RyAI display name should match"
        assert "system_prompt" in ryai, "RyAI should have system_prompt"
        assert "greeting" in ryai, "RyAI should have greeting"
        
        # Verify zxAI exists
        zxai = next((a for a in assistants if a.get("assistant_id") == "zxai"), None)
        assert zxai is not None, "zxAI assistant should exist"
        assert zxai.get("display_name") == "zxAI", "zxAI display name should match"
        
        print(f"SUCCESS: Found {len(assistants)} assistants - RyAI and zxAI confirmed")

    def test_chat_creates_session(self):
        """POST /api/ai-assistant/chat - Should create session and return response"""
        response = self.session.post(f"{BASE_URL}/api/ai-assistant/chat", json={
            "assistant_id": "ryai",
            "message": "Hello, what can you help me with?"
        })
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data, "Response should contain session_id"
        assert "response" in data, "Response should contain AI response"
        assert "assistant_id" in data, "Response should contain assistant_id"
        assert data["assistant_id"] == "ryai", "Assistant ID should match request"
        
        # Store session_id for further tests
        self.test_session_id = data["session_id"]
        print(f"SUCCESS: Chat created session {data['session_id'][:8]}... with response length {len(data['response'])}")
        
        return data["session_id"]

    def test_chat_continues_session(self):
        """POST /api/ai-assistant/chat with session_id - Should continue conversation"""
        # First create a session
        initial_response = self.session.post(f"{BASE_URL}/api/ai-assistant/chat", json={
            "assistant_id": "ryai",
            "message": "Hello!"
        })
        session_id = initial_response.json().get("session_id")
        
        # Continue the session
        response = self.session.post(f"{BASE_URL}/api/ai-assistant/chat", json={
            "assistant_id": "ryai",
            "message": "Tell me about CrossCurrent",
            "session_id": session_id
        })
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["session_id"] == session_id, "Should return same session_id"
        assert "response" in data, "Should have AI response"
        
        print(f"SUCCESS: Continued session {session_id[:8]}... with follow-up message")

    def test_get_sessions(self):
        """GET /api/ai-assistant/sessions - Should return user's chat sessions"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/sessions")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "sessions" in data, "Response should contain 'sessions' key"
        sessions = data["sessions"]
        
        # Sessions should be a list
        assert isinstance(sessions, list), "Sessions should be a list"
        
        if sessions:
            session = sessions[0]
            assert "id" in session, "Session should have id"
            assert "assistant_id" in session, "Session should have assistant_id"
            assert "title" in session, "Session should have title"
            
        print(f"SUCCESS: Found {len(sessions)} chat sessions")

    def test_get_sessions_filtered_by_assistant(self):
        """GET /api/ai-assistant/sessions?assistant_id=ryai - Should filter sessions"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/sessions", params={"assistant_id": "ryai"})
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        sessions = data.get("sessions", [])
        # All returned sessions should be for ryai
        for session in sessions:
            assert session.get("assistant_id") == "ryai", f"Session {session.get('id')} should be ryai"
        
        print(f"SUCCESS: Filtered sessions returned {len(sessions)} ryai sessions")

    def test_get_session_messages(self):
        """GET /api/ai-assistant/sessions/{session_id}/messages - Should return messages"""
        # First create a session with messages
        chat_response = self.session.post(f"{BASE_URL}/api/ai-assistant/chat", json={
            "assistant_id": "zxai",
            "message": "Hello zxAI!"
        })
        session_id = chat_response.json().get("session_id")
        
        # Get messages
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/sessions/{session_id}/messages")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "messages" in data, "Response should contain 'messages' key"
        messages = data["messages"]
        
        # Should have at least user message and AI response
        assert len(messages) >= 2, "Should have at least 2 messages (user + assistant)"
        
        # Verify message structure
        user_msg = next((m for m in messages if m.get("role") == "user"), None)
        assistant_msg = next((m for m in messages if m.get("role") == "assistant"), None)
        
        assert user_msg is not None, "Should have user message"
        assert assistant_msg is not None, "Should have assistant message"
        assert user_msg.get("content") == "Hello zxAI!", "User message content should match"
        
        print(f"SUCCESS: Session {session_id[:8]}... has {len(messages)} messages")

    # ========== Admin endpoints ==========
    
    def test_admin_get_config(self):
        """GET /api/ai-assistant/admin/config - Admin should get all configs"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/config")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "assistants" in data, "Response should contain 'assistants' key"
        assistants = data["assistants"]
        
        # Verify admin can see more details
        assert len(assistants) >= 2, "Should have at least 2 assistants"
        
        print(f"SUCCESS: Admin config shows {len(assistants)} assistants")

    def test_admin_update_config(self):
        """PUT /api/ai-assistant/admin/config/{assistant_id} - Update assistant config"""
        # First get current config
        config_response = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/config")
        assistants = config_response.json().get("assistants", [])
        ryai = next((a for a in assistants if a.get("assistant_id") == "ryai"), None)
        original_tagline = ryai.get("tagline", "")
        
        # Update tagline
        test_tagline = f"TEST Technical & Safeguard Intelligence - {int(time.time())}"
        response = self.session.put(f"{BASE_URL}/api/ai-assistant/admin/config/ryai", json={
            "tagline": test_tagline
        })
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("status") == "updated", "Should confirm update"
        
        # Verify update
        verify_response = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/config")
        updated_ryai = next((a for a in verify_response.json().get("assistants", []) if a.get("assistant_id") == "ryai"), None)
        assert updated_ryai.get("tagline") == test_tagline, "Tagline should be updated"
        
        # Restore original tagline
        self.session.put(f"{BASE_URL}/api/ai-assistant/admin/config/ryai", json={
            "tagline": original_tagline or "Technical & Safeguard Intelligence"
        })
        
        print("SUCCESS: Admin updated ryai config successfully")

    def test_admin_add_training_knowledge(self):
        """POST /api/ai-assistant/admin/train - Add knowledge base entry"""
        test_entry = {
            "assistant_id": "ryai",
            "category": "Testing",
            "question": f"TEST: What is the test question? {int(time.time())}",
            "answer": "This is a test answer for the AI assistant knowledge base."
        }
        
        response = self.session.post(f"{BASE_URL}/api/ai-assistant/admin/train", json=test_entry)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("status") == "added", "Should confirm knowledge added"
        
        print("SUCCESS: Added training knowledge entry")

    def test_admin_get_knowledge(self):
        """GET /api/ai-assistant/admin/knowledge - Get knowledge base entries"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/knowledge")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "entries" in data, "Response should contain 'entries' key"
        entries = data["entries"]
        
        # Verify entry structure
        if entries:
            entry = entries[0]
            assert "id" in entry, "Entry should have id"
            assert "assistant_id" in entry, "Entry should have assistant_id"
            assert "question" in entry, "Entry should have question"
            assert "answer" in entry, "Entry should have answer"
            assert "category" in entry, "Entry should have category"
        
        print(f"SUCCESS: Knowledge base has {len(entries)} entries")

    def test_admin_get_knowledge_filtered(self):
        """GET /api/ai-assistant/admin/knowledge?assistant_id=ryai - Filter knowledge"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/knowledge", params={"assistant_id": "ryai"})
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        entries = data.get("entries", [])
        for entry in entries:
            assert entry.get("assistant_id") == "ryai", f"Entry should be for ryai"
        
        print(f"SUCCESS: Filtered knowledge has {len(entries)} ryai entries")

    def test_admin_get_stats(self):
        """GET /api/ai-assistant/admin/stats - Get usage statistics"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/stats")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify stats fields
        expected_fields = ["total_sessions", "total_messages", "pending_unanswered", 
                         "knowledge_entries", "total_interactions", "escalated_count", "escalation_rate"]
        
        for field in expected_fields:
            assert field in data, f"Stats should contain '{field}'"
        
        print(f"SUCCESS: Stats - Sessions: {data['total_sessions']}, Messages: {data['total_messages']}, Knowledge: {data['knowledge_entries']}")

    def test_admin_get_unanswered(self):
        """GET /api/ai-assistant/admin/unanswered - Get unanswered questions"""
        response = self.session.get(f"{BASE_URL}/api/ai-assistant/admin/unanswered")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "items" in data, "Response should contain 'items' key"
        items = data["items"]
        
        if items:
            item = items[0]
            assert "id" in item, "Item should have id"
            assert "question" in item, "Item should have question"
            assert "assistant_id" in item, "Item should have assistant_id"
        
        print(f"SUCCESS: Found {len(items)} unanswered questions")

    def test_delete_session(self):
        """DELETE /api/ai-assistant/sessions/{session_id} - Delete a chat session"""
        # First create a session
        chat_response = self.session.post(f"{BASE_URL}/api/ai-assistant/chat", json={
            "assistant_id": "ryai",
            "message": "This is a test session to delete"
        })
        session_id = chat_response.json().get("session_id")
        
        # Delete the session
        response = self.session.delete(f"{BASE_URL}/api/ai-assistant/sessions/{session_id}")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("status") == "deleted", "Should confirm deletion"
        
        print(f"SUCCESS: Deleted session {session_id[:8]}...")


class TestChatWithZxAI:
    """Test zxAI specifically for chat functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Login failed")

    def test_zxai_chat_response(self):
        """POST /api/ai-assistant/chat with zxAI - Test knowledge assistant"""
        response = self.session.post(f"{BASE_URL}/api/ai-assistant/chat", json={
            "assistant_id": "zxai",
            "message": "What benefits does CrossCurrent offer?"
        })
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["assistant_id"] == "zxai", "Should use zxAI"
        assert "session_id" in data, "Should return session_id"
        assert len(data.get("response", "")) > 0, "Should have a response"
        
        print(f"SUCCESS: zxAI responded with {len(data['response'])} chars")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

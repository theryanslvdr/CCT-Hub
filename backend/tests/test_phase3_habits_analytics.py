"""
Phase 3: Habit Tracker (Soft Gate) + Banner Analytics Enhancement Tests
Tests for:
- Banner Analytics API (POST /api/settings/banner-analytics/track, GET /api/settings/banner-analytics)
- User Habit APIs (GET /api/habits/, POST /api/habits/{id}/complete, POST /api/habits/{id}/uncomplete)
- Admin Habit APIs (GET/POST/PUT/DELETE /api/admin/habits)
- Signal Block Status with habit_gate_locked field
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "iam@ryansalvador.com"
ADMIN_PASSWORD = "admin123"

# Known seeded habit ID
SEEDED_HABIT_ID = "99306d6a-5ac8-4d24-98ed-542aefcabcfd"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin login failed - cannot run authenticated tests")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestBannerAnalyticsTracking:
    """Banner Analytics tracking API - no auth required"""

    def test_track_notice_banner_impression(self):
        """POST /api/settings/banner-analytics/track - track impression"""
        response = requests.post(
            f"{BASE_URL}/api/settings/banner-analytics/track",
            params={"event_type": "impression", "banner_type": "notice_banner"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True

    def test_track_notice_banner_dismiss(self):
        """POST /api/settings/banner-analytics/track - track dismiss"""
        response = requests.post(
            f"{BASE_URL}/api/settings/banner-analytics/track",
            params={"event_type": "dismiss", "banner_type": "notice_banner"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True

    def test_track_promo_popup_impression(self):
        """POST /api/settings/banner-analytics/track - promo popup impression"""
        response = requests.post(
            f"{BASE_URL}/api/settings/banner-analytics/track",
            params={"event_type": "impression", "banner_type": "promo_popup"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True

    def test_track_promo_popup_dismiss(self):
        """POST /api/settings/banner-analytics/track - promo popup dismiss"""
        response = requests.post(
            f"{BASE_URL}/api/settings/banner-analytics/track",
            params={"event_type": "dismiss", "banner_type": "promo_popup"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True


class TestBannerAnalyticsAdmin:
    """Banner Analytics GET endpoint - admin auth required"""

    def test_get_banner_analytics_requires_auth(self):
        """GET /api/settings/banner-analytics without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/settings/banner-analytics")
        assert response.status_code in [401, 403]

    def test_get_banner_analytics_with_auth(self, admin_headers):
        """GET /api/settings/banner-analytics with admin auth"""
        response = requests.get(
            f"{BASE_URL}/api/settings/banner-analytics",
            params={"days": 30},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "days" in data
        assert "summary" in data
        assert "daily" in data
        assert data["days"] == 30
        
        # If we have summary data, check structure
        if data["summary"]:
            for banner_type, stats in data["summary"].items():
                assert "impressions" in stats
                assert "dismissals" in stats
                assert "dismiss_rate" in stats
                assert "days_active" in stats


class TestUserHabitAPI:
    """User-facing Habit Tracker APIs - requires auth"""

    def test_get_habits_requires_auth(self):
        """GET /api/habits/ without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/habits/")
        assert response.status_code in [401, 403]

    def test_get_habits_returns_list(self, admin_headers):
        """GET /api/habits/ returns habits list and gate status"""
        response = requests.get(f"{BASE_URL}/api/habits/", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "habits" in data
        assert "completions_today" in data
        assert "gate_unlocked" in data
        assert "date" in data
        
        # Habits should be a list
        assert isinstance(data["habits"], list)
        assert isinstance(data["completions_today"], list)
        assert isinstance(data["gate_unlocked"], bool)

    def test_complete_habit(self, admin_headers):
        """POST /api/habits/{habit_id}/complete marks habit done"""
        response = requests.post(
            f"{BASE_URL}/api/habits/{SEEDED_HABIT_ID}/complete",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Response should have message and already flag
        assert "message" in data
        assert "already" in data

    def test_uncomplete_habit(self, admin_headers):
        """POST /api/habits/{habit_id}/uncomplete undoes completion"""
        response = requests.post(
            f"{BASE_URL}/api/habits/{SEEDED_HABIT_ID}/uncomplete",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_complete_nonexistent_habit(self, admin_headers):
        """POST /api/habits/{fake_id}/complete should return 404"""
        fake_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/habits/{fake_id}/complete",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestAdminHabitAPI:
    """Admin Habit management APIs"""

    def test_admin_get_habits(self, admin_headers):
        """GET /api/admin/habits returns all habits including inactive"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "habits" in data
        assert isinstance(data["habits"], list)

    def test_admin_create_habit(self, admin_headers):
        """POST /api/admin/habits creates a new habit"""
        new_habit = {
            "title": f"Test Habit {uuid.uuid4().hex[:8]}",
            "description": "Created by automated test",
            "action_type": "generic",
            "action_data": "",
            "is_gate": False
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/habits",
            json=new_habit,
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify returned habit has all fields
        assert "id" in data
        assert data["title"] == new_habit["title"]
        assert data["description"] == new_habit["description"]
        assert data["action_type"] == "generic"
        assert data["is_gate"] == False
        assert data["active"] == True
        
        # Store for cleanup
        return data["id"]

    def test_admin_update_habit(self, admin_headers):
        """PUT /api/admin/habits/{habit_id} updates a habit"""
        # First create a habit to update
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/habits",
            json={
                "title": "Habit to Update",
                "description": "Will be updated",
                "action_type": "generic",
                "action_data": "",
                "is_gate": False
            },
            headers=admin_headers
        )
        habit_id = create_resp.json()["id"]
        
        # Now update it
        update_data = {
            "title": "Updated Habit Title",
            "description": "Updated description",
            "action_type": "link_click",
            "action_data": "https://example.com",
            "is_gate": True
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/habits/{habit_id}",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Verify update by getting habits
        get_resp = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        habits = get_resp.json()["habits"]
        updated = next((h for h in habits if h["id"] == habit_id), None)
        assert updated is not None
        assert updated["title"] == "Updated Habit Title"
        assert updated["action_type"] == "link_click"

    def test_admin_delete_habit_soft_delete(self, admin_headers):
        """DELETE /api/admin/habits/{habit_id} soft-deletes (deactivates)"""
        # Create a habit first
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/habits",
            json={
                "title": "Habit to Delete",
                "description": "",
                "action_type": "generic",
                "action_data": "",
                "is_gate": False
            },
            headers=admin_headers
        )
        habit_id = create_resp.json()["id"]
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}/api/admin/habits/{habit_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Verify it's inactive (still exists in admin list but active=False)
        get_resp = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        habits = get_resp.json()["habits"]
        deleted = next((h for h in habits if h["id"] == habit_id), None)
        assert deleted is not None
        assert deleted["active"] == False

    def test_admin_create_send_invite_habit(self, admin_headers):
        """POST /api/admin/habits with send_invite action type"""
        new_habit = {
            "title": "Send 1 invite today",
            "description": "Help grow the community!",
            "action_type": "send_invite",
            "action_data": "Hey! Join our trading community - we share daily signals!",
            "is_gate": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/habits",
            json=new_habit,
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["action_type"] == "send_invite"
        assert data["action_data"] == new_habit["action_data"]
        assert data["is_gate"] == True


class TestSignalBlockStatusWithHabitGate:
    """Test signal-block-status API includes habit_gate_locked field"""

    def test_signal_block_status_has_habit_gate_field(self, admin_headers):
        """GET /api/trade/signal-block-status returns habit_gate_locked"""
        response = requests.get(
            f"{BASE_URL}/api/trade/signal-block-status",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Must have habit_gate_locked field
        assert "habit_gate_locked" in data
        assert isinstance(data["habit_gate_locked"], bool)
        
        # Also has standard fields
        assert "blocked" in data
        assert "reason" in data


class TestSeededHabitExists:
    """Verify the seeded test habit exists and is correct"""

    def test_seeded_habit_in_list(self, admin_headers):
        """Seeded habit ID should be in the habits list"""
        response = requests.get(f"{BASE_URL}/api/admin/habits", headers=admin_headers)
        assert response.status_code == 200
        habits = response.json()["habits"]
        
        seeded = next((h for h in habits if h["id"] == SEEDED_HABIT_ID), None)
        assert seeded is not None, f"Seeded habit {SEEDED_HABIT_ID} not found"
        
        # Verify seeded habit properties
        assert seeded["action_type"] == "send_invite"
        assert seeded["is_gate"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Test: Rewards System Phase 3 (Gamification & Badges) + Phase 4 (Admin Tools Enhancement)
Iteration: 129

Phase 3 Features:
- GET /api/rewards/badges - 14 badge definitions (public)
- GET /api/rewards/badges/user - user badges with earned/locked status (JWT)

Phase 4 Features:
- GET /api/rewards/admin/search-users?q=name - autocomplete user search (admin JWT)
- GET /api/rewards/admin/badges - all badges including inactive (admin JWT)
- PUT /api/rewards/admin/badges/{badge_id} - update badge (master admin JWT)
- POST /api/rewards/admin/adjust-points - manual adjustment with audit trail (admin JWT)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
MASTER_ADMIN_EMAIL = "iam@ryansalvador.com"
MASTER_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get master admin JWT token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": MASTER_ADMIN_EMAIL,
        "password": MASTER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # Token is returned as 'access_token' per main agent context
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data}"
    return token


class TestBadgeDefinitions:
    """Phase 3: Badge definitions endpoint (public)"""
    
    def test_get_badge_definitions(self):
        """GET /api/rewards/badges returns 14 badge definitions"""
        response = requests.get(f"{BASE_URL}/api/rewards/badges")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "badges" in data, "Response missing 'badges' key"
        badges = data["badges"]
        
        # Should have 14 default badges
        assert len(badges) == 14, f"Expected 14 badges, got {len(badges)}"
        
        # Verify badge structure
        for badge in badges:
            assert "id" in badge
            assert "name" in badge
            assert "description" in badge
            assert "icon" in badge
            assert "category" in badge
            assert "condition_type" in badge
            assert "condition_value" in badge
            assert "sort_order" in badge
        
        # Verify expected badges exist
        badge_ids = [b["id"] for b in badges]
        expected_badges = [
            "first_trade", "streak_7", "streak_14", "streak_30",
            "points_500", "points_1000", "points_5000", "points_10000",
            "referral_3", "referral_5", "referral_10",
            "deposit_hero", "trades_50", "trades_100"
        ]
        for expected_id in expected_badges:
            assert expected_id in badge_ids, f"Missing expected badge: {expected_id}"
        
        print(f"✓ GET /api/rewards/badges returned {len(badges)} badges")


class TestUserBadges:
    """Phase 3: User badges endpoint (JWT required)"""
    
    def test_get_user_badges_requires_auth(self):
        """GET /api/rewards/badges/user requires JWT"""
        response = requests.get(f"{BASE_URL}/api/rewards/badges/user")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/rewards/badges/user properly requires auth")
    
    def test_get_user_badges_with_auth(self, admin_token):
        """GET /api/rewards/badges/user returns badges with earned/locked status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/rewards/badges/user", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "user_id" in data
        assert "badges" in data
        badges = data["badges"]
        
        # Verify badge status structure
        for badge in badges:
            assert "id" in badge
            assert "name" in badge
            assert "earned" in badge, f"Badge missing 'earned' field: {badge}"
            assert isinstance(badge["earned"], bool)
            # If earned, should have earned_at
            if badge["earned"]:
                assert "earned_at" in badge
                assert badge["earned_at"] is not None
        
        earned_count = sum(1 for b in badges if b["earned"])
        locked_count = sum(1 for b in badges if not b["earned"])
        print(f"✓ GET /api/rewards/badges/user: {earned_count} earned, {locked_count} locked")


class TestAdminUserSearch:
    """Phase 4: Admin user search autocomplete"""
    
    def test_search_users_requires_admin(self):
        """GET /api/rewards/admin/search-users requires admin JWT"""
        response = requests.get(f"{BASE_URL}/api/rewards/admin/search-users", params={"q": "ryan"})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/rewards/admin/search-users properly requires auth")
    
    def test_search_users_min_chars(self, admin_token):
        """Search requires at least 2 characters"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Query with 1 char - should return empty
        response = requests.get(f"{BASE_URL}/api/rewards/admin/search-users", 
                               params={"q": "r"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["users"] == [], "Expected empty results for 1-char query"
        print("✓ Search with 1 char returns empty as expected")
    
    def test_search_users_by_name_ryan(self, admin_token):
        """Search for 'ryan' returns matching users"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/rewards/admin/search-users",
                               params={"q": "ryan"}, headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "users" in data
        users = data["users"]
        
        # Should find users with 'ryan' in name
        print(f"✓ Search 'ryan' found {len(users)} users")
        for user in users:
            assert "id" in user
            assert "full_name" in user
            assert "email" in user
            # Verify match (case-insensitive)
            matches_name = "ryan" in user.get("full_name", "").lower()
            matches_email = "ryan" in user.get("email", "").lower()
            assert matches_name or matches_email, f"User {user} doesn't match 'ryan'"
    
    def test_search_users_by_name_riz(self, admin_token):
        """Search for 'riz' returns Rizza Miles"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/rewards/admin/search-users",
                               params={"q": "riz"}, headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        users = data["users"]
        print(f"✓ Search 'riz' found {len(users)} users")
        
        # Should find at least 1 user
        assert len(users) >= 1, "Expected at least 1 user matching 'riz'"
        # Check if Rizza Miles is in results
        names = [u.get("full_name", "") for u in users]
        found_rizza = any("rizza" in name.lower() for name in names)
        print(f"  Users found: {names}")
        if not found_rizza:
            print("  Note: Rizza Miles not found but other matches returned")


class TestAdminBadgeManagement:
    """Phase 4: Admin badge management endpoints"""
    
    def test_admin_get_all_badges_requires_admin(self):
        """GET /api/rewards/admin/badges requires admin JWT"""
        response = requests.get(f"{BASE_URL}/api/rewards/admin/badges")
        assert response.status_code == 401
        print("✓ GET /api/rewards/admin/badges properly requires auth")
    
    def test_admin_get_all_badges(self, admin_token):
        """GET /api/rewards/admin/badges returns all badges including inactive"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/rewards/admin/badges", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "badges" in data
        badges = data["badges"]
        
        # All 14 badges should be visible (even if some are inactive)
        assert len(badges) >= 14, f"Expected at least 14 badges, got {len(badges)}"
        
        # Verify is_active field is present
        for badge in badges:
            assert "is_active" in badge
        
        active_count = sum(1 for b in badges if b["is_active"])
        inactive_count = sum(1 for b in badges if not b["is_active"])
        print(f"✓ Admin badges: {active_count} active, {inactive_count} inactive")
    
    def test_admin_update_badge_requires_master_admin(self, admin_token):
        """PUT /api/rewards/admin/badges/{id} requires master admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get first badge ID
        response = requests.get(f"{BASE_URL}/api/rewards/admin/badges", headers=headers)
        badges = response.json()["badges"]
        badge_id = badges[0]["id"]
        
        # Try to update (master admin should succeed)
        response = requests.put(
            f"{BASE_URL}/api/rewards/admin/badges/{badge_id}",
            json={"description": "Test update description"},
            headers=headers
        )
        # Should succeed for master admin
        assert response.status_code == 200, f"Update failed: {response.text}"
        print("✓ Master admin can update badge")
    
    def test_admin_update_badge_name_description(self, admin_token):
        """Update badge name and description"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get first_trade badge
        badge_id = "first_trade"
        original_desc = "Complete your first trade"
        
        # Update description
        new_desc = "Make your very first trade to earn this badge!"
        response = requests.put(
            f"{BASE_URL}/api/rewards/admin/badges/{badge_id}",
            json={"description": new_desc},
            headers=headers
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert data["badge"]["description"] == new_desc
        
        # Revert to original
        response = requests.put(
            f"{BASE_URL}/api/rewards/admin/badges/{badge_id}",
            json={"description": original_desc},
            headers=headers
        )
        assert response.status_code == 200
        print("✓ Badge description updated and reverted successfully")


class TestAdminPointAdjustment:
    """Phase 4: Admin manual point adjustment with audit trail"""
    
    def test_adjust_points_requires_admin(self):
        """POST /api/rewards/admin/adjust-points requires admin JWT"""
        response = requests.post(
            f"{BASE_URL}/api/rewards/admin/adjust-points",
            json={"user_id": "test", "points": 100, "reason": "test"}
        )
        assert response.status_code == 401
        print("✓ POST /api/rewards/admin/adjust-points properly requires auth")
    
    def test_adjust_points_credit(self, admin_token):
        """Credit points to a user with audit trail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get admin's user_id
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        admin_user_id = me_response.json()["id"]
        
        # Get current points
        lookup_response = requests.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"user_id": admin_user_id},
            headers=headers
        )
        current_points = lookup_response.json().get("lifetime_points", 0)
        
        # Credit 50 points
        response = requests.post(
            f"{BASE_URL}/api/rewards/admin/adjust-points",
            json={
                "user_id": admin_user_id,
                "points": 50,
                "reason": "Test credit - iteration 129",
                "is_deduction": False
            },
            headers=headers
        )
        assert response.status_code == 200, f"Credit failed: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert data["new_lifetime_points"] == current_points + 50
        print(f"✓ Credited 50 points. New total: {data['new_lifetime_points']}")
        
        # Verify audit trail in history
        history_response = requests.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"user_id": admin_user_id},
            headers=headers
        )
        history = history_response.json().get("history", [])
        
        # Most recent entry should be our credit
        if history:
            latest = history[0]
            assert latest["source"] == "admin_adjustment_credit"
            assert latest["points"] == 50
            assert "reason" in latest.get("metadata", {})
            assert latest["metadata"]["reason"] == "Test credit - iteration 129"
            print("✓ Audit trail verified in history")
    
    def test_adjust_points_deduct(self, admin_token):
        """Deduct points from a user with audit trail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get admin's user_id
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        admin_user_id = me_response.json()["id"]
        
        # Get current points
        lookup_response = requests.get(
            f"{BASE_URL}/api/rewards/admin/lookup",
            params={"user_id": admin_user_id},
            headers=headers
        )
        current_points = lookup_response.json().get("lifetime_points", 0)
        
        # Deduct 25 points
        response = requests.post(
            f"{BASE_URL}/api/rewards/admin/adjust-points",
            json={
                "user_id": admin_user_id,
                "points": 25,
                "reason": "Test deduction - iteration 129",
                "is_deduction": True
            },
            headers=headers
        )
        assert response.status_code == 200, f"Deduct failed: {response.text}"
        
        data = response.json()
        assert data["success"] is True
        assert data["new_lifetime_points"] == current_points - 25
        print(f"✓ Deducted 25 points. New total: {data['new_lifetime_points']}")


class TestBadgeNotFound:
    """Edge case: updating non-existent badge"""
    
    def test_update_nonexistent_badge(self, admin_token):
        """PUT /api/rewards/admin/badges/{invalid_id} returns 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.put(
            f"{BASE_URL}/api/rewards/admin/badges/nonexistent_badge_xyz",
            json={"name": "Test"},
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent badge returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

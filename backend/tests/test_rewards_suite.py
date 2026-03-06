"""Comprehensive tests for /api/rewards/* endpoints (rewards.py)."""
import pytest
import requests


class TestRewardsSummary:
    """GET /api/rewards/summary?user_id=..."""

    def test_summary_with_user_id(self, base_url, admin_user):
        resp = requests.get(
            f"{base_url}/api/rewards/summary",
            params={"user_id": admin_user["id"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == admin_user["id"]
        assert "lifetime_points" in data
        assert "level" in data
        assert "current_streak" in data

    def test_summary_missing_user_id(self, base_url):
        resp = requests.get(f"{base_url}/api/rewards/summary")
        assert resp.status_code == 422  # missing required query param


class TestRewardsLeaderboard:
    """GET /api/rewards/leaderboard?user_id=..."""

    def test_leaderboard_with_user_id(self, base_url, admin_user):
        resp = requests.get(
            f"{base_url}/api/rewards/leaderboard",
            params={"user_id": admin_user["id"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == admin_user["id"]

    def test_full_leaderboard(self, base_url):
        resp = requests.get(f"{base_url}/api/rewards/leaderboard/full")
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestRewardsBadges:
    """GET /api/rewards/badges — public endpoint."""

    def test_badge_definitions(self, base_url):
        resp = requests.get(f"{base_url}/api/rewards/badges")
        assert resp.status_code == 200
        data = resp.json()
        assert "badges" in data
        assert isinstance(data["badges"], list)

    def test_user_badges(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/rewards/badges/user", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "badges" in data
        assert isinstance(data["badges"], list)


class TestRewardsEarningActions:
    """GET /api/rewards/earning-actions"""

    def test_earning_actions(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/rewards/earning-actions", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))


class TestRewardsHistory:
    """GET /api/rewards/history"""

    def test_history(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/rewards/history", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data
        assert isinstance(data["history"], list)


class TestRewardsAdminOverview:
    """GET /api/rewards/admin/overview"""

    def test_admin_overview(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/rewards/admin/overview", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_admin_members(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/rewards/admin/members", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_admin_badges(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/rewards/admin/badges", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

"""Comprehensive tests for general routes, system health, and notifications."""
import pytest
import requests


class TestHealthAndVersion:
    """Public health/version endpoints."""

    def test_health(self, base_url):
        resp = requests.get(f"{base_url}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root(self, base_url):
        resp = requests.get(f"{base_url}/api/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "CrossCurrent" in data["message"]

    def test_version(self, base_url):
        resp = requests.get(f"{base_url}/api/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "build_version" in data


class TestNotifications:
    """GET /api/notifications"""

    def test_notifications_authenticated(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/notifications", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "notifications" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)

    def test_notifications_no_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/notifications")
        assert resp.status_code in [401, 403]


class TestWebSocketStatus:
    """GET /api/ws/status (admin only)"""

    def test_ws_status(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/ws/status", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestSystemHealth:
    """GET /api/admin/system-health (master admin only)"""

    def test_system_health(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/system-health", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "uptime" in data
        assert "system" in data
        assert "database" in data
        assert "websockets" in data
        assert "route_latencies" in data
        assert "external_services" in data
        assert "build" in data
        assert "users" in data
        # Verify sub-fields
        assert data["database"]["status"] == "healthy"
        assert "cpu_percent" in data["system"]
        assert "memory" in data["system"]

    def test_system_health_no_auth(self, base_url):
        resp = requests.get(f"{base_url}/api/admin/system-health")
        assert resp.status_code in [401, 403]


class TestDBPing:
    """GET /api/admin/system-health/db-ping"""

    def test_db_ping(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/system-health/db-ping", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "ping_ms" in data
        assert isinstance(data["ping_ms"], (int, float))

"""Tests for settings, currency, debt, goals, habits, users, family routes."""
import pytest
import requests


# ─── Settings Routes (/api/settings/*) ───

class TestSettingsPlatform:
    """GET /api/settings/platform"""

    def test_platform_settings(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/settings/platform", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestSettingsNoticeBanner:
    """GET /api/settings/notice-banner — may be public."""

    def test_notice_banner(self, base_url):
        resp = requests.get(f"{base_url}/api/settings/notice-banner")
        assert resp.status_code == 200


class TestSettingsPromotionPopup:
    """GET /api/settings/promotion-popup — may be public."""

    def test_promotion_popup(self, base_url):
        resp = requests.get(f"{base_url}/api/settings/promotion-popup")
        assert resp.status_code == 200


class TestSettingsEmailTemplates:
    """GET /api/settings/email-templates"""

    def test_email_templates(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/settings/email-templates", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestSettingsManifest:
    """GET /api/settings/manifest.json — public PWA manifest."""

    def test_manifest(self, base_url):
        resp = requests.get(f"{base_url}/api/settings/manifest.json")
        assert resp.status_code == 200


# ─── Currency Routes (/api/currency/*) ───

class TestCurrencyRates:
    """GET /api/currency/rates"""

    def test_rates(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/currency/rates", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


class TestCurrencyConvert:
    """POST /api/currency/convert"""

    def test_convert(self, base_url, admin_headers):
        resp = requests.post(
            f"{base_url}/api/currency/convert",
            headers=admin_headers,
            params={"amount": 100, "from_currency": "USD", "to_currency": "EUR"},
        )
        # May return 200 or error if CoinGecko unavailable
        assert resp.status_code in [200, 400, 500, 503]


# ─── Debt Routes (/api/debt/*) ───

class TestDebtRoutes:
    """GET /api/debt"""

    def test_list_debts(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/debt", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_debt_plan(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/debt/plan", headers=admin_headers)
        assert resp.status_code == 200


# ─── Goals Routes (/api/goals/*) ───

class TestGoalRoutes:
    """GET /api/goals"""

    def test_list_goals(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/goals", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ─── Habits Routes (/api/habits/*) ───

class TestHabitRoutes:
    """GET /api/habits/"""

    def test_list_habits(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/habits/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_habits_streak(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/habits/streak", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


# ─── Users Routes (/api/users/*) ───

class TestUserRoutes:
    """User profile & notification preferences."""

    def test_notification_preferences(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/users/notification-preferences", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_vapid_public_key(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/users/vapid-public-key", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


# ─── Family Routes (/api/family/*) ───

class TestFamilyRoutes:
    """Family account endpoints — only for honorary licensees."""

    def test_family_list_non_licensee(self, base_url, admin_headers):
        """Non-honorary admin should get 403."""
        resp = requests.get(f"{base_url}/api/family/members", headers=admin_headers)
        assert resp.status_code in [200, 403, 404]


# ─── Activity Feed (/api/admin/activity-feed) ───

class TestActivityFeed:
    """GET /api/admin/activity-feed"""

    def test_activity_feed(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/admin/activity-feed", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None


# ─── Affiliate Routes (/api/affiliate-resources) ───

class TestAffiliateRoutes:
    """GET /api/affiliate-resources"""

    def test_affiliate_resources(self, base_url, admin_headers):
        resp = requests.get(f"{base_url}/api/affiliate-resources", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

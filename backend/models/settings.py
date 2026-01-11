"""Settings-related Pydantic models"""
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class PlatformSettings(BaseModel):
    platform_name: str = "CrossCurrent"
    tagline: str = "Finance Center"
    site_title: str = "CrossCurrent Finance Center"
    site_description: str = "Trading profit management platform"
    favicon_url: Optional[str] = None
    logo_url: Optional[str] = None
    og_image_url: Optional[str] = None
    primary_color: str = "#3B82F6"
    accent_color: str = "#06B6D4"
    hide_emergent_badge: bool = False
    # Login Customization
    login_title: Optional[str] = None
    login_tagline: Optional[str] = None
    login_notice: str = "Only CrossCurrent community members can access this platform."
    # Production URL
    production_site_url: Optional[str] = None
    # Integration API Keys
    emailit_api_key: Optional[str] = None
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    heartbeat_api_key: Optional[str] = None
    # Custom Links
    custom_registration_link: Optional[str] = None
    # Footer Settings
    footer_copyright: str = "© 2024 CrossCurrent Finance Center. All rights reserved."
    footer_links: Optional[List[dict]] = None  # [{label: "Privacy", url: "/privacy"}, ...]


class EmailTemplateType(str, Enum):
    WELCOME = "welcome"
    FORGOT_PASSWORD = "forgot_password"
    TRADE_NOTIFICATION = "trade_notification"
    MISSED_TRADE = "missed_trade"
    LICENSE_INVITE = "license_invite"
    ADMIN_NOTIFICATION = "admin_notification"
    SUPER_ADMIN_NOTIFICATION = "super_admin_notification"


class EmailTemplateUpdate(BaseModel):
    subject: str
    body: str
    variables: Optional[List[str]] = None  # Available template variables like {{name}}, {{link}}

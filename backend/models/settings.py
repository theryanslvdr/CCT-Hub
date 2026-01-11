from pydantic import BaseModel
from typing import Optional
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
    # Integration API Keys
    emailit_api_key: Optional[str] = None
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    heartbeat_api_key: Optional[str] = None
    # Custom Links
    custom_registration_link: Optional[str] = None

class EmailTemplateType(str, Enum):
    welcome = "welcome"
    password_reset = "password_reset"
    license_invite = "license_invite"
    license_activated = "license_activated"
    deposit_approved = "deposit_approved"
    withdrawal_completed = "withdrawal_completed"
    notification = "notification"

class EmailTemplateUpdate(BaseModel):
    subject: str
    body: str

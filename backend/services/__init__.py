"""Backend Services Package"""

from .email_service import (
    send_email,
    get_emailit_api_key,
    get_license_invite_email,
    get_admin_notification_email,
    get_password_reset_email,
    get_trade_alert_email,
)

from .file_service import (
    upload_file,
    delete_file,
    get_user_files,
    upload_profile_picture,
    upload_deposit_screenshot,
    get_cloudinary_config,
)

__all__ = [
    # Email service
    "send_email",
    "get_emailit_api_key",
    "get_license_invite_email",
    "get_admin_notification_email",
    "get_password_reset_email",
    "get_trade_alert_email",
    # File service
    "upload_file",
    "delete_file",
    "get_user_files",
    "upload_profile_picture",
    "upload_deposit_screenshot",
    "get_cloudinary_config",
]

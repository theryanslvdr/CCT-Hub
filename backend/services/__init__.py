"""Backend Services Package"""

from .email_service import (
    send_email,
    get_emailit_api_key,
    get_license_invite_email,
    get_admin_notification_email,
    get_password_reset_email,
    get_trade_alert_email,
    get_welcome_email,
    get_transaction_update_email,
    get_missed_trade_email,
    get_weekly_summary_email,
)

from .file_service import (
    upload_file,
    delete_file,
    get_user_files,
    upload_profile_picture,
    upload_deposit_screenshot,
    get_cloudinary_config,
)

from .websocket_service import (
    manager as websocket_manager,
    NotificationType,
    create_notification,
    notify_admins_deposit_request,
    notify_admins_withdrawal_request,
    notify_user_transaction_status,
    notify_trade_signal,
    notify_system_announcement,
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
    # WebSocket service
    "websocket_manager",
    "NotificationType",
    "create_notification",
    "notify_admins_deposit_request",
    "notify_admins_withdrawal_request",
    "notify_user_transaction_status",
    "notify_trade_signal",
    "notify_system_announcement",
]

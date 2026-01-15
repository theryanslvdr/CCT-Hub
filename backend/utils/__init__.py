"""Backend Utilities Package"""

from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_role_level,
    check_role_permission,
    get_role_from_secret_code,
    is_admin_role,
    is_master_admin,
    is_super_admin_or_above,
    ROLE_HIERARCHY,
    SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SUPER_ADMIN_SECRET,
    MASTER_ADMIN_SECRET,
    SUPER_ADMIN_BYPASS,
)

from .calculations import (
    calculate_account_value,
    get_user_financial_summary,
    calculate_lot_size,
    calculate_projected_profit,
    calculate_profit_difference,
    determine_performance,
    calculate_performance_rate,
    calculate_withdrawal_fees,
    calculate_quarterly_profit,
    format_currency,
    get_trading_day_range,
)

__all__ = [
    # Auth utilities
    "hash_password", "verify_password", "create_access_token", "decode_token",
    "get_role_level", "check_role_permission", "get_role_from_secret_code",
    "is_admin_role", "is_master_admin", "is_super_admin_or_above",
    "ROLE_HIERARCHY", "SECRET_KEY", "JWT_ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES",
    "SUPER_ADMIN_SECRET", "MASTER_ADMIN_SECRET", "SUPER_ADMIN_BYPASS",
    # Calculation utilities
    "calculate_account_value", "get_user_financial_summary",
    "calculate_lot_size", "calculate_projected_profit", "calculate_profit_difference",
    "determine_performance", "calculate_performance_rate", "calculate_withdrawal_fees",
    "calculate_quarterly_profit", "format_currency", "get_trading_day_range",
]

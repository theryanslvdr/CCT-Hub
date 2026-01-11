"""Backend Models Package - Pydantic models for API request/response"""

# User models
from .user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    ProfileUpdate,
    PasswordChange,
    VerifyPasswordRequest,
    HeartbeatVerifyRequest,
    SetPasswordRequest,
    SecretUpgradeRequest,
    RoleUpgrade,
    AdminUserUpdate,
    TempPasswordSet,
)

# Trade models
from .trade import (
    TradeLogCreate,
    TradeLogResponse,
    TradingSignalCreate,
    TradingSignalUpdate,
    TradingSignalResponse,
    UpdateTradeTimeEntered,
)

# Common models
from .common import (
    DepositCreate,
    DepositResponse,
    WithdrawalRequest,
    WithdrawalSimulation,
    ConfirmReceiptRequest,
    DebtCreate,
    DebtResponse,
    GoalCreate,
    GoalResponse,
    NotificationCreate,
    NotificationResponse,
    APIConnectionCreate,
    APIConnectionResponse,
)

# License models
from .license import (
    LicenseType,
    LicenseCreate,
    LicenseResponse,
    LicenseInviteCreate,
    LicenseInviteUpdate,
    LicenseeTransactionStatus,
    LicenseeDepositCreate,
    LicenseeWithdrawalCreate,
    LicenseeTransactionFeedback,
)

# Settings models
from .settings import (
    PlatformSettings,
    EmailTemplateType,
    EmailTemplateUpdate,
)

__all__ = [
    # User
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse",
    "ProfileUpdate", "PasswordChange", "VerifyPasswordRequest",
    "HeartbeatVerifyRequest", "SetPasswordRequest", "SecretUpgradeRequest",
    "RoleUpgrade", "AdminUserUpdate", "TempPasswordSet",
    # Trade
    "TradeLogCreate", "TradeLogResponse", "TradingSignalCreate",
    "TradingSignalUpdate", "TradingSignalResponse", "UpdateTradeTimeEntered",
    # Common
    "DepositCreate", "DepositResponse", "WithdrawalRequest", "WithdrawalSimulation",
    "ConfirmReceiptRequest", "DebtCreate", "DebtResponse", "GoalCreate",
    "GoalResponse", "NotificationCreate", "NotificationResponse",
    "APIConnectionCreate", "APIConnectionResponse",
    # License
    "LicenseType", "LicenseCreate", "LicenseResponse", "LicenseInviteCreate",
    "LicenseInviteUpdate", "LicenseeTransactionStatus", "LicenseeDepositCreate",
    "LicenseeWithdrawalCreate", "LicenseeTransactionFeedback",
    # Settings
    "PlatformSettings", "EmailTemplateType", "EmailTemplateUpdate",
]

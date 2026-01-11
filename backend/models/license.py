"""License-related Pydantic models"""
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class LicenseType(str, Enum):
    STANDARD = "standard"
    EXTENDED = "extended"
    HONORARY = "honorary"


class LicenseCreate(BaseModel):
    user_id: str
    license_type: str  # extended or honorary
    starting_amount: float
    start_date: Optional[str] = None  # YYYY-MM-DD format
    notes: Optional[str] = None


class LicenseResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    license_type: str
    starting_amount: float
    current_amount: float
    start_date: str
    notes: Optional[str] = None
    is_active: bool
    created_at: str
    created_by: str


class LicenseInviteCreate(BaseModel):
    license_type: str  # extended or honorary
    starting_amount: float
    valid_duration: str  # 3_months, 6_months, 1_year, indefinite
    max_uses: int = 1
    notes: Optional[str] = None
    invitee_email: Optional[str] = None
    invitee_name: Optional[str] = None


class LicenseInviteUpdate(BaseModel):
    valid_duration: Optional[str] = None
    max_uses: Optional[int] = None
    notes: Optional[str] = None
    invitee_email: Optional[str] = None
    invitee_name: Optional[str] = None


class LicenseeTransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    REJECTED = "rejected"


class LicenseeDepositCreate(BaseModel):
    amount: float
    deposit_date: str
    notes: Optional[str] = None
    # screenshot_url will be added after file upload


class LicenseeWithdrawalCreate(BaseModel):
    amount: float
    notes: Optional[str] = None


class LicenseeTransactionFeedback(BaseModel):
    message: str
    status: Optional[str] = None  # pending, processing, awaiting_confirmation, completed, rejected
    final_amount: Optional[float] = None
    # screenshot_url will be added after file upload

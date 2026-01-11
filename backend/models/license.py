from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class LicenseType(str, Enum):
    extended = "extended"
    honorary = "honorary"

class LicenseCreate(BaseModel):
    user_id: str
    license_type: str
    starting_amount: float
    start_date: Optional[str] = None
    notes: Optional[str] = None

class LicenseResponse(BaseModel):
    id: str
    user_id: str
    license_type: str
    starting_amount: float
    current_amount: float
    start_date: str
    is_active: bool
    notes: Optional[str] = None
    created_at: str
    created_by: str

class LicenseInviteCreate(BaseModel):
    email: str
    license_type: str
    starting_amount: float
    notes: Optional[str] = None
    duration_days: int = 365
    temp_password: Optional[str] = None

class LicenseInviteUpdate(BaseModel):
    starting_amount: Optional[float] = None
    license_type: Optional[str] = None
    notes: Optional[str] = None
    duration_days: Optional[int] = None

class LicenseeTransactionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    awaiting_confirmation = "awaiting_confirmation"
    completed = "completed"
    rejected = "rejected"

class LicenseeDepositCreate(BaseModel):
    amount: float
    deposit_date: str
    notes: Optional[str] = None

class LicenseeWithdrawalCreate(BaseModel):
    amount: float
    notes: Optional[str] = None

class LicenseeTransactionFeedback(BaseModel):
    transaction_id: str
    feedback: str
    new_status: Optional[str] = None

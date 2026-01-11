"""Common Pydantic models (deposits, debts, goals, notifications, etc.)"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class DepositCreate(BaseModel):
    amount: float
    product: str = "MOIL10"
    currency: str = "USDT"
    notes: Optional[str] = None


class DepositResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    product: Optional[str] = "MOIL10"  # Made optional with default for withdrawals
    currency: str
    notes: Optional[str]
    created_at: datetime


class WithdrawalRequest(BaseModel):
    amount: float
    notes: Optional[str] = ""


class WithdrawalSimulation(BaseModel):
    amount: float
    from_currency: str = "USDT"
    to_currency: str = "USD"


class ConfirmReceiptRequest(BaseModel):
    confirmed_at: str


class DebtCreate(BaseModel):
    name: str
    total_amount: float
    minimum_payment: float
    due_day: int
    interest_rate: Optional[float] = 0
    currency: str = "USD"


class DebtResponse(BaseModel):
    id: str
    user_id: str
    name: str
    total_amount: float
    remaining_amount: float
    minimum_payment: float
    due_day: int
    interest_rate: float
    currency: str
    created_at: datetime


class GoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: Optional[float] = 0
    target_date: Optional[datetime] = None
    price_type: str = "fixed"  # fixed or market
    market_item: Optional[str] = None
    currency: str = "USD"


class GoalResponse(BaseModel):
    id: str
    user_id: str
    name: str
    target_amount: float
    current_amount: float
    target_date: Optional[datetime]
    price_type: str
    market_item: Optional[str]
    currency: str
    progress_percentage: float
    created_at: datetime


class NotificationCreate(BaseModel):
    type: str  # deposit, withdrawal, trade_underperform
    title: str
    message: str
    user_id: str  # The user who triggered the notification
    user_name: str
    amount: Optional[float] = None
    metadata: Optional[Dict] = None


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    user_id: str
    user_name: str
    amount: Optional[float] = None
    metadata: Optional[Dict] = None
    is_read: bool = False
    created_at: datetime


class APIConnectionCreate(BaseModel):
    name: str
    endpoint_url: str
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    is_active: bool = True


class APIConnectionResponse(BaseModel):
    id: str
    name: str
    endpoint_url: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DepositCreate(BaseModel):
    amount: float
    type: str = "deposit"
    notes: Optional[str] = None

class DepositResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    type: str
    notes: Optional[str] = None
    created_at: datetime

class DebtCreate(BaseModel):
    creditor: str
    original_amount: float
    current_balance: float
    interest_rate: float = 0
    due_date: Optional[str] = None
    notes: Optional[str] = None

class DebtResponse(BaseModel):
    id: str
    user_id: str
    creditor: str
    original_amount: float
    current_balance: float
    interest_rate: float
    due_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    payments: list = []

class GoalCreate(BaseModel):
    title: str
    target_amount: float
    target_date: Optional[str] = None
    notes: Optional[str] = None

class GoalResponse(BaseModel):
    id: str
    user_id: str
    title: str
    target_amount: float
    current_amount: float = 0
    target_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    is_achieved: bool = False

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str
    user_id: Optional[str] = None
    metadata: Optional[dict] = None

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    created_at: str
    is_read: bool = False
    user_id: Optional[str] = None
    metadata: Optional[dict] = None

class APIConnectionCreate(BaseModel):
    provider: str
    endpoint_url: str
    api_key: Optional[str] = None
    additional_config: Optional[dict] = None

class APIConnectionResponse(BaseModel):
    id: str
    provider: str
    endpoint_url: str
    is_connected: bool
    last_checked: Optional[str] = None

class WithdrawalSimulation(BaseModel):
    amount: float
    to_currency: str = "USD"

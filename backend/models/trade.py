from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TradeLogCreate(BaseModel):
    projected_exit: float
    actual_profit: float
    lot_size: float
    signal_id: Optional[str] = None

class TradeLogResponse(BaseModel):
    id: str
    user_id: str
    projected_exit: float
    actual_profit: float
    lot_size: float
    signal_id: Optional[str] = None
    created_at: datetime

class TradingSignalCreate(BaseModel):
    direction: str
    trade_time: str
    trade_timezone: str = "Asia/Manila"
    multiplier: float = 15.0
    notes: Optional[str] = None
    countdown_seconds: int = 60

class TradingSignalUpdate(BaseModel):
    direction: Optional[str] = None
    trade_time: Optional[str] = None
    trade_timezone: Optional[str] = None
    multiplier: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    countdown_seconds: Optional[int] = None

class TradingSignalResponse(BaseModel):
    id: str
    direction: str
    trade_time: str
    trade_timezone: str
    multiplier: float
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    created_by: str
    countdown_seconds: int = 60

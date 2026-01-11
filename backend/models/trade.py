"""Trade-related Pydantic models"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TradeLogCreate(BaseModel):
    lot_size: float
    direction: str  # BUY or SELL
    actual_profit: float
    notes: Optional[str] = None


class TradeLogResponse(BaseModel):
    id: str
    user_id: str
    lot_size: float
    direction: str
    projected_profit: float
    actual_profit: float
    profit_difference: float
    performance: str
    signal_id: Optional[str]
    created_at: datetime


class TradingSignalCreate(BaseModel):
    product: str = "MOIL10"
    trade_time: str  # HH:MM format
    trade_timezone: str = "Asia/Manila"  # Default to Philippine time
    direction: str  # BUY or SELL
    profit_points: float = 15  # Default profit multiplier
    notes: Optional[str] = None


class TradingSignalUpdate(BaseModel):
    trade_time: Optional[str] = None
    trade_timezone: Optional[str] = None
    direction: Optional[str] = None
    profit_points: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TradingSignalResponse(BaseModel):
    id: str
    product: str
    trade_time: str
    trade_timezone: str
    direction: str
    profit_points: float
    notes: Optional[str]
    is_active: bool
    is_simulated: bool = False
    created_by: str
    created_at: datetime


class UpdateTradeTimeEntered(BaseModel):
    time_entered: str  # HH:MM format

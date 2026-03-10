"""Trade monitoring routes - extracted from server.py"""
import uuid
import os
import math
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

import deps
from models.trade import TradeLogResponse, TradingSignalResponse, TradeLogCreate, UpdateTradeTimeEntered
from helpers import (
    create_admin_notification, create_member_notification, create_user_notification,
    truncate_lot_size, calculate_exit_value, send_push_to_admins, send_push_notification
)
from services import websocket_manager

try:
    from services import notify_trade_signal
except ImportError:
    async def notify_trade_signal(*a, **kw): pass

try:
    from utils.trading_days import get_trading_days_count, get_holidays_for_range, is_us_market_holiday
except ImportError:
    pass

logger = logging.getLogger("server")

router = APIRouter(prefix="/trade", tags=["Trade Monitor"])


# ─── Request Models ───

class TradeChangeRequest(BaseModel):
    trade_id: str
    field: str
    old_value: str
    new_value: str
    reason: str

class ErrorTradeCreate(BaseModel):
    product: Optional[str] = None
    direction: Optional[str] = None
    error_type: str = "system"
    error_details: Optional[str] = None
    lot_size: Optional[float] = None

@router.post("/log", response_model=TradeLogResponse)
async def log_trade(data: TradeLogCreate, user: dict = Depends(deps.get_current_user)):
    # CRITICAL: Always recalculate lot_size from the authoritative account_value
    # to prevent stale frontend values from corrupting trade history
    from utils.calculations import calculate_account_value, calculate_lot_size
    
    account_value = await calculate_account_value(deps.db, user["id"], user)
    lot_size = calculate_lot_size(account_value)
    
    # Log for debugging
    logger.info(f"Trade log: user={user['id']}, account_value={account_value}, calculated_lot_size={lot_size}, frontend_lot_size={data.lot_size}, commission={data.commission}")
    
    projected_profit = calculate_exit_value(lot_size)
    profit_difference = data.actual_profit - projected_profit
    
    # Determine performance
    if abs(profit_difference) < 0.01:
        performance = "perfect"
    elif profit_difference > 0:
        performance = "exceeded"
    else:
        performance = "below"
    
    # Get active signal - USE SIGNAL DIRECTION AS SOURCE OF TRUTH
    active_signal = await deps.db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    
    # Direction should come from the official signal, not from frontend
    # This ensures trade history matches signal history
    trade_direction = active_signal.get("direction") if active_signal else data.direction
    
    trade_id = str(uuid.uuid4())
    trade = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": lot_size,  # Use server-calculated lot_size
        "direction": trade_direction,  # Use signal direction as source of truth
        "projected_profit": projected_profit,
        "actual_profit": data.actual_profit,
        "commission": data.commission or 0,  # Daily commission from referrals
        "profit_difference": profit_difference,
        "performance": performance,
        "signal_id": active_signal["id"] if active_signal else None,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.trade_logs.insert_one(trade)
    
    # Create notification if member exited below projected amount (admin-only)
    if performance == "below" and profit_difference < -5:  # Only notify if more than $5 below
        await create_admin_notification(
            notification_type="trade_underperform",
            title="Underperforming Trade",
            message=f"{user['full_name']} exited ${abs(profit_difference):.2f} below projected",
            user_id=user["id"],
            user_name=user["full_name"],
            amount=data.actual_profit,
            metadata={
                "projected": projected_profit,
                "actual": data.actual_profit,
                "difference": profit_difference,
                "lot_size": lot_size,
                "commission": data.commission or 0
            }
        )
    
    # Create notification for all members about profit submission (community notification)
    await create_member_notification(
        notification_type="profit_submitted",
        title="Profit Reported",
        message=f"{user['full_name']} reported ${data.actual_profit:.2f} profit",
        triggered_by_id=user["id"],
        triggered_by_name=user["full_name"],
        amount=data.actual_profit,
        metadata={"performance": performance, "lot_size": lot_size}
    )
    
    return TradeLogResponse(**{**trade, "created_at": datetime.fromisoformat(trade["created_at"])})


@router.get("/logs", response_model=List[TradeLogResponse])
async def get_trade_logs(limit: int = 50, user_id: Optional[str] = None, user: dict = Depends(deps.get_current_user)):
    # For admins, allow fetching another user's logs
    target_user_id = user["id"]
    if user_id and user["role"] in ["basic_admin", "admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    trades = await deps.db.trade_logs.find(
        {"user_id": target_user_id}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    result = []
    for t in trades:
        # Ensure required fields have sensible defaults for edge cases
        if t.get("direction") is None:
            t["direction"] = "NONE"
        result.append(TradeLogResponse(**{**t, "created_at": datetime.fromisoformat(t["created_at"]) if isinstance(t["created_at"], str) else t["created_at"]}))
    return result


@router.get("/history")
async def get_trade_history(
    page: int = 1, 
    page_size: int = 10,
    user_id: Optional[str] = None,
    current_month_only: bool = True,  # Filter to current month by default
    user: dict = Depends(deps.get_current_user)
):
    """Get paginated trade history with signal details.
    Admins can pass user_id to view another user's history (for simulation).
    By default, only returns trades from the current month.
    """
    # Determine which user's history to fetch
    target_user_id = user["id"]
    
    # If user_id provided and requester is admin, use that user_id
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    skip = (page - 1) * page_size
    
    # Build query - optionally filter to current month
    query = {"user_id": target_user_id}
    
    if current_month_only:
        now = datetime.now(timezone.utc)
        # Get first day of current month
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start = first_day.strftime("%Y-%m")
        query["created_at"] = {"$regex": f"^{month_start}"}
    
    # Get total count
    total = await deps.db.trade_logs.count_documents(query)
    
    # Get paginated trades
    trades = await deps.db.trade_logs.find(
        query, 
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Batch fetch all signal IDs to avoid N+1 query problem
    signal_ids = list(set(trade.get("signal_id") for trade in trades if trade.get("signal_id")))
    signals_map = {}
    if signal_ids:
        signals = await deps.db.trading_signals.find(
            {"id": {"$in": signal_ids}}, 
            {"_id": 0, "id": 1, "product": 1, "trade_time": 1, "trade_timezone": 1, "direction": 1}
        ).to_list(len(signal_ids))
        signals_map = {s["id"]: s for s in signals}
    
    # Enrich with signal details (using pre-fetched signals)
    # Also compute the running trade day number for each trade
    # Get all distinct trade dates for this user to compute the day numbers
    all_trade_dates_cursor = deps.db.trade_logs.aggregate([
        {"$match": {"user_id": target_user_id}},
        {"$project": {"date": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {"_id": "$date"}},
        {"$sort": {"_id": 1}},
    ])
    all_trade_dates = [d["_id"] async for d in all_trade_dates_cursor]
    date_to_day_number = {date: i + 1 for i, date in enumerate(all_trade_dates)}

    enriched_trades = []
    for trade in trades:
        signal_details = None
        signal_id = trade.get("signal_id")
        signal_direction = trade.get("direction")  # Default to stored direction
        
        if signal_id and signal_id in signals_map:
            signal = signals_map[signal_id]
            signal_details = {
                "product": signal.get("product", "MOIL10"),
                "trade_time": signal.get("trade_time"),
                "trade_timezone": signal.get("trade_timezone", "Asia/Manila"),
            }
            # Use signal direction as the source of truth
            signal_direction = signal.get("direction", trade.get("direction"))
        
        trade_date = trade.get("created_at", "")[:10]
        enriched_trades.append({
            **trade,
            "direction": signal_direction,  # Override with signal direction
            "commission": trade.get("commission", 0),  # Default to 0 for backward compatibility
            "created_at": datetime.fromisoformat(trade["created_at"]) if isinstance(trade["created_at"], str) else trade["created_at"],
            "signal_details": signal_details,
            "time_entered": trade.get("time_entered"),  # User-editable field
            "trade_day_number": date_to_day_number.get(trade_date, 0),
        })
    
    return {
        "trades": enriched_trades,
        "total": total,
        "total_trade_days": len(all_trade_dates),
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.put("/logs/{trade_id}/time-entered")
async def update_trade_time_entered(
    trade_id: str, 
    data: UpdateTradeTimeEntered, 
    user: dict = Depends(deps.get_current_user)
):
    """Update the time entered for a trade log"""
    result = await deps.db.trade_logs.update_one(
        {"id": trade_id, "user_id": user["id"]},
        {"$set": {"time_entered": data.time_entered}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return {"message": "Time entered updated", "time_entered": data.time_entered}


@router.get("/streak")
async def get_trade_streak(user_id: Optional[str] = None, user: dict = Depends(deps.get_current_user)):
    """Calculate current streak of consecutive trading days (regardless of profit/loss).
    Admins can pass user_id to view another user's streak.
    """
    # Determine target user
    target_user_id = user["id"]
    target_user = user
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
        # Fetch the target user's data for streak_reset_date
        target_user = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
        if not target_user:
            target_user = user
    
    # Check if user has a streak reset date (from "did not trade" action)
    streak_reset_date = target_user.get("streak_reset_date")
    streak_reset_filter = None
    if streak_reset_date:
        try:
            reset_date = datetime.strptime(streak_reset_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            # Only count trades AFTER the reset date
            streak_reset_filter = reset_date.isoformat()
        except:
            pass
    
    # Fetch global holidays from database instead of hardcoded list
    global_holidays_cursor = deps.db.global_holidays.find({}, {"_id": 0, "date": 1})
    global_holidays_list = await global_holidays_cursor.to_list(1000)
    HOLIDAYS = set()
    for h in global_holidays_list:
        try:
            # Parse date string to tuple (year, month, day)
            date_str = h.get("date", "")
            if date_str:
                parts = date_str.split("-")
                if len(parts) == 3:
                    HOLIDAYS.add((int(parts[0]), int(parts[1]), int(parts[2])))
        except:
            continue
    
    def is_trading_day(d):
        """Check if a date is a trading day (not weekend, not holiday)"""
        # Skip weekends
        if d.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        # Skip holidays - holidays are treated like weekends (don't break streak)
        if (d.year, d.month, d.day) in HOLIDAYS:
            return False
        return True
    
    def get_previous_trading_day(d):
        """Get the previous trading day, skipping weekends and holidays"""
        prev = d - timedelta(days=1)
        attempts = 0
        while not is_trading_day(prev) and attempts < 14:  # Look back up to 2 weeks
            prev = prev - timedelta(days=1)
            attempts += 1
        return prev if attempts < 14 else None
    
    # Build query - exclude "did not trade" entries from streak calculation
    query = {
        "user_id": target_user_id,
        "did_not_trade": {"$ne": True}  # Exclude "did not trade" entries
    }
    
    # If there's a streak reset date, only count trades after that date
    if streak_reset_filter:
        query["created_at"] = {"$gt": streak_reset_filter}
    
    # Get all valid trades ordered by date descending
    trades = await deps.db.trade_logs.find(
        query, 
        {"_id": 0, "created_at": 1}
    ).sort("created_at", -1).to_list(1000)
    
    if not trades:
        return {"streak": 0, "streak_type": None, "total_trades": 0}
    
    # Calculate streak based on consecutive trading days
    # A streak counts consecutive TRADING days where the user traded
    # Holidays and weekends are skipped (don't break the streak)
    # Streak freezes protect missed trading days
    streak = 0
    last_trade_date = None
    
    # Build a set of dates the user traded
    traded_dates_set = set()
    for trade in trades:
        trade_date_str = trade.get("created_at", "")
        if not trade_date_str:
            continue
        try:
            if isinstance(trade_date_str, str):
                td = datetime.fromisoformat(trade_date_str.replace('Z', '+00:00')).date()
            else:
                td = trade_date_str.date()
            traded_dates_set.add(td)
        except:
            continue
    
    # Get all streak freeze usage for this user (trade type)
    freeze_usage = await deps.db.streak_freeze_usage.find(
        {"user_id": target_user_id, "freeze_type": "trade"},
        {"_id": 0, "date": 1}
    ).to_list(500)
    frozen_dates = {u["date"] for u in freeze_usage}
    
    # Count streak walking backwards from most recent trading day
    today_date = datetime.now(timezone.utc).date()
    check = today_date
    
    # Find starting point: today or last trading day
    if not is_trading_day(check):
        prev = get_previous_trading_day(check)
        if prev:
            check = prev
    elif check not in traded_dates_set and check.isoformat() not in frozen_dates:
        # Today is a trading day but user hasn't traded yet today
        # The day isn't over, so don't break the streak — start from previous trading day
        prev = get_previous_trading_day(check)
        if prev:
            check = prev
    
    # Walk backwards through trading days
    while check is not None:
        date_iso = check.isoformat()
        
        if check in traded_dates_set:
            streak += 1
        elif date_iso in frozen_dates:
            # Freeze protects this day - streak continues but don't increment
            streak += 1
        else:
            # Not traded and no freeze - streak breaks
            break
        
        check = get_previous_trading_day(check)
        if check is None:
            break
        # Safety: don't look back more than 400 days
        if (today_date - check).days > 400:
            break
    
    return {
        "streak": streak,
        "streak_type": "trading" if streak > 0 else None,
        "total_trades": len(trades)
    }


@router.get("/active-signal")
async def get_active_signal():
    signal = await deps.db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    if not signal:
        return {"message": "No active signal", "signal": None}
    # Handle missing fields for backward compatibility
    signal.setdefault("profit_points", 15)
    signal.setdefault("is_simulated", False)
    signal.setdefault("trade_timezone", "Asia/Manila")
    return {"signal": TradingSignalResponse(**{**signal, "created_at": datetime.fromisoformat(signal["created_at"]) if isinstance(signal["created_at"], str) else signal["created_at"]})}


@router.get("/daily-summary")
async def get_daily_summary(user_id: Optional[str] = None, user: dict = Depends(deps.get_current_user)):
    """Get today's trade summary. Admins can pass user_id to view another user's summary."""
    # Determine target user
    target_user_id = user["id"]
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    trades = await deps.db.trade_logs.find({
        "user_id": target_user_id,
        "created_at": {"$gte": today.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    total_projected = sum(t["projected_profit"] for t in trades)
    total_actual = sum(t["actual_profit"] for t in trades)
    
    return {
        "date": today.isoformat(),
        "trades_count": len(trades),
        "total_projected": round(total_projected, 2),
        "total_actual": round(total_actual, 2),
        "difference": round(total_actual - total_projected, 2),
        "trades": trades
    }


@router.get("/missed-trade-status")
async def check_missed_trade_status(user: dict = Depends(deps.get_current_user)):
    """Check if the current user has missed today's trade"""
    
    # Get today's date range
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # Check if user has traded today
    today_trade = await deps.db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0})
    
    has_traded_today = today_trade is not None
    
    # Get active signal and check if trade window has passed
    signal = await deps.db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    
    signal_completed = False
    is_post_trade_window = False
    trade_window_passed = False
    
    if signal:
        # Parse trade time
        trade_time_str = signal.get("trade_time", "12:00")
        trade_tz_str = signal.get("trade_timezone", "Asia/Manila")
        
        try:
            tz = pytz.timezone(trade_tz_str)
            now = datetime.now(tz)
            
            # Parse trade time (e.g., "12:00" or "20:20")
            parts = trade_time_str.split(":")
            trade_hour = int(parts[0])
            trade_minute = int(parts[1]) if len(parts) > 1 else 0
            
            # Create trade time for today in the signal's timezone
            trade_time_today = now.replace(hour=trade_hour, minute=trade_minute, second=0, microsecond=0)
            
            # Check if trade window has passed (trade time + 30 minutes buffer)
            trade_window_end = trade_time_today + timedelta(minutes=30)
            
            if now > trade_window_end:
                trade_window_passed = True
            
            # Post-trade window is 30 minutes after trade time
            if now > trade_time_today and now <= trade_window_end:
                is_post_trade_window = True
                
        except Exception as e:
            print(f"Error parsing trade time: {e}")
    else:
        # No active signal means the signal has been deactivated (completed)
        # Check if there was a signal today that's now inactive
        inactive_signal = await deps.db.trading_signals.find_one(
            {
                "is_active": False,
                "created_at": {"$gte": today_start.isoformat()}
            },
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        if inactive_signal:
            signal_completed = True
    
    # User should see missed trade popup if:
    # 1. Signal is completed (deactivated) and user hasn't traded today
    # 2. OR trade window has passed and user hasn't traded today
    should_show_missed_popup = (not has_traded_today) and (signal_completed or trade_window_passed)
    
    return {
        "has_traded_today": has_traded_today,
        "signal_completed": signal_completed,
        "is_post_trade_window": is_post_trade_window,
        "trade_window_passed": trade_window_passed,
        "should_show_missed_popup": should_show_missed_popup,
        "active_signal": signal is not None
    }


@router.post("/log-missed-trade")
async def log_missed_trade(
    date: str,  # ISO date string for which trade was missed
    actual_profit: float,
    commission: float = 0,  # Daily commission from referrals
    lot_size: Optional[float] = None,
    direction: Optional[str] = "BUY",
    notes: Optional[str] = None,
    user: dict = Depends(deps.get_current_user)
):
    """Log a trade that was missed but user wants to record retroactively"""
    
    # Parse the date - set to noon UTC to avoid timezone edge cases
    try:
        if 'T' in date:
            trade_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        else:
            # Just a date string (YYYY-MM-DD) - set to noon UTC
            trade_date = datetime.strptime(date, "%Y-%m-%d").replace(
                hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    
    # Check if user already has a trade for this date
    # Use date string prefix matching to avoid timezone comparison issues
    date_str = trade_date.strftime("%Y-%m-%d")
    
    existing_trade = await deps.db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {"$regex": f"^{date_str}"}
    })
    
    if existing_trade:
        raise HTTPException(status_code=400, detail="Trade already exists for this date")
    
    # Get user's current balance to calculate lot size if not provided
    if lot_size is None:
        deposits = await deps.db.deposits.aggregate([
            {"$match": {"user_id": user["id"], "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        withdrawals = await deps.db.withdrawals.aggregate([
            {"$match": {"user_id": user["id"], "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        profits = await deps.db.trade_logs.aggregate([
            {"$match": {"user_id": user["id"]}},
            {"$group": {"_id": None, "total": {"$sum": "$actual_profit"}}}
        ]).to_list(1)
        commissions = await deps.db.trade_logs.aggregate([
            {"$match": {"user_id": user["id"]}},
            {"$group": {"_id": None, "total": {"$sum": "$commission"}}}
        ]).to_list(1)
        
        balance = (deposits[0]["total"] if deposits else 0) - \
                  (withdrawals[0]["total"] if withdrawals else 0) + \
                  (profits[0]["total"] if profits else 0) + \
                  (commissions[0]["total"] if commissions else 0)
        
        lot_size = truncate_lot_size(balance)
    
    # Calculate projected profit
    projected_profit = round(lot_size * 15, 2)
    profit_difference = round(actual_profit - projected_profit, 2)
    
    # Create the trade log with all required fields
    trade_id = str(uuid.uuid4())
    # Ensure created_at has timezone info
    created_at_str = trade_date.isoformat()
    if '+' not in created_at_str and not created_at_str.endswith('Z'):
        created_at_str = created_at_str + "+00:00"
    
    # Determine performance category (consistent with regular trade logging)
    if actual_profit >= projected_profit:
        performance = "exceeded" if actual_profit > projected_profit else "perfect"
    elif actual_profit > 0:
        performance = "below"
    else:
        performance = "below"
    
    trade_log = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": lot_size,
        "direction": direction,
        "projected_profit": projected_profit,
        "actual_profit": actual_profit,
        "commission": commission,  # Daily commission from referrals
        "profit_difference": profit_difference,
        "performance": performance,
        "signal_id": None,  # No signal for retroactive trades
        "notes": notes or "Retroactively logged trade",
        "is_retroactive": True,
        "is_manual_adjustment": True,  # Flag for manually adjusted trades
        "created_at": created_at_str
    }
    
    await deps.db.trade_logs.insert_one(trade_log)
    
    return {
        "message": "Trade logged successfully",
        "trade": {k: v for k, v in trade_log.items() if k != "_id"}
    }


@router.post("/log-error")
async def log_error_trade(data: ErrorTradeCreate, user: dict = Depends(deps.get_current_user)):
    """
    Log an error trade (wrong product, wrong time, wrong direction, or other user errors).
    This creates a special trade log entry that affects the account value.
    Also sends a notification to admins.
    """
    # Parse the date
    if data.date:
        try:
            if 'T' in data.date:
                trade_date = datetime.fromisoformat(data.date.replace('Z', '+00:00'))
            else:
                trade_date = datetime.strptime(data.date, "%Y-%m-%d").replace(
                    hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    else:
        trade_date = datetime.now(timezone.utc)
    
    # Get user's current balance to calculate lot size
    deposits = await deps.db.deposits.aggregate([
        {"$match": {"user_id": user["id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    withdrawals = await deps.db.withdrawals.aggregate([
        {"$match": {"user_id": user["id"], "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    profits = await deps.db.trade_logs.aggregate([
        {"$match": {"user_id": user["id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$actual_profit"}}}
    ]).to_list(1)
    commissions = await deps.db.trade_logs.aggregate([
        {"$match": {"user_id": user["id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$commission"}}}
    ]).to_list(1)
    
    balance = (deposits[0]["total"] if deposits else 0) - \
              (withdrawals[0]["total"] if withdrawals else 0) + \
              (profits[0]["total"] if profits else 0) + \
              (commissions[0]["total"] if commissions else 0)
    
    lot_size = truncate_lot_size(balance)
    projected_profit = round(lot_size * 15, 2)
    profit_difference = round(data.actual_profit - projected_profit, 2)
    
    # Determine performance
    if data.actual_profit >= projected_profit:
        performance = "exceeded" if data.actual_profit > projected_profit else "perfect"
    elif data.actual_profit > 0:
        performance = "below"
    else:
        performance = "loss"
    
    # Error type labels for display
    error_type_labels = {
        'wrong_product': 'Wrong Product Selection',
        'wrong_time': 'Wrong Trade Time',
        'wrong_direction': 'Wrong Direction',
        'other': 'Other Error'
    }
    error_label = error_type_labels.get(data.error_type, 'User Error')
    
    # Build notes with error information
    notes = f"ERROR TRADE: {error_label}"
    if data.error_explanation:
        notes += f" - {data.error_explanation}"
    
    trade_id = str(uuid.uuid4())
    created_at_str = trade_date.isoformat()
    
    trade_log = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": lot_size,
        "direction": data.direction or "BUY",
        "product": data.product or "MOIL10",
        "projected_profit": projected_profit,
        "actual_profit": data.actual_profit,
        "commission": 0,
        "profit_difference": profit_difference,
        "performance": performance,
        "signal_id": None,
        "notes": notes,
        "is_error_trade": True,
        "error_type": data.error_type,
        "error_explanation": data.error_explanation,
        "is_manual_adjustment": True,
        "created_at": created_at_str
    }
    
    await deps.db.trade_logs.insert_one(trade_log)
    
    # Create admin notification about the error trade
    await create_admin_notification(
        notification_type="error_trade",
        title="Error Trade Reported",
        message=f"{user['full_name']} reported an error trade ({error_label}): ${data.actual_profit:.2f}",
        user_id=user["id"],
        user_name=user.get("full_name", "Unknown"),
        amount=data.actual_profit,
        metadata={
            "error_type": data.error_type,
            "error_explanation": data.error_explanation,
            "trade_id": trade_id
        }
    )
    
    logger.info(f"Error trade logged for user {user['id']}: {error_label}, profit: ${data.actual_profit}")
    
    return {
        "message": "Error trade logged successfully",
        "trade": {k: v for k, v in trade_log.items() if k != "_id"}
    }


@router.post("/did-not-trade")
async def mark_did_not_trade(
    date: str,  # ISO date string (YYYY-MM-DD)
    user: dict = Depends(deps.get_current_user)
):
    """Mark a date as 'did not trade' - sets profit to 0 and resets streak"""
    
    # Parse the date
    try:
        if 'T' in date:
            trade_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        else:
            trade_date = datetime.strptime(date, "%Y-%m-%d").replace(
                hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    
    # Check if this is a past date (can't mark future dates as did not trade)
    now = datetime.now(timezone.utc)
    if trade_date.date() >= now.date():
        raise HTTPException(status_code=400, detail="Can only mark past dates as 'did not trade'")
    
    # Check if user already has a trade for this date
    # Use date string prefix matching to avoid timezone comparison issues
    date_str = trade_date.strftime("%Y-%m-%d")
    
    existing_trade = await deps.db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {"$regex": f"^{date_str}"}
    })
    
    if existing_trade:
        raise HTTPException(status_code=400, detail="Trade already exists for this date")
    
    # Create the "did not trade" entry with 0 profit
    trade_id = str(uuid.uuid4())
    created_at_str = trade_date.isoformat()
    if '+' not in created_at_str and not created_at_str.endswith('Z'):
        created_at_str = created_at_str + "+00:00"
    
    trade_log = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": 0,
        "direction": "NONE",
        "projected_profit": 0,
        "actual_profit": 0,
        "commission": 0,
        "profit_difference": 0,
        "performance": "missed",
        "signal_id": None,
        "notes": "Did not trade",
        "did_not_trade": True,
        "is_retroactive": True,
        "created_at": created_at_str
    }
    
    await deps.db.trade_logs.insert_one(trade_log)
    
    # Reset user's streak to 0 by storing the reset date
    await deps.db.users.update_one(
        {"id": user["id"]},
        {"$set": {"streak_reset_date": trade_date.strftime("%Y-%m-%d")}}
    )
    
    return {
        "message": "Marked as 'did not trade'. Your trading streak has been reset to 0.",
        "trade_id": trade_id,
        "date": date,
        "streak_reset": True
    }


@router.post("/forward-to-profit")
async def forward_trade_to_profit(trade_id: str, is_bve: bool = False, user: dict = Depends(deps.get_current_user)):
    """Forward trade profit to profit tracker by creating a deposit entry"""
    
    # Use BVE collection if in BVE mode
    trade_collection = deps.db.bve_trade_logs if is_bve else deps.db.trade_logs
    trade = await trade_collection.find_one({"id": trade_id, "user_id": user["id"]}, {"_id": 0})
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # BVE trades should NOT be forwarded to production profit tracker
    if is_bve:
        raise HTTPException(status_code=400, detail="BVE trades cannot be forwarded to production profit tracker. Exit BVE mode to access real trades.")
    
    # Check if already forwarded
    existing = await deps.db.deposits.find_one({"trade_id": trade_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Trade already forwarded to profit tracker")
    
    # Create deposit entry for the profit
    deposit_id = str(uuid.uuid4())
    deposit = {
        "id": deposit_id,
        "user_id": user["id"],
        "amount": trade["actual_profit"],
        "product": "MOIL10",
        "currency": "USD",
        "notes": f"Trade profit from {trade['created_at'][:10]} - {trade['direction']}",
        "trade_id": trade_id,
        "type": "profit",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await deps.db.deposits.insert_one(deposit)
    
    return {
        "message": "Trade profit forwarded to profit tracker",
        "deposit_id": deposit_id,
        "amount": trade["actual_profit"]
    }


@router.delete("/reset/{trade_id}")
async def reset_trade(trade_id: str, user: dict = Depends(deps.require_master_admin)):
    """Reset/delete a trade - Master Admin only. Allows trade to be re-entered."""
    
    # Find the trade
    trade = await deps.db.trade_logs.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Store in reset_trades collection for audit trail
    reset_record = {
        "id": str(uuid.uuid4()),
        "original_trade": trade,
        "reset_by": user["id"],
        "reset_by_name": user.get("full_name", user.get("email")),
        "reset_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Master admin reset"
    }
    await deps.db.reset_trades.insert_one(reset_record)
    
    # Delete the trade
    await deps.db.trade_logs.delete_one({"id": trade_id})
    
    # Also delete any associated deposit (if trade was forwarded to profit)
    await deps.db.deposits.delete_many({"trade_id": trade_id})
    
    # Notify the original user via WebSocket
    try:
        await websocket_manager.send_notification(
            trade["user_id"],
            {
                "type": "trade_reset",
                "title": "Trade Reset",
                "message": f"Your trade from {trade['created_at'][:10]} has been reset by admin. You can re-enter it.",
                "data": {"trade_date": trade["created_at"][:10]}
            }
        )
    except:
        pass
    
    return {
        "message": "Trade reset successfully",
        "trade_date": trade["created_at"][:10],
        "user_id": trade["user_id"]
    }


@router.delete("/undo-by-date/{date}")
async def undo_trade_by_date(date: str, user: dict = Depends(deps.get_current_user)):
    """Undo/delete a trade by date - Users can undo their own trades from the Daily Projection table"""
    
    # Parse the date
    try:
        trade_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    
    # Find the trade for this user on this date
    # Use date string prefix matching to avoid timezone comparison issues
    date_str = trade_date.strftime("%Y-%m-%d")
    
    trade = await deps.db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {"$regex": f"^{date_str}"}
    }, {"_id": 0})
    
    if not trade:
        raise HTTPException(status_code=404, detail="No trade found for this date")
    
    # Store in reset_trades collection for audit trail
    reset_record = {
        "id": str(uuid.uuid4()),
        "original_trade": trade,
        "reset_by": user["id"],
        "reset_by_name": user.get("full_name", user.get("email")),
        "reset_at": datetime.now(timezone.utc).isoformat(),
        "reason": "User undo from Daily Projection"
    }
    await deps.db.reset_trades.insert_one(reset_record)
    
    # Delete the trade
    await deps.db.trade_logs.delete_one({"id": trade["id"]})
    
    # Also delete any associated deposit (if trade was forwarded to profit)
    await deps.db.deposits.delete_many({"trade_id": trade["id"]})
    
    logger.info(f"Trade undone: user={user['id']}, date={date}, trade_id={trade['id']}")
    
    return {
        "message": "Trade undone successfully",
        "trade_date": date,
        "trade_id": trade["id"]
    }


@router.get("/holidays")
async def get_user_holidays(user: dict = Depends(deps.get_current_user)):
    """Get user-specific holidays"""
    holidays = await deps.db.user_holidays.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    return {"holidays": holidays}


@router.post("/holidays")
async def add_user_holiday(
    date: str,
    reason: Optional[str] = "Personal holiday",
    user: dict = Depends(deps.get_current_user)
):
    """Mark a date as a user-specific holiday"""
    
    # Parse and validate the date
    try:
        holiday_date = datetime.strptime(date, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    
    # Check if this date is already marked as a holiday
    existing = await deps.db.user_holidays.find_one({
        "user_id": user["id"],
        "date": date
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="This date is already marked as a holiday")
    
    # Check if there's already a trade logged for this date
    # Use date string prefix matching to avoid timezone comparison issues
    date_str = holiday_date.strftime("%Y-%m-%d")
    
    existing_trade = await deps.db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {"$regex": f"^{date_str}"}
    })
    
    if existing_trade:
        raise HTTPException(
            status_code=400, 
            detail="Cannot mark as holiday - a trade already exists for this date. Undo the trade first."
        )
    
    # Create the holiday record
    holiday_id = str(uuid.uuid4())
    holiday = {
        "id": holiday_id,
        "user_id": user["id"],
        "date": date,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.user_holidays.insert_one(holiday)
    
    logger.info(f"User holiday added: user={user['id']}, date={date}")
    
    return {
        "message": "Holiday marked successfully",
        "holiday": {k: v for k, v in holiday.items() if k != "_id"}
    }


@router.delete("/holidays/{date}")
async def remove_user_holiday(date: str, user: dict = Depends(deps.get_current_user)):
    """Remove a user-specific holiday"""
    
    result = await deps.db.user_holidays.delete_one({
        "user_id": user["id"],
        "date": date
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found for this date")
    
    logger.info(f"User holiday removed: user={user['id']}, date={date}")
    
    return {"message": "Holiday removed successfully", "date": date}


@router.get("/global-holidays")
async def get_global_holidays_for_user(user: dict = Depends(deps.get_current_user)):
    """Get all global holidays (for any authenticated user to see)"""
    holidays = await deps.db.global_holidays.find(
        {},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    return {"holidays": holidays}


@router.get("/trading-products")
async def get_trading_products_for_user(user: dict = Depends(deps.get_current_user)):
    """Get active trading products (for any authenticated user)"""
    products = await deps.db.trading_products.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("order", 1).to_list(50)
    
    # If no products exist, return default products
    if not products:
        products = [
            {"id": "default-1", "name": "MOIL10", "is_active": True},
            {"id": "default-2", "name": "XAUUSD", "is_active": True},
            {"id": "default-3", "name": "EURUSD", "is_active": True},
            {"id": "default-4", "name": "GBPUSD", "is_active": True},
            {"id": "default-5", "name": "USDJPY", "is_active": True},
        ]
    
    return {"products": products}


@router.post("/request-change")
async def request_trade_change(data: TradeChangeRequest, user: dict = Depends(deps.get_current_user)):
    """Request a change to a trade - for non-master-admin users"""
    
    # Find the trade
    trade = await deps.db.trade_logs.find_one({"id": data.trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Verify the trade belongs to the requesting user
    if trade["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only request changes to your own trades")
    
    # Check if there's already a pending request for this trade
    existing_request = await deps.db.trade_change_requests.find_one({
        "trade_id": data.trade_id,
        "status": "pending"
    })
    if existing_request:
        raise HTTPException(status_code=400, detail="A change request for this trade is already pending")
    
    # Create the change request
    request_id = str(uuid.uuid4())
    change_request = {
        "id": request_id,
        "trade_id": data.trade_id,
        "user_id": user["id"],
        "user_name": user.get("full_name", user.get("email")),
        "trade_date": trade["created_at"][:10],
        "original_profit": trade["actual_profit"],
        "reason": data.reason,
        "requested_changes": data.requested_changes,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await deps.db.trade_change_requests.insert_one(change_request)
    
    # Notify all admins via WebSocket
    try:
        admins = await deps.db.users.find(
            {"role": {"$in": ["basic_admin", "admin", "super_admin", "master_admin"]}},
            {"_id": 0, "id": 1}
        ).to_list(100)
        
        for admin in admins:
            await websocket_manager.send_notification(
                admin["id"],
                {
                    "type": "trade_change_request",
                    "title": "Trade Change Request",
                    "message": f"{user.get('full_name', 'A user')} requested a change to their trade from {trade['created_at'][:10]}",
                    "data": {"request_id": request_id}
                }
            )
    except:
        pass
    
    return {
        "message": "Change request submitted successfully",
        "request_id": request_id
    }


@router.get("/signal-block-status")
async def get_signal_block_status(user: dict = Depends(deps.get_current_user)):
    """Check if the current member is blocked from viewing trading signals due to unreported profit tracker data."""
    user_id = user["id"]
    user_role = user.get("role", "member")

    # Admins are never blocked
    if user_role in ("admin", "basic_admin", "super_admin", "master_admin"):
        return {"blocked": False, "reason": None, "missing_days": 0, "habit_gate_locked": False}

    # Check admin manual override
    user_doc = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "signal_unblocked_until": 1, "created_at": 1})
    if user_doc and user_doc.get("signal_unblocked_until"):
        unblocked_until = user_doc["signal_unblocked_until"]
        if isinstance(unblocked_until, str):
            unblocked_until = datetime.fromisoformat(unblocked_until)
        if unblocked_until > datetime.now(timezone.utc):
            return {"blocked": False, "reason": "admin_override", "missing_days": 0, "habit_gate_locked": False}

    # Check habit gate: if there are gate habits, user must have completed one within its validity window
    habit_gate_locked = False
    gate_deadline = None
    gate_habits = await deps.db.habits.find({"active": True, "is_gate": True}, {"_id": 0, "id": 1, "validity_days": 1}).to_list(100)
    if gate_habits:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_date = datetime.now(timezone.utc).date()
        gate_unlocked = False
        for gh in gate_habits:
            validity = gh.get("validity_days", 1)
            window_start = (today_date - timedelta(days=validity - 1)).isoformat()
            recent = await deps.db.habit_completions.find_one(
                {"user_id": user_id, "habit_id": gh["id"], "date": {"$gte": window_start}},
                {"_id": 0, "date": 1}
            )
            if recent:
                gate_unlocked = True
                completion_date = datetime.strptime(recent["date"], "%Y-%m-%d").date()
                expires = completion_date + timedelta(days=validity)
                if gate_deadline is None or expires > gate_deadline:
                    gate_deadline = expires
        if not gate_unlocked:
            habit_gate_locked = True

    today = datetime.now(timezone.utc).date()
    seven_days_ago = today - timedelta(days=7)

    # Find user's most recent trade log entry
    last_trade = await deps.db.trade_logs.find_one(
        {"user_id": user_id},
        {"_id": 0, "created_at": 1},
        sort=[("created_at", -1)]
    )

    if last_trade:
        last_date_str = last_trade["created_at"][:10]  # YYYY-MM-DD
        last_trade_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    else:
        # Never traded — use account creation date
        created_at = user_doc.get("created_at", "") if user_doc else ""
        if created_at:
            last_trade_date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date() if isinstance(created_at, str) else created_at.date()
        else:
            last_trade_date = seven_days_ago

    days_since_last = (today - last_trade_date).days

    if days_since_last < 7:
        resp = {"blocked": habit_gate_locked, "reason": "habit_gate" if habit_gate_locked else None, "missing_days": days_since_last, "habit_gate_locked": habit_gate_locked}
        if gate_deadline:
            resp["gate_deadline"] = gate_deadline.isoformat()
        return resp

    # Were there any official signals in the unreported gap?
    gap_start = (last_trade_date + timedelta(days=1)).isoformat()
    gap_end = today.isoformat()

    signals_in_gap = await deps.db.trading_signals.count_documents({
        "created_at": {"$gte": gap_start, "$lte": gap_end + "T23:59:59"},
        "is_official": True
    })

    if signals_in_gap == 0:
        resp = {"blocked": habit_gate_locked, "reason": "habit_gate" if habit_gate_locked else "no_signals", "missing_days": days_since_last, "habit_gate_locked": habit_gate_locked}
        if gate_deadline:
            resp["gate_deadline"] = gate_deadline.isoformat()
        return resp

    return {
        "blocked": True,
        "reason": "unreported_week",
        "missing_days": days_since_last,
        "last_report_date": last_trade_date.isoformat(),
        "signals_in_gap": signals_in_gap,
        "habit_gate_locked": habit_gate_locked,
        "message": f"You have {days_since_last} days of unreported profit tracker data. Please update your profit tracker to unlock the trading signal."
    }

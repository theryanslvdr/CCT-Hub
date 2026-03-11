"""Admin management routes - extracted from server.py"""
import uuid
import os
import io
import math
import logging
import pytz
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Request, UploadFile, File, Form, Body
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum

import deps
from models.trade import TradeLogResponse, TradingSignalResponse, TradingSignalUpdate, TradingSignalCreate
from models.license import LicenseCreate, LicenseInviteCreate, LicenseInviteUpdate
from models.user import RoleUpgrade
from models.settings import EmailTemplateUpdate
from helpers import (
    create_admin_notification, create_member_notification, create_user_notification,
    truncate_lot_size, calculate_exit_value, calculate_withdrawal_fees,
    send_push_to_admins, send_push_notification, send_push_to_all_members,
    verify_heartbeat_user, send_signal_email_to_members,
    schedule_pre_trade_notifications,
    calculate_extended_license_projections, get_quarterly_summary, get_quarter
)
from services import websocket_manager

try:
    from services import notify_trade_signal
except ImportError:
    async def notify_trade_signal(*a, **kw): pass

from utils.calculations import (
    _is_honorary, calculate_honorary_licensee_value,
    get_user_financial_summary, calculate_account_value
)

try:
    from utils.trading_days import get_trading_days_count, get_holidays_for_range, is_us_market_holiday
except ImportError:
    pass

try:
    from services.rewards_sync_service import sync_user_to_rewards_platform
except ImportError:
    async def sync_user_to_rewards_platform(*a, **kw): pass

try:
    import cloudinary
    import cloudinary.uploader
except ImportError:
    cloudinary = None

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger("server")

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Request Models ───

class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    lot_size: Optional[float] = None
    allowed_dashboards: Optional[List[str]] = None
    timezone: Optional[str] = None
    referral_code: Optional[str] = None
    merin_referral_code: Optional[str] = None
    trading_start_date: Optional[str] = None
    referred_by_user_id: Optional[str] = None

class TempPasswordSet(BaseModel):
    temp_password: str

class NotifyMissedTradeRequest(BaseModel):
    user_ids: List[str]
    custom_message: Optional[str] = None

class ChangeLicenseTypeRequest(BaseModel):
    new_type: str
    starting_amount: Optional[float] = None

class ResetStartingAmountRequest(BaseModel):
    new_starting_amount: float
    reason: Optional[str] = None

class SendEmailRequest(BaseModel):
    subject: str
    body: str
    template_type: Optional[str] = "admin_notification"

class EmailTemplateCreate(BaseModel):
    type: str
    subject: str
    body: str
    variables: Optional[List[str]] = None

class EmailTemplateUpdateModel(BaseModel):
    subject: str
    body: str
    variables: Optional[List[str]] = None

class NotifyRequest(BaseModel):
    type: str = "general"
    title: str
    message: str

class _HabitBase(BaseModel):
    title: str
    description: Optional[str] = None
    action_type: str = "generic"
    action_data: Optional[str] = ""
    is_gate: bool = True
    validity_days: int = 1
    requires_screenshot: bool = True
    day_of_week: Optional[str] = None  # "monday","tuesday",...,"sunday" or None for daily

class _HabitCreate(_HabitBase):
    pass

class LicenseeTradeOverride(BaseModel):
    license_id: str
    date: str
    traded: bool
    notes: Optional[str] = None

@router.post("/push-notify-all")
async def admin_push_notify_all(request: Request, user: dict = Depends(deps.require_admin)):
    """Admin: Send push notification to all subscribed users"""
    body = await request.json()
    title = body.get("title", "CrossCurrent Alert")
    message = body.get("message", "")
    url = body.get("url", "/")
    tag = body.get("tag", "admin")
    
    result = await send_push_to_all_members(title, message, url, tag)
    return {"message": f"Push sent to {result['sent']} devices", **result}


@router.get("/global-holidays")
async def get_global_holidays(user: dict = Depends(deps.require_admin)):
    """Get all global holidays (Master Admin only)"""
    holidays = await deps.db.global_holidays.find(
        {},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    return {"holidays": holidays}


@router.post("/global-holidays")
async def add_global_holiday(
    date: str,
    reason: Optional[str] = "Market holiday",
    user: dict = Depends(deps.require_super_or_master_admin)
):
    """Add a global holiday for all users (Super Admin or Master Admin only)"""
    
    # Parse and validate the date
    try:
        holiday_date = datetime.strptime(date, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    
    # Check if this date is already a global holiday
    existing = await deps.db.global_holidays.find_one({"date": date})
    if existing:
        raise HTTPException(status_code=400, detail="This date is already a global holiday")
    
    # Create the global holiday record
    holiday_id = str(uuid.uuid4())
    holiday = {
        "id": holiday_id,
        "date": date,
        "reason": reason,
        "created_by": user["id"],
        "created_by_name": user.get("full_name", user.get("email")),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.global_holidays.insert_one(holiday)
    
    logger.info(f"Global holiday added: date={date}, by={user['id']}")
    
    return {
        "message": "Global holiday added successfully",
        "holiday": {k: v for k, v in holiday.items() if k != "_id"}
    }


@router.delete("/global-holidays/{date}")
async def remove_global_holiday(date: str, user: dict = Depends(deps.require_super_or_master_admin)):
    """Remove a global holiday (Super Admin or Master Admin only)"""
    
    result = await deps.db.global_holidays.delete_one({"date": date})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Global holiday not found for this date")
    
    logger.info(f"Global holiday removed: date={date}, by={user['id']}")
    
    return {"message": "Global holiday removed successfully", "date": date}


@router.get("/trading-products")
async def get_trading_products(user: dict = Depends(deps.require_admin)):
    """Get all trading products"""
    products = await deps.db.trading_products.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    
    # If no products exist, return default products
    if not products:
        default_products = [
            {"id": str(uuid.uuid4()), "name": "MOIL10", "is_active": True, "order": 0},
            {"id": str(uuid.uuid4()), "name": "XAUUSD", "is_active": True, "order": 1},
            {"id": str(uuid.uuid4()), "name": "EURUSD", "is_active": True, "order": 2},
            {"id": str(uuid.uuid4()), "name": "GBPUSD", "is_active": True, "order": 3},
            {"id": str(uuid.uuid4()), "name": "USDJPY", "is_active": True, "order": 4},
        ]
        # Insert default products
        for product in default_products:
            product["created_at"] = datetime.now(timezone.utc).isoformat()
            await deps.db.trading_products.insert_one(product)
        products = default_products
    
    return {"products": products}


@router.post("/trading-products")
async def add_trading_product(
    name: str,
    user: dict = Depends(deps.require_master_admin)
):
    """Add a new trading product (Master Admin only)"""
    
    # Check if product already exists
    existing = await deps.db.trading_products.find_one({"name": name.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Product already exists")
    
    # Get the highest order number
    last_product = await deps.db.trading_products.find_one({}, sort=[("order", -1)])
    next_order = (last_product.get("order", 0) + 1) if last_product else 0
    
    product_id = str(uuid.uuid4())
    product = {
        "id": product_id,
        "name": name.upper(),
        "is_active": True,
        "order": next_order,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.trading_products.insert_one(product)
    
    logger.info(f"Trading product added: {name.upper()}, by={user['id']}")
    
    return {
        "message": "Product added successfully",
        "product": {k: v for k, v in product.items() if k != "_id"}
    }


@router.delete("/trading-products/{product_id}")
async def remove_trading_product(product_id: str, user: dict = Depends(deps.require_master_admin)):
    """Remove a trading product (Master Admin only)"""
    
    result = await deps.db.trading_products.delete_one({"id": product_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    logger.info(f"Trading product removed: {product_id}, by={user['id']}")
    
    return {"message": "Product removed successfully"}


@router.put("/trading-products/{product_id}")
async def update_trading_product(
    product_id: str,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    user: dict = Depends(deps.require_master_admin)
):
    """Update a trading product (Master Admin only)"""
    
    product = await deps.db.trading_products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name.upper()
    if is_active is not None:
        update_data["is_active"] = is_active
    
    if update_data:
        await deps.db.trading_products.update_one({"id": product_id}, {"$set": update_data})
    
    updated = await deps.db.trading_products.find_one({"id": product_id}, {"_id": 0})
    
    return {"message": "Product updated successfully", "product": updated}


@router.get("/trade-change-requests")
async def get_trade_change_requests(
    status: Optional[str] = None,
    user: dict = Depends(deps.require_admin)
):
    """Get all trade change requests - Admin only"""
    query = {}
    if status:
        query["status"] = status
    
    requests = await deps.db.trade_change_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"requests": requests}


@router.put("/trade-change-requests/{request_id}")
async def handle_trade_change_request(
    request_id: str,
    action: str,  # "approve" or "reject"
    admin_notes: Optional[str] = None,
    user: dict = Depends(deps.require_master_admin)
):
    """Handle a trade change request - Master Admin only"""
    
    request = await deps.db.trade_change_requests.find_one({"id": request_id}, {"_id": 0})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request has already been processed")
    
    if action == "approve":
        # Reset the trade (same as reset_trade endpoint)
        trade = await deps.db.trade_logs.find_one({"id": request["trade_id"]}, {"_id": 0})
        if trade:
            # Store in reset_trades for audit
            reset_record = {
                "id": str(uuid.uuid4()),
                "original_trade": trade,
                "reset_by": user["id"],
                "reset_by_name": user.get("full_name", user.get("email")),
                "reset_at": datetime.now(timezone.utc).isoformat(),
                "reason": f"Approved change request: {request['reason']}",
                "request_id": request_id
            }
            await deps.db.reset_trades.insert_one(reset_record)
            
            # Delete the trade
            await deps.db.trade_logs.delete_one({"id": request["trade_id"]})
            await deps.db.deposits.delete_many({"trade_id": request["trade_id"]})
        
        # Update request status
        await deps.db.trade_change_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": "approved",
                "handled_by": user["id"],
                "handled_by_name": user.get("full_name", user.get("email")),
                "handled_at": datetime.now(timezone.utc).isoformat(),
                "admin_notes": admin_notes
            }}
        )
        
        # Notify the user
        try:
            await websocket_manager.send_notification(
                request["user_id"],
                {
                    "type": "trade_change_approved",
                    "title": "Change Request Approved",
                    "message": f"Your trade change request for {request['trade_date']} has been approved. You can now re-enter the trade.",
                    "data": {"trade_date": request["trade_date"]}
                }
            )
        except:
            pass
        
        return {"message": "Request approved and trade reset", "status": "approved"}
    
    elif action == "reject":
        # Update request status
        await deps.db.trade_change_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": "rejected",
                "handled_by": user["id"],
                "handled_by_name": user.get("full_name", user.get("email")),
                "handled_at": datetime.now(timezone.utc).isoformat(),
                "admin_notes": admin_notes
            }}
        )
        
        # Notify the user
        try:
            await websocket_manager.send_notification(
                request["user_id"],
                {
                    "type": "trade_change_rejected",
                    "title": "Change Request Rejected",
                    "message": f"Your trade change request for {request['trade_date']} has been rejected." + (f" Reason: {admin_notes}" if admin_notes else ""),
                    "data": {"trade_date": request["trade_date"]}
                }
            )
        except:
            pass
        
        return {"message": "Request rejected", "status": "rejected"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")


@router.post("/signals", response_model=TradingSignalResponse)
async def create_signal(data: TradingSignalCreate, request: Request, user: dict = Depends(deps.require_admin)):
    # Deactivate all existing signals
    await deps.db.trading_signals.update_many({}, {"$set": {"is_active": False}})
    
    signal_id = str(uuid.uuid4())
    signal = {
        "id": signal_id,
        "product": data.product,
        "trade_time": data.trade_time,
        "trade_timezone": data.trade_timezone,
        "direction": data.direction,
        "profit_points": data.profit_points,
        "notes": data.notes,
        "is_active": True,
        "is_official": data.is_official,  # Official trading signal flag
        "is_simulated": False,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.trading_signals.insert_one(signal)
    
    # Create notification for all members about new official trading signal
    if data.is_official:
        await create_member_notification(
            notification_type="trading_signal",
            title=f"New Trading Signal: {data.direction}",
            message=f"Official {data.direction} signal for {data.product} at {data.trade_time}",
            triggered_by_id=user["id"],
            triggered_by_name=user["full_name"],
            metadata={"signal_id": signal_id, "direction": data.direction, "product": data.product, "trade_time": data.trade_time}
        )
        
        # Send email to all active members if send_email is True
        if data.send_email:
            # Get frontend URL from request headers or use default
            frontend_url = request.headers.get("origin") or os.environ.get("FRONTEND_URL", "")
            try:
                email_result = await send_signal_email_to_members(signal, frontend_url)
                logger.info(f"Signal email sent to {email_result['sent']} members")
            except Exception as e:
                logger.error(f"Failed to send signal emails: {e}")
        
        # Send push notification to all members
        try:
            push_result = await send_push_to_all_members(
                title=f"Trading Signal: {data.direction} {data.product}",
                body=f"Trade at {data.trade_time} | Multiplier: ×{data.profit_multiplier or data.profit_points}",
                url="/trade-monitor",
                tag="trading-signal"
            )
            logger.info(f"Push notification sent to {push_result['sent']} devices")
        except Exception as e:
            logger.error(f"Failed to send push notifications: {e}")
        
        # Schedule pre-trade push notifications (10min and 5min before)
        try:
            schedule_pre_trade_notifications(data.trade_time, data.trade_timezone, data.product, data.direction)
        except Exception as e:
            logger.error(f"Failed to schedule pre-trade notifications: {e}")
    
    return TradingSignalResponse(**{**signal, "created_at": datetime.fromisoformat(signal["created_at"])})


@router.put("/signals/{signal_id}")
async def update_signal(signal_id: str, data: TradingSignalUpdate, user: dict = Depends(deps.require_admin)):
    signal = await deps.db.trading_signals.find_one({"id": signal_id}, {"_id": 0})
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    update_data = {}
    if data.trade_time is not None:
        update_data["trade_time"] = data.trade_time
    if data.trade_timezone is not None:
        update_data["trade_timezone"] = data.trade_timezone
    if data.direction is not None:
        update_data["direction"] = data.direction
    if data.profit_points is not None:
        update_data["profit_points"] = data.profit_points
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.is_active is not None:
        if data.is_active:
            # Deactivate all other signals first
            await deps.db.trading_signals.update_many({"id": {"$ne": signal_id}}, {"$set": {"is_active": False}})
        update_data["is_active"] = data.is_active
    if data.is_official is not None:
        update_data["is_official"] = data.is_official
    
    if update_data:
        await deps.db.trading_signals.update_one({"id": signal_id}, {"$set": update_data})
    
    updated = await deps.db.trading_signals.find_one({"id": signal_id}, {"_id": 0})
    return TradingSignalResponse(**{**updated, "created_at": datetime.fromisoformat(updated["created_at"]) if isinstance(updated["created_at"], str) else updated["created_at"]})


@router.post("/signals/simulate", response_model=TradingSignalResponse)
async def simulate_signal(data: TradingSignalCreate, user: dict = Depends(deps.require_super_admin)):
    """Create a simulated signal for testing - Super Admin only"""
    # Deactivate all existing signals
    await deps.db.trading_signals.update_many({}, {"$set": {"is_active": False}})
    
    signal_id = str(uuid.uuid4())
    signal = {
        "id": signal_id,
        "product": data.product,
        "trade_time": data.trade_time,
        "trade_timezone": data.trade_timezone,
        "direction": data.direction,
        "profit_points": data.profit_points,
        "notes": data.notes or "",  # Don't prepend [SIMULATED] - use is_simulated flag instead
        "is_active": True,
        "is_simulated": True,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.trading_signals.insert_one(signal)
    return TradingSignalResponse(**{**signal, "created_at": datetime.fromisoformat(signal["created_at"])})


@router.get("/signals", response_model=List[TradingSignalResponse])
async def get_signals(user: dict = Depends(deps.require_admin)):
    signals = await deps.db.trading_signals.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    result = []
    for s in signals:
        s.setdefault("profit_points", 15)
        s.setdefault("is_simulated", False)
        result.append(TradingSignalResponse(**{**s, "created_at": datetime.fromisoformat(s["created_at"]) if isinstance(s["created_at"], str) else s["created_at"]}))
    return result


@router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: str, user: dict = Depends(deps.require_admin)):
    result = await deps.db.trading_signals.delete_one({"id": signal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"message": "Signal deleted"}


@router.get("/run-diagnostic/{user_id}")
@router.post("/run-diagnostic/{user_id}")
async def run_account_diagnostic(user_id: str, user: dict = Depends(deps.require_admin)):
    """Dedicated diagnostic endpoint - separate from member details to avoid routing conflicts"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all trade logs
    all_trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    trades_sorted = sorted(all_trades, key=lambda x: x.get("created_at", ""))
    
    # Get all deposits
    all_deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    deposits_sorted = sorted(all_deposits, key=lambda x: x.get("created_at", ""))
    
    # Get reset/deleted trades
    reset_trades = await deps.db.reset_trades.find({"original_trade.user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Calculate totals
    total_deposits_amt = sum(d.get("amount", 0) for d in all_deposits if d.get("amount", 0) > 0)
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in all_deposits if d.get("amount", 0) < 0)
    total_profit = sum(t.get("actual_profit", 0) for t in all_trades)
    total_commission = sum(t.get("commission", 0) for t in all_trades)
    
    # Count did_not_trade entries
    did_not_trade_count = len([t for t in all_trades if t.get("did_not_trade")])
    actual_trades_count = len([t for t in all_trades if not t.get("did_not_trade")])
    
    calculated_balance = total_deposits_amt - total_withdrawals + total_profit + total_commission
    
    return {
        "user": {
            "id": member.get("id"),
            "email": member.get("email"),
            "full_name": member.get("full_name"),
            "onboarding_completed": member.get("onboarding_completed"),
            "trading_type": member.get("trading_type"),
            "trading_start_date": member.get("trading_start_date"),
            "streak_reset_date": member.get("streak_reset_date")
        },
        "summary": {
            "total_deposits": round(total_deposits_amt, 2),
            "total_withdrawals": round(total_withdrawals, 2),
            "total_profit": round(total_profit, 2),
            "total_commission": round(total_commission, 2),
            "calculated_balance": round(calculated_balance, 2),
            "total_trades": len(all_trades),
            "actual_trades": actual_trades_count,
            "did_not_trade_entries": did_not_trade_count,
            "reset_trades_count": len(reset_trades)
        },
        "trades": [
            {
                "date": t.get("created_at", "")[:10] if t.get("created_at") else "",
                "profit": t.get("actual_profit", 0),
                "commission": t.get("commission", 0),
                "did_not_trade": t.get("did_not_trade", False),
                "lot_size": t.get("lot_size"),
                "notes": (t.get("notes", "") or "")[:50]
            }
            for t in trades_sorted[-20:]
        ],
        "deposits": [
            {
                "date": d.get("created_at", "")[:10] if d.get("created_at") else "",
                "amount": d.get("amount", 0),
                "type": d.get("type", ""),
                "notes": (d.get("notes", "") or "")[:50]
            }
            for d in deposits_sorted[-20:]
        ],
        "reset_trades": [
            {
                "reset_at": (r.get("reset_at", "") or "")[:19],
                "original_date": (r.get("original_trade", {}).get("created_at", "") or "")[:10],
                "original_profit": r.get("original_trade", {}).get("actual_profit", 0),
                "reset_by": r.get("reset_by_name", "")
            }
            for r in reset_trades[-10:]
        ]
    }


@router.get("/export-debug-data/{user_id}")
async def export_debug_data(user_id: str, user: dict = Depends(deps.require_admin)):
    """Export comprehensive user data for debugging - downloadable JSON"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    all_trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(5000)
    all_deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(5000)
    all_withdrawals = await deps.db.withdrawals.find({"user_id": user_id}, {"_id": 0}).to_list(5000)
    reset_trades = await deps.db.reset_trades.find({"original_trade.user_id": user_id}, {"_id": 0}).to_list(500)
    balance_overrides = await deps.db.balance_overrides.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    commissions = await deps.db.commissions.find({"user_id": user_id}, {"_id": 0}).to_list(5000)
    
    from datetime import datetime, timezone
    return {
        "export_meta": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "exported_by": user.get("email"),
            "target_user_id": user_id,
            "version": "1.0"
        },
        "user_profile": member,
        "trades": sorted(all_trades, key=lambda x: x.get("created_at", "")),
        "deposits": sorted(all_deposits, key=lambda x: x.get("created_at", "")),
        "withdrawals": sorted(all_withdrawals, key=lambda x: x.get("created_at", "")),
        "reset_trades": reset_trades,
        "balance_overrides": balance_overrides,
        "commissions": commissions,
        "summary": {
            "total_trades": len(all_trades),
            "total_deposits": len(all_deposits),
            "total_withdrawals": len(all_withdrawals),
            "total_resets": len(reset_trades),
            "total_overrides": len(balance_overrides)
        }
    }


@router.get("/members")
async def get_members(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    sort_account_value: Optional[str] = None,  # 'asc' or 'desc'
    user: dict = Depends(deps.require_admin)
):
    query = {}
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if role and role != "all":
        query["role"] = role
    if status == "suspended":
        query["is_suspended"] = True
    elif status == "deactivated":
        query["is_deactivated"] = True
    elif status == "active":
        query["is_suspended"] = {"$ne": True}
        query["is_deactivated"] = {"$ne": True}
    else:
        # Default "all" excludes suspended and deactivated users
        query["is_suspended"] = {"$ne": True}
        query["is_deactivated"] = {"$ne": True}
    
    # IMPORTANT: Exclude licensees from standard member list
    # Licensees should be managed through the Licenses page, not Member Management
    query["license_type"] = {"$exists": False}
    
    total = await deps.db.users.count_documents(query)
    skip = (page - 1) * limit
    users_cursor = await deps.db.users.find(query, {"_id": 0, "password": 0}).skip(skip).limit(limit).to_list(limit)
    
    # For super_admin and master_admin, calculate account_value for each user
    users = []
    requesting_user_role = user.get("role")
    can_see_account_value = requesting_user_role in ["super_admin", "master_admin"]
    
    for u in users_cursor:
        user_data = dict(u)
        if can_see_account_value:
            # Check if user is a licensee - use license current_amount for their account_value
            if u.get("license_type"):
                license = await deps.db.licenses.find_one({"user_id": u["id"], "is_active": True}, {"_id": 0})
                if license:
                    if _is_honorary(license.get("license_type")):
                        from utils.calculations import calculate_honorary_licensee_value
                        user_data["account_value"] = await calculate_honorary_licensee_value(deps.db, license)
                    else:
                        user_data["account_value"] = round(license.get("current_amount", license.get("starting_amount", 0)), 2)
                else:
                    user_data["account_value"] = round(u.get("account_value", 0), 2)
            else:
                # Calculate account value from deposits and profits for non-licensees
                deposits = await deps.db.deposits.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)
                trades = await deps.db.trade_logs.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)
                
                total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit" and d.get("type") != "withdrawal")
                total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
                total_profit = sum(t.get("actual_profit", 0) for t in trades)
                
                user_data["account_value"] = round(total_deposits - total_withdrawals + total_profit, 2)
        users.append(user_data)
    
    # Sort by account value if requested (sorting happens after calculation)
    if sort_account_value and can_see_account_value:
        reverse = sort_account_value == 'desc'
        users.sort(key=lambda x: x.get('account_value', 0), reverse=reverse)
    
    return {
        "members": users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }



@router.get("/members/stats/overview")
async def get_member_stats_overview(user: dict = Depends(deps.require_admin)):
    """Return stat card counts: active members, team leaders, suspended, in danger."""
    db = deps.db

    # Exclude licensees from all counts (consistent with member list)
    base_q = {"license_type": {"$exists": False}}

    # Total active = not suspended, not deactivated
    active_count = await db.users.count_documents({
        **base_q,
        "is_suspended": {"$ne": True},
        "is_deactivated": {"$ne": True},
    })

    # Team leaders = users who have at least one referral
    # A user is a team leader if anyone has referred_by matching their referral_code or merin_referral_code
    all_codes = set()
    async for u in db.users.find(
        {"$or": [{"referral_code": {"$exists": True, "$ne": None}}, {"merin_referral_code": {"$exists": True, "$ne": None}}]},
        {"_id": 0, "referral_code": 1, "merin_referral_code": 1}
    ):
        if u.get("referral_code"):
            all_codes.add(u["referral_code"])
        if u.get("merin_referral_code"):
            all_codes.add(u["merin_referral_code"])

    team_leader_count = 0
    if all_codes:
        # Find codes that actually appear as referred_by
        pipeline = [
            {"$match": {"referred_by": {"$in": list(all_codes)}}},
            {"$group": {"_id": "$referred_by"}},
        ]
        active_codes = set()
        async for doc in db.users.aggregate(pipeline):
            active_codes.add(doc["_id"])
        # Count distinct users who own those codes
        if active_codes:
            tl_query = {"$or": [
                {"referral_code": {"$in": list(active_codes)}},
                {"merin_referral_code": {"$in": list(active_codes)}},
            ]}
            team_leader_count = await db.users.count_documents(tl_query)

    # Suspended count
    suspended_count = await db.users.count_documents({
        **base_q,
        "is_suspended": True,
    })

    # In Danger: members who haven't logged a trade in 7+ days (but are active)
    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    # Get active user IDs
    active_user_ids = []
    async for u in db.users.find(
        {**base_q, "is_suspended": {"$ne": True}, "is_deactivated": {"$ne": True}, "role": "member"},
        {"_id": 0, "id": 1}
    ):
        active_user_ids.append(u["id"])

    in_danger_count = 0
    if active_user_ids:
        # Users who have at least one trade but none in last 7 days
        users_with_recent = set()
        pipeline_recent = [
            {"$match": {"user_id": {"$in": active_user_ids}, "created_at": {"$gte": cutoff}}},
            {"$group": {"_id": "$user_id"}},
        ]
        async for doc in db.trade_logs.aggregate(pipeline_recent):
            users_with_recent.add(doc["_id"])

        # Users with at least one trade ever
        users_with_any_trade = set()
        pipeline_any = [
            {"$match": {"user_id": {"$in": active_user_ids}}},
            {"$group": {"_id": "$user_id"}},
        ]
        async for doc in db.trade_logs.aggregate(pipeline_any):
            users_with_any_trade.add(doc["_id"])

        # In danger = has traded before but not in last 7 days
        in_danger_count = len(users_with_any_trade - users_with_recent)

    return {
        "active_members": active_count,
        "team_leaders": team_leader_count,
        "suspended": suspended_count,
        "in_danger": in_danger_count,
    }


@router.get("/members/{user_id}")
async def get_member_details(user_id: str, diagnostic: str = None, user: dict = Depends(deps.require_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if diagnostic mode - handle string "true" from query param
    is_diagnostic = diagnostic is not None and diagnostic.lower() == "true"
    
    # If diagnostic mode, return detailed diagnostic data
    if is_diagnostic:
        # Get all trade logs
        all_trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        trades_sorted = sorted(all_trades, key=lambda x: x.get("created_at", ""))
        
        # Get all deposits
        all_deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        deposits_sorted = sorted(all_deposits, key=lambda x: x.get("created_at", ""))
        
        # Get reset/deleted trades
        reset_trades = await deps.db.reset_trades.find({"original_trade.user_id": user_id}, {"_id": 0}).to_list(100)
        
        # Calculate totals
        total_deposits_amt = sum(d.get("amount", 0) for d in all_deposits if d.get("amount", 0) > 0)
        total_withdrawals = sum(abs(d.get("amount", 0)) for d in all_deposits if d.get("amount", 0) < 0)
        total_profit = sum(t.get("actual_profit", 0) for t in all_trades)
        total_commission = sum(t.get("commission", 0) for t in all_trades)
        
        # Count did_not_trade entries
        did_not_trade_count = len([t for t in all_trades if t.get("did_not_trade")])
        actual_trades_count = len([t for t in all_trades if not t.get("did_not_trade")])
        
        calculated_balance = total_deposits_amt - total_withdrawals + total_profit + total_commission
        
        return {
            "user": {
                "id": member.get("id"),
                "email": member.get("email"),
                "full_name": member.get("full_name"),
                "onboarding_completed": member.get("onboarding_completed"),
                "trading_type": member.get("trading_type"),
                "trading_start_date": member.get("trading_start_date"),
                "streak_reset_date": member.get("streak_reset_date")
            },
            "summary": {
                "total_deposits": round(total_deposits_amt, 2),
                "total_withdrawals": round(total_withdrawals, 2),
                "total_profit": round(total_profit, 2),
                "total_commission": round(total_commission, 2),
                "calculated_balance": round(calculated_balance, 2),
                "total_trades": len(all_trades),
                "actual_trades": actual_trades_count,
                "did_not_trade_entries": did_not_trade_count,
                "reset_trades_count": len(reset_trades)
            },
            "trades": [
                {
                    "date": t.get("created_at", "")[:10] if t.get("created_at") else "",
                    "profit": t.get("actual_profit", 0),
                    "commission": t.get("commission", 0),
                    "did_not_trade": t.get("did_not_trade", False),
                    "lot_size": t.get("lot_size"),
                    "notes": (t.get("notes", "") or "")[:50]
                }
                for t in trades_sorted[-20:]
            ],
            "deposits": [
                {
                    "date": d.get("created_at", "")[:10] if d.get("created_at") else "",
                    "amount": d.get("amount", 0),
                    "type": d.get("type", ""),
                    "notes": (d.get("notes", "") or "")[:50]
                }
                for d in deposits_sorted[-20:]
            ],
            "reset_trades": [
                {
                    "reset_at": (r.get("reset_at", "") or "")[:19],
                    "original_date": (r.get("original_trade", {}).get("created_at", "") or "")[:10],
                    "original_profit": r.get("original_trade", {}).get("actual_profit", 0),
                    "reset_by": r.get("reset_by_name", "")
                }
                for r in reset_trades[-10:]
            ]
        }
    
    # Regular member details response
    # Get user's trades
    trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    # Get user's deposits
    deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Calculate summary
    total_trades = len(trades)
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit")
    
    # For licensees, use license.current_amount as the authoritative account_value
    # And calculate profit as current_amount - starting_amount (projected profits when manager traded)
    account_value = round(total_deposits + total_profit, 2)
    licensee_profit = None
    licensee_trades = 0
    performance_rate = 0
    
    # Always check for active license (don't rely on user.license_type which may be stale/missing)
    license = await deps.db.licenses.find_one(
        {"user_id": user_id, "is_active": True}, 
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if license:
        is_licensee_member = True
    elif member.get("license_type"):
        is_licensee_member = True
        license = None
    else:
        is_licensee_member = False
        license = None

    if is_licensee_member and license:
            try:
                starting_amount = float(license.get("starting_amount", 0) or 0)
            except (TypeError, ValueError):
                starting_amount = 0.0
            
            # For extended licensees, calculate current_amount dynamically using projections
            # This ensures consistency with /api/admin/licenses endpoint
            lt = (license.get("license_type") or "").strip().lower()
            if lt == "extended":
                try:
                    start_date_raw = license.get("start_date", "")
                    if isinstance(start_date_raw, str):
                        start_date = datetime.strptime(start_date_raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    else:
                        start_date = start_date_raw.replace(tzinfo=timezone.utc)
                    
                    today = datetime.now(timezone.utc)
                    days_since_start = (today - start_date).days
                    if days_since_start > 0:
                        projections = calculate_extended_license_projections(
                            starting_amount, 
                            start_date, 
                            min(days_since_start + 1, 365)
                        )
                        if projections:
                            account_value = projections[-1]["account_value"]
                        else:
                            account_value = starting_amount
                    else:
                        account_value = starting_amount
                except Exception as e:
                    logger.error(f"Extended license calc failed for {user_id}: {e}")
                    account_value = float(license.get("current_amount", starting_amount) or starting_amount)
            else:
                # Honorary licensees: dynamically calculate current_amount
                try:
                    from utils.calculations import calculate_honorary_licensee_value
                    account_value = await calculate_honorary_licensee_value(deps.db, license)
                except Exception as e:
                    logger.error(f"Honorary calc failed in member_details for {user_id}: {e}", exc_info=True)
                    account_value = float(license.get("current_amount", starting_amount) or starting_amount)
            
            # For licensees, profit = current_amount - starting_amount
            licensee_profit = round(float(account_value) - starting_amount, 2)
            
            # Count Master Admin trades (days when manager traded that benefited this licensee)
            # Exclude did_not_trade entries
            master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1})
            if master_admin:
                effective_start = license.get("effective_start_date", license.get("start_date"))
                
                match_cond = {"user_id": master_admin["id"], "did_not_trade": {"$ne": True}}
                if effective_start:
                    if isinstance(effective_start, str):
                        start_dt = datetime.strptime(effective_start[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    else:
                        start_dt = effective_start.replace(tzinfo=timezone.utc)
                    match_cond["created_at"] = {"$gte": start_dt.isoformat()}
                
                master_trades = await deps.db.trade_logs.find(match_cond, {"_id": 0, "created_at": 1}).to_list(1000)
                unique_dates = set()
                for trade in master_trades:
                    created = trade.get("created_at", "")
                    if created:
                        date_str = str(created)[:10]
                        unique_dates.add(date_str)
                licensee_trades = len(unique_dates)
            
            # For licensees, performance_rate is always 100% if they have profit (they get exactly projected)
            if starting_amount > 0:
                performance_rate = round((float(account_value) / float(starting_amount)) * 100 - 100, 2)  # Growth rate
    else:
        # Regular user performance rate
        total_projected = sum(t.get("projected_profit", 0) for t in trades)
        if total_projected > 0:
            performance_rate = round((total_profit / total_projected) * 100, 2)
    
    # Get family member count for honorary_fa licensees
    family_member_count = 0
    if license and _is_honorary(license.get("license_type")):
        family_member_count = await deps.db.family_members.count_documents(
            {"parent_user_id": user_id, "is_active": True}
        )

    return {
        "user": member,
        "stats": {
            "total_trades": licensee_trades if licensee_profit is not None else total_trades,
            "total_profit": round(float(licensee_profit), 2) if licensee_profit is not None else round(float(total_profit), 2),
            "total_actual_profit": round(float(licensee_profit), 2) if licensee_profit is not None else round(float(total_profit), 2),
            "total_deposits": round(float(total_deposits), 2),
            "account_value": round(float(account_value), 2),
            "performance_rate": round(float(performance_rate), 2),
            "is_licensee": is_licensee_member and license is not None,
            "family_member_count": family_member_count,
            "license_type": license.get("license_type") if license else None,
            "starting_amount": round(float(starting_amount), 2) if is_licensee_member and license else 0,
        },
        "recent_trades": trades[:10],
        "recent_deposits": deposits[:10]
    }


@router.get("/members/{user_id}/deposits")
async def get_member_deposits(user_id: str, user: dict = Depends(deps.require_admin)):
    """Get all deposits for a specific member (admin only)"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    deposits = await deps.db.deposits.find(
        {"user_id": user_id, "is_withdrawal": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    return deposits


@router.get("/members/{user_id}/withdrawals")
async def get_member_withdrawals(user_id: str, user: dict = Depends(deps.require_admin)):
    """Get all withdrawals for a specific member (admin only)"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    withdrawals = await deps.db.deposits.find(
        {"user_id": user_id, "is_withdrawal": True},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    return withdrawals


@router.delete("/members/{user_id}/trades/{trade_id}")
async def delete_member_trade(user_id: str, trade_id: str, user: dict = Depends(deps.require_master_admin)):
    """Delete a specific trade for a member and deduct profit from balance (Master Admin only)"""
    
    # Verify member exists
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the trade
    trade = await deps.db.trade_logs.find_one({"id": trade_id, "user_id": user_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found for this user")
    
    actual_profit = trade.get("actual_profit", 0)
    commission = trade.get("commission", 0)
    total_deduction = actual_profit + commission
    
    # Store in audit trail
    audit_record = {
        "id": str(uuid.uuid4()),
        "action": "admin_trade_delete",
        "trade_id": trade_id,
        "user_id": user_id,
        "admin_id": user["id"],
        "admin_name": user.get("full_name", "Admin"),
        "trade_data": trade,
        "profit_deducted": total_deduction,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await deps.db.audit_logs.insert_one(audit_record)
    
    # Delete the trade
    await deps.db.trade_logs.delete_one({"id": trade_id})
    
    # Also delete any associated deposit (if trade was forwarded to profit)
    await deps.db.deposits.delete_many({"trade_id": trade_id})
    
    # Create a negative deposit to deduct the profit from balance
    if total_deduction > 0:
        deduction_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": -total_deduction,  # Negative to deduct from balance
            "type": "admin_adjustment",
            "notes": f"Admin deleted trade from {trade.get('created_at', 'unknown date')}. Profit deducted: ${actual_profit:.2f}, Commission: ${commission:.2f}",
            "is_withdrawal": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "admin_id": user["id"]
        }
        await deps.db.deposits.insert_one(deduction_record)
    
    return {
        "message": "Trade deleted successfully",
        "profit_deducted": total_deduction,
        "trade_id": trade_id
    }


@router.put("/members/{user_id}")
async def update_member(user_id: str, data: AdminUserUpdate, user: dict = Depends(deps.require_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.full_name:
        update_data["full_name"] = data.full_name
    if data.timezone:
        update_data["timezone"] = data.timezone
    if data.lot_size is not None:
        update_data["lot_size"] = data.lot_size
    if data.merin_referral_code is not None:
        update_data["merin_referral_code"] = data.merin_referral_code.strip().upper() if data.merin_referral_code else ""
    
    # Only super_admin or master_admin can update allowed_dashboards
    if data.allowed_dashboards is not None and user.get("role") in ["super_admin", "master_admin"]:
        update_data["allowed_dashboards"] = data.allowed_dashboards
    
    # Only master_admin can change roles, email, and trading_start_date
    if user.get("role") == "master_admin":
        if data.role:
            update_data["role"] = data.role
        if data.email:
            update_data["email"] = data.email.lower()
        if data.trading_start_date:
            update_data["trading_start_date"] = data.trading_start_date
        if data.referred_by_user_id is not None:
            if data.referred_by_user_id == "":
                # Clear inviter
                update_data["referred_by"] = None
                update_data["referred_by_user_id"] = None
            else:
                inviter = await deps.db.users.find_one(
                    {"id": data.referred_by_user_id},
                    {"_id": 0, "id": 1, "referral_code": 1, "merin_referral_code": 1},
                )
                if inviter:
                    code = inviter.get("referral_code") or inviter.get("merin_referral_code") or inviter["id"]
                    update_data["referred_by"] = code
                    update_data["referred_by_user_id"] = inviter["id"]
    
    await deps.db.users.update_one({"id": user_id}, {"$set": update_data})
    return {"message": "User updated"}


@router.post("/members/{user_id}/suspend")
async def suspend_member(user_id: str, user: dict = Depends(deps.require_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    if member.get("role") == "super_admin" and user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Cannot suspend super admin")
    
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {"is_suspended": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "User suspended"}


@router.post("/members/{user_id}/unsuspend")
async def unsuspend_member(user_id: str, user: dict = Depends(deps.require_admin)):
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {"is_suspended": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "User unsuspended"}


@router.post("/members/{user_id}/fix-trading-start")
async def fix_trading_start_date(user_id: str, user: dict = Depends(deps.require_admin)):
    """Auto-fix trading_start_date based on the user's first trade"""
    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only master admin can fix trading start date")
    
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the user's first trade (excluding did_not_trade entries)
    first_trade = await deps.db.trade_logs.find_one(
        {"user_id": user_id, "did_not_trade": {"$ne": True}},
        {"_id": 0, "created_at": 1},
        sort=[("created_at", 1)]
    )
    
    if not first_trade:
        # No trades found, check for first deposit instead
        first_deposit = await deps.db.deposits.find_one(
            {"user_id": user_id},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", 1)]
        )
        if first_deposit:
            first_date = first_deposit.get("created_at", "")[:10]
        else:
            raise HTTPException(status_code=400, detail="No trades or deposits found for this user")
    else:
        first_date = first_trade.get("created_at", "")[:10]
    
    if not first_date:
        raise HTTPException(status_code=400, detail="Could not determine first trade date")
    
    # Update the user's trading_start_date
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {
            "trading_start_date": first_date,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": f"Trading start date set to {first_date}",
        "trading_start_date": first_date
    }


@router.delete("/members/{user_id}")
async def delete_member(user_id: str, user: dict = Depends(deps.require_super_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    if member.get("role") == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot delete super admin")
    
    # Delete user and related data
    await deps.db.users.delete_one({"id": user_id})
    await deps.db.deposits.delete_many({"user_id": user_id})
    await deps.db.trade_logs.delete_many({"user_id": user_id})
    await deps.db.debts.delete_many({"user_id": user_id})
    await deps.db.goals.delete_many({"user_id": user_id})
    
    return {"message": "User and all related data deleted"}


@router.post("/members/{user_id}/set-temp-password")
async def set_temp_password(user_id: str, data: TempPasswordSet, user: dict = Depends(deps.require_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Set temporary password and flag for forced change
    new_hash = deps.hash_password(data.temp_password)
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password": new_hash,
            "must_change_password": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # TODO: Send email with temp password via Emailit
    
    return {"message": "Temporary password set. User will be prompted to change on next login."}


@router.get("/members/{user_id}/simulate")
async def simulate_member_view(user_id: str, user: dict = Depends(deps.require_master_admin)):
    """Master Admin only: Get all data to simulate viewing as a specific member"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get member's deposits
    deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Get member's trades
    trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Get member's debts
    debts = await deps.db.debts.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get member's goals
    goals = await deps.db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Calculate account value
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit" and d.get("type") != "withdrawal")
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    account_value = round(total_deposits - total_withdrawals + total_profit, 2)
    
    # For licensees, use dynamic calculation for accurate account value
    # Always check licenses collection directly (don't rely on user.license_type)
    license = await deps.db.licenses.find_one({"user_id": user_id, "is_active": True}, {"_id": 0})
    if license:
        if _is_honorary(license.get("license_type")):
            from utils.calculations import calculate_honorary_licensee_value
            account_value = await calculate_honorary_licensee_value(deps.db, license)
        else:
            account_value = round(license.get("current_amount", license.get("starting_amount", 0)), 2)
        total_deposits = round(license.get("starting_amount", 0), 2)
        total_profit = round(account_value - total_deposits, 2)
    
    # Calculate LOT size
    lot_size = truncate_lot_size(account_value) if account_value > 0 else 0
    
    # Get family members for honorary_fa licensees
    family_members = []
    if license and _is_honorary(license.get("license_type")):
        raw_members = await deps.db.family_members.find(
            {"parent_user_id": user_id, "is_active": True}, {"_id": 0}
        ).to_list(100)
        from routes.family import calculate_family_member_value
        for fm in raw_members:
            fm_value = await calculate_family_member_value(deps.db, fm)
            family_members.append({
                **fm,
                "account_value": fm_value,
                "profit": round(fm_value - fm.get("starting_amount", 0), 2)
            })

    return {
        "member": member,
        "account_value": account_value,
        "lot_size": lot_size,
        "total_deposits": round(total_deposits, 2),
        "total_withdrawals": round(total_withdrawals, 2),
        "total_profit": round(total_profit, 2),
        "deposits": deposits,
        "trades": trades[:20],
        "debts": debts,
        "goals": goals,
        "family_members": family_members,
        "license_type": license.get("license_type") if license else member.get("license_type"),
        "is_licensee": license is not None,
        "summary": {
            "total_trades": len(trades),
            "winning_trades": len([t for t in trades if t.get("performance") in ["exceeded", "perfect"]]),
            "total_debts": len(debts),
            "total_goals": len(goals)
        }
    }


@router.get("/signals/history")
async def get_signals_history(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(deps.require_admin)
):
    """Get paginated signal history"""
    skip = (page - 1) * page_size
    
    total = await deps.db.trading_signals.count_documents({})
    signals = await deps.db.trading_signals.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "signals": signals,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.get("/signals/archive")
async def get_signals_archive(user: dict = Depends(deps.require_admin)):
    """Get signals organized by month"""
    signals = await deps.db.trading_signals.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Organize by month
    archive = {}
    for signal in signals:
        created_at = signal.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        month_key = created_at.strftime("%Y-%m")  # e.g., "2026-01"
        month_label = created_at.strftime("%B %Y")  # e.g., "January 2026"
        
        if month_key not in archive:
            archive[month_key] = {
                "month_key": month_key,
                "month_label": month_label,
                "signals": []
            }
        archive[month_key]["signals"].append(signal)
    
    # Convert to sorted list (newest first)
    months = sorted(archive.values(), key=lambda x: x["month_key"], reverse=True)
    
    return {"months": months}


@router.post("/signals/archive-month")
async def archive_current_month_signals(user: dict = Depends(deps.require_super_admin)):
    """Archive all signals from the current month"""
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get signals from current month that are not active
    signals_to_archive = await deps.db.trading_signals.find({
        "created_at": {"$gte": start_of_month.isoformat()},
        "is_active": False
    }, {"_id": 0}).to_list(1000)
    
    if not signals_to_archive:
        return {"message": "No inactive signals to archive", "archived_count": 0}
    
    # Mark them as archived
    archived_count = 0
    for signal in signals_to_archive:
        await deps.db.trading_signals.update_one(
            {"id": signal["id"]},
            {"$set": {"is_archived": True}}
        )
        archived_count += 1
    
    return {"message": f"Archived {archived_count} signals", "archived_count": archived_count}


@router.get("/analytics/team")
async def get_team_analytics(user: dict = Depends(deps.require_admin)):
    """Get collective team analytics: total account value, profit, traders, performance
    Note: Honorary Licensees are excluded from team totals but still shown in member stats"""
    
    # Get all users including admins (include all roles in team stats)
    all_users = await deps.db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    # Include all users: members, admins, super_admins, master_admin
    active_users = [u for u in all_users if not u.get("is_suspended", False)]
    
    # Get all active licenses to check for licensed users (both extended and honorary are excluded)
    all_licenses = await deps.db.licenses.find({"is_active": True}, {"_id": 0}).to_list(1000)
    licensed_user_ids = set(lic["user_id"] for lic in all_licenses)
    honorary_user_ids = set(
        lic["user_id"] for lic in all_licenses 
        if _is_honorary(lic.get("license_type"))
    )
    extended_user_ids = set(
        lic["user_id"] for lic in all_licenses 
        if lic.get("license_type") == "extended"
    )
    
    total_account_value = 0
    total_profit = 0
    total_trades = 0
    winning_trades = 0
    
    member_stats = []
    
    for member in active_users:
        user_id = member["id"]
        is_licensed = user_id in licensed_user_ids
        is_honorary = user_id in honorary_user_ids
        is_extended = user_id in extended_user_ids
        
        # Get deposits
        deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit", "withdrawal"])
        total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
        
        # Get trades
        trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        user_profit = sum(t.get("actual_profit", 0) for t in trades)
        
        # For licensees, use dynamic calculation for account value
        if is_licensed:
            license = next((lic for lic in all_licenses if lic["user_id"] == user_id), None)
            if license and _is_honorary(license.get("license_type")):
                from utils.calculations import calculate_honorary_licensee_value
                user_account_value = await calculate_honorary_licensee_value(deps.db, license)
            elif license:
                user_account_value = license.get("current_amount", license.get("starting_amount", 0))
            else:
                user_account_value = 0
        else:
            user_account_value = total_deposits - total_withdrawals + user_profit
        
        # Only add to team totals if NOT a licensed user (both extended and honorary are excluded)
        if not is_licensed:
            total_account_value += user_account_value
            total_profit += user_profit
        
        # Always count trades for performance tracking
        total_trades += len(trades)
        winning_trades += len([t for t in trades if t.get("performance") in ["exceeded", "perfect"]])
        
        member_stats.append({
            "id": user_id,
            "name": member.get("full_name", "Unknown"),
            "email": member.get("email", ""),
            "role": member.get("role", "member"),
            "account_value": round(user_account_value, 2),
            "total_profit": round(user_profit, 2),
            "trades_count": len(trades),
            "is_licensed": is_licensed,
            "is_honorary": is_honorary,
            "is_extended": is_extended
        })
    
    # Calculate performance rate
    performance_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    return {
        "total_account_value": round(total_account_value, 2),
        "total_profit": round(total_profit, 2),
        "total_traders": len(active_users),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "performance_rate": round(performance_rate, 1),
        "member_stats": sorted(member_stats, key=lambda x: x["total_profit"], reverse=True),
        "licensed_excluded_count": len(licensed_user_ids),
        "honorary_count": len(honorary_user_ids),
        "extended_count": len(extended_user_ids)
    }


@router.get("/analytics/missed-trades")
async def get_missed_trades(user: dict = Depends(deps.require_admin)):
    """Get members with undeclared trading days (days with signals but no trade entry and not marked as 'did not trade')"""
    
    # Get all member users
    all_users = await deps.db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    member_users = [u for u in all_users if u.get("role") == "member"]
    
    # Get all signals to determine trading days (use trading_signals collection)
    all_signals = await deps.db.trading_signals.find({}, {"_id": 0}).to_list(500)
    
    # Create a set of all trading dates (dates with signals)
    trading_dates = set()
    for signal in all_signals:
        if signal.get("created_at"):
            signal_date = signal["created_at"].split("T")[0]
            trading_dates.add(signal_date)
    
    # Get today's date
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()
    
    # Get all trade logs (includes both actual trades and "did not trade" declarations)
    all_trades = await deps.db.trade_logs.find({}, {"_id": 0}).to_list(10000)
    
    # Get all user holidays
    all_holidays = await deps.db.user_holidays.find({}, {"_id": 0}).to_list(5000)
    
    # Build a map of user_id -> set of dates they have accounted for (traded OR declared did_not_trade OR holiday)
    user_accounted_dates = {}
    
    # Add trade log dates (both actual trades and did_not_trade entries)
    for trade in all_trades:
        user_id = trade.get("user_id")
        if user_id:
            if user_id not in user_accounted_dates:
                user_accounted_dates[user_id] = set()
            trade_date = trade.get("created_at", "").split("T")[0]
            if trade_date:
                user_accounted_dates[user_id].add(trade_date)
    
    # Add user holiday dates
    for holiday in all_holidays:
        user_id = holiday.get("user_id")
        holiday_date = holiday.get("date", "").split("T")[0] if holiday.get("date") else None
        if user_id and holiday_date:
            if user_id not in user_accounted_dates:
                user_accounted_dates[user_id] = set()
            user_accounted_dates[user_id].add(holiday_date)
    
    # Find members with undeclared trading days
    missed_traders = []
    for member in member_users:
        user_id = member["id"]
        member_join_date = member.get("created_at", "").split("T")[0] if member.get("created_at") else "2000-01-01"
        
        # Get dates this member has accounted for
        accounted_dates = user_accounted_dates.get(user_id, set())
        
        # Find undeclared trading days (signal dates after member joined, up to today, not accounted for)
        undeclared_dates = []
        for signal_date in trading_dates:
            # Only count dates after member joined and up to today
            if signal_date >= member_join_date and signal_date <= today_str:
                if signal_date not in accounted_dates:
                    undeclared_dates.append(signal_date)
        
        undeclared_count = len(undeclared_dates)
        
        if undeclared_count > 0:
            # Get last trade date (actual trades only, not did_not_trade)
            member_actual_trades = [t for t in all_trades if t.get("user_id") == user_id and not t.get("did_not_trade")]
            last_trade_at = None
            if member_actual_trades:
                sorted_trades = sorted(member_actual_trades, key=lambda x: x.get("created_at", ""), reverse=True)
                last_trade_at = sorted_trades[0].get("created_at")
            
            missed_traders.append({
                "id": member["id"],
                "full_name": member.get("full_name", "Unknown"),
                "email": member.get("email", ""),
                "last_trade_at": last_trade_at,
                "undeclared_count": undeclared_count,
                "undeclared_dates": sorted(undeclared_dates)[-5:]  # Last 5 undeclared dates for reference
            })
    
    # Sort by most undeclared days first
    missed_traders.sort(key=lambda x: x["undeclared_count"], reverse=True)
    
    # Calculate today's team stats
    today_trades = [t for t in all_trades if t.get("created_at", "").startswith(today_str) and not t.get("did_not_trade")]
    team_profit_today = sum(t.get("actual_profit", 0) for t in today_trades)
    users_who_traded_today = set(t.get("user_id") for t in today_trades)
    
    highest_earner = None
    highest_profit = 0
    for trade in today_trades:
        if trade.get("actual_profit", 0) > highest_profit:
            highest_profit = trade.get("actual_profit", 0)
            user_data = next((u for u in all_users if u["id"] == trade.get("user_id")), None)
            if user_data:
                highest_earner = user_data.get("full_name", "Unknown")
    
    return {
        "missed_traders": missed_traders,
        "team_profit_today": round(team_profit_today, 2),
        "highest_earner": highest_earner,
        "highest_profit": round(highest_profit, 2),
        "total_traded_today": len(users_who_traded_today)
    }


@router.get("/analytics/today-stats")
async def get_today_stats(user: dict = Depends(deps.require_admin)):
    """Get today's team performance stats (profit and commissions)"""
    
    # Get today's date range
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # Get today's trades
    today_trades = await deps.db.trade_logs.find({
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0}).to_list(1000)
    
    # Calculate total profit
    total_profit = sum(t.get("actual_profit", 0) for t in today_trades)
    
    # Get today's commissions from deposits
    today_commissions = await deps.db.deposits.find({
        "type": "commission",
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0}).to_list(500)
    
    total_commission = sum(c.get("amount", 0) for c in today_commissions)
    
    return {
        "total_profit": round(total_profit, 2),
        "total_commission": round(total_commission, 2),
        "trades_count": len(today_trades)
    }


@router.post("/analytics/notify-missed")
async def notify_missed_trade(data: NotifyMissedTradeRequest, user: dict = Depends(deps.require_admin)):
    """Send email to member who missed the trade"""
    member = await deps.db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get today's stats
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    today_trades = await deps.db.trade_logs.find({
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0}).to_list(1000)
    
    team_profit = sum(t.get("actual_profit", 0) for t in today_trades)
    
    # Find highest earner
    highest_earner = "the team"
    highest_profit = 0
    for trade in today_trades:
        if trade.get("actual_profit", 0) > highest_profit:
            highest_profit = trade.get("actual_profit", 0)
            trader = await deps.db.users.find_one({"id": trade.get("user_id")}, {"_id": 0})
            if trader:
                highest_earner = trader.get("full_name", "a teammate")
    
    # Create email content
    subject = "You Missed Today's Trade! 🚨"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #18181B; color: #fff; padding: 40px; border-radius: 16px;">
        <h1 style="color: #EF4444; margin-bottom: 20px;">You Missed Today's Trade!</h1>
        <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6;">
            Hey {member.get('full_name', 'Trader')},
        </p>
        <div style="background: linear-gradient(135deg, #1E3A5F 0%, #1E1E3F 100%); padding: 30px; border-radius: 12px; margin: 20px 0;">
            <p style="color: #fff; font-size: 18px; margin: 0;">
                The team earned <span style="color: #10B981; font-weight: bold; font-size: 24px;">${team_profit:.2f}</span> today,
                but you weren't a part of it.
            </p>
            <p style="color: #A1A1AA; margin-top: 15px;">
                The highest earner is <span style="color: #3B82F6; font-weight: bold;">{highest_earner}</span> 
                with <span style="color: #10B981;">${highest_profit:.2f}</span>!
            </p>
        </div>
        <p style="color: #FBBF24; font-size: 18px; font-weight: bold; text-align: center;">
            🔔 Remember to join us for tomorrow's trade!
        </p>
        <hr style="border: none; border-top: 1px solid #27272A; margin: 30px 0;">
        <p style="color: #71717A; font-size: 12px; text-align: center;">
            CrossCurrent Finance Center - Your Trading Success Partner
        </p>
    </div>
    """
    
    if not EMAILIT_API_KEY:
        # Return preview if email not configured
        return {
            "message": "Email preview (Emailit not configured)",
            "preview": {
                "to": member.get("email"),
                "subject": subject,
                "team_profit": round(team_profit, 2),
                "highest_earner": highest_earner,
                "highest_profit": round(highest_profit, 2)
            }
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.emailit.com/v1/emails",
                headers={
                    "Authorization": f"Bearer {EMAILIT_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "noreply@crosscurrent.finance",
                    "to": member["email"],
                    "subject": subject,
                    "html": html_body
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to send email")
                
        return {"message": f"Notification sent to {member.get('full_name')}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")


@router.get("/analytics/growth-data")
async def get_growth_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(deps.require_admin)
):
    """Get historical data for growth charts with optional date filtering"""
    
    # Build query filter
    query = {}
    
    # Get all trades sorted by date
    all_trades = await deps.db.trade_logs.find({}, {"_id": 0}).sort("created_at", 1).to_list(10000)
    
    # Get all deposits sorted by date
    all_deposits = await deps.db.deposits.find({}, {"_id": 0}).sort("created_at", 1).to_list(10000)
    
    # Build daily aggregates
    daily_data = {}
    running_account_value = 0
    running_profit = 0
    running_trades = 0
    running_winning = 0
    
    for deposit in all_deposits:
        date_str = deposit.get("created_at", "")[:10]  # Get YYYY-MM-DD
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "deposits": 0,
                "withdrawals": 0,
                "profit": 0,
                "trades": 0,
                "winning": 0
            }
        
        if deposit.get("type") == "withdrawal":
            daily_data[date_str]["withdrawals"] += abs(deposit.get("amount", 0))
        else:
            daily_data[date_str]["deposits"] += deposit.get("amount", 0)
    
    for trade in all_trades:
        date_str = trade.get("created_at", "")[:10]
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "deposits": 0,
                "withdrawals": 0,
                "profit": 0,
                "trades": 0,
                "winning": 0
            }
        
        daily_data[date_str]["profit"] += trade.get("actual_profit", 0)
        daily_data[date_str]["trades"] += 1
        if trade.get("performance") in ["exceeded", "perfect"]:
            daily_data[date_str]["winning"] += 1
    
    # Build cumulative chart data with optional date filtering
    chart_data = []
    for date_str in sorted(daily_data.keys()):
        day = daily_data[date_str]
        running_account_value += day["deposits"] - day["withdrawals"] + day["profit"]
        running_profit += day["profit"]
        running_trades += day["trades"]
        running_winning += day["winning"]
        
        # Apply date filter
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
        
        performance_rate = (running_winning / running_trades * 100) if running_trades > 0 else 0
        
        chart_data.append({
            "date": date_str,
            "account_value": round(running_account_value, 2),
            "total_profit": round(running_profit, 2),
            "total_trades": running_trades,
            "performance_rate": round(performance_rate, 1)
        })
    
    # If no date filter, return last 30 points; otherwise return all filtered data
    if not start_date and not end_date:
        return {"chart_data": chart_data[-30:]}
    return {"chart_data": chart_data}


@router.get("/analytics/member/{user_id}")
async def get_member_analytics(user_id: str, user: dict = Depends(deps.require_admin)):
    """Get individual member analytics"""
    
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get deposits
    deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit", "withdrawal"])
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
    
    # Get trades
    trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    account_value = total_deposits - total_withdrawals + total_profit
    
    winning_trades = len([t for t in trades if t.get("performance") in ["exceeded", "perfect"]])
    performance_rate = (winning_trades / len(trades) * 100) if trades else 0
    
    # Build daily trade history for chart
    trade_history = {}
    for trade in trades:
        date_str = trade.get("created_at", "")[:10]
        if date_str not in trade_history:
            trade_history[date_str] = {"date": date_str, "profit": 0, "trades": 0}
        trade_history[date_str]["profit"] += trade.get("actual_profit", 0)
        trade_history[date_str]["trades"] += 1
    
    return {
        "member": {
            "id": member["id"],
            "name": member.get("full_name", "Unknown"),
            "email": member.get("email", ""),
            "role": member.get("role", "member"),
            "timezone": member.get("timezone", "Asia/Manila"),
            "joined": member.get("created_at", "")
        },
        "stats": {
            "account_value": round(account_value, 2),
            "lot_size": truncate_lot_size(account_value) if account_value > 0 else 0,
            "total_deposits": round(total_deposits, 2),
            "total_withdrawals": round(total_withdrawals, 2),
            "total_profit": round(total_profit, 2),
            "total_trades": len(trades),
            "winning_trades": winning_trades,
            "performance_rate": round(performance_rate, 1)
        },
        "recent_trades": trades[:10],
        "trade_history": sorted(trade_history.values(), key=lambda x: x["date"])[-30:]
    }


@router.get("/analytics/recent-trades")
async def get_recent_team_trades(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(deps.require_admin)
):
    """Get recent trades from all team members with pagination"""
    
    # Get all users for name lookup
    all_users = await deps.db.users.find({}, {"_id": 0, "id": 1, "full_name": 1}).to_list(1000)
    user_names = {u["id"]: u.get("full_name", "Unknown") for u in all_users}
    
    skip = (page - 1) * page_size
    total = await deps.db.trade_logs.count_documents({})
    
    trades = await deps.db.trade_logs.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Add user names to trades and ensure commission field is present
    enriched_trades = []
    for trade in trades:
        trade["trader_name"] = user_names.get(trade.get("user_id"), "Unknown")
        trade["commission"] = trade.get("commission", 0)  # Default to 0 for backward compatibility
        enriched_trades.append(trade)
    
    return {
        "trades": enriched_trades,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.post("/analytics/archive-trades")
async def archive_old_trades(user: dict = Depends(deps.require_super_admin)):
    """Archive trades older than 3 days, delete archive older than 2 months"""
    now = datetime.now(timezone.utc)
    
    # Archive threshold: 3 days ago
    archive_threshold = now - timedelta(days=3)
    
    # Delete threshold: 2 months ago
    delete_threshold = now - timedelta(days=60)
    
    # Delete very old archived trades
    delete_result = await deps.db.trade_logs.delete_many({
        "is_archived": True,
        "archived_at": {"$lt": delete_threshold.isoformat()}
    })
    
    # Archive trades older than 3 days
    archive_result = await deps.db.trade_logs.update_many(
        {
            "created_at": {"$lt": archive_threshold.isoformat()},
            "is_archived": {"$ne": True}
        },
        {
            "$set": {
                "is_archived": True,
                "archived_at": now.isoformat()
            }
        }
    )
    
    return {
        "archived_count": archive_result.modified_count,
        "deleted_count": delete_result.deleted_count
    }


@router.get("/notifications")
async def get_admin_notifications(
    limit: int = 50,
    unread_only: bool = False,
    user: dict = Depends(deps.require_admin)
):
    """Get notifications for admins (deposits, withdrawals, underperforming trades)"""
    # Check if user is super_admin or master_admin
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can view notifications")
    
    query = {}
    if unread_only:
        query["is_read"] = False
    
    notifications = await deps.db.admin_notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Count unread
    unread_count = await deps.db.admin_notifications.count_documents({"is_read": False})
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(deps.require_admin)):
    """Mark a notification as read"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can manage notifications")
    
    result = await deps.db.admin_notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(deps.require_admin)):
    """Mark all notifications as read"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can manage notifications")
    
    result = await deps.db.admin_notifications.update_many(
        {"is_read": False},
        {"$set": {"is_read": True}}
    )
    
    return {"message": f"Marked {result.modified_count} notifications as read"}


@router.get("/transactions")
async def get_team_transactions(
    page: int = 1,
    page_size: int = 20,
    transaction_type: Optional[str] = None,  # deposit, withdrawal, or None for all
    user_search: Optional[str] = None,
    user: dict = Depends(deps.require_admin)
):
    """Get all team transactions (deposits and withdrawals) with pagination"""
    # Check if user is super_admin or master_admin
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can view transactions")
    
    # Get all users for name lookup
    all_users = await deps.db.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "email": 1}).to_list(1000)
    user_lookup = {u["id"]: {"name": u.get("full_name", "Unknown"), "email": u.get("email", "")} for u in all_users}
    
    # CRITICAL: Build query based on filter type
    if transaction_type == "profit":
        # Show ONLY profit-type entries
        query = {"type": "profit", "user_id": {"$exists": True}}
    else:
        # Default: exclude type=profit entries
        query = {"type": {"$ne": "profit"}}
        
        if transaction_type == "withdrawal":
            query["is_withdrawal"] = True
        elif transaction_type == "deposit":
            query["$and"] = query.get("$and", [])
            query["$and"].append({"$or": [
                {"is_withdrawal": {"$ne": True}},
                {"is_withdrawal": {"$exists": False}}
            ]})
    
    # User search filter
    if user_search:
        matching_user_ids = [
            u["id"] for u in all_users
            if user_search.lower() in u.get("full_name", "").lower()
            or user_search.lower() in u.get("email", "").lower()
        ]
        query["user_id"] = {"$in": matching_user_ids}
    
    skip = (page - 1) * page_size
    total = await deps.db.deposits.count_documents(query)
    
    transactions = await deps.db.deposits.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Enrich with user info
    enriched = []
    for tx in transactions:
        user_info = user_lookup.get(tx.get("user_id"), {"name": "Unknown", "email": ""})
        tx["user_name"] = user_info["name"]
        tx["user_email"] = user_info["email"]
        if tx.get("type") == "profit":
            tx["type"] = "profit"
        elif tx.get("is_withdrawal"):
            tx["type"] = "withdrawal"
        else:
            tx["type"] = "deposit"
        enriched.append(tx)
    
    return {
        "transactions": enriched,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
    }


@router.get("/transactions/stats")
async def get_transaction_stats(user: dict = Depends(deps.require_admin)):
    """Get transaction statistics summary"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can view transaction stats")
    
    # CRITICAL: Exclude type=profit entries from all stats
    all_deposits = await deps.db.deposits.find({"type": {"$ne": "profit"}}, {"_id": 0}).to_list(10000)
    
    # Calculate stats
    deposits = [d for d in all_deposits if not d.get("is_withdrawal") and d.get("amount", 0) > 0]
    withdrawals = [d for d in all_deposits if d.get("is_withdrawal")]
    
    total_deposits = sum(d.get("amount", 0) for d in deposits)
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in withdrawals)
    
    # Get unique depositors
    unique_depositors = len(set(d.get("user_id") for d in deposits))
    
    # Get today's stats
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_deposits = sum(d.get("amount", 0) for d in deposits if d.get("created_at", "").startswith(today))
    today_withdrawals = sum(abs(d.get("amount", 0)) for d in withdrawals if d.get("created_at", "").startswith(today))
    
    return {
        "total_deposits": round(total_deposits, 2),
        "total_withdrawals": round(total_withdrawals, 2),
        "net_flow": round(total_deposits - total_withdrawals, 2),
        "deposit_count": len(deposits),
        "withdrawal_count": len(withdrawals),
        "unique_depositors": unique_depositors,
        "today_deposits": round(today_deposits, 2),
        "today_withdrawals": round(today_withdrawals, 2)
    }


@router.get("/members/{user_id}/recent-transactions")
async def get_recent_transactions(
    user_id: str,
    limit: int = Query(5, ge=1, le=20),
    admin: dict = Depends(deps.require_admin),
):
    """Get a member's most recent deposits/withdrawals for correction purposes."""
    if admin["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    txns = await deps.db.deposits.find(
        {"user_id": user_id, "type": {"$ne": "profit"}},
        {"_id": 0},
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"transactions": txns}


@router.put("/transactions/{tx_id}/correct")
async def correct_transaction(
    tx_id: str,
    body: dict = Body(...),
    admin: dict = Depends(deps.require_admin),
):
    """Admin corrects a deposit/withdrawal amount. Preserves audit trail."""
    if admin["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    new_amount = body.get("new_amount")
    reason = body.get("reason", "Admin correction")
    
    if new_amount is None:
        raise HTTPException(status_code=400, detail="new_amount is required")
    
    tx = await deps.db.deposits.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    old_amount = tx.get("amount", 0)
    now = datetime.now(timezone.utc).isoformat()
    
    # Record the correction in the transaction itself
    correction_record = {
        "old_amount": old_amount,
        "new_amount": new_amount,
        "reason": reason,
        "corrected_by": admin["id"],
        "corrected_by_name": admin.get("full_name", "Admin"),
        "corrected_at": now,
    }
    
    # Update the transaction amount and mark as corrected
    await deps.db.deposits.update_one(
        {"id": tx_id},
        {
            "$set": {
                "amount": new_amount,
                "is_corrected": True,
                "updated_at": now,
            },
            "$push": {"corrections": correction_record},
        },
    )
    
    # Log to admin audit
    await deps.db.admin_audit_log.insert_one({
        "_id": str(uuid.uuid4()),
        "action": "transaction_correction",
        "tx_id": tx_id,
        "user_id": tx.get("user_id"),
        "old_amount": old_amount,
        "new_amount": new_amount,
        "reason": reason,
        "admin_id": admin["id"],
        "admin_name": admin.get("full_name", "Admin"),
        "created_at": now,
    })
    
    return {
        "message": "Transaction corrected",
        "tx_id": tx_id,
        "old_amount": old_amount,
        "new_amount": new_amount,
        "reason": reason,
    }


@router.delete("/transactions/{tx_id}")
async def delete_transaction(
    tx_id: str,
    admin: dict = Depends(deps.require_admin),
):
    """Admin deletes a transaction. Stores in audit log."""
    if admin["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    tx = await deps.db.deposits.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Don't allow deleting type=profit entries
    if tx.get("type") == "profit":
        raise HTTPException(status_code=400, detail="Cannot delete system-generated profit entries")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Log to audit before deletion
    await deps.db.admin_audit_log.insert_one({
        "_id": str(uuid.uuid4()),
        "action": "transaction_deletion",
        "tx_id": tx_id,
        "user_id": tx.get("user_id"),
        "deleted_transaction": tx,
        "admin_id": admin["id"],
        "admin_name": admin.get("full_name", "Admin"),
        "created_at": now,
    })
    
    await deps.db.deposits.delete_one({"id": tx_id})
    
    return {"message": "Transaction deleted", "tx_id": tx_id}


@router.get("/licenses")
async def get_all_licenses(user: dict = Depends(deps.require_admin)):
    """Get all licensed users (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can manage licenses")
    
    licenses = await deps.db.licenses.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with user info (including timezone for profile editing)
    all_users = await deps.db.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "email": 1, "timezone": 1}).to_list(1000)
    user_lookup = {u["id"]: u for u in all_users}
    
    enriched = []
    for lic in licenses:
        user_info = user_lookup.get(lic["user_id"], {})
        lic["user_name"] = user_info.get("full_name", "Unknown")
        lic["user_email"] = user_info.get("email", "")
        lic["user_timezone"] = user_info.get("timezone", "Asia/Manila")
        
        # Calculate current amount dynamically based on license type
        if lic.get("is_active"):
            if _is_honorary(lic.get("license_type")):
                # Dynamic calculation for honorary licensees
                try:
                    from utils.calculations import calculate_honorary_licensee_value
                    lic["current_amount"] = await calculate_honorary_licensee_value(deps.db, lic)
                except Exception as e:
                    import logging
                    logging.getLogger("server").error(f"Failed to calculate honorary value for {lic.get('user_id')}: {e}")
                    lic["current_amount"] = lic.get("current_amount") or lic.get("starting_amount", 0)
            elif lic["license_type"] == "extended":
                # Parse start_date - handle both string and datetime formats
                start_date_raw = lic.get("start_date", "")
                if isinstance(start_date_raw, str):
                    start_date = datetime.strptime(start_date_raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    start_date = start_date_raw.replace(tzinfo=timezone.utc)
                
                today = datetime.now(timezone.utc)
                days_since_start = (today - start_date).days
                if days_since_start > 0:
                    projections = calculate_extended_license_projections(
                        lic["starting_amount"], 
                        start_date, 
                        min(days_since_start + 1, 365)
                    )
                    if projections:
                        lic["current_amount"] = projections[-1]["account_value"]
                    else:
                        lic["current_amount"] = lic["starting_amount"]
                else:
                    lic["current_amount"] = lic["starting_amount"]
            else:
                lic["current_amount"] = lic.get("starting_amount", 0)
        else:
            lic["current_amount"] = lic.get("starting_amount", 0)
        
        enriched.append(lic)
    
    return {"licenses": enriched}


@router.post("/licenses")
async def create_license(data: LicenseCreate, user: dict = Depends(deps.require_admin)):
    """Create a new license for a user (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can create licenses")
    
    # Verify target user exists
    target_user = await deps.db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user already has an active license
    existing = await deps.db.licenses.find_one({"user_id": data.user_id, "is_active": True}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="User already has an active license")
    
    # Validate license type
    if data.license_type not in ["extended", "honorary", "honorary_fa"]:
        raise HTTPException(status_code=400, detail="Invalid license type. Must be 'extended', 'honorary', or 'honorary_fa'")
    
    # Determine start date
    if data.start_date:
        start_date = datetime.fromisoformat(data.start_date)
    else:
        # Default to first trading day of current quarter
        today = datetime.now(timezone.utc)
        q = get_quarter(today)
        quarter_start_month = (q - 1) * 3 + 1
        start_date = datetime(today.year, quarter_start_month, 1, tzinfo=timezone.utc)
        # Advance to first weekday if it falls on a weekend
        while start_date.weekday() >= 5:
            start_date += timedelta(days=1)
    
    license_id = str(uuid.uuid4())
    license_doc = {
        "id": license_id,
        "user_id": data.user_id,
        "license_type": data.license_type,
        "starting_amount": data.starting_amount,
        "current_amount": data.starting_amount,  # Set current_amount = starting_amount
        "start_date": start_date.isoformat(),
        "notes": data.notes,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    
    await deps.db.licenses.insert_one(license_doc)
    
    # Update user record with license type and account_value
    await deps.db.users.update_one(
        {"id": data.user_id},
        {"$set": {
            "license_type": data.license_type,
            "account_value": data.starting_amount  # Sync account_value with license
        }}
    )
    
    # Record the starting amount as an initial deposit transaction
    if data.starting_amount > 0:
        initial_deposit = {
            "id": str(uuid.uuid4()),
            "user_id": data.user_id,
            "type": "deposit",
            "amount": data.starting_amount,
            "status": "completed",
            "deposit_date": start_date.isoformat(),
            "notes": "Initial starting balance",
            "is_initial_balance": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "completed_by": user["id"]
        }
        await deps.db.licensee_transactions.insert_one(initial_deposit)
    
    return {"message": "License created successfully", "license_id": license_id}


@router.get("/licenses/{license_id}")
async def get_license_details(license_id: str, user: dict = Depends(deps.require_admin)):
    """Get detailed license information including projections"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view license details")
    
    license_doc = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get user info
    target_user = await deps.db.users.find_one({"id": license_doc["user_id"]}, {"_id": 0, "password": 0})
    
    result = {
        "license": license_doc,
        "user": target_user
    }
    
    # Calculate projections for extended licensees
    if license_doc["license_type"] == "extended":
        start_date = datetime.fromisoformat(license_doc["start_date"].replace("Z", "+00:00"))
        projections = calculate_extended_license_projections(
            license_doc["starting_amount"],
            start_date,
            365  # 1 year projection
        )
        result["projections"] = projections
        
        # Get current values
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")
        current_projection = next((p for p in projections if p["date"] == today_str), None)
        if current_projection:
            result["current_values"] = current_projection
        elif projections:
            # Find the most recent trading day
            result["current_values"] = projections[-1]
    
    return result


@router.get("/licenses/{license_id}/projections")
async def get_license_projections(license_id: str, user: dict = Depends(deps.require_admin)):
    """Get daily projections for a specific license (for simulation view)
    
    This endpoint returns projections that can be used by the frontend
    when the Master Admin is simulating a licensee's view.
    """
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view license projections")
    
    license_doc = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Use effective_start_date if available, otherwise start_date
    effective_start = license_doc.get("effective_start_date") or license_doc.get("start_date")
    if effective_start:
        # Handle various date formats
        if "T" in effective_start:
            # Full datetime string
            start_date = datetime.fromisoformat(effective_start.replace("Z", "+00:00") if "Z" in effective_start else effective_start)
        else:
            # Date-only string (YYYY-MM-DD) - parse and add timezone
            start_date = datetime.strptime(effective_start[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        # Ensure timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
    else:
        start_date = datetime.now(timezone.utc)
    
    starting_amount = license_doc.get("starting_amount", 0)
    current_amount = license_doc.get("current_amount", starting_amount)
    
    # Get Master Admin's trade logs to determine which days manager traded
    master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1})
    master_trade_logs = {}
    if master_admin:
        trades = await deps.db.trade_logs.find(
            {"user_id": master_admin["id"], "did_not_trade": {"$ne": True}},
            {"_id": 0, "created_at": 1, "trade_date": 1, "actual_profit": 1, "commission": 1}
        ).to_list(1000)
        for trade in trades:
            date_key = trade.get("trade_date") or trade.get("created_at", "")[:10]
            if date_key:
                master_trade_logs[date_key] = {
                    "traded": True,
                    "actual_profit": trade.get("actual_profit", 0),
                    "commission": trade.get("commission", 0)
                }
    
    # Get trade overrides for this license
    overrides = {}
    async for override in deps.db.licensee_trade_overrides.find({"license_id": license_id}, {"_id": 0}):
        overrides[override["date"]] = override
    
    # Generate projections for up to 2 years from start date
    # Formula: daily_profit = round((balance_at_quarter_start / 980) * 15, 2)
    # Daily profit is FIXED for the entire quarter, recalculated at each new calendar quarter
    from utils.trading_days import get_holidays_for_range, is_trading_day as is_trading_day_with_holidays
    
    projections = []
    current_balance = starting_amount
    
    # Track quarter for quarterly compounding
    current_quarter = get_quarter(start_date)
    current_year = start_date.year
    
    # Calculate initial daily profit (with truncated lot_size)
    quarter_daily_profit = round(truncate_lot_size(current_balance) * 15, 2)
    
    # Generate projections day by day
    current_date = start_date
    today = datetime.now(timezone.utc)
    end_date = today + timedelta(days=365)
    holidays = get_holidays_for_range(start_date.year, end_date.year + 1)
    
    while current_date <= end_date:
        # Skip non-trading days (weekends + holidays)
        if not is_trading_day_with_holidays(current_date, holidays):
            current_date += timedelta(days=1)
            continue
        
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Check if we've moved to a new quarter - recalculate daily profit
        new_quarter = get_quarter(current_date)
        new_year = current_date.year
        
        if new_year != current_year or new_quarter != current_quarter:
            quarter_daily_profit = round(truncate_lot_size(current_balance) * 15, 2)
            current_quarter = new_quarter
            current_year = new_year
        
        lot_size = truncate_lot_size(current_balance)
        daily_profit = quarter_daily_profit
        
        is_future = current_date > today
        
        # Past dates: check actual trades. Future dates: assume manager trades.
        if is_future:
            manager_traded = True
        else:
            override = overrides.get(date_str)
            master_trade = master_trade_logs.get(date_str)
            
            if override:
                manager_traded = override.get("traded", False)
            elif master_trade:
                manager_traded = master_trade.get("traded", True)
            else:
                manager_traded = False
        
        projections.append({
            "date": date_str,
            "start_value": round(current_balance, 2),
            "account_value": round(current_balance + daily_profit, 2) if manager_traded else round(current_balance, 2),
            "lot_size": lot_size,
            "daily_profit": daily_profit,
            "manager_traded": manager_traded,
            "is_projected": is_future,
            "has_override": date_str in overrides
        })
        
        # Update balance
        if manager_traded:
            current_balance = round(current_balance + daily_profit, 2)
        
        current_date += timedelta(days=1)
    
    return {
        "license": license_doc,
        "projections": projections,
        "current_amount": current_amount,
        "starting_amount": starting_amount,
        "master_trade_logs": master_trade_logs
    }


@router.put("/licenses/{license_id}")
async def update_license(license_id: str, starting_amount: Optional[float] = None, notes: Optional[str] = None, is_active: Optional[bool] = None, user: dict = Depends(deps.require_admin)):
    """Update a license (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update licenses")
    
    license_doc = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    update_fields = {}
    if starting_amount is not None:
        update_fields["starting_amount"] = starting_amount
    if notes is not None:
        update_fields["notes"] = notes
    if is_active is not None:
        update_fields["is_active"] = is_active
        # Update user record if deactivating
        if not is_active:
            await deps.db.users.update_one(
                {"id": license_doc["user_id"]},
                {"$unset": {"license_type": ""}}
            )
    
    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        await deps.db.licenses.update_one({"id": license_id}, {"$set": update_fields})
    
    return {"message": "License updated successfully"}


@router.post("/licenses/{license_id}/change-type")
async def change_license_type(license_id: str, data: ChangeLicenseTypeRequest, user: dict = Depends(deps.require_admin)):
    """Change license type - preserves all financial data (Master Admin only)
    
    When converting honorary -> honorary_fa (or vice versa), all historical data
    (start_date, starting_amount, effective_start_date, trade history, growth) is preserved.
    Only the license_type field changes.
    """
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can change license types")
    
    # Get existing license
    old_license = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not old_license:
        raise HTTPException(status_code=404, detail="License not found")
    
    if not old_license.get("is_active"):
        raise HTTPException(status_code=400, detail="Cannot change an inactive license")
    
    if data.new_license_type not in ["extended", "honorary", "honorary_fa"]:
        raise HTTPException(status_code=400, detail="Invalid license type")
    
    old_type = old_license.get("license_type")
    
    # For honorary <-> honorary_fa conversions, preserve ALL data in-place
    if _is_honorary(old_type) and _is_honorary(data.new_license_type):
        update_fields = {
            "license_type": data.new_license_type,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if data.notes:
            update_fields["notes"] = data.notes
        
        await deps.db.licenses.update_one({"id": license_id}, {"$set": update_fields})
        await deps.db.users.update_one(
            {"id": old_license["user_id"]},
            {"$set": {"license_type": data.new_license_type}}
        )
        return {"message": f"License converted from {old_type} to {data.new_license_type} (data preserved)", "new_license_id": license_id}
    
    # For other conversions (e.g., extended -> honorary), deactivate old and create new
    await deps.db.licenses.update_one(
        {"id": license_id},
        {"$set": {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc).isoformat(),
            "deactivation_reason": f"Changed to {data.new_license_type} by {user['full_name']}"
        }}
    )
    
    # Preserve financial data from old license where possible
    starting_amount = data.new_starting_amount if data.new_starting_amount is not None else old_license.get("starting_amount", 0)
    
    new_license_id = str(uuid.uuid4())
    new_license = {
        "id": new_license_id,
        "user_id": old_license["user_id"],
        "license_type": data.new_license_type,
        "starting_amount": starting_amount,
        "current_amount": starting_amount,
        "start_date": old_license.get("start_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "effective_start_date": old_license.get("effective_start_date"),
        "is_active": True,
        "notes": data.notes or f"Changed from {old_type} license",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "previous_license_id": license_id
    }
    await deps.db.licenses.insert_one(new_license)
    
    await deps.db.users.update_one(
        {"id": old_license["user_id"]},
        {"$set": {"license_type": data.new_license_type}}
    )
    
    return {"message": f"License changed to {data.new_license_type}", "new_license_id": new_license_id}


@router.post("/licenses/{license_id}/reset-balance")
async def reset_license_balance(license_id: str, data: ResetStartingAmountRequest, user: dict = Depends(deps.require_admin)):
    """Reset license starting amount/current balance (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can reset license balances")
    
    if data.new_amount < 0:
        raise HTTPException(status_code=400, detail="Amount cannot be negative")
    
    license = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    if not license.get("is_active"):
        raise HTTPException(status_code=400, detail="Cannot reset an inactive license")
    
    old_amount = license.get("current_amount", license.get("starting_amount", 0))
    
    # For honorary licensees, dynamically calculate the old amount
    if _is_honorary(license.get("license_type")):
        from utils.calculations import calculate_honorary_licensee_value
        old_amount = await calculate_honorary_licensee_value(deps.db, license)
    
    difference = data.new_amount - old_amount
    
    # Update license
    await deps.db.licenses.update_one(
        {"id": license_id},
        {"$set": {
            "starting_amount": data.new_amount,
            "current_amount": data.new_amount,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "reset_by": user["id"],
            "reset_notes": data.notes
        }}
    )
    
    # Update user's account_value
    await deps.db.users.update_one(
        {"id": license["user_id"]},
        {"$set": {"account_value": data.new_amount}}
    )
    
    # Record adjustment as transaction
    if data.record_as_deposit and difference != 0:
        adjustment_type = "deposit" if difference > 0 else "withdrawal"
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": license["user_id"],
            "type": adjustment_type,
            "amount": abs(difference),
            "status": "completed",
            "notes": data.notes or f"Balance reset by admin (was ${old_amount:,.2f}, now ${data.new_amount:,.2f})",
            "is_balance_reset": True,
            "balance_before": old_amount,
            "balance_after": data.new_amount,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "completed_by": user["id"]
        }
        await deps.db.licensee_transactions.insert_one(transaction)
    
    return {
        "message": f"License balance reset from ${old_amount:,.2f} to ${data.new_amount:,.2f}",
        "old_amount": old_amount,
        "new_amount": data.new_amount
    }


@router.delete("/licenses/{license_id}")
async def delete_license(license_id: str, user: dict = Depends(deps.require_admin)):
    """Delete a license (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete licenses")
    
    license_doc = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Remove license type from user
    await deps.db.users.update_one(
        {"id": license_doc["user_id"]},
        {"$unset": {"license_type": ""}}
    )
    
    await deps.db.licenses.delete_one({"id": license_id})
    
    return {"message": "License deleted successfully"}


@router.put("/licenses/{license_id}/effective-start-date")
async def update_license_effective_start_date(
    license_id: str,
    effective_start_date: str = Body(..., embed=True),
    user: dict = Depends(deps.require_admin)
):
    """Update the effective start date for a license (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update license effective start date")
    
    license_doc = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Validate date format
    try:
        datetime.strptime(effective_start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    old_date = license_doc.get("effective_start_date", license_doc.get("start_date"))
    
    await deps.db.licenses.update_one(
        {"id": license_id},
        {"$set": {
            "effective_start_date": effective_start_date,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": f"Effective start date updated from {old_date} to {effective_start_date}",
        "old_date": old_date,
        "new_date": effective_start_date
    }


@router.get("/licenses/{license_id}/trade-overrides")
async def get_license_trade_overrides(license_id: str, user: dict = Depends(deps.require_admin)):
    """Get all trade overrides for a specific license"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view trade overrides")
    
    overrides = await deps.db.licensee_trade_overrides.find(
        {"license_id": license_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Convert to a dict keyed by date for easy lookup
    overrides_by_date = {o["date"]: o for o in overrides}
    
    return {"overrides": overrides_by_date}


@router.post("/licenses/{license_id}/trade-overrides")
async def set_license_trade_override(
    license_id: str,
    data: LicenseeTradeOverride,
    user: dict = Depends(deps.require_admin)
):
    """Set or update a trade override for a specific license on a specific date"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can set trade overrides")
    
    # Validate license exists
    license_doc = await deps.db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Validate date format
    try:
        datetime.strptime(data.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Check if override already exists
    existing = await deps.db.licensee_trade_overrides.find_one(
        {"license_id": license_id, "date": data.date},
        {"_id": 0}
    )
    
    if existing:
        # Update existing override
        await deps.db.licensee_trade_overrides.update_one(
            {"license_id": license_id, "date": data.date},
            {"$set": {
                "traded": data.traded,
                "notes": data.notes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": user["id"]
            }}
        )
        action = "updated"
    else:
        # Create new override
        override_doc = {
            "id": str(uuid.uuid4()),
            "license_id": license_id,
            "date": data.date,
            "traded": data.traded,
            "notes": data.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        await deps.db.licensee_trade_overrides.insert_one(override_doc)
        action = "created"
    
    return {
        "message": f"Trade override {action} successfully",
        "license_id": license_id,
        "date": data.date,
        "traded": data.traded
    }


@router.delete("/licenses/{license_id}/trade-overrides/{date}")
async def delete_license_trade_override(
    license_id: str,
    date: str,
    user: dict = Depends(deps.require_admin)
):
    """Delete a trade override (revert to automatic detection)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete trade overrides")
    
    result = await deps.db.licensee_trade_overrides.delete_one(
        {"license_id": license_id, "date": date}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Override not found")
    
    return {"message": "Trade override deleted, reverting to automatic detection"}


@router.get("/license-invites")
async def get_all_license_invites(user: dict = Depends(deps.require_admin)):
    """Get all license invites (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can manage license invites")
    
    invites = await deps.db.license_invites.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with usage info
    for invite in invites:
        # Check if expired
        if invite.get("valid_until"):
            valid_until = datetime.fromisoformat(invite["valid_until"].replace("Z", "+00:00"))
            invite["is_expired"] = datetime.now(timezone.utc) > valid_until
        else:
            invite["is_expired"] = False
        
        # Check if fully used
        invite["is_fully_used"] = invite.get("uses_count", 0) >= invite.get("max_uses", 1)
        
        # Get users who registered with this invite
        registered_users = await deps.db.users.find(
            {"license_invite_code": invite["code"]}, 
            {"_id": 0, "id": 1, "full_name": 1, "email": 1, "created_at": 1}
        ).to_list(100)
        invite["registered_users"] = registered_users
    
    return {"invites": invites}


@router.post("/license-invites")
async def create_license_invite(data: LicenseInviteCreate, user: dict = Depends(deps.require_admin)):
    """Create a new license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can create license invites")
    
    if data.license_type not in ["extended", "honorary", "honorary_fa"]:
        raise HTTPException(status_code=400, detail="Invalid license type. Must be 'extended', 'honorary', or 'honorary_fa'")
    
    invite_code = generate_invite_code()
    valid_until = calculate_validity_date(data.valid_duration)
    
    invite = {
        "id": str(uuid.uuid4()),
        "code": invite_code,
        "license_type": data.license_type,
        "starting_amount": data.starting_amount,
        "valid_duration": data.valid_duration,
        "valid_until": valid_until,
        "max_uses": data.max_uses,
        "uses_count": 0,
        "notes": data.notes,
        "invitee_email": data.invitee_email,
        "invitee_name": data.invitee_name,
        "effective_start_date": data.effective_start_date,  # When licensee's trading starts
        "is_revoked": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "created_by_name": user.get("full_name", "Admin")
    }
    
    await deps.db.license_invites.insert_one(invite)
    
    # Generate registration URL
    frontend_url = os.environ.get("FRONTEND_URL", "https://streaks-referral.preview.emergentagent.com")
    registration_url = f"{frontend_url}/register/license/{invite_code}"
    
    return {
        "message": "License invite created successfully",
        "invite_id": invite["id"],
        "code": invite_code,
        "registration_url": registration_url,
        "starting_amount": invite["starting_amount"],
        "license_type": invite["license_type"]
    }


@router.get("/license-invites/{invite_id}")
async def get_license_invite(invite_id: str, user: dict = Depends(deps.require_admin)):
    """Get a specific license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view license invites")
    
    invite = await deps.db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    # Get registered users
    registered_users = await deps.db.users.find(
        {"license_invite_code": invite["code"]}, 
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "created_at": 1}
    ).to_list(100)
    invite["registered_users"] = registered_users
    
    return invite


@router.put("/license-invites/{invite_id}")
async def update_license_invite(invite_id: str, data: LicenseInviteUpdate, user: dict = Depends(deps.require_admin)):
    """Update a license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update license invites")
    
    invite = await deps.db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.valid_duration is not None:
        update_fields["valid_duration"] = data.valid_duration
        update_fields["valid_until"] = calculate_validity_date(data.valid_duration)
    
    if data.max_uses is not None:
        update_fields["max_uses"] = data.max_uses
    
    if data.notes is not None:
        update_fields["notes"] = data.notes
    
    if data.invitee_email is not None:
        update_fields["invitee_email"] = data.invitee_email
    
    if data.invitee_name is not None:
        update_fields["invitee_name"] = data.invitee_name
    
    await deps.db.license_invites.update_one({"id": invite_id}, {"$set": update_fields})
    
    return {"message": "License invite updated successfully"}


@router.post("/license-invites/{invite_id}/revoke")
async def revoke_license_invite(invite_id: str, user: dict = Depends(deps.require_admin)):
    """Revoke a license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can revoke license invites")
    
    invite = await deps.db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    await deps.db.license_invites.update_one(
        {"id": invite_id}, 
        {"$set": {"is_revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "License invite revoked successfully"}


@router.post("/license-invites/{invite_id}/renew")
async def renew_license_invite(invite_id: str, new_duration: str = "3_months", user: dict = Depends(deps.require_admin)):
    """Renew/revive an expired or revoked license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can renew license invites")
    
    invite = await deps.db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    new_valid_until = calculate_validity_date(new_duration)
    
    await deps.db.license_invites.update_one(
        {"id": invite_id}, 
        {"$set": {
            "is_revoked": False,
            "valid_duration": new_duration,
            "valid_until": new_valid_until,
            "renewed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "License invite renewed successfully", "valid_until": new_valid_until}


@router.post("/license-invites/{invite_id}/resend")
async def resend_license_invite(invite_id: str, user: dict = Depends(deps.require_admin)):
    """Resend license invite email (Master Admin only) - ILI"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can resend license invites")
    
    invite = await deps.db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    if not invite.get("invitee_email"):
        raise HTTPException(status_code=400, detail="No email address associated with this invite")
    
    # Get email template
    template = await deps.db.email_templates.find_one({"type": "license_invite"}, {"_id": 0})
    if not template:
        template = {
            "subject": "You've been invited to CrossCurrent Finance Center",
            "body": """Hello {{name}},

You have been invited to join CrossCurrent Finance Center as a {{license_type}} Licensee!

Click the link below to complete your registration:
{{registration_link}}

Your license details:
- Type: {{license_type}} Licensee
- Starting Amount: ${{starting_amount}}

This invite is valid until: {{valid_until}}

Best regards,
CrossCurrent Team"""
        }
    
    frontend_url = os.environ.get("FRONTEND_URL", "https://streaks-referral.preview.emergentagent.com")
    registration_url = f"{frontend_url}/register/license/{invite['code']}"
    
    # Replace template variables
    body = template["body"]
    body = body.replace("{{name}}", invite.get("invitee_name", "Trader"))
    body = body.replace("{{license_type}}", invite["license_type"].title())
    body = body.replace("{{registration_link}}", registration_url)
    body = body.replace("{{starting_amount}}", f"{invite['starting_amount']:,.2f}")
    body = body.replace("{{valid_until}}", invite.get("valid_until", "Indefinite")[:10] if invite.get("valid_until") else "Indefinite")
    
    subject = template["subject"]
    
    # Send email via Emailit
    settings = await deps.db.platform_settings.find_one({}, {"_id": 0})
    emailit_key = settings.get("emailit_api_key") if settings else None
    
    if not emailit_key:
        emailit_key = os.environ.get("EMAILIT_API_KEY")
    
    if emailit_key:
        try:
            email_response = requests.post(
                "https://api.emailit.com/v1/emails",
                headers={
                    "Authorization": f"Bearer {emailit_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "CrossCurrent Finance <noreply@crosscurrent.finance>",
                    "to": invite["invitee_email"],
                    "subject": subject,
                    "text": body
                },
                timeout=10
            )
            
            if email_response.status_code in [200, 201, 202]:
                await deps.db.license_invites.update_one(
                    {"id": invite_id},
                    {"$set": {"last_sent_at": datetime.now(timezone.utc).isoformat()}}
                )
                return {"message": "License invite email sent successfully"}
            else:
                return {"message": "Email service returned an error, but invite is still valid", "registration_url": registration_url}
        except Exception as e:
            return {"message": f"Could not send email: {str(e)}", "registration_url": registration_url}
    else:
        return {"message": "Email service not configured. Please share the link manually.", "registration_url": registration_url}


@router.delete("/license-invites/{invite_id}")
async def delete_license_invite(invite_id: str, user: dict = Depends(deps.require_admin)):
    """Delete a license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete license invites")
    
    invite = await deps.db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    await deps.db.license_invites.delete_one({"id": invite_id})
    
    return {"message": "License invite deleted successfully"}


@router.get("/licensee-transactions")
async def get_all_licensee_transactions(user: dict = Depends(deps.require_admin)):
    """Get all licensee deposit/withdrawal requests (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view licensee transactions")
    
    transactions = await deps.db.licensee_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with user info
    for tx in transactions:
        user_doc = await deps.db.users.find_one({"id": tx["user_id"]}, {"_id": 0, "full_name": 1, "email": 1})
        if user_doc:
            tx["user_name"] = user_doc.get("full_name", "Unknown")
            tx["user_email"] = user_doc.get("email", "")
    
    return {"transactions": transactions}


@router.post("/licensee-transactions/{tx_id}/feedback")
async def add_transaction_feedback(
    tx_id: str, 
    message: str = Form(...),
    status: Optional[str] = Form(None),
    final_amount: Optional[float] = Form(None),
    screenshot: Optional[UploadFile] = File(None),
    user: dict = Depends(deps.require_admin)
):
    """Add feedback to a licensee transaction (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can respond to transactions")
    
    tx = await deps.db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Handle screenshot upload
    screenshot_url = None
    if screenshot:
        try:
            contents = await screenshot.read()
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="licensee_transactions",
                resource_type="auto"
            )
            screenshot_url = upload_result.get("secure_url")
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {e}")
    
    feedback_entry = {
        "id": str(uuid.uuid4()),
        "message": message,
        "status_change": status,
        "final_amount": final_amount,
        "screenshot_url": screenshot_url,
        "from_admin": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "created_by_name": user.get("full_name", "Admin")
    }
    
    update_data = {
        "$push": {"feedback": feedback_entry},
        "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
    }
    
    if status:
        update_data["$set"]["status"] = status
    
    if final_amount is not None:
        update_data["$set"]["final_amount"] = final_amount
    
    await deps.db.licensee_transactions.update_one({"id": tx_id}, update_data)
    
    # Create notification for the licensee
    notification = {
        "id": str(uuid.uuid4()),
        "type": "transaction_feedback",
        "title": f"Update on your {tx['type']} request",
        "message": message,
        "user_id": tx["user_id"],
        "admin_id": user["id"],
        "transaction_id": tx_id,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await deps.db.notifications.insert_one(notification)
    
    return {"message": "Feedback added successfully"}


@router.post("/licensee-transactions/{tx_id}/approve")
async def approve_transaction(tx_id: str, user: dict = Depends(deps.require_admin)):
    """Approve/accept a pending transaction (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can approve transactions")
    
    tx = await deps.db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    await deps.db.licensee_transactions.update_one(
        {"id": tx_id},
        {"$set": {
            "status": "processing",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user["id"]
        }}
    )
    
    return {"message": "Transaction approved and set to processing"}


@router.post("/licensee-transactions/{tx_id}/complete")
async def complete_transaction(
    tx_id: str,
    screenshot: Optional[UploadFile] = File(None),
    user: dict = Depends(deps.require_admin)
):
    """Mark transaction as completed with optional screenshot (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can complete transactions")
    
    tx = await deps.db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Handle screenshot upload
    screenshot_url = None
    if screenshot:
        try:
            contents = await screenshot.read()
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="licensee_transactions",
                resource_type="auto"
            )
            screenshot_url = upload_result.get("secure_url")
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {e}")
    
    update_data = {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "completed_by": user["id"]
    }
    
    if screenshot_url:
        update_data["completion_screenshot_url"] = screenshot_url
    
    await deps.db.licensee_transactions.update_one({"id": tx_id}, {"$set": update_data})
    
    # Get licensee info and their active license
    licensee = await deps.db.users.find_one({"id": tx["user_id"]}, {"_id": 0})
    license = await deps.db.licenses.find_one({"user_id": tx["user_id"], "is_active": True}, {"_id": 0})
    
    # If deposit and approved, add to user balance AND Master Admin balance  
    if tx["type"] == "deposit" and licensee and license:
        deposit_amount = abs(tx.get("final_amount", tx["amount"]))
        
        # For honorary licensees, calculate current balance dynamically
        if _is_honorary(license.get("license_type")):
            from utils.calculations import calculate_honorary_licensee_value
            current_balance = await calculate_honorary_licensee_value(deps.db, license)
        else:
            current_balance = license.get("current_amount", license.get("starting_amount", 0))
        
        # For honorary licensees, update starting_amount (deposits increase the base)
        if _is_honorary(license.get("license_type")):
            new_starting = license.get("starting_amount", 0) + deposit_amount
            await deps.db.licenses.update_one(
                {"id": license["id"]},
                {"$set": {"starting_amount": new_starting, "current_amount": current_balance + deposit_amount, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        else:
            new_balance = current_balance + deposit_amount
            await deps.db.licenses.update_one(
                {"id": license["id"]},
                {"$set": {"current_amount": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        
        # Update user's account_value
        await deps.db.users.update_one(
            {"id": tx["user_id"]},
            {"$set": {"account_value": new_balance}}
        )
        
        # Record the deposit for tracking
        deposit_record = {
            "id": str(uuid.uuid4()),
            "user_id": tx["user_id"],
            "amount": deposit_amount,
            "type": "deposit",
            "notes": f"Licensee deposit - Transaction #{tx_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await deps.db.deposits.insert_one(deposit_record)
        
        # Also add to Master Admin's balance (since licensee funds are tied to master admin)
        master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0})
        if master_admin:
            master_deposit_record = {
                "id": str(uuid.uuid4()),
                "user_id": master_admin["id"],
                "amount": deposit_amount,
                "type": "deposit",
                "notes": f"Licensee ({licensee.get('full_name', 'Unknown')}) deposit - Transaction #{tx_id[:8]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "related_licensee_id": tx["user_id"],
                "related_transaction_id": tx_id
            }
            await deps.db.deposits.insert_one(master_deposit_record)
    
    # If withdrawal completed, deduct from Master Admin's balance
    # (Licensee balance was already deducted when withdrawal was submitted)
    elif tx["type"] == "withdrawal" and licensee:
        # Record the withdrawal for tracking
        withdrawal_record = {
            "id": str(uuid.uuid4()),
            "user_id": tx["user_id"],
            "amount": -abs(tx["amount"]),
            "type": "withdrawal",
            "notes": f"Licensee withdrawal - Transaction #{tx_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await deps.db.deposits.insert_one(withdrawal_record)
        
        # Also deduct from Master Admin's balance (since licensee funds are tied to master admin)
        master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0})
        if master_admin:
            master_withdrawal_record = {
                "id": str(uuid.uuid4()),
                "user_id": master_admin["id"],
                "amount": -abs(tx["amount"]),
                "type": "withdrawal",
                "notes": f"Licensee ({licensee.get('full_name', 'Unknown')}) withdrawal - Transaction #{tx_id[:8]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "related_licensee_id": tx["user_id"],
                "related_transaction_id": tx_id
            }
            await deps.db.deposits.insert_one(master_withdrawal_record)
    
    return {"message": "Transaction completed successfully"}


@router.put("/licensee-transactions/{tx_id}")
async def update_licensee_transaction(
    tx_id: str,
    amount: float = Body(..., embed=False),
    notes: Optional[str] = Body(None, embed=False),
    user: dict = Depends(deps.require_admin)
):
    """Update a licensee transaction amount (Master Admin only)"""
    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update transactions")
    
    tx = await deps.db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    old_amount = tx.get("amount", 0)
    
    # Update the transaction
    update_data = {
        "$set": {
            "amount": amount,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "correction_notes": notes or f"Amount corrected from ${old_amount} to ${amount}",
            "corrected_by": user["id"]
        }
    }
    
    await deps.db.licensee_transactions.update_one({"id": tx_id}, update_data)
    
    # If transaction was completed, we need to update the related deposit/withdrawal records
    if tx.get("status") == "completed":
        # Update corresponding deposit or withdrawal record
        if tx["type"] == "deposit":
            await deps.db.deposits.update_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}},
                {"$set": {"amount": amount}}
            )
        else:
            await deps.db.withdrawals.update_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}},
                {"$set": {"amount": amount}}
            )
    
    return {"message": "Transaction updated successfully", "old_amount": old_amount, "new_amount": amount}


@router.delete("/licensee-transactions/{tx_id}")
async def delete_licensee_transaction(tx_id: str, user: dict = Depends(deps.require_admin)):
    """Delete a licensee transaction (Master Admin only)"""
    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete transactions")
    
    tx = await deps.db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Delete the transaction
    await deps.db.licensee_transactions.delete_one({"id": tx_id})
    
    # If transaction was completed, we need to delete the related deposit/withdrawal records
    if tx.get("status") == "completed":
        if tx["type"] == "deposit":
            await deps.db.deposits.delete_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}}
            )
        else:
            await deps.db.withdrawals.delete_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}}
            )
    
    return {"message": "Transaction deleted successfully"}


@router.post("/pwa-icon/upload")
async def upload_pwa_icon_admin(file: UploadFile = File(...), user: dict = Depends(deps.require_admin)):
    """Upload PWA app icon via file upload"""
    try:
        content = await file.read()
        import io
        result = cloudinary.uploader.upload(
            io.BytesIO(content),
            folder="crosscurrent/branding",
            public_id="pwa_icon",
            overwrite=True,
            resource_type="image",
        )
        url = result.get("secure_url")
        await deps.db.platform_settings.update_one({}, {"$set": {"pwa_icon_url": url}}, upsert=True)
        return {"url": url}
    except Exception as e:
        logger.error(f"PWA icon upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.put("/pwa-icon/url")
async def set_pwa_icon_url_admin(request: Request, user: dict = Depends(deps.require_admin)):
    """Set PWA icon directly via URL"""
    body = await request.json()
    url = body.get("url", "")
    await deps.db.platform_settings.update_one({}, {"$set": {"pwa_icon_url": url}}, upsert=True)
    return {"url": url, "message": "PWA icon URL updated"}


@router.get("/pwa-manifest")
async def get_pwa_manifest_admin():
    """Serve dynamic PWA manifest"""
    from fastapi.responses import JSONResponse
    settings = await deps.db.platform_settings.find_one({}, {"_id": 0})
    pwa_icon_url = settings.get("pwa_icon_url", "") if settings else ""
    platform_name = settings.get("platform_name", "CrossCurrent") if settings else "CrossCurrent"
    icons = []
    if pwa_icon_url:
        icons = [
            {"src": pwa_icon_url, "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": pwa_icon_url, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ]
    else:
        icons = [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ]
    manifest = {
        "short_name": platform_name, "name": f"The {platform_name} Hub",
        "description": "Your complete trading profit management platform",
        "icons": icons, "start_url": "/", "display": "standalone",
        "theme_color": "#09090b", "background_color": "#09090b",
        "orientation": "any", "scope": "/",
        "categories": ["finance", "productivity"], "prefer_related_applications": False,
    }
    return JSONResponse(content=manifest, headers={"Content-Type": "application/manifest+json"})


@router.post("/licensee-health-check")
async def licensee_health_check(user: dict = Depends(deps.require_admin)):
    """One-click diagnostic: validates ALL active honorary licensees and their projections.
    Returns per-user status and auto-fixes missing fields where possible."""
    from utils.calculations import calculate_honorary_licensee_value
    from utils.trading_days import project_quarterly_growth, get_holidays_for_range

    results = []
    fixed = 0
    today = datetime.now(timezone.utc)
    holidays = get_holidays_for_range(today.year, today.year + 6)

    async for lic in deps.db.licenses.find({"is_active": True, "license_type": {"$regex": "^honorary", "$options": "i"}}, {"_id": 0}):
        uid = lic.get("user_id")
        user_doc = await deps.db.users.find_one({"id": uid}, {"_id": 0, "email": 1, "first_name": 1, "last_name": 1}) if uid else None
        email = user_doc.get("email", "?") if user_doc else "no_user"
        entry = {"user_id": uid, "email": email, "license_type": lic.get("license_type"), "status": "ok", "issues": [], "fixes": []}

        # Check start date
        eff = lic.get("effective_start_date") or lic.get("start_date")
        if not eff:
            entry["issues"].append("missing_start_date")
            if lic.get("created_at"):
                await deps.db.licenses.update_one({"user_id": uid, "is_active": True}, {"$set": {"start_date": str(lic["created_at"])[:10]}})
                entry["fixes"].append("set_start_date_from_created_at")
                fixed += 1
            entry["status"] = "fixed" if entry["fixes"] else "broken"
        if not uid:
            entry["issues"].append("missing_user_id")
            entry["status"] = "broken"

        # Try projection
        try:
            cv = await calculate_honorary_licensee_value(deps.db, lic)
            entry["current_value"] = round(cv, 2)
            proj = project_quarterly_growth(cv, today, 250, holidays)
            entry["1yr_projection"] = round(proj["projected_value"], 2)
        except Exception as e:
            entry["issues"].append(f"projection_error: {str(e)}")
            entry["status"] = "broken"

        results.append(entry)

    ok = sum(1 for r in results if r["status"] == "ok")
    broken = sum(1 for r in results if r["status"] == "broken")
    return {
        "total": len(results),
        "ok": ok,
        "broken": broken,
        "fixed": fixed,
        "results": results
    }


@router.post("/licensee/{user_id}/force-sync")
async def force_sync_licensee(user_id: str, user: dict = Depends(deps.require_admin)):
    """Force recalculate and sync a licensee's account value.
    
    This is a safeguard tool for admins to manually trigger recalculation
    when the dashboard shows incorrect values.
    """
    from utils.calculations import calculate_honorary_licensee_value, _is_honorary
    
    # Find the user
    target_user = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
    
    # Find their license
    license = await deps.db.licenses.find_one(
        {"user_id": user_id, "is_active": True},
        {"_id": 0}
    )
    if not license:
        raise HTTPException(status_code=404, detail=f"No active license found for user: {user_id}")
    
    result = {
        "user_id": user_id,
        "email": target_user.get("email"),
        "license_type": license.get("license_type"),
        "starting_amount": float(license.get("starting_amount", 0) or 0),
        "synced_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Calculate the current value
    if _is_honorary(license.get("license_type")):
        try:
            calculated_value = await calculate_honorary_licensee_value(deps.db, license)
            result["calculated_value"] = round(calculated_value, 2)
            result["calculated_profit"] = round(calculated_value - result["starting_amount"], 2)
            
            # Update the current_amount in the license document to match calculated value
            await deps.db.licenses.update_one(
                {"user_id": user_id, "is_active": True},
                {"$set": {"current_amount": round(calculated_value, 2), "last_synced": datetime.now(timezone.utc)}}
            )
            result["status"] = "synced"
            result["message"] = f"Successfully synced. Account value: ${calculated_value:,.2f}"
            
            logger.info(f"Force sync for {user_id}: calculated_value={calculated_value}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Force sync failed for {user_id}: {e}")
    else:
        result["status"] = "skipped"
        result["message"] = "Not an honorary license - no calculation needed"
        result["calculated_value"] = float(license.get("current_amount", license.get("starting_amount", 0)) or 0)
    
    return result


@router.post("/licensee/batch-sync-all")
async def batch_sync_all_licensees(user: dict = Depends(deps.require_admin)):
    """Batch sync/recalculate ALL active honorary licensees.
    
    This is a maintenance tool to ensure all licensee account values are up-to-date.
    Should be run periodically (recommended: weekly).
    """
    from utils.calculations import calculate_honorary_licensee_value, _is_honorary
    
    # Find all active honorary licenses
    licenses = await deps.db.licenses.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(1000)
    
    results = {
        "total": len(licenses),
        "synced": 0,
        "skipped": 0,
        "errors": 0,
        "details": [],
        "synced_at": datetime.now(timezone.utc).isoformat()
    }
    
    for license in licenses:
        license_type = license.get("license_type", "")
        user_id = license.get("user_id")
        
        if not _is_honorary(license_type):
            results["skipped"] += 1
            continue
        
        try:
            # Calculate the current value
            calculated_value = await calculate_honorary_licensee_value(deps.db, license)
            starting_amount = float(license.get("starting_amount", 0) or 0)
            
            # Update the license
            await deps.db.licenses.update_one(
                {"user_id": user_id, "is_active": True},
                {"$set": {
                    "current_amount": round(calculated_value, 2),
                    "last_synced": datetime.now(timezone.utc)
                }}
            )
            
            results["synced"] += 1
            results["details"].append({
                "user_id": user_id,
                "license_type": license_type,
                "starting_amount": starting_amount,
                "calculated_value": round(calculated_value, 2),
                "profit": round(calculated_value - starting_amount, 2),
                "status": "synced"
            })
            
            logger.info(f"Batch sync: {user_id} -> ${calculated_value}")
            
        except Exception as e:
            results["errors"] += 1
            results["details"].append({
                "user_id": user_id,
                "license_type": license_type,
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Batch sync error for {user_id}: {e}")
    
    logger.info(f"Batch sync complete: {results['synced']} synced, {results['skipped']} skipped, {results['errors']} errors")
    
    return results


@router.post("/members/{user_id}/send-email")
async def send_email_to_member(user_id: str, data: SendEmailRequest, user: dict = Depends(deps.require_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Use the email service with verified sender
    from services.email_service import send_email as send_email_service
    
    result = await send_email_service(
        db=deps.db,
        to_email=member["email"],
        subject=data.subject,
        html_content=data.body,
        template_type="admin_reminder",
        metadata={"sent_by": user["id"], "sent_to": user_id}
    )
    
    if result.get("success"):
        return {"message": "Email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Email sending failed"))


@router.get("/email-templates")
async def get_email_templates(user: dict = Depends(deps.require_admin)):
    """Get all email templates"""
    templates = await deps.db.email_templates.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"templates": templates}


@router.get("/email-templates/{template_id}")
async def get_email_template(template_id: str, user: dict = Depends(deps.require_admin)):
    """Get a specific email template"""
    template = await deps.db.email_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/email-templates")
async def create_email_template(data: EmailTemplateCreate, user: dict = Depends(deps.require_master_admin)):
    """Create a new email template (Master Admin only)"""
    template = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "subject": data.subject,
        "body": data.body,
        "category": data.category,
        "is_html": data.is_html,
        "created_by": user["id"],
        "created_by_name": user.get("full_name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await deps.db.email_templates.insert_one(template)
    template.pop("_id", None)
    return template


@router.put("/email-templates/{template_id}")
async def update_email_template(template_id: str, data: EmailTemplateUpdate, user: dict = Depends(deps.require_master_admin)):
    """Update an email template (Master Admin only)"""
    template = await deps.db.email_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.name is not None:
        update_data["name"] = data.name
    if data.subject is not None:
        update_data["subject"] = data.subject
    if data.body is not None:
        update_data["body"] = data.body
    if data.category is not None:
        update_data["category"] = data.category
    if data.is_html is not None:
        update_data["is_html"] = data.is_html
    
    await deps.db.email_templates.update_one({"id": template_id}, {"$set": update_data})
    
    updated = await deps.db.email_templates.find_one({"id": template_id}, {"_id": 0})
    return updated


@router.delete("/email-templates/{template_id}")
async def delete_email_template(template_id: str, user: dict = Depends(deps.require_master_admin)):
    """Delete an email template (Master Admin only)"""
    result = await deps.db.email_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}


@router.post("/members/{user_id}/notify")
async def notify_member(user_id: str, data: NotifyRequest, user: dict = Depends(deps.require_admin)):
    """Send an in-app notification to a member"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create in-app notification
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "admin_reminder",
        "title": data.title,
        "message": data.message,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_by": user["id"]
    }
    
    await deps.db.notifications.insert_one(notification)
    
    # Also send email as backup
    from services.email_service import send_email as send_email_service
    
    await send_email_service(
        db=deps.db,
        to_email=member["email"],
        subject=data.title,
        html_content=f"<p>{data.message}</p>",
        template_type="admin_reminder",
        metadata={"sent_by": user["id"], "sent_to": user_id}
    )
    
    return {"message": "Notification sent successfully"}


@router.post("/upgrade-role")
async def upgrade_role(data: RoleUpgrade, user: dict = Depends(deps.require_admin)):
    """Upgrade a user's role. Master Admin can promote to any role without secret code."""
    target_user = await deps.db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate role
    valid_roles = ["basic_admin", "admin", "super_admin"]
    if data.new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    
    # Master Admin can promote to any role without secret code
    if user["role"] == "master_admin":
        pass  # No restrictions for master admin
    elif data.new_role == "super_admin":
        # Non-master admins need secret code for super_admin promotion
        if data.secret_code != deps.SUPER_ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret code")
        if user["role"] not in ["super_admin", "master_admin"]:
            raise HTTPException(status_code=403, detail="Only super admin or master admin can create super admins")
    elif data.new_role == "basic_admin" or data.new_role == "admin":
        # Super admins can create basic admins
        if user["role"] not in ["super_admin", "master_admin"]:
            raise HTTPException(status_code=403, detail="Only super admin or master admin can create admins")
    
    await deps.db.users.update_one(
        {"id": data.user_id},
        {"$set": {"role": data.new_role, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": f"User upgraded to {data.new_role}"}


@router.post("/downgrade-role/{user_id}")
async def downgrade_role(user_id: str, user: dict = Depends(deps.require_super_admin)):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot downgrade yourself")
    
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {"role": "member", "updated_at": datetime.now(timezone.utc).isoformat()}}  # Changed from "user" to "member"
    )
    return {"message": "User downgraded to member"}


@router.post("/deactivate/{user_id}")
async def deactivate_user(user_id: str, user: dict = Depends(deps.require_admin)):
    """Deactivate a user - they cannot login until reactivated"""
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    target_user = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check role hierarchy - can't deactivate higher or equal roles
    role_hierarchy = {'super_admin': 4, 'master_admin': 3, 'admin': 2, 'member': 1}
    if role_hierarchy.get(target_user.get("role"), 0) >= role_hierarchy.get(user.get("role"), 0):
        raise HTTPException(status_code=403, detail="Cannot deactivate users with equal or higher role")
    
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {"is_deactivated": True, "deactivated_at": datetime.now(timezone.utc).isoformat(), "deactivated_by": user["id"]}}
    )
    return {"message": "User has been deactivated"}


@router.post("/reactivate/{user_id}")
async def reactivate_user(user_id: str, user: dict = Depends(deps.require_admin)):
    """Reactivate a deactivated user"""
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {"is_deactivated": False}, "$unset": {"deactivated_at": "", "deactivated_by": ""}}
    )
    return {"message": "User has been reactivated"}


@router.post("/migrate-trade-directions")
@router.get("/migrate-trade-directions")  # Also allow GET for easier testing
async def migrate_trade_directions(user: dict = Depends(deps.require_master_admin)):
    """
    One-time migration to fix historical trade log directions.
    Updates trade_logs.direction field to match the linked signal's direction.
    Only Master Admin can run this migration.
    """
    try:
        # Get all trade logs with a signal_id
        trades_with_signals = await deps.db.trade_logs.find(
            {"signal_id": {"$ne": None}},
            {"_id": 0, "id": 1, "signal_id": 1, "direction": 1}
        ).to_list(10000)
        
        if not trades_with_signals:
            return {"message": "No trades found to migrate", "updated": 0, "skipped": 0}
        
        # Get all unique signal IDs
        signal_ids = list(set(t.get("signal_id") for t in trades_with_signals if t.get("signal_id")))
        
        # Fetch all signals in one query
        signals = await deps.db.trading_signals.find(
            {"id": {"$in": signal_ids}},
            {"_id": 0, "id": 1, "direction": 1}
        ).to_list(len(signal_ids))
        
        signals_map = {s["id"]: s.get("direction") for s in signals}
        
        updated_count = 0
        skipped_count = 0
        
        for trade in trades_with_signals:
            signal_id = trade.get("signal_id")
            current_direction = trade.get("direction")
            signal_direction = signals_map.get(signal_id)
            
            # Skip if signal not found or direction already matches
            if not signal_direction:
                skipped_count += 1
                continue
                
            if current_direction == signal_direction:
                skipped_count += 1
                continue
            
            # Update the trade's direction to match the signal
            result = await deps.db.trade_logs.update_one(
                {"id": trade["id"]},
                {"$set": {"direction": signal_direction}}
            )
            
            if result.modified_count > 0:
                updated_count += 1
                logger.info(f"Migrated trade {trade['id']}: {current_direction} -> {signal_direction}")
            else:
                skipped_count += 1
        
        return {
            "message": f"Migration complete. Updated {updated_count} trades, skipped {skipped_count} trades.",
            "updated": updated_count,
            "skipped": skipped_count
        }
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")


@router.get("/top-performers")
async def get_top_performers(
    limit: int = 10,
    exclude_non_traders: bool = True,
    user: dict = Depends(deps.require_admin)
):
    """Get top performing members based on total profit"""
    try:
        # Get date range for "active" traders (traded in last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Get users who have traded recently (if excluding non-traders)
        recent_traders = set()
        if exclude_non_traders:
            recent_traders = set(await deps.db.trade_logs.distinct(
                "user_id",
                {"created_at": {"$gte": thirty_days_ago}}
            ))
        
        # Get all active members with their stats
        pipeline = [
            {"$match": {"role": "member", "is_active": True}},
            {"$lookup": {
                "from": "trade_logs",
                "localField": "id",
                "foreignField": "user_id",
                "as": "trades"
            }},
            {"$addFields": {
                "total_profit": {"$sum": "$trades.actual_profit"},
                "total_trades": {"$size": "$trades"},
                "avg_profit_per_trade": {
                    "$cond": [
                        {"$gt": [{"$size": "$trades"}, 0]},
                        {"$divide": [{"$sum": "$trades.actual_profit"}, {"$size": "$trades"}]},
                        0
                    ]
                }
            }},
            {"$sort": {"total_profit": -1}},
            {"$project": {
                "_id": 0,
                "id": 1,
                "full_name": 1,
                "email": 1,
                "total_profit": 1,
                "total_trades": 1,
                "avg_profit_per_trade": 1
            }}
        ]
        
        performers = await deps.db.users.aggregate(pipeline).to_list(100)
        
        # Filter to only include recent traders if requested
        if exclude_non_traders and recent_traders:
            performers = [p for p in performers if p["id"] in recent_traders]
        
        # Limit results
        performers = performers[:limit]
        
        # Add rank
        for i, p in enumerate(performers, 1):
            p["rank"] = i
        
        return {"performers": performers, "total": len(performers)}
        
    except Exception as e:
        logger.error(f"Failed to get top performers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/report/image")
async def generate_performance_report_image(
    period: str = "monthly",  # daily, weekly, monthly
    user_id: Optional[str] = None,  # Admin can generate for specific user
    user: dict = Depends(deps.require_admin)  # Changed to require admin
):
    """Generate an image-based performance report (Admin only)"""
    from services.report_generator import generate_performance_report
    
    try:
        # Use provided user_id or default to current admin's id
        target_user_id = user_id if user_id else user["id"]
        
        # Get target user details if generating for another user
        if user_id:
            target_user = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            user_name = target_user.get("full_name", target_user.get("email", "Trader"))
        else:
            user_name = user.get("full_name", user.get("email", "Trader"))
        
        # Calculate date range based on period
        now = datetime.now(timezone.utc)
        if period == "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start_date = now - timedelta(days=7)
        else:  # monthly
            start_date = now - timedelta(days=30)
        
        # Get user's trades for the period
        trades_cursor = deps.db.trade_logs.find(
            {
                "user_id": target_user_id,
                "created_at": {"$gte": start_date}
            },
            {"_id": 0}
        ).sort("created_at", -1)
        trades = await trades_cursor.to_list(100)
        
        # Calculate statistics
        total_profit = sum(t.get("actual_profit", 0) for t in trades)
        total_trades = len(trades)
        
        winning_trades = [t for t in trades if t.get("actual_profit", 0) > 0]
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        profits = [t.get("actual_profit", 0) for t in trades]
        best_trade = max(profits) if profits else 0
        worst_trade = min(profits) if profits else 0
        
        # Get account value from latest deposit summary
        summary = await deps.db.deposits.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        deposits_total = summary[0]["total"] if summary else 0
        
        withdrawals = await deps.db.withdrawals.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        withdrawals_total = withdrawals[0]["total"] if withdrawals else 0
        
        all_time_profit = await deps.db.trade_logs.aggregate([
            {"$match": {"user_id": target_user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$actual_profit"}}}
        ]).to_list(1)
        
        all_profit = all_time_profit[0]["total"] if all_time_profit else 0
        account_value = deposits_total - withdrawals_total + all_profit
        
        # Calculate streak
        streak = 0
        for trade in trades:
            profit = trade.get("actual_profit", 0)
            if profit > 0:
                if streak >= 0:
                    streak += 1
                else:
                    break
            elif profit < 0:
                if streak <= 0:
                    streak -= 1
                else:
                    break
        
        stats = {
            "account_value": account_value,
            "total_profit": total_profit,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_profit_per_trade": avg_profit,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "streak": streak
        }
        
        # Format trades for report
        formatted_trades = []
        for t in trades[:5]:
            formatted_trades.append({
                "date": t.get("created_at", "").strftime("%Y-%m-%d") if hasattr(t.get("created_at", ""), "strftime") else str(t.get("created_at", ""))[:10],
                "direction": t.get("direction", "-"),
                "lot_size": t.get("lot_size", 0),
                "actual_profit": t.get("actual_profit", 0)
            })
        
        # Get platform name from settings
        settings = await deps.db.settings.find_one({}, {"_id": 0, "site_name": 1})
        platform_name = settings.get("site_name", "CrossCurrent") if settings else "CrossCurrent"
        
        # Generate the image
        image_bytes = await generate_performance_report(
            user_name=user_name,
            period=period,
            stats=stats,
            trades=formatted_trades,
            platform_name=platform_name
        )
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="performance_report_{period}_{now.strftime("%Y%m%d")}.png"'
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/report/base64")
async def generate_performance_report_base64(
    period: str = "monthly",
    user_id: Optional[str] = None,  # Admin can generate for specific user
    user: dict = Depends(deps.require_admin)  # Changed to require admin
):
    """Generate a performance report and return as base64 for embedding (Admin only)"""
    from services.report_generator import generate_report_base64
    
    try:
        # Use provided user_id or default to current admin's id
        target_user_id = user_id if user_id else user["id"]
        
        # Get target user details if generating for another user
        if user_id:
            target_user = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            user_name = target_user.get("full_name", target_user.get("email", "Trader"))
        else:
            user_name = user.get("full_name", user.get("email", "Trader"))
        
        # Use the same logic as above but return base64
        now = datetime.now(timezone.utc)
        if period == "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start_date = now - timedelta(days=7)
        else:
            start_date = now - timedelta(days=30)
        
        trades_cursor = deps.db.trade_logs.find(
            {"user_id": target_user_id, "created_at": {"$gte": start_date}},
            {"_id": 0}
        ).sort("created_at", -1)
        trades = await trades_cursor.to_list(100)
        
        total_profit = sum(t.get("actual_profit", 0) for t in trades)
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get("actual_profit", 0) > 0]
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        profits = [t.get("actual_profit", 0) for t in trades]
        best_trade = max(profits) if profits else 0
        worst_trade = min(profits) if profits else 0
        
        summary = await deps.db.deposits.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        deposits_total = summary[0]["total"] if summary else 0
        
        withdrawals = await deps.db.withdrawals.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        withdrawals_total = withdrawals[0]["total"] if withdrawals else 0
        
        all_time_profit = await deps.db.trade_logs.aggregate([
            {"$match": {"user_id": target_user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$actual_profit"}}}
        ]).to_list(1)
        all_profit = all_time_profit[0]["total"] if all_time_profit else 0
        account_value = deposits_total - withdrawals_total + all_profit
        
        streak = 0
        for trade in trades:
            profit = trade.get("actual_profit", 0)
            if profit > 0:
                if streak >= 0: streak += 1
                else: break
            elif profit < 0:
                if streak <= 0: streak -= 1
                else: break
        
        stats = {
            "account_value": account_value,
            "total_profit": total_profit,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_profit_per_trade": avg_profit,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "streak": streak
        }
        
        formatted_trades = [{
            "date": t.get("created_at", "").strftime("%Y-%m-%d") if hasattr(t.get("created_at", ""), "strftime") else str(t.get("created_at", ""))[:10],
            "direction": t.get("direction", "-"),
            "lot_size": t.get("lot_size", 0),
            "actual_profit": t.get("actual_profit", 0)
        } for t in trades[:5]]
        
        settings = await deps.db.settings.find_one({}, {"_id": 0, "site_name": 1})
        platform_name = settings.get("site_name", "CrossCurrent") if settings else "CrossCurrent"
        
        base64_image = await generate_report_base64(
            user_name=user_name,
            period=period,
            stats=stats,
            trades=formatted_trades,
            platform_name=platform_name
        )
        
        return {
            "image_base64": base64_image,
            "period": period,
            "generated_at": now.isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to generate base64 report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-trade-summary")
async def get_daily_trade_summary(date: Optional[str] = None, user: dict = Depends(deps.require_admin)):
    """Get a comprehensive daily trade summary for admin notifications - who traded, who missed, profits, commissions"""
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        target_date = datetime.now(timezone.utc).date()
    
    date_str = target_date.strftime("%Y-%m-%d")
    
    # Get all active members
    all_members = await deps.db.users.find(
        {"status": {"$ne": "deactivated"}, "role": {"$nin": ["master_admin"]}},
        {"_id": 0, "password": 0}
    ).to_list(500)
    
    # Get all trades for this date
    trades = await deps.db.trade_logs.find(
        {"date": {"$regex": f"^{date_str}"}},
        {"_id": 0}
    ).to_list(1000)
    
    # Build member lookup
    member_lookup = {m["id"]: m for m in all_members}
    
    # Categorize
    traded = []
    missed = []
    did_not_trade = []
    
    traded_user_ids = set()
    for t in trades:
        uid = t.get("user_id")
        traded_user_ids.add(uid)
        member = member_lookup.get(uid, {})
        entry = {
            "user_id": uid,
            "name": member.get("full_name", "Unknown"),
            "email": member.get("email", ""),
            "actual_profit": t.get("actual_profit", 0),
            "commission": t.get("commission", 0),
            "direction": t.get("direction", ""),
            "lot_size": t.get("lot_size", 0),
            "did_not_trade": t.get("did_not_trade", False),
            "is_retroactive": t.get("is_retroactive", False),
        }
        if t.get("did_not_trade"):
            did_not_trade.append(entry)
        else:
            traded.append(entry)
    
    # Members who have no trade entry at all
    for m in all_members:
        if m["id"] not in traded_user_ids and m.get("onboarding_completed"):
            missed.append({
                "user_id": m["id"],
                "name": m.get("full_name", "Unknown"),
                "email": m.get("email", ""),
            })
    
    # Sort traded by profit desc
    traded.sort(key=lambda x: x.get("actual_profit", 0), reverse=True)
    
    total_profit = sum(t.get("actual_profit", 0) for t in traded)
    total_commission = sum(t.get("commission", 0) for t in traded)
    
    # Get the signal for this date
    signal = await deps.db.trading_signals.find_one(
        {"created_at": {"$regex": f"^{date_str}"}},
        {"_id": 0}
    )
    
    return {
        "date": date_str,
        "signal": signal,
        "traded": traded,
        "missed": missed,
        "did_not_trade": did_not_trade,
        "stats": {
            "total_traded": len(traded),
            "total_missed": len(missed),
            "total_did_not_trade": len(did_not_trade),
            "total_profit": round(total_profit, 2),
            "total_commission": round(total_commission, 2),
            "total_members": len(all_members),
        }
    }


@router.post("/signals/force-notify")
async def force_send_signal_email(request: Request, user: dict = Depends(deps.require_admin)):
    """Force send the active signal email to all members, respecting their notification preferences"""
    signal = await deps.db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    if not signal:
        raise HTTPException(status_code=404, detail="No active signal found")
    
    frontend_url = request.headers.get("origin") or os.environ.get("FRONTEND_URL", "")
    
    try:
        email_result = await send_signal_email_to_members(signal, frontend_url)
        
        # Also send push notification
        push_result = await send_push_to_all_members(
            title=f"Trading Signal: {signal.get('direction', '')} {signal.get('product', '')}",
            body=f"Trade at {signal.get('trade_time', '')} | Multiplier: ×{signal.get('profit_multiplier', 15)}",
            url="/trade-monitor",
            tag="trading-signal"
        )
        
        return {
            "message": f"Signal email sent to {email_result.get('sent', 0)} members, push to {push_result.get('sent', 0)} devices",
            "sent": email_result.get("sent", 0),
            "failed": email_result.get("failed", 0),
            "total": email_result.get("total", 0),
            "push_sent": push_result.get("sent", 0),
        }
    except Exception as e:
        logger.error(f"Failed to force send signal emails: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send emails: {str(e)}")


@router.post("/members/{user_id}/unblock-signal")
async def admin_unblock_signal(user_id: str, days: int = 7, user: dict = Depends(deps.require_admin)):
    """Master/Super admin manually unblocks a member's signal view for N days."""
    target = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "full_name": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    unblock_until = datetime.now(timezone.utc) + timedelta(days=days)
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {"signal_unblocked_until": unblock_until.isoformat()}}
    )

    return {
        "message": f"Signal unblocked for {target.get('full_name', user_id)} until {unblock_until.isoformat()[:10]}",
        "unblocked_until": unblock_until.isoformat()
    }


@router.get("/habits")
async def admin_get_habits(user: dict = Depends(deps.require_admin)):
    habits = await deps.db.habits.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"habits": habits}


@router.post("/habits")
async def admin_create_habit(data: _HabitCreate, user: dict = Depends(deps.require_admin)):
    habit = {
        "id": str(uuid.uuid4()),
        "title": data.title,
        "description": data.description or "",
        "action_type": data.action_type,
        "action_data": data.action_data or "",
        "is_gate": data.is_gate,
        "validity_days": max(1, data.validity_days),
        "requires_screenshot": data.requires_screenshot,
        "day_of_week": data.day_of_week,  # None = daily, "monday" = Mon only
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
    }
    await deps.db.habits.insert_one(habit)
    habit.pop("_id", None)
    return habit


@router.put("/habits/{habit_id}")
async def admin_update_habit(habit_id: str, data: _HabitCreate, user: dict = Depends(deps.require_admin)):
    result = await deps.db.habits.update_one(
        {"id": habit_id},
        {"$set": {
            "title": data.title,
            "description": data.description or "",
            "action_type": data.action_type,
            "action_data": data.action_data or "",
            "is_gate": data.is_gate,
            "validity_days": max(1, data.validity_days),
            "requires_screenshot": data.requires_screenshot,
            "day_of_week": data.day_of_week,
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"message": "Habit updated"}


@router.delete("/habits/{habit_id}")
async def admin_delete_habit(habit_id: str, user: dict = Depends(deps.require_admin)):
    await deps.db.habits.update_one({"id": habit_id}, {"$set": {"active": False}})
    return {"message": "Habit deactivated"}


@router.post("/habits/{habit_id}/activate")
async def admin_activate_habit(habit_id: str, user: dict = Depends(deps.require_admin)):
    await deps.db.habits.update_one({"id": habit_id}, {"$set": {"active": True}})
    return {"message": "Habit activated"}


# ─── Smart Registration Security ───

@router.get("/pending-registrations")
async def get_pending_registrations(user: dict = Depends(deps.require_admin)):
    """Get flagged registrations awaiting admin approval."""
    db = deps.db
    flagged = await db.users.find(
        {"registration_flagged": True, "registration_approved": False},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "created_at": 1,
         "registration_flags": 1, "referred_by": 1}
    ).sort("created_at", -1).to_list(100)
    return {"pending": flagged, "count": len(flagged)}


@router.post("/approve-registration/{user_id}")
async def approve_registration(user_id: str, user: dict = Depends(deps.require_admin)):
    """Approve a flagged registration."""
    db = deps.db
    result = await db.users.update_one(
        {"id": user_id, "registration_flagged": True},
        {"$set": {"registration_approved": True, "approved_by": user["id"],
                  "approved_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Flagged registration not found")
    return {"message": "Registration approved"}


@router.post("/reject-registration/{user_id}")
async def reject_registration(user_id: str, user: dict = Depends(deps.require_admin)):
    """Reject and suspend a flagged registration."""
    db = deps.db
    result = await db.users.update_one(
        {"id": user_id, "registration_flagged": True},
        {"$set": {
            "is_suspended": True,
            "suspended_at": datetime.now(timezone.utc).isoformat(),
            "suspension_reason": "Registration rejected by admin — flagged as suspicious",
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Flagged registration not found")
    return {"message": "Registration rejected — user suspended"}


# ─── Admin Cleanup Page Data ───

@router.get("/cleanup-overview")
async def get_cleanup_overview(user: dict = Depends(deps.require_admin)):
    """Get counts and data for the Admin Cleanup Page — one-stop review hub."""
    db = deps.db

    # 1. Pending screenshot proofs
    pending_proofs = await db.habit_completions.count_documents({
        "screenshot_url": {"$exists": True, "$ne": ""},
        "verification_status": {"$nin": ["approved", "rejected"]},
    })

    # 2. Members with active fraud warnings
    fraud_warned = await db.fraud_warnings.find(
        {"resolution": "pending"},
        {"_id": 0, "user_id": 1, "fraud_count": 1, "acknowledged": 1, "countdown_end": 1, "created_at": 1}
    ).to_list(100)
    # Enrich with user info
    for fw in fraud_warned:
        u = await db.users.find_one({"id": fw["user_id"]}, {"_id": 0, "full_name": 1, "email": 1})
        fw["user_name"] = u.get("full_name", "Unknown") if u else "Unknown"
        fw["user_email"] = u.get("email", "") if u else ""

    # 3. In-danger members (no trade in 7+ days but have traded before)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    active_member_ids = []
    async for u in db.users.find(
        {"is_suspended": {"$ne": True}, "is_deactivated": {"$ne": True}, "role": "member", "license_type": {"$exists": False}},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1}
    ):
        active_member_ids.append(u)

    users_with_recent = set()
    async for doc in db.trade_logs.aggregate([
        {"$match": {"user_id": {"$in": [u["id"] for u in active_member_ids]}, "created_at": {"$gte": cutoff}}},
        {"$group": {"_id": "$user_id"}},
    ]):
        users_with_recent.add(doc["_id"])

    users_with_any = set()
    async for doc in db.trade_logs.aggregate([
        {"$match": {"user_id": {"$in": [u["id"] for u in active_member_ids]}}},
        {"$group": {"_id": "$user_id"}},
    ]):
        users_with_any.add(doc["_id"])

    in_danger_ids = users_with_any - users_with_recent
    in_danger = [
        {"id": u["id"], "name": u["full_name"], "email": u["email"]}
        for u in active_member_ids if u["id"] in in_danger_ids
    ]

    # 4. Auto-suspended members
    auto_suspended = await db.users.find(
        {"is_suspended": True, "suspension_type": "permanent"},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "suspended_at": 1, "suspension_reason": 1}
    ).to_list(50)

    # 5. Pending registration approvals
    pending_regs = await db.users.count_documents({
        "registration_flagged": True, "registration_approved": False
    })

    return {
        "pending_proofs": pending_proofs,
        "fraud_warnings": fraud_warned,
        "fraud_warning_count": len(fraud_warned),
        "in_danger": in_danger,
        "in_danger_count": len(in_danger),
        "auto_suspended": auto_suspended,
        "auto_suspended_count": len(auto_suspended),
        "pending_registrations": pending_regs,
    }

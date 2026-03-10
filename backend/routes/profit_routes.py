"""Profit tracker & financial routes - extracted from server.py"""
import uuid
import os
import math
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Body, Form, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

import deps
from models.common import DepositResponse, DepositCreate, WithdrawalRequest, WithdrawalSimulation, ConfirmReceiptRequest
from helpers import (
    create_admin_notification, create_member_notification, create_user_notification,
    truncate_lot_size, calculate_exit_value, calculate_withdrawal_fees,
    add_business_days, send_push_to_admins,
    calculate_extended_license_projections, get_quarterly_summary
)
from services import websocket_manager

try:
    from services import notify_admins_deposit_request, notify_admins_withdrawal_request
except ImportError:
    async def notify_admins_deposit_request(*a, **kw): pass
    async def notify_admins_withdrawal_request(*a, **kw): pass

from utils.calculations import (
    _is_honorary, calculate_honorary_licensee_value,
    get_user_financial_summary, calculate_account_value
)

try:
    from utils.trading_days import get_trading_days_count, get_holidays_for_range, is_us_market_holiday
except ImportError:
    pass

logger = logging.getLogger("server")

router = APIRouter(prefix="/profit", tags=["Profit Tracker"])


# ─── Request Models ───

class CommissionCreate(BaseModel):
    amount: float
    source: str = "referral"
    traders_count: int = 1
    notes: Optional[str] = None
    commission_date: Optional[str] = None
    skip_deposit: bool = False  # True = record-only, don't add to account balance

class OnboardingTransaction(BaseModel):
    type: str
    amount: float
    date: str
    notes: Optional[str] = None

class OnboardingTradeEntry(BaseModel):
    date: str
    actual_profit: float
    direction: str = "BUY"
    notes: Optional[str] = None

class OnboardingData(BaseModel):
    starting_balance: float
    trading_start_date: str
    transactions: Optional[List[OnboardingTransaction]] = []
    trades: Optional[List[OnboardingTradeEntry]] = []

class BalanceOverrideData(BaseModel):
    override_balance: float
    override_date: str
    reason: Optional[str] = None

@router.post("/deposits", response_model=DepositResponse)
async def create_deposit(data: DepositCreate, user: dict = Depends(deps.get_current_user)):
    deposit_id = str(uuid.uuid4())
    deposit = {
        "id": deposit_id,
        "user_id": user["id"],
        "amount": data.amount,
        "product": data.product,
        "currency": data.currency,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await deps.db.deposits.insert_one(deposit)
    
    # Create notification for admins
    await create_admin_notification(
        notification_type="deposit",
        title="New Deposit",
        message=f"{user['full_name']} deposited ${data.amount:.2f}",
        user_id=user["id"],
        user_name=user["full_name"],
        amount=data.amount,
        metadata={"product": data.product, "currency": data.currency}
    )
    
    return DepositResponse(**{**deposit, "created_at": datetime.fromisoformat(deposit["created_at"])})


@router.get("/deposits", response_model=List[DepositResponse])
async def get_deposits(user: dict = Depends(deps.get_current_user)):
    deposits = await deps.db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    return [DepositResponse(**{**d, "created_at": datetime.fromisoformat(d["created_at"]) if isinstance(d["created_at"], str) else d["created_at"]}) for d in deposits]


@router.get("/summary")
async def get_profit_summary(user: dict = Depends(deps.get_current_user)):
    """Get financial summary for the current user - uses unified calculation utility
    
    NOTE: For Master Admin, account_value is the actual Merin balance.
    Licensee funds are ALREADY PART OF this balance (they deposited into it).
    We do NOT add licensee funds on top.
    """
    from utils.calculations import get_user_financial_summary
    
    user_id = user["id"]
    logger.info(f"GET /profit/summary called for user_id={user_id}, email={user.get('email')}, role={user.get('role')}")
    
    try:
        summary = await get_user_financial_summary(deps.db, user_id, user)
        
        logger.info(f"GET /profit/summary response for {user_id}: account_value={summary.get('account_value')}, total_profit={summary.get('total_profit')}, is_licensee={summary.get('is_licensee')}")
        
        return {
            "total_deposits": summary["total_deposits"],
            "total_projected_profit": summary["total_projected_profit"],
            "total_actual_profit": summary["total_profit"],
            "profit_difference": round(summary["total_profit"] - summary["total_projected_profit"], 2),
            "account_value": summary["account_value"],
            "total_trades": summary["total_trades"],
            "performance_rate": summary["performance_rate"],
            "is_licensee": summary.get("is_licensee", False),
            "license_type": summary.get("license_type")
        }
    except Exception as e:
        logger.error(f"GET /profit/summary FAILED for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate summary: {str(e)}")


@router.get("/debug-calculation")
async def debug_profit_calculation(user: dict = Depends(deps.get_current_user)):
    """DEBUG ENDPOINT: Returns detailed calculation breakdown for troubleshooting.
    
    This helps diagnose why a user's account value might be incorrect.
    """
    user_id = user["id"]
    debug_info = {
        "user_id": user_id,
        "email": user.get("email"),
        "role": user.get("role"),
        "steps": []
    }
    
    try:
        # Step 1: Find license
        license = await deps.db.licenses.find_one(
            {"user_id": user_id, "is_active": True},
            {"_id": 0}
        )
        
        if license:
            debug_info["license_found"] = True
            debug_info["license_data"] = {
                "id": license.get("id"),
                "user_id": license.get("user_id"),
                "license_type": license.get("license_type"),
                "starting_amount": license.get("starting_amount"),
                "current_amount": license.get("current_amount"),
                "effective_start_date": str(license.get("effective_start_date")),
                "start_date": str(license.get("start_date")),
                "is_active": license.get("is_active")
            }
            debug_info["steps"].append("✓ License document found")
        else:
            debug_info["license_found"] = False
            debug_info["steps"].append("✗ No license found for user_id")
            # Try to find any license in the system with similar email
            user_email = user.get("email")
            if user_email:
                all_licenses = await deps.db.licenses.find({"is_active": True}, {"_id": 0}).to_list(100)
                for lic in all_licenses:
                    lic_user = await deps.db.users.find_one({"id": lic.get("user_id")}, {"_id": 0, "email": 1, "full_name": 1})
                    if lic_user and lic_user.get("email") == user_email:
                        debug_info["potential_license_match"] = {
                            "license_user_id": lic.get("user_id"),
                            "query_user_id": user_id,
                            "reason": "Found license with matching email but different user_id"
                        }
                        break
        
        # Step 2: Find master admin
        master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1, "email": 1})
        if master_admin:
            debug_info["master_admin_id"] = master_admin.get("id")
            debug_info["steps"].append(f"✓ Master admin found: {master_admin.get('id')}")
        else:
            debug_info["master_admin_id"] = None
            debug_info["steps"].append("✗ No master admin found")
        
        # Step 3: Count master admin trades
        if master_admin:
            all_master_trades = await deps.db.trade_logs.find(
                {"user_id": master_admin["id"], "did_not_trade": {"$ne": True}},
                {"_id": 0, "created_at": 1, "trade_date": 1}
            ).to_list(10000)
            
            traded_dates = set()
            for trade in all_master_trades:
                trade_date = trade.get("trade_date")
                if not trade_date:
                    created = trade.get("created_at")
                    if created:
                        if isinstance(created, datetime):
                            trade_date = created.strftime("%Y-%m-%d")
                        else:
                            trade_date = str(created)[:10]
                if trade_date:
                    traded_dates.add(str(trade_date)[:10])
            
            debug_info["master_admin_total_trade_days"] = len(traded_dates)
            debug_info["master_admin_trade_dates_sample"] = sorted(list(traded_dates))[:10]  # First 10
            debug_info["steps"].append(f"✓ Master admin has {len(traded_dates)} unique trade days")
            
            # If license found, show how many trades are AFTER the effective start date
            if license:
                eff_start = license.get("effective_start_date") or license.get("start_date")
                if eff_start:
                    start_str = str(eff_start)[:10]
                    trades_after_start = [d for d in traded_dates if d >= start_str]
                    debug_info["license_effective_start"] = start_str
                    debug_info["trades_after_license_start"] = len(trades_after_start)
                    debug_info["trades_after_start_sample"] = sorted(trades_after_start)[:10]
                    debug_info["steps"].append(f"✓ {len(trades_after_start)} trades are on/after license start date ({start_str})")
        
        # Step 4: Calculate if honorary
        if license:
            from utils.calculations import _is_honorary, calculate_honorary_licensee_value
            is_hon = _is_honorary(license.get("license_type"))
            debug_info["is_honorary"] = is_hon
            
            if is_hon:
                debug_info["steps"].append(f"✓ License type '{license.get('license_type')}' is honorary")
                
                # Calculate value
                try:
                    calc_value = await calculate_honorary_licensee_value(deps.db, license)
                    debug_info["calculated_value"] = calc_value
                    debug_info["calculated_profit"] = round(calc_value - float(license.get("starting_amount", 0) or 0), 2)
                    debug_info["steps"].append(f"✓ Calculated value: ${calc_value}")
                except Exception as e:
                    debug_info["calculation_error"] = str(e)
                    debug_info["steps"].append(f"✗ Calculation failed: {e}")
            else:
                debug_info["steps"].append(f"License type '{license.get('license_type')}' is NOT honorary - using current_amount")
                debug_info["calculated_value"] = license.get("current_amount", license.get("starting_amount", 0))
        
        # Step 5: Get the actual summary
        from utils.calculations import get_user_financial_summary
        summary = await get_user_financial_summary(deps.db, user_id, user)
        debug_info["summary_result"] = {
            "account_value": summary.get("account_value"),
            "total_profit": summary.get("total_profit"),
            "is_licensee": summary.get("is_licensee"),
            "total_trades": summary.get("total_trades")
        }
        debug_info["steps"].append(f"✓ Final summary: account_value=${summary.get('account_value')}, profit=${summary.get('total_profit')}")
        
        return debug_info
        
    except Exception as e:
        debug_info["error"] = str(e)
        debug_info["steps"].append(f"✗ Error during debug: {e}")
        return debug_info


@router.post("/calculate-exit")
async def calculate_exit(lot_size: float):
    exit_value = calculate_exit_value(lot_size)
    return {
        "lot_size": lot_size,
        "exit_value": exit_value,
        "formula": "LOT Size × 15"
    }


@router.post("/simulate-withdrawal")
async def simulate_withdrawal(data: WithdrawalSimulation, user: dict = Depends(deps.get_current_user)):
    """Simulate withdrawal with fee calculation - uses unified account value calculation"""
    from utils.calculations import calculate_account_value
    
    fees = calculate_withdrawal_fees(data.amount)
    
    # Get current account value using unified calculation
    account_value = await calculate_account_value(deps.db, user["id"], user)
    
    if data.amount > account_value:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    return {
        **fees,
        "current_balance": round(account_value, 2),
        "balance_after_withdrawal": round(account_value - data.amount, 2)
    }


@router.delete("/reset")
async def reset_profit_tracker(user_id: Optional[str] = None, user: dict = Depends(deps.get_current_user)):
    """Reset all profit tracker data for the current user or a simulated member (Master Admin only)"""
    admin_roles = {"master_admin", "super_admin", "basic_admin"}
    
    # Determine target user
    target_user_id = user["id"]
    
    # If user_id provided and requester is Master Admin, reset that user's data
    if user_id:
        if user.get("role") != "master_admin":
            raise HTTPException(status_code=403, detail="Only Master Admin can reset other users' data")
        # Verify the target user exists before resetting
        target_user = await deps.db.users.find_one({"id": user_id})
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        # Prevent resetting any admin account
        if target_user.get("role") in admin_roles:
            raise HTTPException(status_code=403, detail="Admin accounts cannot be reset")
        target_user_id = user_id
        logger.info(f"Master Admin {user['id']} resetting data for user {user_id}")
    else:
        # Prevent admins from resetting their own account
        if user.get("role") in admin_roles:
            raise HTTPException(status_code=403, detail="Admin accounts cannot be reset. This action is only available for member accounts.")
        logger.info(f"User {user['id']} resetting their own data")
    
    # Delete deposits
    deleted_deposits = await deps.db.deposits.delete_many({"user_id": target_user_id})
    # Delete trade logs
    deleted_trades = await deps.db.trade_logs.delete_many({"user_id": target_user_id})
    # Also reset user's onboarding status
    await deps.db.users.update_one(
        {"id": target_user_id},
        {"$set": {
            "onboarding_completed": False,
            "trading_type": None,
            "trading_start_date": None
        }}
    )
    
    return {
        "message": "Profit tracker reset successfully", 
        "deleted": True,
        "target_user_id": target_user_id,
        "deposits_deleted": deleted_deposits.deleted_count,
        "trades_deleted": deleted_trades.deleted_count
    }


@router.post("/withdrawal")
async def record_withdrawal(data: WithdrawalRequest, user: dict = Depends(deps.get_current_user)):
    """Record a withdrawal from the Merin account"""
    # Calculate fees (Binance fee moved to deposit)
    merin_fee = data.amount * 0.03  # 3% Merin fee only
    net_amount = data.amount - merin_fee
    
    # Calculate estimated arrival date (2 business days)
    estimated_arrival = add_business_days(datetime.now(timezone.utc), 2)
    
    # Record as negative deposit (withdrawal)
    withdrawal = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": -data.amount,  # Negative to indicate withdrawal
        "product": "WITHDRAWAL",  # Mark as withdrawal type
        "currency": "USDT",
        "notes": data.notes or "Withdrawal to Binance",
        "is_withdrawal": True,
        "gross_amount": data.amount,
        "merin_fee": merin_fee,
        "net_amount": net_amount,
        "estimated_arrival": estimated_arrival.strftime("%Y-%m-%d"),
        "confirmed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.deposits.insert_one(withdrawal)
    
    # Create notification for admins
    await create_admin_notification(
        notification_type="withdrawal",
        title="New Withdrawal",
        message=f"{user['full_name']} withdrew ${data.amount:.2f}",
        user_id=user["id"],
        user_name=user["full_name"],
        amount=data.amount,
        metadata={"net_amount": net_amount, "merin_fee": merin_fee}
    )
    
    return {
        "message": "Withdrawal recorded successfully",
        "withdrawal_id": withdrawal["id"],
        "gross_amount": data.amount,
        "merin_fee": round(merin_fee, 2),
        "net_amount": round(net_amount, 2)
    }


@router.get("/withdrawals")
async def get_withdrawals(user: dict = Depends(deps.get_current_user)):
    """Get all withdrawals for the current user from the withdrawals collection and deposits with is_withdrawal=True"""
    # CRITICAL FIX: Get withdrawals from BOTH places:
    # 1. The dedicated withdrawals collection (actual withdrawal requests)
    # 2. The deposits collection with is_withdrawal=True or negative amounts (legacy)
    
    # Get from withdrawals collection
    actual_withdrawals = await deps.db.withdrawals.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Convert to have negative amounts for frontend consumption
    # (withdrawals collection stores positive amounts, but frontend expects negative)
    for w in actual_withdrawals:
        if w.get("amount", 0) > 0:
            w["amount"] = -w["amount"]  # Make negative for frontend
    
    # Also get legacy withdrawals from deposits collection
    legacy_withdrawals = await deps.db.deposits.find(
        {
            "user_id": user["id"], 
            "$or": [
                {"is_withdrawal": True},
                {"amount": {"$lt": 0}}  # Also include negative amounts
            ]
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Combine both sources (dedupe by id if needed)
    seen_ids = set()
    combined = []
    for w in actual_withdrawals + legacy_withdrawals:
        w_id = w.get("id")
        if w_id and w_id not in seen_ids:
            seen_ids.add(w_id)
            combined.append(w)
        elif not w_id:
            combined.append(w)
    
    # Sort by created_at descending
    combined.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return combined


@router.put("/withdrawals/{withdrawal_id}/confirm")
async def confirm_withdrawal_receipt(
    withdrawal_id: str, 
    data: ConfirmReceiptRequest,
    user: dict = Depends(deps.get_current_user)
):
    """Confirm receipt of a withdrawal"""
    result = await deps.db.deposits.update_one(
        {"id": withdrawal_id, "user_id": user["id"], "is_withdrawal": True},
        {"$set": {"confirmed_at": data.confirmed_at}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    return {"message": "Receipt confirmed", "confirmed_at": data.confirmed_at}


@router.post("/commission")
async def record_commission(data: CommissionCreate, user: dict = Depends(deps.get_current_user)):
    """Record a commission from referral trades"""
    # Use the specified commission date or default to today
    commission_date = data.commission_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    commission = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": data.amount,
        "traders_count": data.traders_count,
        "notes": data.notes or f"Commission from {data.traders_count} referral trades",
        "commission_date": commission_date,
        "skip_deposit": data.skip_deposit,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.commissions.insert_one(commission)
    
    # Also record as a deposit (commission adds to account balance) — unless skip_deposit
    if not data.skip_deposit:
        deposit = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "amount": data.amount,
            "product": "COMMISSION",
            "currency": "USDT",
            "notes": f"Referral commission ({data.traders_count} traders)",
            "is_commission": True,
            "commission_date": commission_date,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await deps.db.deposits.insert_one(deposit)
    
    return {
        "message": "Commission recorded successfully",
        "commission_id": commission["id"],
        "amount": data.amount,
        "traders_count": data.traders_count,
        "commission_date": commission_date,
        "deposit_created": not data.skip_deposit
    }


@router.get("/commissions")
async def get_commissions(user: dict = Depends(deps.get_current_user)):
    """Get all commissions for the current user"""
    commissions = await deps.db.commissions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return commissions


@router.get("/vsd")
async def get_virtual_share_distribution(user: dict = Depends(deps.require_master_admin)):
    """Get Virtual Share Distribution (VSD) for Master Admin.
    
    Shows how the Master Admin's Merin balance is distributed:
    - Total Pool (Master Admin's Merin balance - the actual trading account)
    - Master Admin's remaining portion (their share after licensee allocations)
    - Total licensee virtual shares
    - Breakdown per licensee (Current Balance, Total Deposit, Total Profit, % Share)
    
    NOTE: Licensee funds are PART OF the total pool (they deposited into it).
    """
    from utils.calculations import get_master_admin_financial_breakdown as get_breakdown
    
    breakdown = await get_breakdown(deps.db, user["id"], user)
    return breakdown


@router.get("/balance-on-date")
async def get_balance_on_date(
    date: str,
    user_id: Optional[str] = None,
    user: dict = Depends(deps.get_current_user)
):
    """
    Get the user's account balance as of a specific date.
    
    This is the authoritative backend calculation that the frontend should use
    for historical balance lookups instead of frontend-side recalculation.
    
    The balance is calculated as:
    - Sum of all deposits/withdrawals up to and including the date
    - Plus sum of all profits/commissions from trades up to and including the date
    
    Args:
        date: Date string in YYYY-MM-DD format (end of day)
        user_id: Optional user ID (for admin simulation)
    
    Returns:
        balance_on_date: The account balance at end of the given date
        lot_size: The LOT size (balance / 980)
        date: The requested date
    """
    # Determine target user
    target_user_id = user["id"]
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    # Parse the date
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        target_date_str = target_date.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all deposits up to and including the target date
    deposits = await deps.db.deposits.find(
        {
            "user_id": target_user_id,
            "created_at": {"$lte": target_date_str}
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Get all trades up to and including the target date
    trades = await deps.db.trade_logs.find(
        {
            "user_id": target_user_id,
            "created_at": {"$lte": target_date_str}
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Calculate net deposits (positive = deposit, negative = withdrawal)
    total_net_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit"])
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_commission = sum(t.get("commission", 0) for t in trades)
    
    balance_on_date = round(total_net_deposits + total_profit + total_commission, 2)
    lot_size = truncate_lot_size(balance_on_date) if balance_on_date > 0 else 0
    
    return {
        "balance_on_date": balance_on_date,
        "lot_size": lot_size,
        "date": date,
        "deposits_count": len(deposits),
        "trades_count": len(trades),
        "total_deposits": round(sum(d.get("amount", 0) for d in deposits if d.get("amount", 0) > 0), 2),
        "total_withdrawals": round(abs(sum(d.get("amount", 0) for d in deposits if d.get("amount", 0) < 0)), 2),
        "total_profit": round(total_profit, 2),
        "total_commission": round(total_commission, 2)
    }


@router.get("/daily-balances")
async def get_daily_balances(
    start_date: str,
    end_date: str,
    user_id: Optional[str] = None,
    user: dict = Depends(deps.get_current_user)
):
    """
    Get daily balance calculations for a date range.
    
    CRITICAL: The "Balance Before" for any day represents the account balance
    at the START of that trading day, BEFORE any trades happen.
    
    Timeline for a single day:
    1. Balance Before = previous day's ending balance
    2. User trades → earns profit + commission
    3. User may deposit or withdraw
    4. Day ends with: Balance Before + Profit + Commission + Deposits - Withdrawals
    
    For calculating Balance Before:
    - Deposits/Withdrawals on day D affect the ENDING balance of day D
    - This means they affect the "Balance Before" of day D+1
    - NOT the "Balance Before" of day D itself
    """
    # Determine target user
    target_user_id = user["id"]
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    # Parse dates
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    
    # Check for balance override
    balance_override = await deps.db.balance_overrides.find_one(
        {"user_id": target_user_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    override_date = None
    override_adjustment = 0
    if balance_override:
        override_date = balance_override.get("effective_date")
        override_adjustment = balance_override.get("adjustment_amount", 0)
    
    # Get ALL deposits (including withdrawals stored as negative deposits)
    all_deposits = await deps.db.deposits.find(
        {"user_id": target_user_id},
        {"_id": 0}
    ).to_list(10000)
    
    # Get withdrawals from the separate withdrawals collection
    all_withdrawals = await deps.db.withdrawals.find(
        {
            "user_id": target_user_id,
            "status": {"$ne": "rejected"}
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Get all trades
    all_trades = await deps.db.trade_logs.find(
        {"user_id": target_user_id},
        {"_id": 0}
    ).to_list(10000)
    
    # Group transactions by date
    deposits_by_date = {}  # Positive amounts (actual deposits)
    withdrawals_by_date = {}  # Positive amounts (money leaving)
    trades_by_date = {}
    
    # Process deposits
    for d in all_deposits:
        amount = d.get("amount", 0)
        date_key = d.get("created_at", "")[:10]
        dep_type = d.get("type", "")
        if not date_key:
            continue
        
        # CRITICAL FIX: Skip type=profit entries - these are duplicates of trade_logs
        # and would cause double-counting if included as deposits
        if dep_type == "profit":
            continue
        
        if amount > 0 and not d.get("is_withdrawal"):
            # Regular deposit (initial, deposit, etc.)
            deposits_by_date[date_key] = deposits_by_date.get(date_key, 0) + amount
        elif amount < 0 or d.get("is_withdrawal"):
            # Withdrawal stored as negative deposit
            withdrawals_by_date[date_key] = withdrawals_by_date.get(date_key, 0) + abs(amount)
    
    # Process withdrawals from withdrawals collection
    for w in all_withdrawals:
        amount = w.get("amount", 0)
        date_key = w.get("created_at", "")[:10]
        if date_key and amount > 0:
            withdrawals_by_date[date_key] = withdrawals_by_date.get(date_key, 0) + amount
    
    # Process trades
    for t in all_trades:
        date_key = t.get("created_at", "")[:10]
        if not date_key:
            continue
        if date_key not in trades_by_date:
            trades_by_date[date_key] = {"profit": 0, "commission": 0, "lot_size": None, "projected": None}
        trades_by_date[date_key]["profit"] += t.get("actual_profit", 0)
        trades_by_date[date_key]["commission"] += t.get("commission", 0)
        if t.get("lot_size"):
            trades_by_date[date_key]["lot_size"] = t.get("lot_size")
            trades_by_date[date_key]["projected"] = t.get("projected_profit")
    
    # Get all unique dates
    all_dates = sorted(set(
        list(deposits_by_date.keys()) + 
        list(withdrawals_by_date.keys()) + 
        list(trades_by_date.keys())
    ))
    
    # Calculate running balance FORWARD from the first transaction
    running_balance = 0.0
    start_date_str = start.strftime("%Y-%m-%d")
    override_applied = False
    
    # First, calculate the balance at the START of start_date
    for date_key in all_dates:
        if date_key >= start_date_str:
            break
        
        # Check if override should be applied
        if not override_applied and override_date and date_key >= override_date:
            running_balance += override_adjustment
            override_applied = True
        
        # For dates BEFORE our range, apply all transactions to get running balance
        # Order: deposits → trades → withdrawals
        running_balance += deposits_by_date.get(date_key, 0)
        trade_data = trades_by_date.get(date_key, {})
        running_balance += trade_data.get("profit", 0)
        running_balance += trade_data.get("commission", 0)
        running_balance -= withdrawals_by_date.get(date_key, 0)
    
    # Now iterate through the requested date range
    daily_balances = []
    current_date = start
    
    while current_date <= end:
        date_key = current_date.strftime("%Y-%m-%d")
        
        # Check if we need to apply the override
        if not override_applied and override_date and date_key >= override_date:
            running_balance += override_adjustment
            override_applied = True
        
        # CRITICAL: "Balance Before" is balance at START of day
        # BEFORE deposits, trades, or withdrawals
        balance_before = round(running_balance, 2)
        lot_size = truncate_lot_size(balance_before) if balance_before > 0 else 0
        target_profit = round(lot_size * 15, 2)
        
        trade_data = trades_by_date.get(date_key, {})
        actual_profit = trade_data.get("profit")
        commission = trade_data.get("commission", 0)
        stored_lot_size = trade_data.get("lot_size")
        stored_projected = trade_data.get("projected")
        
        day_deposits = deposits_by_date.get(date_key, 0)
        day_withdrawals = withdrawals_by_date.get(date_key, 0)
        
        daily_balances.append({
            "date": date_key,
            "balance_before": balance_before,
            "lot_size": lot_size,
            "target_profit": target_profit,
            "actual_profit": actual_profit if actual_profit is not None else None,
            "commission": commission if commission is not None else None,
            "has_trade": date_key in trades_by_date,
            "stored_lot_size": stored_lot_size,
            "stored_projected": stored_projected,
            "day_deposits": day_deposits,
            "day_withdrawals": day_withdrawals,
        })
        
        # Apply this day's transactions to get ending balance
        # which becomes tomorrow's "Balance Before"
        running_balance += day_deposits
        if actual_profit is not None:
            running_balance += actual_profit
        if commission:
            running_balance += commission
        running_balance -= day_withdrawals
        
        current_date += timedelta(days=1)
    
    return {
        "daily_balances": daily_balances,
        "start_date": start_date,
        "end_date": end_date,
        "user_id": target_user_id,
        "override_applied": override_applied,
        "override_amount": override_adjustment if override_applied else None,
        "debug": {
            "total_deposits": sum(deposits_by_date.values()),
            "total_withdrawals": sum(withdrawals_by_date.values()),
            "deposit_dates": list(deposits_by_date.keys()),
            "withdrawal_dates": list(withdrawals_by_date.keys()),
        }
    }


@router.get("/debug-transactions")
async def debug_transactions(
    user_id: Optional[str] = None,
    user: dict = Depends(deps.get_current_user)
):
    """
    Debug endpoint to see ALL raw transaction data for troubleshooting balance issues.
    Admin only.
    """
    if user.get("role") not in ["admin", "basic_admin", "super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    target_user_id = user_id or user["id"]
    
    # Get ALL deposits
    deposits = await deps.db.deposits.find(
        {"user_id": target_user_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(10000)
    
    # Get ALL withdrawals from withdrawals collection
    withdrawals = await deps.db.withdrawals.find(
        {"user_id": target_user_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(10000)
    
    # Get ALL trades
    trades = await deps.db.trade_logs.find(
        {"user_id": target_user_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(10000)
    
    # Get balance overrides
    overrides = await deps.db.balance_overrides.find(
        {"user_id": target_user_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    # Calculate running totals
    # CRITICAL: Exclude type=profit entries from deposit totals to avoid double-counting
    total_positive_deposits = sum(d.get("amount", 0) for d in deposits if d.get("amount", 0) > 0 and not d.get("is_withdrawal") and d.get("type") != "profit")
    total_profit_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") == "profit")
    total_negative_deposits = sum(abs(d.get("amount", 0)) for d in deposits if d.get("amount", 0) < 0 or d.get("is_withdrawal"))
    total_withdrawals_collection = sum(w.get("amount", 0) for w in withdrawals if w.get("status") != "rejected")
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_commission = sum(t.get("commission", 0) for t in trades)
    
    # Get latest override
    latest_override = overrides[-1] if overrides else None
    override_amount = latest_override.get("adjustment_amount", 0) if latest_override else 0
    
    # Calculate expected account value
    net_deposits = total_positive_deposits - total_negative_deposits - total_withdrawals_collection
    expected_account_value = net_deposits + total_profit + total_commission + override_amount
    
    return {
        "user_id": target_user_id,
        "summary": {
            "total_positive_deposits": round(total_positive_deposits, 2),
            "total_profit_deposits_excluded": round(total_profit_deposits, 2),
            "total_negative_deposits_legacy": round(total_negative_deposits, 2),
            "total_withdrawals_collection": round(total_withdrawals_collection, 2),
            "total_profit": round(total_profit, 2),
            "total_commission": round(total_commission, 2),
            "override_amount": round(override_amount, 2),
            "expected_account_value": round(expected_account_value, 2),
        },
        "deposits": [
            {
                "date": d.get("created_at", "")[:10],
                "amount": d.get("amount"),
                "is_withdrawal": d.get("is_withdrawal", False),
                "type": d.get("type"),
            }
            for d in deposits
        ],
        "withdrawals_collection": [
            {
                "date": w.get("created_at", "")[:10],
                "amount": w.get("amount"),
                "status": w.get("status"),
            }
            for w in withdrawals
        ],
        "trades": [
            {
                "date": t.get("created_at", "")[:10],
                "actual_profit": t.get("actual_profit"),
                "commission": t.get("commission"),
                "lot_size": t.get("lot_size"),
            }
            for t in trades
        ],
        "overrides": overrides,
    }


@router.get("/my-recent-transactions")
async def get_my_recent_transactions(user: dict = Depends(deps.get_current_user)):
    """Get user's last 2 editable deposit/withdrawal simulations."""
    txns = await deps.db.deposits.find(
        {
            "user_id": user["id"],
            "type": {"$nin": ["profit", "initial"]},
        },
        {"_id": 0},
    ).sort("created_at", -1).limit(2).to_list(2)
    
    # Mark which ones are editable (within 48hrs and not corrected by admin)
    now = datetime.now(timezone.utc)
    for tx in txns:
        created = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00"))
        elapsed = (now - created).total_seconds()
        tx["editable"] = elapsed < 172800 and not tx.get("is_corrected")  # 48 hours
    
    return {"transactions": txns}


@router.put("/my-transactions/{tx_id}")
async def edit_my_transaction(
    tx_id: str,
    body: dict = Body(...),
    user: dict = Depends(deps.get_current_user),
):
    """Member edits their own recent transaction (last 2, within 48hrs)."""
    new_amount = body.get("new_amount")
    reason = body.get("reason", "Self correction")
    
    if new_amount is None:
        raise HTTPException(status_code=400, detail="new_amount is required")
    
    tx = await deps.db.deposits.find_one({"id": tx_id, "user_id": user["id"]}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx.get("type") in ["profit", "initial"]:
        raise HTTPException(status_code=400, detail="Cannot edit this type of transaction")
    
    if tx.get("is_corrected"):
        raise HTTPException(status_code=400, detail="This transaction was already corrected by admin")
    
    # Check 48hr window
    created = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00"))
    elapsed = (datetime.now(timezone.utc) - created).total_seconds()
    if elapsed > 172800:
        raise HTTPException(status_code=403, detail="Edit window expired (48 hours)")
    
    # Verify it's one of the last 2 non-profit transactions
    recent = await deps.db.deposits.find(
        {"user_id": user["id"], "type": {"$nin": ["profit", "initial"]}},
        {"_id": 0, "id": 1},
    ).sort("created_at", -1).limit(2).to_list(2)
    recent_ids = {r["id"] for r in recent}
    if tx_id not in recent_ids:
        raise HTTPException(status_code=403, detail="Can only edit your last 2 transactions")
    
    old_amount = tx.get("amount", 0)
    now = datetime.now(timezone.utc).isoformat()
    
    correction_record = {
        "old_amount": old_amount,
        "new_amount": new_amount,
        "reason": reason,
        "corrected_by": user["id"],
        "corrected_by_name": user.get("full_name", "Member"),
        "corrected_at": now,
        "self_edit": True,
    }
    
    await deps.db.deposits.update_one(
        {"id": tx_id},
        {
            "$set": {"amount": new_amount, "updated_at": now},
            "$push": {"corrections": correction_record},
        },
    )
    
    return {
        "message": "Transaction updated",
        "tx_id": tx_id,
        "old_amount": old_amount,
        "new_amount": new_amount,
    }


@router.post("/licensee/deposit")
async def create_licensee_deposit(
    amount: float = Form(...),
    deposit_date: str = Form(...),
    notes: Optional[str] = Form(None),
    screenshot: UploadFile = File(...),
    user: dict = Depends(deps.get_current_user)
):
    """Submit a deposit request (Licensees only)"""
    # Check if user is a licensee
    license = await deps.db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensed users can use this feature")
    
    # Upload screenshot
    screenshot_url = None
    try:
        contents = await screenshot.read()
        upload_result = cloudinary.uploader.upload(
            contents,
            folder="licensee_deposits",
            resource_type="auto"
        )
        screenshot_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload screenshot: {str(e)}")
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "type": "deposit",
        "amount": amount,
        "deposit_date": deposit_date,
        "notes": notes,
        "screenshot_url": screenshot_url,
        "status": "pending",
        "feedback": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.licensee_transactions.insert_one(transaction)
    
    # Notify master admin
    admins = await deps.db.users.find({"role": "master_admin"}, {"_id": 0, "id": 1}).to_list(100)
    for admin in admins:
        notification = {
            "id": str(uuid.uuid4()),
            "type": "licensee_deposit",
            "title": "New Licensee Deposit Request",
            "message": f"{user.get('full_name', 'A licensee')} submitted a deposit request for ${amount:,.2f}",
            "user_id": admin["id"],
            "from_user_id": user["id"],
            "transaction_id": transaction["id"],
            "amount": amount,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await deps.db.notifications.insert_one(notification)
    
    return {"message": "Deposit request submitted successfully", "transaction_id": transaction["id"]}


@router.post("/licensee/withdrawal")
async def create_licensee_withdrawal(
    amount: float = Form(...),
    notes: Optional[str] = Form(None),
    user: dict = Depends(deps.get_current_user)
):
    """Submit a withdrawal request (Licensees only) - 5 business days processing
    
    IMPORTANT: Withdrawal amount is IMMEDIATELY deducted from the licensee's balance.
    """
    # Check if user is a licensee
    license = await deps.db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensed users can use this feature")
    
    # Check if user has sufficient balance - use dynamic calculation for honorary
    if _is_honorary(license.get("license_type")):
        from utils.calculations import calculate_honorary_licensee_value
        current_balance = await calculate_honorary_licensee_value(deps.db, license)
    else:
        current_balance = license.get("current_amount", license.get("starting_amount", 0))
    
    if amount > current_balance:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Current balance: ${current_balance:,.2f}")
    
    # Calculate fees
    fees = calculate_withdrawal_fees(amount)
    net_amount = fees["net_amount"]
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "type": "withdrawal",
        "amount": amount,
        "gross_amount": amount,
        "merin_fee": fees["merin_fee"],
        "binance_fee": fees["binance_fee"],
        "total_fees": fees["total_fees"],
        "net_amount": net_amount,
        "notes": notes,
        "status": "pending",
        "processing_days": 5,  # 5 business days for licensees
        "feedback": [],
        "balance_before": current_balance,
        "balance_after": current_balance - amount,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.licensee_transactions.insert_one(transaction)
    
    # IMMEDIATELY deduct from licensee's balance
    # For honorary, we reduce starting_amount since current value is computed dynamically
    if _is_honorary(license.get("license_type")):
        new_starting = license.get("starting_amount", 0) - amount
        await deps.db.licenses.update_one(
            {"id": license["id"]},
            {"$set": {"starting_amount": max(new_starting, 0), "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        new_balance = current_balance - amount
        await deps.db.licenses.update_one(
            {"id": license["id"]},
            {"$set": {"current_amount": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    # Also update user's account_value
    await deps.db.users.update_one(
        {"id": user["id"]},
        {"$set": {"account_value": new_balance}}
    )
    
    # Notify master admin
    admins = await deps.db.users.find({"role": "master_admin"}, {"_id": 0, "id": 1}).to_list(100)
    for admin in admins:
        notification = {
            "id": str(uuid.uuid4()),
            "type": "licensee_withdrawal",
            "title": "New Licensee Withdrawal Request",
            "message": f"{user.get('full_name', 'A licensee')} requested a withdrawal of ${amount:,.2f}",
            "user_id": admin["id"],
            "from_user_id": user["id"],
            "transaction_id": transaction["id"],
            "amount": amount,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await deps.db.notifications.insert_one(notification)
    
    return {
        "message": "Withdrawal request submitted successfully. Processing time: 5 business days.",
        "transaction_id": transaction["id"],
        "processing_days": 5
    }


@router.get("/licensee/transactions")
async def get_my_licensee_transactions(user: dict = Depends(deps.get_current_user)):
    """Get current user's licensee transactions"""
    # Check if user is a licensee
    license = await deps.db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        return {"transactions": [], "is_licensee": False}
    
    transactions = await deps.db.licensee_transactions.find(
        {"user_id": user["id"]}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"transactions": transactions, "is_licensee": True, "license": license}


@router.post("/licensee/transactions/{tx_id}/confirm")
async def confirm_licensee_transaction(tx_id: str, user: dict = Depends(deps.get_current_user)):
    """Licensee confirms the transaction after seeing admin's calculations"""
    tx = await deps.db.licensee_transactions.find_one({"id": tx_id, "user_id": user["id"]}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx["status"] != "awaiting_confirmation":
        raise HTTPException(status_code=400, detail="Transaction is not awaiting confirmation")
    
    await deps.db.licensee_transactions.update_one(
        {"id": tx_id},
        {"$set": {
            "status": "processing",
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify master admin
    admins = await deps.db.users.find({"role": "master_admin"}, {"_id": 0, "id": 1}).to_list(100)
    for admin in admins:
        notification = {
            "id": str(uuid.uuid4()),
            "type": "licensee_confirmation",
            "title": "Licensee Confirmed Transaction",
            "message": f"{user.get('full_name', 'A licensee')} confirmed their {tx['type']} request",
            "user_id": admin["id"],
            "from_user_id": user["id"],
            "transaction_id": tx_id,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await deps.db.notifications.insert_one(notification)
    
    return {"message": "Transaction confirmed. Admin will process your request."}


@router.get("/licensee/welcome-info")
async def get_licensee_welcome_info(user: dict = Depends(deps.get_current_user)):
    """Get licensee welcome info for first login screen"""
    # Check if user is a licensee
    license = await deps.db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        return {"is_licensee": False, "has_seen_welcome": True}
    
    # Check if user has seen welcome
    has_seen = user.get("has_seen_welcome", False)
    
    # Get master admin info
    master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0, "full_name": 1})
    master_admin_name = master_admin.get("full_name", "Master Admin") if master_admin else "Master Admin"
    
    # Calculate current balance dynamically for honorary licensees
    if _is_honorary(license.get("license_type")):
        from utils.calculations import calculate_honorary_licensee_value
        current_balance = await calculate_honorary_licensee_value(deps.db, license)
    else:
        current_balance = license.get("current_amount", license.get("starting_amount", 0))
    
    return {
        "is_licensee": True,
        "has_seen_welcome": has_seen,
        "licensee_name": user.get("full_name", "Licensee"),
        "starting_balance": license.get("starting_amount", 0),
        "current_balance": round(current_balance, 2),
        "effective_start_date": license.get("effective_start_date", license.get("start_date")),
        "license_type": license.get("license_type"),
        "master_admin_name": master_admin_name
    }


@router.post("/licensee/mark-welcome-seen")
async def mark_licensee_welcome_seen(user: dict = Depends(deps.get_current_user)):
    """Mark that licensee has seen the welcome screen"""
    # Verify user is a licensee
    license = await deps.db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensees can access this endpoint")
    
    await deps.db.users.update_one(
        {"id": user["id"]},
        {"$set": {"has_seen_welcome": True}}
    )
    
    return {"message": "Welcome screen marked as seen"}


@router.get("/licensee/daily-projection")
async def get_licensee_daily_projection(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(deps.get_current_user)
):
    """Get daily projection table for licensees (with Manager Traded column).
    
    Past dates use actual master admin trade data.
    Future dates assume manager trades every trading day (weekdays excl. holidays).
    """
    from utils.trading_days import get_holidays_for_range, is_trading_day as is_trading_day_with_holidays
    
    # Check if user is a licensee
    license = await deps.db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensees can access this endpoint")
    
    # Get effective start date from license
    effective_start = license.get("effective_start_date", license.get("start_date"))
    
    # Get master admin's trade logs to determine "Manager Traded" status
    master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1})
    master_admin_id = master_admin["id"] if master_admin else None
    
    # Get all master admin trades (exclude did_not_trade entries)
    master_trades = []
    if master_admin_id:
        master_trades = await deps.db.trade_logs.find(
            {"user_id": master_admin_id, "did_not_trade": {"$ne": True}},
            {"_id": 0, "trade_date": 1, "created_at": 1}
        ).to_list(10000)
    
    # Create a set of dates when master admin traded
    traded_dates = set()
    for trade in master_trades:
        trade_date = trade.get("trade_date")
        if not trade_date and trade.get("created_at"):
            trade_date = trade["created_at"][:10]
        if trade_date:
            traded_dates.add(trade_date)
    
    # Get licensee deposits (for adding to their account)
    licensee_deposits = await deps.db.licensee_transactions.find(
        {"user_id": user["id"], "type": "deposit", "status": "completed"},
        {"_id": 0}
    ).to_list(1000)
    
    # Map deposits by date
    deposit_by_date = {}
    for dep in licensee_deposits:
        dep_date = dep.get("completed_at", dep.get("created_at", ""))[:10]
        if dep_date:
            deposit_by_date[dep_date] = deposit_by_date.get(dep_date, 0) + dep.get("amount", 0)
    
    # Get trade overrides for this license
    overrides = {}
    license_id = license.get("id")
    if license_id:
        async for override in deps.db.licensee_trade_overrides.find({"license_id": license_id}, {"_id": 0}):
            overrides[override["date"]] = override
    
    # Build projection table with quarterly compounding
    projections = []
    current_balance = license.get("starting_amount", 0)
    
    # Parse start date
    try:
        start_dt = datetime.strptime(effective_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except:
        start_dt = datetime.now(timezone.utc)
    
    end_dt = datetime.now(timezone.utc) + timedelta(days=365)
    today = datetime.now(timezone.utc)
    
    # Get holidays for the date range
    holidays = get_holidays_for_range(start_dt.year, end_dt.year + 1)
    
    # Track quarter for quarterly compounding
    current_quarter = get_quarter(start_dt)
    current_year = start_dt.year
    quarter_daily_profit = round(truncate_lot_size(current_balance) * 15, 2)
    
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime("%Y-%m-%d")
        
        # Skip non-trading days (weekends + holidays)
        if not is_trading_day_with_holidays(current_dt, holidays):
            current_dt += timedelta(days=1)
            continue
        
        # Check for new quarter - recalculate daily profit
        new_quarter = get_quarter(current_dt)
        new_year = current_dt.year
        if new_year != current_year or new_quarter != current_quarter:
            quarter_daily_profit = round(truncate_lot_size(current_balance) * 15, 2)
            current_quarter = new_quarter
            current_year = new_year
        
        # Check for deposits on this date
        deposit_amount = deposit_by_date.get(date_str, 0)
        if deposit_amount > 0:
            current_balance += deposit_amount
        
        is_future = current_dt > today
        
        # For past dates: check if manager actually traded
        # For future dates: assume manager trades (projection)
        if is_future:
            manager_traded = True  # Projected
        else:
            override = overrides.get(date_str)
            if override:
                manager_traded = override.get("traded", False)
            elif date_str in traded_dates:
                manager_traded = True
            else:
                manager_traded = False
        
        projections.append({
            "date": date_str,
            "start_value": round(current_balance, 2),
            "account_value": round(current_balance + quarter_daily_profit, 2) if manager_traded else round(current_balance, 2),
            "lot_size": truncate_lot_size(current_balance),
            "daily_profit": quarter_daily_profit,
            "manager_traded": manager_traded,
            "is_projected": is_future,
            "has_override": date_str in overrides,
            "deposit": deposit_amount if deposit_amount > 0 else None
        })
        
        # Update balance
        if manager_traded:
            current_balance = round(current_balance + quarter_daily_profit, 2)
        
        current_dt += timedelta(days=1)
    
    return {
        "projections": projections,
        "effective_start_date": effective_start,
        "starting_amount": license.get("starting_amount", 0),
        "current_balance": round(current_balance, 2)
    }


@router.get("/license-projections")
async def get_my_license_projections(user: dict = Depends(deps.get_current_user)):
    """Get license projections for the current user (if they have an extended license)"""
    license_doc = await deps.db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    
    if not license_doc:
        return {"has_license": False, "message": "No active license found"}
    
    if license_doc["license_type"] != "extended":
        return {
            "has_license": True,
            "license_type": license_doc["license_type"],
            "message": "Honorary licenses use standard calculations"
        }
    
    # Calculate projections for extended license
    start_date = datetime.fromisoformat(license_doc["start_date"].replace("Z", "+00:00"))
    projections = calculate_extended_license_projections(
        license_doc["starting_amount"],
        start_date,
        365
    )
    
    # Get current values
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")
    current_projection = next((p for p in projections if p["date"] == today_str), None)
    
    # Get this month's projections
    current_month = today.strftime("%Y-%m")
    monthly_projections = [p for p in projections if p["date"].startswith(current_month)]
    
    return {
        "has_license": True,
        "license_type": "extended",
        "starting_amount": license_doc["starting_amount"],
        "start_date": license_doc["start_date"],
        "current_values": current_projection or (projections[-1] if projections else None),
        "monthly_projections": monthly_projections,
        "quarterly_summary": get_quarterly_summary(projections)
    }


@router.get("/master-admin-trades")
async def get_master_admin_trades(
    start_date: str = None,
    end_date: str = None,
    user: dict = Depends(deps.get_current_user)
):
    """
    Get master admin's trading status for each day in the date range.
    Used by extended licensees to determine if profit was credited.
    """
    # Only licensees can access this endpoint
    if not user.get("license_type"):
        raise HTTPException(status_code=403, detail="This endpoint is for licensees only")
    
    # Get the master admin
    master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0})
    if not master_admin:
        return {"trades": [], "message": "No master admin found"}
    
    # Build date query
    query = {"user_id": master_admin["id"]}
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
        query["created_at"] = {"$gte": start_dt.isoformat()}
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        if "created_at" in query:
            query["created_at"]["$lte"] = end_dt.isoformat()
        else:
            query["created_at"] = {"$lte": end_dt.isoformat()}
    
    # Get master admin's trades (exclude did_not_trade entries)
    query["did_not_trade"] = {"$ne": True}
    trades = await deps.db.trade_logs.find(query, {"_id": 0}).to_list(1000)
    
    # Create a dictionary of dates with trades
    trading_dates = {}
    for trade in trades:
        trade_date = trade.get("created_at", "")
        if isinstance(trade_date, str):
            date_key = trade_date[:10]  # Get YYYY-MM-DD
        else:
            date_key = trade_date.strftime("%Y-%m-%d")
        
        trading_dates[date_key] = {
            "traded": True,
            "actual_profit": trade.get("actual_profit", 0),
            "projected_profit": trade.get("projected_profit", 0)
        }
    
    return {
        "trading_dates": trading_dates,
        "total_trades": len(trades)
    }


@router.post("/balance-override")
async def create_balance_override(data: BalanceOverrideData, user: dict = Depends(deps.get_current_user)):
    """
    Create a balance override to sync the calculated balance with the actual Merin balance.
    This does NOT affect past balances - only future calculations will use this as the starting point.
    
    The override works by calculating the difference between the system's calculated balance
    and the actual Merin balance, then storing an adjustment that will be applied going forward.
    """
    user_id = user["id"]
    
    # Get current calculated balance
    deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("amount", 0) > 0)
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("amount", 0) < 0)
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_commission = sum(t.get("commission", 0) for t in trades)
    
    calculated_balance = total_deposits - total_withdrawals + total_profit + total_commission
    
    # Calculate the adjustment needed
    adjustment_amount = data.actual_balance - calculated_balance
    
    # Determine effective date
    if data.effective_date:
        effective_date = data.effective_date
    else:
        effective_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Store the balance override
    override_id = str(uuid.uuid4())
    override_record = {
        "id": override_id,
        "user_id": user_id,
        "actual_balance": data.actual_balance,
        "calculated_balance": round(calculated_balance, 2),
        "adjustment_amount": round(adjustment_amount, 2),
        "effective_date": effective_date,
        "reason": data.reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id
    }
    
    await deps.db.balance_overrides.insert_one(override_record)
    
    # Also update the user's record with the latest override info
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {
            "balance_override": {
                "id": override_id,
                "actual_balance": data.actual_balance,
                "adjustment_amount": round(adjustment_amount, 2),
                "effective_date": effective_date,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": "Balance override created successfully",
        "override": {
            "id": override_id,
            "actual_balance": data.actual_balance,
            "calculated_balance": round(calculated_balance, 2),
            "adjustment_amount": round(adjustment_amount, 2),
            "effective_date": effective_date
        }
    }


@router.get("/balance-override")
async def get_balance_override(user: dict = Depends(deps.get_current_user)):
    """Get the current balance override for the user"""
    user_id = user["id"]
    
    # Get the most recent override
    override = await deps.db.balance_overrides.find_one(
        {"user_id": user_id},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if not override:
        return {"has_override": False, "override": None}
    
    return {"has_override": True, "override": override}


@router.delete("/balance-override")
async def delete_balance_override(user: dict = Depends(deps.get_current_user)):
    """Remove the balance override for the user"""
    user_id = user["id"]
    
    # Remove all overrides for this user
    result = await deps.db.balance_overrides.delete_many({"user_id": user_id})
    
    # Remove from user record
    await deps.db.users.update_one(
        {"id": user_id},
        {"$unset": {"balance_override": ""}}
    )
    
    return {"message": f"Removed {result.deleted_count} balance override(s)"}


@router.get("/sync-validation")
async def get_sync_validation(user: dict = Depends(deps.get_current_user)):
    """
    Validate user's data completeness before allowing balance sync.
    Returns a detailed report of what needs to be fixed.
    """
    user_id = user["id"]
    user_data = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    validation = {
        "can_sync": True,
        "issues": [],
        "trading_start_date": user_data.get("trading_start_date"),
        "missing_trade_days": [],
        "pre_start_trades": [],
        "summary": {
            "total_trading_days": 0,
            "reported_days": 0,
            "missing_days": 0,
            "pre_start_trade_count": 0
        }
    }
    
    # Step 1: Check trading start date
    trading_start_date = user_data.get("trading_start_date")
    if not trading_start_date:
        validation["can_sync"] = False
        validation["issues"].append({
            "type": "no_start_date",
            "severity": "blocker",
            "message": "Trading start date is not set"
        })
        
        # Try to auto-detect from first trade or deposit
        first_trade = await deps.db.trade_logs.find_one(
            {"user_id": user_id, "did_not_trade": {"$ne": True}},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", 1)]
        )
        first_deposit = await deps.db.deposits.find_one(
            {"user_id": user_id},
            {"_id": 0, "created_at": 1},
            sort=[("created_at", 1)]
        )
        
        suggested_date = None
        if first_trade and first_deposit:
            trade_date = first_trade.get("created_at", "")[:10]
            deposit_date = first_deposit.get("created_at", "")[:10]
            suggested_date = min(trade_date, deposit_date)
        elif first_trade:
            suggested_date = first_trade.get("created_at", "")[:10]
        elif first_deposit:
            suggested_date = first_deposit.get("created_at", "")[:10]
        
        validation["suggested_start_date"] = suggested_date
        return validation
    
    # Parse start date
    try:
        start_date = datetime.strptime(trading_start_date, "%Y-%m-%d")
    except ValueError:
        validation["can_sync"] = False
        validation["issues"].append({
            "type": "invalid_start_date",
            "severity": "blocker",
            "message": f"Invalid trading start date format: {trading_start_date}"
        })
        return validation
    
    # Step 2: Check for missing trade days
    today = datetime.now(timezone.utc).date()
    
    # Get all trade logs for user
    all_trades = await deps.db.trade_logs.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(10000)
    
    # Create a set of dates with trade entries
    trade_dates = {}
    for trade in all_trades:
        date_key = trade.get("created_at", "")[:10]
        if date_key:
            trade_dates[date_key] = {
                "has_profit": trade.get("actual_profit") is not None,
                "did_not_trade": trade.get("did_not_trade", False),
                "actual_profit": trade.get("actual_profit"),
                "commission": trade.get("commission", 0)
            }
    
    # Get global holidays
    holidays = await deps.db.global_holidays.find({}, {"_id": 0}).to_list(1000)
    holiday_dates = set()
    for h in holidays:
        holiday_dates.add(h.get("date", "")[:10])
    
    # Get user holidays
    user_holidays = await deps.db.user_holidays.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    for h in user_holidays:
        holiday_dates.add(h.get("date", "")[:10])
    
    # Iterate through each day from start date to today
    current = start_date.date()
    missing_days = []
    
    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        day_of_week = current.weekday()
        
        # Skip weekends (Saturday=5, Sunday=6)
        if day_of_week >= 5:
            current += timedelta(days=1)
            continue
        
        # Skip holidays
        if date_str in holiday_dates:
            current += timedelta(days=1)
            continue
        
        # Skip today (might not have traded yet)
        if current == today:
            current += timedelta(days=1)
            continue
        
        # Check if this day has a trade entry
        trade_info = trade_dates.get(date_str)
        
        if not trade_info:
            # No entry at all
            missing_days.append({
                "date": date_str,
                "status": "no_entry",
                "message": "No trade entry for this day"
            })
        elif not trade_info["did_not_trade"] and not trade_info["has_profit"]:
            # Has entry but no actual profit reported (and not marked as did_not_trade)
            missing_days.append({
                "date": date_str,
                "status": "incomplete",
                "message": "Trade entry exists but actual profit not reported"
            })
        
        current += timedelta(days=1)
    
    validation["missing_trade_days"] = missing_days
    validation["summary"]["missing_days"] = len(missing_days)
    
    if missing_days:
        validation["can_sync"] = False
        validation["issues"].append({
            "type": "missing_trade_days",
            "severity": "blocker",
            "message": f"{len(missing_days)} trading day(s) without reported data",
            "count": len(missing_days)
        })
    
    # Calculate total trading days
    total_days = 0
    current = start_date.date()
    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        day_of_week = current.weekday()
        if day_of_week < 5 and date_str not in holiday_dates and current != today:
            total_days += 1
        current += timedelta(days=1)
    
    validation["summary"]["total_trading_days"] = total_days
    validation["summary"]["reported_days"] = total_days - len(missing_days)
    
    # Step 3: Check for trades before start date
    pre_start_trades = []
    for trade in all_trades:
        trade_date = trade.get("created_at", "")[:10]
        if trade_date and trade_date < trading_start_date:
            pre_start_trades.append({
                "date": trade_date,
                "actual_profit": trade.get("actual_profit", 0),
                "commission": trade.get("commission", 0),
                "did_not_trade": trade.get("did_not_trade", False)
            })
    
    validation["pre_start_trades"] = sorted(pre_start_trades, key=lambda x: x["date"])
    validation["summary"]["pre_start_trade_count"] = len(pre_start_trades)
    
    if pre_start_trades:
        # This is a warning, not a blocker, but user must acknowledge
        validation["issues"].append({
            "type": "pre_start_trades",
            "severity": "warning",
            "message": f"{len(pre_start_trades)} trade(s) exist before your start date",
            "count": len(pre_start_trades),
            "requires_acknowledgment": True
        })
    
    return validation


@router.post("/set-trading-start-date")
async def set_trading_start_date(
    trading_start_date: str = Body(..., embed=True),
    user: dict = Depends(deps.get_current_user)
):
    """Set or update the user's trading start date"""
    user_id = user["id"]
    
    # Validate date format
    try:
        datetime.strptime(trading_start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {
            "trading_start_date": trading_start_date,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": f"Trading start date set to {trading_start_date}"}


@router.post("/complete-onboarding")
async def complete_onboarding(data: OnboardingData, user: dict = Depends(deps.get_current_user)):
    """
    Complete the onboarding process for new or experienced traders.
    Creates initial deposits, withdrawals, and trade logs based on user input.
    
    If user already has data (reset scenario), this will add to existing data.
    For clean reset, call DELETE /profit/reset first.
    """
    try:
        # Check if this is a reset scenario - if user already completed onboarding before,
        # we should check if their data was properly cleared
        if user.get("onboarding_completed"):
            # User already completed onboarding - this might be a re-submit
            # Check if they have data (should have been cleared by reset)
            existing_deposits = await deps.db.deposits.count_documents({"user_id": user["id"]})
            existing_trades = await deps.db.trade_logs.count_documents({"user_id": user["id"]})
            
            # If they have data, this might be a duplicate submission - proceed anyway
            # but log it for debugging
            if existing_deposits > 0 or existing_trades > 0:
                logger.warning(f"User {user['id']} completing onboarding with existing data: {existing_deposits} deposits, {existing_trades} trades")
        
        # Track which deposits and trades we create
        created_deposits = []
        created_trades = []
        
        # 1. Create the initial deposit (starting balance)
        initial_deposit_id = str(uuid.uuid4())
        start_date = data.start_date if data.start_date else datetime.now(timezone.utc).isoformat()
        
        # Parse start date for ordering
        if isinstance(start_date, str):
            if 'T' in start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            start_dt = start_date
        
        initial_deposit = {
            "id": initial_deposit_id,
            "user_id": user["id"],
            "amount": data.starting_balance,
            "product": "MOIL10",
            "currency": "USDT",
            "notes": f"Initial balance - Onboarding ({data.user_type} trader)",
            "type": "initial",
            "created_at": start_dt.isoformat()
        }
        await deps.db.deposits.insert_one(initial_deposit)
        created_deposits.append(initial_deposit_id)
        
        # 2. Create additional deposits/withdrawals for experienced traders
        if data.user_type == 'experienced' and data.transactions:
            for tx in data.transactions:
                tx_id = str(uuid.uuid4())
                tx_date = datetime.fromisoformat(tx.date.replace('Z', '+00:00')) if 'T' in tx.date else datetime.strptime(tx.date[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
                deposit_entry = {
                    "id": tx_id,
                    "user_id": user["id"],
                    "amount": tx.amount if tx.type == 'deposit' else -tx.amount,
                    "product": "MOIL10",
                    "currency": "USDT",
                    "type": tx.type,
                    "notes": f"Onboarding {tx.type}",
                    "is_withdrawal": tx.type == 'withdrawal',
                    "created_at": tx_date.isoformat()
                }
                await deps.db.deposits.insert_one(deposit_entry)
                created_deposits.append(tx_id)
        
        # 3. Create trade logs for experienced traders
        if data.user_type == 'experienced' and data.trade_entries:
            # Calculate running balance for each trade
            running_balance = data.starting_balance
            
            # Add initial transactions to running balance calculation
            tx_by_date = {}
            if data.transactions:
                for tx in data.transactions:
                    tx_date_key = tx.date[:10]
                    if tx_date_key not in tx_by_date:
                        tx_by_date[tx_date_key] = 0
                    tx_by_date[tx_date_key] += tx.amount if tx.type == 'deposit' else -tx.amount
            
            # Sort trade entries by date
            sorted_entries = sorted(data.trade_entries, key=lambda e: e.date)
            
            for entry in sorted_entries:
                if entry.missed:
                    continue  # Skip missed days
                
                # Apply any transactions for this date BEFORE calculating lot size
                if entry.date in tx_by_date:
                    running_balance += tx_by_date[entry.date]
                
                # Use user-entered balance if provided, otherwise use running balance
                # This ensures Trade History matches Daily Projection when users enter custom balances
                effective_balance = entry.balance if entry.balance else running_balance
                
                # Calculate lot size and projected profit from effective balance
                lot_size = truncate_lot_size(effective_balance)
                projected_profit = round(lot_size * 15, 2)
                actual_profit = entry.actual_profit or 0
                commission = entry.commission or 0  # Daily commission from referrals
                profit_difference = round(actual_profit - projected_profit, 2)
                
                # Determine performance
                if actual_profit >= projected_profit:
                    performance = "exceeded" if actual_profit > projected_profit else "perfect"
                elif actual_profit > 0:
                    performance = "below"
                else:
                    performance = "below"
                
                # Create trade log
                trade_id = str(uuid.uuid4())
                trade_date = datetime.strptime(entry.date, "%Y-%m-%d").replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)
                
                # Get product and direction from entry or use defaults
                product = entry.product or 'MOIL10'
                direction = entry.direction or 'BUY'
                
                trade_log = {
                    "id": trade_id,
                    "user_id": user["id"],
                    "lot_size": lot_size,
                    "direction": direction,
                    "product": product,
                    "projected_profit": projected_profit,
                    "actual_profit": actual_profit,
                    "commission": commission,  # Daily commission from referrals
                    "profit_difference": profit_difference,
                    "performance": performance,
                    "signal_id": None,
                    "notes": "Imported via onboarding",
                    "is_retroactive": True,
                    "is_onboarding_import": True,
                    "created_at": trade_date.isoformat()
                }
                await deps.db.trade_logs.insert_one(trade_log)
                created_trades.append(trade_id)
                
                # Update running balance for next iteration (Balance + Profit + Commission)
                running_balance += actual_profit + commission
        
        # 4. If total_commission is provided (from final step), assign it to the LAST trade entry
        # This ensures it appears in the Daily Projection Commission column for the last trading day
        if data.total_commission and data.total_commission > 0 and created_trades:
            # Get the last trade log ID and update its commission field
            last_trade_id = created_trades[-1]
            
            # Update the last trade log with the total commission
            await deps.db.trade_logs.update_one(
                {"id": last_trade_id},
                {"$inc": {"commission": data.total_commission}}  # Add to any existing commission
            )
            
            logger.info(f"Assigned total commission ${data.total_commission} to last trade {last_trade_id}")
        
        # 5. Update user's onboarding status
        await deps.db.users.update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "onboarding_completed": True,
                    "trading_type": data.user_type,
                    "trading_start_date": data.start_date,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # 6. Create notification for admins about tracker reset (if experienced trader resetting)
        if data.user_type == 'experienced':
            await create_admin_notification(
                notification_type="tracker_reset",
                title="Tracker Reset",
                message=f"{user['full_name']} reset their tracker as experienced trader",
                user_id=user["id"],
                user_name=user["full_name"],
                amount=data.starting_balance,
                metadata={
                    "user_type": data.user_type,
                    "start_date": data.start_date,
                    "deposits_created": len(created_deposits),
                    "trades_created": len(created_trades)
                }
            )
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "deposits_created": len(created_deposits),
            "trades_created": len(created_trades),
            "starting_balance": data.starting_balance,
            "user_type": data.user_type,
            "total_commission": data.total_commission or 0
        }
        
    except Exception as e:
        logger.error(f"Onboarding failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")


@router.get("/onboarding-status")
async def get_onboarding_status(user: dict = Depends(deps.get_current_user)):
    """Check if user has completed onboarding and their trading type"""
    return {
        "onboarding_completed": user.get("onboarding_completed", False),
        "trading_type": user.get("trading_type"),  # 'new' or 'experienced'
        "trading_start_date": user.get("trading_start_date"),
        "has_deposits": bool(await deps.db.deposits.find_one({"user_id": user["id"]})),
        "has_trades": bool(await deps.db.trade_logs.find_one({"user_id": user["id"]}))
    }


@router.get("/licensee/year-projections")
async def get_licensee_year_projections(user_id: Optional[str] = None, user: dict = Depends(deps.get_current_user)):
    """Get year-by-year growth projections for a licensee using quarterly compounding.
    
    Formula: Daily Profit = round((Account Value at Quarter Start / 980) * 15, 2)
    Daily profit is FIXED for the entire quarter, recalculated at each new calendar quarter.
    Projections assume manager trades every trading day (weekdays excl. US market holidays).
    Admin can pass ?user_id=xxx to get projections for a specific licensee.
    
    Returns TWO types of projections:
    1. "projections" - Forward projections from TODAY's current balance (next 1/2/3/5 years)
    2. "license_year_projections" - Balance at end of License Year 1/2/3/5 from effective start date
    """
    try:
        from utils.trading_days import project_quarterly_growth, get_holidays_for_range

        target_user_id = user["id"]
        if user_id and user.get("role") in ("master_admin", "super_admin", "admin", "basic_admin"):
            target_user_id = user_id
        
        # Find any active honorary/honorary_fa license for this user
        license = await deps.db.licenses.find_one(
            {"user_id": target_user_id, "is_active": True, "license_type": {"$regex": "^honorary", "$options": "i"}},
            {"_id": 0}
        )
        if not license:
            # Fallback: any active license
            license = await deps.db.licenses.find_one(
                {"user_id": target_user_id, "is_active": True},
                {"_id": 0}
            )
        if not license:
            raise HTTPException(status_code=404, detail="No active license found")
        
        from utils.calculations import calculate_honorary_licensee_value
        current_value = float(await calculate_honorary_licensee_value(deps.db, license))
        starting_amount = float(license.get("starting_amount", 0) or 0)
        
        # Guard against zero or negative values
        if current_value <= 0:
            current_value = starting_amount or 1.0
        
        today = datetime.now(timezone.utc)
        
        # Get effective start date for license year calculations
        effective_start = license.get("effective_start_date") or license.get("start_date")
        if effective_start:
            try:
                start_str = str(effective_start)
                if "T" in start_str:
                    effective_start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                else:
                    effective_start_dt = datetime.strptime(start_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if effective_start_dt.tzinfo is None:
                    effective_start_dt = effective_start_dt.replace(tzinfo=timezone.utc)
            except Exception:
                effective_start_dt = today
        else:
            effective_start_dt = today
        
        # Get holidays for the full range needed
        start_year = min(effective_start_dt.year, today.year)
        holidays = get_holidays_for_range(start_year, start_year + 10)
        
        # Starting quarter daily profit (for display)
        starting_daily_profit = round(truncate_lot_size(current_value) * 15, 2)
        
        # === TYPE 1: Forward projections from TODAY's current balance ===
        projections = []
        for years in [1, 2, 3, 5]:
            trading_days = years * 250
            result = project_quarterly_growth(current_value, today, trading_days, holidays)
            
            total_profit = round(result["projected_value"] - starting_amount, 2)
            growth_pct = round(((result["projected_value"] / starting_amount) - 1) * 100, 1) if starting_amount > 0 else 0
            
            projections.append({
                "years": years,
                "projected_value": result["projected_value"],
                "total_profit": total_profit,
                "profit_from_current": result["total_profit"],
                "growth_percent": growth_pct,
                "trading_days": result["trading_days"],
                "quarter_breakdown": result["quarter_breakdown"]
            })
        
        # === TYPE 2: License Year End projections from EFFECTIVE START DATE ===
        # These show where the account will be at the end of License Year 1, 2, 3, 5
        license_year_projections = []
        for years in [1, 2, 3, 5]:
            trading_days = years * 250
            # Project from the original starting_amount and effective_start_date
            result = project_quarterly_growth(starting_amount, effective_start_dt, trading_days, holidays)
            
            total_profit = round(result["projected_value"] - starting_amount, 2)
            growth_pct = round(((result["projected_value"] / starting_amount) - 1) * 100, 1) if starting_amount > 0 else 0
            
            license_year_projections.append({
                "license_year": years,
                "projected_value": result["projected_value"],
                "total_profit": total_profit,
                "growth_percent": growth_pct,
                "trading_days": result["trading_days"],
                "from_start_date": effective_start_dt.strftime("%Y-%m-%d"),
            })
        
        return {
            "current_value": round(current_value, 2),
            "starting_amount": starting_amount,
            "current_profit": round(current_value - starting_amount, 2),
            "starting_daily_profit": starting_daily_profit,
            "trading_days_per_year": 250,
            "effective_start_date": effective_start_dt.strftime("%Y-%m-%d"),
            "projections": projections,  # Forward from today
            "license_year_projections": license_year_projections  # From effective start date
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Year projections failed for user_id={user_id or user.get('id')}: {e}", exc_info=True)
        # FALLBACK: Return simple projections from the license's current_amount
        # instead of crashing. This ensures users ALWAYS see SOMETHING.
        try:
            from utils.trading_days import project_quarterly_growth, get_holidays_for_range
            fallback_value = license.get("current_amount", license.get("starting_amount", 1000)) if license else 1000
            fallback_start = license.get("starting_amount", fallback_value) if license else fallback_value
            today = datetime.now(timezone.utc)
            holidays = get_holidays_for_range(today.year, today.year + 6)
            projections = []
            for years in [1, 2, 3, 5]:
                result = project_quarterly_growth(float(fallback_value), today, years * 250, holidays)
                projections.append({
                    "years": years,
                    "projected_value": result["projected_value"],
                    "total_profit": round(result["projected_value"] - float(fallback_start), 2),
                    "profit_from_current": result["total_profit"],
                    "growth_percent": round(((result["projected_value"] / max(float(fallback_start), 1)) - 1) * 100, 1),
                    "trading_days": result["trading_days"],
                    "quarter_breakdown": result["quarter_breakdown"]
                })
            # Also add license_year_projections for fallback
            license_year_projections = []
            for years in [1, 2, 3, 5]:
                result = project_quarterly_growth(float(fallback_start), today, years * 250, holidays)
                license_year_projections.append({
                    "license_year": years,
                    "projected_value": result["projected_value"],
                    "total_profit": round(result["projected_value"] - float(fallback_start), 2),
                    "growth_percent": round(((result["projected_value"] / max(float(fallback_start), 1)) - 1) * 100, 1),
                    "trading_days": result["trading_days"],
                    "from_start_date": today.strftime("%Y-%m-%d"),
                })
            return {
                "current_value": round(float(fallback_value), 2),
                "starting_amount": float(fallback_start),
                "current_profit": round(float(fallback_value) - float(fallback_start), 2),
                "starting_daily_profit": round(truncate_lot_size(float(fallback_value)) * 15, 2),
                "trading_days_per_year": 250,
                "effective_start_date": today.strftime("%Y-%m-%d"),
                "projections": projections,
                "license_year_projections": license_year_projections,
                "fallback": True
            }
        except Exception as e2:
            logger.error(f"Even fallback projections failed: {e2}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Projection calculation error: {str(e)}")



@router.get("/daily-summary")
async def get_daily_profit_summary(user=Depends(deps.get_current_user)):
    """Get a consolidated daily profit summary for notification display."""
    db = deps.db
    user_id = user["id"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get today's trade logs
    today_logs = []
    async for log in db.trade_logs.find({"user_id": user_id, "date": today}, {"_id": 0}):
        today_logs.append(log)

    total_profit = sum(l.get("profit_usdt", 0) or 0 for l in today_logs)
    total_commission = sum(l.get("commission", 0) or 0 for l in today_logs)
    trade_count = len(today_logs)

    # Get account value
    summary = await get_user_financial_summary(db, user_id)
    account_value = summary.get("account_value", 0) if summary else 0

    # Get streak info
    streak = await db.habit_streaks.find_one({"user_id": user_id}, {"_id": 0})

    return {
        "date": today,
        "trade_count": trade_count,
        "total_profit": round(total_profit, 2),
        "total_commission": round(total_commission, 2),
        "net_profit": round(total_profit - total_commission, 2),
        "account_value": round(account_value, 2),
        "current_streak": streak.get("current_streak", 0) if streak else 0,
        "has_traded_today": trade_count > 0,
    }

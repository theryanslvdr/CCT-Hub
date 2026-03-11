"""Admin member management routes — extracted from admin_routes.py"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List

import deps
from helpers import (
    truncate_lot_size, calculate_extended_license_projections,
    send_push_notification,
)
from utils.calculations import _is_honorary, calculate_honorary_licensee_value
from services import websocket_manager

try:
    from services.rewards_sync_service import sync_user_to_rewards_platform
except ImportError:
    async def sync_user_to_rewards_platform(*a, **kw): pass

logger = logging.getLogger("server")

router = APIRouter(prefix="/admin", tags=["Admin Members"])


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


class SendEmailRequest(BaseModel):
    subject: str
    body: str
    template_type: Optional[str] = "admin_notification"


class NotifyRequest(BaseModel):
    type: str = "general"
    title: str
    message: str


# ─── Member List ───

@router.get("/members")
async def get_members(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    sort_account_value: Optional[str] = None,
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
        query["is_suspended"] = {"$ne": True}
        query["is_deactivated"] = {"$ne": True}

    query["license_type"] = {"$exists": False}

    total = await deps.db.users.count_documents(query)
    skip = (page - 1) * limit
    users_cursor = await deps.db.users.find(query, {"_id": 0, "password": 0}).skip(skip).limit(limit).to_list(limit)

    users = []
    requesting_user_role = user.get("role")
    can_see_account_value = requesting_user_role in ["super_admin", "master_admin"]

    for u in users_cursor:
        user_data = dict(u)
        if can_see_account_value:
            if u.get("license_type"):
                license = await deps.db.licenses.find_one({"user_id": u["id"], "is_active": True}, {"_id": 0})
                if license:
                    if _is_honorary(license.get("license_type")):
                        user_data["account_value"] = await calculate_honorary_licensee_value(deps.db, license)
                    else:
                        user_data["account_value"] = round(license.get("current_amount", license.get("starting_amount", 0)), 2)
                else:
                    user_data["account_value"] = round(u.get("account_value", 0), 2)
            else:
                deposits = await deps.db.deposits.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)
                trades = await deps.db.trade_logs.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)

                total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit" and d.get("type") != "withdrawal")
                total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
                total_profit = sum(t.get("actual_profit", 0) for t in trades)

                user_data["account_value"] = round(total_deposits - total_withdrawals + total_profit, 2)
        users.append(user_data)

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


# ─── Member Stats ───

@router.get("/members/stats/overview")
async def get_member_stats_overview(user: dict = Depends(deps.require_admin)):
    """Return stat card counts: active members, team leaders, suspended, in danger."""
    db = deps.db
    base_q = {"license_type": {"$exists": False}}

    active_count = await db.users.count_documents({
        **base_q,
        "is_suspended": {"$ne": True},
        "is_deactivated": {"$ne": True},
    })

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
        pipeline = [
            {"$match": {"referred_by": {"$in": list(all_codes)}}},
            {"$group": {"_id": "$referred_by"}},
        ]
        active_codes = set()
        async for doc in db.users.aggregate(pipeline):
            active_codes.add(doc["_id"])
        if active_codes:
            tl_query = {"$or": [
                {"referral_code": {"$in": list(active_codes)}},
                {"merin_referral_code": {"$in": list(active_codes)}},
            ]}
            team_leader_count = await db.users.count_documents(tl_query)

    suspended_count = await db.users.count_documents({
        **base_q,
        "is_suspended": True,
    })

    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    active_user_ids = []
    async for u in db.users.find(
        {**base_q, "is_suspended": {"$ne": True}, "is_deactivated": {"$ne": True}, "role": "member"},
        {"_id": 0, "id": 1}
    ):
        active_user_ids.append(u["id"])

    in_danger_count = 0
    if active_user_ids:
        users_with_recent = set()
        async for doc in db.trade_logs.aggregate([
            {"$match": {"user_id": {"$in": active_user_ids}, "created_at": {"$gte": cutoff}}},
            {"$group": {"_id": "$user_id"}},
        ]):
            users_with_recent.add(doc["_id"])

        users_with_any_trade = set()
        async for doc in db.trade_logs.aggregate([
            {"$match": {"user_id": {"$in": active_user_ids}}},
            {"$group": {"_id": "$user_id"}},
        ]):
            users_with_any_trade.add(doc["_id"])

        in_danger_count = len(users_with_any_trade - users_with_recent)

    return {
        "active_members": active_count,
        "team_leaders": team_leader_count,
        "suspended": suspended_count,
        "in_danger": in_danger_count,
    }


# ─── Member Details ───

@router.get("/members/{user_id}")
async def get_member_details(user_id: str, diagnostic: str = None, user: dict = Depends(deps.require_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    is_diagnostic = diagnostic is not None and diagnostic.lower() == "true"

    if is_diagnostic:
        all_trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        trades_sorted = sorted(all_trades, key=lambda x: x.get("created_at", ""))
        all_deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        deposits_sorted = sorted(all_deposits, key=lambda x: x.get("created_at", ""))
        reset_trades = await deps.db.reset_trades.find({"original_trade.user_id": user_id}, {"_id": 0}).to_list(100)

        total_deposits_amt = sum(d.get("amount", 0) for d in all_deposits if d.get("amount", 0) > 0)
        total_withdrawals = sum(abs(d.get("amount", 0)) for d in all_deposits if d.get("amount", 0) < 0)
        total_profit = sum(t.get("actual_profit", 0) for t in all_trades)
        total_commission = sum(t.get("commission", 0) for t in all_trades)
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
    trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(100)

    total_trades = len(trades)
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit")

    account_value = round(total_deposits + total_profit, 2)
    licensee_profit = None
    licensee_trades = 0
    performance_rate = 0

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
                try:
                    account_value = await calculate_honorary_licensee_value(deps.db, license)
                except Exception as e:
                    logger.error(f"Honorary calc failed in member_details for {user_id}: {e}", exc_info=True)
                    account_value = float(license.get("current_amount", starting_amount) or starting_amount)

            licensee_profit = round(float(account_value) - starting_amount, 2)

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
                        unique_dates.add(str(created)[:10])
                licensee_trades = len(unique_dates)

            if starting_amount > 0:
                performance_rate = round((float(account_value) / float(starting_amount)) * 100 - 100, 2)
    else:
        total_projected = sum(t.get("projected_profit", 0) for t in trades)
        if total_projected > 0:
            performance_rate = round((total_profit / total_projected) * 100, 2)

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
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    trade = await deps.db.trade_logs.find_one({"id": trade_id, "user_id": user_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found for this user")

    actual_profit = trade.get("actual_profit", 0)
    commission = trade.get("commission", 0)
    total_deduction = actual_profit + commission

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

    await deps.db.trade_logs.delete_one({"id": trade_id})
    await deps.db.deposits.delete_many({"trade_id": trade_id})

    if total_deduction > 0:
        deduction_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": -total_deduction,
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

    if data.allowed_dashboards is not None and user.get("role") in ["super_admin", "master_admin"]:
        update_data["allowed_dashboards"] = data.allowed_dashboards

    if user.get("role") == "master_admin":
        if data.role:
            update_data["role"] = data.role
        if data.email:
            update_data["email"] = data.email.lower()
        if data.trading_start_date:
            update_data["trading_start_date"] = data.trading_start_date
        if data.referred_by_user_id is not None:
            if data.referred_by_user_id == "":
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

    first_trade = await deps.db.trade_logs.find_one(
        {"user_id": user_id, "did_not_trade": {"$ne": True}},
        {"_id": 0, "created_at": 1},
        sort=[("created_at", 1)]
    )

    if not first_trade:
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

    new_hash = deps.hash_password(data.temp_password)
    await deps.db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password": new_hash,
            "must_change_password": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    return {"message": "Temporary password set. User will be prompted to change on next login."}


@router.get("/members/{user_id}/simulate")
async def simulate_member_view(user_id: str, user: dict = Depends(deps.require_master_admin)):
    """Master Admin only: Get all data to simulate viewing as a specific member"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    deposits = await deps.db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    trades = await deps.db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    debts = await deps.db.debts.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    goals = await deps.db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(100)

    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit" and d.get("type") != "withdrawal")
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    account_value = round(total_deposits - total_withdrawals + total_profit, 2)

    license = await deps.db.licenses.find_one({"user_id": user_id, "is_active": True}, {"_id": 0})
    if license:
        if _is_honorary(license.get("license_type")):
            account_value = await calculate_honorary_licensee_value(deps.db, license)
        else:
            account_value = round(license.get("current_amount", license.get("starting_amount", 0)), 2)
        total_deposits = round(license.get("starting_amount", 0), 2)
        total_profit = round(account_value - total_deposits, 2)

    lot_size = truncate_lot_size(account_value) if account_value > 0 else 0

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


# ─── Member Communication ───

@router.post("/members/{user_id}/send-email")
async def send_email_to_member(user_id: str, data: SendEmailRequest, user: dict = Depends(deps.require_admin)):
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

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


@router.post("/members/{user_id}/notify")
async def notify_member(user_id: str, data: NotifyRequest, user: dict = Depends(deps.require_admin)):
    """Send an in-app notification to a member"""
    member = await deps.db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

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

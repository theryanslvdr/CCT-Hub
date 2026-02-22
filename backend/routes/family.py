"""Family Account routes for Honorary FA Licensees"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
import logging

import deps
from deps import get_current_user, require_admin

logger = logging.getLogger("server")

router = APIRouter(prefix="/family", tags=["Family Accounts"])
admin_family_router = APIRouter(prefix="/admin/family", tags=["Admin Family Accounts"])


# ==================== MODELS ====================

class FamilyMemberCreate(BaseModel):
    name: str
    relationship: str  # spouse, child, sibling, parent, other
    email: Optional[str] = None
    starting_amount: float
    deposit_date: Optional[str] = None  # YYYY-MM-DD - trading starts next trading day after this
    effective_start_date: Optional[str] = None  # YYYY-MM-DD (legacy, overridden by deposit_date)

class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    email: Optional[str] = None

class FamilyWithdrawalRequest(BaseModel):
    amount: float
    notes: Optional[str] = None


# ==================== HELPER ====================

def get_next_trading_day(date_str: str) -> str:
    """Given a deposit date (YYYY-MM-DD), return the next trading day (weekday, skipping weekends)."""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str
    # Move to the next day first
    dt += timedelta(days=1)
    # Skip weekends
    while dt.weekday() >= 5:  # 5=Saturday, 6=Sunday
        dt += timedelta(days=1)
    return dt.strftime("%Y-%m-%d")


async def calculate_family_member_value(db, member_doc: dict) -> float:
    """Calculate account value for a family member using the same logic as honorary licensees."""
    from utils.calculations import calculate_honorary_licensee_value
    # Build a virtual license-like dict for the calculation
    virtual_license = {
        "id": member_doc.get("id"),
        "starting_amount": member_doc.get("starting_amount", 0),
        "effective_start_date": member_doc.get("effective_start_date"),
        "start_date": member_doc.get("effective_start_date"),
    }
    return await calculate_honorary_licensee_value(db, virtual_license)


async def get_family_member_projections(db, member_doc: dict) -> list:
    """Generate daily projections for a family member (same as honorary licensee)."""
    from server import get_quarter

    starting_amount = member_doc.get("starting_amount", 0)
    effective_start = member_doc.get("effective_start_date")
    if not effective_start:
        return []

    try:
        start_dt = datetime.strptime(str(effective_start)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return []

    # Get master admin trade logs (exclude did_not_trade)
    master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1})
    if not master_admin:
        return []

    master_trades = await db.trade_logs.find(
        {"user_id": master_admin["id"], "did_not_trade": {"$ne": True}},
        {"_id": 0, "created_at": 1, "trade_date": 1}
    ).to_list(10000)

    traded_dates = set()
    for trade in master_trades:
        trade_date = trade.get("trade_date") or str(trade.get("created_at", ""))[:10]
        if trade_date:
            traded_dates.add(trade_date)

    # Get trade overrides for the parent license
    overrides = {}
    parent_license_id = member_doc.get("parent_license_id")
    if parent_license_id:
        async for override in db.licensee_trade_overrides.find({"license_id": parent_license_id}, {"_id": 0}):
            overrides[override["date"]] = override

    # Quarterly compounding projection
    projections = []
    current_balance = starting_amount
    current_quarter = get_quarter(start_dt)
    current_year = start_dt.year
    quarter_lot_size = round(current_balance / 980, 2)
    quarter_daily_profit = round(quarter_lot_size * 15, 2)

    current_date = start_dt
    end_date = datetime.now(timezone.utc) + timedelta(days=365)

    while current_date <= end_date:
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        date_str = current_date.strftime("%Y-%m-%d")

        new_quarter = get_quarter(current_date)
        new_year = current_date.year
        if new_year != current_year or new_quarter != current_quarter:
            quarter_lot_size = round(current_balance / 980, 2)
            quarter_daily_profit = round(quarter_lot_size * 15, 2)
            current_quarter = new_quarter
            current_year = new_year

        override = overrides.get(date_str)
        if override:
            manager_traded = override.get("traded", False)
        elif date_str in traded_dates:
            manager_traded = True
        else:
            manager_traded = False

        projections.append({
            "date": date_str,
            "start_value": current_balance,
            "account_value": current_balance + quarter_daily_profit if manager_traded else current_balance,
            "lot_size": quarter_lot_size,
            "daily_profit": quarter_daily_profit,
            "manager_traded": manager_traded,
            "has_override": override is not None
        })

        if manager_traded and current_date <= datetime.now(timezone.utc):
            current_balance += quarter_daily_profit

        current_date += timedelta(days=1)

    return projections


# ==================== HELPER: Robust license check ====================

async def verify_honorary_fa_license(db, user: dict) -> dict:
    """Verify user has an active honorary_fa license by checking the licenses collection directly.
    Returns the license document if valid, raises HTTPException otherwise."""
    # First check user document (fast path)
    if user.get("license_type") == "honorary_fa":
        license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
        if license and license.get("license_type") == "honorary_fa":
            return license
    
    # Fallback: check licenses collection directly (handles missing user.license_type)
    license = await db.licenses.find_one(
        {"user_id": user["id"], "is_active": True, "license_type": "honorary_fa"},
        {"_id": 0}
    )
    if not license:
        raise HTTPException(status_code=403, detail="Only Honorary FA licensees can access family accounts")
    return license


# ==================== LICENSEE ENDPOINTS ====================

@router.get("/members")
async def get_family_members(user: dict = Depends(get_current_user)):
    """Get all family members for the current licensee."""
    db = deps.db
    await verify_honorary_fa_license(db, user)

    members = await db.family_members.find(
        {"parent_user_id": user["id"], "is_active": True}, {"_id": 0}
    ).to_list(100)

    # Calculate account values for each member
    enriched = []
    for m in members:
        account_value = await calculate_family_member_value(db, m)
        profit = round(account_value - m.get("starting_amount", 0), 2)
        enriched.append({
            **m,
            "account_value": account_value,
            "profit": profit
        })

    return {"family_members": enriched}


@router.post("/members")
async def add_family_member(data: FamilyMemberCreate, user: dict = Depends(get_current_user)):
    """Add a family member to the licensee's account."""
    db = deps.db
    license = await verify_honorary_fa_license(db, user)

    # Check family member limit (max 5)
    existing_count = await db.family_members.count_documents(
        {"parent_user_id": user["id"], "is_active": True}
    )
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 family members allowed per account")

    # Get parent license (already verified by verify_honorary_fa_license)
    if not license:
        license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=400, detail="No active license found")

    # Calculate effective_start_date from deposit_date (next trading day after deposit)
    if data.deposit_date:
        effective_start = get_next_trading_day(data.deposit_date)
        deposit_date = data.deposit_date
    elif data.effective_start_date:
        effective_start = data.effective_start_date
        deposit_date = data.effective_start_date
    else:
        deposit_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        effective_start = get_next_trading_day(deposit_date)

    member_id = str(uuid.uuid4())
    member = {
        "id": member_id,
        "parent_user_id": user["id"],
        "parent_license_id": license["id"],
        "name": data.name,
        "relationship": data.relationship,
        "email": data.email,
        "starting_amount": data.starting_amount,
        "deposit_date": deposit_date,
        "effective_start_date": effective_start,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.family_members.insert_one(member)
    member.pop("_id", None)

    return {"message": "Family member added", "member": member}


@router.put("/members/{member_id}")
async def update_family_member(member_id: str, data: FamilyMemberUpdate, user: dict = Depends(get_current_user)):
    """Update a family member's info."""
    db = deps.db
    await verify_honorary_fa_license(db, user)

    member = await db.family_members.find_one(
        {"id": member_id, "parent_user_id": user["id"], "is_active": True}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.relationship is not None:
        updates["relationship"] = data.relationship
    if data.email is not None:
        updates["email"] = data.email

    if updates:
        await db.family_members.update_one({"id": member_id}, {"$set": updates})

    return {"message": "Family member updated"}


@router.delete("/members/{member_id}")
async def remove_family_member(member_id: str, user: dict = Depends(get_current_user)):
    """Deactivate a family member."""
    db = deps.db
    await verify_honorary_fa_license(db, user)

    member = await db.family_members.find_one(
        {"id": member_id, "parent_user_id": user["id"], "is_active": True}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    await db.family_members.update_one({"id": member_id}, {"$set": {"is_active": False}})
    return {"message": "Family member removed"}


@router.get("/members/{member_id}/projections")
async def get_family_member_projections_endpoint(member_id: str, user: dict = Depends(get_current_user)):
    """Get daily projections for a specific family member."""
    db = deps.db
    await verify_honorary_fa_license(db, user)

    member = await db.family_members.find_one(
        {"id": member_id, "parent_user_id": user["id"], "is_active": True}, {"_id": 0}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    projections = await get_family_member_projections(db, member)
    account_value = await calculate_family_member_value(db, member)

    return {
        "member": member,
        "projections": projections,
        "starting_amount": member.get("starting_amount", 0),
        "current_balance": account_value
    }


# ==================== WITHDRAWAL FLOW ====================

@router.post("/members/{member_id}/withdraw")
async def request_family_withdrawal(member_id: str, data: FamilyWithdrawalRequest, user: dict = Depends(get_current_user)):
    """Family member withdrawal request (requires parent then admin approval)."""
    db = deps.db
    await verify_honorary_fa_license(db, user)

    member = await db.family_members.find_one(
        {"id": member_id, "parent_user_id": user["id"], "is_active": True}, {"_id": 0}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    account_value = await calculate_family_member_value(db, member)
    if data.amount > account_value:
        raise HTTPException(status_code=400, detail="Withdrawal amount exceeds account value")

    withdrawal_id = str(uuid.uuid4())
    withdrawal = {
        "id": withdrawal_id,
        "family_member_id": member_id,
        "family_member_name": member["name"],
        "parent_user_id": user["id"],
        "parent_user_name": user["full_name"],
        "amount": data.amount,
        "notes": data.notes,
        "status": "pending_parent_approval",
        "account_value_at_request": account_value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parent_approved_at": None,
        "admin_approved_at": None,
        "rejected_at": None,
        "rejection_reason": None
    }
    await db.family_withdrawals.insert_one(withdrawal)
    withdrawal.pop("_id", None)

    # Send notification to parent licensee
    from helpers import send_push_notification
    try:
        await send_push_notification(
            db, user["id"],
            f"Withdrawal Request: {member['name']}",
            f"{member['name']} requested a ${data.amount:.2f} withdrawal. Please review."
        )
    except Exception as e:
        logger.warning(f"Failed to send family withdrawal notification: {e}")

    return {"message": "Withdrawal request submitted", "withdrawal": withdrawal}


@router.get("/withdrawals")
async def get_family_withdrawals(user: dict = Depends(get_current_user)):
    """Get all family withdrawal requests for the licensee."""
    db = deps.db

    if user.get("license_type") != "honorary_fa":
        raise HTTPException(status_code=403, detail="Only Honorary FA licensees can view family withdrawals")

    withdrawals = await db.family_withdrawals.find(
        {"parent_user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {"withdrawals": withdrawals}


@router.put("/withdrawals/{withdrawal_id}/approve")
async def parent_approve_withdrawal(withdrawal_id: str, user: dict = Depends(get_current_user)):
    """Parent licensee approves a family member's withdrawal request."""
    db = deps.db

    if user.get("license_type") != "honorary_fa":
        raise HTTPException(status_code=403, detail="Only Honorary FA licensees can approve withdrawals")

    withdrawal = await db.family_withdrawals.find_one(
        {"id": withdrawal_id, "parent_user_id": user["id"]}, {"_id": 0}
    )
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")

    if withdrawal["status"] != "pending_parent_approval":
        raise HTTPException(status_code=400, detail=f"Cannot approve: status is '{withdrawal['status']}'")

    await db.family_withdrawals.update_one(
        {"id": withdrawal_id},
        {"$set": {
            "status": "pending_admin_approval",
            "parent_approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    # Notify admins
    from helpers import send_push_to_admins
    try:
        await send_push_to_admins(
            db,
            f"Family Withdrawal Approved by {user['full_name']}",
            f"{withdrawal['family_member_name']} withdrawal of ${withdrawal['amount']:.2f} needs admin approval."
        )
    except Exception as e:
        logger.warning(f"Failed to send admin notification: {e}")

    return {"message": "Withdrawal approved. Sent to Master Admin for processing."}


@router.put("/withdrawals/{withdrawal_id}/reject")
async def parent_reject_withdrawal(withdrawal_id: str, reason: str = "", user: dict = Depends(get_current_user)):
    """Parent licensee rejects a family member's withdrawal request."""
    db = deps.db

    if user.get("license_type") != "honorary_fa":
        raise HTTPException(status_code=403, detail="Only Honorary FA licensees can reject withdrawals")

    withdrawal = await db.family_withdrawals.find_one(
        {"id": withdrawal_id, "parent_user_id": user["id"]}, {"_id": 0}
    )
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")

    if withdrawal["status"] != "pending_parent_approval":
        raise HTTPException(status_code=400, detail=f"Cannot reject: status is '{withdrawal['status']}'")

    await db.family_withdrawals.update_one(
        {"id": withdrawal_id},
        {"$set": {
            "status": "rejected_by_parent",
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": reason or "Rejected by parent licensee"
        }}
    )

    return {"message": "Withdrawal request rejected."}


# ==================== ADMIN ENDPOINTS ====================

@admin_family_router.get("/withdrawals")
async def admin_get_family_withdrawals(user: dict = Depends(require_admin)):
    """Get all pending family withdrawal requests for admin approval."""
    db = deps.db

    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can manage family withdrawals")

    withdrawals = await db.family_withdrawals.find(
        {"status": "pending_admin_approval"}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    return {"withdrawals": withdrawals}


@admin_family_router.put("/withdrawals/{withdrawal_id}/approve")
async def admin_approve_family_withdrawal(withdrawal_id: str, user: dict = Depends(require_admin)):
    """Master Admin approves a family withdrawal (final step)."""
    db = deps.db

    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can approve family withdrawals")

    withdrawal = await db.family_withdrawals.find_one({"id": withdrawal_id}, {"_id": 0})
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")

    if withdrawal["status"] != "pending_admin_approval":
        raise HTTPException(status_code=400, detail=f"Cannot approve: status is '{withdrawal['status']}'")

    await db.family_withdrawals.update_one(
        {"id": withdrawal_id},
        {"$set": {
            "status": "approved",
            "admin_approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    # Notify parent and family member
    from helpers import send_push_notification
    try:
        await send_push_notification(
            db, withdrawal["parent_user_id"],
            "Withdrawal Approved",
            f"{withdrawal['family_member_name']}'s withdrawal of ${withdrawal['amount']:.2f} has been approved by admin."
        )
    except Exception as e:
        logger.warning(f"Failed to send approval notification: {e}")

    return {"message": "Family withdrawal approved and processed."}


@admin_family_router.put("/withdrawals/{withdrawal_id}/reject")
async def admin_reject_family_withdrawal(withdrawal_id: str, reason: str = "", user: dict = Depends(require_admin)):
    """Master Admin rejects a family withdrawal."""
    db = deps.db

    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can reject family withdrawals")

    withdrawal = await db.family_withdrawals.find_one({"id": withdrawal_id}, {"_id": 0})
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")

    if withdrawal["status"] != "pending_admin_approval":
        raise HTTPException(status_code=400, detail=f"Cannot reject: status is '{withdrawal['status']}'")

    await db.family_withdrawals.update_one(
        {"id": withdrawal_id},
        {"$set": {
            "status": "rejected_by_admin",
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": reason or "Rejected by Master Admin"
        }}
    )

    # Notify parent
    from helpers import send_push_notification
    try:
        await send_push_notification(
            db, withdrawal["parent_user_id"],
            "Withdrawal Rejected",
            f"{withdrawal['family_member_name']}'s withdrawal was rejected: {reason or 'No reason given'}"
        )
    except Exception as e:
        logger.warning(f"Failed to send rejection notification: {e}")

    return {"message": "Family withdrawal rejected."}


@admin_family_router.get("/members/{user_id}")
async def admin_get_family_members(user_id: str, user: dict = Depends(require_admin)):
    """Admin view: Get family members for a specific licensee."""
    db = deps.db

    members = await db.family_members.find(
        {"parent_user_id": user_id, "is_active": True}, {"_id": 0}
    ).to_list(100)

    enriched = []
    for m in members:
        account_value = await calculate_family_member_value(db, m)
        profit = round(account_value - m.get("starting_amount", 0), 2)
        enriched.append({**m, "account_value": account_value, "profit": profit})

    return {"family_members": enriched}


@admin_family_router.post("/members/{user_id}")
async def admin_add_family_member(user_id: str, data: FamilyMemberCreate, user: dict = Depends(require_admin)):
    """Admin can also add family members on behalf of a licensee."""
    db = deps.db

    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can add family members for users")

    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target or target.get("license_type") != "honorary_fa":
        raise HTTPException(status_code=400, detail="Target user must be an Honorary FA licensee")

    license = await db.licenses.find_one({"user_id": user_id, "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=400, detail="No active license found")

    existing_count = await db.family_members.count_documents(
        {"parent_user_id": user_id, "is_active": True}
    )
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 family members allowed per account")

    # Calculate effective_start_date from deposit_date (next trading day after deposit)
    if data.deposit_date:
        effective_start = get_next_trading_day(data.deposit_date)
        deposit_date = data.deposit_date
    elif data.effective_start_date:
        effective_start = data.effective_start_date
        deposit_date = data.effective_start_date
    else:
        deposit_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        effective_start = get_next_trading_day(deposit_date)

    member_id = str(uuid.uuid4())
    member = {
        "id": member_id,
        "parent_user_id": user_id,
        "parent_license_id": license["id"],
        "name": data.name,
        "relationship": data.relationship,
        "email": data.email,
        "starting_amount": data.starting_amount,
        "deposit_date": deposit_date,
        "effective_start_date": effective_start,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.family_members.insert_one(member)
    member.pop("_id", None)

    return {"message": "Family member added by admin", "member": member}


@admin_family_router.get("/members/{user_id}/{member_id}/projections")
async def admin_get_family_member_projections(user_id: str, member_id: str, user: dict = Depends(require_admin)):
    """Admin view: Get projections for a specific family member."""
    db = deps.db

    member = await db.family_members.find_one(
        {"id": member_id, "parent_user_id": user_id, "is_active": True}, {"_id": 0}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    projections = await get_family_member_projections(db, member)
    account_value = await calculate_family_member_value(db, member)

    return {
        "member": member,
        "projections": projections,
        "starting_amount": member.get("starting_amount", 0),
        "current_balance": account_value
    }


class FamilyMemberResetBalance(BaseModel):
    starting_amount: Optional[float] = None
    effective_start_date: Optional[str] = None


@admin_family_router.put("/members/{user_id}/{member_id}/reset")
async def admin_reset_family_member(user_id: str, member_id: str, data: FamilyMemberResetBalance, user: dict = Depends(require_admin)):
    """Admin resets a family member's starting balance and/or start date."""
    db = deps.db

    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can reset family member balances")

    member = await db.family_members.find_one(
        {"id": member_id, "parent_user_id": user_id, "is_active": True}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    updates = {}
    if data.starting_amount is not None:
        if data.starting_amount < 0:
            raise HTTPException(status_code=400, detail="Starting amount cannot be negative")
        updates["starting_amount"] = data.starting_amount
    if data.effective_start_date is not None:
        try:
            datetime.strptime(data.effective_start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        updates["effective_start_date"] = data.effective_start_date

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.family_members.update_one({"id": member_id}, {"$set": updates})

    return {"message": "Family member updated", "updates": updates}


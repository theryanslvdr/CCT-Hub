"""Admin cleanup, registration, and review routes — extracted from admin_routes.py"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends

import deps

router = APIRouter(prefix="/admin", tags=["Admin Cleanup"])


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

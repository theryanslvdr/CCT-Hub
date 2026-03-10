"""Referral System routes - referral code management, tree visualization, habit rewards."""
import uuid
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

import deps
from deps import get_current_user, require_admin, require_master_admin

logger = logging.getLogger("server")

router = APIRouter(prefix="/referrals", tags=["Referrals"])

REWARDS_API_BASE = "https://trade-rewards-1.emergent.host/api/external"
REWARDS_API_KEY = deps.__dict__.get("REWARDS_API_KEY", None)


def _rewards_headers():
    import os
    key = os.environ.get("REWARDS_PLATFORM_API_KEY", "cct_izJiIkSgzqQGiqSr_VZn1icO5Fw7cjMj-zw4OW4LqW4")
    return {"X-API-Key": key, "Content-Type": "application/json"}


# ─── Request Models ───

class SetReferralCodeRequest(BaseModel):
    referral_code: str

class SetInviterRequest(BaseModel):
    inviter_id: str


class AdminSetReferralRequest(BaseModel):
    user_id: str
    referral_code: str


# ─── User Endpoints ───

@router.get("/my-code")
async def get_my_referral_code(user: dict = Depends(get_current_user)):
    """Get the current user's referral code and referral stats."""
    db = deps.db
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "referral_code": 1, "referred_by": 1})

    referral_code = (user_doc or {}).get("referral_code")
    referred_by = (user_doc or {}).get("referred_by")

    # Count direct referrals
    direct_referrals = 0
    if referral_code:
        direct_referrals = await db.users.count_documents({"referred_by": referral_code})

    return {
        "referral_code": referral_code,
        "referred_by": referred_by,
        "direct_referrals": direct_referrals,
        "onboarding_complete": referral_code is not None,
    }


@router.post("/set-code")
async def set_referral_code(data: SetReferralCodeRequest, user: dict = Depends(get_current_user)):
    """Set the current user's Merin referral code. This is a mandatory onboarding step."""
    db = deps.db
    code = data.referral_code.strip()

    if not code or len(code) < 3:
        raise HTTPException(status_code=400, detail="Referral code must be at least 3 characters.")

    # Check if user already has a code set
    existing = await db.users.find_one({"id": user["id"]}, {"_id": 0, "referral_code": 1})
    if existing and existing.get("referral_code"):
        raise HTTPException(status_code=400, detail="Referral code already set. Contact admin to change it.")

    # Check uniqueness within the hub
    duplicate = await db.users.find_one({"referral_code": code, "id": {"$ne": user["id"]}}, {"_id": 0, "id": 1})
    if duplicate:
        raise HTTPException(status_code=400, detail="This referral code is already in use by another member.")

    # Validate against the external rewards platform (best effort)
    validation_result = await _validate_code_external(code)

    # Store the referral code on the user
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "referral_code": code,
            "referral_code_set_at": datetime.now(timezone.utc).isoformat(),
            "referral_validation": validation_result,
        }}
    )

    # Log the referral onboarding event
    await db.referral_events.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "event": "code_set",
        "referral_code": code,
        "validation": validation_result,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "success": True,
        "referral_code": code,
        "validation": validation_result,
        "message": "Referral code set successfully!",
    }


@router.post("/set-referred-by")
async def set_referred_by(data: SetReferralCodeRequest, user: dict = Depends(get_current_user)):
    """Set who referred this user (the inviter's referral code)."""
    db = deps.db
    code = data.referral_code.strip()

    if not code:
        raise HTTPException(status_code=400, detail="Referral code is required.")

    # Check if already set
    existing = await db.users.find_one({"id": user["id"]}, {"_id": 0, "referred_by": 1})
    if existing and existing.get("referred_by"):
        raise HTTPException(status_code=400, detail="Referred-by already set.")

    # Verify the inviter exists in the hub
    inviter = await db.users.find_one({"referral_code": code}, {"_id": 0, "id": 1, "full_name": 1})
    if not inviter:
        raise HTTPException(status_code=404, detail="No member found with this referral code.")

    # Can't refer yourself
    if inviter["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot refer yourself.")

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "referred_by": code,
            "referred_by_user_id": inviter["id"],
            "referred_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    # Log referral event
    await db.referral_events.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "event": "referred_by_set",
        "referral_code": code,
        "inviter_id": inviter["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "success": True,
        "referred_by": code,
        "inviter_name": inviter.get("full_name", "Unknown"),
    }


@router.post("/set-inviter")
async def set_inviter(data: SetInviterRequest, user: dict = Depends(get_current_user)):
    """Set or update who invited this user by inviter's user ID (from member lookup)."""
    db = deps.db

    # Find the inviter by user ID
    inviter = await db.users.find_one(
        {"id": data.inviter_id},
        {"_id": 0, "id": 1, "full_name": 1, "referral_code": 1, "merin_referral_code": 1},
    )
    if not inviter:
        raise HTTPException(status_code=404, detail="Inviter not found.")

    if inviter["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot invite yourself.")

    # Use referral_code if available, else merin_referral_code, else the user ID as fallback
    code = inviter.get("referral_code") or inviter.get("merin_referral_code") or inviter["id"]

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "referred_by": code,
            "referred_by_user_id": inviter["id"],
            "referred_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    await db.referral_events.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "event": "inviter_set_via_lookup",
        "referral_code": code,
        "inviter_id": inviter["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "success": True,
        "referred_by": code,
        "inviter_name": inviter.get("full_name", "Unknown"),
    }


@router.get("/check-onboarding")
async def check_onboarding_status(user: dict = Depends(get_current_user)):
    """Check if the user has completed referral onboarding."""
    db = deps.db
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "referral_code": 1, "role": 1})

    role = (user_doc or {}).get("role", user.get("role", "member"))
    has_code = bool((user_doc or {}).get("referral_code"))

    # Admins don't need to complete onboarding
    admin_roles = {"basic_admin", "admin", "super_admin", "master_admin"}
    needs_onboarding = role not in admin_roles and not has_code

    return {
        "needs_onboarding": needs_onboarding,
        "has_referral_code": has_code,
        "role": role,
    }


# ─── Admin Endpoints ───

@router.get("/admin/tree")
async def get_referral_tree(user: dict = Depends(require_admin)):
    """Get the full referral tree for admin visualization."""
    db = deps.db

    # Fetch all users with referral data
    users = await db.users.find(
        {},
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "role": 1,
         "referral_code": 1, "referred_by": 1, "created_at": 1}
    ).to_list(5000)

    # Build tree structure
    # Root nodes: users who were not referred by anyone
    # Children: users whose referred_by matches parent's referral_code
    code_to_user = {}
    for u in users:
        if u.get("referral_code"):
            code_to_user[u["referral_code"]] = u

    # Build adjacency list (parent code -> list of children)
    children_map = {}
    root_users = []
    for u in users:
        referred_by = u.get("referred_by")
        if referred_by and referred_by in code_to_user:
            children_map.setdefault(referred_by, []).append(u)
        else:
            root_users.append(u)

    def build_node(u):
        code = u.get("referral_code", "")
        children = children_map.get(code, [])
        return {
            "id": u["id"],
            "name": u.get("full_name", u.get("email", "Unknown")),
            "email": u.get("email", ""),
            "role": u.get("role", "member"),
            "referral_code": code,
            "referred_by": u.get("referred_by"),
            "created_at": u.get("created_at", ""),
            "direct_referrals": len(children),
            "children": [build_node(c) for c in children],
        }

    tree = [build_node(u) for u in root_users]

    # Stats
    total_users = len(users)
    users_with_code = sum(1 for u in users if u.get("referral_code"))
    users_referred = sum(1 for u in users if u.get("referred_by"))

    return {
        "tree": tree,
        "stats": {
            "total_users": total_users,
            "users_with_code": users_with_code,
            "users_referred": users_referred,
            "onboarding_completion_rate": round(users_with_code / total_users * 100, 1) if total_users > 0 else 0,
        },
    }


@router.get("/admin/flat-list")
async def get_referral_flat_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    user: dict = Depends(require_admin),
):
    """Get a flat, paginated list of all referral relationships for table view."""
    db = deps.db

    query = {}
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"referral_code": {"$regex": search, "$options": "i"}},
        ]

    total = await db.users.count_documents(query)
    users = await db.users.find(
        query,
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "role": 1,
         "referral_code": 1, "referred_by": 1, "created_at": 1}
    ).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size).to_list(page_size)

    # Enrich with referral count
    for u in users:
        code = u.get("referral_code")
        if code:
            u["referral_count"] = await db.users.count_documents({"referred_by": code})
        else:
            u["referral_count"] = 0

    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/admin/set-code")
async def admin_set_referral_code(data: AdminSetReferralRequest, user: dict = Depends(require_admin)):
    """Admin override: set or change a user's referral code."""
    db = deps.db
    target = await db.users.find_one({"id": data.user_id}, {"_id": 0, "id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    code = data.referral_code.strip()
    if not code or len(code) < 3:
        raise HTTPException(status_code=400, detail="Code must be at least 3 characters.")

    # Check uniqueness
    dup = await db.users.find_one({"referral_code": code, "id": {"$ne": data.user_id}}, {"_id": 0, "id": 1})
    if dup:
        raise HTTPException(status_code=400, detail="Code already in use by another member.")

    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {
            "referral_code": code,
            "referral_code_set_at": datetime.now(timezone.utc).isoformat(),
            "referral_code_set_by": user["id"],
        }}
    )

    return {"success": True, "message": f"Referral code set to '{code}'"}


# ─── Habit Reward Points ───

@router.post("/habit-reward")
async def award_habit_reward(user: dict = Depends(get_current_user)):
    """Award points for completing daily habits. Points scale with streak."""
    from utils.rewards_engine import award_points
    db = deps.db

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if already awarded today
    existing = await db.rewards_point_logs.find_one({
        "user_id": user["id"],
        "source": "habit_completion",
        "metadata.date": today,
    })
    if existing:
        return {"success": False, "message": "Already awarded today", "points": 0}

    # Get streak to calculate points
    from routes.habits import _calc_habit_streak
    streak_data = await _calc_habit_streak(user["id"])
    streak = streak_data.get("current_streak", 0)

    # Scaling rewards: minimal at start, significant over time
    # Day 1-7: 5 pts/day
    # Day 8-21: 10 pts/day
    # Day 22-45: 20 pts/day
    # Day 46+: 35 pts/day
    if streak >= 46:
        points = 35
    elif streak >= 22:
        points = 20
    elif streak >= 8:
        points = 10
    else:
        points = 5

    await award_points(db, user["id"], points, "habit_completion", {
        "date": today,
        "streak": streak,
        "streak_tier": "thought_leader" if streak >= 46 else "content_creator" if streak >= 22 else "active_engager" if streak >= 8 else "getting_started",
    })

    return {
        "success": True,
        "points": points,
        "streak": streak,
        "message": f"+{points} reward points for day {streak} streak!",
    }


# ─── Internal Helpers ───

async def _award_habit_points(user_id: str) -> dict:
    """Internal helper called by habits routes to award streak-based points.
    Returns reward info or None if already awarded today."""
    from utils.rewards_engine import award_points
    db = deps.db

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check if already awarded today
    existing = await db.rewards_point_logs.find_one({
        "user_id": user_id,
        "source": "habit_completion",
        "metadata.date": today,
    })
    if existing:
        return None

    # Get streak to calculate points
    from routes.habits import _calc_habit_streak
    streak_data = await _calc_habit_streak(user_id)
    streak = streak_data.get("current_streak", 0)

    # Scaling rewards: minimal at start, significant over time
    # Day 1-7: 5 pts/day
    # Day 8-21: 10 pts/day
    # Day 22-45: 20 pts/day
    # Day 46-59: 35 pts/day
    # Day 60-79: 50 pts/day
    # Day 80-99: 70 pts/day
    # Day 100+: 100 pts/day
    if streak >= 100:
        points = 100
    elif streak >= 80:
        points = 70
    elif streak >= 60:
        points = 50
    elif streak >= 46:
        points = 35
    elif streak >= 22:
        points = 20
    elif streak >= 8:
        points = 10
    else:
        points = 5

    await award_points(db, user_id, points, "habit_completion", {
        "date": today,
        "streak": streak,
        "streak_tier": (
            "community_leader" if streak >= 100 else
            "growth_hacker" if streak >= 80 else
            "brand_ambassador" if streak >= 60 else
            "thought_leader" if streak >= 46 else
            "content_creator" if streak >= 22 else
            "active_engager" if streak >= 8 else
            "getting_started"
        ),
    })

    return {"points": points, "streak": streak}


async def _validate_code_external(code: str) -> dict:
    """Try to validate a referral code against the external rewards platform."""
    result = {"validated": False, "source": "none", "details": None}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try the rewards platform lookup
            resp = await client.get(
                f"{REWARDS_API_BASE}/members",
                headers=_rewards_headers(),
                params={"search": code, "limit": 1},
            )
            if resp.status_code == 200:
                data = resp.json()
                members = data if isinstance(data, list) else data.get("members", [])
                if members:
                    result["validated"] = True
                    result["source"] = "rewards_platform"
                    result["details"] = "Code found on rewards platform"
                else:
                    result["source"] = "rewards_platform"
                    result["details"] = "Code not found on rewards platform (new code)"
            else:
                result["source"] = "rewards_platform_error"
                result["details"] = f"Platform returned {resp.status_code}"
    except Exception as e:
        result["source"] = "error"
        result["details"] = str(e)[:100]
        logger.warning(f"External referral validation failed: {e}")

    return result



# ─── Referral Tracking & Leaderboard ───

REFERRAL_MILESTONES = [
    {"threshold": 1, "title": "First Referral", "points": 150, "icon": "user-plus"},
    {"threshold": 3, "title": "Referral Champion", "points": 100, "icon": "users"},
    {"threshold": 5, "title": "Referral Pro", "points": 200, "icon": "users"},
    {"threshold": 10, "title": "Referral Legend", "points": 500, "icon": "trophy"},
    {"threshold": 25, "title": "Network Builder", "points": 1000, "icon": "crown"},
    {"threshold": 50, "title": "Community Architect", "points": 2500, "icon": "crown"},
]


@router.get("/tracking")
async def get_referral_tracking(user: dict = Depends(get_current_user)):
    """Get referral tracking data for the current user."""
    db = deps.db

    user_doc = await db.users.find_one(
        {"id": user["id"]},
        {"_id": 0, "referral_code": 1, "merin_referral_code": 1, "full_name": 1}
    )
    referral_code = user_doc.get("referral_code") if user_doc else None
    merin_code = user_doc.get("merin_referral_code") or referral_code

    # Count referrals
    direct_count = 0
    referrals = []
    if referral_code:
        cursor = db.users.find(
            {"referred_by": referral_code},
            {"_id": 0, "id": 1, "full_name": 1, "created_at": 1, "onboarding_completed": 1}
        ).sort("created_at", -1)
        referrals = await cursor.to_list(500)
        direct_count = len(referrals)

    # Milestone progress
    milestones = []
    for m in REFERRAL_MILESTONES:
        milestones.append({
            **m,
            "achieved": direct_count >= m["threshold"],
            "progress": min(direct_count / m["threshold"], 1.0),
        })

    # Next milestone
    next_milestone = None
    for m in milestones:
        if not m["achieved"]:
            next_milestone = m
            break

    # Invite link (Merin registration)
    invite_link = None
    if merin_code:
        invite_link = f"https://www.meringlobaltrading.com/#/pages/login/regist?code={merin_code}&lang=en_US"

    # Onboarding invite link (for sharing with new members)
    onboarding_invite_link = None
    if merin_code:
        onboarding_invite_link = f"https://crosscur.rent/onboarding?merin_code={merin_code}"

    return {
        "referral_code": referral_code,
        "merin_code": merin_code,
        "direct_count": direct_count,
        "referred_by": user_doc.get("referred_by") if user_doc else None,
        "referred_by_user_id": user_doc.get("referred_by_user_id") if user_doc else None,
        "referrals": [
            {
                "name": r.get("full_name", "Unknown"),
                "joined": r.get("created_at", ""),
                "onboarded": r.get("onboarding_completed", False),
            }
            for r in referrals[:20]
        ],
        "milestones": milestones,
        "next_milestone": next_milestone,
        "invite_link": invite_link,
        "onboarding_invite_link": onboarding_invite_link,
    }


@router.get("/lookup-members")
async def lookup_members(
    q: str = Query(..., min_length=1, max_length=100),
    user: dict = Depends(get_current_user),
):
    """Search members by name or email to find their Merin referral code."""
    db = deps.db
    query_regex = {"$regex": q.strip(), "$options": "i"}
    cursor = db.users.find(
        {
            "$and": [
                {"merin_referral_code": {"$exists": True, "$nin": [None, ""]}},
                {"$or": [{"full_name": query_regex}, {"email": query_regex}]},
            ]
        },
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "merin_referral_code": 1},
    ).limit(10)
    results = await cursor.to_list(10)

    def mask_email(email: str) -> str:
        if not email or "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "***"
        else:
            masked_local = local[0] + "***" + local[-1]
        return f"{masked_local}@{domain}"

    return {
        "results": [
            {
                "id": r["id"],
                "name": r.get("full_name", "Unknown"),
                "masked_email": mask_email(r.get("email", "")),
                "merin_code": r.get("merin_referral_code", ""),
            }
            for r in results
        ]
    }


@router.get("/leaderboard")
async def get_referral_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """Get the referral leaderboard — top referrers."""
    db = deps.db

    # Aggregate referral counts
    pipeline = [
        {"$match": {"referred_by": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$referred_by", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    results = await db.users.aggregate(pipeline).to_list(limit)

    leaderboard = []
    for i, r in enumerate(results):
        code = r["_id"]
        referrer = await db.users.find_one(
            {"referral_code": code},
            {"_id": 0, "id": 1, "full_name": 1, "avatar_url": 1}
        )
        if referrer:
            # Determine milestone badge
            badge = None
            for m in reversed(REFERRAL_MILESTONES):
                if r["count"] >= m["threshold"]:
                    badge = m["title"]
                    break

            leaderboard.append({
                "rank": i + 1,
                "user_id": referrer["id"],
                "name": referrer.get("full_name", "Unknown"),
                "avatar_url": referrer.get("avatar_url"),
                "referral_count": r["count"],
                "referral_code": code,
                "badge": badge,
                "is_current_user": referrer["id"] == user["id"],
            })

    # Find current user's rank if not in top list
    current_rank = None
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "referral_code": 1})
    if user_doc and user_doc.get("referral_code"):
        code = user_doc["referral_code"]
        my_count = await db.users.count_documents({"referred_by": code})
        if not any(l["is_current_user"] for l in leaderboard):
            # Count how many have more
            above = await db.users.aggregate([
                {"$match": {"referred_by": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$referred_by", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": my_count}}},
                {"$count": "total"},
            ]).to_list(1)
            current_rank = (above[0]["total"] + 1) if above else 1

    return {
        "leaderboard": leaderboard,
        "current_user_rank": current_rank,
        "total_referrers": await db.users.count_documents({"referral_code": {"$exists": True, "$ne": None}}),
    }


@router.get("/admin/stats")
async def get_admin_referral_stats(user: dict = Depends(require_admin)):
    """Admin: Get referral program statistics."""
    db = deps.db

    total_members = await db.users.count_documents({"role": "member"})
    members_with_code = await db.users.count_documents({"referral_code": {"$exists": True, "$ne": None}, "role": "member"})
    members_referred = await db.users.count_documents({"referred_by": {"$exists": True, "$ne": None}})

    # Top referrers
    pipeline = [
        {"$match": {"referred_by": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$referred_by", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top = await db.users.aggregate(pipeline).to_list(10)

    top_referrers = []
    for r in top:
        referrer = await db.users.find_one({"referral_code": r["_id"]}, {"_id": 0, "full_name": 1})
        top_referrers.append({
            "name": referrer.get("full_name", "Unknown") if referrer else "Unknown",
            "code": r["_id"],
            "count": r["count"],
        })

    return {
        "total_members": total_members,
        "members_with_code": members_with_code,
        "members_referred": members_referred,
        "referral_rate": round(members_referred / max(total_members, 1) * 100, 1),
        "code_adoption_rate": round(members_with_code / max(total_members, 1) * 100, 1),
        "top_referrers": top_referrers,
    }

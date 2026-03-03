"""Rewards API routes - stable endpoints for hub and rewards frontends."""
import os
import uuid
import jwt as pyjwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends, Query
from pydantic import BaseModel

import deps
from utils.rewards_engine import (
    award_points, deduct_points, compute_level, BASE_POINTS,
    process_trade_event, process_deposit_event, process_withdrawal_event,
    process_referral_qualified, check_and_award_badges, seed_default_badges,
    calc_deposit_points,
)

router = APIRouter(prefix="/rewards", tags=["Rewards"])

INTERNAL_API_KEY = os.environ.get("REWARDS_INTERNAL_API_KEY")

MIN_REDEEM_POINTS = 2000


# ─── Auth helpers ───

def verify_internal_key(x_internal_api_key: str = Header(None)):
    """Verify the internal API key for protected endpoints."""
    if not INTERNAL_API_KEY:
        raise HTTPException(status_code=503, detail="Rewards system not configured")
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return True


# ─── Request models ───

class RedeemRequest(BaseModel):
    user_id: str
    reward_id: str
    cost_points: int


class CreditRequest(BaseModel):
    user_id: str
    points: int
    source: str = "manual_promo"
    metadata: Optional[dict] = None


class EventTradeRequest(BaseModel):
    user_id: str


class EventDepositRequest(BaseModel):
    user_id: str
    amount_usdt: float


class EventWithdrawalRequest(BaseModel):
    user_id: str
    amount_usdt: float
    recent_deposit_within_48h: bool = False


class EventSignupRequest(BaseModel):
    user_id: str


class EventReferralRequest(BaseModel):
    inviter_id: str
    invitee_id: str


class EventCommunityRequest(BaseModel):
    user_id: str
    action: str  # "join_community", "first_daily_win", "help_chat"


class AdminSimulateRequest(BaseModel):
    user_id: str
    action_type: str  # test_deposit, test_trade, test_referral, manual_bonus
    points: Optional[int] = None  # only for manual_bonus
    amount_usdt: Optional[float] = None  # for deposit/withdrawal sim


# ─── PUBLIC ENDPOINTS (no auth) ───

@router.get("/summary")
async def get_rewards_summary(user_id: str):
    """GET /api/rewards/summary?user_id={USER_ID}
    Public endpoint - returns user's rewards summary including streak data."""
    db = deps.db

    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})

    if not stats:
        return {
            "user_id": user_id,
            "lifetime_points": 0,
            "monthly_points": 0,
            "level": "Newbie",
            "estimated_usdt": 0.0,
            "min_redeem_points": MIN_REDEEM_POINTS,
            "is_redeemable": False,
            "current_streak": 0,
            "best_streak": 0,
            "referral_count": 0,
            "total_trades": 0,
        }

    lifetime = stats.get("lifetime_points", 0)
    
    # Get referral count
    referral_count = await db.referrals.count_documents({"referrer_id": user_id, "status": "qualified"})
    
    return {
        "user_id": user_id,
        "lifetime_points": lifetime,
        "monthly_points": stats.get("monthly_points", 0),
        "level": stats.get("level", "Newbie"),
        "estimated_usdt": round(lifetime / 100, 2),
        "min_redeem_points": MIN_REDEEM_POINTS,
        "is_redeemable": lifetime >= MIN_REDEEM_POINTS,
        "current_streak": stats.get("current_streak", 0),
        "best_streak": stats.get("best_streak", 0),
        "referral_count": referral_count,
        "total_trades": stats.get("trade_count", 0),
    }


@router.get("/leaderboard")
async def get_rewards_leaderboard(user_id: str):
    """GET /api/rewards/leaderboard?user_id={USER_ID}
    Public endpoint - returns user's leaderboard position and motivational message."""
    db = deps.db
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")

    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    if not stats:
        return {
            "user_id": user_id,
            "current_rank": 0,
            "monthly_points": 0,
            "level": "Newbie",
            "distance_to_next": 0,
            "next_user_name": None,
            "suggested_message": "Start earning points to appear on the leaderboard!",
        }

    entry = await db.rewards_leaderboard.find_one(
        {"user_id": user_id, "month": month_key}, {"_id": 0}
    )
    my_rank = entry.get("rank", 0) if entry else 0
    my_points = stats.get("monthly_points", 0)

    # Find user above
    distance = 0
    next_name = None
    if my_rank > 1:
        above = await db.rewards_leaderboard.find_one(
            {"month": month_key, "rank": my_rank - 1}, {"_id": 0}
        )
        if above:
            above_pts = above.get("monthly_points", 0)
            distance = max(0, above_pts - my_points + 1)
            above_user = await db.users.find_one(
                {"id": above["user_id"]}, {"_id": 0, "full_name": 1}
            )
            if above_user:
                name = above_user.get("full_name", "Unknown")
                parts = name.split()
                next_name = f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else name

    # Build message
    if my_rank == 0:
        msg = "Start earning points to appear on the leaderboard!"
    elif my_rank == 1:
        msg = f"You are Rank #1 this month with {my_points} points. Keep dominating!"
    elif next_name and distance > 0:
        msg = f"You are Rank #{my_rank} this month. {distance} points to pass {next_name}. Don't break your streak!"
    else:
        msg = f"You are Rank #{my_rank} this month with {my_points} points. Keep climbing!"

    return {
        "user_id": user_id,
        "current_rank": my_rank,
        "monthly_points": my_points,
        "level": stats.get("level", "Newbie"),
        "distance_to_next": distance,
        "next_user_name": next_name,
        "suggested_message": msg,
    }


@router.get("/leaderboard/full")
async def get_full_leaderboard(period: str = "monthly", limit: int = 100):
    """GET /api/rewards/leaderboard/full?period=monthly|alltime&limit=100
    Public endpoint - returns full leaderboard for display."""
    db = deps.db
    
    leaderboard = []
    
    if period == "monthly":
        month_key = datetime.now(timezone.utc).strftime("%Y-%m")
        
        # Get leaderboard entries for this month
        entries = await db.rewards_leaderboard.find(
            {"month": month_key},
            {"_id": 0}
        ).sort("rank", 1).limit(limit).to_list(limit)
        
        # Enrich with user data
        for entry in entries:
            user = await db.users.find_one({"id": entry["user_id"]}, {"_id": 0, "full_name": 1})
            stats = await db.rewards_stats.find_one({"user_id": entry["user_id"]}, {"_id": 0, "level": 1})
            
            display_name = "Anonymous"
            if user and user.get("full_name"):
                name = user["full_name"]
                parts = name.split()
                display_name = f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else name
            
            leaderboard.append({
                "user_id": entry["user_id"],
                "rank": entry.get("rank", 0),
                "points": entry.get("monthly_points", 0),
                "display_name": display_name,
                "level": stats.get("level", "Newbie") if stats else "Newbie",
                "rank_change": entry.get("rank_change", 0),
            })
    else:
        # All-time leaderboard - use lifetime_points from stats
        all_stats = await db.rewards_stats.find(
            {"lifetime_points": {"$gt": 0}},
            {"_id": 0}
        ).sort("lifetime_points", -1).limit(limit).to_list(limit)
        
        for i, stats in enumerate(all_stats, 1):
            user = await db.users.find_one({"id": stats["user_id"]}, {"_id": 0, "full_name": 1})
            
            display_name = "Anonymous"
            if user and user.get("full_name"):
                name = user["full_name"]
                parts = name.split()
                display_name = f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else name
            
            leaderboard.append({
                "user_id": stats["user_id"],
                "rank": i,
                "points": stats.get("lifetime_points", 0),
                "display_name": display_name,
                "level": stats.get("level", "Newbie"),
                "rank_change": 0,  # N/A for all-time
            })
    
    return {
        "period": period,
        "leaderboard": leaderboard,
        "total": len(leaderboard),
    }


# ─── PROTECTED ENDPOINTS (require X-INTERNAL-API-KEY) ───

@router.post("/redeem")
async def redeem_reward(req: RedeemRequest, _: bool = Depends(verify_internal_key)):
    """POST /api/rewards/redeem
    Protected - redeems points for a reward."""
    db = deps.db

    stats = await db.rewards_stats.find_one({"user_id": req.user_id}, {"_id": 0})
    if not stats or stats.get("lifetime_points", 0) < req.cost_points:
        return {"success": False, "message": "Not enough points to redeem."}

    if req.cost_points < MIN_REDEEM_POINTS:
        return {"success": False, "message": f"Minimum redemption is {MIN_REDEEM_POINTS} points."}

    await deduct_points(db, req.user_id, req.cost_points, "redeem", {
        "reward_id": req.reward_id,
        "cost_points": req.cost_points,
    })

    # Record redemption
    await db.rewards_redemptions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "reward_id": req.reward_id,
        "cost_points": req.cost_points,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    updated = await db.rewards_stats.find_one({"user_id": req.user_id}, {"_id": 0})
    return {
        "success": True,
        "new_lifetime_points": updated.get("lifetime_points", 0),
        "message": "Redemption accepted. Processing within 1-2 days for small vouchers, and 3-5 days for larger amounts.",
    }


@router.post("/credit")
async def credit_points(req: CreditRequest, _: bool = Depends(verify_internal_key)):
    """POST /api/rewards/credit
    Protected - manually credit points to a user (admin/internal only)."""
    db = deps.db

    await award_points(db, req.user_id, req.points, req.source, req.metadata)

    updated = await db.rewards_stats.find_one({"user_id": req.user_id}, {"_id": 0})
    return {
        "success": True,
        "new_lifetime_points": updated.get("lifetime_points", 0),
    }


# ─── EVENT HOOKS (protected, called internally when events happen) ───

@router.post("/events/trade")
async def event_trade(req: EventTradeRequest, _: bool = Depends(verify_internal_key)):
    """Record a trade event and compute points/streaks."""
    await process_trade_event(deps.db, req.user_id)
    return {"success": True}


@router.post("/events/deposit")
async def event_deposit(req: EventDepositRequest, _: bool = Depends(verify_internal_key)):
    """Record a deposit event and award points."""
    await process_deposit_event(deps.db, req.user_id, req.amount_usdt)
    return {"success": True}


@router.post("/events/withdrawal")
async def event_withdrawal(req: EventWithdrawalRequest, _: bool = Depends(verify_internal_key)):
    """Record a withdrawal event and award points."""
    await process_withdrawal_event(deps.db, req.user_id, req.amount_usdt, req.recent_deposit_within_48h)
    return {"success": True}


@router.post("/events/signup")
async def event_signup(req: EventSignupRequest, _: bool = Depends(verify_internal_key)):
    """Record sign-up & verify event."""
    await award_points(deps.db, req.user_id, BASE_POINTS["signup_verify"], "signup_verify")
    return {"success": True}


@router.post("/events/referral-qualified")
async def event_referral(req: EventReferralRequest, _: bool = Depends(verify_internal_key)):
    """Record a qualified referral."""
    await process_referral_qualified(deps.db, req.inviter_id, req.invitee_id)
    return {"success": True}


@router.post("/events/community")
async def event_community(req: EventCommunityRequest, _: bool = Depends(verify_internal_key)):
    """Record a community action (join, daily win, help chat)."""
    db = deps.db
    action = req.action

    if action == "join_community":
        await award_points(db, req.user_id, BASE_POINTS["join_community"], "join_community")
    elif action == "first_daily_win":
        await award_points(db, req.user_id, BASE_POINTS["first_daily_win"], "first_daily_win")
    elif action == "help_chat":
        # Check daily cap
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_logs = await db.rewards_point_logs.find({
            "user_id": req.user_id,
            "source": "help_chat",
            "created_at": {"$regex": f"^{today}"},
        }).to_list(100)
        daily_total = sum(log.get("base_points", 0) for log in today_logs)
        if daily_total < BASE_POINTS["help_chat_daily_cap"]:
            pts = min(BASE_POINTS["help_chat"], BASE_POINTS["help_chat_daily_cap"] - daily_total)
            await award_points(db, req.user_id, pts, "help_chat")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown community action: {action}")

    return {"success": True}


# ─── EARNING ACTIONS STATUS & CLAIM ───

@router.get("/earning-actions")
async def get_earning_actions_status(user: dict = Depends(deps.get_current_user)):
    """Get the status of all earning actions for the current user — which are claimed/awarded."""
    db = deps.db
    user_id = user["id"]

    # Get all point log sources for this user
    logs = await db.rewards_point_logs.find(
        {"user_id": user_id},
        {"_id": 0, "source": 1, "base_points": 1}
    ).to_list(5000)
    
    source_set = set()
    source_counts = {}
    for log in logs:
        src = log.get("source")
        source_set.add(src)
        source_counts[src] = source_counts.get(src, 0) + 1

    # Get user stats
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    trade_count = stats.get("lifetime_trades", 0) if stats else 0
    best_streak = stats.get("best_streak_days", 0) if stats else 0
    deposit_total = stats.get("lifetime_deposit_usdt", 0) if stats else 0
    referral_count = stats.get("qualified_referrals", 0) if stats else 0

    actions = [
        {
            "id": "signup_verify",
            "name": "Sign Up & Verify",
            "description": "Create your account and enter your first trade",
            "points": BASE_POINTS["signup_verify"],
            "awarded": "signup_verify" in source_set,
            "claimable": False,
            "one_time": True,
            "category": "onboarding",
        },
        {
            "id": "join_community",
            "name": "Join Community",
            "description": "Join our trading community",
            "points": BASE_POINTS["join_community"],
            "awarded": "join_community" in source_set,
            "claimable": "join_community" not in source_set,
            "one_time": True,
            "category": "onboarding",
        },
        {
            "id": "first_trade",
            "name": "First Trade",
            "description": "Complete your very first trade",
            "points": BASE_POINTS["first_trade"],
            "awarded": "first_trade" in source_set,
            "claimable": False,
            "one_time": True,
            "category": "trading",
        },
        {
            "id": "first_daily_win",
            "name": "First Daily Win",
            "description": "Achieve your first profitable trade",
            "points": BASE_POINTS["first_daily_win"],
            "awarded": "first_daily_win" in source_set,
            "claimable": False,
            "one_time": True,
            "category": "trading",
        },
        {
            "id": "streak_5_day",
            "name": "5-Day Trade Streak",
            "description": "Maintain a 5-day consecutive trading streak",
            "points": BASE_POINTS["streak_5_day"],
            "awarded": "streak_5_day" in source_set,
            "times_awarded": source_counts.get("streak_5_day", 0),
            "claimable": False,
            "one_time": False,
            "category": "streaks",
        },
        {
            "id": "milestone_10_trade",
            "name": "10 Trades Milestone",
            "description": "Complete your 10th trade",
            "points": BASE_POINTS["milestone_10_trade"],
            "awarded": "milestone_10_trade" in source_set,
            "claimable": False,
            "one_time": True,
            "category": "trading",
        },
        {
            "id": "qualified_referral",
            "name": "Qualified Referral",
            "description": "Refer a new member who completes their first trade",
            "points": BASE_POINTS["qualified_referral"],
            "awarded": "qualified_referral" in source_set,
            "times_awarded": source_counts.get("qualified_referral", 0),
            "claimable": False,
            "one_time": False,
            "category": "referrals",
        },
        {
            "id": "deposit",
            "name": "Deposit Bonus",
            "description": "Earn 50 points for every $50 USDT deposited",
            "points": BASE_POINTS["deposit_per_50_usdt"],
            "points_label": "50 pts / $50",
            "awarded": "deposit" in source_set,
            "claimable": False,
            "one_time": False,
            "category": "deposits",
        },
    ]

    return {
        "actions": actions,
        "stats": {
            "lifetime_trades": trade_count,
            "best_streak": best_streak,
            "lifetime_deposit": deposit_total,
            "referrals": referral_count,
        },
    }


@router.post("/claim/{action_id}")
async def claim_earning_action(
    action_id: str,
    user: dict = Depends(deps.get_current_user),
):
    """Claim a one-time earning action (e.g., join_community)."""
    db = deps.db
    user_id = user["id"]

    claimable_actions = {"join_community"}
    if action_id not in claimable_actions:
        raise HTTPException(status_code=400, detail="This action cannot be manually claimed.")

    # Check if already claimed
    existing = await db.rewards_point_logs.find_one({
        "user_id": user_id,
        "source": action_id,
    })
    if existing:
        raise HTTPException(status_code=400, detail="You have already claimed this action.")

    pts = BASE_POINTS.get(action_id, 0)
    if pts <= 0:
        raise HTTPException(status_code=400, detail="Invalid action.")

    await award_points(db, user_id, pts, action_id)
    return {"success": True, "points_awarded": pts, "action": action_id}


# ─── POINTS HISTORY (auth via JWT) ───

@router.get("/history")
async def get_rewards_history(
    user_id: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(deps.get_current_user),
):
    """GET /api/rewards/history — get points transaction log.
    Members see their own history. Admins can pass ?user_id= to see any user."""
    db = deps.db
    admin_roles = {"basic_admin", "admin", "super_admin", "master_admin"}

    target_uid = user["id"]
    if user_id and user.get("role") in admin_roles:
        target_uid = user_id
    elif user_id and user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Cannot view another user's history")

    logs = await db.rewards_point_logs.find(
        {"user_id": target_uid}, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)

    # Compute running balance (oldest → newest, then reverse)
    logs_asc = list(reversed(logs))
    running = 0
    for log in logs_asc:
        running += log.get("points", 0)
        log["balance_after"] = max(running, 0)
    logs_asc.reverse()

    return {"user_id": target_uid, "history": logs_asc}


# ─── ADMIN REWARDS TOOLS (require admin JWT) ───

@router.get("/admin/lookup")
async def admin_rewards_lookup(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    user: dict = Depends(deps.require_admin),
):
    """Admin lookup — search by user_id or email, returns full rewards profile."""
    db = deps.db

    if not user_id and not email:
        raise HTTPException(status_code=400, detail="Provide user_id or email")

    if email and not user_id:
        target = await db.users.find_one({"email": email}, {"_id": 0, "id": 1, "full_name": 1, "email": 1})
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = target["id"]
    else:
        target = await db.users.find_one({"id": user_id}, {"_id": 0, "id": 1, "full_name": 1, "email": 1})
        if not target:
            raise HTTPException(status_code=404, detail="User not found")

    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0}) or {}
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    lb_entry = await db.rewards_leaderboard.find_one(
        {"user_id": user_id, "month": month_key}, {"_id": 0}
    )

    logs = await db.rewards_point_logs.find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)

    # Running balance
    logs_asc = list(reversed(logs))
    running = 0
    for log in logs_asc:
        running += log.get("points", 0)
        log["balance_after"] = max(running, 0)
    logs_asc.reverse()

    lifetime = stats.get("lifetime_points", 0)
    return {
        "user_id": user_id,
        "full_name": target.get("full_name", ""),
        "email": target.get("email", ""),
        "lifetime_points": lifetime,
        "monthly_points": stats.get("monthly_points", 0),
        "level": stats.get("level", "Newbie"),
        "estimated_usdt": round(lifetime / 100, 2),
        "current_rank": lb_entry.get("rank", 0) if lb_entry else 0,
        "lifetime_trades": stats.get("lifetime_trades", 0),
        "lifetime_deposit_usdt": stats.get("lifetime_deposit_usdt", 0),
        "current_streak_days": stats.get("current_streak_days", 0),
        "best_streak_days": stats.get("best_streak_days", 0),
        "qualified_referrals": stats.get("qualified_referrals", 0),
        "history": logs_asc,
    }


@router.post("/admin/simulate")
async def admin_simulate_points(
    req: AdminSimulateRequest,
    user: dict = Depends(deps.require_admin),
):
    """Admin simulate — award points using the real rewards engine.
    Actions: test_deposit, test_trade, test_referral, manual_bonus."""
    db = deps.db

    target = await db.users.find_one({"id": req.user_id}, {"_id": 0, "id": 1, "full_name": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    sim_meta = {"simulated_by": user["id"], "admin_test": True}

    if req.action_type == "test_trade":
        await process_trade_event(db, req.user_id)
        # Tag the most recent log as simulated
        await db.rewards_point_logs.update_many(
            {"user_id": req.user_id, "metadata.admin_test": {"$exists": False}},
            {"$set": {"metadata.admin_test": True, "metadata.simulated_by": user["id"]}},
        )
        action_label = "Simulated Trade"

    elif req.action_type == "test_deposit":
        amount = req.amount_usdt or 100.0
        await process_deposit_event(db, req.user_id, amount)
        await db.rewards_point_logs.update_one(
            {"user_id": req.user_id, "source": "deposit"},
            {"$set": {"metadata.admin_test": True, "metadata.simulated_by": user["id"]}},
            sort=[("created_at", -1)],
        )
        action_label = f"Simulated Deposit (${amount})"

    elif req.action_type == "test_referral":
        await process_referral_qualified(db, req.user_id, f"sim_invitee_{uuid.uuid4().hex[:8]}")
        action_label = "Simulated Referral"

    elif req.action_type == "manual_bonus":
        pts = req.points or 100
        await award_points(db, req.user_id, pts, "manual_bonus", sim_meta)
        action_label = f"Manual Bonus (+{pts} pts)"

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action_type: {req.action_type}")

    stats = await db.rewards_stats.find_one({"user_id": req.user_id}, {"_id": 0})
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    lb_entry = await db.rewards_leaderboard.find_one(
        {"user_id": req.user_id, "month": month_key}, {"_id": 0}
    )

    return {
        "success": True,
        "action": action_label,
        "new_lifetime_points": stats.get("lifetime_points", 0) if stats else 0,
        "new_monthly_points": stats.get("monthly_points", 0) if stats else 0,
        "level": stats.get("level", "Newbie") if stats else "Newbie",
        "current_rank": lb_entry.get("rank", 0) if lb_entry else 0,
    }


# ─── SYSTEM CHECK (admin auth via JWT) ───

@router.post("/system-check")
async def run_system_check(user: dict = Depends(deps.require_master_admin)):
    """Run a full system health check for the rewards system.
    Creates a test user, simulates events, and validates all endpoints."""
    db = deps.db
    test_user_id = "test_debug_user"
    results = []
    overall_pass = True

    try:
        # Step 1: Ensure test user exists
        test_user = await db.users.find_one({"id": test_user_id}, {"_id": 0})
        if not test_user:
            await db.users.insert_one({
                "id": test_user_id,
                "full_name": "Test Debug User",
                "email": "test_debug@crosscurrent.test",
                "role": "member",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        results.append({"step": "Create test user", "status": "pass"})

        # Clean previous test data
        await db.rewards_stats.delete_many({"user_id": test_user_id})
        await db.rewards_leaderboard.delete_many({"user_id": test_user_id})
        await db.rewards_point_logs.delete_many({"user_id": test_user_id})
        await db.rewards_redemptions.delete_many({"user_id": test_user_id})

        # Step 2: Simulate sign-up & verify
        await award_points(db, test_user_id, BASE_POINTS["signup_verify"], "signup_verify")
        stats = await db.rewards_stats.find_one({"user_id": test_user_id}, {"_id": 0})
        assert stats["lifetime_points"] == 25, f"Expected 25 pts, got {stats['lifetime_points']}"
        results.append({"step": "Sign-up & verify (25 pts)", "status": "pass", "points": 25})

        # Step 3: Simulate deposit (100 USDT = 100 pts)
        await process_deposit_event(db, test_user_id, 100.0)
        stats = await db.rewards_stats.find_one({"user_id": test_user_id}, {"_id": 0})
        expected = 25 + 100  # 25 signup + 100 deposit (100/50*50)
        assert stats["lifetime_points"] == expected, f"Expected {expected}, got {stats['lifetime_points']}"
        assert stats["lifetime_deposit_usdt"] == 100.0
        results.append({"step": "Deposit 100 USDT (100 pts)", "status": "pass", "points": expected})

        # Step 4: Simulate a trade
        await process_trade_event(db, test_user_id)
        stats = await db.rewards_stats.find_one({"user_id": test_user_id}, {"_id": 0})
        expected += 25  # first trade bonus
        assert stats["lifetime_points"] == expected, f"Expected {expected}, got {stats['lifetime_points']}"
        assert stats["lifetime_trades"] == 1
        results.append({"step": "First trade (25 pts)", "status": "pass", "points": expected})

        # Step 5: Simulate qualified referral
        await process_referral_qualified(db, test_user_id, "test_invitee_user")
        stats = await db.rewards_stats.find_one({"user_id": test_user_id}, {"_id": 0})
        expected += 150  # referral bonus
        assert stats["lifetime_points"] == expected, f"Expected {expected}, got {stats['lifetime_points']}"
        results.append({"step": "Qualified referral (150 pts)", "status": "pass", "points": expected})

        # Step 6: Validate Summary endpoint
        summary = await get_rewards_summary(test_user_id)
        required_fields = ["user_id", "lifetime_points", "monthly_points", "level", "estimated_usdt", "min_redeem_points", "is_redeemable"]
        for f in required_fields:
            assert f in summary, f"Missing field: {f}"
        assert summary["lifetime_points"] == expected
        results.append({"step": "Summary API", "status": "pass", "response": summary})

        # Step 7: Validate Leaderboard endpoint
        lb = await get_rewards_leaderboard(test_user_id)
        required_lb = ["user_id", "current_rank", "monthly_points", "level", "distance_to_next", "next_user_name", "suggested_message"]
        for f in required_lb:
            assert f in lb, f"Missing field: {f}"
        results.append({"step": "Leaderboard API", "status": "pass", "response": lb})

        # Step 8: Credit some extra points to enable redemption
        credit_amount = 2000 - expected + 100  # Enough to redeem
        await award_points(db, test_user_id, credit_amount, "system_check_credit")
        expected += credit_amount
        stats = await db.rewards_stats.find_one({"user_id": test_user_id}, {"_id": 0})
        assert stats["lifetime_points"] == expected
        results.append({"step": f"Credit {credit_amount} pts", "status": "pass", "points": expected})

        # Step 9: Validate Redeem
        pre_redeem = stats["lifetime_points"]
        await deduct_points(db, test_user_id, 2000, "redeem", {"reward_id": "test_reward"})
        stats = await db.rewards_stats.find_one({"user_id": test_user_id}, {"_id": 0})
        assert stats["lifetime_points"] == pre_redeem - 2000, f"Redeem failed: expected {pre_redeem - 2000}, got {stats['lifetime_points']}"
        results.append({"step": "Redeem 2000 pts", "status": "pass", "points": stats["lifetime_points"]})

        # Step 10: Validate Credit restores points
        pre_credit = stats["lifetime_points"]
        await award_points(db, test_user_id, 500, "system_check_restore")
        stats = await db.rewards_stats.find_one({"user_id": test_user_id}, {"_id": 0})
        assert stats["lifetime_points"] == pre_credit + 500
        results.append({"step": "Credit 500 pts", "status": "pass", "points": stats["lifetime_points"]})

        # Cleanup test data
        await db.rewards_stats.delete_many({"user_id": test_user_id})
        await db.rewards_leaderboard.delete_many({"user_id": test_user_id})
        await db.rewards_point_logs.delete_many({"user_id": test_user_id})
        await db.rewards_redemptions.delete_many({"user_id": test_user_id})

    except AssertionError as exc:
        results.append({"step": "ASSERTION FAILED", "status": "fail", "error": str(exc)})
        overall_pass = False
    except Exception as exc:
        results.append({"step": "UNEXPECTED ERROR", "status": "fail", "error": str(exc)})
        overall_pass = False

    return {
        "overall": "pass" if overall_pass else "fail",
        "message": "Hub system check passed. Summary OK, Leaderboard OK, Redeem OK, Credit OK." if overall_pass
                   else f"Hub system check failed at: {results[-1].get('step', 'unknown')} - {results[-1].get('error', '')}",
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── USER SEARCH (admin) ───

@router.get("/admin/search-users")
async def admin_search_users(
    q: str = "",
    limit: int = 10,
    user: dict = Depends(deps.require_admin),
):
    """Search users by name or email for autocomplete dropdown."""
    db = deps.db
    if not q or len(q) < 2:
        return {"users": []}

    query = {
        "$or": [
            {"full_name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]
    }
    users = await db.users.find(query, {"_id": 0, "id": 1, "full_name": 1, "email": 1, "role": 1}).limit(limit).to_list(limit)
    return {"users": users}


# ─── BADGES ENDPOINTS ───

@router.get("/badges")
async def get_badge_definitions():
    """Get all active badge definitions (public)."""
    db = deps.db
    badges = await db.rewards_badge_definitions.find(
        {"is_active": True}, {"_id": 0}
    ).sort("sort_order", 1).to_list(100)
    return {"badges": badges}


@router.get("/badges/user")
async def get_user_badges(
    user_id: Optional[str] = None,
    user: dict = Depends(deps.get_current_user),
):
    """Get badges earned by a user. Members see own, admins can view any user."""
    db = deps.db
    admin_roles = {"basic_admin", "admin", "super_admin", "master_admin"}
    target_uid = user["id"]
    if user_id and user.get("role") in admin_roles:
        target_uid = user_id
    elif user_id and user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Cannot view another user's badges")

    earned = await db.rewards_user_badges.find(
        {"user_id": target_uid}, {"_id": 0}
    ).sort("earned_at", -1).to_list(100)

    # Get all badge definitions for comparison
    definitions = await db.rewards_badge_definitions.find(
        {"is_active": True}, {"_id": 0}
    ).sort("sort_order", 1).to_list(100)

    earned_ids = {b["badge_id"] for b in earned}
    earned_map = {b["badge_id"]: b for b in earned}

    badges_with_status = []
    for badge_def in definitions:
        is_earned = badge_def["id"] in earned_ids
        badges_with_status.append({
            **badge_def,
            "earned": is_earned,
            "earned_at": earned_map[badge_def["id"]]["earned_at"] if is_earned else None,
        })

    return {"user_id": target_uid, "badges": badges_with_status}


@router.post("/badges/check")
async def check_badges_for_user(
    user_id: Optional[str] = None,
    user: dict = Depends(deps.get_current_user),
):
    """Trigger badge check for a user. Returns newly awarded badges."""
    db = deps.db
    target_uid = user["id"]
    admin_roles = {"basic_admin", "admin", "super_admin", "master_admin"}
    if user_id and user.get("role") in admin_roles:
        target_uid = user_id

    newly_awarded = await check_and_award_badges(db, target_uid)
    return {"user_id": target_uid, "newly_awarded": newly_awarded}


@router.post("/retroactive-scan")
async def retroactive_badge_scan(
    user_id: Optional[str] = None,
    user: dict = Depends(deps.get_current_user),
):
    """Scan a user's actual hub records and retroactively calculate rewards_stats,
    then check and award all earned badges. Can be run by any user for themselves,
    or by an admin for any user."""
    db = deps.db
    target_uid = user["id"]
    admin_roles = {"basic_admin", "admin", "super_admin", "master_admin"}
    if user_id and user.get("role") in admin_roles:
        target_uid = user_id

    stats_update = await _compute_real_stats(db, target_uid)

    # Update rewards_stats with real data (merge, don't overwrite points)
    existing = await db.rewards_stats.find_one({"user_id": target_uid}, {"_id": 0})

    update_fields = {
        "lifetime_trades": stats_update["lifetime_trades"],
        "distinct_trade_days": stats_update["distinct_trade_days"],
        "best_streak_days": max(
            stats_update["best_streak_days"],
            existing.get("best_streak_days", 0) if existing else 0
        ),
        "current_streak_days": stats_update["current_streak_days"],
        "lifetime_deposit_usdt": stats_update["lifetime_deposit_usdt"],
        "qualified_referrals": stats_update["qualified_referrals"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.rewards_stats.update_one(
        {"user_id": target_uid},
        {"$set": update_fields, "$setOnInsert": {"user_id": target_uid, "level": 1, "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )

    # Now check and award badges
    newly_awarded = await check_and_award_badges(db, target_uid)

    return {
        "user_id": target_uid,
        "stats": update_fields,
        "newly_awarded": newly_awarded,
        "awarded_actions": stats_update.get("awarded_actions", []),
    }


@router.post("/retroactive-scan-all")
async def retroactive_scan_all_users(
    user: dict = Depends(deps.require_master_admin),
):
    """Scan ALL users and retroactively award badges and points. Master admin only."""
    db = deps.db
    users = await db.users.find({}, {"_id": 0, "id": 1}).to_list(1000)

    results = []
    for u in users:
        uid = u["id"]
        try:
            stats_update = await _compute_real_stats(db, uid)
            existing = await db.rewards_stats.find_one({"user_id": uid}, {"_id": 0})
            update_fields = {
                "lifetime_trades": stats_update["lifetime_trades"],
                "distinct_trade_days": stats_update["distinct_trade_days"],
                "best_streak_days": max(
                    stats_update["best_streak_days"],
                    existing.get("best_streak_days", 0) if existing else 0
                ),
                "current_streak_days": stats_update["current_streak_days"],
                "lifetime_deposit_usdt": stats_update["lifetime_deposit_usdt"],
                "qualified_referrals": stats_update["qualified_referrals"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.rewards_stats.update_one(
                {"user_id": uid},
                {"$set": update_fields, "$setOnInsert": {"user_id": uid, "level": 1, "created_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
            newly_awarded = await check_and_award_badges(db, uid)
            results.append({"user_id": uid, "badges_awarded": len(newly_awarded), "newly_awarded": newly_awarded})
        except Exception as e:
            results.append({"user_id": uid, "error": str(e)})

    return {"scanned": len(users), "results": results}


async def _compute_real_stats(db, user_id: str) -> dict:
    """Compute real user stats by scanning actual DB records,
    and retroactively award any missed points."""
    from utils.trading_days import get_holidays_for_range

    # 1. Count trades and distinct trade days
    trade_count = await db.trade_logs.count_documents({"user_id": user_id})
    
    # Distinct trade days
    date_agg = await db.trade_logs.aggregate([
        {"$match": {"user_id": user_id}},
        {"$project": {"date": {"$substr": ["$created_at", 0, 10]}}},
        {"$group": {"_id": "$date"}},
        {"$sort": {"_id": 1}},
    ]).to_list(2000)
    trade_dates = sorted([d["_id"] for d in date_agg])
    distinct_days = len(trade_dates)

    # 2. Calculate best streak from trade dates (skip weekends + holidays)
    best_streak = 0
    current_streak = 0
    if trade_dates:
        min_year = int(trade_dates[0][:4])
        max_year = int(trade_dates[-1][:4])
        holidays = get_holidays_for_range(min_year, max_year + 1)
        date_set = set(trade_dates)

        from datetime import date as date_type
        first = date_type.fromisoformat(trade_dates[0])
        today = date_type.today()
        check = first
        streak = 0
        while check <= today:
            if check.weekday() >= 5 or check.isoformat() in holidays:
                check += timedelta(days=1)
                continue
            if check.isoformat() in date_set:
                streak += 1
                best_streak = max(best_streak, streak)
            else:
                streak = 0
            check += timedelta(days=1)

        # Current streak walking backwards from today
        current_streak = 0
        check = today
        while check.weekday() >= 5 or check.isoformat() in holidays:
            check -= timedelta(days=1)
        if check.isoformat() not in date_set:
            check -= timedelta(days=1)
            while check.weekday() >= 5 or check.isoformat() in holidays:
                check -= timedelta(days=1)
        while check.isoformat() in date_set:
            current_streak += 1
            check -= timedelta(days=1)
            while check.weekday() >= 5 or check.isoformat() in holidays:
                check -= timedelta(days=1)

    # 3. Count deposits
    total_deposits = 0.0
    try:
        dep_agg = await db.deposits.aggregate([
            {"$match": {"user_id": user_id, "status": "approved"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]).to_list(1)
        if dep_agg:
            total_deposits = dep_agg[0].get("total", 0)
    except Exception:
        pass
    try:
        adj_agg = await db.profit_adjustments.aggregate([
            {"$match": {"user_id": user_id, "type": "deposit"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]).to_list(1)
        if adj_agg:
            total_deposits += adj_agg[0].get("total", 0)
    except Exception:
        pass

    # 4. Count referrals
    referral_count = 0
    try:
        referral_count = await db.users.count_documents({"referred_by": user_id})
    except Exception:
        pass

    # 5. Check for any winning trade (actual_profit > 0) for first_daily_win
    has_winning_trade = False
    try:
        winning = await db.trade_logs.find_one(
            {"user_id": user_id, "actual_profit": {"$gt": 0}},
            {"_id": 0, "id": 1}
        )
        has_winning_trade = winning is not None
    except Exception:
        pass

    # ─── RETROACTIVE POINT AWARDS ───
    # Check which one-time actions have already been awarded
    existing_sources = set()
    logs = await db.rewards_point_logs.find(
        {"user_id": user_id},
        {"_id": 0, "source": 1}
    ).to_list(5000)
    for log in logs:
        existing_sources.add(log.get("source"))

    awarded_actions = []

    # signup_verify: award if user has at least 1 trade and never received it
    if trade_count >= 1 and "signup_verify" not in existing_sources:
        await award_points(db, user_id, BASE_POINTS["signup_verify"], "signup_verify")
        awarded_actions.append("signup_verify")

    # first_trade: award if user has trades and never received it
    if trade_count >= 1 and "first_trade" not in existing_sources:
        await award_points(db, user_id, BASE_POINTS["first_trade"], "first_trade")
        awarded_actions.append("first_trade")

    # first_daily_win: award if user has a winning trade and never received it
    if has_winning_trade and "first_daily_win" not in existing_sources:
        await award_points(db, user_id, BASE_POINTS["first_daily_win"], "first_daily_win")
        awarded_actions.append("first_daily_win")

    # streak_5_day: award for each 5-day streak milestone not yet awarded
    if best_streak >= 5:
        # Count how many logs with streak_5_day source exist
        streak_logs = await db.rewards_point_logs.count_documents(
            {"user_id": user_id, "source": "streak_5_day"}
        )
        deserved = best_streak // 5
        if streak_logs < deserved:
            for _ in range(deserved - streak_logs):
                await award_points(db, user_id, BASE_POINTS["streak_5_day"], "streak_5_day",
                                   {"retroactive": True, "best_streak": best_streak})
            awarded_actions.append(f"streak_5_day (x{deserved - streak_logs})")

    # milestone_10_trade: award if 10+ trades and never received
    if trade_count >= 10 and "milestone_10_trade" not in existing_sources:
        await award_points(db, user_id, BASE_POINTS["milestone_10_trade"], "milestone_10_trade")
        awarded_actions.append("milestone_10_trade")

    # deposit points: calculate total owed vs total awarded
    if total_deposits > 0:
        deserved_deposit_pts = calc_deposit_points(total_deposits)
        dep_logs = await db.rewards_point_logs.find(
            {"user_id": user_id, "source": "deposit"},
            {"_id": 0, "base_points": 1}
        ).to_list(5000)
        awarded_deposit_pts = sum(log.get("base_points", 0) for log in dep_logs)
        diff = deserved_deposit_pts - awarded_deposit_pts
        if diff > 0:
            await award_points(db, user_id, diff, "deposit", {"retroactive": True, "total_deposits": total_deposits})
            awarded_actions.append(f"deposit ({diff} pts)")

    # qualified_referral: award for each referral not yet awarded
    if referral_count > 0:
        ref_logs = await db.rewards_point_logs.count_documents(
            {"user_id": user_id, "source": "qualified_referral"}
        )
        if ref_logs < referral_count:
            for _ in range(referral_count - ref_logs):
                await award_points(db, user_id, BASE_POINTS["qualified_referral"], "qualified_referral",
                                   {"retroactive": True})
            awarded_actions.append(f"qualified_referral (x{referral_count - ref_logs})")

    return {
        "lifetime_trades": trade_count,
        "distinct_trade_days": distinct_days,
        "best_streak_days": best_streak,
        "current_streak_days": current_streak,
        "lifetime_deposit_usdt": total_deposits,
        "qualified_referrals": referral_count,
        "awarded_actions": awarded_actions,
    }



# ─── ADMIN BADGE MANAGEMENT (master admin only) ───

class BadgeUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.put("/admin/badges/{badge_id}")
async def admin_update_badge(
    badge_id: str,
    req: BadgeUpdateRequest,
    user: dict = Depends(deps.require_master_admin),
):
    """Master admin can customize badge names, descriptions, icons, and active status."""
    db = deps.db

    badge = await db.rewards_badge_definitions.find_one({"id": badge_id})
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if req.name is not None:
        updates["name"] = req.name
    if req.description is not None:
        updates["description"] = req.description
    if req.icon is not None:
        updates["icon"] = req.icon
    if req.is_active is not None:
        updates["is_active"] = req.is_active
    if req.sort_order is not None:
        updates["sort_order"] = req.sort_order

    await db.rewards_badge_definitions.update_one(
        {"id": badge_id}, {"$set": updates}
    )

    updated = await db.rewards_badge_definitions.find_one({"id": badge_id}, {"_id": 0})
    return {"success": True, "badge": updated}


@router.get("/admin/badges")
async def admin_get_all_badges(
    user: dict = Depends(deps.require_admin),
):
    """Admin view of all badge definitions (including inactive)."""
    db = deps.db
    badges = await db.rewards_badge_definitions.find(
        {}, {"_id": 0}
    ).sort("sort_order", 1).to_list(200)
    return {"badges": badges}


# ─── ADMIN MANUAL POINT ADJUSTMENT WITH AUDIT ───

class ManualAdjustRequest(BaseModel):
    user_id: str
    points: int
    reason: str
    is_deduction: bool = False


@router.post("/admin/adjust-points")
async def admin_adjust_points(
    req: ManualAdjustRequest,
    user: dict = Depends(deps.require_admin),
):
    """Admin manual point adjustment with audit trail."""
    db = deps.db

    target = await db.users.find_one({"id": req.user_id}, {"_id": 0, "id": 1, "full_name": 1})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    metadata = {
        "adjusted_by": user["id"],
        "adjusted_by_name": user.get("full_name", "Admin"),
        "reason": req.reason,
        "admin_adjustment": True,
    }

    if req.is_deduction:
        await deduct_points(db, req.user_id, abs(req.points), "admin_adjustment_deduct", metadata)
    else:
        await award_points(db, req.user_id, abs(req.points), "admin_adjustment_credit", metadata)

    # Check badges after adjustment
    await check_and_award_badges(db, req.user_id)

    stats = await db.rewards_stats.find_one({"user_id": req.user_id}, {"_id": 0})
    return {
        "success": True,
        "new_lifetime_points": stats.get("lifetime_points", 0) if stats else 0,
        "level": stats.get("level", "Newbie") if stats else "Newbie",
    }


# ─── REWARDS STORE CROSS-SITE AUTH ───

STORE_JWT_SECRET = os.environ.get("JWT_SECRET", os.environ.get("SECRET_KEY", ""))
STORE_TOKEN_EXPIRY_MINUTES = 10


@router.post("/store-token")
async def generate_store_token(
    user: dict = Depends(deps.get_current_user),
):
    """Generate a signed JWT for seamless cross-site auth with the rewards store."""
    db = deps.db

    stats = await db.rewards_stats.find_one({"user_id": user["id"]}, {"_id": 0})

    payload = {
        "sub": user["id"],
        "email": user.get("email", ""),
        "name": user.get("full_name", ""),
        "role": user.get("role", "member"),
        "level": stats.get("level", "Newbie") if stats else "Newbie",
        "points": stats.get("lifetime_points", 0) if stats else 0,
        "iss": "crosscurrent-hub",
        "aud": "crosscurrent-store",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=STORE_TOKEN_EXPIRY_MINUTES),
    }

    token = pyjwt.encode(payload, STORE_JWT_SECRET, algorithm="HS256")

    return {
        "token": token,
        "expires_in": STORE_TOKEN_EXPIRY_MINUTES * 60,
        "store_url": f"https://rewards.crosscur.rent/login?token={token}",
    }


@router.post("/store-verify")
async def verify_store_token(
    token: str = Query(...),
    x_internal_api_key: str = Header(None),
):
    """Called by the rewards store to verify a user token and get their profile.
    Requires the internal API key for security."""
    verify_internal_key(x_internal_api_key)

    try:
        payload = pyjwt.decode(
            token, STORE_JWT_SECRET, algorithms=["HS256"],
            audience="crosscurrent-store", issuer="crosscurrent-hub",
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    db = deps.db
    user_id = payload.get("sub")
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "id": 1, "email": 1, "full_name": 1})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "valid": True,
        "user": {
            "id": user["id"],
            "email": user.get("email"),
            "name": user.get("full_name"),
            "level": stats.get("level", "Newbie") if stats else "Newbie",
            "lifetime_points": stats.get("lifetime_points", 0) if stats else 0,
            "available_balance": stats.get("lifetime_points", 0) if stats else 0,
        },
    }


@router.post("/store-deduct")
async def store_deduct_points(
    user_id: str = Query(...),
    points: int = Query(..., gt=0),
    item_name: str = Query("Store Redemption"),
    x_internal_api_key: str = Header(None),
):
    """Called by the rewards store to deduct points when a user redeems an item."""
    verify_internal_key(x_internal_api_key)
    db = deps.db

    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    if not stats or stats.get("lifetime_points", 0) < points:
        raise HTTPException(status_code=400, detail="Insufficient points")

    await deduct_points(db, user_id, points, "store_redemption", {
        "item_name": item_name,
        "source": "rewards_store",
    })

    updated_stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    return {
        "success": True,
        "deducted": points,
        "remaining_points": updated_stats.get("lifetime_points", 0) if updated_stats else 0,
    }



# ─── REWARDS PLATFORM SYNC ENDPOINTS ───

@router.post("/admin/sync-all-users")
async def admin_sync_all_users(
    user: dict = Depends(deps.require_master_admin),
):
    """Master admin: Batch sync all hub users to the rewards platform."""
    from services.rewards_sync_service import batch_sync_all_users
    db = deps.db
    summary = await batch_sync_all_users(db)
    return {"success": True, "summary": summary}


@router.post("/admin/sync-user/{user_id}")
async def admin_sync_single_user(
    user_id: str,
    user: dict = Depends(deps.require_admin),
):
    """Admin: Sync a single hub user to the rewards platform."""
    from services.rewards_sync_service import sync_user_to_rewards
    db = deps.db
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    result = await sync_user_to_rewards(db, target)
    return result


@router.get("/admin/sync-status")
async def admin_get_sync_status(
    user: dict = Depends(deps.require_admin),
):
    """Admin: Get sync status between hub and rewards platform."""
    from services.rewards_sync_service import get_sync_status
    db = deps.db
    status = await get_sync_status(db)
    return status



# ─── STREAK FREEZE ENDPOINTS ───

STREAK_FREEZE_COSTS = {
    "trade": 200,    # 200 points per trade streak freeze
    "habit": 150,    # 150 points per habit streak freeze
}

class PurchaseStreakFreezeRequest(BaseModel):
    freeze_type: str  # "trade" or "habit"
    quantity: int = 1


@router.get("/streak-freezes")
async def get_streak_freezes(user: dict = Depends(deps.get_current_user)):
    """Get user's available streak freezes and purchase history."""
    db = deps.db
    user_id = user["id"]

    inventory = await db.streak_freezes.find_one(
        {"user_id": user_id}, {"_id": 0}
    )

    if not inventory:
        inventory = {
            "user_id": user_id,
            "trade_freezes": 0,
            "habit_freezes": 0,
            "trade_freezes_used": 0,
            "habit_freezes_used": 0,
        }

    # Get recent usage history
    usage = await db.streak_freeze_usage.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("used_at", -1).limit(20).to_list(20)

    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})

    return {
        "trade_freezes": inventory.get("trade_freezes", 0),
        "habit_freezes": inventory.get("habit_freezes", 0),
        "trade_freezes_used": inventory.get("trade_freezes_used", 0),
        "habit_freezes_used": inventory.get("habit_freezes_used", 0),
        "costs": STREAK_FREEZE_COSTS,
        "available_points": stats.get("lifetime_points", 0) if stats else 0,
        "usage_history": usage,
    }


@router.post("/streak-freezes/purchase")
async def purchase_streak_freeze(
    req: PurchaseStreakFreezeRequest,
    user: dict = Depends(deps.get_current_user),
):
    """Purchase streak freezes using reward points."""
    db = deps.db
    user_id = user["id"]

    if req.freeze_type not in STREAK_FREEZE_COSTS:
        raise HTTPException(status_code=400, detail="Invalid freeze type. Use 'trade' or 'habit'.")

    if req.quantity < 1 or req.quantity > 10:
        raise HTTPException(status_code=400, detail="Quantity must be between 1 and 10.")

    cost_per = STREAK_FREEZE_COSTS[req.freeze_type]
    total_cost = cost_per * req.quantity

    # Check balance
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    current_points = stats.get("lifetime_points", 0) if stats else 0

    if current_points < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient points. Need {total_cost} but have {current_points}."
        )

    # Deduct points
    await deduct_points(db, user_id, total_cost, "streak_freeze_purchase", {
        "freeze_type": req.freeze_type,
        "quantity": req.quantity,
        "cost_per": cost_per,
    })

    # Add freezes to inventory
    field = f"{req.freeze_type}_freezes"
    await db.streak_freezes.update_one(
        {"user_id": user_id},
        {
            "$inc": {field: req.quantity},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()},
        },
        upsert=True,
    )

    updated = await db.streak_freezes.find_one({"user_id": user_id}, {"_id": 0})

    return {
        "success": True,
        "purchased": req.quantity,
        "freeze_type": req.freeze_type,
        "points_spent": total_cost,
        "trade_freezes": updated.get("trade_freezes", 0),
        "habit_freezes": updated.get("habit_freezes", 0),
    }


async def use_streak_freeze(db, user_id: str, freeze_type: str, date_str: str) -> bool:
    """Attempt to consume one streak freeze for a missed day. Returns True if successful."""
    field = f"{freeze_type}_freezes"
    used_field = f"{freeze_type}_freezes_used"

    inventory = await db.streak_freezes.find_one({"user_id": user_id}, {"_id": 0})
    if not inventory or inventory.get(field, 0) <= 0:
        return False

    # Check if already used a freeze for this date
    existing = await db.streak_freeze_usage.find_one({
        "user_id": user_id,
        "freeze_type": freeze_type,
        "date": date_str,
    })
    if existing:
        return True  # Already frozen for this date

    # Consume one freeze
    await db.streak_freezes.update_one(
        {"user_id": user_id, field: {"$gt": 0}},
        {
            "$inc": {field: -1, used_field: 1},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )

    # Log usage
    await db.streak_freeze_usage.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "freeze_type": freeze_type,
        "date": date_str,
        "used_at": datetime.now(timezone.utc).isoformat(),
    })

    return True


async def check_freeze_for_date(db, user_id: str, freeze_type: str, date_str: str) -> bool:
    """Check if a streak freeze was used for a specific date (without consuming)."""
    existing = await db.streak_freeze_usage.find_one({
        "user_id": user_id,
        "freeze_type": freeze_type,
        "date": date_str,
    })
    return existing is not None


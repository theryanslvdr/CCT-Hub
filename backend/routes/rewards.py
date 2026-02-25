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
        "store_url": f"https://rewards.crosscur.rent/store?token={token}",
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


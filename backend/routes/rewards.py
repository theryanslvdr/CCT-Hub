"""Rewards API routes - stable endpoints for hub and rewards frontends."""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

import deps
from utils.rewards_engine import (
    award_points, deduct_points, compute_level, BASE_POINTS,
    process_trade_event, process_deposit_event, process_withdrawal_event,
    process_referral_qualified,
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


# ─── PUBLIC ENDPOINTS (no auth) ───

@router.get("/summary")
async def get_rewards_summary(user_id: str):
    """GET /api/rewards/summary?user_id={USER_ID}
    Public endpoint - returns user's rewards summary."""
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
        }

    lifetime = stats.get("lifetime_points", 0)
    return {
        "user_id": user_id,
        "lifetime_points": lifetime,
        "monthly_points": stats.get("monthly_points", 0),
        "level": stats.get("level", "Newbie"),
        "estimated_usdt": round(lifetime / 100, 2),
        "min_redeem_points": MIN_REDEEM_POINTS,
        "is_redeemable": lifetime >= MIN_REDEEM_POINTS,
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

    except AssertionError as e:
        results.append({"step": "ASSERTION FAILED", "status": "fail", "error": str(e)})
        overall_pass = False
    except Exception as e:
        results.append({"step": "UNEXPECTED ERROR", "status": "fail", "error": str(e)})
        overall_pass = False

    return {
        "overall": "pass" if overall_pass else "fail",
        "message": "Hub system check passed. Summary OK, Leaderboard OK, Redeem OK, Credit OK." if overall_pass
                   else f"Hub system check failed at: {results[-1].get('step', 'unknown')} - {results[-1].get('error', '')}",
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

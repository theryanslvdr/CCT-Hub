"""Rewards engine - points calculation, level computation, leaderboard logic."""
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

logger = logging.getLogger("server")

# ─── LEVEL DEFINITIONS ───
LEVELS = [
    {"name": "Newbie", "order": 1, "check": lambda s: True},
    {"name": "Trader", "order": 2, "check": lambda s: s.get("lifetime_trades", 0) >= 1},
    {"name": "Investor", "order": 3, "check": lambda s: s.get("lifetime_deposit_usdt", 0) >= 10},
    {"name": "Connector", "order": 4, "check": lambda s: s.get("qualified_referrals", 0) >= 1},
    {"name": "Trade Novice", "order": 5, "check": lambda s: s.get("distinct_trade_days", 0) >= 5},
    {"name": "Amateur Trader", "order": 6, "check": lambda s: s.get("trades_last_30d", 0) >= 12},
    {"name": "Seasoned Trader", "order": 7, "check": lambda s: (
        s.get("lifetime_trades", 0) >= 50 and s.get("lifetime_deposit_usdt", 0) >= 100
    )},
    {"name": "Pro Trader", "order": 8, "check": lambda s: (
        s.get("lifetime_trades", 0) >= 200 and s.get("lifetime_deposit_usdt", 0) >= 500
    )},
    {"name": "Elite", "order": 9, "check": lambda s: (
        s.get("lifetime_trades", 0) >= 500 and
        s.get("lifetime_deposit_usdt", 0) >= 1000 and
        s.get("qualified_referrals", 0) >= 5
    )},
]

# ─── BASE POINT VALUES ───
BASE_POINTS = {
    "signup_verify": 25,
    "join_community": 5,
    "first_trade": 25,
    "first_daily_win": 10,
    "help_chat": 5,           # per interaction, cap 25/day
    "help_chat_daily_cap": 25,
    "qualified_referral": 150,
    "deposit_per_50_usdt": 50,
    "withdrawal_per_15_usdt": 5,
    "streak_5_day": 50,
    "milestone_10_trade": 125,
    "milestone_20_trade_streak": 20,
}


def compute_level(stats: dict) -> str:
    """Compute the highest level a user qualifies for."""
    highest = "Newbie"
    for lvl in LEVELS:
        if lvl["check"](stats):
            highest = lvl["name"]
    return highest


def calc_deposit_points(amount_usdt: float) -> int:
    """Points for a deposit: 50 pts per 50 USDT, pro-rated."""
    if amount_usdt <= 0:
        return 0
    return int((amount_usdt / 50) * BASE_POINTS["deposit_per_50_usdt"])


def calc_withdrawal_points(amount_usdt: float, recent_deposit_within_48h: bool = False) -> int:
    """Points for a withdrawal: 5 pts per 15 USDT. No points if full withdrawal within 48h of deposit."""
    if amount_usdt <= 0 or recent_deposit_within_48h:
        return 0
    return int((amount_usdt / 15) * BASE_POINTS["withdrawal_per_15_usdt"])


async def get_active_multiplier(db, action: str) -> float:
    """Get the effective multiplier for an action based on active promotions."""
    now = datetime.now(timezone.utc).isoformat()
    promo = await db.rewards_promotions.find_one({
        "is_active": True,
        "start_date": {"$lte": now},
        "end_date": {"$gte": now},
        "type": "seasonal",
    }, {"_id": 0})

    if promo and promo.get("rules_json", {}).get(action):
        return promo.get("multiplier", 1.0)
    return 1.0


async def award_points(db, user_id: str, base_points: int, source: str, metadata: dict = None):
    """Award points to a user, applying any active seasonal multiplier.
    Updates stats, logs the event, and refreshes the leaderboard."""
    multiplier = await get_active_multiplier(db, source)
    effective_points = int(base_points * multiplier)

    now = datetime.now(timezone.utc)
    month_key = now.strftime("%Y-%m")

    # Upsert account stats
    await db.rewards_stats.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "lifetime_points": effective_points,
                "monthly_points": effective_points,
            },
            "$set": {"updated_at": now.isoformat()},
            "$setOnInsert": {
                "user_id": user_id,
                "level": "Newbie",
                "lifetime_deposit_usdt": 0,
                "lifetime_withdraw_usdt": 0,
                "lifetime_trades": 0,
                "current_streak_days": 0,
                "best_streak_days": 0,
                "last_trade_date": None,
                "distinct_trade_days": 0,
                "qualified_referrals": 0,
                "trades_last_30d": 0,
                "current_month": month_key,
                "created_at": now.isoformat(),
            },
        },
        upsert=True,
    )

    # Reset monthly points if month changed
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    if stats and stats.get("current_month") != month_key:
        await db.rewards_stats.update_one(
            {"user_id": user_id},
            {"$set": {"monthly_points": effective_points, "current_month": month_key}},
        )

    # Point log (audit trail)
    await db.rewards_point_logs.insert_one({
        "user_id": user_id,
        "points": effective_points,
        "base_points": base_points,
        "multiplier": multiplier,
        "source": source,
        "metadata": metadata or {},
        "created_at": now.isoformat(),
    })

    # Recompute level
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    if stats:
        new_level = compute_level(stats)
        if new_level != stats.get("level"):
            await db.rewards_stats.update_one(
                {"user_id": user_id},
                {"$set": {"level": new_level}},
            )

    # Update leaderboard
    await refresh_leaderboard(db, user_id, month_key)

    return effective_points


async def deduct_points(db, user_id: str, points: int, source: str, metadata: dict = None):
    """Deduct points from a user (for redemptions)."""
    now = datetime.now(timezone.utc)

    await db.rewards_stats.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "lifetime_points": -points,
                "monthly_points": -points,
            },
            "$set": {"updated_at": now.isoformat()},
        },
    )

    # Ensure points don't go negative
    await db.rewards_stats.update_one(
        {"user_id": user_id, "lifetime_points": {"$lt": 0}},
        {"$set": {"lifetime_points": 0}},
    )
    await db.rewards_stats.update_one(
        {"user_id": user_id, "monthly_points": {"$lt": 0}},
        {"$set": {"monthly_points": 0}},
    )

    # Point log
    await db.rewards_point_logs.insert_one({
        "user_id": user_id,
        "points": -points,
        "base_points": -points,
        "multiplier": 1.0,
        "source": source,
        "metadata": metadata or {},
        "created_at": now.isoformat(),
    })

    # Update leaderboard
    month_key = now.strftime("%Y-%m")
    await refresh_leaderboard(db, user_id, month_key)


async def refresh_leaderboard(db, user_id: str, month_key: str):
    """Update a user's leaderboard entry and recompute ranks for the month."""
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    if not stats:
        return

    monthly_pts = stats.get("monthly_points", 0)

    # Upsert this user's snapshot
    await db.rewards_leaderboard.update_one(
        {"user_id": user_id, "month": month_key},
        {
            "$set": {
                "monthly_points": monthly_pts,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            "$setOnInsert": {
                "user_id": user_id,
                "month": month_key,
                "rank": 0,
            },
        },
        upsert=True,
    )

    # Recompute all ranks for this month
    entries = await db.rewards_leaderboard.find(
        {"month": month_key},
        {"_id": 0, "user_id": 1, "monthly_points": 1},
    ).sort("monthly_points", -1).to_list(10000)

    for i, entry in enumerate(entries):
        await db.rewards_leaderboard.update_one(
            {"user_id": entry["user_id"], "month": month_key},
            {"$set": {"rank": i + 1}},
        )


async def process_trade_event(db, user_id: str):
    """Process a trade event: update stats, check streaks/milestones, award points."""
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    month_key = now.strftime("%Y-%m")

    # Ensure stats exist
    stats = await db.rewards_stats.find_one({"user_id": user_id})
    if not stats:
        await db.rewards_stats.insert_one({
            "user_id": user_id,
            "lifetime_points": 0,
            "monthly_points": 0,
            "level": "Newbie",
            "lifetime_deposit_usdt": 0,
            "lifetime_withdraw_usdt": 0,
            "lifetime_trades": 0,
            "current_streak_days": 0,
            "best_streak_days": 0,
            "last_trade_date": None,
            "distinct_trade_days": 0,
            "qualified_referrals": 0,
            "trades_last_30d": 0,
            "current_month": month_key,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })
        stats = await db.rewards_stats.find_one({"user_id": user_id})

    last_trade = stats.get("last_trade_date")
    lifetime_trades = stats.get("lifetime_trades", 0) + 1

    # Streak logic
    streak = stats.get("current_streak_days", 0)
    if last_trade:
        last_dt = datetime.strptime(last_trade, "%Y-%m-%d")
        diff = (now.date() - last_dt.date()).days
        if diff == 1:
            streak += 1
        elif diff == 0:
            pass  # Same day, no streak change
        else:
            streak = 1
    else:
        streak = 1

    best_streak = max(stats.get("best_streak_days", 0), streak)

    # Count distinct trade days
    distinct_days = stats.get("distinct_trade_days", 0)
    if last_trade != today_str:
        distinct_days += 1

    update_fields = {
        "lifetime_trades": lifetime_trades,
        "current_streak_days": streak,
        "best_streak_days": best_streak,
        "last_trade_date": today_str,
        "distinct_trade_days": distinct_days,
        "trades_last_30d": stats.get("trades_last_30d", 0) + 1,
        "updated_at": now.isoformat(),
    }

    await db.rewards_stats.update_one(
        {"user_id": user_id},
        {"$set": update_fields},
    )

    # First trade bonus
    if lifetime_trades == 1:
        await award_points(db, user_id, BASE_POINTS["first_trade"], "first_trade")

    # 5-day streak bonus
    if streak > 0 and streak % 5 == 0:
        await award_points(db, user_id, BASE_POINTS["streak_5_day"], "streak_5_day",
                           {"streak_days": streak})

    # 10-trade milestone
    if lifetime_trades == 10:
        await award_points(db, user_id, BASE_POINTS["milestone_10_trade"], "milestone_10_trade")

    # 20-trade-and-up milestones
    if lifetime_trades > 10 and lifetime_trades % 20 == 0:
        await award_points(db, user_id, BASE_POINTS["milestone_20_trade_streak"], "milestone_20_trade_streak",
                           {"total_trades": lifetime_trades})


async def process_deposit_event(db, user_id: str, amount_usdt: float):
    """Process a deposit event: update stats and award points."""
    now = datetime.now(timezone.utc)

    await db.rewards_stats.update_one(
        {"user_id": user_id},
        {
            "$inc": {"lifetime_deposit_usdt": amount_usdt},
            "$set": {"updated_at": now.isoformat()},
            "$setOnInsert": {
                "user_id": user_id,
                "lifetime_points": 0,
                "monthly_points": 0,
                "level": "Newbie",
                "lifetime_withdraw_usdt": 0,
                "lifetime_trades": 0,
                "current_streak_days": 0,
                "best_streak_days": 0,
                "last_trade_date": None,
                "distinct_trade_days": 0,
                "qualified_referrals": 0,
                "trades_last_30d": 0,
                "current_month": now.strftime("%Y-%m"),
                "created_at": now.isoformat(),
            },
        },
        upsert=True,
    )

    pts = calc_deposit_points(amount_usdt)
    if pts > 0:
        await award_points(db, user_id, pts, "deposit", {"amount_usdt": amount_usdt})

    # Recompute level
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    if stats:
        new_level = compute_level(stats)
        await db.rewards_stats.update_one({"user_id": user_id}, {"$set": {"level": new_level}})


async def process_withdrawal_event(db, user_id: str, amount_usdt: float, recent_deposit_within_48h: bool = False):
    """Process a withdrawal event."""
    now = datetime.now(timezone.utc)

    await db.rewards_stats.update_one(
        {"user_id": user_id},
        {
            "$inc": {"lifetime_withdraw_usdt": amount_usdt},
            "$set": {"updated_at": now.isoformat()},
        },
    )

    pts = calc_withdrawal_points(amount_usdt, recent_deposit_within_48h)
    if pts > 0:
        await award_points(db, user_id, pts, "withdrawal", {"amount_usdt": amount_usdt})


async def process_referral_qualified(db, inviter_id: str, invitee_id: str):
    """Award points for a qualified referral."""
    await db.rewards_stats.update_one(
        {"user_id": inviter_id},
        {
            "$inc": {"qualified_referrals": 1},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    await award_points(db, inviter_id, BASE_POINTS["qualified_referral"], "qualified_referral",
                       {"invitee_id": invitee_id})

    # Recompute level
    stats = await db.rewards_stats.find_one({"user_id": inviter_id}, {"_id": 0})
    if stats:
        new_level = compute_level(stats)
        await db.rewards_stats.update_one({"user_id": inviter_id}, {"$set": {"level": new_level}})

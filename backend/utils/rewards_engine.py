"""Rewards engine - points calculation, level computation, leaderboard logic, badges."""
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging
import uuid

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

    # Check and award any new badges
    await check_and_award_badges(db, user_id)


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

    # Check and award any new badges
    await check_and_award_badges(db, user_id)


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

    # Check and award any new badges
    await check_and_award_badges(db, inviter_id)


# ─── DEFAULT BADGE DEFINITIONS ───
DEFAULT_BADGES = [
    # Trading milestones
    {"id": "first_trade", "name": "First Trade", "description": "Complete your first trade", "icon": "trending-up", "category": "trading", "condition_type": "trade_count", "condition_value": 1, "sort_order": 1},
    {"id": "trades_10", "name": "Getting Started", "description": "Complete 10 trades", "icon": "target", "category": "trading", "condition_type": "trade_count", "condition_value": 10, "sort_order": 2},
    {"id": "trades_25", "name": "Quarter Century", "description": "Complete 25 trades", "icon": "target", "category": "trading", "condition_type": "trade_count", "condition_value": 25, "sort_order": 3},
    {"id": "trades_50", "name": "50 Trades Club", "description": "Complete 50 trades", "icon": "target", "category": "trading", "condition_type": "trade_count", "condition_value": 50, "sort_order": 4},
    {"id": "trades_100", "name": "Century Trader", "description": "Complete 100 trades", "icon": "award", "category": "trading", "condition_type": "trade_count", "condition_value": 100, "sort_order": 5},
    {"id": "trades_200", "name": "Trading Veteran", "description": "Complete 200 trades", "icon": "award", "category": "trading", "condition_type": "trade_count", "condition_value": 200, "sort_order": 6},
    {"id": "trades_500", "name": "Trading Legend", "description": "Complete 500 trades", "icon": "crown", "category": "trading", "condition_type": "trade_count", "condition_value": 500, "sort_order": 7},

    # Streak achievements
    {"id": "streak_3", "name": "Streak Starter", "description": "Maintain a 3-day trading streak", "icon": "flame", "category": "streaks", "condition_type": "best_streak", "condition_value": 3, "sort_order": 10},
    {"id": "streak_7", "name": "Streak Master 7", "description": "Maintain a 7-day trading streak", "icon": "flame", "category": "streaks", "condition_type": "best_streak", "condition_value": 7, "sort_order": 11},
    {"id": "streak_14", "name": "Streak Master 14", "description": "Maintain a 14-day trading streak", "icon": "flame", "category": "streaks", "condition_type": "best_streak", "condition_value": 14, "sort_order": 12},
    {"id": "streak_30", "name": "Streak Master 30", "description": "Maintain a 30-day trading streak", "icon": "flame", "category": "streaks", "condition_type": "best_streak", "condition_value": 30, "sort_order": 13},
    {"id": "streak_50", "name": "Streak Champion", "description": "Maintain a 50-day trading streak", "icon": "flame", "category": "streaks", "condition_type": "best_streak", "condition_value": 50, "sort_order": 14},
    {"id": "streak_100", "name": "Streak Legend", "description": "Maintain a 100-day trading streak", "icon": "crown", "category": "streaks", "condition_type": "best_streak", "condition_value": 100, "sort_order": 15},

    # Points milestones
    {"id": "points_100", "name": "Points Rookie", "description": "Earn 100 lifetime points", "icon": "star", "category": "points", "condition_type": "lifetime_points", "condition_value": 100, "sort_order": 20},
    {"id": "points_500", "name": "Points Milestone 500", "description": "Earn 500 lifetime points", "icon": "star", "category": "points", "condition_type": "lifetime_points", "condition_value": 500, "sort_order": 21},
    {"id": "points_1000", "name": "Points Milestone 1K", "description": "Earn 1,000 lifetime points", "icon": "star", "category": "points", "condition_type": "lifetime_points", "condition_value": 1000, "sort_order": 22},
    {"id": "points_5000", "name": "Points Milestone 5K", "description": "Earn 5,000 lifetime points", "icon": "star", "category": "points", "condition_type": "lifetime_points", "condition_value": 5000, "sort_order": 23},
    {"id": "points_10000", "name": "Points Milestone 10K", "description": "Earn 10,000 lifetime points", "icon": "star", "category": "points", "condition_type": "lifetime_points", "condition_value": 10000, "sort_order": 24},

    # Referral achievements
    {"id": "referral_1", "name": "First Referral", "description": "Refer your first qualified member", "icon": "users", "category": "referrals", "condition_type": "referral_count", "condition_value": 1, "sort_order": 30},
    {"id": "referral_3", "name": "Referral Champion", "description": "Refer 3 qualified members", "icon": "users", "category": "referrals", "condition_type": "referral_count", "condition_value": 3, "sort_order": 31},
    {"id": "referral_5", "name": "Referral Pro", "description": "Refer 5 qualified members", "icon": "users", "category": "referrals", "condition_type": "referral_count", "condition_value": 5, "sort_order": 32},
    {"id": "referral_10", "name": "Referral Legend", "description": "Refer 10 qualified members", "icon": "users", "category": "referrals", "condition_type": "referral_count", "condition_value": 10, "sort_order": 33},

    # Deposit achievements
    {"id": "deposit_100", "name": "First Deposit", "description": "Deposit $100 or more total", "icon": "wallet", "category": "deposits", "condition_type": "lifetime_deposit", "condition_value": 100, "sort_order": 40},
    {"id": "deposit_hero", "name": "Deposit Hero", "description": "Deposit $500 or more total", "icon": "wallet", "category": "deposits", "condition_type": "lifetime_deposit", "condition_value": 500, "sort_order": 41},
    {"id": "deposit_1000", "name": "High Roller", "description": "Deposit $1,000 or more total", "icon": "wallet", "category": "deposits", "condition_type": "lifetime_deposit", "condition_value": 1000, "sort_order": 42},
    {"id": "deposit_5000", "name": "Whale", "description": "Deposit $5,000 or more total", "icon": "wallet", "category": "deposits", "condition_type": "lifetime_deposit", "condition_value": 5000, "sort_order": 43},

    # Distinct trading days
    {"id": "days_10", "name": "10 Days Active", "description": "Trade on 10 distinct days", "icon": "calendar", "category": "activity", "condition_type": "distinct_days", "condition_value": 10, "sort_order": 50},
    {"id": "days_30", "name": "Monthly Warrior", "description": "Trade on 30 distinct days", "icon": "calendar", "category": "activity", "condition_type": "distinct_days", "condition_value": 30, "sort_order": 51},
    {"id": "days_50", "name": "50 Days Strong", "description": "Trade on 50 distinct days", "icon": "calendar", "category": "activity", "condition_type": "distinct_days", "condition_value": 50, "sort_order": 52},
    {"id": "days_100", "name": "Centurion", "description": "Trade on 100 distinct days", "icon": "shield", "category": "activity", "condition_type": "distinct_days", "condition_value": 100, "sort_order": 53},

    # Quiz achievements
    {"id": "quiz_10", "name": "Quiz Rookie", "description": "Answer 10 quiz questions correctly", "icon": "book-open", "category": "quizzes", "condition_type": "quiz_correct_count", "condition_value": 10, "sort_order": 60},
    {"id": "quiz_25", "name": "Knowledge Seeker", "description": "Answer 25 quiz questions correctly", "icon": "book-open", "category": "quizzes", "condition_type": "quiz_correct_count", "condition_value": 25, "sort_order": 61},
    {"id": "quiz_50", "name": "Quiz Master", "description": "Answer 50 quiz questions correctly", "icon": "graduation-cap", "category": "quizzes", "condition_type": "quiz_correct_count", "condition_value": 50, "sort_order": 62},
    {"id": "quiz_100", "name": "Quiz Legend", "description": "Answer 100 quiz questions correctly", "icon": "crown", "category": "quizzes", "condition_type": "quiz_correct_count", "condition_value": 100, "sort_order": 63},
]


async def seed_default_badges(db):
    """Seed default badge definitions if they don't exist."""
    for badge in DEFAULT_BADGES:
        existing = await db.rewards_badge_definitions.find_one({"id": badge["id"]})
        if not existing:
            await db.rewards_badge_definitions.insert_one({
                **badge,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })


def _check_badge_condition(condition_type: str, condition_value, stats: dict) -> bool:
    """Check if a user's stats meet a badge condition."""
    val = condition_value
    if isinstance(val, str):
        val = float(val)
    if condition_type == "trade_count":
        return stats.get("lifetime_trades", 0) >= val
    elif condition_type == "best_streak":
        return stats.get("best_streak_days", 0) >= val
    elif condition_type == "lifetime_points":
        return stats.get("lifetime_points", 0) >= val
    elif condition_type == "referral_count":
        return stats.get("qualified_referrals", 0) >= val
    elif condition_type == "lifetime_deposit":
        return stats.get("lifetime_deposit_usdt", 0) >= val
    elif condition_type == "distinct_days":
        return stats.get("distinct_trade_days", 0) >= val
    elif condition_type == "quiz_correct_count":
        return stats.get("quiz_correct_count", 0) >= val
    return False


async def check_and_award_badges(db, user_id: str):
    """Check all active badge definitions and award any newly earned badges.
    Returns list of newly awarded badge names (for notification)."""
    stats = await db.rewards_stats.find_one({"user_id": user_id}, {"_id": 0})
    if not stats:
        return []

    # Get all active badge definitions
    definitions = await db.rewards_badge_definitions.find(
        {"is_active": True}, {"_id": 0}
    ).to_list(100)

    # Get already earned badge IDs
    earned = await db.rewards_user_badges.find(
        {"user_id": user_id}, {"_id": 0, "badge_id": 1}
    ).to_list(100)
    earned_ids = {b["badge_id"] for b in earned}

    newly_awarded = []
    now = datetime.now(timezone.utc).isoformat()

    for badge_def in definitions:
        if badge_def["id"] in earned_ids:
            continue
        if _check_badge_condition(badge_def.get("condition_type", ""), badge_def.get("condition_value", 0), stats):
            await db.rewards_user_badges.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "badge_id": badge_def["id"],
                "badge_name": badge_def["name"],
                "earned_at": now,
            })
            newly_awarded.append(badge_def["name"])

    return newly_awarded


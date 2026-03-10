"""Shared utility for computing trading streak."""
from datetime import datetime, timezone, timedelta


async def compute_trading_streak(db, user_id: str) -> int:
    """Compute the current consecutive trading day streak for a user.
    Skips weekends and holidays (don't break streak).
    """
    # Check for streak reset date
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "streak_reset_date": 1})
    streak_reset_date = user_doc.get("streak_reset_date") if user_doc else None
    streak_reset_filter = None
    if streak_reset_date:
        try:
            reset_date = datetime.strptime(streak_reset_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            streak_reset_filter = reset_date.isoformat()
        except (ValueError, TypeError):
            pass

    # Fetch holidays
    holidays_cursor = db.global_holidays.find({}, {"_id": 0, "date": 1})
    holidays_list = await holidays_cursor.to_list(1000)
    HOLIDAYS = set()
    for h in holidays_list:
        try:
            date_str = h.get("date", "")
            if date_str:
                parts = date_str.split("-")
                if len(parts) == 3:
                    HOLIDAYS.add((int(parts[0]), int(parts[1]), int(parts[2])))
        except (ValueError, IndexError):
            continue

    def is_trading_day(d):
        if d.weekday() >= 5:
            return False
        if (d.year, d.month, d.day) in HOLIDAYS:
            return False
        return True

    def get_previous_trading_day(d):
        prev = d - timedelta(days=1)
        attempts = 0
        while not is_trading_day(prev) and attempts < 14:
            prev -= timedelta(days=1)
            attempts += 1
        return prev if attempts < 14 else None

    # Get trades (excluding "did not trade")
    query = {"user_id": user_id, "did_not_trade": {"$ne": True}}
    if streak_reset_filter:
        query["created_at"] = {"$gt": streak_reset_filter}

    trades = await db.trade_logs.find(
        query, {"_id": 0, "created_at": 1}
    ).sort("created_at", -1).to_list(1000)

    if not trades:
        return 0

    # Build set of traded dates
    traded_dates = set()
    for t in trades:
        ts = t.get("created_at", "")
        if not ts:
            continue
        try:
            td = datetime.fromisoformat(ts.replace('Z', '+00:00')).date() if isinstance(ts, str) else ts.date()
            traded_dates.add(td)
        except (ValueError, AttributeError):
            continue

    # Get streak freezes
    freeze_usage = await db.streak_freeze_usage.find(
        {"user_id": user_id, "freeze_type": "trade"}, {"_id": 0, "date": 1}
    ).to_list(500)
    frozen_dates = {u["date"] for u in freeze_usage}

    # Walk backwards from today
    today = datetime.now(timezone.utc).date()
    check = today

    if not is_trading_day(check):
        prev = get_previous_trading_day(check)
        if prev:
            check = prev
    elif check not in traded_dates and check.isoformat() not in frozen_dates:
        prev = get_previous_trading_day(check)
        if prev:
            check = prev

    streak = 0
    while check is not None:
        if check in traded_dates or check.isoformat() in frozen_dates:
            streak += 1
        else:
            break
        check = get_previous_trading_day(check)
        if check is None or (today - check).days > 400:
            break

    return streak

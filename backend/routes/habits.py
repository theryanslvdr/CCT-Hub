"""Habit Tracker routes - extracted from server.py"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import uuid
import base64
import logging

import deps
from deps import get_current_user, require_admin
from helpers import send_push_to_admins
from utils.trading_days import is_trading_day, get_holidays_for_range

logger = logging.getLogger("server")

router = APIRouter(prefix="/habits", tags=["Habit Tracker"])


class HabitCreate(BaseModel):
    title: str
    description: str = ""
    action_type: str = "generic"
    action_data: str = ""
    is_gate: bool = True
    validity_days: int = 1


@router.get("/")
async def get_habits(user: dict = Depends(get_current_user)):
    """Get all active habits and the user's completion status."""
    db = deps.db
    habits = await db.habits.find({"active": True}, {"_id": 0}).to_list(100)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_date = datetime.strptime(today, "%Y-%m-%d").date()

    # Get today's completions for display
    completions_today = await db.habit_completions.find(
        {"user_id": user["id"], "date": today}, {"_id": 0}
    ).to_list(100)
    completed_ids = {c["habit_id"] for c in completions_today}

    # Check gate unlock: for each gate habit, check if completed within its validity window
    gate_habits = [h for h in habits if h.get("is_gate")]
    gate_unlocked = True
    gate_deadline = None

    if gate_habits:
        gate_unlocked = False
        # Find the best (most recent) valid completion across all gate habits
        for gh in gate_habits:
            validity = gh.get("validity_days", 1)
            window_start = (today_date - timedelta(days=validity - 1)).isoformat()

            recent = await db.habit_completions.find_one(
                {"user_id": user["id"], "habit_id": gh["id"], "date": {"$gte": window_start}},
                {"_id": 0, "date": 1}
            )
            if recent:
                gate_unlocked = True
                # Calculate when this completion expires
                completion_date = datetime.strptime(recent["date"], "%Y-%m-%d").date()
                expires = completion_date + timedelta(days=validity)
                if gate_deadline is None or expires > gate_deadline:
                    gate_deadline = expires

    streak = await _calc_habit_streak(user["id"])

    result = {
        "habits": habits,
        "completions_today": list(completed_ids),
        "gate_unlocked": gate_unlocked,
        "date": today,
        "streak": streak,
    }
    if gate_deadline:
        result["gate_deadline"] = gate_deadline.isoformat()

    return result


@router.get("/streak")
async def get_habit_streak(user: dict = Depends(get_current_user)):
    """Get the user's habit streak info."""
    return await _calc_habit_streak(user["id"])


async def _calc_habit_streak(user_id: str) -> dict:
    """Calculate consecutive trading-day streak for this user.
    
    Weekends and US market holidays are skipped - missing those days
    does NOT break a streak. Streak freezes protect missed trading days.
    """
    db = deps.db
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$date"}},
        {"$sort": {"_id": -1}},
        {"$limit": 400},
    ]
    dates_docs = await db.habit_completions.aggregate(pipeline).to_list(400)
    if not dates_docs:
        return {"current_streak": 0, "longest_streak": 0, "total_days": 0}

    dates = sorted([d["_id"] for d in dates_docs], reverse=True)
    date_set = set(dates)
    today = datetime.now(timezone.utc).date()

    # Pre-compute holidays for the range of dates we're checking
    min_year = min(int(d[:4]) for d in dates)
    holidays = get_holidays_for_range(min_year, today.year + 1)

    # Get streak freeze usage for habit type
    freeze_usage = await db.streak_freeze_usage.find(
        {"user_id": user_id, "freeze_type": "habit"},
        {"_id": 0, "date": 1}
    ).to_list(500)
    frozen_dates = {u["date"] for u in freeze_usage}

    def _prev_trading_day(d):
        """Get the previous trading day (skip weekends and holidays)."""
        d = d - timedelta(days=1)
        while d.weekday() >= 5 or d.isoformat() in holidays:
            d = d - timedelta(days=1)
        return d

    def _is_trading_day(d):
        return d.weekday() < 5 and d.isoformat() not in holidays

    def _is_covered(d):
        """Check if a date is covered by completion or freeze."""
        return d.isoformat() in date_set or d.isoformat() in frozen_dates

    # Current streak: count backwards from today, skipping non-trading days
    current_streak = 0
    check_date = today

    # If today is not a trading day, move to the last trading day
    if not _is_trading_day(check_date):
        check_date = _prev_trading_day(check_date + timedelta(days=1))

    # If user hasn't completed today and no freeze, check previous trading day
    if not _is_covered(check_date):
        prev_td = _prev_trading_day(check_date)
        if _is_covered(prev_td):
            check_date = prev_td
        else:
            current_streak = 0
            check_date = None

    if check_date is not None:
        while _is_covered(check_date):
            current_streak += 1
            check_date = _prev_trading_day(check_date)

    # Longest streak: count consecutive trading days in sorted order
    # Include frozen dates in the calculation
    all_covered = sorted(set(
        [datetime.strptime(d, "%Y-%m-%d").date() for d in dates] +
        [datetime.strptime(d, "%Y-%m-%d").date() for d in frozen_dates]
    ))
    longest = 0
    run = 0
    for i, d in enumerate(all_covered):
        if i == 0:
            run = 1
        else:
            prev = all_covered[i - 1]
            expected_next = prev + timedelta(days=1)
            # Skip non-trading days between prev and d
            while expected_next < d and (expected_next.weekday() >= 5 or expected_next.isoformat() in holidays):
                expected_next += timedelta(days=1)
            if expected_next == d:
                run += 1
            else:
                run = 1
        longest = max(longest, run)

    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "total_days": len(dates),
    }


class HabitCompleteRequest(BaseModel):
    screenshot_url: str = ""

@router.post("/{habit_id}/complete")
async def complete_habit(habit_id: str, data: HabitCompleteRequest = None, screenshot_url: str = "", user: dict = Depends(get_current_user)):
    """Mark a habit as completed for today."""
    # Support both body and query param for backward compatibility
    effective_screenshot_url = (data.screenshot_url if data and data.screenshot_url else screenshot_url) or ""
    db = deps.db
    habit = await db.habits.find_one({"id": habit_id, "active": True}, {"_id": 0})
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = await db.habit_completions.find_one(
        {"user_id": user["id"], "habit_id": habit_id, "date": today}
    )
    if existing:
        return {"message": "Already completed today", "already": True}

    await db.habit_completions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "habit_id": habit_id,
        "date": today,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "screenshot_url": effective_screenshot_url,
    })

    try:
        user_name = user.get("full_name", "A member")
        habit_title = habit.get("title", "a habit")
        await send_push_to_admins(
            title=f"{user_name} completed a habit",
            body=f'Completed "{habit_title}"',
            url="/dashboard",
            tag=f"habit-{user['id']}-{today}",
        )
    except Exception as e:
        logger.warning(f"Failed to send admin push for habit completion: {e}")

    return {"message": "Habit completed!", "already": False}


@router.post("/upload-screenshot")
async def upload_habit_screenshot(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload a screenshot for habit completion proof. Stores as base64 data URL."""
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    b64 = base64.b64encode(contents).decode()
    content_type = file.content_type or "image/png"
    data_url = f"data:{content_type};base64,{b64}"
    return {"url": data_url}


@router.post("/{habit_id}/uncomplete")
async def uncomplete_habit(habit_id: str, user: dict = Depends(get_current_user)):
    """Undo a habit completion for today."""
    db = deps.db
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await db.habit_completions.delete_one(
        {"user_id": user["id"], "habit_id": habit_id, "date": today}
    )
    return {"message": "Habit unmarked"}
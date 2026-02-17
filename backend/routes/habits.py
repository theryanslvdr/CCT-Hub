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
    """Calculate consecutive days this user completed at least one habit."""
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
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    current_streak = 0
    check_date = datetime.strptime(today_str, "%Y-%m-%d").date()
    if dates[0] != today_str:
        yesterday = (check_date - timedelta(days=1)).isoformat()
        if dates[0] != yesterday:
            current_streak = 0
        else:
            check_date = check_date - timedelta(days=1)

    date_set = set(dates)
    while check_date.isoformat() in date_set:
        current_streak += 1
        check_date -= timedelta(days=1)

    longest = 0
    run = 0
    all_dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in dates])
    for i, d in enumerate(all_dates):
        if i == 0 or (d - all_dates[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)

    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "total_days": len(dates),
    }


@router.post("/{habit_id}/complete")
async def complete_habit(habit_id: str, screenshot_url: str = "", user: dict = Depends(get_current_user)):
    """Mark a habit as completed for today."""
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
        "screenshot_url": screenshot_url,
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
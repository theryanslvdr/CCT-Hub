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
    all_habits = await db.habits.find({"active": True}, {"_id": 0}).to_list(100)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_date = datetime.strptime(today, "%Y-%m-%d").date()
    today_day = today_date.strftime("%A").lower()  # "monday", "tuesday", etc.

    # Filter: show only habits for today (daily habits + matching day_of_week)
    habits = [
        h for h in all_habits
        if not h.get("day_of_week") or h.get("day_of_week") == today_day
    ]

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

    # Check if screenshot is required
    if habit.get("requires_screenshot", False) and not effective_screenshot_url:
        raise HTTPException(status_code=400, detail="Screenshot proof is required for this habit")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = await db.habit_completions.find_one(
        {"user_id": user["id"], "habit_id": habit_id, "date": today}
    )
    if existing:
        return {"message": "Already completed today", "already": True}

    completion_id = str(uuid.uuid4())
    await db.habit_completions.insert_one({
        "id": completion_id,
        "user_id": user["id"],
        "habit_id": habit_id,
        "date": today,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "screenshot_url": effective_screenshot_url,
    })

    # AI Visual Review — auto-flag suspicious screenshots
    if effective_screenshot_url:
        try:
            await _ai_review_screenshot(db, completion_id, effective_screenshot_url, user["id"], habit.get("title", ""))
        except Exception as e:
            logger.warning(f"AI screenshot review failed (non-blocking): {e}")

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

    # Award habit reward points (auto-scales with streak)
    reward_info = None
    try:
        from routes.referral_routes import _award_habit_points
        reward_info = await _award_habit_points(user["id"])
    except Exception as e:
        logger.warning(f"Failed to award habit points: {e}")

    return {"message": "Habit completed!", "already": False, "reward": reward_info}


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


# ─── Social Media Growth Engine ───

@router.get("/social-tasks")
async def get_social_tasks(user: dict = Depends(get_current_user)):
    """Get AI-generated daily social media growth tasks based on streak level."""
    from services.ai_service import call_llm
    db = deps.db

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    streak_data = await _calc_habit_streak(user["id"])
    streak = streak_data.get("current_streak", 0)

    # Determine level based on streak
    if streak >= 100:
        level = 7
        level_name = "Community Leader"
    elif streak >= 80:
        level = 6
        level_name = "Growth Hacker"
    elif streak >= 60:
        level = 5
        level_name = "Brand Ambassador"
    elif streak >= 46:
        level = 4
        level_name = "Thought Leader"
    elif streak >= 22:
        level = 3
        level_name = "Content Creator"
    elif streak >= 8:
        level = 2
        level_name = "Active Engager"
    else:
        level = 1
        level_name = "Getting Started"

    # Check for existing tasks today
    existing = await db.social_tasks.find(
        {"user_id": user["id"], "date": today}, {"_id": 0}
    ).to_list(10)

    if existing:
        return {
            "tasks": existing,
            "level": level,
            "level_name": level_name,
            "streak": streak,
            "date": today,
            "next_level_at": _next_level_streak(level),
        }

    # Task count scales with level: L1-3 = 3 tasks, L4-5 = 4 tasks, L6-7 = 5 tasks
    task_count = 3 if level <= 3 else 4 if level <= 5 else 5

    # Generate tasks via AI
    level_descriptions = {
        1: "Easy social media tasks for a beginner: liking trading posts, following key accounts, browsing trading forums. Max 5 minutes each.",
        2: "Medium engagement tasks: commenting on trading discussions, sharing useful content, engaging with trading communities, asking questions in groups. Max 10 minutes each.",
        3: "Content creation tasks: sharing trading insights, posting about personal trading journey, creating short educational content, tagging relevant people. Max 15 minutes each.",
        4: "Thought leadership: creating original trading tips, hosting discussions, creating educational threads, doing live Q&As, inviting friends to explore trading. Max 20 minutes each.",
        5: "Ambassador tasks: writing testimonials, recording short video reviews, reaching out via DMs to people who might benefit from trading, posting comparison/results content. Max 20 minutes each.",
        6: "Growth hacking: creating referral-driven challenges, running mini-campaigns to attract new traders, collaborating with other creators, building a funnel post series. Max 25 minutes each.",
        7: "Community leadership: mentoring newcomers, organizing virtual meetups, creating evergreen resource posts, cross-platform syndication, leading community initiatives. Max 30 minutes each.",
    }

    referral_context = ""
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "referral_code": 1})
    ref_code = (user_doc or {}).get("referral_code")
    if ref_code:
        referral_context = (
            f"\nThis member has referral code '{ref_code}'. "
            "Include at least 1 task that naturally encourages sharing their referral code or inviting people. "
            "Frame it as helping others discover trading, not hard-selling."
        )

    system = (
        "You are a social media growth coach for a trading community. "
        "Your goal is to help members build an authentic personal brand that attracts new members organically. "
        f"Generate exactly {task_count} daily tasks as a JSON array. Each task has: "
        '{"title": "short title", "description": "1-2 sentence instruction", "platform": "Instagram|Twitter|YouTube|TikTok|LinkedIn|Facebook|Any", "task_type": "engage|create|invite|collaborate|lead", "time_estimate": "X min"}\n'
        "Tasks should feel natural and achievable. Mix task types so the member both engages AND creates AND invites. "
        "Vary platforms across tasks. Return ONLY the JSON array, no markdown."
        + referral_context
    )

    prompt = (
        f"Level: {level} ({level_name})\n"
        f"Streak: {streak} days\n"
        f"Task difficulty: {level_descriptions[level]}\n"
        f"Day of week: {datetime.now(timezone.utc).strftime('%A')}\n"
        f"Number of tasks: {task_count}\n\n"
        f"Generate {task_count} social media growth tasks for today."
    )

    result = await call_llm(system, prompt, "habit_tasks", user["id"], today, temperature=0.7)

    tasks = []
    if result:
        import json as json_mod
        try:
            # Handle markdown code blocks
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()
            parsed = json_mod.loads(clean)
            if isinstance(parsed, list):
                for i, t in enumerate(parsed[:task_count]):
                    task = {
                        "id": str(uuid.uuid4()),
                        "user_id": user["id"],
                        "date": today,
                        "title": t.get("title", f"Task {i+1}"),
                        "description": t.get("description", ""),
                        "platform": t.get("platform", "Any"),
                        "task_type": t.get("task_type", "engage"),
                        "time_estimate": t.get("time_estimate", "5 min"),
                        "level": level,
                        "completed": False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    tasks.append(task)
        except (ValueError, TypeError, KeyError):
            pass

    # Fallback if AI failed
    if not tasks:
        fallback_tasks = [
            {"title": "Like 3 trading posts", "description": "Find and like 3 interesting posts about trading on your feed.", "platform": "Any", "task_type": "engage", "time_estimate": "3 min"},
            {"title": "Follow a trader", "description": "Follow one new trading account or influencer.", "platform": "Instagram", "task_type": "engage", "time_estimate": "2 min"},
            {"title": "Share a trading win", "description": "Post a quick update about something positive in your trading journey.", "platform": "Twitter", "task_type": "create", "time_estimate": "5 min"},
        ]
        if level >= 4:
            fallback_tasks.append({"title": "Invite a friend", "description": "Send a DM to someone who might be interested in trading about your experience.", "platform": "Any", "task_type": "invite", "time_estimate": "5 min"})
        if level >= 6:
            fallback_tasks.append({"title": "Collaborate post", "description": "Reach out to another community member to do a joint insight post.", "platform": "LinkedIn", "task_type": "collaborate", "time_estimate": "10 min"})
        for i, ft in enumerate(fallback_tasks[:task_count]):
            tasks.append({
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "date": today,
                "level": level,
                "completed": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **ft,
            })

    # Store tasks in DB
    if tasks:
        await db.social_tasks.insert_many([{**t} for t in tasks])
        # Remove _id from response
        for t in tasks:
            t.pop("_id", None)

    return {
        "tasks": tasks,
        "level": level,
        "level_name": level_name,
        "streak": streak,
        "date": today,
        "next_level_at": _next_level_streak(level),
    }


def _next_level_streak(current_level):
    """Return the streak needed to reach the next level."""
    thresholds = {1: 8, 2: 22, 3: 46, 4: 60, 5: 80, 6: 100, 7: None}
    return thresholds.get(current_level)


@router.post("/social-task/{task_id}/complete")
async def complete_social_task(task_id: str, user: dict = Depends(get_current_user)):
    """Mark a social media growth task as completed."""
    db = deps.db
    result = await db.social_tasks.update_one(
        {"id": task_id, "user_id": user["id"]},
        {"$set": {"completed": True, "completed_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if all 3 tasks completed today — count as a habit completion day
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_tasks = await db.social_tasks.find(
        {"user_id": user["id"], "date": today}, {"_id": 0, "completed": 1}
    ).to_list(10)

    all_done = all(t.get("completed") for t in today_tasks) and len(today_tasks) >= 3

    # Award habit reward points when all social tasks are done
    reward_info = None
    if all_done:
        try:
            from routes.referral_routes import _award_habit_points
            reward_info = await _award_habit_points(user["id"])
        except Exception as e:
            logger.warning(f"Failed to award social task points: {e}")

    return {"message": "Task completed!", "task_id": task_id, "all_done": all_done, "reward": reward_info}


@router.post("/social-task/{task_id}/uncomplete")
async def uncomplete_social_task(task_id: str, user: dict = Depends(get_current_user)):
    """Unmark a social media growth task."""
    db = deps.db
    await db.social_tasks.update_one(
        {"id": task_id, "user_id": user["id"]},
        {"$set": {"completed": False}, "$unset": {"completed_at": ""}},
    )
    return {"message": "Task unmarked"}



# ─── Admin Spot-Check / Proof Verification ───

class SpotCheckAction(BaseModel):
    action: str  # "approve" or "reject"
    reason: str = ""


@router.get("/admin/pending-proofs")
async def get_pending_proofs(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(require_admin),
):
    """Get habit completions with proof screenshots that need admin verification."""
    db = deps.db
    query = {
        "screenshot_url": {"$exists": True, "$ne": ""},
        "verification_status": {"$nin": ["approved"]},
    }
    total = await db.habit_completions.count_documents(query)
    completions = await db.habit_completions.find(
        query, {"_id": 0}
    ).sort("completed_at", -1).skip((page - 1) * page_size).limit(page_size).to_list(page_size)

    # Enrich with user and habit info
    for c in completions:
        u = await db.users.find_one({"id": c.get("user_id")}, {"_id": 0, "full_name": 1, "email": 1})
        c["user_name"] = u.get("full_name", "Unknown") if u else "Unknown"
        c["user_email"] = u.get("email", "") if u else ""
        h = await db.habits.find_one({"id": c.get("habit_id")}, {"_id": 0, "title": 1})
        c["habit_title"] = h.get("title", "Unknown") if h else "Unknown"

    return {"completions": completions, "total": total, "page": page}


@router.post("/admin/spot-check/{completion_id}")
async def admin_spot_check(
    completion_id: str,
    data: SpotCheckAction,
    user: dict = Depends(require_admin),
):
    """Admin approves or rejects a habit completion proof.
    Approved proofs get deleted from storage after marking."""
    db = deps.db
    completion = await db.habit_completions.find_one({"id": completion_id}, {"_id": 0})
    if not completion:
        raise HTTPException(status_code=404, detail="Completion not found")

    if data.action == "approve":
        # Mark as approved and clear the proof (save storage)
        await db.habit_completions.update_one(
            {"id": completion_id},
            {"$set": {
                "verification_status": "approved",
                "verified_by": user["id"],
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }, "$unset": {
                "screenshot_url": "",
            }}
        )
        return {"message": "Proof approved and deleted", "action": "approved"}

    elif data.action == "reject":
        # Reject and remove the completion + proof
        await db.habit_completions.update_one(
            {"id": completion_id},
            {"$set": {
                "verification_status": "rejected",
                "rejection_reason": data.reason,
                "verified_by": user["id"],
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }, "$unset": {
                "screenshot_url": "",
            }}
        )
        # Create/increment fraud warning for the user
        member_id = completion.get("user_id")
        if member_id:
            await create_fraud_warning(db, member_id, data.reason)

        return {"message": "Proof rejected — fraud warning issued", "action": "rejected"}

    raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")


@router.get("/admin/spot-check-stats")
async def spot_check_stats(user: dict = Depends(require_admin)):
    """Get stats on pending, approved, and rejected proofs."""
    db = deps.db
    pending = await db.habit_completions.count_documents({
        "screenshot_url": {"$exists": True, "$ne": ""},
        "verification_status": {"$nin": ["approved", "rejected"]},
    })
    approved = await db.habit_completions.count_documents({"verification_status": "approved"})
    rejected = await db.habit_completions.count_documents({"verification_status": "rejected"})

    return {"pending": pending, "approved": approved, "rejected": rejected}


async def _ai_review_screenshot(db, completion_id: str, screenshot_url: str, user_id: str, habit_title: str):
    """Use AI vision to review a screenshot for suspicious content. Non-blocking."""
    import os
    import httpx
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_key:
        return

    prompt = f"""You are reviewing a screenshot proof for a daily habit: "{habit_title}".
Analyze this image and determine if it appears to be a legitimate screenshot proof of completing this habit.

Flag as SUSPICIOUS if:
- The image is a generic stock photo or unrelated content
- The image appears to be a previously used/recycled screenshot (same layout repeated)
- The image is blurry, cropped to hide details, or clearly manipulated
- The image doesn't relate to the habit described

Respond with ONLY one of:
LEGITIMATE - if it appears to be a genuine proof
SUSPICIOUS - [brief reason] if it looks fraudulent"""

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": screenshot_url}},
                    ]}],
                    "max_tokens": 100,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            result = resp.json()["choices"][0]["message"]["content"].strip()

            is_suspicious = result.upper().startswith("SUSPICIOUS")
            await db.habit_completions.update_one(
                {"id": completion_id},
                {"$set": {
                    "ai_review": result,
                    "ai_flagged": is_suspicious,
                    "ai_reviewed_at": datetime.now(timezone.utc).isoformat(),
                }}
            )
            if is_suspicious:
                logger.info(f"AI flagged screenshot for user {user_id}: {result}")
    except Exception as e:
        logger.warning(f"AI screenshot review error: {e}")



# ─── Fraud Warning System ───

@router.get("/my-warnings")
async def get_my_warnings(user: dict = Depends(get_current_user)):
    """Get fraud warnings for the current user."""
    db = deps.db
    warnings = await db.fraud_warnings.find(
        {"user_id": user["id"], "resolution": {"$ne": "cleared"}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)

    # Count total rejections
    rejection_count = await db.habit_completions.count_documents({
        "user_id": user["id"],
        "verification_status": "rejected"
    })

    active_warning = next((w for w in warnings if w.get("resolution") == "pending"), None)

    return {
        "warnings": warnings,
        "active_warning": active_warning,
        "rejection_count": rejection_count,
    }


@router.post("/acknowledge-warning/{warning_id}")
async def acknowledge_warning(warning_id: str, user: dict = Depends(get_current_user)):
    """Member acknowledges a fraud warning — starts 7-day countdown."""
    db = deps.db
    warning = await db.fraud_warnings.find_one(
        {"id": warning_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not warning:
        raise HTTPException(status_code=404, detail="Warning not found")
    if warning.get("acknowledged"):
        return {"message": "Already acknowledged", "countdown_end": warning.get("countdown_end")}

    countdown_end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    await db.fraud_warnings.update_one(
        {"id": warning_id},
        {"$set": {
            "acknowledged": True,
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
            "countdown_end": countdown_end,
        }}
    )
    return {"message": "Warning acknowledged. You have 7 days to correct your behavior.", "countdown_end": countdown_end}


async def create_fraud_warning(db, user_id: str, reason: str = ""):
    """Create a fraud warning for a user after admin rejects their proof."""
    # Check if there's already an active (pending) warning
    existing = await db.fraud_warnings.find_one(
        {"user_id": user_id, "resolution": "pending"}
    )
    if existing:
        # Increment fraud count on existing warning
        await db.fraud_warnings.update_one(
            {"id": existing["id"]},
            {"$inc": {"fraud_count": 1}, "$set": {"last_rejection_at": datetime.now(timezone.utc).isoformat()}}
        )
        return existing["id"]

    warning = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "fraud_count": 1,
        "acknowledged": False,
        "acknowledged_at": None,
        "countdown_end": None,
        "resolution": "pending",  # pending -> acknowledged -> cleared/suspended
        "last_rejection_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.fraud_warnings.insert_one(warning)
    warning.pop("_id", None)
    return warning["id"]


async def check_and_auto_suspend(db):
    """Check for users whose countdown has expired with continued fraud — auto-suspend them."""
    now = datetime.now(timezone.utc).isoformat()
    # Find acknowledged warnings where countdown has expired
    expired_warnings = await db.fraud_warnings.find(
        {
            "resolution": "pending",
            "acknowledged": True,
            "countdown_end": {"$lte": now},
        },
        {"_id": 0}
    ).to_list(100)

    suspended_count = 0
    for w in expired_warnings:
        user_id = w["user_id"]
        # Check if they had MORE rejections after the warning was acknowledged
        new_rejections = await db.habit_completions.count_documents({
            "user_id": user_id,
            "verification_status": "rejected",
            "verified_at": {"$gte": w.get("acknowledged_at", "")},
        })
        if new_rejections > 0:
            # Auto-suspend
            await db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "is_suspended": True,
                    "suspended_at": now,
                    "suspension_reason": "Auto-suspended: continued fraudulent screenshot submissions after warning",
                    "suspension_type": "permanent",
                }}
            )
            await db.fraud_warnings.update_one(
                {"id": w["id"]},
                {"$set": {"resolution": "suspended", "resolved_at": now}}
            )
            suspended_count += 1
            logger.info(f"Auto-suspended user {user_id} for continued fraud after warning")
        else:
            # Cleared — no new fraud during countdown
            await db.fraud_warnings.update_one(
                {"id": w["id"]},
                {"$set": {"resolution": "cleared", "resolved_at": now}}
            )
            logger.info(f"Fraud warning cleared for user {user_id} — no new fraud during countdown")

    return suspended_count

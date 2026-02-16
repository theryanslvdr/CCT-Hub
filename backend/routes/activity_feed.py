"""Activity Feed routes - extracted from server.py"""
from fastapi import APIRouter, Depends

import deps
from deps import require_admin

admin_activity_router = APIRouter(prefix="/admin", tags=["Admin - Activity Feed"])


@admin_activity_router.get("/activity-feed")
async def get_activity_feed(since: str = "", limit: int = 50, user: dict = Depends(require_admin)):
    """
    Get recent member activities: habit completions, trade logs, profit entries.
    'since' is an ISO timestamp — only return events newer than this for live polling.
    """
    db = deps.db
    activities = []

    # 1. Habit completions
    habit_filter = {}
    if since:
        habit_filter["completed_at"] = {"$gt": since}
    habit_completions = await db.habit_completions.find(
        habit_filter, {"_id": 0}
    ).sort("completed_at", -1).limit(limit).to_list(limit)

    # Get user names and habit titles in bulk
    user_ids = list({hc["user_id"] for hc in habit_completions})
    habit_ids = list({hc["habit_id"] for hc in habit_completions})
    users_map = {}
    if user_ids:
        users_list = await db.users.find(
            {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "full_name": 1}
        ).to_list(200)
        users_map = {u["id"]: u["full_name"] for u in users_list}
    habits_map = {}
    if habit_ids:
        habits_list = await db.habits.find(
            {"id": {"$in": habit_ids}}, {"_id": 0, "id": 1, "title": 1}
        ).to_list(200)
        habits_map = {h["id"]: h["title"] for h in habits_list}

    for hc in habit_completions:
        activities.append({
            "type": "habit_completed",
            "user_id": hc["user_id"],
            "user_name": users_map.get(hc["user_id"], "Unknown"),
            "detail": habits_map.get(hc["habit_id"], "Unknown Habit"),
            "screenshot_url": hc.get("screenshot_url", ""),
            "timestamp": hc.get("completed_at", ""),
        })

    # 2. Trade logs (recent)
    trade_filter = {}
    if since:
        trade_filter["created_at"] = {"$gt": since}
    trade_logs = await db.trade_logs.find(
        trade_filter, {"_id": 0, "user_id": 1, "user_name": 1, "actual_profit": 1, "created_at": 1, "trade_type": 1}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    # Resolve missing user_name in trade logs
    trade_user_ids = [tl["user_id"] for tl in trade_logs if not tl.get("user_name") and tl.get("user_id")]
    if trade_user_ids:
        extra_users = await db.users.find(
            {"id": {"$in": list(set(trade_user_ids))}}, {"_id": 0, "id": 1, "full_name": 1}
        ).to_list(200)
        for u in extra_users:
            users_map[u["id"]] = u["full_name"]

    for tl in trade_logs:
        profit = tl.get("actual_profit", 0)
        trade_type = tl.get("trade_type", "trade")
        if trade_type == "did_not_trade":
            detail = "Marked Did Not Trade"
        elif trade_type == "missed_trade":
            detail = "Logged Missed Trade"
        else:
            detail = f"Logged trade: ${profit:+.2f}" if profit else "Logged trade"
        activities.append({
            "type": "trade_logged",
            "user_id": tl.get("user_id", ""),
            "user_name": tl.get("user_name") or users_map.get(tl.get("user_id", ""), "Unknown"),
            "detail": detail,
            "screenshot_url": "",
            "timestamp": tl.get("created_at", ""),
        })

    # Sort all activities by timestamp desc
    activities.sort(key=lambda a: a.get("timestamp", ""), reverse=True)

    return {"activities": activities[:limit]}

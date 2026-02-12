"""Profit Planner (Goals) routes."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import List
import uuid

from deps import db, get_current_user

router = APIRouter(prefix="/goals", tags=["Profit Planner"])


@router.post("")
async def create_goal(data: dict, user: dict = Depends(get_current_user)):
    from server import GoalCreate, GoalResponse
    parsed = GoalCreate(**data) if isinstance(data, dict) else data
    goal_id = str(uuid.uuid4())
    goal = {
        "id": goal_id,
        "user_id": user["id"],
        "name": parsed.name,
        "target_amount": parsed.target_amount,
        "current_amount": parsed.current_amount,
        "target_date": parsed.target_date.isoformat() if parsed.target_date else None,
        "price_type": parsed.price_type,
        "market_item": parsed.market_item,
        "currency": parsed.currency,
        "contributions": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.goals.insert_one(goal)

    progress = (parsed.current_amount / parsed.target_amount * 100) if parsed.target_amount > 0 else 0
    return GoalResponse(
        **{
            **goal,
            "progress_percentage": round(progress, 2),
            "target_date": datetime.fromisoformat(goal["target_date"]) if goal["target_date"] else None,
            "created_at": datetime.fromisoformat(goal["created_at"]),
        }
    )


@router.get("")
async def get_goals(user: dict = Depends(get_current_user)):
    from server import GoalResponse
    goals = await db.goals.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    result = []
    for g in goals:
        progress = (g["current_amount"] / g["target_amount"] * 100) if g["target_amount"] > 0 else 0
        result.append(
            GoalResponse(
                **{
                    **g,
                    "progress_percentage": round(progress, 2),
                    "target_date": datetime.fromisoformat(g["target_date"]) if g.get("target_date") else None,
                    "created_at": datetime.fromisoformat(g["created_at"])
                    if isinstance(g["created_at"], str)
                    else g["created_at"],
                }
            )
        )
    return result


@router.post("/{goal_id}/contribute")
async def contribute_to_goal(goal_id: str, amount: float, user: dict = Depends(get_current_user)):
    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    new_amount = goal["current_amount"] + amount
    contribution = {
        "id": str(uuid.uuid4()),
        "amount": amount,
        "date": datetime.now(timezone.utc).isoformat(),
    }

    await db.goals.update_one(
        {"id": goal_id},
        {"$set": {"current_amount": new_amount}, "$push": {"contributions": contribution}},
    )

    progress = (new_amount / goal["target_amount"] * 100) if goal["target_amount"] > 0 else 0
    return {
        "message": "Contribution added",
        "new_amount": new_amount,
        "progress_percentage": round(progress, 2),
        "completed": new_amount >= goal["target_amount"],
    }


@router.get("/{goal_id}/plan")
async def get_goal_plan(goal_id: str, user: dict = Depends(get_current_user)):
    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    remaining = goal["target_amount"] - goal["current_amount"]

    deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)

    total_deposits = sum(d["amount"] for d in deposits)
    total_profit = sum(t["actual_profit"] for t in trades)
    account_value = total_deposits + total_profit

    if account_value >= remaining:
        suggestion = {
            "type": "ready",
            "message": f"You have enough to reach your goal! Consider withdrawing ${remaining:.2f}",
        }
    else:
        needed = remaining - account_value
        suggestion = {
            "type": "need_more",
            "message": f"You need ${needed:.2f} more. Keep trading to reach your goal!",
            "trades_needed": int(needed / 15) + 1,
        }

    return {
        "goal_name": goal["name"],
        "target": goal["target_amount"],
        "current": goal["current_amount"],
        "remaining": remaining,
        "account_value": round(account_value, 2),
        "suggestion": suggestion,
    }

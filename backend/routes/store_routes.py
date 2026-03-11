"""Store routes — Signal Gate Immunity Credits and purchasable items."""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import logging

import deps
from deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/store", tags=["store"])

STORE_ITEMS = [
    {
        "id": "immunity_1d",
        "name": "1-Day Gate Immunity",
        "description": "Bypass the habit gate for 1 day. Access signals without completing daily habits.",
        "cost": 50,
        "duration_days": 1,
        "type": "immunity_credit",
    },
    {
        "id": "immunity_3d",
        "name": "3-Day Gate Immunity",
        "description": "Bypass the habit gate for 3 days. Best for weekends or travel.",
        "cost": 120,
        "duration_days": 3,
        "type": "immunity_credit",
    },
    {
        "id": "immunity_7d",
        "name": "7-Day Gate Immunity",
        "description": "Full week of signal access without habit requirements.",
        "cost": 250,
        "duration_days": 7,
        "type": "immunity_credit",
    },
]


@router.get("/items")
async def get_store_items(user: dict = Depends(get_current_user)):
    """Get available store items."""
    db = deps.db
    # Get user's current points
    stats = await db.rewards_stats.find_one({"user_id": user["id"]}, {"_id": 0, "lifetime_points": 1})
    points = (stats or {}).get("lifetime_points", 0)

    # Get active immunity
    active = await db.immunity_credits.find_one(
        {"user_id": user["id"], "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}, "used": True},
        {"_id": 0, "expires_at": 1}
    )

    return {
        "items": STORE_ITEMS,
        "user_points": points,
        "active_immunity": active,
    }


class PurchaseRequest(BaseModel):
    item_id: str


@router.post("/purchase")
async def purchase_item(data: PurchaseRequest, user: dict = Depends(get_current_user)):
    """Purchase a store item with reward points."""
    db = deps.db

    # Find the item
    item = next((i for i in STORE_ITEMS if i["id"] == data.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Check points balance
    stats = await db.rewards_stats.find_one({"user_id": user["id"]}, {"_id": 0, "lifetime_points": 1})
    points = (stats or {}).get("lifetime_points", 0)
    if points < item["cost"]:
        raise HTTPException(status_code=400, detail=f"Insufficient points. Need {item['cost']}, have {points}")

    # Deduct points
    await db.rewards_stats.update_one(
        {"user_id": user["id"]},
        {"$inc": {"lifetime_points": -item["cost"]}}
    )

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=item["duration_days"])

    # Create immunity credit
    credit = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "item_id": item["id"],
        "item_name": item["name"],
        "cost": item["cost"],
        "duration_days": item["duration_days"],
        "purchased_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "used": True,
    }
    await db.immunity_credits.insert_one(credit)
    credit.pop("_id", None)

    # Log the purchase
    await db.store_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "item_id": item["id"],
        "item_name": item["name"],
        "points_spent": item["cost"],
        "created_at": now.isoformat(),
    })

    return {
        "message": f"Purchased {item['name']}! Gate immunity active until {expires.strftime('%Y-%m-%d %H:%M')} UTC.",
        "credit": credit,
        "remaining_points": points - item["cost"],
    }


@router.get("/my-credits")
async def get_my_credits(user: dict = Depends(get_current_user)):
    """Get user's active and past immunity credits."""
    db = deps.db
    now = datetime.now(timezone.utc).isoformat()

    active = await db.immunity_credits.find(
        {"user_id": user["id"], "expires_at": {"$gt": now}},
        {"_id": 0}
    ).sort("expires_at", -1).to_list(10)

    history = await db.store_transactions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)

    return {"active_credits": active, "history": history}

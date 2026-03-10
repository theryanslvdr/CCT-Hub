"""User routes - extracted from server.py
Includes: notification preferences, push subscriptions, profile, password change
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict, Optional
import os
import logging
import cloudinary
import cloudinary.uploader

import deps
from deps import get_current_user, hash_password, verify_password

logger = logging.getLogger("server")

router = APIRouter(prefix="/users", tags=["Users"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    lot_size: Optional[float] = None


class NotificationPreferences(BaseModel):
    trading_signal: bool = True
    pre_trade_10min: bool = True
    pre_trade_5min: bool = True
    missed_trade_report: bool = True
    member_trade_submitted: bool = False
    member_missed_trade: bool = False
    member_profit_report: bool = False
    daily_summary: bool = False


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]


DEFAULT_MEMBER_PREFS = {
    "trading_signal": True,
    "pre_trade_10min": True,
    "pre_trade_5min": True,
    "missed_trade_report": True,
}

DEFAULT_ADMIN_PREFS = {
    "trading_signal": True,
    "pre_trade_10min": True,
    "pre_trade_5min": True,
    "missed_trade_report": True,
    "member_trade_submitted": True,
    "member_missed_trade": True,
    "member_profit_report": True,
    "daily_summary": True,
}


@router.get("/notification-preferences")
async def get_notification_preferences(user: dict = Depends(get_current_user)):
    db = deps.db
    prefs = user.get("notification_preferences")
    is_admin = user.get("role") in ["master_admin", "super_admin"]
    defaults = DEFAULT_ADMIN_PREFS if is_admin else DEFAULT_MEMBER_PREFS
    if not prefs:
        return {"preferences": defaults, "is_admin": is_admin}
    merged = {**defaults, **prefs}
    return {"preferences": merged, "is_admin": is_admin}


@router.put("/notification-preferences")
async def update_notification_preferences(data: NotificationPreferences, user: dict = Depends(get_current_user)):
    db = deps.db
    prefs = data.dict()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"notification_preferences": prefs, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Notification preferences updated", "preferences": prefs}


# ==================== PUSH NOTIFICATION ROUTES ====================

@router.post("/push-subscribe")
async def push_subscribe(subscription: PushSubscription, user: dict = Depends(get_current_user)):
    """Subscribe to push notifications"""
    db = deps.db
    sub_data = {
        "user_id": user["id"],
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.push_subscriptions.update_one(
        {"endpoint": subscription.endpoint},
        {"$set": sub_data},
        upsert=True
    )
    return {"message": "Push subscription saved"}


@router.delete("/push-subscribe")
async def push_unsubscribe(subscription: PushSubscription, user: dict = Depends(get_current_user)):
    """Unsubscribe from push notifications"""
    db = deps.db
    await db.push_subscriptions.delete_one({"endpoint": subscription.endpoint, "user_id": user["id"]})
    return {"message": "Push subscription removed"}


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Return VAPID public key for frontend push subscription"""
    key = os.environ.get("VAPID_PUBLIC_KEY", "")
    return {"public_key": key}


# ==================== PROFILE ====================

@router.put("/profile")
async def update_profile(data: ProfileUpdate, user: dict = Depends(get_current_user)):
    db = deps.db
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.full_name:
        update_data["full_name"] = data.full_name
    if data.timezone:
        update_data["timezone"] = data.timezone
    if data.lot_size is not None:
        update_data["lot_size"] = data.lot_size

    await db.users.update_one({"id": user["id"]}, {"$set": update_data})
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0})

    # Auto-sync profile changes to rewards platform
    try:
        from services.rewards_sync_service import sync_user_to_rewards
        full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
        if full_user:
            await sync_user_to_rewards(db, full_user)
    except Exception as e:
        import logging
        logging.getLogger("server").warning(f"Rewards sync on profile update failed: {e}")

    return updated_user


@router.post("/change-password")
async def change_password(data: PasswordChange, user: dict = Depends(get_current_user)):
    db = deps.db
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, full_user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    # Auto-sync password change to rewards platform
    try:
        from services.rewards_sync_service import sync_user_to_rewards
        updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
        if updated_user:
            await sync_user_to_rewards(db, updated_user)
    except Exception as e:
        import logging
        logging.getLogger("server").warning(f"Rewards sync on password change failed: {e}")

    return {"message": "Password changed successfully"}


@router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    db = deps.db
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="crosscurrent/profile-pictures",
            public_id=f"user_{user['id']}",
            overwrite=True
        )
        url = result.get("secure_url")
        await db.users.update_one({"id": user["id"]}, {"$set": {"profile_picture": url}})
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")



@router.get("/member/{member_id}/public")
async def get_public_member_profile(member_id: str, user=Depends(get_current_user)):
    """Get a member's public profile visible to other community members."""
    db = deps.db
    member = await db.users.find_one(
        {"id": member_id},
        {"_id": 0, "password_hash": 0, "push_subscriptions": 0}
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get rewards stats
    reward_stats = await db.rewards_stats.find_one(
        {"user_id": member_id}, {"_id": 0}
    )

    # Get forum activity
    forum_posts = await db.forum_posts.count_documents({"author_id": member_id})
    forum_comments = await db.forum_comments.count_documents({"author_id": member_id})

    # Get habit streak
    habit_stats = await db.habit_streaks.find_one(
        {"user_id": member_id}, {"_id": 0}
    )

    # Get badges
    badges = []
    async for b in db.user_badges.find({"user_id": member_id}, {"_id": 0}).limit(20):
        badges.append(b)

    return {
        "profile": {
            "id": member.get("id"),
            "full_name": member.get("full_name", "Member"),
            "role": member.get("role", "member"),
            "timezone": member.get("timezone"),
            "profile_picture": member.get("profile_picture"),
            "created_at": member.get("created_at"),
            "referral_code": member.get("referral_code"),
        },
        "stats": {
            "level": reward_stats.get("level", "Newbie") if reward_stats else "Newbie",
            "lifetime_points": reward_stats.get("lifetime_points", 0) if reward_stats else 0,
            "current_streak": habit_stats.get("current_streak", 0) if habit_stats else 0,
            "longest_streak": habit_stats.get("longest_streak", 0) if habit_stats else 0,
            "forum_posts": forum_posts,
            "forum_comments": forum_comments,
            "quiz_correct_count": reward_stats.get("quiz_correct_count", 0) if reward_stats else 0,
        },
        "badges": badges,
    }

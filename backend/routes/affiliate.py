"""Affiliate Center routes - extracted from server.py"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

import deps
from deps import get_current_user, require_admin

router = APIRouter(tags=["Affiliate Center"])
admin_affiliate_router = APIRouter(prefix="/admin", tags=["Admin - Affiliate"])


class AffiliateResourceCreate(BaseModel):
    category: str
    title: str
    content: str
    order: int = 0


# ==================== PUBLIC ENDPOINTS ====================

@router.get("/affiliate-resources")
async def get_affiliate_resources(user: dict = Depends(get_current_user)):
    """Get all active affiliate resources for members."""
    db = deps.db
    resources = await db.affiliate_resources.find({"active": True}, {"_id": 0}).sort("order", 1).to_list(200)
    grouped = {}
    for r in resources:
        cat = r.get("category", "other")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(r)
    return {"resources": grouped}


@router.get("/affiliate-chatbase-public")
async def get_affiliate_chatbase_public(user: dict = Depends(get_current_user)):
    """Public endpoint for members to get chatbase embed config."""
    db = deps.db
    settings = await db.platform_settings.find_one({}, {"_id": 0, "chatbase_bot_id": 1, "chatbase_enabled": 1})
    if not settings or not settings.get("chatbase_enabled"):
        return {"enabled": False}
    return {"enabled": True, "bot_id": settings.get("chatbase_bot_id", "")}


# ==================== ADMIN ENDPOINTS ====================

@admin_affiliate_router.get("/affiliate-resources")
async def admin_get_affiliate_resources(user: dict = Depends(require_admin)):
    """Get all affiliate resources for admin management."""
    db = deps.db
    resources = await db.affiliate_resources.find({}, {"_id": 0}).sort("order", 1).to_list(200)
    return {"resources": resources}


@admin_affiliate_router.post("/affiliate-resources")
async def admin_create_affiliate_resource(data: AffiliateResourceCreate, user: dict = Depends(require_admin)):
    """Create a new affiliate resource."""
    db = deps.db
    resource = {
        "id": str(uuid.uuid4()),
        "category": data.category,
        "title": data.title,
        "content": data.content,
        "order": data.order,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.affiliate_resources.insert_one(resource)
    resource.pop("_id", None)
    return resource


@admin_affiliate_router.put("/affiliate-resources/{resource_id}")
async def admin_update_affiliate_resource(resource_id: str, data: AffiliateResourceCreate, user: dict = Depends(require_admin)):
    """Update an affiliate resource."""
    db = deps.db
    result = await db.affiliate_resources.update_one(
        {"id": resource_id},
        {"$set": {"category": data.category, "title": data.title, "content": data.content, "order": data.order}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"message": "Resource updated"}


@admin_affiliate_router.delete("/affiliate-resources/{resource_id}")
async def admin_delete_affiliate_resource(resource_id: str, user: dict = Depends(require_admin)):
    """Delete an affiliate resource."""
    db = deps.db
    await db.affiliate_resources.delete_one({"id": resource_id})
    return {"message": "Resource deleted"}


@admin_affiliate_router.get("/affiliate-chatbase")
async def get_affiliate_chatbase(user: dict = Depends(require_admin)):
    db = deps.db
    settings = await db.platform_settings.find_one({}, {"_id": 0, "chatbase_bot_id": 1, "chatbase_enabled": 1})
    return {
        "bot_id": (settings or {}).get("chatbase_bot_id", ""),
        "enabled": (settings or {}).get("chatbase_enabled", False),
    }


@admin_affiliate_router.put("/affiliate-chatbase")
async def update_affiliate_chatbase(bot_id: str = "", enabled: bool = False, user: dict = Depends(require_admin)):
    db = deps.db
    await db.platform_settings.update_one(
        {}, {"$set": {"chatbase_bot_id": bot_id, "chatbase_enabled": enabled}}, upsert=True
    )
    return {"message": "Chatbase config updated"}

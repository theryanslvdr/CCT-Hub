"""Rewards Platform Sync Service - Syncs hub users to rewards.crosscur.rent"""
import os
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("server")

REWARDS_API_BASE = "https://trade-rewards-1.emergent.host/api/external"
REWARDS_API_KEY = os.environ.get("REWARDS_PLATFORM_API_KEY", "cct_izJiIkSgzqQGiqSr_VZn1icO5Fw7cjMj-zw4OW4LqW4")

# Hub role -> Rewards platform admin mapping
ROLE_MAP = {
    "master_admin": {"is_admin": True, "is_super_admin": True},
    "super_admin": {"is_admin": True, "is_super_admin": True},
    "admin": {"is_admin": True, "is_super_admin": False},
    "basic_admin": {"is_admin": True, "is_super_admin": False},
    "member": {"is_admin": False, "is_super_admin": False},
}


def _headers():
    return {
        "X-API-Key": REWARDS_API_KEY,
        "Content-Type": "application/json",
    }


async def sync_user_to_rewards(db, user: dict) -> dict:
    """Push a single hub user to the rewards platform.
    Uses POST /external/members (creates or updates by email).
    Once the rewards platform adds POST /external/users, this will use that instead.
    """
    email = user.get("email", "")
    name = user.get("full_name", "")
    role = user.get("role", "member")
    hub_id = user.get("id", "")
    password_hash = user.get("password", "")

    admin_flags = ROLE_MAP.get(role, ROLE_MAP["member"])

    payload = {
        "email": email,
        "name": name,
        "hub_user_id": hub_id,
        "source": "hub_sync",
        **admin_flags,
    }

    # Include password hash for credential sync (if the endpoint supports it)
    if password_hash:
        payload["password"] = password_hash

    result = {
        "email": email,
        "name": name,
        "hub_id": hub_id,
        "success": False,
        "action": None,
        "rewards_id": None,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Try POST /external/users first (new endpoint, may not exist yet)
            try:
                resp = await client.post(
                    f"{REWARDS_API_BASE}/users",
                    headers=_headers(),
                    json=payload,
                )
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    result["success"] = True
                    result["action"] = data.get("action", "synced_via_users")
                    result["rewards_id"] = data.get("id")

                    # Store the mapping
                    await _save_sync_mapping(db, hub_id, data.get("id"), email, "users_endpoint")
                    return result
            except Exception:
                pass  # Endpoint doesn't exist yet, fall through to members

            # Fallback: POST /external/members
            resp = await client.post(
                f"{REWARDS_API_BASE}/members",
                headers=_headers(),
                json=payload,
            )

            if resp.status_code in [200, 201]:
                data = resp.json()
                result["success"] = True
                result["action"] = data.get("action", "synced")
                result["rewards_id"] = data.get("id")

                await _save_sync_mapping(db, hub_id, data.get("id"), email, "members_endpoint")
            else:
                result["error"] = resp.text[:200]
                logger.warning(f"Rewards sync failed for {email}: {resp.status_code} {resp.text[:100]}")

    except Exception as e:
        result["error"] = str(e)[:200]
        logger.error(f"Rewards sync error for {email}: {e}")

    return result


async def _save_sync_mapping(db, hub_id: str, rewards_id: str, email: str, method: str):
    """Store the hub<->rewards user mapping."""
    now = datetime.now(timezone.utc).isoformat()
    await db.rewards_sync_mapping.update_one(
        {"hub_user_id": hub_id},
        {"$set": {
            "hub_user_id": hub_id,
            "rewards_platform_id": rewards_id,
            "email": email,
            "sync_method": method,
            "last_synced_at": now,
            "updated_at": now,
        },
        "$setOnInsert": {"created_at": now}},
        upsert=True,
    )


async def batch_sync_all_users(db) -> dict:
    """Push all hub users to the rewards platform. Returns summary."""
    users = await db.users.find({}, {"_id": 0}).to_list(500)

    summary = {"total": len(users), "success": 0, "failed": 0, "created": 0, "updated": 0, "errors": []}

    for user in users:
        result = await sync_user_to_rewards(db, user)
        if result["success"]:
            summary["success"] += 1
            if result["action"] == "created":
                summary["created"] += 1
            else:
                summary["updated"] += 1
        else:
            summary["failed"] += 1
            summary["errors"].append({"email": result["email"], "error": result["error"]})

    # Log the sync
    await db.rewards_sync_log.insert_one({
        "type": "batch_sync",
        "summary": {k: v for k, v in summary.items() if k != "errors"},
        "error_count": summary["failed"],
        "synced_at": datetime.now(timezone.utc).isoformat(),
    })

    return summary


async def get_sync_status(db) -> dict:
    """Get the current sync status between hub and rewards platform."""
    hub_count = await db.users.count_documents({})
    synced_count = await db.rewards_sync_mapping.count_documents({})
    last_sync = await db.rewards_sync_log.find_one(
        {"type": "batch_sync"},
        {"_id": 0},
        sort=[("synced_at", -1)]
    )

    # Try to get rewards platform user count
    rewards_count = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{REWARDS_API_BASE}/stats", headers=_headers())
            if resp.status_code == 200:
                stats = resp.json()
                rewards_count = stats.get("total_users", stats.get("users_count"))
    except Exception:
        pass

    return {
        "hub_users": hub_count,
        "synced_users": synced_count,
        "rewards_platform_users": rewards_count,
        "last_batch_sync": last_sync.get("synced_at") if last_sync else None,
        "last_batch_summary": last_sync.get("summary") if last_sync else None,
    }

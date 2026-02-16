"""
Shared helper functions used across multiple route files.
Extracted from server.py to reduce coupling and improve maintainability.
"""
import uuid
import logging
from datetime import datetime, timezone

import deps

logger = logging.getLogger("server")


async def create_admin_notification(notification_type: str, title: str, message: str, user_id: str, user_name: str, amount: float = None, metadata: dict = None):
    """Create a notification for admins about member activity and broadcast via WebSocket"""
    db = deps.db
    notification = {
        "id": str(uuid.uuid4()),
        "type": notification_type,
        "title": title,
        "message": message,
        "user_id": user_id,
        "user_name": user_name,
        "amount": amount,
        "metadata": metadata or {},
        "is_read": False,
        "visibility": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_notifications.insert_one(notification)
    
    try:
        from server import websocket_manager
        await websocket_manager.broadcast_to_admins(notification)
    except Exception as e:
        logger.error(f"Failed to broadcast admin notification: {e}")
    
    return notification


async def create_member_notification(notification_type: str, title: str, message: str, triggered_by_id: str = None, triggered_by_name: str = None, amount: float = None, metadata: dict = None):
    """Create a notification visible to all members and broadcast via WebSocket"""
    db = deps.db
    notification = {
        "id": str(uuid.uuid4()),
        "type": notification_type,
        "title": title,
        "message": message,
        "triggered_by_id": triggered_by_id,
        "triggered_by_name": triggered_by_name,
        "amount": amount,
        "metadata": metadata or {},
        "is_read": False,
        "visibility": "all",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.member_notifications.insert_one(notification)
    
    try:
        from server import websocket_manager
        await websocket_manager.broadcast_to_members(notification)
    except Exception as e:
        logger.error(f"Failed to broadcast member notification: {e}")
    
    return notification


def calculate_exit_value(lot_size: float) -> float:
    """Calculate projected exit value: LOT * 15 (profit multiplier)"""
    return lot_size * 15


async def send_push_to_admins(title: str, body: str, url: str = "/", tag: str = None):
    """Send push notification to all admin users."""
    import json
    import os
    db = deps.db
    admin_users = await db.users.find(
        {"role": {"$in": ["admin", "basic_admin", "super_admin", "master_admin"]}, "is_deactivated": {"$ne": True}},
        {"_id": 0, "id": 1}
    ).to_list(50)
    admin_ids = [u["id"] for u in admin_users]
    if not admin_ids:
        return {"sent": 0, "failed": 0}

    subscriptions = await db.push_subscriptions.find({"user_id": {"$in": admin_ids}}).to_list(200)

    from pywebpush import webpush, WebPushException

    vapid_private = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_subject = os.environ.get("VAPID_SUBJECT", "mailto:iam@ryansalvador.com")
    if not vapid_private:
        return {"sent": 0, "failed": 0}

    payload = json.dumps({
        "title": title, "body": body, "url": url,
        "tag": tag or "admin-alert",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    sent = 0
    failed = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_subject},
                content_encoding="aes128gcm",
            )
            sent += 1
        except WebPushException as e:
            if hasattr(e, 'response') and e.response and e.response.status_code in [404, 410]:
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})
            failed += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed}


async def send_push_notification(user_id: str, title: str, body: str, url: str = "/", tag: str = None):
    """Send a push notification to a specific user"""
    import json
    import os
    from pywebpush import webpush, WebPushException

    db = deps.db
    vapid_private = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_subject = os.environ.get("VAPID_SUBJECT", "mailto:iam@ryansalvador.com")

    if not vapid_private:
        logger.warning("VAPID_PRIVATE_KEY not set, skipping push notification")
        return {"sent": 0, "failed": 0}

    subscriptions = await db.push_subscriptions.find({"user_id": user_id}).to_list(20)

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "tag": tag or "crosscurrent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    sent = 0
    failed = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_subject},
                content_encoding="aes128gcm",
            )
            sent += 1
        except WebPushException as e:
            logger.warning(f"Push notification failed for {user_id}: {e}")
            if hasattr(e, 'response') and e.response and e.response.status_code in [404, 410]:
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})
            failed += 1
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            failed += 1

    return {"sent": sent, "failed": failed}


async def send_push_to_all_members(title: str, body: str, url: str = "/", tag: str = None, exclude_user_ids: list = None):
    """Send push notification to all active members"""
    import json
    import os
    from pywebpush import webpush, WebPushException

    db = deps.db
    query = {}
    if exclude_user_ids:
        query["user_id"] = {"$nin": exclude_user_ids}

    subscriptions = await db.push_subscriptions.find(query).to_list(1000)

    vapid_private = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_subject = os.environ.get("VAPID_SUBJECT", "mailto:iam@ryansalvador.com")

    if not vapid_private:
        return {"sent": 0, "failed": 0}

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "tag": tag or "crosscurrent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    sent = 0
    failed = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=payload,
                vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_subject},
                content_encoding="aes128gcm",
            )
            sent += 1
        except WebPushException as e:
            if hasattr(e, 'response') and e.response and e.response.status_code in [404, 410]:
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})
            failed += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed}

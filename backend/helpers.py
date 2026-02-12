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

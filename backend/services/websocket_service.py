"""WebSocket service for real-time notifications"""
import asyncio
import json
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
import uuid

logger = logging.getLogger(__name__)

# Database reference (will be set by server.py)
_db = None

def set_database(db):
    """Set the database reference for notifications storage"""
    global _db
    _db = db


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Map of user_id -> list of websocket connections (supports multiple tabs/devices)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Map of role -> set of user_ids (for broadcasting to role groups)
        self.role_connections: Dict[str, Set[str]] = {
            "master_admin": set(),
            "super_admin": set(),
            "basic_admin": set(),
            "member": set()
        }
        # All admin user_ids for admin-only broadcasts
        self.admin_users: Set[str] = set()
    
    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Add to user connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Add to role group
        if role in self.role_connections:
            self.role_connections[role].add(user_id)
        
        # Track admins
        if role in ["master_admin", "super_admin", "basic_admin"]:
            self.admin_users.add(user_id)
        
        logger.info(f"WebSocket connected: user={user_id}, role={role}")
    
    def disconnect(self, websocket: WebSocket, user_id: str, role: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up if no more connections for this user
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Remove from role group
                if role in self.role_connections:
                    self.role_connections[role].discard(user_id)
                
                # Remove from admin tracking
                self.admin_users.discard(user_id)
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def send_notification(self, notification: dict, user_id: str, persist: bool = True):
        """Send a notification to a specific user and optionally persist to database"""
        # Persist to database first
        if persist and _db is not None:
            try:
                notification_copy = notification.copy()
                notification_copy["recipient_id"] = user_id
                notification_copy["read"] = False
                await _db.notifications.insert_one(notification_copy)
            except Exception as e:
                logger.error(f"Failed to persist notification: {e}")
        
        # Send via WebSocket if connected
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(notification)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected
            for ws in disconnected:
                self.active_connections[user_id].remove(ws)
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user (all their connections) - legacy method"""
        await self.send_notification(message, user_id, persist=True)
    
    async def broadcast_to_admins(self, message: dict):
        """Broadcast a message to all connected admin users and persist for each"""
        for user_id in self.admin_users.copy():
            await self.send_notification(message, user_id, persist=True)
    
    async def broadcast_to_role(self, message: dict, role: str):
        """Broadcast a message to all users with a specific role"""
        if role in self.role_connections:
            for user_id in self.role_connections[role].copy():
                await self.send_notification(message, user_id, persist=True)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_notification(message, user_id, persist=True)
    
    def get_connection_count(self) -> Dict[str, int]:
        """Get count of connections by role"""
        return {
            "total_users": len(self.active_connections),
            "total_connections": sum(len(conns) for conns in self.active_connections.values()),
            "master_admin": len(self.role_connections["master_admin"]),
            "super_admin": len(self.role_connections["super_admin"]),
            "basic_admin": len(self.role_connections["basic_admin"]),
            "member": len(self.role_connections["member"])
        }


# Global connection manager instance
manager = ConnectionManager()


# Notification types
class NotificationType:
    # Admin notifications
    DEPOSIT_REQUEST = "deposit_request"
    WITHDRAWAL_REQUEST = "withdrawal_request"
    TRADE_UNDERPERFORM = "trade_underperform"
    NEW_MEMBER = "new_member"
    LICENSE_ACTIVATED = "license_activated"
    
    # User notifications
    TRANSACTION_STATUS = "transaction_status"
    TRADE_SIGNAL = "trade_signal"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    
    # Forum notifications
    FORUM_NEW_COMMENT = "forum_new_comment"
    FORUM_VOTE = "forum_vote"
    FORUM_POST_CLOSED = "forum_post_closed"


def create_notification(
    notification_type: str,
    title: str,
    message: str,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    amount: Optional[float] = None,
    metadata: Optional[dict] = None
) -> dict:
    """Create a notification object"""
    return {
        "id": str(uuid.uuid4()),
        "type": notification_type,
        "title": title,
        "message": message,
        "user_id": user_id,
        "user_name": user_name,
        "amount": amount,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def notify_admins_deposit_request(user_id: str, user_name: str, amount: float, transaction_id: str):
    """Notify admins about a new deposit request"""
    notification = create_notification(
        notification_type=NotificationType.DEPOSIT_REQUEST,
        title="New Deposit Request",
        message=f"{user_name} has submitted a deposit request",
        user_id=user_id,
        user_name=user_name,
        amount=amount,
        metadata={"transaction_id": transaction_id}
    )
    await manager.broadcast_to_admins(notification)


async def notify_admins_withdrawal_request(user_id: str, user_name: str, amount: float, transaction_id: str):
    """Notify admins about a new withdrawal request"""
    notification = create_notification(
        notification_type=NotificationType.WITHDRAWAL_REQUEST,
        title="New Withdrawal Request",
        message=f"{user_name} has requested a withdrawal",
        user_id=user_id,
        user_name=user_name,
        amount=amount,
        metadata={"transaction_id": transaction_id}
    )
    await manager.broadcast_to_admins(notification)


async def notify_user_transaction_status(user_id: str, transaction_type: str, status: str, amount: float, message: str):
    """Notify a user about their transaction status change"""
    notification = create_notification(
        notification_type=NotificationType.TRANSACTION_STATUS,
        title=f"{transaction_type.title()} {status.title()}",
        message=message,
        amount=amount,
        metadata={"transaction_type": transaction_type, "status": status}
    )
    await manager.send_personal_message(notification, user_id)


async def notify_trade_signal(signal: dict):
    """Broadcast a new trade signal to all members"""
    notification = create_notification(
        notification_type=NotificationType.TRADE_SIGNAL,
        title=f"Trade Signal: {signal.get('direction', 'N/A')}",
        message=f"New {signal.get('direction')} signal for {signal.get('product', 'MOIL10')} at {signal.get('trade_time', 'N/A')}",
        metadata=signal
    )
    await manager.broadcast_to_all(notification)


async def notify_system_announcement(title: str, message: str, target_roles: Optional[List[str]] = None):
    """Broadcast a system announcement"""
    notification = create_notification(
        notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title=title,
        message=message
    )
    
    if target_roles:
        for role in target_roles:
            await manager.broadcast_to_role(notification, role)
    else:
        await manager.broadcast_to_all(notification)


async def broadcast_forum_event(event_type: str, post_id: str, data: dict = None):
    """Broadcast a forum event to all connected users (no persistence, no toast)."""
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "post_id": post_id,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Broadcast without persisting — these are ephemeral UI refresh signals
    for user_id in list(manager.active_connections.keys()):
        if user_id in manager.active_connections:
            disconnected = []
            for websocket in manager.active_connections[user_id]:
                try:
                    await websocket.send_json(event)
                except Exception:
                    disconnected.append(websocket)
            for ws in disconnected:
                manager.active_connections[user_id].remove(ws)

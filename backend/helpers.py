"""
Shared helper functions used across multiple route files.
Extracted from server.py to reduce coupling and improve maintainability.
"""
import uuid
import os
import math
import logging
import httpx
from datetime import datetime, timezone, timedelta

import deps

logger = logging.getLogger("server")

HEARTBEAT_API_KEY = os.environ.get('HEARTBEAT_API_KEY', '')
EMAILIT_API_KEY = os.environ.get('EMAILIT_API_KEY', '')


# ─── Notification Helpers ───

async def create_admin_notification(notification_type: str, title: str, message: str, user_id: str, user_name: str, amount: float = None, metadata: dict = None):
    """Create a notification for admins about member activity and broadcast via WebSocket"""
    from services import websocket_manager
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
        await websocket_manager.broadcast_to_admins(notification)
    except Exception as e:
        logger.error(f"Failed to broadcast admin notification: {e}")
    return notification


async def create_member_notification(notification_type: str, title: str, message: str, triggered_by_id: str = None, triggered_by_name: str = None, amount: float = None, metadata: dict = None):
    """Create a notification visible to all members and broadcast via WebSocket"""
    from services import websocket_manager
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
        "visibility": "all",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.member_notifications.insert_one(notification)
    try:
        await websocket_manager.broadcast_to_all(notification)
    except Exception as e:
        logger.error(f"Failed to broadcast member notification: {e}")
    return notification


async def create_user_notification(user_id: str, notification_type: str, title: str, message: str, metadata: dict = None):
    """Create a notification for a specific user and send via WebSocket"""
    from services import websocket_manager
    db = deps.db
    notification = {
        "id": str(uuid.uuid4()),
        "type": notification_type,
        "title": title,
        "message": message,
        "user_id": user_id,
        "metadata": metadata or {},
        "is_read": False,
        "visibility": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_notifications.insert_one(notification)
    try:
        await websocket_manager.send_to_user(user_id, notification)
    except Exception as e:
        logger.error(f"Failed to send user notification to {user_id}: {e}")
    return notification


# ─── Calculation Helpers ───

def calculate_exit_value(lot_size: float) -> float:
    """Calculate exit value: LOT Size x 15"""
    return lot_size * 15


def truncate_lot_size(balance: float, divisor: float = 980) -> float:
    """Calculate LOT size using truncation (floor to 2 decimals) to match frontend behavior."""
    if balance <= 0:
        return 0
    return math.trunc(balance / divisor * 100) / 100


def calculate_withdrawal_fees(amount: float) -> dict:
    """Calculate withdrawal fees: 3% Merin only (Binance fee moved to deposit)"""
    merin_fee = amount * 0.03
    total_fees = merin_fee
    net_amount = amount - total_fees
    return {
        "gross_amount": amount,
        "merin_fee": round(merin_fee, 2),
        "total_fees": round(total_fees, 2),
        "net_amount": round(net_amount, 2),
        "processing_days": "1-2 business days"
    }


def add_business_days(start_date, days):
    """Add business days to a date, skipping weekends"""
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


# ─── Heartbeat / Verification Helpers ───

async def verify_heartbeat_user(email: str) -> dict:
    """Verify if user exists and is active in Heartbeat community."""
    result = {"exists": False, "is_active": False, "user": None, "reason": None}
    if not HEARTBEAT_API_KEY:
        logger.warning("Heartbeat API key not configured, skipping verification")
        return {"exists": True, "is_active": True, "user": None, "reason": None}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.heartbeat.chat/v0/users",
                headers={"Authorization": f"Bearer {HEARTBEAT_API_KEY}"},
                params={"email": email},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    users = data
                else:
                    users = data.get("users", data.get("data", []))
                if isinstance(users, list):
                    for user in users:
                        if isinstance(user, dict) and user.get("email", "").lower() == email.lower():
                            result["exists"] = True
                            result["user"] = user
                            status = user.get("status", "").lower() if user.get("status") else ""
                            is_active = user.get("is_active", user.get("active", True))
                            is_suspended = user.get("suspended", user.get("is_suspended", False))
                            is_banned = user.get("banned", user.get("is_banned", False))
                            is_deleted = user.get("deleted", user.get("is_deleted", False))
                            if status in ["deactivated", "suspended", "banned", "deleted", "inactive", "disabled"]:
                                result["is_active"] = False
                                result["reason"] = f"Account status: {status}"
                            elif is_suspended:
                                result["is_active"] = False
                                result["reason"] = "Account is suspended"
                            elif is_banned:
                                result["is_active"] = False
                                result["reason"] = "Account is banned"
                            elif is_deleted:
                                result["is_active"] = False
                                result["reason"] = "Account has been deleted"
                            elif is_active == False:
                                result["is_active"] = False
                                result["reason"] = "Account is not active"
                            else:
                                result["is_active"] = True
                            return result
            return result
    except Exception as e:
        logger.error(f"Heartbeat verification error: {e}")
        return {"exists": True, "is_active": True, "user": None, "reason": None}


async def verify_heartbeat_user_exists(email: str) -> bool:
    """Legacy function - returns True if user exists (regardless of status)"""
    result = await verify_heartbeat_user(email)
    return result.get("exists", False)


# ─── Push Notification Helpers ───

async def send_push_to_admins(title: str, body: str, url: str = "/", tag: str = None):
    """Send push notification to all admin users."""
    import json
    from pywebpush import webpush, WebPushException
    db = deps.db
    admin_users = await db.users.find(
        {"role": {"$in": ["admin", "basic_admin", "super_admin", "master_admin"]}, "is_deactivated": {"$ne": True}},
        {"_id": 0, "id": 1}
    ).to_list(50)
    admin_ids = [u["id"] for u in admin_users]
    if not admin_ids:
        return {"sent": 0, "failed": 0}
    subscriptions = await db.push_subscriptions.find({"user_id": {"$in": admin_ids}}).to_list(200)
    vapid_private = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_subject = os.environ.get("VAPID_SUBJECT", "mailto:iam@ryansalvador.com")
    if not vapid_private:
        return {"sent": 0, "failed": 0}
    payload = json.dumps({
        "title": title, "body": body, "url": url,
        "tag": tag or "admin-alert",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    sent, failed = 0, 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=payload, vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_subject}, content_encoding="aes128gcm",
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
    from pywebpush import webpush, WebPushException
    db = deps.db
    vapid_private = os.environ.get("VAPID_PRIVATE_KEY")
    vapid_subject = os.environ.get("VAPID_SUBJECT", "mailto:iam@ryansalvador.com")
    if not vapid_private:
        logger.warning("VAPID_PRIVATE_KEY not set, skipping push notification")
        return {"sent": 0, "failed": 0}
    subscriptions = await db.push_subscriptions.find({"user_id": user_id}).to_list(20)
    payload = json.dumps({
        "title": title, "body": body, "url": url,
        "tag": tag or "crosscurrent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    sent, failed = 0, 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=payload, vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_subject}, content_encoding="aes128gcm",
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
        "title": title, "body": body, "url": url,
        "tag": tag or "crosscurrent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    sent, failed = 0, 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=payload, vapid_private_key=vapid_private,
                vapid_claims={"sub": vapid_subject}, content_encoding="aes128gcm",
            )
            sent += 1
        except WebPushException as e:
            if hasattr(e, 'response') and e.response and e.response.status_code in [404, 410]:
                await db.push_subscriptions.delete_one({"endpoint": sub["endpoint"]})
            failed += 1
        except Exception:
            failed += 1
    return {"sent": sent, "failed": failed}


# ─── Email / Signal Helpers ───

async def send_signal_email_to_members(signal: dict, frontend_url: str = None):
    """Send trading signal email to all active members."""
    db = deps.db
    active_users = await db.users.find(
        {"is_active": True},
        {"_id": 0, "id": 1, "email": 1, "full_name": 1}
    ).to_list(10000)
    if not active_users:
        logger.info("No active users to send signal email")
        return {"sent": 0, "failed": 0}
    template = await db.email_templates.find_one({"type": "trading_signal"}, {"_id": 0})
    if not template:
        template = await db.email_templates.find_one({"type": "trade_notification"}, {"_id": 0})
    default_subject = f"New Trading Signal: {signal.get('direction', 'BUY')} {signal.get('product', 'MOIL10')}"
    default_body = f"""Hello {{{{name}}}},

A new official trading signal is available!

Signal Details:
- Product: {signal.get('product', 'MOIL10')}
- Direction: {signal.get('direction', 'BUY')}
- Trade Time: {signal.get('trade_time', '')} ({signal.get('trade_timezone', 'Asia/Manila')})

<a href="{frontend_url or ''}/trade-monitor" style="display:inline-block;padding:12px 24px;background:#3B82F6;color:white;text-decoration:none;border-radius:8px;margin:16px 0;">Go to Trade Monitor</a>

Don't miss this opportunity!

Best regards,
CrossCurrent Team"""
    subject = template.get("subject", default_subject) if template else default_subject
    body = template.get("body", default_body) if template else default_body
    trade_monitor_url = f"{frontend_url}/trade-monitor" if frontend_url else "/trade-monitor"
    current_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
    sent_count, failed_count = 0, 0
    for user in active_users:
        try:
            user_subject = subject.replace("{user_name}", user.get("full_name", "Trader"))
            user_subject = user_subject.replace("{{name}}", user.get("full_name", "Trader"))
            user_subject = user_subject.replace("{product}", signal.get("product", ""))
            user_subject = user_subject.replace("{{product}}", signal.get("product", ""))
            user_subject = user_subject.replace("{direction}", signal.get("direction", ""))
            user_subject = user_subject.replace("{{direction}}", signal.get("direction", ""))
            user_body = body.replace("{user_name}", user.get("full_name", "Trader"))
            user_body = user_body.replace("{{name}}", user.get("full_name", "Trader"))
            user_body = user_body.replace("{user_email}", user.get("email", ""))
            user_body = user_body.replace("{product}", signal.get("product", ""))
            user_body = user_body.replace("{{product}}", signal.get("product", ""))
            user_body = user_body.replace("{direction}", signal.get("direction", ""))
            user_body = user_body.replace("{{direction}}", signal.get("direction", ""))
            user_body = user_body.replace("{time}", signal.get("trade_time", ""))
            user_body = user_body.replace("{{time}}", signal.get("trade_time", ""))
            user_body = user_body.replace("{timezone}", signal.get("trade_timezone", ""))
            user_body = user_body.replace("{trade_monitor_url}", trade_monitor_url)
            user_body = user_body.replace("{current_date}", current_date)
            from services.email_service import send_email
            result = await send_email(
                db=db,
                to_email=user.get("email"),
                subject=user_subject,
                html_content=user_body.replace("\n", "<br>") if "<" not in user_body else user_body,
                template_type="trading_signal",
                log_email_record=True
            )
            if result.get("success"):
                sent_count += 1
            else:
                logger.error(f"Failed to send signal email to {user.get('email')}: {result.get('error')}")
                failed_count += 1
        except Exception as e:
            logger.error(f"Failed to send signal email to {user.get('email')}: {e}")
            failed_count += 1
    logger.info(f"Signal email sent: {sent_count} successful, {failed_count} failed")
    return {"sent": sent_count, "failed": failed_count}


# ─── Scheduler Helpers ───

def schedule_pre_trade_notifications(trade_time: str, trade_timezone: str, product: str, direction: str):
    """Schedule push notifications 10min and 5min before trade time"""
    import pytz
    from apscheduler.triggers.date import DateTrigger
    # Import scheduler from server module (lazy to avoid circular)
    try:
        from server import scheduler
    except ImportError:
        logger.warning("Could not import scheduler")
        return
    try:
        tz = pytz.timezone(trade_timezone or "Asia/Manila")
    except Exception:
        tz = pytz.timezone("Asia/Manila")
    now = datetime.now(tz)
    hour, minute = map(int, trade_time.split(":"))
    trade_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if trade_dt <= now:
        logger.info("Trade time already passed, skipping pre-trade notifications")
        return
    remind_10 = trade_dt - timedelta(minutes=10)
    if remind_10 > now:
        try:
            scheduler.add_job(
                _send_pre_trade_push, DateTrigger(run_date=remind_10),
                id="pre_trade_10min", replace_existing=True,
                args=[10, product, direction, trade_time],
            )
            logger.info(f"Scheduled 10-min pre-trade notification at {remind_10}")
        except Exception as e:
            logger.error(f"Failed to schedule 10min notification: {e}")
    remind_5 = trade_dt - timedelta(minutes=5)
    if remind_5 > now:
        try:
            scheduler.add_job(
                _send_pre_trade_push, DateTrigger(run_date=remind_5),
                id="pre_trade_5min", replace_existing=True,
                args=[5, product, direction, trade_time],
            )
            logger.info(f"Scheduled 5-min pre-trade notification at {remind_5}")
        except Exception as e:
            logger.error(f"Failed to schedule 5min notification: {e}")


async def _send_pre_trade_push(minutes_before: int, product: str, direction: str, trade_time: str):
    """Send pre-trade push notification"""
    await send_push_to_all_members(
        title=f"{minutes_before} Minutes to Trade!",
        body=f"{direction} {product} at {trade_time} - Get ready!",
        url="/trade-monitor",
        tag=f"pre-trade-{minutes_before}min"
    )


# ─── Scheduler Tasks ───

async def check_missed_trades():
    """Check for users who missed today's trade and send email notifications"""
    db = deps.db
    try:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        signal = await db.trading_signals.find_one(
            {"is_active": True, "created_at": {"$gte": today_start, "$lt": today_end}},
            {"_id": 0}
        )
        if not signal:
            logger.info("No active signal found for missed trade check")
            return
        active_members = await db.users.find(
            {"role": "member", "is_active": True, "email_notifications_enabled": {"$ne": False}},
            {"_id": 0, "id": 1, "email": 1, "full_name": 1}
        ).to_list(1000)
        traded_users = await db.trade_logs.distinct(
            "user_id", {"created_at": {"$gte": today_start, "$lt": today_end}}
        )
        missed_members = [m for m in active_members if m["id"] not in traded_users]
        template = await db.email_templates.find_one({"type": "missed_trade"}, {"_id": 0})
        if not template:
            template = {
                "subject": "You missed today's trading signal",
                "body": "Hi {{name}},\n\nWe noticed you didn't participate in today's trading signal.\n\nProduct: {{product}}\nDirection: {{direction}}\nTime: {{trade_time}}\n\nDon't miss tomorrow's opportunity!\n\nBest regards,\nCrossCurrent Team"
            }
        for member in missed_members:
            try:
                subj = template["subject"]
                body = template["body"]
                body = body.replace("{{name}}", member.get("full_name", "Trader"))
                body = body.replace("{{product}}", signal.get("product", ""))
                body = body.replace("{{direction}}", signal.get("direction", ""))
                body = body.replace("{{trade_time}}", signal.get("trade_time", ""))
                from services.email_service import send_email
                await send_email(to=member["email"], subject=subj, body=body)
                await db.email_history.insert_one({
                    "id": str(uuid.uuid4()), "to": member["email"],
                    "subject": subj, "template_type": "missed_trade",
                    "status": "sent", "sent_at": datetime.now(timezone.utc)
                })
                logger.info(f"Sent missed trade email to {member['email']}")
            except Exception as e:
                logger.error(f"Failed to send missed trade email to {member.get('email')}: {e}")
        logger.info(f"Missed trade check complete. Notified {len(missed_members)} members.")
    except Exception as e:
        logger.error(f"Missed trade scheduler error: {e}")


# ─── License Projection Helpers ───

def get_quarter(dt: datetime) -> int:
    """Get the quarter number (1-4) for a date"""
    return (dt.month - 1) // 3 + 1


def calculate_extended_license_projections(starting_amount: float, start_date: datetime, days_to_project: int = 365) -> list:
    """
    Calculate projections for Extended Licensee using quarterly compounding.
    Daily profit is fixed within each quarter and recalculated at quarter start.
    Uses proper trading days (weekdays excluding US market holidays).
    """
    from typing import List, Dict
    from utils.trading_days import get_holidays_for_range, is_trading_day as is_trading_day_with_holidays
    
    holidays = get_holidays_for_range(start_date.year, start_date.year + 6)
    
    projections = []
    current_date = start_date
    current_amount = starting_amount
    current_quarter = get_quarter(start_date)
    current_year = start_date.year
    
    # Calculate initial quarter's values
    quarter_daily_profit = round(truncate_lot_size(current_amount) * 15, 2)
    quarter_lot_size = truncate_lot_size(current_amount)
    quarter_start_amount = current_amount
    
    trading_days_processed = 0
    
    while trading_days_processed < days_to_project:
        # Skip non-trading days
        if not is_trading_day_with_holidays(current_date, holidays):
            current_date += timedelta(days=1)
            continue
        
        # Check if we've moved to a new quarter
        new_quarter = get_quarter(current_date)
        new_year = current_date.year
        
        if new_year != current_year or new_quarter != current_quarter:
            quarter_daily_profit = round(truncate_lot_size(current_amount) * 15, 2)
            quarter_lot_size = truncate_lot_size(current_amount)
            quarter_start_amount = current_amount
            current_quarter = new_quarter
            current_year = new_year
        
        current_amount = round(current_amount + quarter_daily_profit, 2)
        
        projections.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "quarter": f"Q{current_quarter} {current_year}",
            "lot_size": quarter_lot_size,
            "daily_profit": quarter_daily_profit,
            "account_value": current_amount,
            "cumulative_profit": round(current_amount - starting_amount, 2),
            "is_trading_day": True
        })
        
        trading_days_processed += 1
        current_date += timedelta(days=1)
    
    return projections


def get_quarterly_summary(projections: list) -> list:
    """Get summary by quarter from projections"""
    quarters = {}
    for p in projections:
        q = p["quarter"]
        if q not in quarters:
            quarters[q] = {
                "quarter": q,
                "daily_profit": p["daily_profit"],
                "start_value": p["account_value"] - p["daily_profit"],
                "trading_days": 0,
                "total_profit": 0
            }
        quarters[q]["trading_days"] += 1
        quarters[q]["end_value"] = p["account_value"]
        quarters[q]["total_profit"] = round(p["account_value"] - quarters[q]["start_value"], 2)
    
    return list(quarters.values())

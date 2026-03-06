"""General API routes (notifications, uploads, health, email) - extracted from server.py"""
import uuid
import os
import logging
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List

import deps
from helpers import send_push_to_admins
from services import websocket_manager

try:
    from services import upload_file, upload_profile_picture, upload_deposit_screenshot, send_email
except ImportError:
    pass

try:
    from services import get_license_invite_email
except ImportError:
    async def get_license_invite_email(*a, **kw): return None

import httpx

logger = logging.getLogger("server")

router = APIRouter(tags=["General"])

@router.post("/send-email")
async def send_simple_email(to: str, subject: str, body: str, user: dict = Depends(deps.require_admin)):
    """Simple email endpoint - uses direct API call"""
    if not EMAILIT_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.emailit.com/v1/emails",
                headers={
                    "Authorization": f"Bearer {EMAILIT_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "noreply@crosscurrent.finance",
                    "to": to,
                    "subject": subject,
                    "html": body
                },
                timeout=30.0
            )
            
            if response.status_code in [200, 201, 202]:
                return {"message": "Email sent successfully"}
            else:
                raise HTTPException(status_code=response.status_code, detail="Email sending failed")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Email service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")


@router.get("/ws/status")
async def get_websocket_status(user: dict = Depends(deps.require_admin)):
    """Get WebSocket connection statistics (admin only)"""
    return websocket_manager.get_connection_count()


@router.get("/notifications")
async def get_notifications(
    limit: int = 50,
    skip: int = 0,
    unread_only: bool = False,
    user: dict = Depends(deps.get_current_user)
):
    """Get notifications for the current user (personal + community)"""
    is_admin = user.get("role") in ["basic_admin", "admin", "super_admin", "master_admin"]
    
    # Get personal notifications (targeted to this user from WebSocket service)
    personal_query = {"recipient_id": user["id"]}
    if unread_only:
        personal_query["read"] = False
    
    personal_notifications = await deps.db.notifications.find(
        personal_query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit // 2).to_list(limit // 2)
    
    # Get user-specific notifications (from create_user_notification)
    user_notifs = await deps.db.user_notifications.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit // 2).to_list(limit // 2)
    
    # Get community/member notifications (visible to all)
    member_notifications = await deps.db.member_notifications.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit // 2).to_list(limit // 2)
    
    # For admins, also get admin-only notifications
    admin_notifications = []
    if is_admin:
        admin_notifications = await deps.db.admin_notifications.find(
            {},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit // 2).to_list(limit // 2)
    
    # Combine and sort all notifications
    all_notifications = []
    
    for n in personal_notifications:
        n["source"] = "personal"
        n["created_at"] = n.get("timestamp", n.get("created_at"))
        all_notifications.append(n)
    
    for n in user_notifs:
        n["source"] = "personal"
        all_notifications.append(n)
    
    for n in member_notifications:
        n["source"] = "community"
        all_notifications.append(n)
    
    for n in admin_notifications:
        n["source"] = "admin"
        all_notifications.append(n)
    
    # Sort by created_at descending
    all_notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    all_notifications = all_notifications[:limit]
    
    # Get unread counts
    personal_unread = await deps.db.notifications.count_documents({
        "recipient_id": user["id"],
        "read": False
    })
    
    user_notif_unread = await deps.db.user_notifications.count_documents({
        "user_id": user["id"],
        "is_read": False
    })
    
    admin_unread = 0
    if is_admin:
        admin_unread = await deps.db.admin_notifications.count_documents({"is_read": False})
    
    return {
        "notifications": all_notifications,
        "unread_count": personal_unread + user_notif_unread + admin_unread,
        "is_admin": is_admin
    }


@router.post("/notifications/mark-read")
async def mark_notifications_read(user: dict = Depends(deps.get_current_user)):
    """Mark all notifications as read for the current user"""
    result = await deps.db.notifications.update_many(
        {"recipient_id": user["id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"marked_read": result.modified_count}


@router.delete("/notifications")
async def clear_notifications(user: dict = Depends(deps.get_current_user)):
    """Delete all notifications for the current user"""
    result = await deps.db.notifications.delete_many({"recipient_id": user["id"]})
    return {"deleted": result.deleted_count}


@router.post("/upload/profile-picture")
async def upload_profile_picture_endpoint(
    file: UploadFile = File(...),
    user: dict = Depends(deps.get_current_user)
):
    """Upload a profile picture for the current user"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, WebP, GIF")
    
    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 5MB")
    
    result = await upload_profile_picture(deps.db, user["id"], contents, file.filename, file.content_type)
    
    if result.get("success"):
        return {"message": "Profile picture uploaded", "url": result.get("url")}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))


@router.post("/upload/deposit-screenshot/{transaction_id}")
async def upload_deposit_screenshot_endpoint(
    transaction_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(deps.get_current_user)
):
    """Upload a deposit screenshot for a transaction"""
    # Verify transaction belongs to user
    transaction = await deps.db.licensee_transactions.find_one({"id": transaction_id, "user_id": user["id"]})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: JPEG, PNG, WebP")
    
    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    
    result = await upload_deposit_screenshot(deps.db, user["id"], transaction_id, contents, file.filename, file.content_type)
    
    if result.get("success"):
        return {"message": "Screenshot uploaded", "url": result.get("url")}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))


@router.post("/upload/general")
async def upload_general_file(
    file: UploadFile = File(...),
    folder: str = Form("uploads"),
    file_type: str = Form("general"),
    user: dict = Depends(deps.get_current_user)
):
    """Upload a general file"""
    # Validate file size (max 20MB)
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 20MB")
    
    result = await upload_file(deps.db, contents, file.filename, file.content_type, folder, user["id"], file_type)
    
    if result.get("success"):
        return {"message": "File uploaded", "url": result.get("url"), "public_id": result.get("public_id")}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))


@router.post("/email/send-license-invite")
async def send_license_invite_email(
    invite_code: str,
    invitee_email: str,
    invitee_name: str = "",
    user: dict = Depends(deps.require_master_admin)
):
    """Send a license invite email"""
    # Get invite details
    invite = await deps.db.license_invites.find_one({"invite_code": invite_code})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    # Get production URL from settings
    settings = await deps.db.platform_settings.find_one({}, {"_id": 0})
    base_url = settings.get("production_site_url") or os.environ.get("REACT_APP_BACKEND_URL", "https://crosscurrent.finance")
    
    # Generate email content
    email_content = get_license_invite_email(
        invite_code=invite_code,
        invitee_name=invitee_name,
        license_type=invite.get("license_type", "extended"),
        starting_amount=invite.get("starting_amount", 0),
        base_url=base_url
    )
    
    result = await send_email(
        db=deps.db,
        to_email=invitee_email,
        subject=email_content["subject"],
        html_content=email_content["html"],
        text_content=email_content["text"]
    )
    
    if result.get("success"):
        # Update invite with email sent timestamp
        await deps.db.license_invites.update_one(
            {"invite_code": invite_code},
            {"$set": {"email_sent_at": datetime.now(timezone.utc).isoformat(), "invitee_email": invitee_email}}
        )
        return {"message": "Invite email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send email"))


@router.post("/email/test")
async def test_email_service(
    to_email: str,
    user: dict = Depends(deps.require_master_admin)
):
    """Send a test email to verify email service configuration"""
    result = await send_email(
        db=deps.db,
        to_email=to_email,
        subject="Test Email from CrossCurrent Finance Center",
        html_content="""
        <h1>Email Service Test</h1>
        <p>This is a test email from CrossCurrent Finance Center.</p>
        <p>If you received this email, your email service is configured correctly!</p>
        """,
        text_content="This is a test email from CrossCurrent Finance Center. If you received this, your email service is configured correctly!"
    )
    
    if result.get("success"):
        return {"message": "Test email sent successfully", "to": to_email}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send test email"))


@router.get("/version")
async def get_build_version():
    """Returns the current build version (changes on every server restart/deploy)."""
    try:
        with open("/app/.build_version", "r") as f:
            build_version = f.read().strip()
    except FileNotFoundError:
        build_version = "unknown"
    return {"build_version": build_version}


@router.get("/")
async def root():
    return {"message": "CrossCurrent Finance Center API", "version": "1.0.0"}


@router.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2026.02.25.v5",
        "features": ["balance-override", "diagnostic-post", "sync-button", "signal-blocking", "version-banner"]
    }


@router.get("/diagnostic/licensee/{email}")
async def diagnostic_licensee(email: str):
    """PUBLIC diagnostic endpoint to debug licensee calculation issues.
    Returns detailed info about what the calculation sees for this user.
    """
    try:
        from utils.calculations import _is_honorary, calculate_honorary_licensee_value
        
        result = {
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "steps": [],
            "errors": []
        }
        
        # Step 1: Find user
        user = await deps.db.users.find_one({"email": email}, {"_id": 0})
        if not user:
            result["errors"].append(f"User with email '{email}' not found")
            return result
        
        result["user_id"] = user.get("id")
        result["user_role"] = user.get("role")
        result["steps"].append(f"✓ Found user: {user.get('full_name')} (id={user.get('id')})")
        
        # Step 2: Find license
        license = await deps.db.licenses.find_one(
            {"user_id": user.get("id"), "is_active": True},
            {"_id": 0}
        )
        
        if not license:
            result["errors"].append(f"No active license found for user_id={user.get('id')}")
            # Try to find ANY license for this user
            any_license = await deps.db.licenses.find_one({"user_id": user.get("id")}, {"_id": 0})
            if any_license:
                result["found_inactive_license"] = {
                    "license_type": any_license.get("license_type"),
                    "is_active": any_license.get("is_active"),
                    "starting_amount": any_license.get("starting_amount")
                }
            return result
        
        result["license"] = {
            "id": license.get("id"),
            "license_type": license.get("license_type"),
            "starting_amount": license.get("starting_amount"),
            "current_amount": license.get("current_amount"),
            "effective_start_date": str(license.get("effective_start_date")),
            "start_date": str(license.get("start_date")),
            "is_active": license.get("is_active")
        }
        result["steps"].append(f"✓ Found license: type={license.get('license_type')}, starting=${license.get('starting_amount')}")
        
        # Step 3: Check if honorary
        license_type = license.get("license_type")
        is_honorary = _is_honorary(license_type)
        result["is_honorary"] = is_honorary
        result["steps"].append(f"✓ _is_honorary('{license_type}') = {is_honorary}")
        
        # Step 4: Find master admin
        master_admin = await deps.db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1, "email": 1, "full_name": 1})
        if not master_admin:
            result["errors"].append("No master_admin user found in database!")
            return result
        
        result["master_admin"] = {
            "id": master_admin.get("id"),
            "email": master_admin.get("email"),
            "name": master_admin.get("full_name")
        }
        result["steps"].append(f"✓ Found master_admin: {master_admin.get('email')} (id={master_admin.get('id')})")
        
        # Step 5: Count master admin trades
        all_trades = await deps.db.trade_logs.find(
            {"user_id": master_admin["id"]},
            {"_id": 0, "created_at": 1, "trade_date": 1, "did_not_trade": 1}
        ).to_list(10000)
        
        result["master_admin_total_trades"] = len(all_trades)
        
        # Count unique trade days (excluding did_not_trade)
        traded_dates = set()
        did_not_trade_count = 0
        for trade in all_trades:
            if trade.get("did_not_trade") == True:
                did_not_trade_count += 1
                continue
            trade_date = trade.get("trade_date")
            if not trade_date:
                created = trade.get("created_at")
                if created:
                    if isinstance(created, datetime):
                        trade_date = created.strftime("%Y-%m-%d")
                    else:
                        trade_date = str(created)[:10]
            if trade_date:
                traded_dates.add(str(trade_date)[:10])
        
        result["master_admin_unique_trade_days"] = len(traded_dates)
        result["master_admin_did_not_trade_days"] = did_not_trade_count
        result["master_admin_trade_dates"] = sorted(list(traded_dates))[:20]  # First 20
        result["steps"].append(f"✓ Master admin has {len(traded_dates)} unique trade days (out of {len(all_trades)} total records)")
        
        # Step 6: Check effective start date
        effective_start = license.get("effective_start_date") or license.get("start_date")
        if effective_start:
            start_str = str(effective_start)[:10]
            trades_after_start = [d for d in traded_dates if d >= start_str]
            result["effective_start_date"] = start_str
            result["trades_after_start"] = len(trades_after_start)
            result["trades_after_start_dates"] = sorted(trades_after_start)[:15]
            result["steps"].append(f"✓ {len(trades_after_start)} trades are on/after effective start ({start_str})")
        else:
            result["errors"].append("No effective_start_date or start_date found in license!")
        
        # Step 7: Calculate value if honorary
        if is_honorary:
            try:
                calculated_value = await calculate_honorary_licensee_value(deps.db, license)
                starting_amount = float(license.get("starting_amount", 0) or 0)
                result["calculated_value"] = calculated_value
                result["calculated_profit"] = round(calculated_value - starting_amount, 2)
                result["steps"].append(f"✓ Calculated value: ${calculated_value} (profit: ${round(calculated_value - starting_amount, 2)})")
            except Exception as e:
                result["errors"].append(f"calculate_honorary_licensee_value failed: {str(e)}")
        
        return result
        
    except Exception as e:
        return {"error": str(e), "email": email}

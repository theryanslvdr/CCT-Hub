"""
Settings routes - extracted from server.py
Includes: platform settings, email templates, integration tests, email history
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import os
import httpx
import requests
import cloudinary
import cloudinary.uploader

import deps
from deps import get_current_user, require_admin, require_master_admin

router = APIRouter(prefix="/settings", tags=["Settings"])


# ==================== MODELS ====================

class PlatformSettings(BaseModel):
    platform_name: str = "CrossCurrent Finance Center"
    platform_tagline: str = "Finance Center"
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#3B82F6"
    secondary_color: str = "#8B5CF6"
    accent_color: str = "#10B981"
    support_email: str = ""
    support_phone: str = ""
    footer_text: str = ""
    maintenance_mode: bool = False
    maintenance_message: str = ""
    registration_enabled: bool = True
    require_heartbeat_verification: bool = True
    heartbeat_api_key: str = ""
    emailit_api_key: str = ""
    emailit_from_email: str = ""
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""
    enable_email_notifications: bool = True
    enable_auto_missed_trade_emails: bool = True
    auto_missed_trade_time: str = "18:00"
    trading_product: str = "MOIL10"
    default_profit_multiplier: float = 15
    default_exit_multiplier: float = 15
    custom_css: str = ""
    announcement: str = ""
    announcement_type: str = "info"
    show_announcement: bool = False
    meta_title: str = "CrossCurrent Finance Center"
    meta_description: str = "Your complete trading profit management platform"
    features: List[str] = []

class EmailTemplateUpdate(BaseModel):
    subject: str
    body: str
    variables: Optional[List[str]] = None

class TestEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    template_type: str = "test"


# ==================== PLATFORM SETTINGS ====================

@router.get("/platform")
async def get_platform_settings():
    db = deps.db
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    if not settings:
        settings = PlatformSettings().model_dump()
    return settings

@router.put("/platform")
async def update_platform_settings(data: PlatformSettings, user: dict = Depends(require_admin)):
    db = deps.db
    await db.platform_settings.update_one(
        {},
        {"$set": data.model_dump()},
        upsert=True
    )
    return {"message": "Settings updated"}

@router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    db = deps.db
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="crosscurrent/branding",
            public_id="logo",
            overwrite=True
        )
        url = result.get("secure_url")
        await db.platform_settings.update_one(
            {},
            {"$set": {"logo_url": url}},
            upsert=True
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload-favicon")
async def upload_favicon(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    db = deps.db
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="crosscurrent/branding",
            public_id="favicon",
            overwrite=True
        )
        url = result.get("secure_url")
        await db.platform_settings.update_one(
            {},
            {"$set": {"favicon_url": url}},
            upsert=True
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload-pwa-icon")
async def upload_pwa_icon(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    db = deps.db
    try:
        # Read file content first
        content = await file.read()
        import io
        
        result = cloudinary.uploader.upload(
            io.BytesIO(content),
            folder="crosscurrent/branding",
            public_id="pwa_icon",
            overwrite=True,
            resource_type="image",
        )
        url = result.get("secure_url")
        await db.platform_settings.update_one(
            {},
            {"$set": {"pwa_icon_url": url}},
            upsert=True
        )
        return {"url": url}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

class PWAIconURLUpdate(BaseModel):
    url: str

@router.put("/pwa-icon-url")
async def set_pwa_icon_url(data: PWAIconURLUpdate, user: dict = Depends(require_admin)):
    """Set PWA icon directly via URL (no upload needed)"""
    db = deps.db
    await db.platform_settings.update_one(
        {},
        {"$set": {"pwa_icon_url": data.url}},
        upsert=True
    )
    return {"url": data.url, "message": "PWA icon URL updated"}

@router.get("/manifest.json")
async def get_pwa_manifest():
    """Serve dynamic PWA manifest with custom icon if set"""
    from fastapi.responses import JSONResponse
    db = deps.db
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    
    pwa_icon_url = settings.get("pwa_icon_url", "") if settings else ""
    platform_name = settings.get("platform_name", "CrossCurrent") if settings else "CrossCurrent"
    
    icons = []
    if pwa_icon_url:
        icons = [
            {"src": pwa_icon_url, "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": pwa_icon_url, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ]
    else:
        icons = [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ]
    
    manifest = {
        "short_name": platform_name,
        "name": f"The {platform_name} Hub",
        "description": "Your complete trading profit management platform",
        "icons": icons,
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#09090b",
        "background_color": "#09090b",
        "orientation": "any",
        "scope": "/",
        "categories": ["finance", "productivity"],
        "prefer_related_applications": False,
    }
    
    return JSONResponse(content=manifest, headers={"Content-Type": "application/manifest+json"})


# ==================== EMAIL TEMPLATES ====================

@router.get("/email-templates")
async def get_email_templates(user: dict = Depends(require_admin)):
    """Get all email templates"""
    db = deps.db
    if user["role"] not in ["master_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin or Master Admin can manage email templates")
    
    templates = await db.email_templates.find({}, {"_id": 0}).to_list(100)
    
    default_templates = [
        {
            "type": "welcome",
            "subject": "Welcome to CrossCurrent Finance Center!",
            "body": "Hello {{name}},\n\nWelcome to CrossCurrent Finance Center! Your account has been created successfully.\n\nYou can now log in and start trading.\n\nBest regards,\nCrossCurrent Team",
            "variables": ["name", "email"]
        },
        {
            "type": "forgot_password",
            "subject": "Reset Your Password - CrossCurrent",
            "body": "Hello {{name}},\n\nWe received a request to reset your password.\n\nClick the link below to reset:\n{{reset_link}}\n\nIf you didn't request this, please ignore this email.\n\nBest regards,\nCrossCurrent Team",
            "variables": ["name", "reset_link"]
        },
        {
            "type": "trade_notification",
            "subject": "New Trading Signal Available!",
            "body": "Hello {{name}},\n\nA new trading signal is available!\n\nProduct: {{product}}\nDirection: {{direction}}\nTime: {{time}}\n\nLog in to your Trade Monitor to execute the trade.\n\nBest regards,\nCrossCurrent Team",
            "variables": ["name", "product", "direction", "time"]
        },
        {
            "type": "trading_signal",
            "subject": "Official Trading Signal: {{direction}} {{product}}",
            "body": "Hello {{name}},\n\nA new official trading signal has been released!\n\nSignal Details:\n- Product: {{product}}\n- Direction: {{direction}}\n- Trade Time: {{time}} ({{timezone}})\n\n<a href=\"{{trade_monitor_url}}\" style=\"display:inline-block;padding:12px 24px;background:#3B82F6;color:white;text-decoration:none;border-radius:8px;margin:16px 0;\">Go to Trade Monitor</a>\n\nDon't miss this opportunity!\n\nBest regards,\nCrossCurrent Team",
            "variables": ["name", "product", "direction", "time", "timezone", "trade_monitor_url", "current_date"]
        },
        {
            "type": "missed_trade",
            "subject": "You Missed Today's Trade",
            "body": "Hello {{name}},\n\nIt looks like you missed today's trading signal.\n\nDon't worry - there will be more opportunities tomorrow!\n\nMake sure to check your Trade Monitor daily.\n\nBest regards,\nCrossCurrent Team",
            "variables": ["name", "date"]
        },
        {
            "type": "license_invite",
            "subject": "You've been invited to CrossCurrent Finance Center",
            "body": "Hello {{name}},\n\nYou have been invited to join CrossCurrent Finance Center as a {{license_type}} Licensee!\n\nClick the link below to complete your registration:\n{{registration_link}}\n\nYour license details:\n- Type: {{license_type}} Licensee\n- Starting Amount: ${{starting_amount}}\n\nThis invite is valid until: {{valid_until}}\n\nBest regards,\nCrossCurrent Team",
            "variables": ["name", "license_type", "registration_link", "starting_amount", "valid_until"]
        },
        {
            "type": "admin_notification",
            "subject": "Admin Notification - {{subject}}",
            "body": "Hello Admin,\n\n{{message}}\n\nBest regards,\nCrossCurrent System",
            "variables": ["subject", "message"]
        },
        {
            "type": "super_admin_notification",
            "subject": "Super Admin Alert - {{subject}}",
            "body": "Hello Super Admin,\n\n{{message}}\n\nThis is an important system notification.\n\nBest regards,\nCrossCurrent System",
            "variables": ["subject", "message"]
        }
    ]
    
    existing_types = {t["type"] for t in templates}
    for default in default_templates:
        if default["type"] not in existing_types:
            templates.append(default)
    
    return {"templates": templates}

@router.put("/email-templates/{template_type}")
async def update_email_template(template_type: str, data: EmailTemplateUpdate, user: dict = Depends(require_admin)):
    """Update an email template"""
    db = deps.db
    if user["role"] not in ["master_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin or Master Admin can manage email templates")
    
    template = {
        "type": template_type,
        "subject": data.subject,
        "body": data.body,
        "variables": data.variables or [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user["id"]
    }
    
    await db.email_templates.update_one(
        {"type": template_type},
        {"$set": template},
        upsert=True
    )
    
    return {"message": "Email template updated successfully"}

@router.post("/email-templates/test")
async def send_test_email(data: TestEmailRequest, user: dict = Depends(require_admin)):
    """Send a test email with the provided template content"""
    db = deps.db
    from services.email_service import send_email
    
    try:
        result = await send_email(
            to=data.to,
            subject=f"[TEST] {data.subject}",
            body=data.body
        )
        
        await db.email_history.insert_one({
            "id": str(uuid.uuid4()),
            "to": data.to,
            "subject": f"[TEST] {data.subject}",
            "template_type": f"test_{data.template_type}",
            "status": "sent" if result else "failed",
            "sent_at": datetime.now(timezone.utc),
            "sent_by": user["id"]
        })
        
        return {"success": True, "message": "Test email sent successfully"}
    except Exception as e:
        await db.email_history.insert_one({
            "id": str(uuid.uuid4()),
            "to": data.to,
            "subject": f"[TEST] {data.subject}",
            "template_type": f"test_{data.template_type}",
            "status": "failed",
            "error": str(e),
            "sent_at": datetime.now(timezone.utc),
            "sent_by": user["id"]
        })
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")


# ==================== INTEGRATION TESTS ====================

@router.post("/test-emailit")
async def test_emailit_connection(user: dict = Depends(require_admin)):
    """Test Emailit API connection by validating the key format"""
    db = deps.db
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    emailit_key = settings.get("emailit_api_key") if settings else None
    
    if not emailit_key:
        emailit_key = os.environ.get("EMAILIT_API_KEY")
    
    if not emailit_key:
        return {"success": False, "message": "Emailit API key not configured"}
    
    if not emailit_key.startswith("em_"):
        return {"success": False, "message": "Invalid Emailit API key format. Key should start with 'em_'"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.emailit.com/v1/emails",
                headers={
                    "Authorization": f"Bearer {emailit_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "test@test.com",
                    "to": "validation@test.com",
                    "subject": "API Key Validation",
                    "html": "<p>Test</p>"
                },
                timeout=10.0
            )
            
            if response.status_code == 401:
                return {"success": False, "message": "Invalid API key - authentication failed"}
            elif response.status_code in [200, 201, 202]:
                return {"success": True, "message": "Emailit API key is valid and working!"}
            elif response.status_code == 422:
                return {"success": True, "message": "Emailit API key is valid! Note: You may need to verify your sender domain."}
            elif response.status_code == 400:
                return {"success": True, "message": "Emailit API key is valid! Configure a verified sender domain to send emails."}
            else:
                return {"success": False, "message": f"Emailit returned status {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}

@router.post("/test-cloudinary")
async def test_cloudinary_connection(user: dict = Depends(require_admin)):
    """Test Cloudinary API connection"""
    db = deps.db
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    
    cloud_name = settings.get("cloudinary_cloud_name") if settings else None
    api_key = settings.get("cloudinary_api_key") if settings else None
    api_secret = settings.get("cloudinary_api_secret") if settings else None
    
    if not all([cloud_name, api_key, api_secret]):
        return {"success": False, "message": "Cloudinary credentials not fully configured"}
    
    try:
        response = requests.get(
            f"https://api.cloudinary.com/v1_1/{cloud_name}/ping",
            auth=(api_key, api_secret),
            timeout=10
        )
        
        if response.status_code == 200:
            return {"success": True, "message": "Cloudinary connection successful!"}
        else:
            return {"success": False, "message": f"Cloudinary returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}

@router.post("/test-heartbeat")
async def test_heartbeat_connection(user: dict = Depends(require_admin)):
    """Test Heartbeat API connection"""
    db = deps.db
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    heartbeat_key = settings.get("heartbeat_api_key") if settings else None
    
    if not heartbeat_key:
        heartbeat_key = os.environ.get("HEARTBEAT_API_KEY")
    
    if not heartbeat_key:
        return {"success": False, "message": "Heartbeat API key not configured"}
    
    if not heartbeat_key.startswith("hb:"):
        return {"success": False, "message": "Invalid Heartbeat API key format. Key should start with 'hb:'"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.heartbeat.chat/v0/users",
                headers={
                    "Authorization": f"Bearer {heartbeat_key}",
                    "Accept": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                user_count = len(data) if isinstance(data, list) else 0
                return {
                    "success": True, 
                    "message": f"Heartbeat connection successful! Found {user_count} community members."
                }
            elif response.status_code == 401:
                return {"success": False, "message": "Invalid API key - authentication failed"}
            elif response.status_code == 403:
                return {"success": False, "message": "API key doesn't have permission to access users"}
            else:
                return {"success": False, "message": f"Heartbeat returned status {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}


# ==================== EMAIL HISTORY ====================

@router.get("/email-history")
async def get_email_history(
    page: int = 1, 
    page_size: int = 20,
    user: dict = Depends(require_admin)
):
    """Get paginated email history (admin only)"""
    db = deps.db
    skip = (page - 1) * page_size
    
    total = await db.email_history.count_documents({})
    
    emails = await db.email_history.find(
        {}, {"_id": 0}
    ).sort("sent_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "emails": emails,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }

@router.delete("/email-history")
async def clear_email_history(user: dict = Depends(require_master_admin)):
    """Clear all email history (master admin only)"""
    db = deps.db
    result = await db.email_history.delete_many({})
    return {"message": f"Cleared {result.deleted_count} email records"}

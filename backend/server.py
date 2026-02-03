from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import requests
import cloudinary
import cloudinary.uploader
import pytz

# Set up logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from services import (
    send_email, get_license_invite_email, get_admin_notification_email,
    upload_file, upload_profile_picture, upload_deposit_screenshot,
    websocket_manager, notify_admins_deposit_request, notify_admins_withdrawal_request,
    notify_user_transaction_status, notify_trade_signal, set_websocket_database
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with Atlas-compatible settings and connection pooling
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise ValueError("MONGO_URL environment variable is required")

# Configure MongoDB client with proper settings for Atlas and high concurrency
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=30000,  # 30 second timeout
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
    retryWrites=True,
    w='majority',
    # Connection pooling for high concurrency
    maxPoolSize=100,  # Maximum connections in the pool
    minPoolSize=10,   # Minimum connections to keep open
    maxIdleTimeMS=45000,  # Close idle connections after 45 seconds
    waitQueueTimeoutMS=10000,  # Wait up to 10 seconds for a connection
)

# Get database name from environment or parse from connection string
db_name = os.environ.get('DB_NAME')
if not db_name:
    # Try to extract from connection string (mongodb+srv://.../<dbname>?... or mongodb+srv://.../<dbname>)
    import re
    # First try with query parameters
    match = re.search(r'/([^/?]+)\?', mongo_url)
    if not match:
        # Try without query parameters (end of string or just the dbname)
        match = re.search(r'/([^/?]+)$', mongo_url)
    if match:
        db_name = match.group(1)
    else:
        db_name = 'crosscurrent_finance'  # Fallback only if not in URL

db = client[db_name]
logger.info(f"Using database: {db_name}")

# JWT Config - No fallback in production
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Heartbeat API
HEARTBEAT_API_KEY = os.environ.get('HEARTBEAT_API_KEY', '')

# Cloudinary Config
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', '')
)

# Emailit Config
EMAILIT_API_KEY = os.environ.get('EMAILIT_API_KEY', '')

# APScheduler for background tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

# Super Admin Secret Code - No insecure fallback
SUPER_ADMIN_SECRET = os.environ.get('SUPER_ADMIN_SECRET', '')

# Master Admin Secret Code - No insecure fallback
MASTER_ADMIN_SECRET = os.environ.get('MASTER_ADMIN_SECRET', '')

# Super Admin Bypass Code (for hidden settings click feature) - No insecure fallback
SUPER_ADMIN_BYPASS = os.environ.get('SUPER_ADMIN_BYPASS', '')

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    'member': 1,        # Normal member - modular dashboard access
    'basic_admin': 2,   # Can manage members, signals, assist with resets
    'super_admin': 3,   # Full access except hidden features
    'master_admin': 4,  # Full access including hidden features
}

# Create the main app
app = FastAPI(title="CrossCurrent Finance Center API", redirect_slashes=False)

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
profit_router = APIRouter(prefix="/profit", tags=["Profit Tracker"])
trade_router = APIRouter(prefix="/trade", tags=["Trade Monitor"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
debt_router = APIRouter(prefix="/debt", tags=["Debt Management"])
goals_router = APIRouter(prefix="/goals", tags=["Profit Planner"])
currency_router = APIRouter(prefix="/currency", tags=["Currency"])
settings_router = APIRouter(prefix="/settings", tags=["Settings"])
api_center_router = APIRouter(prefix="/api-center", tags=["API Center"])
bve_router = APIRouter(prefix="/bve", tags=["Beta Virtual Environment"])

security = HTTPBearer()

# Update logging format (logger already defined at top)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    heartbeat_email: Optional[str] = None
    secret_code: Optional[str] = None  # For admin/super admin/master admin registration

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime
    profile_picture: Optional[str] = None
    lot_size: Optional[float] = None
    timezone: Optional[str] = "UTC"
    allowed_dashboards: Optional[List[str]] = None  # For normal members - modular access
    license_type: Optional[str] = None  # For licensees: "extended" or "honorary"
    trading_start_date: Optional[str] = None  # For new traders: date they started (YYYY-MM-DD)
    trading_type: Optional[str] = None  # "new" or "experienced"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class DepositCreate(BaseModel):
    amount: float
    product: str = "MOIL10"
    currency: str = "USDT"
    notes: Optional[str] = None

class DepositResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    product: Optional[str] = "MOIL10"  # Made optional with default for withdrawals
    currency: str
    notes: Optional[str]
    type: Optional[str] = None
    is_withdrawal: Optional[bool] = False
    created_at: datetime

class TradeLogCreate(BaseModel):
    lot_size: Optional[float] = None  # Optional - backend will recalculate
    direction: str  # BUY or SELL
    actual_profit: float
    commission: Optional[float] = 0  # Daily commission from referrals
    notes: Optional[str] = None

class TradeLogResponse(BaseModel):
    id: str
    user_id: str
    lot_size: float
    direction: str
    projected_profit: float
    actual_profit: float
    commission: Optional[float] = 0  # Daily commission from referrals
    profit_difference: float
    performance: str
    signal_id: Optional[str]
    created_at: datetime

class TradingSignalCreate(BaseModel):
    product: str = "MOIL10"
    trade_time: str  # HH:MM format
    trade_timezone: str = "Asia/Manila"  # Default to Philippine time
    direction: str  # BUY or SELL
    profit_points: float = 15  # Default profit multiplier
    notes: Optional[str] = None
    is_official: bool = False  # Official trading signal flag

class TradingSignalUpdate(BaseModel):
    trade_time: Optional[str] = None
    trade_timezone: Optional[str] = None
    direction: Optional[str] = None
    profit_points: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    is_official: Optional[bool] = None  # Official trading signal flag

class TradingSignalResponse(BaseModel):
    id: str
    product: str
    trade_time: str
    trade_timezone: str
    direction: str
    profit_points: float
    notes: Optional[str]
    is_active: bool
    is_official: bool = False  # Official trading signal flag
    is_simulated: bool = False
    created_by: str
    created_at: datetime

class DebtCreate(BaseModel):
    name: str
    total_amount: float
    minimum_payment: float
    due_day: int
    interest_rate: Optional[float] = 0
    currency: str = "USD"

class DebtResponse(BaseModel):
    id: str
    user_id: str
    name: str
    total_amount: float
    remaining_amount: float
    minimum_payment: float
    due_day: int
    interest_rate: float
    currency: str
    created_at: datetime

class GoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: Optional[float] = 0
    target_date: Optional[datetime] = None
    price_type: str = "fixed"  # fixed or market
    market_item: Optional[str] = None
    currency: str = "USD"

class GoalResponse(BaseModel):
    id: str
    user_id: str
    name: str
    target_amount: float
    current_amount: float
    target_date: Optional[datetime]
    price_type: str
    market_item: Optional[str]
    currency: str
    progress_percentage: float
    created_at: datetime

class PlatformSettings(BaseModel):
    platform_name: str = "CrossCurrent"
    tagline: str = "Finance Center"
    site_title: str = "CrossCurrent Finance Center"
    site_description: str = "Trading profit management platform"
    favicon_url: Optional[str] = None
    logo_url: Optional[str] = None
    og_image_url: Optional[str] = None
    primary_color: str = "#3B82F6"
    accent_color: str = "#06B6D4"
    hide_emergent_badge: bool = False
    # Login Customization
    login_title: Optional[str] = None
    login_tagline: Optional[str] = None
    login_notice: str = "Only CrossCurrent community members can access this platform."
    # Production URL
    production_site_url: Optional[str] = None
    # Integration API Keys
    emailit_api_key: Optional[str] = None
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    heartbeat_api_key: Optional[str] = None
    # Custom Links
    custom_registration_link: Optional[str] = None
    # Footer Settings
    footer_copyright: str = "© 2024 CrossCurrent Finance Center. All rights reserved."
    footer_links: Optional[List[dict]] = None  # [{label: "Privacy", url: "/privacy"}, ...]
    # Maintenance Settings
    maintenance_mode: bool = False
    maintenance_message: str = "Our services are undergoing maintenance, and will be back soon!"
    # Announcements
    announcements: Optional[List[dict]] = None  # List of announcement dicts
    # Content Protection Settings (copy/screenshot prevention)
    content_protection_enabled: bool = False
    content_protection_watermark: bool = True  # Show user watermark overlay
    content_protection_watermark_custom: Optional[str] = None  # Custom watermark text (Master Admin only)
    content_protection_disable_copy: bool = True  # Disable text selection and copy
    content_protection_disable_rightclick: bool = True  # Disable right-click context menu
    content_protection_disable_shortcuts: bool = True  # Block Ctrl+C, PrtScn, etc.

class LicenseType(str, Enum):
    STANDARD = "standard"
    EXTENDED = "extended"
    HONORARY = "honorary"

class LicenseCreate(BaseModel):
    user_id: str
    license_type: str  # extended or honorary
    starting_amount: float
    start_date: Optional[str] = None  # YYYY-MM-DD format
    notes: Optional[str] = None

class LicenseResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    license_type: str
    starting_amount: float
    current_amount: float
    start_date: str
    notes: Optional[str] = None
    is_active: bool
    created_at: str
    created_by: str

# License Invite Models
class LicenseInviteCreate(BaseModel):
    license_type: str  # extended or honorary
    starting_amount: float
    valid_duration: str  # 3_months, 6_months, 1_year, indefinite
    max_uses: int = 1
    notes: Optional[str] = None
    invitee_email: Optional[str] = None
    invitee_name: Optional[str] = None
    effective_start_date: Optional[str] = None  # YYYY-MM-DD format for when trading starts

class LicenseInviteUpdate(BaseModel):
    valid_duration: Optional[str] = None
    max_uses: Optional[int] = None
    notes: Optional[str] = None
    invitee_email: Optional[str] = None
    invitee_name: Optional[str] = None
    effective_start_date: Optional[str] = None  # Can update the effective start date

# Email Template Models
class EmailTemplateType(str, Enum):
    WELCOME = "welcome"
    FORGOT_PASSWORD = "forgot_password"
    TRADE_NOTIFICATION = "trade_notification"
    MISSED_TRADE = "missed_trade"
    LICENSE_INVITE = "license_invite"
    ADMIN_NOTIFICATION = "admin_notification"
    SUPER_ADMIN_NOTIFICATION = "super_admin_notification"

class EmailTemplateUpdate(BaseModel):
    subject: str
    body: str
    variables: Optional[List[str]] = None  # Available template variables like {{name}}, {{link}}

# Licensee Trade Override Model
class LicenseeTradeOverride(BaseModel):
    license_id: str
    date: str  # YYYY-MM-DD format
    traded: bool
    notes: Optional[str] = None

# Licensee Transaction Models
class LicenseeTransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    REJECTED = "rejected"

class LicenseeDepositCreate(BaseModel):
    amount: float
    deposit_date: str
    notes: Optional[str] = None
    # screenshot_url will be added after file upload

class LicenseeWithdrawalCreate(BaseModel):
    amount: float
    notes: Optional[str] = None

class LicenseeTransactionFeedback(BaseModel):
    message: str
    status: Optional[str] = None  # pending, processing, awaiting_confirmation, completed, rejected
    final_amount: Optional[float] = None
    # screenshot_url will be added after file upload

class NotificationCreate(BaseModel):
    type: str  # deposit, withdrawal, trade_underperform
    title: str
    message: str
    user_id: str  # The user who triggered the notification
    user_name: str
    amount: Optional[float] = None
    metadata: Optional[Dict] = None

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    user_id: str
    user_name: str
    amount: Optional[float] = None
    metadata: Optional[Dict] = None
    is_read: bool = False
    created_at: datetime

class APIConnectionCreate(BaseModel):
    name: str
    endpoint_url: str
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    is_active: bool = True

class APIConnectionResponse(BaseModel):
    id: str
    name: str
    endpoint_url: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]

class WithdrawalSimulation(BaseModel):
    amount: float
    from_currency: str = "USDT"
    to_currency: str = "USD"

class RoleUpgrade(BaseModel):
    user_id: str
    new_role: str  # basic_admin, admin, super_admin
    secret_code: Optional[str] = None

# ==================== HELPERS ====================

async def create_admin_notification(notification_type: str, title: str, message: str, user_id: str, user_name: str, amount: float = None, metadata: dict = None):
    """Create a notification for admins about member activity and broadcast via WebSocket"""
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
        "visibility": "admin",  # admin-only notification
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_notifications.insert_one(notification)
    
    # Also broadcast to connected admins via WebSocket
    try:
        await websocket_manager.broadcast_to_admins(notification)
    except Exception as e:
        logger.error(f"Failed to broadcast admin notification: {e}")
    
    return notification

async def create_member_notification(notification_type: str, title: str, message: str, triggered_by_id: str = None, triggered_by_name: str = None, amount: float = None, metadata: dict = None):
    """Create a notification visible to all members and broadcast via WebSocket"""
    notification = {
        "id": str(uuid.uuid4()),
        "type": notification_type,
        "title": title,
        "message": message,
        "triggered_by_id": triggered_by_id,
        "triggered_by_name": triggered_by_name,
        "amount": amount,
        "metadata": metadata or {},
        "visibility": "all",  # visible to all users
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.member_notifications.insert_one(notification)
    
    # Broadcast to all connected users via WebSocket
    try:
        await websocket_manager.broadcast_to_all(notification)
    except Exception as e:
        logger.error(f"Failed to broadcast member notification: {e}")
    
    return notification

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_basic_admin(user: dict = Depends(get_current_user)):
    """Require at least basic_admin role"""
    admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
    if user.get("role") not in admin_roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_admin(user: dict = Depends(get_current_user)):
    """Require at least admin role (legacy compatibility - same as basic_admin)"""
    admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
    if user.get("role") not in admin_roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_super_admin(user: dict = Depends(get_current_user)):
    """Require at least super_admin role"""
    if user.get("role") not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user

async def require_master_admin(user: dict = Depends(get_current_user)):
    """Require master_admin role (full access including hidden features)"""
    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Master admin access required")
    return user

async def require_super_or_master_admin(user: dict = Depends(get_current_user)):
    """Require super_admin or master_admin role"""
    if user.get("role") not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Super admin or master admin access required")
    return user

async def verify_heartbeat_user(email: str) -> bool:
    """Verify if user exists in Heartbeat community"""
    if not HEARTBEAT_API_KEY:
        logger.warning("Heartbeat API key not configured, skipping verification")
        return True
    
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
                # Handle both list and dict responses
                if isinstance(data, list):
                    users = data
                else:
                    users = data.get("users", data.get("data", []))
                
                if isinstance(users, list):
                    for user in users:
                        if isinstance(user, dict) and user.get("email", "").lower() == email.lower():
                            return True
            return False
    except Exception as e:
        logger.error(f"Heartbeat verification error: {e}")
        return True  # Allow on error for development

def calculate_exit_value(lot_size: float) -> float:
    """Calculate exit value: LOT Size × 15"""
    return lot_size * 15

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

# ==================== AUTH ROUTES ====================

@auth_router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verify Heartbeat membership
    heartbeat_email = data.heartbeat_email or data.email
    is_heartbeat_user = await verify_heartbeat_user(heartbeat_email)
    if not is_heartbeat_user:
        raise HTTPException(
            status_code=403, 
            detail="You must be a Heartbeat community member to register. Please join the community first."
        )
    
    # Determine role based on secret code
    role = "member"  # Default to normal member
    if data.secret_code:
        if data.secret_code == MASTER_ADMIN_SECRET:
            role = "master_admin"
        elif data.secret_code == SUPER_ADMIN_SECRET:
            role = "super_admin"
    
    # Default dashboards for normal members
    default_dashboards = ["dashboard", "profit_tracker", "trade_monitor", "profile"]
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email.lower(),
        "password": hash_password(data.password),
        "full_name": data.full_name,
        "heartbeat_email": heartbeat_email.lower(),
        "role": role,
        "profile_picture": None,
        "lot_size": 0.01,
        "timezone": "UTC",
        "allowed_dashboards": default_dashboards if role == "member" else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    # Send notification to all admins about new registration
    await create_admin_notification(
        notification_type="new_user",
        title="New User Registered",
        message=f"{data.full_name} has joined the platform",
        user_id=user_id,
        user_name=data.full_name,
        metadata={"email": data.email.lower(), "role": role}
    )
    
    # Send notification to all members about new member (community notification)
    await create_member_notification(
        notification_type="new_member",
        title="New Member Joined",
        message=f"Welcome {data.full_name} to the community!",
        triggered_by_id=user_id,
        triggered_by_name=data.full_name,
        metadata={"email": data.email.lower()}
    )
    
    # Send email notification to admins
    try:
        from services.email_service import send_registration_notification_to_admins
        await send_registration_notification_to_admins(data.full_name, data.email)
    except Exception as e:
        print(f"Failed to send email notification: {e}")
    
    token = create_token(user_id, data.email, role)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=data.email,
            full_name=data.full_name,
            role=role,
            created_at=datetime.fromisoformat(user["created_at"]),
            allowed_dashboards=user.get("allowed_dashboards"),
            license_type=user.get("license_type")
        )
    )

@auth_router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is deactivated
    if user.get("is_deactivated"):
        raise HTTPException(
            status_code=403, 
            detail="Your account has been deactivated. Please contact your inviter to reactivate your account."
        )
    
    # Skip Heartbeat verification for admins and licensees
    admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
    is_licensee = user.get("license_type") is not None
    
    # For licensees, check if their license is still active
    if is_licensee:
        active_license = await db.licenses.find_one({
            "user_id": user["id"], 
            "is_active": True
        }, {"_id": 0})
        
        if not active_license:
            # License has been revoked or deleted
            raise HTTPException(
                status_code=403, 
                detail="Your license has been revoked or expired. Please contact the administrator to renew your license."
            )
    elif user.get("role") not in admin_roles:
        # Non-admin, non-licensee - check Heartbeat membership
        heartbeat_email = user.get("heartbeat_email", user["email"])
        is_heartbeat_user = await verify_heartbeat_user(heartbeat_email)
        if not is_heartbeat_user:
            raise HTTPException(
                status_code=403, 
                detail="Your Heartbeat membership could not be verified. Please ensure you're still a community member."
            )
    
    token = create_token(user["id"], user["email"], user["role"])
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"],
            profile_picture=user.get("profile_picture"),
            lot_size=user.get("lot_size"),
            timezone=user.get("timezone", "UTC"),
            allowed_dashboards=user.get("allowed_dashboards"),
            license_type=user.get("license_type")
        )
    )

@auth_router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"],
        profile_picture=user.get("profile_picture"),
        lot_size=user.get("lot_size"),
        timezone=user.get("timezone", "UTC"),
        allowed_dashboards=user.get("allowed_dashboards"),
        license_type=user.get("license_type"),
        trading_start_date=user.get("trading_start_date"),  # For filtering past dates
        trading_type=user.get("trading_type")  # "new" or "experienced"
    )

class VerifyPasswordRequest(BaseModel):
    password: str

@auth_router.post("/verify-password")
async def verify_user_password(data: VerifyPasswordRequest, user: dict = Depends(get_current_user)):
    """Verify the current user's password"""
    db_user = await db.users.find_one({"id": user["id"]})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_valid = bcrypt.checkpw(data.password.encode(), db_user["password"].encode())
    return {"valid": is_valid}

class HeartbeatVerifyRequest(BaseModel):
    email: str

@auth_router.post("/verify-heartbeat")
async def verify_heartbeat_membership(data: HeartbeatVerifyRequest):
    """Verify if email is a Heartbeat member and return user info if exists"""
    email = data.email.lower().strip()
    
    # Get Heartbeat API key from settings, fallback to environment variable
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    heartbeat_api_key = settings.get("heartbeat_api_key") if settings else None
    
    # Fallback to environment variable if not in settings
    if not heartbeat_api_key:
        heartbeat_api_key = os.environ.get("HEARTBEAT_API_KEY")
    
    if not heartbeat_api_key:
        raise HTTPException(status_code=500, detail="Heartbeat integration not configured. Please add your Heartbeat API key in Admin Settings > Integrations.")
    
    # Verify with Heartbeat using the query parameter format (same as verify_heartbeat_user)
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.heartbeat.chat/v0/users",
                headers={"Authorization": f"Bearer {heartbeat_api_key}"},
                params={"email": email},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle both list and dict responses
                users = []
                if isinstance(data, list):
                    users = data
                else:
                    users = data.get("users", data.get("data", []))
                
                # Find the user with matching email
                heartbeat_user = None
                if isinstance(users, list):
                    for u in users:
                        if isinstance(u, dict) and u.get("email", "").lower() == email.lower():
                            heartbeat_user = u
                            break
                
                if heartbeat_user:
                    heartbeat_user_id = heartbeat_user.get("id")
                    
                    # Check if user already exists in our DB
                    existing_user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1, "full_name": 1, "password": 1})
                    
                    return {
                        "verified": True,
                        "user": {
                            "email": email,
                            "full_name": heartbeat_user.get("name", email.split('@')[0]),
                            "heartbeat_id": heartbeat_user_id,
                            "has_password": existing_user is not None and existing_user.get("password") is not None
                        }
                    }
            
            return {"verified": False, "user": None}
    except Exception as e:
        print(f"Heartbeat verification error: {e}")
        return {"verified": False, "user": None}

class SetPasswordRequest(BaseModel):
    email: str
    password: str

@auth_router.post("/set-password")
async def set_password_for_member(data: SetPasswordRequest):
    """Set password for a verified Heartbeat member"""
    email = data.email.lower().strip()
    password = data.password  # Store password before any overwrites
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Verify Heartbeat membership first - check settings then fallback to env
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    heartbeat_api_key = settings.get("heartbeat_api_key") if settings else None
    
    # Fallback to environment variable if not in settings
    if not heartbeat_api_key:
        heartbeat_api_key = os.environ.get("HEARTBEAT_API_KEY")
    
    if not heartbeat_api_key:
        raise HTTPException(status_code=500, detail="Heartbeat integration not configured. Please add your Heartbeat API key in Admin Settings > Integrations.")
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.heartbeat.chat/v0/users",
                headers={"Authorization": f"Bearer {heartbeat_api_key}"},
                params={"email": email},
                timeout=10.0
            )
            
            if response.status_code == 200:
                hb_response = response.json()
                # Handle both list and dict responses
                users = []
                if isinstance(hb_response, list):
                    users = hb_response
                else:
                    users = hb_response.get("users", hb_response.get("data", []))
                
                # Find the user with matching email
                heartbeat_user = None
                if isinstance(users, list):
                    for u in users:
                        if isinstance(u, dict) and u.get("email", "").lower() == email.lower():
                            heartbeat_user = u
                            break
                
                if not heartbeat_user:
                    raise HTTPException(status_code=400, detail="Email not verified with Heartbeat")
                
                heartbeat_user_id = heartbeat_user.get("id")
                full_name = heartbeat_user.get("name", email.split('@')[0])
            else:
                raise HTTPException(status_code=400, detail="Failed to verify Heartbeat membership")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Heartbeat verification error: {e}")
        raise HTTPException(status_code=400, detail="Failed to verify Heartbeat membership")
    
    # Hash password
    hashed_password = hash_password(password)
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        # Update existing user's password
        await db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )
        return {"message": "Password updated successfully"}
    else:
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = {
            "id": user_id,
            "email": email,
            "password": hashed_password,
            "full_name": full_name,
            "role": "member",
            "heartbeat_user_id": heartbeat_user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_suspended": False,
            "lot_size": 0.01,
            "timezone": "Asia/Manila",
            "allowed_dashboards": ["dashboard", "profit_tracker", "trade_monitor", "profile"]
        }
        await db.users.insert_one(new_user)
        return {"message": "Account created successfully"}

class SecretUpgradeRequest(BaseModel):
    user_id: str
    new_role: str
    secret_code: str

@auth_router.post("/secret-upgrade")
async def secret_upgrade(data: SecretUpgradeRequest, user: dict = Depends(get_current_user)):
    """Secret endpoint to upgrade user role with bypass code (triggered by 10x Settings click)"""
    
    # Only allow upgrade to super_admin
    if data.new_role != "super_admin":
        raise HTTPException(status_code=400, detail="Invalid upgrade request")
    
    # Verify bypass code
    if data.secret_code != SUPER_ADMIN_BYPASS:
        raise HTTPException(status_code=403, detail="Invalid secret code")
    
    # User can only upgrade themselves
    if data.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Can only upgrade yourself")
    
    # Don't downgrade master_admin
    if user["role"] == "master_admin":
        raise HTTPException(status_code=400, detail="Master admin cannot be downgraded")
    
    # Upgrade the user
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"role": "super_admin", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Successfully upgraded to Super Admin"}

# ==================== USER ROUTES ====================

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    lot_size: Optional[float] = None

@users_router.put("/profile")
async def update_profile(data: ProfileUpdate, user: dict = Depends(get_current_user)):
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.full_name:
        update_data["full_name"] = data.full_name
    if data.timezone:
        update_data["timezone"] = data.timezone
    if data.lot_size is not None:
        update_data["lot_size"] = data.lot_size
    
    await db.users.update_one({"id": user["id"]}, {"$set": update_data})
    
    # Return updated user
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0})
    return updated_user

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@users_router.post("/change-password")
async def change_password(data: PasswordChange, user: dict = Depends(get_current_user)):
    # Get user with password
    full_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(data.current_password, full_user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    new_hash = hash_password(data.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Password changed successfully"}

@users_router.post("/profile-picture")
async def upload_profile_picture(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
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

# ==================== PROFIT TRACKER ROUTES ====================

@profit_router.post("/deposits", response_model=DepositResponse)
async def create_deposit(data: DepositCreate, user: dict = Depends(get_current_user)):
    deposit_id = str(uuid.uuid4())
    deposit = {
        "id": deposit_id,
        "user_id": user["id"],
        "amount": data.amount,
        "product": data.product,
        "currency": data.currency,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deposits.insert_one(deposit)
    
    # Create notification for admins
    await create_admin_notification(
        notification_type="deposit",
        title="New Deposit",
        message=f"{user['full_name']} deposited ${data.amount:.2f}",
        user_id=user["id"],
        user_name=user["full_name"],
        amount=data.amount,
        metadata={"product": data.product, "currency": data.currency}
    )
    
    return DepositResponse(**{**deposit, "created_at": datetime.fromisoformat(deposit["created_at"])})

@profit_router.get("/deposits", response_model=List[DepositResponse])
async def get_deposits(user: dict = Depends(get_current_user)):
    deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    return [DepositResponse(**{**d, "created_at": datetime.fromisoformat(d["created_at"]) if isinstance(d["created_at"], str) else d["created_at"]}) for d in deposits]

@profit_router.get("/summary")
async def get_profit_summary(user: dict = Depends(get_current_user)):
    """Get financial summary for the current user - uses unified calculation utility
    
    NOTE: For Master Admin, account_value is the actual Merin balance.
    Licensee funds are ALREADY PART OF this balance (they deposited into it).
    We do NOT add licensee funds on top.
    """
    from utils.calculations import get_user_financial_summary
    
    summary = await get_user_financial_summary(db, user["id"], user)
    
    return {
        "total_deposits": summary["total_deposits"],
        "total_projected_profit": summary["total_projected_profit"],
        "total_actual_profit": summary["total_profit"],
        "profit_difference": round(summary["total_profit"] - summary["total_projected_profit"], 2),
        "account_value": summary["account_value"],
        "total_trades": summary["total_trades"],
        "performance_rate": summary["performance_rate"],
        "is_licensee": summary.get("is_licensee", False),
        "license_type": summary.get("license_type")
    }

@profit_router.post("/calculate-exit")
async def calculate_exit(lot_size: float):
    exit_value = calculate_exit_value(lot_size)
    return {
        "lot_size": lot_size,
        "exit_value": exit_value,
        "formula": "LOT Size × 15"
    }

@profit_router.post("/simulate-withdrawal")
async def simulate_withdrawal(data: WithdrawalSimulation, user: dict = Depends(get_current_user)):
    """Simulate withdrawal with fee calculation - uses unified account value calculation"""
    from utils.calculations import calculate_account_value
    
    fees = calculate_withdrawal_fees(data.amount)
    
    # Get current account value using unified calculation
    account_value = await calculate_account_value(db, user["id"], user)
    
    if data.amount > account_value:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    return {
        **fees,
        "current_balance": round(account_value, 2),
        "balance_after_withdrawal": round(account_value - data.amount, 2)
    }

@profit_router.delete("/reset")
async def reset_profit_tracker(user: dict = Depends(get_current_user)):
    """Reset all profit tracker data for the current user"""
    # Delete deposits
    await db.deposits.delete_many({"user_id": user["id"]})
    # Delete trade logs
    await db.trade_logs.delete_many({"user_id": user["id"]})
    
    return {"message": "Profit tracker reset successfully", "deleted": True}

class WithdrawalRequest(BaseModel):
    amount: float
    notes: Optional[str] = ""

def add_business_days(start_date, days):
    """Add business days to a date, skipping weekends"""
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday to Friday
            added += 1
    return current

@profit_router.post("/withdrawal")
async def record_withdrawal(data: WithdrawalRequest, user: dict = Depends(get_current_user)):
    """Record a withdrawal from the Merin account"""
    # Calculate fees (Binance fee moved to deposit)
    merin_fee = data.amount * 0.03  # 3% Merin fee only
    net_amount = data.amount - merin_fee
    
    # Calculate estimated arrival date (2 business days)
    estimated_arrival = add_business_days(datetime.now(timezone.utc), 2)
    
    # Record as negative deposit (withdrawal)
    withdrawal = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": -data.amount,  # Negative to indicate withdrawal
        "product": "WITHDRAWAL",  # Mark as withdrawal type
        "currency": "USDT",
        "notes": data.notes or "Withdrawal to Binance",
        "is_withdrawal": True,
        "gross_amount": data.amount,
        "merin_fee": merin_fee,
        "net_amount": net_amount,
        "estimated_arrival": estimated_arrival.strftime("%Y-%m-%d"),
        "confirmed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.deposits.insert_one(withdrawal)
    
    # Create notification for admins
    await create_admin_notification(
        notification_type="withdrawal",
        title="New Withdrawal",
        message=f"{user['full_name']} withdrew ${data.amount:.2f}",
        user_id=user["id"],
        user_name=user["full_name"],
        amount=data.amount,
        metadata={"net_amount": net_amount, "merin_fee": merin_fee}
    )
    
    return {
        "message": "Withdrawal recorded successfully",
        "withdrawal_id": withdrawal["id"],
        "gross_amount": data.amount,
        "merin_fee": round(merin_fee, 2),
        "net_amount": round(net_amount, 2)
    }

@profit_router.get("/withdrawals")
async def get_withdrawals(user: dict = Depends(get_current_user)):
    """Get all withdrawals for the current user (includes is_withdrawal=True OR negative amounts)"""
    withdrawals = await db.deposits.find(
        {
            "user_id": user["id"], 
            "$or": [
                {"is_withdrawal": True},
                {"amount": {"$lt": 0}}  # Also include negative amounts
            ]
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return withdrawals

class ConfirmReceiptRequest(BaseModel):
    confirmed_at: str

@profit_router.put("/withdrawals/{withdrawal_id}/confirm")
async def confirm_withdrawal_receipt(
    withdrawal_id: str, 
    data: ConfirmReceiptRequest,
    user: dict = Depends(get_current_user)
):
    """Confirm receipt of a withdrawal"""
    result = await db.deposits.update_one(
        {"id": withdrawal_id, "user_id": user["id"], "is_withdrawal": True},
        {"$set": {"confirmed_at": data.confirmed_at}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    return {"message": "Receipt confirmed", "confirmed_at": data.confirmed_at}

# Commission Model
class CommissionCreate(BaseModel):
    amount: float
    traders_count: int
    notes: Optional[str] = None
    commission_date: Optional[str] = None  # Date to tie the commission to (YYYY-MM-DD)

@profit_router.post("/commission")
async def record_commission(data: CommissionCreate, user: dict = Depends(get_current_user)):
    """Record a commission from referral trades"""
    # Use the specified commission date or default to today
    commission_date = data.commission_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    commission = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": data.amount,
        "traders_count": data.traders_count,
        "notes": data.notes or f"Commission from {data.traders_count} referral trades",
        "commission_date": commission_date,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.commissions.insert_one(commission)
    
    # Also record as a deposit (commission adds to account balance)
    deposit = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": data.amount,
        "product": "COMMISSION",
        "currency": "USDT",
        "notes": f"Referral commission ({data.traders_count} traders)",
        "is_commission": True,
        "commission_date": commission_date,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deposits.insert_one(deposit)
    
    return {
        "message": "Commission recorded successfully",
        "commission_id": commission["id"],
        "amount": data.amount,
        "traders_count": data.traders_count,
        "commission_date": commission_date
    }

@profit_router.get("/commissions")
async def get_commissions(user: dict = Depends(get_current_user)):
    """Get all commissions for the current user"""
    commissions = await db.commissions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return commissions


@profit_router.get("/vsd")
async def get_virtual_share_distribution(user: dict = Depends(require_master_admin)):
    """Get Virtual Share Distribution (VSD) for Master Admin.
    
    Shows how the Master Admin's Merin balance is distributed:
    - Total Pool (Master Admin's Merin balance - the actual trading account)
    - Master Admin's remaining portion (their share after licensee allocations)
    - Total licensee virtual shares
    - Breakdown per licensee (Current Balance, Total Deposit, Total Profit, % Share)
    
    NOTE: Licensee funds are PART OF the total pool (they deposited into it).
    """
    from utils.calculations import get_master_admin_financial_breakdown as get_breakdown
    
    breakdown = await get_breakdown(db, user["id"], user)
    return breakdown


# ==================== TRADE MONITOR ROUTES ====================

@trade_router.post("/log", response_model=TradeLogResponse)
async def log_trade(data: TradeLogCreate, user: dict = Depends(get_current_user)):
    # CRITICAL: Always recalculate lot_size from the authoritative account_value
    # to prevent stale frontend values from corrupting trade history
    from utils.calculations import calculate_account_value, calculate_lot_size
    
    account_value = await calculate_account_value(db, user["id"], user)
    lot_size = calculate_lot_size(account_value)
    
    # Log for debugging
    logger.info(f"Trade log: user={user['id']}, account_value={account_value}, calculated_lot_size={lot_size}, frontend_lot_size={data.lot_size}, commission={data.commission}")
    
    projected_profit = calculate_exit_value(lot_size)
    profit_difference = data.actual_profit - projected_profit
    
    # Determine performance
    if abs(profit_difference) < 0.01:
        performance = "perfect"
    elif profit_difference > 0:
        performance = "exceeded"
    else:
        performance = "below"
    
    # Get active signal - USE SIGNAL DIRECTION AS SOURCE OF TRUTH
    active_signal = await db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    
    # Direction should come from the official signal, not from frontend
    # This ensures trade history matches signal history
    trade_direction = active_signal.get("direction") if active_signal else data.direction
    
    trade_id = str(uuid.uuid4())
    trade = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": lot_size,  # Use server-calculated lot_size
        "direction": trade_direction,  # Use signal direction as source of truth
        "projected_profit": projected_profit,
        "actual_profit": data.actual_profit,
        "commission": data.commission or 0,  # Daily commission from referrals
        "profit_difference": profit_difference,
        "performance": performance,
        "signal_id": active_signal["id"] if active_signal else None,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trade_logs.insert_one(trade)
    
    # Create notification if member exited below projected amount (admin-only)
    if performance == "below" and profit_difference < -5:  # Only notify if more than $5 below
        await create_admin_notification(
            notification_type="trade_underperform",
            title="Underperforming Trade",
            message=f"{user['full_name']} exited ${abs(profit_difference):.2f} below projected",
            user_id=user["id"],
            user_name=user["full_name"],
            amount=data.actual_profit,
            metadata={
                "projected": projected_profit,
                "actual": data.actual_profit,
                "difference": profit_difference,
                "lot_size": lot_size,
                "commission": data.commission or 0
            }
        )
    
    # Create notification for all members about profit submission (community notification)
    await create_member_notification(
        notification_type="profit_submitted",
        title="Profit Reported",
        message=f"{user['full_name']} reported ${data.actual_profit:.2f} profit",
        triggered_by_id=user["id"],
        triggered_by_name=user["full_name"],
        amount=data.actual_profit,
        metadata={"performance": performance, "lot_size": lot_size}
    )
    
    return TradeLogResponse(**{**trade, "created_at": datetime.fromisoformat(trade["created_at"])})

@trade_router.get("/logs", response_model=List[TradeLogResponse])
async def get_trade_logs(limit: int = 50, user_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    # For admins, allow fetching another user's logs
    target_user_id = user["id"]
    if user_id and user["role"] in ["basic_admin", "admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    trades = await db.trade_logs.find(
        {"user_id": target_user_id}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return [TradeLogResponse(**{**t, "created_at": datetime.fromisoformat(t["created_at"]) if isinstance(t["created_at"], str) else t["created_at"]}) for t in trades]

@trade_router.get("/history")
async def get_trade_history(
    page: int = 1, 
    page_size: int = 10,
    user_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get paginated trade history with signal details.
    Admins can pass user_id to view another user's history (for simulation).
    """
    # Determine which user's history to fetch
    target_user_id = user["id"]
    
    # If user_id provided and requester is admin, use that user_id
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    skip = (page - 1) * page_size
    
    # Get total count
    total = await db.trade_logs.count_documents({"user_id": target_user_id})
    
    # Get paginated trades
    trades = await db.trade_logs.find(
        {"user_id": target_user_id}, 
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Batch fetch all signal IDs to avoid N+1 query problem
    signal_ids = list(set(trade.get("signal_id") for trade in trades if trade.get("signal_id")))
    signals_map = {}
    if signal_ids:
        signals = await db.trading_signals.find(
            {"id": {"$in": signal_ids}}, 
            {"_id": 0, "id": 1, "product": 1, "trade_time": 1, "trade_timezone": 1, "direction": 1}
        ).to_list(len(signal_ids))
        signals_map = {s["id"]: s for s in signals}
    
    # Enrich with signal details (using pre-fetched signals)
    enriched_trades = []
    for trade in trades:
        signal_details = None
        signal_id = trade.get("signal_id")
        signal_direction = trade.get("direction")  # Default to stored direction
        
        if signal_id and signal_id in signals_map:
            signal = signals_map[signal_id]
            signal_details = {
                "product": signal.get("product", "MOIL10"),
                "trade_time": signal.get("trade_time"),
                "trade_timezone": signal.get("trade_timezone", "Asia/Manila"),
            }
            # Use signal direction as the source of truth
            signal_direction = signal.get("direction", trade.get("direction"))
        
        enriched_trades.append({
            **trade,
            "direction": signal_direction,  # Override with signal direction
            "commission": trade.get("commission", 0),  # Default to 0 for backward compatibility
            "created_at": datetime.fromisoformat(trade["created_at"]) if isinstance(trade["created_at"], str) else trade["created_at"],
            "signal_details": signal_details,
            "time_entered": trade.get("time_entered"),  # User-editable field
        })
    
    return {
        "trades": enriched_trades,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }

class UpdateTradeTimeEntered(BaseModel):
    time_entered: str  # HH:MM format

@trade_router.put("/logs/{trade_id}/time-entered")
async def update_trade_time_entered(
    trade_id: str, 
    data: UpdateTradeTimeEntered, 
    user: dict = Depends(get_current_user)
):
    """Update the time entered for a trade log"""
    result = await db.trade_logs.update_one(
        {"id": trade_id, "user_id": user["id"]},
        {"$set": {"time_entered": data.time_entered}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return {"message": "Time entered updated", "time_entered": data.time_entered}

@trade_router.get("/streak")
async def get_trade_streak(user_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Calculate current streak of consecutive trading days (regardless of profit/loss).
    Admins can pass user_id to view another user's streak.
    """
    # Determine target user
    target_user_id = user["id"]
    target_user = user
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
        # Fetch the target user's data for streak_reset_date
        target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not target_user:
            target_user = user
    
    # Check if user has a streak reset date (from "did not trade" action)
    streak_reset_date = target_user.get("streak_reset_date")
    streak_reset_filter = None
    if streak_reset_date:
        try:
            reset_date = datetime.strptime(streak_reset_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            # Only count trades AFTER the reset date
            streak_reset_filter = reset_date.isoformat()
        except:
            pass
    
    # Fetch global holidays from database instead of hardcoded list
    global_holidays_cursor = db.global_holidays.find({}, {"_id": 0, "date": 1})
    global_holidays_list = await global_holidays_cursor.to_list(1000)
    HOLIDAYS = set()
    for h in global_holidays_list:
        try:
            # Parse date string to tuple (year, month, day)
            date_str = h.get("date", "")
            if date_str:
                parts = date_str.split("-")
                if len(parts) == 3:
                    HOLIDAYS.add((int(parts[0]), int(parts[1]), int(parts[2])))
        except:
            continue
    
    def is_trading_day(d):
        """Check if a date is a trading day (not weekend, not holiday)"""
        # Skip weekends
        if d.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        # Skip holidays - holidays are treated like weekends (don't break streak)
        if (d.year, d.month, d.day) in HOLIDAYS:
            return False
        return True
    
    def get_previous_trading_day(d):
        """Get the previous trading day, skipping weekends and holidays"""
        prev = d - timedelta(days=1)
        attempts = 0
        while not is_trading_day(prev) and attempts < 14:  # Look back up to 2 weeks
            prev = prev - timedelta(days=1)
            attempts += 1
        return prev if attempts < 14 else None
    
    # Build query - exclude "did not trade" entries from streak calculation
    query = {
        "user_id": target_user_id,
        "did_not_trade": {"$ne": True}  # Exclude "did not trade" entries
    }
    
    # If there's a streak reset date, only count trades after that date
    if streak_reset_filter:
        query["created_at"] = {"$gt": streak_reset_filter}
    
    # Get all valid trades ordered by date descending
    trades = await db.trade_logs.find(
        query, 
        {"_id": 0, "created_at": 1}
    ).sort("created_at", -1).to_list(1000)
    
    if not trades:
        return {"streak": 0, "streak_type": None, "total_trades": 0}
    
    # Calculate streak based on consecutive trading days
    # A streak counts consecutive TRADING days where the user traded
    # Holidays and weekends are skipped (don't break the streak)
    streak = 0
    last_trade_date = None
    
    for trade in trades:
        trade_date_str = trade.get("created_at", "")
        if not trade_date_str:
            continue
            
        # Parse the trade date
        try:
            if isinstance(trade_date_str, str):
                trade_date = datetime.fromisoformat(trade_date_str.replace('Z', '+00:00')).date()
            else:
                trade_date = trade_date_str.date()
        except:
            continue
        
        if last_trade_date is None:
            # First trade - start the streak
            streak = 1
            last_trade_date = trade_date
        else:
            # Check if this trade is on the previous trading day
            expected_date = get_previous_trading_day(last_trade_date)
            
            if expected_date is None:
                # Couldn't find a previous trading day
                break
            
            if trade_date == expected_date:
                streak += 1
                last_trade_date = trade_date
            elif trade_date == last_trade_date:
                # Same day - don't break streak but don't increment
                continue
            else:
                # Gap in trading days - streak broken
                break
    
    return {
        "streak": streak,
        "streak_type": "trading" if streak > 0 else None,
        "total_trades": len(trades)
    }

@trade_router.get("/active-signal")
async def get_active_signal():
    signal = await db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    if not signal:
        return {"message": "No active signal", "signal": None}
    # Handle missing fields for backward compatibility
    signal.setdefault("profit_points", 15)
    signal.setdefault("is_simulated", False)
    signal.setdefault("trade_timezone", "Asia/Manila")
    return {"signal": TradingSignalResponse(**{**signal, "created_at": datetime.fromisoformat(signal["created_at"]) if isinstance(signal["created_at"], str) else signal["created_at"]})}

@trade_router.get("/daily-summary")
async def get_daily_summary(user_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get today's trade summary. Admins can pass user_id to view another user's summary."""
    # Determine target user
    target_user_id = user["id"]
    if user_id and user.get("role") in ["admin", "basic_admin", "super_admin", "master_admin"]:
        target_user_id = user_id
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    trades = await db.trade_logs.find({
        "user_id": target_user_id,
        "created_at": {"$gte": today.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    total_projected = sum(t["projected_profit"] for t in trades)
    total_actual = sum(t["actual_profit"] for t in trades)
    
    return {
        "date": today.isoformat(),
        "trades_count": len(trades),
        "total_projected": round(total_projected, 2),
        "total_actual": round(total_actual, 2),
        "difference": round(total_actual - total_projected, 2),
        "trades": trades
    }

@trade_router.get("/missed-trade-status")
async def check_missed_trade_status(user: dict = Depends(get_current_user)):
    """Check if the current user has missed today's trade"""
    
    # Get today's date range
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # Check if user has traded today
    today_trade = await db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0})
    
    has_traded_today = today_trade is not None
    
    # Get active signal and check if trade window has passed
    signal = await db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    
    signal_completed = False
    is_post_trade_window = False
    trade_window_passed = False
    
    if signal:
        # Parse trade time
        trade_time_str = signal.get("trade_time", "12:00")
        trade_tz_str = signal.get("trade_timezone", "Asia/Manila")
        
        try:
            tz = pytz.timezone(trade_tz_str)
            now = datetime.now(tz)
            
            # Parse trade time (e.g., "12:00" or "20:20")
            parts = trade_time_str.split(":")
            trade_hour = int(parts[0])
            trade_minute = int(parts[1]) if len(parts) > 1 else 0
            
            # Create trade time for today in the signal's timezone
            trade_time_today = now.replace(hour=trade_hour, minute=trade_minute, second=0, microsecond=0)
            
            # Check if trade window has passed (trade time + 30 minutes buffer)
            trade_window_end = trade_time_today + timedelta(minutes=30)
            
            if now > trade_window_end:
                trade_window_passed = True
            
            # Post-trade window is 30 minutes after trade time
            if now > trade_time_today and now <= trade_window_end:
                is_post_trade_window = True
                
        except Exception as e:
            print(f"Error parsing trade time: {e}")
    else:
        # No active signal means the signal has been deactivated (completed)
        # Check if there was a signal today that's now inactive
        inactive_signal = await db.trading_signals.find_one(
            {
                "is_active": False,
                "created_at": {"$gte": today_start.isoformat()}
            },
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        if inactive_signal:
            signal_completed = True
    
    # User should see missed trade popup if:
    # 1. Signal is completed (deactivated) and user hasn't traded today
    # 2. OR trade window has passed and user hasn't traded today
    should_show_missed_popup = (not has_traded_today) and (signal_completed or trade_window_passed)
    
    return {
        "has_traded_today": has_traded_today,
        "signal_completed": signal_completed,
        "is_post_trade_window": is_post_trade_window,
        "trade_window_passed": trade_window_passed,
        "should_show_missed_popup": should_show_missed_popup,
        "active_signal": signal is not None
    }

@trade_router.post("/log-missed-trade")
async def log_missed_trade(
    date: str,  # ISO date string for which trade was missed
    actual_profit: float,
    commission: float = 0,  # Daily commission from referrals
    lot_size: Optional[float] = None,
    direction: Optional[str] = "BUY",
    notes: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Log a trade that was missed but user wants to record retroactively"""
    
    # Parse the date - set to noon UTC to avoid timezone edge cases
    try:
        if 'T' in date:
            trade_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        else:
            # Just a date string (YYYY-MM-DD) - set to noon UTC
            trade_date = datetime.strptime(date, "%Y-%m-%d").replace(
                hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    
    # Check if user already has a trade for this date
    date_start = trade_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = trade_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    existing_trade = await db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {
            "$gte": date_start.isoformat(),
            "$lte": date_end.isoformat()
        }
    })
    
    if existing_trade:
        raise HTTPException(status_code=400, detail="Trade already exists for this date")
    
    # Get user's current balance to calculate lot size if not provided
    if lot_size is None:
        deposits = await db.deposits.aggregate([
            {"$match": {"user_id": user["id"], "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        withdrawals = await db.withdrawals.aggregate([
            {"$match": {"user_id": user["id"], "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        profits = await db.trade_logs.aggregate([
            {"$match": {"user_id": user["id"]}},
            {"$group": {"_id": None, "total": {"$sum": "$actual_profit"}}}
        ]).to_list(1)
        commissions = await db.trade_logs.aggregate([
            {"$match": {"user_id": user["id"]}},
            {"$group": {"_id": None, "total": {"$sum": "$commission"}}}
        ]).to_list(1)
        
        balance = (deposits[0]["total"] if deposits else 0) - \
                  (withdrawals[0]["total"] if withdrawals else 0) + \
                  (profits[0]["total"] if profits else 0) + \
                  (commissions[0]["total"] if commissions else 0)
        
        lot_size = round(balance / 980, 2)
    
    # Calculate projected profit
    projected_profit = round(lot_size * 15, 2)
    profit_difference = round(actual_profit - projected_profit, 2)
    
    # Create the trade log with all required fields
    trade_id = str(uuid.uuid4())
    # Ensure created_at has timezone info
    created_at_str = trade_date.isoformat()
    if '+' not in created_at_str and not created_at_str.endswith('Z'):
        created_at_str = created_at_str + "+00:00"
    
    # Determine performance category (consistent with regular trade logging)
    if actual_profit >= projected_profit:
        performance = "exceeded" if actual_profit > projected_profit else "perfect"
    elif actual_profit > 0:
        performance = "below"
    else:
        performance = "below"
    
    trade_log = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": lot_size,
        "direction": direction,
        "projected_profit": projected_profit,
        "actual_profit": actual_profit,
        "commission": commission,  # Daily commission from referrals
        "profit_difference": profit_difference,
        "performance": performance,
        "signal_id": None,  # No signal for retroactive trades
        "notes": notes or "Retroactively logged trade",
        "is_retroactive": True,
        "is_manual_adjustment": True,  # Flag for manually adjusted trades
        "created_at": created_at_str
    }
    
    await db.trade_logs.insert_one(trade_log)
    
    return {
        "message": "Trade logged successfully",
        "trade": {k: v for k, v in trade_log.items() if k != "_id"}
    }

@trade_router.post("/did-not-trade")
async def mark_did_not_trade(
    date: str,  # ISO date string (YYYY-MM-DD)
    user: dict = Depends(get_current_user)
):
    """Mark a date as 'did not trade' - sets profit to 0 and resets streak"""
    
    # Parse the date
    try:
        if 'T' in date:
            trade_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        else:
            trade_date = datetime.strptime(date, "%Y-%m-%d").replace(
                hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    
    # Check if this is a past date (can't mark future dates as did not trade)
    now = datetime.now(timezone.utc)
    if trade_date.date() >= now.date():
        raise HTTPException(status_code=400, detail="Can only mark past dates as 'did not trade'")
    
    # Check if user already has a trade for this date
    date_start = trade_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = trade_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    existing_trade = await db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {
            "$gte": date_start.isoformat(),
            "$lte": date_end.isoformat()
        }
    })
    
    if existing_trade:
        raise HTTPException(status_code=400, detail="Trade already exists for this date")
    
    # Create the "did not trade" entry with 0 profit
    trade_id = str(uuid.uuid4())
    created_at_str = trade_date.isoformat()
    if '+' not in created_at_str and not created_at_str.endswith('Z'):
        created_at_str = created_at_str + "+00:00"
    
    trade_log = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": 0,
        "direction": None,
        "projected_profit": 0,
        "actual_profit": 0,
        "commission": 0,
        "profit_difference": 0,
        "performance": "missed",
        "signal_id": None,
        "notes": "Did not trade",
        "did_not_trade": True,  # Special flag for this type of entry
        "is_retroactive": True,
        "created_at": created_at_str
    }
    
    await db.trade_logs.insert_one(trade_log)
    
    # Reset user's streak to 0 by storing the reset date
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"streak_reset_date": trade_date.strftime("%Y-%m-%d")}}
    )
    
    return {
        "message": "Marked as 'did not trade'. Your trading streak has been reset to 0.",
        "trade_id": trade_id,
        "date": date,
        "streak_reset": True
    }

@trade_router.post("/forward-to-profit")
async def forward_trade_to_profit(trade_id: str, is_bve: bool = False, user: dict = Depends(get_current_user)):
    """Forward trade profit to profit tracker by creating a deposit entry"""
    
    # Use BVE collection if in BVE mode
    trade_collection = db.bve_trade_logs if is_bve else db.trade_logs
    trade = await trade_collection.find_one({"id": trade_id, "user_id": user["id"]}, {"_id": 0})
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # BVE trades should NOT be forwarded to production profit tracker
    if is_bve:
        raise HTTPException(status_code=400, detail="BVE trades cannot be forwarded to production profit tracker. Exit BVE mode to access real trades.")
    
    # Check if already forwarded
    existing = await db.deposits.find_one({"trade_id": trade_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Trade already forwarded to profit tracker")
    
    # Create deposit entry for the profit
    deposit_id = str(uuid.uuid4())
    deposit = {
        "id": deposit_id,
        "user_id": user["id"],
        "amount": trade["actual_profit"],
        "product": "MOIL10",
        "currency": "USD",
        "notes": f"Trade profit from {trade['created_at'][:10]} - {trade['direction']}",
        "trade_id": trade_id,
        "type": "profit",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.deposits.insert_one(deposit)
    
    return {
        "message": "Trade profit forwarded to profit tracker",
        "deposit_id": deposit_id,
        "amount": trade["actual_profit"]
    }

# ==================== TRADE MANAGEMENT ====================

class TradeChangeRequest(BaseModel):
    trade_id: str
    reason: str
    requested_changes: Optional[str] = None

@trade_router.delete("/reset/{trade_id}")
async def reset_trade(trade_id: str, user: dict = Depends(require_master_admin)):
    """Reset/delete a trade - Master Admin only. Allows trade to be re-entered."""
    
    # Find the trade
    trade = await db.trade_logs.find_one({"id": trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Store in reset_trades collection for audit trail
    reset_record = {
        "id": str(uuid.uuid4()),
        "original_trade": trade,
        "reset_by": user["id"],
        "reset_by_name": user.get("full_name", user.get("email")),
        "reset_at": datetime.now(timezone.utc).isoformat(),
        "reason": "Master admin reset"
    }
    await db.reset_trades.insert_one(reset_record)
    
    # Delete the trade
    await db.trade_logs.delete_one({"id": trade_id})
    
    # Also delete any associated deposit (if trade was forwarded to profit)
    await db.deposits.delete_many({"trade_id": trade_id})
    
    # Notify the original user via WebSocket
    try:
        await websocket_manager.send_notification(
            trade["user_id"],
            {
                "type": "trade_reset",
                "title": "Trade Reset",
                "message": f"Your trade from {trade['created_at'][:10]} has been reset by admin. You can re-enter it.",
                "data": {"trade_date": trade["created_at"][:10]}
            }
        )
    except:
        pass
    
    return {
        "message": "Trade reset successfully",
        "trade_date": trade["created_at"][:10],
        "user_id": trade["user_id"]
    }

@trade_router.delete("/undo-by-date/{date}")
async def undo_trade_by_date(date: str, user: dict = Depends(get_current_user)):
    """Undo/delete a trade by date - Users can undo their own trades from the Daily Projection table"""
    
    # Parse the date
    try:
        trade_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    
    # Find the trade for this user on this date
    date_start = trade_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = trade_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    trade = await db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {
            "$gte": date_start.isoformat(),
            "$lte": date_end.isoformat()
        }
    }, {"_id": 0})
    
    if not trade:
        raise HTTPException(status_code=404, detail="No trade found for this date")
    
    # Store in reset_trades collection for audit trail
    reset_record = {
        "id": str(uuid.uuid4()),
        "original_trade": trade,
        "reset_by": user["id"],
        "reset_by_name": user.get("full_name", user.get("email")),
        "reset_at": datetime.now(timezone.utc).isoformat(),
        "reason": "User undo from Daily Projection"
    }
    await db.reset_trades.insert_one(reset_record)
    
    # Delete the trade
    await db.trade_logs.delete_one({"id": trade["id"]})
    
    # Also delete any associated deposit (if trade was forwarded to profit)
    await db.deposits.delete_many({"trade_id": trade["id"]})
    
    logger.info(f"Trade undone: user={user['id']}, date={date}, trade_id={trade['id']}")
    
    return {
        "message": "Trade undone successfully",
        "trade_date": date,
        "trade_id": trade["id"]
    }

# ==================== USER HOLIDAYS ====================

@trade_router.get("/holidays")
async def get_user_holidays(user: dict = Depends(get_current_user)):
    """Get user-specific holidays"""
    holidays = await db.user_holidays.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    return {"holidays": holidays}

@trade_router.post("/holidays")
async def add_user_holiday(
    date: str,
    reason: Optional[str] = "Personal holiday",
    user: dict = Depends(get_current_user)
):
    """Mark a date as a user-specific holiday"""
    
    # Parse and validate the date
    try:
        holiday_date = datetime.strptime(date, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    
    # Check if this date is already marked as a holiday
    existing = await db.user_holidays.find_one({
        "user_id": user["id"],
        "date": date
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="This date is already marked as a holiday")
    
    # Check if there's already a trade logged for this date
    date_start = holiday_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    date_end = holiday_date.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc)
    
    existing_trade = await db.trade_logs.find_one({
        "user_id": user["id"],
        "created_at": {
            "$gte": date_start.isoformat(),
            "$lte": date_end.isoformat()
        }
    })
    
    if existing_trade:
        raise HTTPException(
            status_code=400, 
            detail="Cannot mark as holiday - a trade already exists for this date. Undo the trade first."
        )
    
    # Create the holiday record
    holiday_id = str(uuid.uuid4())
    holiday = {
        "id": holiday_id,
        "user_id": user["id"],
        "date": date,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_holidays.insert_one(holiday)
    
    logger.info(f"User holiday added: user={user['id']}, date={date}")
    
    return {
        "message": "Holiday marked successfully",
        "holiday": {k: v for k, v in holiday.items() if k != "_id"}
    }

@trade_router.delete("/holidays/{date}")
async def remove_user_holiday(date: str, user: dict = Depends(get_current_user)):
    """Remove a user-specific holiday"""
    
    result = await db.user_holidays.delete_one({
        "user_id": user["id"],
        "date": date
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found for this date")
    
    logger.info(f"User holiday removed: user={user['id']}, date={date}")
    
    return {"message": "Holiday removed successfully", "date": date}

# ==================== GLOBAL HOLIDAYS (Master Admin only) ====================

@admin_router.get("/global-holidays")
async def get_global_holidays(user: dict = Depends(require_admin)):
    """Get all global holidays (Master Admin only)"""
    holidays = await db.global_holidays.find(
        {},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    return {"holidays": holidays}

@admin_router.post("/global-holidays")
async def add_global_holiday(
    date: str,
    reason: Optional[str] = "Market holiday",
    user: dict = Depends(require_super_or_master_admin)
):
    """Add a global holiday for all users (Super Admin or Master Admin only)"""
    
    # Parse and validate the date
    try:
        holiday_date = datetime.strptime(date, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    
    # Check if this date is already a global holiday
    existing = await db.global_holidays.find_one({"date": date})
    if existing:
        raise HTTPException(status_code=400, detail="This date is already a global holiday")
    
    # Create the global holiday record
    holiday_id = str(uuid.uuid4())
    holiday = {
        "id": holiday_id,
        "date": date,
        "reason": reason,
        "created_by": user["id"],
        "created_by_name": user.get("full_name", user.get("email")),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.global_holidays.insert_one(holiday)
    
    logger.info(f"Global holiday added: date={date}, by={user['id']}")
    
    return {
        "message": "Global holiday added successfully",
        "holiday": {k: v for k, v in holiday.items() if k != "_id"}
    }

@admin_router.delete("/global-holidays/{date}")
async def remove_global_holiday(date: str, user: dict = Depends(require_super_or_master_admin)):
    """Remove a global holiday (Super Admin or Master Admin only)"""
    
    result = await db.global_holidays.delete_one({"date": date})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Global holiday not found for this date")
    
    logger.info(f"Global holiday removed: date={date}, by={user['id']}")
    
    return {"message": "Global holiday removed successfully", "date": date}

@trade_router.get("/global-holidays")
async def get_global_holidays_for_user(user: dict = Depends(get_current_user)):
    """Get all global holidays (for any authenticated user to see)"""
    holidays = await db.global_holidays.find(
        {},
        {"_id": 0}
    ).sort("date", 1).to_list(100)
    return {"holidays": holidays}

# ==================== TRADING PRODUCTS MANAGEMENT ====================

@admin_router.get("/trading-products")
async def get_trading_products(user: dict = Depends(require_admin)):
    """Get all trading products"""
    products = await db.trading_products.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    
    # If no products exist, return default products
    if not products:
        default_products = [
            {"id": str(uuid.uuid4()), "name": "MOIL10", "is_active": True, "order": 0},
            {"id": str(uuid.uuid4()), "name": "XAUUSD", "is_active": True, "order": 1},
            {"id": str(uuid.uuid4()), "name": "EURUSD", "is_active": True, "order": 2},
            {"id": str(uuid.uuid4()), "name": "GBPUSD", "is_active": True, "order": 3},
            {"id": str(uuid.uuid4()), "name": "USDJPY", "is_active": True, "order": 4},
        ]
        # Insert default products
        for product in default_products:
            product["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.trading_products.insert_one(product)
        products = default_products
    
    return {"products": products}

@admin_router.post("/trading-products")
async def add_trading_product(
    name: str,
    user: dict = Depends(require_master_admin)
):
    """Add a new trading product (Master Admin only)"""
    
    # Check if product already exists
    existing = await db.trading_products.find_one({"name": name.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Product already exists")
    
    # Get the highest order number
    last_product = await db.trading_products.find_one({}, sort=[("order", -1)])
    next_order = (last_product.get("order", 0) + 1) if last_product else 0
    
    product_id = str(uuid.uuid4())
    product = {
        "id": product_id,
        "name": name.upper(),
        "is_active": True,
        "order": next_order,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trading_products.insert_one(product)
    
    logger.info(f"Trading product added: {name.upper()}, by={user['id']}")
    
    return {
        "message": "Product added successfully",
        "product": {k: v for k, v in product.items() if k != "_id"}
    }

@admin_router.delete("/trading-products/{product_id}")
async def remove_trading_product(product_id: str, user: dict = Depends(require_master_admin)):
    """Remove a trading product (Master Admin only)"""
    
    result = await db.trading_products.delete_one({"id": product_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    logger.info(f"Trading product removed: {product_id}, by={user['id']}")
    
    return {"message": "Product removed successfully"}

@admin_router.put("/trading-products/{product_id}")
async def update_trading_product(
    product_id: str,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    user: dict = Depends(require_master_admin)
):
    """Update a trading product (Master Admin only)"""
    
    product = await db.trading_products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name.upper()
    if is_active is not None:
        update_data["is_active"] = is_active
    
    if update_data:
        await db.trading_products.update_one({"id": product_id}, {"$set": update_data})
    
    updated = await db.trading_products.find_one({"id": product_id}, {"_id": 0})
    
    return {"message": "Product updated successfully", "product": updated}

@trade_router.get("/trading-products")
async def get_trading_products_for_user(user: dict = Depends(get_current_user)):
    """Get active trading products (for any authenticated user)"""
    products = await db.trading_products.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("order", 1).to_list(50)
    
    # If no products exist, return default products
    if not products:
        products = [
            {"id": "default-1", "name": "MOIL10", "is_active": True},
            {"id": "default-2", "name": "XAUUSD", "is_active": True},
            {"id": "default-3", "name": "EURUSD", "is_active": True},
            {"id": "default-4", "name": "GBPUSD", "is_active": True},
            {"id": "default-5", "name": "USDJPY", "is_active": True},
        ]
    
    return {"products": products}

@trade_router.post("/request-change")
async def request_trade_change(data: TradeChangeRequest, user: dict = Depends(get_current_user)):
    """Request a change to a trade - for non-master-admin users"""
    
    # Find the trade
    trade = await db.trade_logs.find_one({"id": data.trade_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Verify the trade belongs to the requesting user
    if trade["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only request changes to your own trades")
    
    # Check if there's already a pending request for this trade
    existing_request = await db.trade_change_requests.find_one({
        "trade_id": data.trade_id,
        "status": "pending"
    })
    if existing_request:
        raise HTTPException(status_code=400, detail="A change request for this trade is already pending")
    
    # Create the change request
    request_id = str(uuid.uuid4())
    change_request = {
        "id": request_id,
        "trade_id": data.trade_id,
        "user_id": user["id"],
        "user_name": user.get("full_name", user.get("email")),
        "trade_date": trade["created_at"][:10],
        "original_profit": trade["actual_profit"],
        "reason": data.reason,
        "requested_changes": data.requested_changes,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.trade_change_requests.insert_one(change_request)
    
    # Notify all admins via WebSocket
    try:
        admins = await db.users.find(
            {"role": {"$in": ["basic_admin", "admin", "super_admin", "master_admin"]}},
            {"_id": 0, "id": 1}
        ).to_list(100)
        
        for admin in admins:
            await websocket_manager.send_notification(
                admin["id"],
                {
                    "type": "trade_change_request",
                    "title": "Trade Change Request",
                    "message": f"{user.get('full_name', 'A user')} requested a change to their trade from {trade['created_at'][:10]}",
                    "data": {"request_id": request_id}
                }
            )
    except:
        pass
    
    return {
        "message": "Change request submitted successfully",
        "request_id": request_id
    }

@admin_router.get("/trade-change-requests")
async def get_trade_change_requests(
    status: Optional[str] = None,
    user: dict = Depends(require_admin)
):
    """Get all trade change requests - Admin only"""
    query = {}
    if status:
        query["status"] = status
    
    requests = await db.trade_change_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"requests": requests}

@admin_router.put("/trade-change-requests/{request_id}")
async def handle_trade_change_request(
    request_id: str,
    action: str,  # "approve" or "reject"
    admin_notes: Optional[str] = None,
    user: dict = Depends(require_master_admin)
):
    """Handle a trade change request - Master Admin only"""
    
    request = await db.trade_change_requests.find_one({"id": request_id}, {"_id": 0})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request has already been processed")
    
    if action == "approve":
        # Reset the trade (same as reset_trade endpoint)
        trade = await db.trade_logs.find_one({"id": request["trade_id"]}, {"_id": 0})
        if trade:
            # Store in reset_trades for audit
            reset_record = {
                "id": str(uuid.uuid4()),
                "original_trade": trade,
                "reset_by": user["id"],
                "reset_by_name": user.get("full_name", user.get("email")),
                "reset_at": datetime.now(timezone.utc).isoformat(),
                "reason": f"Approved change request: {request['reason']}",
                "request_id": request_id
            }
            await db.reset_trades.insert_one(reset_record)
            
            # Delete the trade
            await db.trade_logs.delete_one({"id": request["trade_id"]})
            await db.deposits.delete_many({"trade_id": request["trade_id"]})
        
        # Update request status
        await db.trade_change_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": "approved",
                "handled_by": user["id"],
                "handled_by_name": user.get("full_name", user.get("email")),
                "handled_at": datetime.now(timezone.utc).isoformat(),
                "admin_notes": admin_notes
            }}
        )
        
        # Notify the user
        try:
            await websocket_manager.send_notification(
                request["user_id"],
                {
                    "type": "trade_change_approved",
                    "title": "Change Request Approved",
                    "message": f"Your trade change request for {request['trade_date']} has been approved. You can now re-enter the trade.",
                    "data": {"trade_date": request["trade_date"]}
                }
            )
        except:
            pass
        
        return {"message": "Request approved and trade reset", "status": "approved"}
    
    elif action == "reject":
        # Update request status
        await db.trade_change_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": "rejected",
                "handled_by": user["id"],
                "handled_by_name": user.get("full_name", user.get("email")),
                "handled_at": datetime.now(timezone.utc).isoformat(),
                "admin_notes": admin_notes
            }}
        )
        
        # Notify the user
        try:
            await websocket_manager.send_notification(
                request["user_id"],
                {
                    "type": "trade_change_rejected",
                    "title": "Change Request Rejected",
                    "message": f"Your trade change request for {request['trade_date']} has been rejected." + (f" Reason: {admin_notes}" if admin_notes else ""),
                    "data": {"trade_date": request["trade_date"]}
                }
            )
        except:
            pass
        
        return {"message": "Request rejected", "status": "rejected"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")

# ==================== ADMIN ROUTES ====================

@admin_router.post("/signals", response_model=TradingSignalResponse)
async def create_signal(data: TradingSignalCreate, user: dict = Depends(require_admin)):
    # Deactivate all existing signals
    await db.trading_signals.update_many({}, {"$set": {"is_active": False}})
    
    signal_id = str(uuid.uuid4())
    signal = {
        "id": signal_id,
        "product": data.product,
        "trade_time": data.trade_time,
        "trade_timezone": data.trade_timezone,
        "direction": data.direction,
        "profit_points": data.profit_points,
        "notes": data.notes,
        "is_active": True,
        "is_official": data.is_official,  # Official trading signal flag
        "is_simulated": False,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trading_signals.insert_one(signal)
    
    # Create notification for all members about new official trading signal
    if data.is_official:
        await create_member_notification(
            notification_type="trading_signal",
            title=f"New Trading Signal: {data.direction}",
            message=f"Official {data.direction} signal for {data.product} at {data.trade_time}",
            triggered_by_id=user["id"],
            triggered_by_name=user["full_name"],
            metadata={"signal_id": signal_id, "direction": data.direction, "product": data.product, "trade_time": data.trade_time}
        )
    
    return TradingSignalResponse(**{**signal, "created_at": datetime.fromisoformat(signal["created_at"])})

@admin_router.put("/signals/{signal_id}")
async def update_signal(signal_id: str, data: TradingSignalUpdate, user: dict = Depends(require_admin)):
    signal = await db.trading_signals.find_one({"id": signal_id}, {"_id": 0})
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    update_data = {}
    if data.trade_time is not None:
        update_data["trade_time"] = data.trade_time
    if data.trade_timezone is not None:
        update_data["trade_timezone"] = data.trade_timezone
    if data.direction is not None:
        update_data["direction"] = data.direction
    if data.profit_points is not None:
        update_data["profit_points"] = data.profit_points
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.is_active is not None:
        if data.is_active:
            # Deactivate all other signals first
            await db.trading_signals.update_many({"id": {"$ne": signal_id}}, {"$set": {"is_active": False}})
        update_data["is_active"] = data.is_active
    if data.is_official is not None:
        update_data["is_official"] = data.is_official
    
    if update_data:
        await db.trading_signals.update_one({"id": signal_id}, {"$set": update_data})
    
    updated = await db.trading_signals.find_one({"id": signal_id}, {"_id": 0})
    return TradingSignalResponse(**{**updated, "created_at": datetime.fromisoformat(updated["created_at"]) if isinstance(updated["created_at"], str) else updated["created_at"]})

@admin_router.post("/signals/simulate", response_model=TradingSignalResponse)
async def simulate_signal(data: TradingSignalCreate, user: dict = Depends(require_super_admin)):
    """Create a simulated signal for testing - Super Admin only"""
    # Deactivate all existing signals
    await db.trading_signals.update_many({}, {"$set": {"is_active": False}})
    
    signal_id = str(uuid.uuid4())
    signal = {
        "id": signal_id,
        "product": data.product,
        "trade_time": data.trade_time,
        "trade_timezone": data.trade_timezone,
        "direction": data.direction,
        "profit_points": data.profit_points,
        "notes": data.notes or "",  # Don't prepend [SIMULATED] - use is_simulated flag instead
        "is_active": True,
        "is_simulated": True,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trading_signals.insert_one(signal)
    return TradingSignalResponse(**{**signal, "created_at": datetime.fromisoformat(signal["created_at"])})

@admin_router.get("/signals", response_model=List[TradingSignalResponse])
async def get_signals(user: dict = Depends(require_admin)):
    signals = await db.trading_signals.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    result = []
    for s in signals:
        s.setdefault("profit_points", 15)
        s.setdefault("is_simulated", False)
        result.append(TradingSignalResponse(**{**s, "created_at": datetime.fromisoformat(s["created_at"]) if isinstance(s["created_at"], str) else s["created_at"]}))
    return result

@admin_router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: str, user: dict = Depends(require_admin)):
    result = await db.trading_signals.delete_one({"id": signal_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"message": "Signal deleted"}

# Enhanced Member Management
@admin_router.get("/members")
async def get_members(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    sort_account_value: Optional[str] = None,  # 'asc' or 'desc'
    user: dict = Depends(require_admin)
):
    query = {}
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if role and role != "all":
        query["role"] = role
    if status == "suspended":
        query["is_suspended"] = True
    elif status == "deactivated":
        query["is_deactivated"] = True
    elif status == "active":
        query["is_suspended"] = {"$ne": True}
        query["is_deactivated"] = {"$ne": True}
    
    # IMPORTANT: Exclude licensees from standard member list
    # Licensees should be managed through the Licenses page, not Member Management
    query["license_type"] = {"$exists": False}
    
    total = await db.users.count_documents(query)
    skip = (page - 1) * limit
    users_cursor = await db.users.find(query, {"_id": 0, "password": 0}).skip(skip).limit(limit).to_list(limit)
    
    # For super_admin and master_admin, calculate account_value for each user
    users = []
    requesting_user_role = user.get("role")
    can_see_account_value = requesting_user_role in ["super_admin", "master_admin"]
    
    for u in users_cursor:
        user_data = dict(u)
        if can_see_account_value:
            # Check if user is a licensee - use license current_amount for their account_value
            if u.get("license_type"):
                license = await db.licenses.find_one({"user_id": u["id"], "is_active": True}, {"_id": 0})
                if license:
                    user_data["account_value"] = round(license.get("current_amount", license.get("starting_amount", 0)), 2)
                else:
                    user_data["account_value"] = round(u.get("account_value", 0), 2)
            else:
                # Calculate account value from deposits and profits for non-licensees
                deposits = await db.deposits.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)
                trades = await db.trade_logs.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)
                
                total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit" and d.get("type") != "withdrawal")
                total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
                total_profit = sum(t.get("actual_profit", 0) for t in trades)
                
                user_data["account_value"] = round(total_deposits - total_withdrawals + total_profit, 2)
        users.append(user_data)
    
    # Sort by account value if requested (sorting happens after calculation)
    if sort_account_value and can_see_account_value:
        reverse = sort_account_value == 'desc'
        users.sort(key=lambda x: x.get('account_value', 0), reverse=reverse)
    
    return {
        "members": users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@admin_router.get("/members/{user_id}")
async def get_member_details(user_id: str, user: dict = Depends(require_admin)):
    member = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's trades
    trades = await db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    # Get user's deposits
    deposits = await db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Calculate summary
    total_trades = len(trades)
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit")
    
    # For licensees, use license.current_amount as the authoritative account_value
    # And calculate profit as current_amount - starting_amount (projected profits when manager traded)
    account_value = round(total_deposits + total_profit, 2)
    licensee_profit = None
    licensee_trades = 0
    performance_rate = 0
    
    if member.get("license_type"):
        # Get the most recent active license for this user
        license = await db.licenses.find_one(
            {"user_id": user_id, "is_active": True}, 
            {"_id": 0},
            sort=[("created_at", -1)]  # Get most recent license
        )
        if license:
            starting_amount = license.get("starting_amount", 0)
            
            # For extended licensees, calculate current_amount dynamically using projections
            # This ensures consistency with /api/admin/licenses endpoint
            if license.get("license_type") == "extended":
                start_date_raw = license.get("start_date", "")
                if isinstance(start_date_raw, str):
                    start_date = datetime.strptime(start_date_raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    start_date = start_date_raw.replace(tzinfo=timezone.utc)
                
                today = datetime.now(timezone.utc)
                days_since_start = (today - start_date).days
                if days_since_start > 0:
                    projections = calculate_extended_license_projections(
                        starting_amount, 
                        start_date, 
                        min(days_since_start + 1, 365)
                    )
                    if projections:
                        account_value = projections[-1]["account_value"]
                    else:
                        account_value = starting_amount
                else:
                    account_value = starting_amount
            else:
                # Honorary licensees use stored current_amount
                account_value = round(license.get("current_amount", starting_amount), 2)
            
            # For licensees, profit = current_amount - starting_amount
            licensee_profit = round(account_value - starting_amount, 2)
            
            # Count Master Admin trades (days when manager traded that benefited this licensee)
            # Get master admin's trade logs - count distinct dates from created_at
            master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1})
            if master_admin:
                # Count distinct trading days from effective_start_date
                effective_start = license.get("effective_start_date", license.get("start_date"))
                
                # Build match condition
                match_cond = {"user_id": master_admin["id"]}
                if effective_start:
                    # Convert effective_start to datetime for comparison
                    if isinstance(effective_start, str):
                        start_dt = datetime.strptime(effective_start[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    else:
                        start_dt = effective_start.replace(tzinfo=timezone.utc)
                    match_cond["created_at"] = {"$gte": start_dt.isoformat()}
                
                # Get distinct trading days (by date string from created_at)
                master_trades = await db.trade_logs.find(match_cond, {"_id": 0, "created_at": 1}).to_list(1000)
                # Count unique dates (YYYY-MM-DD format)
                unique_dates = set()
                for trade in master_trades:
                    created = trade.get("created_at", "")
                    if created:
                        date_str = str(created)[:10]  # Get YYYY-MM-DD
                        unique_dates.add(date_str)
                licensee_trades = len(unique_dates)
            
            # For licensees, performance_rate is always 100% if they have profit (they get exactly projected)
            if starting_amount > 0:
                performance_rate = round((account_value / starting_amount) * 100 - 100, 2)  # Growth rate
    else:
        # Regular user performance rate
        total_projected = sum(t.get("projected_profit", 0) for t in trades)
        if total_projected > 0:
            performance_rate = round((total_profit / total_projected) * 100, 2)
    
    return {
        "user": member,
        "stats": {
            "total_trades": licensee_trades if licensee_profit is not None else total_trades,
            "total_profit": licensee_profit if licensee_profit is not None else round(total_profit, 2),
            "total_actual_profit": licensee_profit if licensee_profit is not None else round(total_profit, 2),
            "total_deposits": round(total_deposits, 2),
            "account_value": account_value,
            "performance_rate": performance_rate,
            "is_licensee": member.get("license_type") is not None
        },
        "recent_trades": trades[:10],
        "recent_deposits": deposits[:10]
    }

@admin_router.get("/members/{user_id}/deposits")
async def get_member_deposits(user_id: str, user: dict = Depends(require_admin)):
    """Get all deposits for a specific member (admin only)"""
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    deposits = await db.deposits.find(
        {"user_id": user_id, "is_withdrawal": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    return deposits

@admin_router.get("/members/{user_id}/withdrawals")
async def get_member_withdrawals(user_id: str, user: dict = Depends(require_admin)):
    """Get all withdrawals for a specific member (admin only)"""
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    withdrawals = await db.deposits.find(
        {"user_id": user_id, "is_withdrawal": True},
        {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    
    return withdrawals

@admin_router.delete("/members/{user_id}/trades/{trade_id}")
async def delete_member_trade(user_id: str, trade_id: str, user: dict = Depends(require_master_admin)):
    """Delete a specific trade for a member and deduct profit from balance (Master Admin only)"""
    
    # Verify member exists
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the trade
    trade = await db.trade_logs.find_one({"id": trade_id, "user_id": user_id}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found for this user")
    
    actual_profit = trade.get("actual_profit", 0)
    commission = trade.get("commission", 0)
    total_deduction = actual_profit + commission
    
    # Store in audit trail
    audit_record = {
        "id": str(uuid.uuid4()),
        "action": "admin_trade_delete",
        "trade_id": trade_id,
        "user_id": user_id,
        "admin_id": user["id"],
        "admin_name": user.get("full_name", "Admin"),
        "trade_data": trade,
        "profit_deducted": total_deduction,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit_record)
    
    # Delete the trade
    await db.trade_logs.delete_one({"id": trade_id})
    
    # Also delete any associated deposit (if trade was forwarded to profit)
    await db.deposits.delete_many({"trade_id": trade_id})
    
    # Create a negative deposit to deduct the profit from balance
    if total_deduction > 0:
        deduction_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": -total_deduction,  # Negative to deduct from balance
            "type": "admin_adjustment",
            "notes": f"Admin deleted trade from {trade.get('created_at', 'unknown date')}. Profit deducted: ${actual_profit:.2f}, Commission: ${commission:.2f}",
            "is_withdrawal": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "admin_id": user["id"]
        }
        await db.deposits.insert_one(deduction_record)
    
    return {
        "message": "Trade deleted successfully",
        "profit_deducted": total_deduction,
        "trade_id": trade_id
    }

class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    lot_size: Optional[float] = None
    allowed_dashboards: Optional[List[str]] = None  # For super admin to assign dashboards
    role: Optional[str] = None  # For master admin to change roles
    email: Optional[str] = None  # For master admin to change email

@admin_router.put("/members/{user_id}")
async def update_member(user_id: str, data: AdminUserUpdate, user: dict = Depends(require_admin)):
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.full_name:
        update_data["full_name"] = data.full_name
    if data.timezone:
        update_data["timezone"] = data.timezone
    if data.lot_size is not None:
        update_data["lot_size"] = data.lot_size
    
    # Only super_admin or master_admin can update allowed_dashboards
    if data.allowed_dashboards is not None and user.get("role") in ["super_admin", "master_admin"]:
        update_data["allowed_dashboards"] = data.allowed_dashboards
    
    # Only master_admin can change roles and email
    if user.get("role") == "master_admin":
        if data.role:
            update_data["role"] = data.role
        if data.email:
            update_data["email"] = data.email.lower()
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    return {"message": "User updated"}

@admin_router.post("/members/{user_id}/suspend")
async def suspend_member(user_id: str, user: dict = Depends(require_admin)):
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    if member.get("role") == "super_admin" and user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Cannot suspend super admin")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_suspended": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "User suspended"}

@admin_router.post("/members/{user_id}/unsuspend")
async def unsuspend_member(user_id: str, user: dict = Depends(require_admin)):
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_suspended": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "User unsuspended"}

@admin_router.delete("/members/{user_id}")
async def delete_member(user_id: str, user: dict = Depends(require_super_admin)):
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    if member.get("role") == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot delete super admin")
    
    # Delete user and related data
    await db.users.delete_one({"id": user_id})
    await db.deposits.delete_many({"user_id": user_id})
    await db.trade_logs.delete_many({"user_id": user_id})
    await db.debts.delete_many({"user_id": user_id})
    await db.goals.delete_many({"user_id": user_id})
    
    return {"message": "User and all related data deleted"}

class TempPasswordSet(BaseModel):
    temp_password: str

@admin_router.post("/members/{user_id}/set-temp-password")
async def set_temp_password(user_id: str, data: TempPasswordSet, user: dict = Depends(require_admin)):
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Set temporary password and flag for forced change
    new_hash = hash_password(data.temp_password)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "password": new_hash,
            "must_change_password": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # TODO: Send email with temp password via Emailit
    
    return {"message": "Temporary password set. User will be prompted to change on next login."}

# Simulate Member View - Get member's complete data for Master Admin
@admin_router.get("/members/{user_id}/simulate")
async def simulate_member_view(user_id: str, user: dict = Depends(require_master_admin)):
    """Master Admin only: Get all data to simulate viewing as a specific member"""
    member = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get member's deposits
    deposits = await db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Get member's trades
    trades = await db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Get member's debts
    debts = await db.debts.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get member's goals
    goals = await db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Calculate account value
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit" and d.get("type") != "withdrawal")
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    account_value = round(total_deposits - total_withdrawals + total_profit, 2)
    
    # Calculate LOT size
    lot_size = round(account_value / 980, 2) if account_value > 0 else 0
    
    return {
        "member": member,
        "account_value": account_value,
        "lot_size": lot_size,
        "total_deposits": round(total_deposits, 2),
        "total_withdrawals": round(total_withdrawals, 2),
        "total_profit": round(total_profit, 2),
        "deposits": deposits,
        "trades": trades[:20],
        "debts": debts,
        "goals": goals,
        "summary": {
            "total_trades": len(trades),
            "winning_trades": len([t for t in trades if t.get("performance") in ["exceeded", "perfect"]]),
            "total_debts": len(debts),
            "total_goals": len(goals)
        }
    }

# Trading Signals - Paginated History
@admin_router.get("/signals/history")
async def get_signals_history(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(require_admin)
):
    """Get paginated signal history"""
    skip = (page - 1) * page_size
    
    total = await db.trading_signals.count_documents({})
    signals = await db.trading_signals.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "signals": signals,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }

# Trading Signals - Monthly Archive
@admin_router.get("/signals/archive")
async def get_signals_archive(user: dict = Depends(require_admin)):
    """Get signals organized by month"""
    signals = await db.trading_signals.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Organize by month
    archive = {}
    for signal in signals:
        created_at = signal.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        month_key = created_at.strftime("%Y-%m")  # e.g., "2026-01"
        month_label = created_at.strftime("%B %Y")  # e.g., "January 2026"
        
        if month_key not in archive:
            archive[month_key] = {
                "month_key": month_key,
                "month_label": month_label,
                "signals": []
            }
        archive[month_key]["signals"].append(signal)
    
    # Convert to sorted list (newest first)
    months = sorted(archive.values(), key=lambda x: x["month_key"], reverse=True)
    
    return {"months": months}

# Archive current month signals (move to archive and clear from main list)
@admin_router.post("/signals/archive-month")
async def archive_current_month_signals(user: dict = Depends(require_super_admin)):
    """Archive all signals from the current month"""
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get signals from current month that are not active
    signals_to_archive = await db.trading_signals.find({
        "created_at": {"$gte": start_of_month.isoformat()},
        "is_active": False
    }, {"_id": 0}).to_list(1000)
    
    if not signals_to_archive:
        return {"message": "No inactive signals to archive", "archived_count": 0}
    
    # Mark them as archived
    archived_count = 0
    for signal in signals_to_archive:
        await db.trading_signals.update_one(
            {"id": signal["id"]},
            {"$set": {"is_archived": True}}
        )
        archived_count += 1
    
    return {"message": f"Archived {archived_count} signals", "archived_count": archived_count}

# ==================== TEAM ANALYTICS ====================
@admin_router.get("/analytics/team")
async def get_team_analytics(user: dict = Depends(require_admin)):
    """Get collective team analytics: total account value, profit, traders, performance
    Note: Honorary Licensees are excluded from team totals but still shown in member stats"""
    
    # Get all users including admins (include all roles in team stats)
    all_users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    # Include all users: members, admins, super_admins, master_admin
    active_users = [u for u in all_users if not u.get("is_suspended", False)]
    
    # Get all active licenses to check for licensed users (both extended and honorary are excluded)
    all_licenses = await db.licenses.find({"is_active": True}, {"_id": 0}).to_list(1000)
    licensed_user_ids = set(lic["user_id"] for lic in all_licenses)
    honorary_user_ids = set(
        lic["user_id"] for lic in all_licenses 
        if lic.get("license_type") == "honorary"
    )
    extended_user_ids = set(
        lic["user_id"] for lic in all_licenses 
        if lic.get("license_type") == "extended"
    )
    
    total_account_value = 0
    total_profit = 0
    total_trades = 0
    winning_trades = 0
    
    member_stats = []
    
    for member in active_users:
        user_id = member["id"]
        is_licensed = user_id in licensed_user_ids
        is_honorary = user_id in honorary_user_ids
        is_extended = user_id in extended_user_ids
        
        # Get deposits
        deposits = await db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit", "withdrawal"])
        total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
        
        # Get trades
        trades = await db.trade_logs.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
        user_profit = sum(t.get("actual_profit", 0) for t in trades)
        
        # For licensees, use license.current_amount as account value
        if is_licensed:
            license = next((lic for lic in all_licenses if lic["user_id"] == user_id), None)
            user_account_value = license.get("current_amount", license.get("starting_amount", 0)) if license else 0
        else:
            user_account_value = total_deposits - total_withdrawals + user_profit
        
        # Only add to team totals if NOT a licensed user (both extended and honorary are excluded)
        if not is_licensed:
            total_account_value += user_account_value
            total_profit += user_profit
        
        # Always count trades for performance tracking
        total_trades += len(trades)
        winning_trades += len([t for t in trades if t.get("performance") in ["exceeded", "perfect"]])
        
        member_stats.append({
            "id": user_id,
            "name": member.get("full_name", "Unknown"),
            "email": member.get("email", ""),
            "role": member.get("role", "member"),
            "account_value": round(user_account_value, 2),
            "total_profit": round(user_profit, 2),
            "trades_count": len(trades),
            "is_licensed": is_licensed,
            "is_honorary": is_honorary,
            "is_extended": is_extended
        })
    
    # Calculate performance rate
    performance_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    return {
        "total_account_value": round(total_account_value, 2),
        "total_profit": round(total_profit, 2),
        "total_traders": len(active_users),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "performance_rate": round(performance_rate, 1),
        "member_stats": sorted(member_stats, key=lambda x: x["total_profit"], reverse=True),
        "licensed_excluded_count": len(licensed_user_ids),
        "honorary_count": len(honorary_user_ids),
        "extended_count": len(extended_user_ids)
    }

@admin_router.get("/analytics/missed-trades")
async def get_missed_trades(user: dict = Depends(require_admin)):
    """Get members with undeclared trades (missed trading days)"""
    
    # Get all member users
    all_users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    member_users = [u for u in all_users if u.get("role") == "member"]
    
    # Get all signals to determine trading days
    all_signals = await db.signals.find({}, {"_id": 0}).to_list(500)
    
    # Create a set of all trading dates (dates with signals)
    trading_dates = set()
    for signal in all_signals:
        if signal.get("created_at"):
            signal_date = signal["created_at"].split("T")[0]
            trading_dates.add(signal_date)
    
    # Get today's date
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()
    
    # Filter to only past trading dates (not including today if after market close, or today if signal exists)
    past_trading_dates = [d for d in trading_dates if d <= today_str]
    
    # Get all trade logs
    all_trades = await db.trade_logs.find({}, {"_id": 0}).to_list(10000)
    
    # Create a map of user_id -> set of dates they traded
    user_trade_dates = {}
    for trade in all_trades:
        user_id = trade.get("user_id")
        if user_id:
            if user_id not in user_trade_dates:
                user_trade_dates[user_id] = set()
            trade_date = trade.get("created_at", "").split("T")[0]
            if trade_date:
                user_trade_dates[user_id].add(trade_date)
    
    # Calculate missed trades for each member
    missed_traders = []
    for member in member_users:
        user_id = member["id"]
        member_join_date = member.get("created_at", "").split("T")[0] if member.get("created_at") else "2000-01-01"
        
        # Get the dates this member has traded
        member_traded_dates = user_trade_dates.get(user_id, set())
        
        # Calculate missed trading days (trading days after member joined that they didn't trade)
        missed_dates = []
        for trading_date in past_trading_dates:
            # Only count dates after member joined and before/on today
            if trading_date >= member_join_date and trading_date <= today_str:
                if trading_date not in member_traded_dates:
                    missed_dates.append(trading_date)
        
        missed_count = len(missed_dates)
        
        if missed_count > 0:
            # Get last trade date
            last_trade_at = None
            if member_traded_dates:
                last_trade_at = max(member_traded_dates) + "T00:00:00Z"
            
            missed_traders.append({
                "id": member["id"],
                "full_name": member.get("full_name", "Unknown"),
                "email": member.get("email", ""),
                "last_trade_at": last_trade_at,
                "missed_trades_count": missed_count,
                "missed_dates": sorted(missed_dates)[-5:]  # Last 5 missed dates
            })
    
    # Sort by most missed trades first
    missed_traders.sort(key=lambda x: x["missed_trades_count"], reverse=True)
    
    # Calculate today's team stats
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    today_trades = [t for t in all_trades if t.get("created_at", "").startswith(today_str)]
    team_profit_today = sum(t.get("actual_profit", 0) for t in today_trades)
    users_who_traded_today = set(t.get("user_id") for t in today_trades)
    
    highest_earner = None
    highest_profit = 0
    for trade in today_trades:
        if trade.get("actual_profit", 0) > highest_profit:
            highest_profit = trade.get("actual_profit", 0)
            user_data = next((u for u in all_users if u["id"] == trade.get("user_id")), None)
            if user_data:
                highest_earner = user_data.get("full_name", "Unknown")
    
    return {
        "missed_traders": missed_traders,
        "team_profit_today": round(team_profit_today, 2),
        "highest_earner": highest_earner,
        "highest_profit": round(highest_profit, 2),
        "total_traded_today": len(users_who_traded_today)
    }

@admin_router.get("/analytics/today-stats")
async def get_today_stats(user: dict = Depends(require_admin)):
    """Get today's team performance stats (profit and commissions)"""
    
    # Get today's date range
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # Get today's trades
    today_trades = await db.trade_logs.find({
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0}).to_list(1000)
    
    # Calculate total profit
    total_profit = sum(t.get("actual_profit", 0) for t in today_trades)
    
    # Get today's commissions from deposits
    today_commissions = await db.deposits.find({
        "type": "commission",
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0}).to_list(500)
    
    total_commission = sum(c.get("amount", 0) for c in today_commissions)
    
    return {
        "total_profit": round(total_profit, 2),
        "total_commission": round(total_commission, 2),
        "trades_count": len(today_trades)
    }

class NotifyMissedTradeRequest(BaseModel):
    user_id: str

@admin_router.post("/analytics/notify-missed")
async def notify_missed_trade(data: NotifyMissedTradeRequest, user: dict = Depends(require_admin)):
    """Send email to member who missed the trade"""
    member = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get today's stats
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    today_trades = await db.trade_logs.find({
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0}).to_list(1000)
    
    team_profit = sum(t.get("actual_profit", 0) for t in today_trades)
    
    # Find highest earner
    highest_earner = "the team"
    highest_profit = 0
    for trade in today_trades:
        if trade.get("actual_profit", 0) > highest_profit:
            highest_profit = trade.get("actual_profit", 0)
            trader = await db.users.find_one({"id": trade.get("user_id")}, {"_id": 0})
            if trader:
                highest_earner = trader.get("full_name", "a teammate")
    
    # Create email content
    subject = "You Missed Today's Trade! 🚨"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #18181B; color: #fff; padding: 40px; border-radius: 16px;">
        <h1 style="color: #EF4444; margin-bottom: 20px;">You Missed Today's Trade!</h1>
        <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6;">
            Hey {member.get('full_name', 'Trader')},
        </p>
        <div style="background: linear-gradient(135deg, #1E3A5F 0%, #1E1E3F 100%); padding: 30px; border-radius: 12px; margin: 20px 0;">
            <p style="color: #fff; font-size: 18px; margin: 0;">
                The team earned <span style="color: #10B981; font-weight: bold; font-size: 24px;">${team_profit:.2f}</span> today,
                but you weren't a part of it.
            </p>
            <p style="color: #A1A1AA; margin-top: 15px;">
                The highest earner is <span style="color: #3B82F6; font-weight: bold;">{highest_earner}</span> 
                with <span style="color: #10B981;">${highest_profit:.2f}</span>!
            </p>
        </div>
        <p style="color: #FBBF24; font-size: 18px; font-weight: bold; text-align: center;">
            🔔 Remember to join us for tomorrow's trade!
        </p>
        <hr style="border: none; border-top: 1px solid #27272A; margin: 30px 0;">
        <p style="color: #71717A; font-size: 12px; text-align: center;">
            CrossCurrent Finance Center - Your Trading Success Partner
        </p>
    </div>
    """
    
    if not EMAILIT_API_KEY:
        # Return preview if email not configured
        return {
            "message": "Email preview (Emailit not configured)",
            "preview": {
                "to": member.get("email"),
                "subject": subject,
                "team_profit": round(team_profit, 2),
                "highest_earner": highest_earner,
                "highest_profit": round(highest_profit, 2)
            }
        }
    
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
                    "to": member["email"],
                    "subject": subject,
                    "html": html_body
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to send email")
                
        return {"message": f"Notification sent to {member.get('full_name')}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")

@admin_router.get("/analytics/growth-data")
async def get_growth_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(require_admin)
):
    """Get historical data for growth charts with optional date filtering"""
    
    # Build query filter
    query = {}
    
    # Get all trades sorted by date
    all_trades = await db.trade_logs.find({}, {"_id": 0}).sort("created_at", 1).to_list(10000)
    
    # Get all deposits sorted by date
    all_deposits = await db.deposits.find({}, {"_id": 0}).sort("created_at", 1).to_list(10000)
    
    # Build daily aggregates
    daily_data = {}
    running_account_value = 0
    running_profit = 0
    running_trades = 0
    running_winning = 0
    
    for deposit in all_deposits:
        date_str = deposit.get("created_at", "")[:10]  # Get YYYY-MM-DD
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "deposits": 0,
                "withdrawals": 0,
                "profit": 0,
                "trades": 0,
                "winning": 0
            }
        
        if deposit.get("type") == "withdrawal":
            daily_data[date_str]["withdrawals"] += abs(deposit.get("amount", 0))
        else:
            daily_data[date_str]["deposits"] += deposit.get("amount", 0)
    
    for trade in all_trades:
        date_str = trade.get("created_at", "")[:10]
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "deposits": 0,
                "withdrawals": 0,
                "profit": 0,
                "trades": 0,
                "winning": 0
            }
        
        daily_data[date_str]["profit"] += trade.get("actual_profit", 0)
        daily_data[date_str]["trades"] += 1
        if trade.get("performance") in ["exceeded", "perfect"]:
            daily_data[date_str]["winning"] += 1
    
    # Build cumulative chart data with optional date filtering
    chart_data = []
    for date_str in sorted(daily_data.keys()):
        day = daily_data[date_str]
        running_account_value += day["deposits"] - day["withdrawals"] + day["profit"]
        running_profit += day["profit"]
        running_trades += day["trades"]
        running_winning += day["winning"]
        
        # Apply date filter
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
        
        performance_rate = (running_winning / running_trades * 100) if running_trades > 0 else 0
        
        chart_data.append({
            "date": date_str,
            "account_value": round(running_account_value, 2),
            "total_profit": round(running_profit, 2),
            "total_trades": running_trades,
            "performance_rate": round(performance_rate, 1)
        })
    
    # If no date filter, return last 30 points; otherwise return all filtered data
    if not start_date and not end_date:
        return {"chart_data": chart_data[-30:]}
    return {"chart_data": chart_data}

@admin_router.get("/analytics/member/{user_id}")
async def get_member_analytics(user_id: str, user: dict = Depends(require_admin)):
    """Get individual member analytics"""
    
    member = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get deposits
    deposits = await db.deposits.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") not in ["profit", "withdrawal"])
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
    
    # Get trades
    trades = await db.trade_logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    account_value = total_deposits - total_withdrawals + total_profit
    
    winning_trades = len([t for t in trades if t.get("performance") in ["exceeded", "perfect"]])
    performance_rate = (winning_trades / len(trades) * 100) if trades else 0
    
    # Build daily trade history for chart
    trade_history = {}
    for trade in trades:
        date_str = trade.get("created_at", "")[:10]
        if date_str not in trade_history:
            trade_history[date_str] = {"date": date_str, "profit": 0, "trades": 0}
        trade_history[date_str]["profit"] += trade.get("actual_profit", 0)
        trade_history[date_str]["trades"] += 1
    
    return {
        "member": {
            "id": member["id"],
            "name": member.get("full_name", "Unknown"),
            "email": member.get("email", ""),
            "role": member.get("role", "member"),
            "timezone": member.get("timezone", "Asia/Manila"),
            "joined": member.get("created_at", "")
        },
        "stats": {
            "account_value": round(account_value, 2),
            "lot_size": round(account_value / 980, 2) if account_value > 0 else 0,
            "total_deposits": round(total_deposits, 2),
            "total_withdrawals": round(total_withdrawals, 2),
            "total_profit": round(total_profit, 2),
            "total_trades": len(trades),
            "winning_trades": winning_trades,
            "performance_rate": round(performance_rate, 1)
        },
        "recent_trades": trades[:10],
        "trade_history": sorted(trade_history.values(), key=lambda x: x["date"])[-30:]
    }

@admin_router.get("/analytics/recent-trades")
async def get_recent_team_trades(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(require_admin)
):
    """Get recent trades from all team members with pagination"""
    
    # Get all users for name lookup
    all_users = await db.users.find({}, {"_id": 0, "id": 1, "full_name": 1}).to_list(1000)
    user_names = {u["id"]: u.get("full_name", "Unknown") for u in all_users}
    
    skip = (page - 1) * page_size
    total = await db.trade_logs.count_documents({})
    
    trades = await db.trade_logs.find({}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Add user names to trades and ensure commission field is present
    enriched_trades = []
    for trade in trades:
        trade["trader_name"] = user_names.get(trade.get("user_id"), "Unknown")
        trade["commission"] = trade.get("commission", 0)  # Default to 0 for backward compatibility
        enriched_trades.append(trade)
    
    return {
        "trades": enriched_trades,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }

@admin_router.post("/analytics/archive-trades")
async def archive_old_trades(user: dict = Depends(require_super_admin)):
    """Archive trades older than 3 days, delete archive older than 2 months"""
    now = datetime.now(timezone.utc)
    
    # Archive threshold: 3 days ago
    archive_threshold = now - timedelta(days=3)
    
    # Delete threshold: 2 months ago
    delete_threshold = now - timedelta(days=60)
    
    # Delete very old archived trades
    delete_result = await db.trade_logs.delete_many({
        "is_archived": True,
        "archived_at": {"$lt": delete_threshold.isoformat()}
    })
    
    # Archive trades older than 3 days
    archive_result = await db.trade_logs.update_many(
        {
            "created_at": {"$lt": archive_threshold.isoformat()},
            "is_archived": {"$ne": True}
        },
        {
            "$set": {
                "is_archived": True,
                "archived_at": now.isoformat()
            }
        }
    )
    
    return {
        "archived_count": archive_result.modified_count,
        "deleted_count": delete_result.deleted_count
    }

# ==================== ADMIN NOTIFICATIONS ====================
@admin_router.get("/notifications")
async def get_admin_notifications(
    limit: int = 50,
    unread_only: bool = False,
    user: dict = Depends(require_admin)
):
    """Get notifications for admins (deposits, withdrawals, underperforming trades)"""
    # Check if user is super_admin or master_admin
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can view notifications")
    
    query = {}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.admin_notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Count unread
    unread_count = await db.admin_notifications.count_documents({"is_read": False})
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@admin_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(require_admin)):
    """Mark a notification as read"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can manage notifications")
    
    result = await db.admin_notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@admin_router.put("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(require_admin)):
    """Mark all notifications as read"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can manage notifications")
    
    result = await db.admin_notifications.update_many(
        {"is_read": False},
        {"$set": {"is_read": True}}
    )
    
    return {"message": f"Marked {result.modified_count} notifications as read"}

# ==================== TEAM TRANSACTIONS ====================
@admin_router.get("/transactions")
async def get_team_transactions(
    page: int = 1,
    page_size: int = 20,
    transaction_type: Optional[str] = None,  # deposit, withdrawal, or None for all
    user: dict = Depends(require_admin)
):
    """Get all team transactions (deposits and withdrawals) with pagination"""
    # Check if user is super_admin or master_admin
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can view transactions")
    
    # Get all users for name lookup
    all_users = await db.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "email": 1}).to_list(1000)
    user_lookup = {u["id"]: {"name": u.get("full_name", "Unknown"), "email": u.get("email", "")} for u in all_users}
    
    # Build query
    query = {}
    if transaction_type == "withdrawal":
        query["is_withdrawal"] = True
    elif transaction_type == "deposit":
        query["$or"] = [
            {"is_withdrawal": {"$ne": True}},
            {"is_withdrawal": {"$exists": False}}
        ]
    
    skip = (page - 1) * page_size
    total = await db.deposits.count_documents(query)
    
    transactions = await db.deposits.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Enrich with user info
    enriched = []
    for tx in transactions:
        user_info = user_lookup.get(tx.get("user_id"), {"name": "Unknown", "email": ""})
        tx["user_name"] = user_info["name"]
        tx["user_email"] = user_info["email"]
        tx["type"] = "withdrawal" if tx.get("is_withdrawal") else "deposit"
        enriched.append(tx)
    
    # Get summary stats
    all_deposits = await db.deposits.find({}, {"_id": 0}).to_list(10000)
    total_deposits = sum(d.get("amount", 0) for d in all_deposits if not d.get("is_withdrawal") and d.get("amount", 0) > 0)
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in all_deposits if d.get("is_withdrawal"))
    
    return {
        "transactions": enriched,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        "summary": {
            "total_deposits": round(total_deposits, 2),
            "total_withdrawals": round(total_withdrawals, 2),
            "net_flow": round(total_deposits - total_withdrawals, 2)
        }
    }

@admin_router.get("/transactions/stats")
async def get_transaction_stats(user: dict = Depends(require_admin)):
    """Get transaction statistics summary"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin and Master Admin can view transaction stats")
    
    all_deposits = await db.deposits.find({}, {"_id": 0}).to_list(10000)
    
    # Calculate stats
    deposits = [d for d in all_deposits if not d.get("is_withdrawal") and d.get("amount", 0) > 0]
    withdrawals = [d for d in all_deposits if d.get("is_withdrawal")]
    
    total_deposits = sum(d.get("amount", 0) for d in deposits)
    total_withdrawals = sum(abs(d.get("amount", 0)) for d in withdrawals)
    
    # Get unique depositors
    unique_depositors = len(set(d.get("user_id") for d in deposits))
    
    # Get today's stats
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_deposits = sum(d.get("amount", 0) for d in deposits if d.get("created_at", "").startswith(today))
    today_withdrawals = sum(abs(d.get("amount", 0)) for d in withdrawals if d.get("created_at", "").startswith(today))
    
    return {
        "total_deposits": round(total_deposits, 2),
        "total_withdrawals": round(total_withdrawals, 2),
        "net_flow": round(total_deposits - total_withdrawals, 2),
        "deposit_count": len(deposits),
        "withdrawal_count": len(withdrawals),
        "unique_depositors": unique_depositors,
        "today_deposits": round(today_deposits, 2),
        "today_withdrawals": round(today_withdrawals, 2)
    }

# ==================== LICENSE MANAGEMENT ====================
def get_us_trading_holidays(year: int) -> set:
    """Get US stock market holidays for a given year"""
    holidays = set()
    
    # Fixed holidays (or observed dates)
    holidays.add(f"{year}-01-01")  # New Year's Day
    holidays.add(f"{year}-07-04")  # Independence Day
    holidays.add(f"{year}-12-25")  # Christmas
    holidays.add(f"{year}-06-19")  # Juneteenth
    
    # Variable holidays (simplified - would need proper calculation)
    # MLK Day - 3rd Monday of January
    # Presidents' Day - 3rd Monday of February
    # Good Friday - varies
    # Memorial Day - Last Monday of May
    # Labor Day - 1st Monday of September
    # Thanksgiving - 4th Thursday of November
    
    # For 2026 specifically:
    if year == 2026:
        holidays.update([
            "2026-01-19",  # MLK Day
            "2026-02-16",  # Presidents' Day
            "2026-04-03",  # Good Friday
            "2026-05-25",  # Memorial Day
            "2026-09-07",  # Labor Day
            "2026-11-26",  # Thanksgiving
        ])
    
    return holidays

def is_trading_day(date: datetime) -> bool:
    """Check if a date is a valid trading day (not weekend or holiday)"""
    if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    holidays = get_us_trading_holidays(date.year)
    date_str = date.strftime("%Y-%m-%d")
    return date_str not in holidays

def get_quarter(date: datetime) -> int:
    """Get the quarter number (1-4) for a date"""
    return (date.month - 1) // 3 + 1

def get_quarter_start(year: int, quarter: int) -> datetime:
    """Get the first day of a quarter"""
    month = (quarter - 1) * 3 + 1
    return datetime(year, month, 1, tzinfo=timezone.utc)

def get_quarter_end(year: int, quarter: int) -> datetime:
    """Get the last day of a quarter"""
    if quarter == 4:
        return datetime(year, 12, 31, tzinfo=timezone.utc)
    else:
        next_quarter_start = get_quarter_start(year, quarter + 1)
        return next_quarter_start - timedelta(days=1)

def get_first_trading_day_of_quarter(year: int, quarter: int) -> datetime:
    """Get the first valid trading day of a quarter"""
    date = get_quarter_start(year, quarter)
    while not is_trading_day(date):
        date += timedelta(days=1)
    return date

def calculate_extended_license_projections(starting_amount: float, start_date: datetime, days_to_project: int = 365) -> List[Dict]:
    """
    Calculate projections for Extended Licensee using quarterly compounding.
    Daily profit AND lot size are fixed within each quarter and recalculated at quarter start.
    """
    projections = []
    current_date = start_date
    current_amount = starting_amount
    current_quarter = get_quarter(start_date)
    current_year = start_date.year
    
    # Calculate initial quarter's values (FIXED for entire quarter)
    quarter_lot_size = round(current_amount / 980, 2)
    quarter_daily_profit = round(quarter_lot_size * 15, 2)
    quarter_start_amount = current_amount
    
    trading_days_processed = 0
    
    while trading_days_processed < days_to_project:
        # Check if we've moved to a new quarter
        new_quarter = get_quarter(current_date)
        new_year = current_date.year
        
        if new_year != current_year or new_quarter != current_quarter:
            # Recalculate lot size and daily profit for new quarter using accumulated amount
            quarter_lot_size = round(current_amount / 980, 2)
            quarter_daily_profit = round(quarter_lot_size * 15, 2)
            quarter_start_amount = current_amount
            current_quarter = new_quarter
            current_year = new_year
        
        if is_trading_day(current_date):
            current_amount = round(current_amount + quarter_daily_profit, 2)
            
            projections.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "quarter": f"Q{current_quarter} {current_year}",
                "lot_size": quarter_lot_size,  # FIXED for entire quarter
                "daily_profit": quarter_daily_profit,  # FIXED for entire quarter
                "account_value": current_amount,
                "cumulative_profit": round(current_amount - starting_amount, 2),
                "is_trading_day": True
            })
            
            trading_days_processed += 1
        
        current_date += timedelta(days=1)
    
    return projections

@admin_router.get("/licenses")
async def get_all_licenses(user: dict = Depends(require_admin)):
    """Get all licensed users (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can manage licenses")
    
    licenses = await db.licenses.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with user info (including timezone for profile editing)
    all_users = await db.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "email": 1, "timezone": 1}).to_list(1000)
    user_lookup = {u["id"]: u for u in all_users}
    
    enriched = []
    for lic in licenses:
        user_info = user_lookup.get(lic["user_id"], {})
        lic["user_name"] = user_info.get("full_name", "Unknown")
        lic["user_email"] = user_info.get("email", "")
        lic["user_timezone"] = user_info.get("timezone", "Asia/Manila")
        
        # Calculate current amount for extended licensees
        if lic["license_type"] == "extended" and lic.get("is_active"):
            # Parse start_date - handle both string and datetime formats
            start_date_raw = lic.get("start_date", "")
            if isinstance(start_date_raw, str):
                # Parse date string like "2026-01-01" as UTC
                start_date = datetime.strptime(start_date_raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                start_date = start_date_raw.replace(tzinfo=timezone.utc)
            
            today = datetime.now(timezone.utc)
            days_since_start = (today - start_date).days
            if days_since_start > 0:
                projections = calculate_extended_license_projections(
                    lic["starting_amount"], 
                    start_date, 
                    min(days_since_start + 1, 365)
                )
                if projections:
                    lic["current_amount"] = projections[-1]["account_value"]
                else:
                    lic["current_amount"] = lic["starting_amount"]
            else:
                lic["current_amount"] = lic["starting_amount"]
        else:
            lic["current_amount"] = lic.get("starting_amount", 0)
        
        enriched.append(lic)
    
    return {"licenses": enriched}

@admin_router.post("/licenses")
async def create_license(data: LicenseCreate, user: dict = Depends(require_admin)):
    """Create a new license for a user (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can create licenses")
    
    # Verify target user exists
    target_user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user already has an active license
    existing = await db.licenses.find_one({"user_id": data.user_id, "is_active": True}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="User already has an active license")
    
    # Validate license type
    if data.license_type not in ["extended", "honorary"]:
        raise HTTPException(status_code=400, detail="Invalid license type. Must be 'extended' or 'honorary'")
    
    # Determine start date
    if data.start_date:
        start_date = datetime.fromisoformat(data.start_date)
    else:
        # Default to first trading day of current quarter
        today = datetime.now(timezone.utc)
        start_date = get_first_trading_day_of_quarter(today.year, get_quarter(today))
    
    license_id = str(uuid.uuid4())
    license_doc = {
        "id": license_id,
        "user_id": data.user_id,
        "license_type": data.license_type,
        "starting_amount": data.starting_amount,
        "current_amount": data.starting_amount,  # Set current_amount = starting_amount
        "start_date": start_date.isoformat(),
        "notes": data.notes,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    
    await db.licenses.insert_one(license_doc)
    
    # Update user record with license type and account_value
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {
            "license_type": data.license_type,
            "account_value": data.starting_amount  # Sync account_value with license
        }}
    )
    
    # Record the starting amount as an initial deposit transaction
    if data.starting_amount > 0:
        initial_deposit = {
            "id": str(uuid.uuid4()),
            "user_id": data.user_id,
            "type": "deposit",
            "amount": data.starting_amount,
            "status": "completed",
            "deposit_date": start_date.isoformat(),
            "notes": "Initial starting balance",
            "is_initial_balance": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "completed_by": user["id"]
        }
        await db.licensee_transactions.insert_one(initial_deposit)
    
    return {"message": "License created successfully", "license_id": license_id}

@admin_router.get("/licenses/{license_id}")
async def get_license_details(license_id: str, user: dict = Depends(require_admin)):
    """Get detailed license information including projections"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view license details")
    
    license_doc = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get user info
    target_user = await db.users.find_one({"id": license_doc["user_id"]}, {"_id": 0, "password": 0})
    
    result = {
        "license": license_doc,
        "user": target_user
    }
    
    # Calculate projections for extended licensees
    if license_doc["license_type"] == "extended":
        start_date = datetime.fromisoformat(license_doc["start_date"].replace("Z", "+00:00"))
        projections = calculate_extended_license_projections(
            license_doc["starting_amount"],
            start_date,
            365  # 1 year projection
        )
        result["projections"] = projections
        
        # Get current values
        today = datetime.now(timezone.utc)
        today_str = today.strftime("%Y-%m-%d")
        current_projection = next((p for p in projections if p["date"] == today_str), None)
        if current_projection:
            result["current_values"] = current_projection
        elif projections:
            # Find the most recent trading day
            result["current_values"] = projections[-1]
    
    return result


@admin_router.get("/licenses/{license_id}/projections")
async def get_license_projections(license_id: str, user: dict = Depends(require_admin)):
    """Get daily projections for a specific license (for simulation view)
    
    This endpoint returns projections that can be used by the frontend
    when the Master Admin is simulating a licensee's view.
    """
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view license projections")
    
    license_doc = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Use effective_start_date if available, otherwise start_date
    effective_start = license_doc.get("effective_start_date") or license_doc.get("start_date")
    if effective_start:
        # Handle various date formats
        if "T" in effective_start:
            # Full datetime string
            start_date = datetime.fromisoformat(effective_start.replace("Z", "+00:00") if "Z" in effective_start else effective_start)
        else:
            # Date-only string (YYYY-MM-DD) - parse and add timezone
            start_date = datetime.strptime(effective_start[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        # Ensure timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
    else:
        start_date = datetime.now(timezone.utc)
    
    starting_amount = license_doc.get("starting_amount", 0)
    current_amount = license_doc.get("current_amount", starting_amount)
    
    # Get Master Admin's trade logs to determine which days manager traded
    master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1})
    master_trade_logs = {}
    if master_admin:
        trades = await db.trade_logs.find({"user_id": master_admin["id"]}, {"_id": 0}).to_list(1000)
        for trade in trades:
            date_key = trade.get("trade_date") or trade.get("created_at", "")[:10]
            if date_key:
                master_trade_logs[date_key] = {
                    "traded": trade.get("has_traded", True),
                    "actual_profit": trade.get("actual_profit", 0),
                    "commission": trade.get("commission", 0)
                }
    
    # Get trade overrides for this license
    overrides = {}
    async for override in db.licensee_trade_overrides.find({"license_id": license_id}, {"_id": 0}):
        overrides[override["date"]] = override
    
    # Generate projections for up to 2 years from start date
    # IMPORTANT: For BOTH honorary and extended licensees, use QUARTERLY COMPOUNDING
    # Lot size and daily profit are fixed for the entire quarter
    projections = []
    current_balance = starting_amount
    
    # Track quarter for quarterly compounding
    current_quarter = get_quarter(start_date)
    current_year = start_date.year
    
    # Calculate initial quarter's values (FIXED for entire quarter)
    quarter_lot_size = round(current_balance / 980, 2)
    quarter_daily_profit = round(quarter_lot_size * 15, 2)
    
    # Generate projections day by day
    current_date = start_date
    end_date = datetime.now(timezone.utc) + timedelta(days=365)  # Up to 1 year from now
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
        
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Check if we've moved to a new quarter - recalculate lot size and daily profit
        new_quarter = get_quarter(current_date)
        new_year = current_date.year
        
        if new_year != current_year or new_quarter != current_quarter:
            # Recalculate lot size and daily profit for new quarter using accumulated balance
            quarter_lot_size = round(current_balance / 980, 2)
            quarter_daily_profit = round(quarter_lot_size * 15, 2)
            current_quarter = new_quarter
            current_year = new_year
        
        # Use FIXED quarter values (not recalculated daily)
        lot_size = quarter_lot_size
        daily_profit = quarter_daily_profit
        
        # Check if manager traded (override takes precedence)
        override = overrides.get(date_str)
        master_trade = master_trade_logs.get(date_str)
        
        if override:
            manager_traded = override.get("traded", False)
        elif master_trade:
            manager_traded = master_trade.get("traded", True)
        else:
            manager_traded = False  # No trade record = didn't trade
        
        projections.append({
            "date": date_str,
            "start_value": current_balance,
            "account_value": current_balance + daily_profit if manager_traded else current_balance,
            "lot_size": lot_size,
            "daily_profit": daily_profit,
            "manager_traded": manager_traded,
            "has_override": override is not None
        })
        
        # Update balance for next day (only if manager traded AND day is in the past or today)
        if manager_traded and current_date <= datetime.now(timezone.utc):
            current_balance = current_balance + daily_profit
        
        current_date += timedelta(days=1)
    
    return {
        "license": license_doc,
        "projections": projections,
        "current_amount": current_amount,
        "starting_amount": starting_amount,
        "master_trade_logs": master_trade_logs
    }


@admin_router.put("/licenses/{license_id}")
async def update_license(license_id: str, starting_amount: Optional[float] = None, notes: Optional[str] = None, is_active: Optional[bool] = None, user: dict = Depends(require_admin)):
    """Update a license (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update licenses")
    
    license_doc = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    update_fields = {}
    if starting_amount is not None:
        update_fields["starting_amount"] = starting_amount
    if notes is not None:
        update_fields["notes"] = notes
    if is_active is not None:
        update_fields["is_active"] = is_active
        # Update user record if deactivating
        if not is_active:
            await db.users.update_one(
                {"id": license_doc["user_id"]},
                {"$unset": {"license_type": ""}}
            )
    
    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.licenses.update_one({"id": license_id}, {"$set": update_fields})
    
    return {"message": "License updated successfully"}

class ChangeLicenseTypeRequest(BaseModel):
    new_license_type: str
    new_starting_amount: float
    notes: Optional[str] = None

@admin_router.post("/licenses/{license_id}/change-type")
async def change_license_type(license_id: str, data: ChangeLicenseTypeRequest, user: dict = Depends(require_admin)):
    """Change license type - creates new license and invalidates old one (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can change license types")
    
    # Get existing license
    old_license = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not old_license:
        raise HTTPException(status_code=404, detail="License not found")
    
    if not old_license.get("is_active"):
        raise HTTPException(status_code=400, detail="Cannot change an inactive license")
    
    if data.new_license_type not in ["extended", "honorary"]:
        raise HTTPException(status_code=400, detail="Invalid license type")
    
    # Deactivate old license
    await db.licenses.update_one(
        {"id": license_id},
        {"$set": {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc).isoformat(),
            "deactivation_reason": f"Changed to {data.new_license_type} by {user['full_name']}"
        }}
    )
    
    # Create new license
    new_license_id = str(uuid.uuid4())
    new_license = {
        "id": new_license_id,
        "user_id": old_license["user_id"],
        "license_type": data.new_license_type,
        "starting_amount": data.new_starting_amount,
        "current_amount": data.new_starting_amount,
        "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "is_active": True,
        "notes": data.notes or f"Changed from {old_license['license_type']} license",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "previous_license_id": license_id
    }
    await db.licenses.insert_one(new_license)
    
    # Update user record
    await db.users.update_one(
        {"id": old_license["user_id"]},
        {"$set": {"license_type": data.new_license_type}}
    )
    
    return {"message": f"License changed to {data.new_license_type}", "new_license_id": new_license_id}

class ResetStartingAmountRequest(BaseModel):
    new_amount: float
    notes: Optional[str] = None
    record_as_deposit: bool = True  # Whether to record the adjustment as a deposit/withdrawal

@admin_router.post("/licenses/{license_id}/reset-balance")
async def reset_license_balance(license_id: str, data: ResetStartingAmountRequest, user: dict = Depends(require_admin)):
    """Reset license starting amount/current balance (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can reset license balances")
    
    if data.new_amount < 0:
        raise HTTPException(status_code=400, detail="Amount cannot be negative")
    
    license = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    if not license.get("is_active"):
        raise HTTPException(status_code=400, detail="Cannot reset an inactive license")
    
    old_amount = license.get("current_amount", license.get("starting_amount", 0))
    difference = data.new_amount - old_amount
    
    # Update license
    await db.licenses.update_one(
        {"id": license_id},
        {"$set": {
            "starting_amount": data.new_amount,
            "current_amount": data.new_amount,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "reset_by": user["id"],
            "reset_notes": data.notes
        }}
    )
    
    # Update user's account_value
    await db.users.update_one(
        {"id": license["user_id"]},
        {"$set": {"account_value": data.new_amount}}
    )
    
    # Record adjustment as transaction
    if data.record_as_deposit and difference != 0:
        adjustment_type = "deposit" if difference > 0 else "withdrawal"
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": license["user_id"],
            "type": adjustment_type,
            "amount": abs(difference),
            "status": "completed",
            "notes": data.notes or f"Balance reset by admin (was ${old_amount:,.2f}, now ${data.new_amount:,.2f})",
            "is_balance_reset": True,
            "balance_before": old_amount,
            "balance_after": data.new_amount,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "completed_by": user["id"]
        }
        await db.licensee_transactions.insert_one(transaction)
    
    return {
        "message": f"License balance reset from ${old_amount:,.2f} to ${data.new_amount:,.2f}",
        "old_amount": old_amount,
        "new_amount": data.new_amount
    }

@admin_router.delete("/licenses/{license_id}")
async def delete_license(license_id: str, user: dict = Depends(require_admin)):
    """Delete a license (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete licenses")
    
    license_doc = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Remove license type from user
    await db.users.update_one(
        {"id": license_doc["user_id"]},
        {"$unset": {"license_type": ""}}
    )
    
    await db.licenses.delete_one({"id": license_id})
    
    return {"message": "License deleted successfully"}

@admin_router.put("/licenses/{license_id}/effective-start-date")
async def update_license_effective_start_date(
    license_id: str,
    effective_start_date: str = Body(..., embed=True),
    user: dict = Depends(require_admin)
):
    """Update the effective start date for a license (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update license effective start date")
    
    license_doc = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Validate date format
    try:
        datetime.strptime(effective_start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    old_date = license_doc.get("effective_start_date", license_doc.get("start_date"))
    
    await db.licenses.update_one(
        {"id": license_id},
        {"$set": {
            "effective_start_date": effective_start_date,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": f"Effective start date updated from {old_date} to {effective_start_date}",
        "old_date": old_date,
        "new_date": effective_start_date
    }

# ==================== LICENSE INVITES ====================
def calculate_validity_date(duration: str) -> Optional[str]:
    """Calculate expiry date based on duration string"""
    if duration == "indefinite":
        return None
    
    today = datetime.now(timezone.utc)
    if duration == "3_months":
        expiry = today + timedelta(days=90)
    elif duration == "6_months":
        expiry = today + timedelta(days=180)
    elif duration == "1_year":
        expiry = today + timedelta(days=365)
    else:
        expiry = today + timedelta(days=90)  # Default to 3 months
    
    return expiry.isoformat()

def generate_invite_code() -> str:
    """Generate a unique invite code"""
    import secrets
    return f"LIC-{secrets.token_urlsafe(12).upper()[:16]}"

# ==================== LICENSEE TRADE OVERRIDES ====================

@admin_router.get("/licenses/{license_id}/trade-overrides")
async def get_license_trade_overrides(license_id: str, user: dict = Depends(require_admin)):
    """Get all trade overrides for a specific license"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view trade overrides")
    
    overrides = await db.licensee_trade_overrides.find(
        {"license_id": license_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Convert to a dict keyed by date for easy lookup
    overrides_by_date = {o["date"]: o for o in overrides}
    
    return {"overrides": overrides_by_date}

@admin_router.post("/licenses/{license_id}/trade-overrides")
async def set_license_trade_override(
    license_id: str,
    data: LicenseeTradeOverride,
    user: dict = Depends(require_admin)
):
    """Set or update a trade override for a specific license on a specific date"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can set trade overrides")
    
    # Validate license exists
    license_doc = await db.licenses.find_one({"id": license_id}, {"_id": 0})
    if not license_doc:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Validate date format
    try:
        datetime.strptime(data.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Check if override already exists
    existing = await db.licensee_trade_overrides.find_one(
        {"license_id": license_id, "date": data.date},
        {"_id": 0}
    )
    
    if existing:
        # Update existing override
        await db.licensee_trade_overrides.update_one(
            {"license_id": license_id, "date": data.date},
            {"$set": {
                "traded": data.traded,
                "notes": data.notes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": user["id"]
            }}
        )
        action = "updated"
    else:
        # Create new override
        override_doc = {
            "id": str(uuid.uuid4()),
            "license_id": license_id,
            "date": data.date,
            "traded": data.traded,
            "notes": data.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        await db.licensee_trade_overrides.insert_one(override_doc)
        action = "created"
    
    return {
        "message": f"Trade override {action} successfully",
        "license_id": license_id,
        "date": data.date,
        "traded": data.traded
    }

@admin_router.delete("/licenses/{license_id}/trade-overrides/{date}")
async def delete_license_trade_override(
    license_id: str,
    date: str,
    user: dict = Depends(require_admin)
):
    """Delete a trade override (revert to automatic detection)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete trade overrides")
    
    result = await db.licensee_trade_overrides.delete_one(
        {"license_id": license_id, "date": date}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Override not found")
    
    return {"message": "Trade override deleted, reverting to automatic detection"}

@admin_router.get("/license-invites")
async def get_all_license_invites(user: dict = Depends(require_admin)):
    """Get all license invites (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can manage license invites")
    
    invites = await db.license_invites.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with usage info
    for invite in invites:
        # Check if expired
        if invite.get("valid_until"):
            valid_until = datetime.fromisoformat(invite["valid_until"].replace("Z", "+00:00"))
            invite["is_expired"] = datetime.now(timezone.utc) > valid_until
        else:
            invite["is_expired"] = False
        
        # Check if fully used
        invite["is_fully_used"] = invite.get("uses_count", 0) >= invite.get("max_uses", 1)
        
        # Get users who registered with this invite
        registered_users = await db.users.find(
            {"license_invite_code": invite["code"]}, 
            {"_id": 0, "id": 1, "full_name": 1, "email": 1, "created_at": 1}
        ).to_list(100)
        invite["registered_users"] = registered_users
    
    return {"invites": invites}

@admin_router.post("/license-invites")
async def create_license_invite(data: LicenseInviteCreate, user: dict = Depends(require_admin)):
    """Create a new license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can create license invites")
    
    if data.license_type not in ["extended", "honorary"]:
        raise HTTPException(status_code=400, detail="Invalid license type. Must be 'extended' or 'honorary'")
    
    invite_code = generate_invite_code()
    valid_until = calculate_validity_date(data.valid_duration)
    
    invite = {
        "id": str(uuid.uuid4()),
        "code": invite_code,
        "license_type": data.license_type,
        "starting_amount": data.starting_amount,
        "valid_duration": data.valid_duration,
        "valid_until": valid_until,
        "max_uses": data.max_uses,
        "uses_count": 0,
        "notes": data.notes,
        "invitee_email": data.invitee_email,
        "invitee_name": data.invitee_name,
        "effective_start_date": data.effective_start_date,  # When licensee's trading starts
        "is_revoked": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "created_by_name": user.get("full_name", "Admin")
    }
    
    await db.license_invites.insert_one(invite)
    
    # Generate registration URL
    frontend_url = os.environ.get("FRONTEND_URL", "https://hub-mobile-enhance.preview.emergentagent.com")
    registration_url = f"{frontend_url}/register/license/{invite_code}"
    
    return {
        "message": "License invite created successfully",
        "invite_id": invite["id"],
        "code": invite_code,
        "registration_url": registration_url,
        "starting_amount": invite["starting_amount"],
        "license_type": invite["license_type"]
    }

@admin_router.get("/license-invites/{invite_id}")
async def get_license_invite(invite_id: str, user: dict = Depends(require_admin)):
    """Get a specific license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view license invites")
    
    invite = await db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    # Get registered users
    registered_users = await db.users.find(
        {"license_invite_code": invite["code"]}, 
        {"_id": 0, "id": 1, "full_name": 1, "email": 1, "created_at": 1}
    ).to_list(100)
    invite["registered_users"] = registered_users
    
    return invite

@admin_router.put("/license-invites/{invite_id}")
async def update_license_invite(invite_id: str, data: LicenseInviteUpdate, user: dict = Depends(require_admin)):
    """Update a license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update license invites")
    
    invite = await db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.valid_duration is not None:
        update_fields["valid_duration"] = data.valid_duration
        update_fields["valid_until"] = calculate_validity_date(data.valid_duration)
    
    if data.max_uses is not None:
        update_fields["max_uses"] = data.max_uses
    
    if data.notes is not None:
        update_fields["notes"] = data.notes
    
    if data.invitee_email is not None:
        update_fields["invitee_email"] = data.invitee_email
    
    if data.invitee_name is not None:
        update_fields["invitee_name"] = data.invitee_name
    
    await db.license_invites.update_one({"id": invite_id}, {"$set": update_fields})
    
    return {"message": "License invite updated successfully"}

@admin_router.post("/license-invites/{invite_id}/revoke")
async def revoke_license_invite(invite_id: str, user: dict = Depends(require_admin)):
    """Revoke a license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can revoke license invites")
    
    invite = await db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    await db.license_invites.update_one(
        {"id": invite_id}, 
        {"$set": {"is_revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "License invite revoked successfully"}

@admin_router.post("/license-invites/{invite_id}/renew")
async def renew_license_invite(invite_id: str, new_duration: str = "3_months", user: dict = Depends(require_admin)):
    """Renew/revive an expired or revoked license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can renew license invites")
    
    invite = await db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    new_valid_until = calculate_validity_date(new_duration)
    
    await db.license_invites.update_one(
        {"id": invite_id}, 
        {"$set": {
            "is_revoked": False,
            "valid_duration": new_duration,
            "valid_until": new_valid_until,
            "renewed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "License invite renewed successfully", "valid_until": new_valid_until}

@admin_router.post("/license-invites/{invite_id}/resend")
async def resend_license_invite(invite_id: str, user: dict = Depends(require_admin)):
    """Resend license invite email (Master Admin only) - ILI"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can resend license invites")
    
    invite = await db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    if not invite.get("invitee_email"):
        raise HTTPException(status_code=400, detail="No email address associated with this invite")
    
    # Get email template
    template = await db.email_templates.find_one({"type": "license_invite"}, {"_id": 0})
    if not template:
        template = {
            "subject": "You've been invited to CrossCurrent Finance Center",
            "body": """Hello {{name}},

You have been invited to join CrossCurrent Finance Center as a {{license_type}} Licensee!

Click the link below to complete your registration:
{{registration_link}}

Your license details:
- Type: {{license_type}} Licensee
- Starting Amount: ${{starting_amount}}

This invite is valid until: {{valid_until}}

Best regards,
CrossCurrent Team"""
        }
    
    frontend_url = os.environ.get("FRONTEND_URL", "https://hub-mobile-enhance.preview.emergentagent.com")
    registration_url = f"{frontend_url}/register/license/{invite['code']}"
    
    # Replace template variables
    body = template["body"]
    body = body.replace("{{name}}", invite.get("invitee_name", "Trader"))
    body = body.replace("{{license_type}}", invite["license_type"].title())
    body = body.replace("{{registration_link}}", registration_url)
    body = body.replace("{{starting_amount}}", f"{invite['starting_amount']:,.2f}")
    body = body.replace("{{valid_until}}", invite.get("valid_until", "Indefinite")[:10] if invite.get("valid_until") else "Indefinite")
    
    subject = template["subject"]
    
    # Send email via Emailit
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    emailit_key = settings.get("emailit_api_key") if settings else None
    
    if not emailit_key:
        emailit_key = os.environ.get("EMAILIT_API_KEY")
    
    if emailit_key:
        try:
            email_response = requests.post(
                "https://api.emailit.com/v1/emails",
                headers={
                    "Authorization": f"Bearer {emailit_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "CrossCurrent Finance <noreply@crosscurrent.finance>",
                    "to": invite["invitee_email"],
                    "subject": subject,
                    "text": body
                },
                timeout=10
            )
            
            if email_response.status_code in [200, 201, 202]:
                await db.license_invites.update_one(
                    {"id": invite_id},
                    {"$set": {"last_sent_at": datetime.now(timezone.utc).isoformat()}}
                )
                return {"message": "License invite email sent successfully"}
            else:
                return {"message": "Email service returned an error, but invite is still valid", "registration_url": registration_url}
        except Exception as e:
            return {"message": f"Could not send email: {str(e)}", "registration_url": registration_url}
    else:
        return {"message": "Email service not configured. Please share the link manually.", "registration_url": registration_url}

@admin_router.delete("/license-invites/{invite_id}")
async def delete_license_invite(invite_id: str, user: dict = Depends(require_admin)):
    """Delete a license invite (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete license invites")
    
    invite = await db.license_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="License invite not found")
    
    await db.license_invites.delete_one({"id": invite_id})
    
    return {"message": "License invite deleted successfully"}

# Public endpoint to validate license invite code
@auth_router.get("/license-invite/{code}")
async def validate_license_invite(code: str):
    """Validate a license invite code (public endpoint for registration page)"""
    invite = await db.license_invites.find_one({"code": code}, {"_id": 0})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if invite.get("is_revoked"):
        raise HTTPException(status_code=400, detail="This invite has been revoked")
    
    # Check expiry
    if invite.get("valid_until"):
        valid_until = datetime.fromisoformat(invite["valid_until"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > valid_until:
            raise HTTPException(status_code=400, detail="This invite has expired")
    
    # Check uses
    if invite.get("uses_count", 0) >= invite.get("max_uses", 1):
        raise HTTPException(status_code=400, detail="This invite has reached its maximum number of uses")
    
    return {
        "valid": True,
        "license_type": invite["license_type"],
        "starting_amount": invite["starting_amount"],
        "invitee_name": invite.get("invitee_name"),
        "invitee_email": invite.get("invitee_email"),
        "valid_until": invite.get("valid_until"),
        "notes": invite.get("notes")
    }

# Registration with license invite
@auth_router.post("/register-with-license")
async def register_with_license(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    invite_code: str = Form(...)
):
    """Register a new user with a license invite code"""
    # Validate invite
    invite = await db.license_invites.find_one({"code": invite_code}, {"_id": 0})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if invite.get("is_revoked"):
        raise HTTPException(status_code=400, detail="This invite has been revoked")
    
    if invite.get("valid_until"):
        valid_until = datetime.fromisoformat(invite["valid_until"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > valid_until:
            raise HTTPException(status_code=400, detail="This invite has expired")
    
    if invite.get("uses_count", 0) >= invite.get("max_uses", 1):
        raise HTTPException(status_code=400, detail="This invite has reached its maximum number of uses")
    
    # Check if email already exists
    existing = await db.users.find_one({"email": email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    new_user = {
        "id": user_id,
        "email": email.lower(),
        "password": hashed_password.decode('utf-8'),
        "full_name": full_name,
        "role": "member",
        "allowed_dashboards": ["dashboard", "profit_tracker", "trade_monitor", "profile"],
        "timezone": "Asia/Manila",
        "lot_size": 0.01,
        "is_verified": False,
        "is_suspended": False,
        "license_invite_code": invite_code,
        "license_type": invite["license_type"],
        "has_seen_welcome": False,  # Track if licensee has seen welcome screen
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(new_user)
    
    # Determine effective start date - use invite's effective_start_date or today
    effective_start_date = invite.get("effective_start_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Create the actual license
    license_id = str(uuid.uuid4())
    license_doc = {
        "id": license_id,
        "user_id": user_id,
        "license_type": invite["license_type"],
        "starting_amount": invite["starting_amount"],
        "current_amount": invite["starting_amount"],  # Initialize current_amount
        "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "effective_start_date": effective_start_date,  # When trading projections start
        "notes": f"Created via invite: {invite_code}",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": invite.get("created_by", "system")
    }
    
    await db.licenses.insert_one(license_doc)
    
    # Increment invite uses count
    await db.license_invites.update_one(
        {"code": invite_code},
        {"$inc": {"uses_count": 1}}
    )
    
    # Generate token
    token = create_token(user_id, email.lower(), "member")
    
    # Remove password and _id from response
    del new_user["password"]
    if "_id" in new_user:
        del new_user["_id"]
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user,
        "license": {
            "type": invite["license_type"],
            "starting_amount": invite["starting_amount"]
        }
    }

# ==================== LICENSEE TRANSACTIONS ====================
@admin_router.get("/licensee-transactions")
async def get_all_licensee_transactions(user: dict = Depends(require_admin)):
    """Get all licensee deposit/withdrawal requests (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can view licensee transactions")
    
    transactions = await db.licensee_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with user info
    for tx in transactions:
        user_doc = await db.users.find_one({"id": tx["user_id"]}, {"_id": 0, "full_name": 1, "email": 1})
        if user_doc:
            tx["user_name"] = user_doc.get("full_name", "Unknown")
            tx["user_email"] = user_doc.get("email", "")
    
    return {"transactions": transactions}

@admin_router.post("/licensee-transactions/{tx_id}/feedback")
async def add_transaction_feedback(
    tx_id: str, 
    message: str = Form(...),
    status: Optional[str] = Form(None),
    final_amount: Optional[float] = Form(None),
    screenshot: Optional[UploadFile] = File(None),
    user: dict = Depends(require_admin)
):
    """Add feedback to a licensee transaction (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can respond to transactions")
    
    tx = await db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Handle screenshot upload
    screenshot_url = None
    if screenshot:
        try:
            contents = await screenshot.read()
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="licensee_transactions",
                resource_type="auto"
            )
            screenshot_url = upload_result.get("secure_url")
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {e}")
    
    feedback_entry = {
        "id": str(uuid.uuid4()),
        "message": message,
        "status_change": status,
        "final_amount": final_amount,
        "screenshot_url": screenshot_url,
        "from_admin": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "created_by_name": user.get("full_name", "Admin")
    }
    
    update_data = {
        "$push": {"feedback": feedback_entry},
        "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
    }
    
    if status:
        update_data["$set"]["status"] = status
    
    if final_amount is not None:
        update_data["$set"]["final_amount"] = final_amount
    
    await db.licensee_transactions.update_one({"id": tx_id}, update_data)
    
    # Create notification for the licensee
    notification = {
        "id": str(uuid.uuid4()),
        "type": "transaction_feedback",
        "title": f"Update on your {tx['type']} request",
        "message": message,
        "user_id": tx["user_id"],
        "admin_id": user["id"],
        "transaction_id": tx_id,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    return {"message": "Feedback added successfully"}

@admin_router.post("/licensee-transactions/{tx_id}/approve")
async def approve_transaction(tx_id: str, user: dict = Depends(require_admin)):
    """Approve/accept a pending transaction (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can approve transactions")
    
    tx = await db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    await db.licensee_transactions.update_one(
        {"id": tx_id},
        {"$set": {
            "status": "processing",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user["id"]
        }}
    )
    
    return {"message": "Transaction approved and set to processing"}

@admin_router.post("/licensee-transactions/{tx_id}/complete")
async def complete_transaction(
    tx_id: str,
    screenshot: Optional[UploadFile] = File(None),
    user: dict = Depends(require_admin)
):
    """Mark transaction as completed with optional screenshot (Master Admin only)"""
    if user["role"] != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can complete transactions")
    
    tx = await db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Handle screenshot upload
    screenshot_url = None
    if screenshot:
        try:
            contents = await screenshot.read()
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="licensee_transactions",
                resource_type="auto"
            )
            screenshot_url = upload_result.get("secure_url")
        except Exception as e:
            logging.error(f"Failed to upload screenshot: {e}")
    
    update_data = {
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "completed_by": user["id"]
    }
    
    if screenshot_url:
        update_data["completion_screenshot_url"] = screenshot_url
    
    await db.licensee_transactions.update_one({"id": tx_id}, {"$set": update_data})
    
    # Get licensee info and their active license
    licensee = await db.users.find_one({"id": tx["user_id"]}, {"_id": 0})
    license = await db.licenses.find_one({"user_id": tx["user_id"], "is_active": True}, {"_id": 0})
    
    # If deposit and approved, add to user balance AND Master Admin balance  
    if tx["type"] == "deposit" and licensee and license:
        deposit_amount = abs(tx.get("final_amount", tx["amount"]))
        current_balance = license.get("current_amount", license.get("starting_amount", 0))
        new_balance = current_balance + deposit_amount
        
        # Update license current_amount
        await db.licenses.update_one(
            {"id": license["id"]},
            {"$set": {"current_amount": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Update user's account_value
        await db.users.update_one(
            {"id": tx["user_id"]},
            {"$set": {"account_value": new_balance}}
        )
        
        # Record the deposit for tracking
        deposit_record = {
            "id": str(uuid.uuid4()),
            "user_id": tx["user_id"],
            "amount": deposit_amount,
            "type": "deposit",
            "notes": f"Licensee deposit - Transaction #{tx_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.deposits.insert_one(deposit_record)
        
        # Also add to Master Admin's balance (since licensee funds are tied to master admin)
        master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0})
        if master_admin:
            master_deposit_record = {
                "id": str(uuid.uuid4()),
                "user_id": master_admin["id"],
                "amount": deposit_amount,
                "type": "deposit",
                "notes": f"Licensee ({licensee.get('full_name', 'Unknown')}) deposit - Transaction #{tx_id[:8]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "related_licensee_id": tx["user_id"],
                "related_transaction_id": tx_id
            }
            await db.deposits.insert_one(master_deposit_record)
    
    # If withdrawal completed, deduct from Master Admin's balance
    # (Licensee balance was already deducted when withdrawal was submitted)
    elif tx["type"] == "withdrawal" and licensee:
        # Record the withdrawal for tracking
        withdrawal_record = {
            "id": str(uuid.uuid4()),
            "user_id": tx["user_id"],
            "amount": -abs(tx["amount"]),
            "type": "withdrawal",
            "notes": f"Licensee withdrawal - Transaction #{tx_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.deposits.insert_one(withdrawal_record)
        
        # Also deduct from Master Admin's balance (since licensee funds are tied to master admin)
        master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0})
        if master_admin:
            master_withdrawal_record = {
                "id": str(uuid.uuid4()),
                "user_id": master_admin["id"],
                "amount": -abs(tx["amount"]),
                "type": "withdrawal",
                "notes": f"Licensee ({licensee.get('full_name', 'Unknown')}) withdrawal - Transaction #{tx_id[:8]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "related_licensee_id": tx["user_id"],
                "related_transaction_id": tx_id
            }
            await db.deposits.insert_one(master_withdrawal_record)
    
    return {"message": "Transaction completed successfully"}

@admin_router.put("/licensee-transactions/{tx_id}")
async def update_licensee_transaction(
    tx_id: str,
    amount: float = Body(..., embed=False),
    notes: Optional[str] = Body(None, embed=False),
    user: dict = Depends(require_admin)
):
    """Update a licensee transaction amount (Master Admin only)"""
    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can update transactions")
    
    tx = await db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    old_amount = tx.get("amount", 0)
    
    # Update the transaction
    update_data = {
        "$set": {
            "amount": amount,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "correction_notes": notes or f"Amount corrected from ${old_amount} to ${amount}",
            "corrected_by": user["id"]
        }
    }
    
    await db.licensee_transactions.update_one({"id": tx_id}, update_data)
    
    # If transaction was completed, we need to update the related deposit/withdrawal records
    if tx.get("status") == "completed":
        # Update corresponding deposit or withdrawal record
        if tx["type"] == "deposit":
            await db.deposits.update_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}},
                {"$set": {"amount": amount}}
            )
        else:
            await db.withdrawals.update_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}},
                {"$set": {"amount": amount}}
            )
    
    return {"message": "Transaction updated successfully", "old_amount": old_amount, "new_amount": amount}

@admin_router.delete("/licensee-transactions/{tx_id}")
async def delete_licensee_transaction(tx_id: str, user: dict = Depends(require_admin)):
    """Delete a licensee transaction (Master Admin only)"""
    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Only Master Admin can delete transactions")
    
    tx = await db.licensee_transactions.find_one({"id": tx_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Delete the transaction
    await db.licensee_transactions.delete_one({"id": tx_id})
    
    # If transaction was completed, we need to delete the related deposit/withdrawal records
    if tx.get("status") == "completed":
        if tx["type"] == "deposit":
            await db.deposits.delete_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}}
            )
        else:
            await db.withdrawals.delete_many(
                {"user_id": tx["user_id"], "notes": {"$regex": f"Transaction #{tx_id[:8]}"}}
            )
    
    return {"message": "Transaction deleted successfully"}

# Licensee endpoints (for licensed users)
@profit_router.post("/licensee/deposit")
async def create_licensee_deposit(
    amount: float = Form(...),
    deposit_date: str = Form(...),
    notes: Optional[str] = Form(None),
    screenshot: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Submit a deposit request (Licensees only)"""
    # Check if user is a licensee
    license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensed users can use this feature")
    
    # Upload screenshot
    screenshot_url = None
    try:
        contents = await screenshot.read()
        upload_result = cloudinary.uploader.upload(
            contents,
            folder="licensee_deposits",
            resource_type="auto"
        )
        screenshot_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload screenshot: {str(e)}")
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "type": "deposit",
        "amount": amount,
        "deposit_date": deposit_date,
        "notes": notes,
        "screenshot_url": screenshot_url,
        "status": "pending",
        "feedback": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.licensee_transactions.insert_one(transaction)
    
    # Notify master admin
    admins = await db.users.find({"role": "master_admin"}, {"_id": 0, "id": 1}).to_list(100)
    for admin in admins:
        notification = {
            "id": str(uuid.uuid4()),
            "type": "licensee_deposit",
            "title": "New Licensee Deposit Request",
            "message": f"{user.get('full_name', 'A licensee')} submitted a deposit request for ${amount:,.2f}",
            "user_id": admin["id"],
            "from_user_id": user["id"],
            "transaction_id": transaction["id"],
            "amount": amount,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
    
    return {"message": "Deposit request submitted successfully", "transaction_id": transaction["id"]}

@profit_router.post("/licensee/withdrawal")
async def create_licensee_withdrawal(
    amount: float = Form(...),
    notes: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Submit a withdrawal request (Licensees only) - 5 business days processing
    
    IMPORTANT: Withdrawal amount is IMMEDIATELY deducted from the licensee's balance.
    """
    # Check if user is a licensee
    license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensed users can use this feature")
    
    # Check if user has sufficient balance using the license's current_amount
    current_balance = license.get("current_amount", license.get("starting_amount", 0))
    
    if amount > current_balance:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Current balance: ${current_balance:,.2f}")
    
    # Calculate fees
    fees = calculate_withdrawal_fees(amount)
    net_amount = fees["net_amount"]
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "type": "withdrawal",
        "amount": amount,
        "gross_amount": amount,
        "merin_fee": fees["merin_fee"],
        "binance_fee": fees["binance_fee"],
        "total_fees": fees["total_fees"],
        "net_amount": net_amount,
        "notes": notes,
        "status": "pending",
        "processing_days": 5,  # 5 business days for licensees
        "feedback": [],
        "balance_before": current_balance,
        "balance_after": current_balance - amount,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.licensee_transactions.insert_one(transaction)
    
    # IMMEDIATELY deduct from licensee's balance
    new_balance = current_balance - amount
    await db.licenses.update_one(
        {"id": license["id"]},
        {"$set": {"current_amount": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Also update user's account_value
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"account_value": new_balance}}
    )
    
    # Notify master admin
    admins = await db.users.find({"role": "master_admin"}, {"_id": 0, "id": 1}).to_list(100)
    for admin in admins:
        notification = {
            "id": str(uuid.uuid4()),
            "type": "licensee_withdrawal",
            "title": "New Licensee Withdrawal Request",
            "message": f"{user.get('full_name', 'A licensee')} requested a withdrawal of ${amount:,.2f}",
            "user_id": admin["id"],
            "from_user_id": user["id"],
            "transaction_id": transaction["id"],
            "amount": amount,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
    
    return {
        "message": "Withdrawal request submitted successfully. Processing time: 5 business days.",
        "transaction_id": transaction["id"],
        "processing_days": 5
    }

@profit_router.get("/licensee/transactions")
async def get_my_licensee_transactions(user: dict = Depends(get_current_user)):
    """Get current user's licensee transactions"""
    # Check if user is a licensee
    license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        return {"transactions": [], "is_licensee": False}
    
    transactions = await db.licensee_transactions.find(
        {"user_id": user["id"]}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"transactions": transactions, "is_licensee": True, "license": license}

@profit_router.post("/licensee/transactions/{tx_id}/confirm")
async def confirm_licensee_transaction(tx_id: str, user: dict = Depends(get_current_user)):
    """Licensee confirms the transaction after seeing admin's calculations"""
    tx = await db.licensee_transactions.find_one({"id": tx_id, "user_id": user["id"]}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx["status"] != "awaiting_confirmation":
        raise HTTPException(status_code=400, detail="Transaction is not awaiting confirmation")
    
    await db.licensee_transactions.update_one(
        {"id": tx_id},
        {"$set": {
            "status": "processing",
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify master admin
    admins = await db.users.find({"role": "master_admin"}, {"_id": 0, "id": 1}).to_list(100)
    for admin in admins:
        notification = {
            "id": str(uuid.uuid4()),
            "type": "licensee_confirmation",
            "title": "Licensee Confirmed Transaction",
            "message": f"{user.get('full_name', 'A licensee')} confirmed their {tx['type']} request",
            "user_id": admin["id"],
            "from_user_id": user["id"],
            "transaction_id": tx_id,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
    
    return {"message": "Transaction confirmed. Admin will process your request."}

@profit_router.get("/licensee/welcome-info")
async def get_licensee_welcome_info(user: dict = Depends(get_current_user)):
    """Get licensee welcome info for first login screen"""
    # Check if user is a licensee
    license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        return {"is_licensee": False, "has_seen_welcome": True}
    
    # Check if user has seen welcome
    has_seen = user.get("has_seen_welcome", False)
    
    # Get master admin info
    master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0, "full_name": 1})
    master_admin_name = master_admin.get("full_name", "Master Admin") if master_admin else "Master Admin"
    
    return {
        "is_licensee": True,
        "has_seen_welcome": has_seen,
        "licensee_name": user.get("full_name", "Licensee"),
        "starting_balance": license.get("starting_amount", 0),
        "current_balance": license.get("current_amount", license.get("starting_amount", 0)),
        "effective_start_date": license.get("effective_start_date", license.get("start_date")),
        "license_type": license.get("license_type"),
        "master_admin_name": master_admin_name
    }

@profit_router.post("/licensee/mark-welcome-seen")
async def mark_licensee_welcome_seen(user: dict = Depends(get_current_user)):
    """Mark that licensee has seen the welcome screen"""
    # Verify user is a licensee
    license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensees can access this endpoint")
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"has_seen_welcome": True}}
    )
    
    return {"message": "Welcome screen marked as seen"}

@profit_router.get("/licensee/daily-projection")
async def get_licensee_daily_projection(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get daily projection table for licensees (with Manager Traded column)"""
    # Check if user is a licensee
    license = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    if not license:
        raise HTTPException(status_code=403, detail="Only licensees can access this endpoint")
    
    # Get effective start date from license
    effective_start = license.get("effective_start_date", license.get("start_date"))
    
    # Get master admin's trade logs to determine "Manager Traded" status
    master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0, "id": 1})
    master_admin_id = master_admin["id"] if master_admin else None
    
    # Get all master admin trades
    master_trades = []
    if master_admin_id:
        master_trades = await db.trade_logs.find(
            {"user_id": master_admin_id},
            {"_id": 0, "trade_date": 1, "created_at": 1}
        ).to_list(10000)
    
    # Create a set of dates when master admin traded
    traded_dates = set()
    for trade in master_trades:
        trade_date = trade.get("trade_date")
        if not trade_date and trade.get("created_at"):
            # Extract date from created_at
            trade_date = trade["created_at"][:10]
        if trade_date:
            traded_dates.add(trade_date)
    
    # Get licensee deposits (for adding to their account)
    licensee_deposits = await db.licensee_transactions.find(
        {"user_id": user["id"], "type": "deposit", "status": "completed"},
        {"_id": 0}
    ).to_list(1000)
    
    # Map deposits by date
    deposit_by_date = {}
    for dep in licensee_deposits:
        dep_date = dep.get("completed_at", dep.get("created_at", ""))[:10]
        if dep_date:
            deposit_by_date[dep_date] = deposit_by_date.get(dep_date, 0) + dep.get("amount", 0)
    
    # Build projection table starting from effective_start_date
    projections = []
    current_balance = license.get("starting_amount", 0)
    
    # Parse start date
    try:
        start_dt = datetime.strptime(effective_start, "%Y-%m-%d")
    except:
        start_dt = datetime.now(timezone.utc)
    
    end_dt = datetime.now(timezone.utc)
    
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime("%Y-%m-%d")
        
        # Check if master admin traded this day
        manager_traded = date_str in traded_dates
        
        # Check for deposits on this date
        deposit_amount = deposit_by_date.get(date_str, 0)
        
        # Calculate projected profit based on manager traded status
        if manager_traded:
            # Use 0.5% daily profit (standard projection)
            projected_profit = round(current_balance * 0.005, 2)
        else:
            projected_profit = None  # Show "--" in frontend
        
        # Add deposit first
        if deposit_amount > 0:
            current_balance += deposit_amount
        
        projection = {
            "date": date_str,
            "day_of_week": current_dt.strftime("%A"),
            "starting_balance": round(current_balance, 2),
            "manager_traded": manager_traded,
            "projected_profit": projected_profit,
            "deposit": deposit_amount if deposit_amount > 0 else None
        }
        
        # Update balance for next day
        if manager_traded and projected_profit:
            current_balance += projected_profit
        
        projection["ending_balance"] = round(current_balance, 2)
        
        projections.append(projection)
        current_dt += timedelta(days=1)
    
    return {
        "projections": projections,
        "effective_start_date": effective_start,
        "starting_amount": license.get("starting_amount", 0),
        "current_balance": round(current_balance, 2)
    }

# ==================== EMAIL TEMPLATES ====================
@settings_router.get("/email-templates")
async def get_email_templates(user: dict = Depends(require_admin)):
    """Get all email templates"""
    if user["role"] not in ["master_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only Super Admin or Master Admin can manage email templates")
    
    templates = await db.email_templates.find({}, {"_id": 0}).to_list(100)
    
    # Default templates if none exist
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
    
    # Merge with defaults
    existing_types = {t["type"] for t in templates}
    for default in default_templates:
        if default["type"] not in existing_types:
            templates.append(default)
    
    return {"templates": templates}

@settings_router.put("/email-templates/{template_type}")
async def update_email_template(template_type: str, data: EmailTemplateUpdate, user: dict = Depends(require_admin)):
    """Update an email template"""
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

class TestEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    template_type: str = "test"

@settings_router.post("/email-templates/test")
async def send_test_email(data: TestEmailRequest, user: dict = Depends(require_admin)):
    """Send a test email with the provided template content"""
    from services.email_service import send_email
    
    try:
        # Send the email
        result = await send_email(
            to=data.to,
            subject=f"[TEST] {data.subject}",
            body=data.body
        )
        
        # Log to email history
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
        # Log failed attempt
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
@settings_router.post("/test-emailit")
async def test_emailit_connection(user: dict = Depends(require_admin)):
    """Test Emailit API connection by validating the key format"""
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    emailit_key = settings.get("emailit_api_key") if settings else None
    
    if not emailit_key:
        emailit_key = os.environ.get("EMAILIT_API_KEY")
    
    if not emailit_key:
        return {"success": False, "message": "Emailit API key not configured"}
    
    # Validate key format (should start with 'em_')
    if not emailit_key.startswith("em_"):
        return {"success": False, "message": "Invalid Emailit API key format. Key should start with 'em_'"}
    
    try:
        # Test by sending a minimal validation request
        # Emailit doesn't have an /account endpoint, so we validate the key format
        # and check if the API accepts the authorization header
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
            
            # 401 = invalid key, 422 = valid key but invalid sender (expected)
            # 200/201 = email sent (shouldn't happen with test@test.com)
            if response.status_code == 401:
                return {"success": False, "message": "Invalid API key - authentication failed"}
            elif response.status_code in [200, 201, 202]:
                return {"success": True, "message": "Emailit API key is valid and working!"}
            elif response.status_code == 422:
                # This is actually good - means key is valid but sender not verified
                return {"success": True, "message": "Emailit API key is valid! Note: You may need to verify your sender domain."}
            elif response.status_code == 400:
                # Bad request but key accepted
                return {"success": True, "message": "Emailit API key is valid! Configure a verified sender domain to send emails."}
            else:
                return {"success": False, "message": f"Emailit returned status {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}

@settings_router.post("/test-cloudinary")
async def test_cloudinary_connection(user: dict = Depends(require_admin)):
    """Test Cloudinary API connection"""
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    
    cloud_name = settings.get("cloudinary_cloud_name") if settings else None
    api_key = settings.get("cloudinary_api_key") if settings else None
    api_secret = settings.get("cloudinary_api_secret") if settings else None
    
    if not all([cloud_name, api_key, api_secret]):
        return {"success": False, "message": "Cloudinary credentials not fully configured"}
    
    try:
        # Test by pinging Cloudinary API
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

@settings_router.post("/test-heartbeat")
async def test_heartbeat_connection(user: dict = Depends(require_admin)):
    """Test Heartbeat API connection"""
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    heartbeat_key = settings.get("heartbeat_api_key") if settings else None
    
    if not heartbeat_key:
        heartbeat_key = os.environ.get("HEARTBEAT_API_KEY")
    
    if not heartbeat_key:
        return {"success": False, "message": "Heartbeat API key not configured"}
    
    # Validate key format (should start with 'hb:')
    if not heartbeat_key.startswith("hb:"):
        return {"success": False, "message": "Invalid Heartbeat API key format. Key should start with 'hb:'"}
    
    try:
        # Test Heartbeat connection using the /users endpoint
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

@settings_router.get("/email-history")
async def get_email_history(
    page: int = 1, 
    page_size: int = 20,
    user: dict = Depends(require_admin)
):
    """Get paginated email history (admin only)"""
    skip = (page - 1) * page_size
    
    # Get total count
    total = await db.email_history.count_documents({})
    
    # Get paginated emails
    emails = await db.email_history.find(
        {}, 
        {"_id": 0}
    ).sort("sent_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    return {
        "emails": emails,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    }

@settings_router.delete("/email-history")
async def clear_email_history(user: dict = Depends(require_master_admin)):
    """Clear all email history (master admin only)"""
    result = await db.email_history.delete_many({})
    return {"message": f"Cleared {result.deleted_count} email records"}

# User endpoint to get their own license projections
@profit_router.get("/license-projections")
async def get_my_license_projections(user: dict = Depends(get_current_user)):
    """Get license projections for the current user (if they have an extended license)"""
    license_doc = await db.licenses.find_one({"user_id": user["id"], "is_active": True}, {"_id": 0})
    
    if not license_doc:
        return {"has_license": False, "message": "No active license found"}
    
    if license_doc["license_type"] != "extended":
        return {
            "has_license": True,
            "license_type": license_doc["license_type"],
            "message": "Honorary licenses use standard calculations"
        }
    
    # Calculate projections for extended license
    start_date = datetime.fromisoformat(license_doc["start_date"].replace("Z", "+00:00"))
    projections = calculate_extended_license_projections(
        license_doc["starting_amount"],
        start_date,
        365
    )
    
    # Get current values
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")
    current_projection = next((p for p in projections if p["date"] == today_str), None)
    
    # Get this month's projections
    current_month = today.strftime("%Y-%m")
    monthly_projections = [p for p in projections if p["date"].startswith(current_month)]
    
    return {
        "has_license": True,
        "license_type": "extended",
        "starting_amount": license_doc["starting_amount"],
        "start_date": license_doc["start_date"],
        "current_values": current_projection or (projections[-1] if projections else None),
        "monthly_projections": monthly_projections,
        "quarterly_summary": get_quarterly_summary(projections)
    }

def get_quarterly_summary(projections: List[Dict]) -> List[Dict]:
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


@profit_router.get("/master-admin-trades")
async def get_master_admin_trades(
    start_date: str = None,
    end_date: str = None,
    user: dict = Depends(get_current_user)
):
    """
    Get master admin's trading status for each day in the date range.
    Used by extended licensees to determine if profit was credited.
    """
    # Only licensees can access this endpoint
    if not user.get("license_type"):
        raise HTTPException(status_code=403, detail="This endpoint is for licensees only")
    
    # Get the master admin
    master_admin = await db.users.find_one({"role": "master_admin"}, {"_id": 0})
    if not master_admin:
        return {"trades": [], "message": "No master admin found"}
    
    # Build date query
    query = {"user_id": master_admin["id"]}
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
        query["created_at"] = {"$gte": start_dt.isoformat()}
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        if "created_at" in query:
            query["created_at"]["$lte"] = end_dt.isoformat()
        else:
            query["created_at"] = {"$lte": end_dt.isoformat()}
    
    # Get master admin's trades
    trades = await db.trade_logs.find(query, {"_id": 0}).to_list(1000)
    
    # Create a dictionary of dates with trades
    trading_dates = {}
    for trade in trades:
        trade_date = trade.get("created_at", "")
        if isinstance(trade_date, str):
            date_key = trade_date[:10]  # Get YYYY-MM-DD
        else:
            date_key = trade_date.strftime("%Y-%m-%d")
        
        trading_dates[date_key] = {
            "traded": True,
            "actual_profit": trade.get("actual_profit", 0),
            "projected_profit": trade.get("projected_profit", 0)
        }
    
    return {
        "trading_dates": trading_dates,
        "total_trades": len(trades)
    }


# Onboarding Models
class OnboardingTransaction(BaseModel):
    type: str  # 'deposit' or 'withdrawal'
    amount: float
    date: str  # ISO date string

class OnboardingTradeEntry(BaseModel):
    date: str  # YYYY-MM-DD
    actual_profit: Optional[float] = None
    missed: bool = False
    balance: Optional[float] = None  # User-entered balance (source of truth for lot_size)
    product: Optional[str] = 'MOIL10'
    direction: Optional[str] = 'BUY'
    commission: Optional[float] = 0  # Daily commission from referrals

class OnboardingData(BaseModel):
    user_type: str  # 'new' or 'experienced'
    starting_balance: float
    start_date: Optional[str] = None  # ISO date string for experienced traders
    transactions: Optional[List[OnboardingTransaction]] = []
    trade_entries: Optional[List[OnboardingTradeEntry]] = []
    total_commission: Optional[float] = 0  # Total commission to be added at the end

@profit_router.post("/complete-onboarding")
async def complete_onboarding(data: OnboardingData, user: dict = Depends(get_current_user)):
    """
    Complete the onboarding process for new or experienced traders.
    Creates initial deposits, withdrawals, and trade logs based on user input.
    """
    try:
        # Track which deposits and trades we create
        created_deposits = []
        created_trades = []
        
        # 1. Create the initial deposit (starting balance)
        initial_deposit_id = str(uuid.uuid4())
        start_date = data.start_date if data.start_date else datetime.now(timezone.utc).isoformat()
        
        # Parse start date for ordering
        if isinstance(start_date, str):
            if 'T' in start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            else:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            start_dt = start_date
        
        initial_deposit = {
            "id": initial_deposit_id,
            "user_id": user["id"],
            "amount": data.starting_balance,
            "product": "MOIL10",
            "currency": "USDT",
            "notes": f"Initial balance - Onboarding ({data.user_type} trader)",
            "type": "initial",
            "created_at": start_dt.isoformat()
        }
        await db.deposits.insert_one(initial_deposit)
        created_deposits.append(initial_deposit_id)
        
        # 2. Create additional deposits/withdrawals for experienced traders
        if data.user_type == 'experienced' and data.transactions:
            for tx in data.transactions:
                tx_id = str(uuid.uuid4())
                tx_date = datetime.fromisoformat(tx.date.replace('Z', '+00:00')) if 'T' in tx.date else datetime.strptime(tx.date[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
                deposit_entry = {
                    "id": tx_id,
                    "user_id": user["id"],
                    "amount": tx.amount if tx.type == 'deposit' else -tx.amount,
                    "product": "MOIL10",
                    "currency": "USDT",
                    "type": tx.type,
                    "notes": f"Onboarding {tx.type}",
                    "is_withdrawal": tx.type == 'withdrawal',
                    "created_at": tx_date.isoformat()
                }
                await db.deposits.insert_one(deposit_entry)
                created_deposits.append(tx_id)
        
        # 3. Create trade logs for experienced traders
        if data.user_type == 'experienced' and data.trade_entries:
            # Calculate running balance for each trade
            running_balance = data.starting_balance
            
            # Add initial transactions to running balance calculation
            tx_by_date = {}
            if data.transactions:
                for tx in data.transactions:
                    tx_date_key = tx.date[:10]
                    if tx_date_key not in tx_by_date:
                        tx_by_date[tx_date_key] = 0
                    tx_by_date[tx_date_key] += tx.amount if tx.type == 'deposit' else -tx.amount
            
            # Sort trade entries by date
            sorted_entries = sorted(data.trade_entries, key=lambda e: e.date)
            
            for entry in sorted_entries:
                if entry.missed:
                    continue  # Skip missed days
                
                # Apply any transactions for this date BEFORE calculating lot size
                if entry.date in tx_by_date:
                    running_balance += tx_by_date[entry.date]
                
                # Use user-entered balance if provided, otherwise use running balance
                # This ensures Trade History matches Daily Projection when users enter custom balances
                effective_balance = entry.balance if entry.balance else running_balance
                
                # Calculate lot size and projected profit from effective balance
                lot_size = round(effective_balance / 980, 2)
                projected_profit = round(lot_size * 15, 2)
                actual_profit = entry.actual_profit or 0
                commission = entry.commission or 0  # Daily commission from referrals
                profit_difference = round(actual_profit - projected_profit, 2)
                
                # Determine performance
                if actual_profit >= projected_profit:
                    performance = "exceeded" if actual_profit > projected_profit else "perfect"
                elif actual_profit > 0:
                    performance = "below"
                else:
                    performance = "below"
                
                # Create trade log
                trade_id = str(uuid.uuid4())
                trade_date = datetime.strptime(entry.date, "%Y-%m-%d").replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)
                
                # Get product and direction from entry or use defaults
                product = getattr(entry, 'product', 'MOIL10') or 'MOIL10'
                direction = getattr(entry, 'direction', 'BUY') or 'BUY'
                
                trade_log = {
                    "id": trade_id,
                    "user_id": user["id"],
                    "lot_size": lot_size,
                    "direction": direction,
                    "product": product,
                    "projected_profit": projected_profit,
                    "actual_profit": actual_profit,
                    "commission": commission,  # Daily commission from referrals
                    "profit_difference": profit_difference,
                    "performance": performance,
                    "signal_id": None,
                    "notes": "Imported via onboarding",
                    "is_retroactive": True,
                    "is_onboarding_import": True,
                    "created_at": trade_date.isoformat()
                }
                await db.trade_logs.insert_one(trade_log)
                created_trades.append(trade_id)
                
                # Update running balance for next iteration (Balance + Profit + Commission)
                running_balance += actual_profit + commission
        
        # 4. If total_commission is provided (from final step), assign it to the LAST trade entry
        # This ensures it appears in the Daily Projection Commission column for the last trading day
        if data.total_commission and data.total_commission > 0 and created_trades:
            # Get the last trade log ID and update its commission field
            last_trade_id = created_trades[-1]
            
            # Update the last trade log with the total commission
            await db.trade_logs.update_one(
                {"id": last_trade_id},
                {"$inc": {"commission": data.total_commission}}  # Add to any existing commission
            )
            
            logger.info(f"Assigned total commission ${data.total_commission} to last trade {last_trade_id}")
        
        # 5. Update user's onboarding status
        await db.users.update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "onboarding_completed": True,
                    "trading_type": data.user_type,
                    "trading_start_date": data.start_date,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # 6. Create notification for admins about tracker reset (if experienced trader resetting)
        if data.user_type == 'experienced':
            await create_admin_notification(
                notification_type="tracker_reset",
                title="Tracker Reset",
                message=f"{user['full_name']} reset their tracker as experienced trader",
                user_id=user["id"],
                user_name=user["full_name"],
                amount=data.starting_balance,
                metadata={
                    "user_type": data.user_type,
                    "start_date": data.start_date,
                    "deposits_created": len(created_deposits),
                    "trades_created": len(created_trades)
                }
            )
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "deposits_created": len(created_deposits),
            "trades_created": len(created_trades),
            "starting_balance": data.starting_balance,
            "user_type": data.user_type,
            "total_commission": data.total_commission or 0
        }
        
    except Exception as e:
        logger.error(f"Onboarding failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

@profit_router.get("/onboarding-status")
async def get_onboarding_status(user: dict = Depends(get_current_user)):
    """Check if user has completed onboarding and their trading type"""
    return {
        "onboarding_completed": user.get("onboarding_completed", False),
        "trading_type": user.get("trading_type"),  # 'new' or 'experienced'
        "trading_start_date": user.get("trading_start_date"),
        "has_deposits": bool(await db.deposits.find_one({"user_id": user["id"]})),
        "has_trades": bool(await db.trade_logs.find_one({"user_id": user["id"]}))
    }



class SendEmailRequest(BaseModel):
    subject: str
    body: str

@admin_router.post("/members/{user_id}/send-email")
async def send_email_to_member(user_id: str, data: SendEmailRequest, user: dict = Depends(require_admin)):
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Use the email service with verified sender
    from services.email_service import send_email as send_email_service
    
    result = await send_email_service(
        db=db,
        to_email=member["email"],
        subject=data.subject,
        html_content=data.body,
        template_type="admin_reminder",
        metadata={"sent_by": user["id"], "sent_to": user_id}
    )
    
    if result.get("success"):
        return {"message": "Email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Email sending failed"))

# Email Templates CRUD (Master Admin only)
class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body: str
    category: Optional[str] = "general"
    is_html: bool = False

class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    is_html: Optional[bool] = None

@admin_router.get("/email-templates")
async def get_email_templates(user: dict = Depends(require_admin)):
    """Get all email templates"""
    templates = await db.email_templates.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"templates": templates}

@admin_router.get("/email-templates/{template_id}")
async def get_email_template(template_id: str, user: dict = Depends(require_admin)):
    """Get a specific email template"""
    template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@admin_router.post("/email-templates")
async def create_email_template(data: EmailTemplateCreate, user: dict = Depends(require_master_admin)):
    """Create a new email template (Master Admin only)"""
    template = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "subject": data.subject,
        "body": data.body,
        "category": data.category,
        "is_html": data.is_html,
        "created_by": user["id"],
        "created_by_name": user.get("full_name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.email_templates.insert_one(template)
    del template["_id"] if "_id" in template else None
    return template

@admin_router.put("/email-templates/{template_id}")
async def update_email_template(template_id: str, data: EmailTemplateUpdate, user: dict = Depends(require_master_admin)):
    """Update an email template (Master Admin only)"""
    template = await db.email_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.name is not None:
        update_data["name"] = data.name
    if data.subject is not None:
        update_data["subject"] = data.subject
    if data.body is not None:
        update_data["body"] = data.body
    if data.category is not None:
        update_data["category"] = data.category
    if data.is_html is not None:
        update_data["is_html"] = data.is_html
    
    await db.email_templates.update_one({"id": template_id}, {"$set": update_data})
    
    updated = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
    return updated

@admin_router.delete("/email-templates/{template_id}")
async def delete_email_template(template_id: str, user: dict = Depends(require_master_admin)):
    """Delete an email template (Master Admin only)"""
    result = await db.email_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}

class NotifyRequest(BaseModel):
    title: str
    message: str

@admin_router.post("/members/{user_id}/notify")
async def notify_member(user_id: str, data: NotifyRequest, user: dict = Depends(require_admin)):
    """Send an in-app notification to a member"""
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create in-app notification
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "admin_reminder",
        "title": data.title,
        "message": data.message,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_by": user["id"]
    }
    
    await db.notifications.insert_one(notification)
    
    # Also send email as backup
    from services.email_service import send_email as send_email_service
    
    await send_email_service(
        db=db,
        to_email=member["email"],
        subject=data.title,
        html_content=f"<p>{data.message}</p>",
        template_type="admin_reminder",
        metadata={"sent_by": user["id"], "sent_to": user_id}
    )
    
    return {"message": "Notification sent successfully"}

@admin_router.post("/upgrade-role")
async def upgrade_role(data: RoleUpgrade, user: dict = Depends(require_admin)):
    """Upgrade a user's role. Master Admin can promote to any role without secret code."""
    target_user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate role
    valid_roles = ["basic_admin", "admin", "super_admin"]
    if data.new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    
    # Master Admin can promote to any role without secret code
    if user["role"] == "master_admin":
        pass  # No restrictions for master admin
    elif data.new_role == "super_admin":
        # Non-master admins need secret code for super_admin promotion
        if data.secret_code != SUPER_ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret code")
        if user["role"] not in ["super_admin", "master_admin"]:
            raise HTTPException(status_code=403, detail="Only super admin or master admin can create super admins")
    elif data.new_role == "basic_admin" or data.new_role == "admin":
        # Super admins can create basic admins
        if user["role"] not in ["super_admin", "master_admin"]:
            raise HTTPException(status_code=403, detail="Only super admin or master admin can create admins")
    
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {"role": data.new_role, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": f"User upgraded to {data.new_role}"}

@admin_router.post("/downgrade-role/{user_id}")
async def downgrade_role(user_id: str, user: dict = Depends(require_super_admin)):
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot downgrade yourself")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": "member", "updated_at": datetime.now(timezone.utc).isoformat()}}  # Changed from "user" to "member"
    )
    return {"message": "User downgraded to member"}

@admin_router.post("/deactivate/{user_id}")
async def deactivate_user(user_id: str, user: dict = Depends(require_admin)):
    """Deactivate a user - they cannot login until reactivated"""
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check role hierarchy - can't deactivate higher or equal roles
    role_hierarchy = {'super_admin': 4, 'master_admin': 3, 'admin': 2, 'member': 1}
    if role_hierarchy.get(target_user.get("role"), 0) >= role_hierarchy.get(user.get("role"), 0):
        raise HTTPException(status_code=403, detail="Cannot deactivate users with equal or higher role")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_deactivated": True, "deactivated_at": datetime.now(timezone.utc).isoformat(), "deactivated_by": user["id"]}}
    )
    return {"message": "User has been deactivated"}

@admin_router.post("/reactivate/{user_id}")
async def reactivate_user(user_id: str, user: dict = Depends(require_admin)):
    """Reactivate a deactivated user"""
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_deactivated": False}, "$unset": {"deactivated_at": "", "deactivated_by": ""}}
    )
    return {"message": "User has been reactivated"}

# ==================== DEBT MANAGEMENT ROUTES ====================

@debt_router.post("", response_model=DebtResponse)
async def create_debt(data: DebtCreate, user: dict = Depends(get_current_user)):
    debt_id = str(uuid.uuid4())
    debt = {
        "id": debt_id,
        "user_id": user["id"],
        "name": data.name,
        "total_amount": data.total_amount,
        "remaining_amount": data.total_amount,
        "minimum_payment": data.minimum_payment,
        "due_day": data.due_day,
        "interest_rate": data.interest_rate,
        "currency": data.currency,
        "payments": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.debts.insert_one(debt)
    return DebtResponse(**{**debt, "created_at": datetime.fromisoformat(debt["created_at"])})

@debt_router.get("", response_model=List[DebtResponse])
async def get_debts(user: dict = Depends(get_current_user)):
    debts = await db.debts.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return [DebtResponse(**{**d, "created_at": datetime.fromisoformat(d["created_at"]) if isinstance(d["created_at"], str) else d["created_at"]}) for d in debts]

@debt_router.post("/{debt_id}/payment")
async def make_debt_payment(debt_id: str, amount: float, user: dict = Depends(get_current_user)):
    debt = await db.debts.find_one({"id": debt_id, "user_id": user["id"]}, {"_id": 0})
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    
    new_remaining = max(0, debt["remaining_amount"] - amount)
    payment = {
        "id": str(uuid.uuid4()),
        "amount": amount,
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    await db.debts.update_one(
        {"id": debt_id},
        {
            "$set": {"remaining_amount": new_remaining},
            "$push": {"payments": payment}
        }
    )
    
    return {"message": "Payment recorded", "new_remaining": new_remaining}

@debt_router.get("/plan")
async def get_debt_repayment_plan(user: dict = Depends(get_current_user)):
    debts = await db.debts.find({"user_id": user["id"], "remaining_amount": {"$gt": 0}}, {"_id": 0}).to_list(100)
    
    # Calculate monthly commitment
    monthly_commitment = sum(d["minimum_payment"] for d in debts)
    
    # Get account summary
    deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    total_deposits = sum(d["amount"] for d in deposits)
    total_profit = sum(t["actual_profit"] for t in trades)
    account_value = total_deposits + total_profit
    
    # Calculate withdrawal timing
    upcoming_payments = []
    today = datetime.now(timezone.utc)
    
    for debt in debts:
        due_day = debt["due_day"]
        if today.day < due_day:
            next_due = today.replace(day=due_day)
        else:
            next_month = today.month + 1 if today.month < 12 else 1
            next_year = today.year if today.month < 12 else today.year + 1
            next_due = today.replace(year=next_year, month=next_month, day=due_day)
        
        days_until = (next_due - today).days
        
        upcoming_payments.append({
            "debt_name": debt["name"],
            "amount": debt["minimum_payment"],
            "due_date": next_due.isoformat(),
            "days_until": days_until,
            "withdrawal_deadline": (next_due - timedelta(days=2)).isoformat()  # 2 days for processing
        })
    
    return {
        "total_debt": sum(d["remaining_amount"] for d in debts),
        "monthly_commitment": monthly_commitment,
        "account_value": round(account_value, 2),
        "can_cover_this_month": account_value >= monthly_commitment,
        "upcoming_payments": sorted(upcoming_payments, key=lambda x: x["days_until"]),
        "debts_count": len(debts)
    }

# ==================== PROFIT PLANNER (GOALS) ROUTES ====================

@goals_router.post("", response_model=GoalResponse)
async def create_goal(data: GoalCreate, user: dict = Depends(get_current_user)):
    goal_id = str(uuid.uuid4())
    goal = {
        "id": goal_id,
        "user_id": user["id"],
        "name": data.name,
        "target_amount": data.target_amount,
        "current_amount": data.current_amount,
        "target_date": data.target_date.isoformat() if data.target_date else None,
        "price_type": data.price_type,
        "market_item": data.market_item,
        "currency": data.currency,
        "contributions": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.goals.insert_one(goal)
    
    progress = (data.current_amount / data.target_amount * 100) if data.target_amount > 0 else 0
    return GoalResponse(**{
        **goal, 
        "progress_percentage": round(progress, 2),
        "target_date": datetime.fromisoformat(goal["target_date"]) if goal["target_date"] else None,
        "created_at": datetime.fromisoformat(goal["created_at"])
    })

@goals_router.get("", response_model=List[GoalResponse])
async def get_goals(user: dict = Depends(get_current_user)):
    goals = await db.goals.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    result = []
    for g in goals:
        progress = (g["current_amount"] / g["target_amount"] * 100) if g["target_amount"] > 0 else 0
        result.append(GoalResponse(**{
            **g,
            "progress_percentage": round(progress, 2),
            "target_date": datetime.fromisoformat(g["target_date"]) if g.get("target_date") else None,
            "created_at": datetime.fromisoformat(g["created_at"]) if isinstance(g["created_at"], str) else g["created_at"]
        }))
    return result

@goals_router.post("/{goal_id}/contribute")
async def contribute_to_goal(goal_id: str, amount: float, user: dict = Depends(get_current_user)):
    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    new_amount = goal["current_amount"] + amount
    contribution = {
        "id": str(uuid.uuid4()),
        "amount": amount,
        "date": datetime.now(timezone.utc).isoformat()
    }
    
    await db.goals.update_one(
        {"id": goal_id},
        {
            "$set": {"current_amount": new_amount},
            "$push": {"contributions": contribution}
        }
    )
    
    progress = (new_amount / goal["target_amount"] * 100) if goal["target_amount"] > 0 else 0
    return {
        "message": "Contribution added",
        "new_amount": new_amount,
        "progress_percentage": round(progress, 2),
        "completed": new_amount >= goal["target_amount"]
    }

@goals_router.get("/{goal_id}/plan")
async def get_goal_plan(goal_id: str, user: dict = Depends(get_current_user)):
    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    remaining = goal["target_amount"] - goal["current_amount"]
    
    # Get account summary
    deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    total_deposits = sum(d["amount"] for d in deposits)
    total_profit = sum(t["actual_profit"] for t in trades)
    account_value = total_deposits + total_profit
    
    # Calculate suggestion
    suggestion = {}
    if account_value >= remaining:
        suggestion = {
            "type": "ready",
            "message": f"You have enough to reach your goal! Consider withdrawing ${remaining:.2f}"
        }
    else:
        needed = remaining - account_value
        suggestion = {
            "type": "need_more",
            "message": f"You need ${needed:.2f} more. Keep trading to reach your goal!",
            "trades_needed": int(needed / 15) + 1  # Assuming $15 profit per trade
        }
    
    return {
        "goal_name": goal["name"],
        "target": goal["target_amount"],
        "current": goal["current_amount"],
        "remaining": remaining,
        "account_value": round(account_value, 2),
        "suggestion": suggestion
    }

# ==================== CURRENCY ROUTES ====================

@currency_router.get("/rates")
async def get_exchange_rates(base: str = "USD"):
    try:
        api_key = os.environ.get('EXCHANGE_RATE_API_KEY', '')
        
        # For USDT base, use CoinGecko API (free, no key required for basic usage)
        if base.upper() == "USDT":
            return await get_usdt_rates()
        
        if not api_key:
            # Return mock rates for development
            return {
                "base": base,
                "rates": {"USD": 1, "PHP": 56.5, "USDT": 1, "EUR": 0.92, "GBP": 0.79},
                "source": "mock"
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}",
                timeout=10.0
            )
            data = response.json()
            return {
                "base": base,
                "rates": data.get("conversion_rates", {}),
                "source": "exchangerate-api"
            }
    except Exception as e:
        logger.error(f"Currency API error: {e}")
        return {
            "base": base,
            "rates": {"USD": 1, "PHP": 56.5, "USDT": 1},
            "source": "fallback"
        }

# Cache for USDT rates (to avoid rate limiting)
_usdt_rates_cache = {
    "data": None,
    "timestamp": None,
    "fetching": False  # Prevent concurrent API calls
}

async def get_usdt_rates():
    """Get USDT exchange rates from CoinGecko API with caching (15 min cache)"""
    global _usdt_rates_cache
    
    # Check cache (15 minute TTL - increased from 5 to reduce API calls)
    if _usdt_rates_cache["data"] and _usdt_rates_cache["timestamp"]:
        cache_age = (datetime.now(timezone.utc) - _usdt_rates_cache["timestamp"]).total_seconds()
        if cache_age < 900:  # 15 minutes
            return _usdt_rates_cache["data"]
    
    # If another request is already fetching, return cached data or wait briefly
    if _usdt_rates_cache["fetching"]:
        # Return cached data if available while another request fetches
        if _usdt_rates_cache["data"]:
            return _usdt_rates_cache["data"]
        # Wait a bit and try again with cache
        import asyncio
        await asyncio.sleep(0.5)
        if _usdt_rates_cache["data"]:
            return _usdt_rates_cache["data"]
    
    try:
        _usdt_rates_cache["fetching"] = True
        async with httpx.AsyncClient() as client:
            # CoinGecko API - get USDT price in multiple currencies
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "tether",
                    "vs_currencies": "usd,php,eur,gbp,jpy,cny,krw,sgd,hkd,aud,cad,inr,myr,thb,idr,vnd"
                },
                timeout=10.0,
                headers={
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 429:
                logger.warning("CoinGecko rate limited, using cache or fallback")
                if _usdt_rates_cache["data"]:
                    return _usdt_rates_cache["data"]
                raise Exception("Rate limited")
            
            data = response.json()
            
            if "tether" in data:
                tether_prices = data["tether"]
                # CoinGecko returns how much 1 USDT is worth in each currency
                rates = {currency.upper(): price for currency, price in tether_prices.items()}
                rates["USDT"] = 1  # 1 USDT = 1 USDT
                
                result = {
                    "base": "USDT",
                    "rates": rates,
                    "source": "coingecko",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Update cache
                _usdt_rates_cache["data"] = result
                _usdt_rates_cache["timestamp"] = datetime.now(timezone.utc)
                _usdt_rates_cache["fetching"] = False
                
                return result
            else:
                raise Exception("Invalid CoinGecko response")
                
    except Exception as e:
        _usdt_rates_cache["fetching"] = False
        logger.error(f"CoinGecko USDT API error: {e}")
        # Return cached data if available
        if _usdt_rates_cache["data"]:
            return _usdt_rates_cache["data"]
        
        # Fallback rates (approximate - updated periodically)
        fallback = {
            "base": "USDT",
            "rates": {
                "USD": 1.0,
                "PHP": 58.0,  # Updated PHP rate
                "EUR": 0.92,
                "GBP": 0.79,
                "JPY": 149.5,
                "CNY": 7.25,
                "KRW": 1350,
                "SGD": 1.35,
                "HKD": 7.82,
                "AUD": 1.55,
                "CAD": 1.36,
                "INR": 83.5,
                "MYR": 4.72,
                "THB": 35.8,
                "IDR": 15750,
                "VND": 24500,
                "USDT": 1
            },
            "source": "fallback"
        }
        return fallback

@currency_router.post("/convert")
async def convert_currency(amount: float, from_currency: str, to_currency: str):
    rates_data = await get_exchange_rates(from_currency)
    rates = rates_data.get("rates", {})
    
    if to_currency not in rates:
        raise HTTPException(status_code=400, detail=f"Currency {to_currency} not supported")
    
    converted = amount * rates[to_currency]
    return {
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
        "converted": round(converted, 2),
        "rate": rates[to_currency]
    }

# ==================== SETTINGS ROUTES ====================

@settings_router.get("/platform")
async def get_platform_settings():
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    if not settings:
        settings = PlatformSettings().model_dump()
    return settings

@settings_router.put("/platform")
async def update_platform_settings(data: PlatformSettings, user: dict = Depends(require_admin)):
    await db.platform_settings.update_one(
        {},
        {"$set": data.model_dump()},
        upsert=True
    )
    return {"message": "Settings updated"}

@settings_router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(require_admin)):
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

@settings_router.post("/upload-favicon")
async def upload_favicon(file: UploadFile = File(...), user: dict = Depends(require_admin)):
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

# ==================== API CENTER ROUTES ====================

@api_center_router.post("/connections", response_model=APIConnectionResponse)
async def create_api_connection(data: APIConnectionCreate, user: dict = Depends(require_admin)):
    conn_id = str(uuid.uuid4())
    connection = {
        "id": conn_id,
        "name": data.name,
        "endpoint_url": data.endpoint_url,
        "api_key": data.api_key,
        "headers": data.headers or {},
        "is_active": data.is_active,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": None
    }
    await db.api_connections.insert_one(connection)
    return APIConnectionResponse(**{**connection, "created_at": datetime.fromisoformat(connection["created_at"])})

@api_center_router.get("/connections", response_model=List[APIConnectionResponse])
async def get_api_connections(user: dict = Depends(require_admin)):
    connections = await db.api_connections.find({}, {"_id": 0, "api_key": 0}).to_list(100)
    return [APIConnectionResponse(**{
        **c, 
        "created_at": datetime.fromisoformat(c["created_at"]) if isinstance(c["created_at"], str) else c["created_at"],
        "last_used": datetime.fromisoformat(c["last_used"]) if c.get("last_used") else None
    }) for c in connections]

@api_center_router.post("/connections/{conn_id}/send")
async def send_to_connection(conn_id: str, payload: Dict[str, Any], user: dict = Depends(get_current_user)):
    connection = await db.api_connections.find_one({"id": conn_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if not connection.get("is_active"):
        raise HTTPException(status_code=400, detail="Connection is not active")
    
    try:
        headers = connection.get("headers", {})
        if connection.get("api_key"):
            headers["Authorization"] = f"Bearer {connection['api_key']}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                connection["endpoint_url"],
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            await db.api_connections.update_one(
                {"id": conn_id},
                {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
            )
            
            return {
                "status_code": response.status_code,
                "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@api_center_router.post("/receive")
async def receive_webhook(payload: Dict[str, Any]):
    """Endpoint to receive data from external apps"""
    webhook_id = str(uuid.uuid4())
    webhook_log = {
        "id": webhook_id,
        "payload": payload,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "processed": False
    }
    await db.webhook_logs.insert_one(webhook_log)
    
    # Process based on payload type
    action = payload.get("action")
    if action == "update_signal":
        # Allow external apps to update trading signal
        signal_data = payload.get("data", {})
        if signal_data:
            await db.trading_signals.update_many({}, {"$set": {"is_active": False}})
            signal_id = str(uuid.uuid4())
            signal = {
                "id": signal_id,
                "product": signal_data.get("product", "MOIL10"),
                "trade_time": signal_data.get("trade_time", "00:00"),
                "direction": signal_data.get("direction", "BUY"),
                "notes": signal_data.get("notes"),
                "is_active": True,
                "created_by": "webhook",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.trading_signals.insert_one(signal)
    
    return {"received": True, "webhook_id": webhook_id}

@api_center_router.delete("/connections/{conn_id}")
async def delete_api_connection(conn_id: str, user: dict = Depends(require_admin)):
    result = await db.api_connections.delete_one({"id": conn_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"message": "Connection deleted"}

# ==================== EMAIL ROUTES ====================

@api_router.post("/send-email")
async def send_simple_email(to: str, subject: str, body: str, user: dict = Depends(require_admin)):
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

# ==================== WEBSOCKET ROUTES ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    # Get user info from token in query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("sub") != user_id:
            await websocket.close(code=4003)
            return
        role = payload.get("role", "member")
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4002)
        return
    except jwt.InvalidTokenError:
        await websocket.close(code=4001)
        return
    
    await websocket_manager.connect(websocket, user_id, role)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id, role)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(websocket, user_id, role)

# Add a second WebSocket endpoint under /api/ for ingress routing
@app.websocket("/api/ws/{user_id}")
async def api_websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications (via /api/ route)"""
    # Get user info from token in query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("sub") != user_id:
            await websocket.close(code=4003)
            return
        role = payload.get("role", "member")
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4002)
        return
    except jwt.InvalidTokenError:
        await websocket.close(code=4001)
        return
    
    await websocket_manager.connect(websocket, user_id, role)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id, role)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(websocket, user_id, role)

@api_router.get("/ws/status")
async def get_websocket_status(user: dict = Depends(require_admin)):
    """Get WebSocket connection statistics (admin only)"""
    return websocket_manager.get_connection_count()


@api_router.get("/notifications")
async def get_notifications(
    limit: int = 50,
    skip: int = 0,
    unread_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """Get notifications for the current user (personal + community)"""
    is_admin = user.get("role") in ["basic_admin", "admin", "super_admin", "master_admin"]
    
    # Get personal notifications (targeted to this user)
    personal_query = {"recipient_id": user["id"]}
    if unread_only:
        personal_query["read"] = False
    
    personal_notifications = await db.notifications.find(
        personal_query,
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit // 2).to_list(limit // 2)
    
    # Get community/member notifications (visible to all)
    member_notifications = await db.member_notifications.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit // 2).to_list(limit // 2)
    
    # For admins, also get admin-only notifications
    admin_notifications = []
    if is_admin:
        admin_notifications = await db.admin_notifications.find(
            {},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit // 2).to_list(limit // 2)
    
    # Combine and sort all notifications
    all_notifications = []
    
    for n in personal_notifications:
        n["source"] = "personal"
        n["created_at"] = n.get("timestamp", n.get("created_at"))
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
    personal_unread = await db.notifications.count_documents({
        "recipient_id": user["id"],
        "read": False
    })
    
    admin_unread = 0
    if is_admin:
        admin_unread = await db.admin_notifications.count_documents({"is_read": False})
    
    return {
        "notifications": all_notifications,
        "unread_count": personal_unread + admin_unread,
        "is_admin": is_admin
    }

@api_router.post("/notifications/mark-read")
async def mark_notifications_read(user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the current user"""
    result = await db.notifications.update_many(
        {"recipient_id": user["id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"marked_read": result.modified_count}

@api_router.delete("/notifications")
async def clear_notifications(user: dict = Depends(get_current_user)):
    """Delete all notifications for the current user"""
    result = await db.notifications.delete_many({"recipient_id": user["id"]})
    return {"deleted": result.deleted_count}


# ==================== FILE UPLOAD ROUTES ====================

@api_router.post("/upload/profile-picture")
async def upload_profile_picture_endpoint(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
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
    
    result = await upload_profile_picture(db, user["id"], contents, file.filename, file.content_type)
    
    if result.get("success"):
        return {"message": "Profile picture uploaded", "url": result.get("url")}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))

@api_router.post("/upload/deposit-screenshot/{transaction_id}")
async def upload_deposit_screenshot_endpoint(
    transaction_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload a deposit screenshot for a transaction"""
    # Verify transaction belongs to user
    transaction = await db.licensee_transactions.find_one({"id": transaction_id, "user_id": user["id"]})
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
    
    result = await upload_deposit_screenshot(db, user["id"], transaction_id, contents, file.filename, file.content_type)
    
    if result.get("success"):
        return {"message": "Screenshot uploaded", "url": result.get("url")}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))

@api_router.post("/upload/general")
async def upload_general_file(
    file: UploadFile = File(...),
    folder: str = Form("uploads"),
    file_type: str = Form("general"),
    user: dict = Depends(get_current_user)
):
    """Upload a general file"""
    # Validate file size (max 20MB)
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 20MB")
    
    result = await upload_file(db, contents, file.filename, file.content_type, folder, user["id"], file_type)
    
    if result.get("success"):
        return {"message": "File uploaded", "url": result.get("url"), "public_id": result.get("public_id")}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))

# ==================== ENHANCED EMAIL ROUTES ====================

@api_router.post("/email/send-license-invite")
async def send_license_invite_email(
    invite_code: str,
    invitee_email: str,
    invitee_name: str = "",
    user: dict = Depends(require_master_admin)
):
    """Send a license invite email"""
    # Get invite details
    invite = await db.license_invites.find_one({"invite_code": invite_code})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    # Get production URL from settings
    settings = await db.platform_settings.find_one({}, {"_id": 0})
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
        db=db,
        to_email=invitee_email,
        subject=email_content["subject"],
        html_content=email_content["html"],
        text_content=email_content["text"]
    )
    
    if result.get("success"):
        # Update invite with email sent timestamp
        await db.license_invites.update_one(
            {"invite_code": invite_code},
            {"$set": {"email_sent_at": datetime.now(timezone.utc).isoformat(), "invitee_email": invitee_email}}
        )
        return {"message": "Invite email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send email"))

@api_router.post("/email/test")
async def test_email_service(
    to_email: str,
    user: dict = Depends(require_master_admin)
):
    """Send a test email to verify email service configuration"""
    result = await send_email(
        db=db,
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

# ==================== BETA VIRTUAL ENVIRONMENT (BVE) ====================

class BVESessionCreate(BaseModel):
    pass

class BVESessionExit(BaseModel):
    session_id: str

class BVERewind(BaseModel):
    session_id: str

class BVESignalCreate(BaseModel):
    product: str = "MOIL10"
    direction: str = "BUY"
    trade_time: str
    trade_timezone: str = "Asia/Manila"
    profit_multiplier: float = 15

async def require_super_or_master_admin(user: dict = Depends(get_current_user)):
    """Require super admin or master admin role for BVE access"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Beta Virtual Environment requires Super Admin or Master Admin access")
    return user

@bve_router.post("/enter")
async def enter_bve(user: dict = Depends(require_super_or_master_admin)):
    """Enter the Beta Virtual Environment - creates a snapshot and session"""
    session_id = str(uuid.uuid4())
    
    # Create snapshot of current state for this user
    # We'll snapshot: trading_signals, trade_logs (user's), and their account data
    
    # Get current active signal
    active_signal = await db.trading_signals.find_one(
        {"is_active": True},
        {"_id": 0}
    )
    
    # Get user's trade logs
    user_trade_logs = await db.trade_logs.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    # Get user's deposits
    user_deposits = await db.deposits.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    # Get user profile
    user_profile = await db.users.find_one(
        {"id": user["id"]},
        {"_id": 0, "password": 0}
    )
    
    # Store snapshot
    snapshot = {
        "id": session_id,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_data": {
            "active_signal": active_signal,
            "trade_logs": user_trade_logs,
            "deposits": user_deposits,
            "user_profile": user_profile
        }
    }
    
    await db.bve_sessions.insert_one(snapshot)
    
    # Initialize BVE collections with cloned data
    # Clone signals to bve_trading_signals
    if active_signal:
        bve_signal = {**active_signal, "bve_session_id": session_id}
        await db.bve_trading_signals.delete_many({"bve_session_id": session_id})
        await db.bve_trading_signals.insert_one(bve_signal)
    
    # Clone trade logs to bve_trade_logs
    await db.bve_trade_logs.delete_many({"bve_session_id": session_id})
    for log in user_trade_logs:
        bve_log = {**log, "bve_session_id": session_id}
        await db.bve_trade_logs.insert_one(bve_log)
    
    # Clone deposits to bve_deposits
    await db.bve_deposits.delete_many({"bve_session_id": session_id})
    for dep in user_deposits:
        bve_dep = {**dep, "bve_session_id": session_id}
        await db.bve_deposits.insert_one(bve_dep)
    
    return {
        "session_id": session_id,
        "message": "Entered Beta Virtual Environment",
        "snapshot": {
            "signals_count": 1 if active_signal else 0,
            "trade_logs_count": len(user_trade_logs),
            "deposits_count": len(user_deposits)
        }
    }

@bve_router.post("/exit")
async def exit_bve(data: BVESessionExit, user: dict = Depends(require_super_or_master_admin)):
    """Exit the Beta Virtual Environment - cleans up BVE data"""
    session_id = data.session_id
    
    # Clean up BVE collections for this session
    await db.bve_trading_signals.delete_many({"bve_session_id": session_id})
    await db.bve_trade_logs.delete_many({"bve_session_id": session_id})
    await db.bve_deposits.delete_many({"bve_session_id": session_id})
    
    # Mark session as ended
    await db.bve_sessions.update_one(
        {"id": session_id},
        {"$set": {"ended_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Exited Beta Virtual Environment", "session_id": session_id}

@bve_router.post("/rewind")
async def rewind_bve(data: BVERewind, user: dict = Depends(require_super_or_master_admin)):
    """Rewind BVE to the initial snapshot state"""
    session_id = data.session_id
    
    # Get the snapshot
    session = await db.bve_sessions.find_one({"id": session_id, "user_id": user["id"]})
    if not session:
        raise HTTPException(status_code=404, detail="BVE session not found")
    
    snapshot_data = session.get("snapshot_data", {})
    
    # Clear current BVE data
    await db.bve_trading_signals.delete_many({"bve_session_id": session_id})
    await db.bve_trade_logs.delete_many({"bve_session_id": session_id})
    await db.bve_deposits.delete_many({"bve_session_id": session_id})
    
    # Restore from snapshot
    active_signal = snapshot_data.get("active_signal")
    if active_signal:
        bve_signal = {**active_signal, "bve_session_id": session_id}
        await db.bve_trading_signals.insert_one(bve_signal)
    
    for log in snapshot_data.get("trade_logs", []):
        bve_log = {**log, "bve_session_id": session_id}
        await db.bve_trade_logs.insert_one(bve_log)
    
    for dep in snapshot_data.get("deposits", []):
        bve_dep = {**dep, "bve_session_id": session_id}
        await db.bve_deposits.insert_one(bve_dep)
    
    return {
        "message": "BVE state rewound to entry point",
        "session_id": session_id,
        "restored": {
            "signals": 1 if active_signal else 0,
            "trade_logs": len(snapshot_data.get("trade_logs", [])),
            "deposits": len(snapshot_data.get("deposits", []))
        }
    }

@bve_router.get("/signals")
async def get_bve_signals(user: dict = Depends(require_super_or_master_admin)):
    """Get signals in BVE mode"""
    # Get session from header or query
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    signals = await db.bve_trading_signals.find(
        {"bve_session_id": session["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return signals

@bve_router.post("/signals")
async def create_bve_signal(data: BVESignalCreate, user: dict = Depends(require_super_or_master_admin)):
    """Create a new signal in BVE mode (does not affect real data)"""
    # Get active BVE session
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    # Deactivate other BVE signals
    await db.bve_trading_signals.update_many(
        {"bve_session_id": session["id"], "is_active": True},
        {"$set": {"is_active": False, "status": "completed"}}
    )
    
    # Create new BVE signal
    signal = {
        "id": str(uuid.uuid4()),
        "bve_session_id": session["id"],
        "product": data.product,
        "direction": data.direction,
        "trade_time": data.trade_time,
        "trade_timezone": data.trade_timezone,
        "profit_multiplier": data.profit_multiplier,
        "is_active": True,
        "is_simulated": True,
        "status": "active",
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bve_trading_signals.insert_one(signal)
    
    return {"message": "BVE signal created", "signal": {k: v for k, v in signal.items() if k != "_id"}}

@bve_router.put("/signals/{signal_id}")
async def update_bve_signal(signal_id: str, data: TradingSignalUpdate, user: dict = Depends(require_super_or_master_admin)):
    """Update a BVE signal (deactivate, change direction, etc.)"""
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    # Find the signal
    signal = await db.bve_trading_signals.find_one(
        {"id": signal_id, "bve_session_id": session["id"]},
        {"_id": 0}
    )
    if not signal:
        raise HTTPException(status_code=404, detail="BVE signal not found")
    
    update_data = {}
    if data.trade_time is not None:
        update_data["trade_time"] = data.trade_time
    if data.trade_timezone is not None:
        update_data["trade_timezone"] = data.trade_timezone
    if data.direction is not None:
        update_data["direction"] = data.direction
    if data.profit_points is not None:
        update_data["profit_points"] = data.profit_points
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.is_active is not None:
        if data.is_active:
            # Deactivate all other signals in this BVE session first
            await db.bve_trading_signals.update_many(
                {"bve_session_id": session["id"], "id": {"$ne": signal_id}},
                {"$set": {"is_active": False}}
            )
        update_data["is_active"] = data.is_active
    
    if update_data:
        await db.bve_trading_signals.update_one(
            {"id": signal_id, "bve_session_id": session["id"]},
            {"$set": update_data}
        )
    
    updated = await db.bve_trading_signals.find_one(
        {"id": signal_id, "bve_session_id": session["id"]},
        {"_id": 0}
    )
    return {"message": "BVE signal updated", "signal": updated}

@bve_router.get("/active-signal")
async def get_bve_active_signal(user: dict = Depends(require_super_or_master_admin)):
    """Get active signal in BVE mode"""
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        return {"signal": None}
    
    signal = await db.bve_trading_signals.find_one(
        {"bve_session_id": session["id"], "is_active": True},
        {"_id": 0}
    )
    
    return {"signal": signal}

@bve_router.post("/trade/log")
async def log_bve_trade(data: TradeLogCreate, user: dict = Depends(require_super_or_master_admin)):
    """Log a trade in BVE mode (does not affect real data)"""
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    # Get current BVE account value
    bve_deposits = await db.bve_deposits.find(
        {"bve_session_id": session["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    bve_trade_logs = await db.bve_trade_logs.find(
        {"bve_session_id": session["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    total_deposits = sum(d.get("amount", 0) for d in bve_deposits if d.get("amount", 0) > 0)
    total_profit = sum(t.get("actual_profit", 0) for t in bve_trade_logs)
    account_value = total_deposits + total_profit
    
    # Calculate projected profit
    lot_size = account_value / 980 if account_value > 0 else 0
    projected_profit = lot_size * 15
    profit_difference = data.actual_profit - projected_profit
    
    # Create BVE trade log
    trade_log = {
        "id": str(uuid.uuid4()),
        "bve_session_id": session["id"],
        "user_id": user["id"],
        "lot_size": data.lot_size or lot_size,
        "direction": data.direction,
        "actual_profit": data.actual_profit,
        "projected_profit": projected_profit,
        "profit_difference": profit_difference,
        "performance": "above" if profit_difference > 0 else "below" if profit_difference < 0 else "target",
        "notes": data.notes,
        "is_simulated": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bve_trade_logs.insert_one(trade_log)
    
    return {k: v for k, v in trade_log.items() if k != "_id"}

@bve_router.get("/summary")
async def get_bve_summary(user: dict = Depends(require_super_or_master_admin)):
    """Get profit summary in BVE mode"""
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    # Calculate BVE summary
    bve_deposits = await db.bve_deposits.find(
        {"bve_session_id": session["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    bve_trade_logs = await db.bve_trade_logs.find(
        {"bve_session_id": session["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    total_deposits = sum(d.get("amount", 0) for d in bve_deposits if d.get("amount", 0) > 0)
    total_profit = sum(t.get("actual_profit", 0) for t in bve_trade_logs)
    account_value = total_deposits + total_profit
    lot_size = account_value / 980 if account_value > 0 else 0
    
    return {
        "account_value": account_value,
        "total_deposits": total_deposits,
        "total_profit": total_profit,
        "current_lot_size": lot_size,
        "is_bve": True
    }

# ==================== SCHEDULED TASKS ====================

async def check_missed_trades():
    """Check for users who missed today's trade and send email notifications"""
    try:
        # Get today's date range
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Get today's active signal
        signal = await db.trading_signals.find_one(
            {
                "is_active": True,
                "created_at": {"$gte": today_start, "$lt": today_end}
            },
            {"_id": 0}
        )
        
        if not signal:
            logger.info("No active signal found for missed trade check")
            return
        
        # Get all active members (users who should be trading)
        active_members = await db.users.find(
            {
                "role": "member",
                "is_active": True,
                "email_notifications_enabled": {"$ne": False}  # Not explicitly disabled
            },
            {"_id": 0, "id": 1, "email": 1, "full_name": 1}
        ).to_list(1000)
        
        # Get users who logged a trade today
        traded_users = await db.trade_logs.distinct(
            "user_id",
            {"created_at": {"$gte": today_start, "$lt": today_end}}
        )
        
        # Find members who missed the trade
        missed_members = [m for m in active_members if m["id"] not in traded_users]
        
        # Get email template
        template = await db.email_templates.find_one({"type": "missed_trade"}, {"_id": 0})
        
        if not template:
            template = {
                "subject": "You missed today's trading signal",
                "body": "Hi {{name}},\n\nWe noticed you didn't participate in today's trading signal.\n\nProduct: {{product}}\nDirection: {{direction}}\nTime: {{trade_time}}\n\nDon't miss tomorrow's opportunity!\n\nBest regards,\nCrossCurrent Team"
            }
        
        # Send emails to missed members
        for member in missed_members:
            try:
                subject = template["subject"]
                body = template["body"]
                
                # Replace variables
                body = body.replace("{{name}}", member.get("full_name", "Trader"))
                body = body.replace("{{product}}", signal.get("product", ""))
                body = body.replace("{{direction}}", signal.get("direction", ""))
                body = body.replace("{{trade_time}}", signal.get("trade_time", ""))
                
                from services.email_service import send_email
                await send_email(
                    to=member["email"],
                    subject=subject,
                    body=body
                )
                
                # Log the email
                await db.email_history.insert_one({
                    "id": str(uuid.uuid4()),
                    "to": member["email"],
                    "subject": subject,
                    "template_type": "missed_trade",
                    "status": "sent",
                    "sent_at": datetime.now(timezone.utc)
                })
                
                logger.info(f"Sent missed trade email to {member['email']}")
                
            except Exception as e:
                logger.error(f"Failed to send missed trade email to {member.get('email')}: {e}")
        
        logger.info(f"Missed trade check complete. Notified {len(missed_members)} members.")
        
    except Exception as e:
        logger.error(f"Missed trade scheduler error: {e}")

# ==================== TOP PERFORMERS ====================

@admin_router.get("/top-performers")
async def get_top_performers(
    limit: int = 10,
    exclude_non_traders: bool = True,
    user: dict = Depends(require_admin)
):
    """Get top performing members based on total profit"""
    try:
        # Get date range for "active" traders (traded in last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Get users who have traded recently (if excluding non-traders)
        recent_traders = set()
        if exclude_non_traders:
            recent_traders = set(await db.trade_logs.distinct(
                "user_id",
                {"created_at": {"$gte": thirty_days_ago}}
            ))
        
        # Get all active members with their stats
        pipeline = [
            {"$match": {"role": "member", "is_active": True}},
            {"$lookup": {
                "from": "trade_logs",
                "localField": "id",
                "foreignField": "user_id",
                "as": "trades"
            }},
            {"$addFields": {
                "total_profit": {"$sum": "$trades.actual_profit"},
                "total_trades": {"$size": "$trades"},
                "avg_profit_per_trade": {
                    "$cond": [
                        {"$gt": [{"$size": "$trades"}, 0]},
                        {"$divide": [{"$sum": "$trades.actual_profit"}, {"$size": "$trades"}]},
                        0
                    ]
                }
            }},
            {"$sort": {"total_profit": -1}},
            {"$project": {
                "_id": 0,
                "id": 1,
                "full_name": 1,
                "email": 1,
                "total_profit": 1,
                "total_trades": 1,
                "avg_profit_per_trade": 1
            }}
        ]
        
        performers = await db.users.aggregate(pipeline).to_list(100)
        
        # Filter to only include recent traders if requested
        if exclude_non_traders and recent_traders:
            performers = [p for p in performers if p["id"] in recent_traders]
        
        # Limit results
        performers = performers[:limit]
        
        # Add rank
        for i, p in enumerate(performers, 1):
            p["rank"] = i
        
        return {"performers": performers, "total": len(performers)}
        
    except Exception as e:
        logger.error(f"Failed to get top performers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PERFORMANCE REPORT (ADMIN PROTECTED) ====================

from fastapi.responses import Response

@admin_router.get("/analytics/report/image")
async def generate_performance_report_image(
    period: str = "monthly",  # daily, weekly, monthly
    user_id: Optional[str] = None,  # Admin can generate for specific user
    user: dict = Depends(require_admin)  # Changed to require admin
):
    """Generate an image-based performance report (Admin only)"""
    from services.report_generator import generate_performance_report
    
    try:
        # Use provided user_id or default to current admin's id
        target_user_id = user_id if user_id else user["id"]
        
        # Get target user details if generating for another user
        if user_id:
            target_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            user_name = target_user.get("full_name", target_user.get("email", "Trader"))
        else:
            user_name = user.get("full_name", user.get("email", "Trader"))
        
        # Calculate date range based on period
        now = datetime.now(timezone.utc)
        if period == "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start_date = now - timedelta(days=7)
        else:  # monthly
            start_date = now - timedelta(days=30)
        
        # Get user's trades for the period
        trades_cursor = db.trade_logs.find(
            {
                "user_id": target_user_id,
                "created_at": {"$gte": start_date}
            },
            {"_id": 0}
        ).sort("created_at", -1)
        trades = await trades_cursor.to_list(100)
        
        # Calculate statistics
        total_profit = sum(t.get("actual_profit", 0) for t in trades)
        total_trades = len(trades)
        
        winning_trades = [t for t in trades if t.get("actual_profit", 0) > 0]
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        profits = [t.get("actual_profit", 0) for t in trades]
        best_trade = max(profits) if profits else 0
        worst_trade = min(profits) if profits else 0
        
        # Get account value from latest deposit summary
        summary = await db.deposits.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        deposits_total = summary[0]["total"] if summary else 0
        
        withdrawals = await db.withdrawals.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        withdrawals_total = withdrawals[0]["total"] if withdrawals else 0
        
        all_time_profit = await db.trade_logs.aggregate([
            {"$match": {"user_id": target_user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$actual_profit"}}}
        ]).to_list(1)
        
        all_profit = all_time_profit[0]["total"] if all_time_profit else 0
        account_value = deposits_total - withdrawals_total + all_profit
        
        # Calculate streak
        streak = 0
        for trade in trades:
            profit = trade.get("actual_profit", 0)
            if profit > 0:
                if streak >= 0:
                    streak += 1
                else:
                    break
            elif profit < 0:
                if streak <= 0:
                    streak -= 1
                else:
                    break
        
        stats = {
            "account_value": account_value,
            "total_profit": total_profit,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_profit_per_trade": avg_profit,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "streak": streak
        }
        
        # Format trades for report
        formatted_trades = []
        for t in trades[:5]:
            formatted_trades.append({
                "date": t.get("created_at", "").strftime("%Y-%m-%d") if hasattr(t.get("created_at", ""), "strftime") else str(t.get("created_at", ""))[:10],
                "direction": t.get("direction", "-"),
                "lot_size": t.get("lot_size", 0),
                "actual_profit": t.get("actual_profit", 0)
            })
        
        # Get platform name from settings
        settings = await db.settings.find_one({}, {"_id": 0, "site_name": 1})
        platform_name = settings.get("site_name", "CrossCurrent") if settings else "CrossCurrent"
        
        # Generate the image
        image_bytes = await generate_performance_report(
            user_name=user_name,
            period=period,
            stats=stats,
            trades=formatted_trades,
            platform_name=platform_name
        )
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="performance_report_{period}_{now.strftime("%Y%m%d")}.png"'
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/analytics/report/base64")
async def generate_performance_report_base64(
    period: str = "monthly",
    user_id: Optional[str] = None,  # Admin can generate for specific user
    user: dict = Depends(require_admin)  # Changed to require admin
):
    """Generate a performance report and return as base64 for embedding (Admin only)"""
    from services.report_generator import generate_report_base64
    
    try:
        # Use provided user_id or default to current admin's id
        target_user_id = user_id if user_id else user["id"]
        
        # Get target user details if generating for another user
        if user_id:
            target_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
            if not target_user:
                raise HTTPException(status_code=404, detail="User not found")
            user_name = target_user.get("full_name", target_user.get("email", "Trader"))
        else:
            user_name = user.get("full_name", user.get("email", "Trader"))
        
        # Use the same logic as above but return base64
        now = datetime.now(timezone.utc)
        if period == "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start_date = now - timedelta(days=7)
        else:
            start_date = now - timedelta(days=30)
        
        trades_cursor = db.trade_logs.find(
            {"user_id": target_user_id, "created_at": {"$gte": start_date}},
            {"_id": 0}
        ).sort("created_at", -1)
        trades = await trades_cursor.to_list(100)
        
        total_profit = sum(t.get("actual_profit", 0) for t in trades)
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get("actual_profit", 0) > 0]
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        profits = [t.get("actual_profit", 0) for t in trades]
        best_trade = max(profits) if profits else 0
        worst_trade = min(profits) if profits else 0
        
        summary = await db.deposits.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        deposits_total = summary[0]["total"] if summary else 0
        
        withdrawals = await db.withdrawals.aggregate([
            {"$match": {"user_id": target_user_id, "status": "completed"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        withdrawals_total = withdrawals[0]["total"] if withdrawals else 0
        
        all_time_profit = await db.trade_logs.aggregate([
            {"$match": {"user_id": target_user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$actual_profit"}}}
        ]).to_list(1)
        all_profit = all_time_profit[0]["total"] if all_time_profit else 0
        account_value = deposits_total - withdrawals_total + all_profit
        
        streak = 0
        for trade in trades:
            profit = trade.get("actual_profit", 0)
            if profit > 0:
                if streak >= 0: streak += 1
                else: break
            elif profit < 0:
                if streak <= 0: streak -= 1
                else: break
        
        stats = {
            "account_value": account_value,
            "total_profit": total_profit,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_profit_per_trade": avg_profit,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "streak": streak
        }
        
        formatted_trades = [{
            "date": t.get("created_at", "").strftime("%Y-%m-%d") if hasattr(t.get("created_at", ""), "strftime") else str(t.get("created_at", ""))[:10],
            "direction": t.get("direction", "-"),
            "lot_size": t.get("lot_size", 0),
            "actual_profit": t.get("actual_profit", 0)
        } for t in trades[:5]]
        
        settings = await db.settings.find_one({}, {"_id": 0, "site_name": 1})
        platform_name = settings.get("site_name", "CrossCurrent") if settings else "CrossCurrent"
        
        base64_image = await generate_report_base64(
            user_name=user_name,
            period=period,
            stats=stats,
            trades=formatted_trades,
            platform_name=platform_name
        )
        
        return {
            "image_base64": base64_image,
            "period": period,
            "generated_at": now.isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to generate base64 report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MAIN SETUP ====================

@api_router.get("/")
async def root():
    return {"message": "CrossCurrent Finance Center API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(profit_router)
api_router.include_router(trade_router)
api_router.include_router(admin_router)
api_router.include_router(debt_router)
api_router.include_router(goals_router)
api_router.include_router(currency_router)
api_router.include_router(settings_router)
api_router.include_router(api_center_router)
api_router.include_router(bve_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db():
    import asyncio
    
    # Retry logic for database connection (important for Atlas)
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Test the connection first
            await client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB (attempt {attempt + 1})")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts: {e}")
                raise
    
    # Create indexes with error handling
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.deposits.create_index("user_id")
        await db.deposits.create_index([("user_id", 1), ("created_at", -1)])  # For sorted queries
        await db.trade_logs.create_index("user_id")
        await db.trade_logs.create_index([("user_id", 1), ("created_at", -1)])  # For paginated trade history
        await db.trade_logs.create_index("signal_id")  # For signal lookups
        await db.trading_signals.create_index("is_active")
        await db.trading_signals.create_index("id")  # For signal enrichment
        await db.debts.create_index("user_id")
        await db.goals.create_index("user_id")
        await db.notifications.create_index("recipient_id")
        await db.notifications.create_index([("recipient_id", 1), ("timestamp", -1)])
        await db.global_holidays.create_index("date", unique=True)  # For holiday lookups
        await db.trading_products.create_index("id")  # For product lookups
        await db.licenses.create_index([("user_id", 1), ("is_active", 1)])  # For license checks
        logger.info("Database indexes created")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")
    
    # Initialize websocket service with database reference
    set_websocket_database(db)
    logger.info("WebSocket service initialized with database")
    
    # Start the scheduler for missed trade emails
    # Run at 11 PM UTC every day (after typical trading hours)
    try:
        scheduler.add_job(
            check_missed_trades,
            CronTrigger(hour=23, minute=0),
            id="missed_trade_check",
            replace_existing=True
        )
        scheduler.start()
        logger.info("Scheduler started for missed trade notifications")
    except Exception as e:
        logger.warning(f"Scheduler startup warning: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()

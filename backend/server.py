from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'crosscurrent-finance-secret-key-2024')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Heartbeat API
HEARTBEAT_API_KEY = os.environ.get('HEARTBEAT_API_KEY', '')

# Cloudinary Config
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'crosscurrent'),
    api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', '')
)

# Emailit Config
EMAILIT_API_KEY = os.environ.get('EMAILIT_API_KEY', '')

# Super Admin Secret Code
SUPER_ADMIN_SECRET = os.environ.get('SUPER_ADMIN_SECRET', 'CROSSCURRENT2024')

# Master Admin Secret Code
MASTER_ADMIN_SECRET = os.environ.get('MASTER_ADMIN_SECRET', 'CrossCurrentGODSEYE')

# Super Admin Bypass Code (for hidden settings click feature)
SUPER_ADMIN_BYPASS = os.environ.get('SUPER_ADMIN_BYPASS', 'SUPER_ADMIN_BYPASS')

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

security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    created_at: datetime

class TradeLogCreate(BaseModel):
    lot_size: float
    direction: str  # BUY or SELL
    actual_profit: float
    notes: Optional[str] = None

class TradeLogResponse(BaseModel):
    id: str
    user_id: str
    lot_size: float
    direction: str
    projected_profit: float
    actual_profit: float
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

class TradingSignalUpdate(BaseModel):
    trade_time: Optional[str] = None
    trade_timezone: Optional[str] = None
    direction: Optional[str] = None
    profit_points: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class TradingSignalResponse(BaseModel):
    id: str
    product: str
    trade_time: str
    trade_timezone: str
    direction: str
    profit_points: float
    notes: Optional[str]
    is_active: bool
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
    site_title: str = "CrossCurrent Finance Center"
    site_description: str = "Trading profit management platform"
    favicon_url: Optional[str] = None
    logo_url: Optional[str] = None
    og_image_url: Optional[str] = None
    primary_color: str = "#3B82F6"
    accent_color: str = "#06B6D4"
    hide_emergent_badge: bool = False
    # Integration API Keys
    emailit_api_key: Optional[str] = None
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    heartbeat_api_key: Optional[str] = None

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

class LicenseInviteUpdate(BaseModel):
    valid_duration: Optional[str] = None
    max_uses: Optional[int] = None
    notes: Optional[str] = None
    invitee_email: Optional[str] = None
    invitee_name: Optional[str] = None

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
    new_role: str  # admin or super_admin
    secret_code: Optional[str] = None

# ==================== HELPERS ====================

async def create_admin_notification(notification_type: str, title: str, message: str, user_id: str, user_name: str, amount: float = None, metadata: dict = None):
    """Create a notification for admins about member activity"""
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_notifications.insert_one(notification)
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
    """Calculate withdrawal fees: 3% Merin + $1 Binance"""
    merin_fee = amount * 0.03
    binance_fee = 1.0
    total_fees = merin_fee + binance_fee
    net_amount = amount - total_fees
    return {
        "gross_amount": amount,
        "merin_fee": round(merin_fee, 2),
        "binance_fee": binance_fee,
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
    
    token = create_token(user_id, data.email, role)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=data.email,
            full_name=data.full_name,
            role=role,
            created_at=datetime.fromisoformat(user["created_at"]),
            allowed_dashboards=user.get("allowed_dashboards")
        )
    )

@auth_router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Skip Heartbeat verification for admins and above
    admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
    if user.get("role") not in admin_roles:
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
            allowed_dashboards=user.get("allowed_dashboards")
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
        allowed_dashboards=user.get("allowed_dashboards")
    )

class VerifyPasswordRequest(BaseModel):
    password: str

@auth_router.post("/verify-password")
async def verify_password(data: VerifyPasswordRequest, user: dict = Depends(get_current_user)):
    """Verify the current user's password"""
    db_user = await db.users.find_one({"id": user["id"]})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_valid = bcrypt.checkpw(data.password.encode(), db_user["password"].encode())
    return {"valid": is_valid}

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
    deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    total_deposits = sum(d["amount"] for d in deposits)
    total_projected = sum(t["projected_profit"] for t in trades)
    total_actual = sum(t["actual_profit"] for t in trades)
    
    return {
        "total_deposits": round(total_deposits, 2),
        "total_projected_profit": round(total_projected, 2),
        "total_actual_profit": round(total_actual, 2),
        "profit_difference": round(total_actual - total_projected, 2),
        "account_value": round(total_deposits + total_actual, 2),
        "total_trades": len(trades),
        "performance_rate": round((total_actual / total_projected * 100) if total_projected > 0 else 0, 2)
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
    fees = calculate_withdrawal_fees(data.amount)
    
    # Get current account value
    deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    trades = await db.trade_logs.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    
    total_deposits = sum(d["amount"] for d in deposits)
    total_profit = sum(t["actual_profit"] for t in trades)
    account_value = total_deposits + total_profit
    
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
    # Calculate fees
    merin_fee = data.amount * 0.03  # 3% Merin fee
    binance_fee = 1.0  # $1 Binance fee
    net_amount = data.amount - merin_fee - binance_fee
    
    # Calculate estimated arrival date (2 business days)
    estimated_arrival = add_business_days(datetime.now(timezone.utc), 2)
    
    # Record as negative deposit (withdrawal)
    withdrawal = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": -data.amount,  # Negative to indicate withdrawal
        "product": "WITHDRAWAL",  # Mark as withdrawal type
        "currency": "USDT",
        "notes": data.notes or f"Withdrawal to Binance",
        "is_withdrawal": True,
        "gross_amount": data.amount,
        "merin_fee": merin_fee,
        "binance_fee": binance_fee,
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
        metadata={"net_amount": net_amount, "merin_fee": merin_fee, "binance_fee": binance_fee}
    )
    
    return {
        "message": "Withdrawal recorded successfully",
        "withdrawal_id": withdrawal["id"],
        "gross_amount": data.amount,
        "merin_fee": round(merin_fee, 2),
        "binance_fee": binance_fee,
        "net_amount": round(net_amount, 2)
    }

@profit_router.get("/withdrawals")
async def get_withdrawals(user: dict = Depends(get_current_user)):
    """Get all withdrawals for the current user"""
    withdrawals = await db.deposits.find(
        {"user_id": user["id"], "is_withdrawal": True},
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


# ==================== TRADE MONITOR ROUTES ====================

@trade_router.post("/log", response_model=TradeLogResponse)
async def log_trade(data: TradeLogCreate, user: dict = Depends(get_current_user)):
    projected_profit = calculate_exit_value(data.lot_size)
    profit_difference = data.actual_profit - projected_profit
    
    # Determine performance
    if abs(profit_difference) < 0.01:
        performance = "perfect"
    elif profit_difference > 0:
        performance = "exceeded"
    else:
        performance = "below"
    
    # Get active signal
    active_signal = await db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    
    trade_id = str(uuid.uuid4())
    trade = {
        "id": trade_id,
        "user_id": user["id"],
        "lot_size": data.lot_size,
        "direction": data.direction,
        "projected_profit": projected_profit,
        "actual_profit": data.actual_profit,
        "profit_difference": profit_difference,
        "performance": performance,
        "signal_id": active_signal["id"] if active_signal else None,
        "notes": data.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trade_logs.insert_one(trade)
    
    # Create notification if member exited below projected amount
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
                "lot_size": data.lot_size
            }
        )
    
    return TradeLogResponse(**{**trade, "created_at": datetime.fromisoformat(trade["created_at"])})

@trade_router.get("/logs", response_model=List[TradeLogResponse])
async def get_trade_logs(limit: int = 50, user: dict = Depends(get_current_user)):
    trades = await db.trade_logs.find(
        {"user_id": user["id"]}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return [TradeLogResponse(**{**t, "created_at": datetime.fromisoformat(t["created_at"]) if isinstance(t["created_at"], str) else t["created_at"]}) for t in trades]

@trade_router.get("/history")
async def get_trade_history(
    page: int = 1, 
    page_size: int = 10, 
    user: dict = Depends(get_current_user)
):
    """Get paginated trade history with signal details"""
    skip = (page - 1) * page_size
    
    # Get total count
    total = await db.trade_logs.count_documents({"user_id": user["id"]})
    
    # Get paginated trades
    trades = await db.trade_logs.find(
        {"user_id": user["id"]}, 
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Enrich with signal details
    enriched_trades = []
    for trade in trades:
        signal_details = None
        if trade.get("signal_id"):
            signal = await db.trading_signals.find_one({"id": trade["signal_id"]}, {"_id": 0})
            if signal:
                signal_details = {
                    "product": signal.get("product", "MOIL10"),
                    "trade_time": signal.get("trade_time"),
                    "trade_timezone": signal.get("trade_timezone", "Asia/Manila"),
                }
        
        enriched_trades.append({
            **trade,
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
async def get_trade_streak(user: dict = Depends(get_current_user)):
    """Calculate current streak of 'exceeded' or 'perfect' trades"""
    # Get all trades ordered by date descending
    trades = await db.trade_logs.find(
        {"user_id": user["id"]}, 
        {"_id": 0, "performance": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(1000)
    
    if not trades:
        return {"streak": 0, "streak_type": None}
    
    # Calculate streak
    streak = 0
    streak_type = None
    
    for trade in trades:
        perf = trade.get("performance")
        if perf in ["exceeded", "perfect"]:
            if streak == 0:
                streak_type = "winning"
            streak += 1
        else:
            break  # Streak broken
    
    return {
        "streak": streak,
        "streak_type": streak_type,  # "winning" if positive, None if no streak
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
async def get_daily_summary(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    trades = await db.trade_logs.find({
        "user_id": user["id"],
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

@trade_router.post("/forward-to-profit")
async def forward_trade_to_profit(trade_id: str, user: dict = Depends(get_current_user)):
    """Forward trade profit to profit tracker by creating a deposit entry"""
    trade = await db.trade_logs.find_one({"id": trade_id, "user_id": user["id"]}, {"_id": 0})
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
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
        "is_simulated": False,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trading_signals.insert_one(signal)
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
    elif status == "active":
        query["is_suspended"] = {"$ne": True}
    
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
            # Calculate account value from deposits and profits
            deposits = await db.deposits.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)
            trades = await db.trade_logs.find({"user_id": u["id"]}, {"_id": 0}).to_list(1000)
            
            total_deposits = sum(d.get("amount", 0) for d in deposits if d.get("type") != "profit" and d.get("type") != "withdrawal")
            total_withdrawals = sum(abs(d.get("amount", 0)) for d in deposits if d.get("type") == "withdrawal")
            total_profit = sum(t.get("actual_profit", 0) for t in trades)
            
            user_data["account_value"] = round(total_deposits - total_withdrawals + total_profit, 2)
        users.append(user_data)
    
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
    
    return {
        "user": member,
        "stats": {
            "total_trades": total_trades,
            "total_profit": round(total_profit, 2),
            "total_deposits": round(total_deposits, 2),
            "account_value": round(total_deposits + total_profit, 2)
        },
        "recent_trades": trades[:10],
        "recent_deposits": deposits[:10]
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
    """Get members who didn't enter today's trade"""
    
    # Get today's date range
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # Get all member users
    all_users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    member_users = [u for u in all_users if u.get("role") in ["user", "member"]]
    
    # Get today's trades
    today_trades = await db.trade_logs.find({
        "created_at": {
            "$gte": today_start.isoformat(),
            "$lte": today_end.isoformat()
        }
    }, {"_id": 0}).to_list(1000)
    
    # Get users who traded today
    users_who_traded = set(t.get("user_id") for t in today_trades)
    
    # Find who missed
    missed_members = []
    for member in member_users:
        if member["id"] not in users_who_traded:
            missed_members.append({
                "id": member["id"],
                "name": member.get("full_name", "Unknown"),
                "email": member.get("email", "")
            })
    
    # Calculate today's team stats for email
    team_profit_today = sum(t.get("actual_profit", 0) for t in today_trades)
    highest_earner = None
    highest_profit = 0
    
    for trade in today_trades:
        if trade.get("actual_profit", 0) > highest_profit:
            highest_profit = trade.get("actual_profit", 0)
            # Find the user's name
            user_id = trade.get("user_id")
            user_data = next((u for u in all_users if u["id"] == user_id), None)
            if user_data:
                highest_earner = user_data.get("full_name", "Unknown")
    
    return {
        "missed_members": missed_members,
        "team_profit_today": round(team_profit_today, 2),
        "highest_earner": highest_earner,
        "highest_profit": round(highest_profit, 2),
        "total_traded_today": len(users_who_traded)
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
    
    # Add user names to trades
    enriched_trades = []
    for trade in trades:
        trade["trader_name"] = user_names.get(trade.get("user_id"), "Unknown")
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
    Daily profit is fixed within each quarter and recalculated at quarter start.
    """
    projections = []
    current_date = start_date
    current_amount = starting_amount
    current_quarter = get_quarter(start_date)
    current_year = start_date.year
    
    # Calculate initial quarter's daily profit
    quarter_daily_profit = round((current_amount / 980) * 15, 2)
    quarter_start_amount = current_amount
    
    trading_days_processed = 0
    
    while trading_days_processed < days_to_project:
        # Check if we've moved to a new quarter
        new_quarter = get_quarter(current_date)
        new_year = current_date.year
        
        if new_year != current_year or new_quarter != current_quarter:
            # Recalculate daily profit for new quarter using last amount
            quarter_daily_profit = round((current_amount / 980) * 15, 2)
            quarter_start_amount = current_amount
            current_quarter = new_quarter
            current_year = new_year
        
        if is_trading_day(current_date):
            current_amount = round(current_amount + quarter_daily_profit, 2)
            
            projections.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "quarter": f"Q{current_quarter} {current_year}",
                "daily_profit": quarter_daily_profit,
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
    
    # Enrich with user info
    all_users = await db.users.find({}, {"_id": 0, "id": 1, "full_name": 1, "email": 1}).to_list(1000)
    user_lookup = {u["id"]: u for u in all_users}
    
    enriched = []
    for lic in licenses:
        user_info = user_lookup.get(lic["user_id"], {})
        lic["user_name"] = user_info.get("full_name", "Unknown")
        lic["user_email"] = user_info.get("email", "")
        
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
        "start_date": start_date.isoformat(),
        "notes": data.notes,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"]
    }
    
    await db.licenses.insert_one(license_doc)
    
    # Update user record with license type
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {"license_type": data.license_type}}
    )
    
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
        "is_revoked": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user["id"],
        "created_by_name": user.get("full_name", "Admin")
    }
    
    await db.license_invites.insert_one(invite)
    
    # Generate registration URL
    frontend_url = os.environ.get("FRONTEND_URL", "https://trader-hub-39.preview.emergentagent.com")
    registration_url = f"{frontend_url}/register/license/{invite_code}"
    
    return {
        "message": "License invite created successfully",
        "invite_id": invite["id"],
        "code": invite_code,
        "registration_url": registration_url
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
    
    frontend_url = os.environ.get("FRONTEND_URL", "https://trader-hub-39.preview.emergentagent.com")
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(new_user)
    
    # Create the actual license
    license_id = str(uuid.uuid4())
    license_doc = {
        "id": license_id,
        "user_id": user_id,
        "license_type": invite["license_type"],
        "starting_amount": invite["starting_amount"],
        "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
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
    token = create_access_token({"sub": user_id})
    
    # Remove password from response
    del new_user["password"]
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user,
        "license": {
            "type": invite["license_type"],
            "starting_amount": invite["starting_amount"]
        }
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

# ==================== INTEGRATION TESTS ====================
@settings_router.post("/test-emailit")
async def test_emailit_connection(user: dict = Depends(require_admin)):
    """Test Emailit API connection"""
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    emailit_key = settings.get("emailit_api_key") if settings else None
    
    if not emailit_key:
        emailit_key = os.environ.get("EMAILIT_API_KEY")
    
    if not emailit_key:
        return {"success": False, "message": "Emailit API key not configured"}
    
    try:
        # Test by checking account status
        response = requests.get(
            "https://api.emailit.com/v1/account",
            headers={"Authorization": f"Bearer {emailit_key}"},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"success": True, "message": "Emailit connection successful!", "data": response.json()}
        else:
            return {"success": False, "message": f"Emailit returned status {response.status_code}"}
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
    
    try:
        # Test Heartbeat connection
        response = requests.get(
            "https://api.heartbeat.chat/v0/community",
            headers={"Authorization": f"Bearer {heartbeat_key}"},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"success": True, "message": "Heartbeat connection successful!", "data": response.json()}
        else:
            return {"success": False, "message": f"Heartbeat returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}"}

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

@admin_router.post("/members/{user_id}/send-email")
async def send_email_to_member(user_id: str, subject: str, body: str, user: dict = Depends(require_admin)):
    member = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="User not found")
    
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
                    "to": member["email"],
                    "subject": subject,
                    "html": body
                },
                timeout=30.0
            )
            if response.status_code in [200, 201, 202]:
                return {"message": "Email sent successfully"}
            else:
                raise HTTPException(status_code=response.status_code, detail="Email sending failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")

@admin_router.post("/upgrade-role")
async def upgrade_role(data: RoleUpgrade, user: dict = Depends(require_admin)):
    target_user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.new_role == "super_admin":
        if data.secret_code != SUPER_ADMIN_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret code")
        if user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can create super admins")
    
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
        {"$set": {"role": "user", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "User downgraded to regular user"}

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
async def send_email(to: str, subject: str, body: str, user: dict = Depends(require_admin)):
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
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.deposits.create_index("user_id")
    await db.trade_logs.create_index("user_id")
    await db.trading_signals.create_index("is_active")
    await db.debts.create_index("user_id")
    await db.goals.create_index("user_id")
    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

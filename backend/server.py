from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
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

async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_super_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
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
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email.lower(),
        "password": hash_password(data.password),
        "full_name": data.full_name,
        "heartbeat_email": heartbeat_email.lower(),
        "role": "user",
        "profile_picture": None,
        "lot_size": 0.01,
        "timezone": "UTC",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    token = create_token(user_id, data.email, "user")
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=data.email,
            full_name=data.full_name,
            role="user",
            created_at=datetime.fromisoformat(user["created_at"])
        )
    )

@auth_router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Skip Heartbeat verification for admins and super_admins
    if user.get("role") not in ["admin", "super_admin"]:
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
            timezone=user.get("timezone", "UTC")
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
        timezone=user.get("timezone", "UTC")
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
    users = await db.users.find(query, {"_id": 0, "password": 0}).skip(skip).limit(limit).to_list(limit)
    
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

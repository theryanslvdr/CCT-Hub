"""
CrossCurrent Finance Center API - Main Application Entry Point
Refactored: Routes extracted to /routes/ modules.
"""
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
import uuid
from datetime import datetime, timezone
import jwt
import hashlib

import cloudinary

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Build version
_version_file = "/app/.build_version"
try:
    with open(_version_file, 'r') as f:
        BUILD_VERSION = f.read().strip()
except FileNotFoundError:
    BUILD_VERSION = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:12]
    try:
        with open(_version_file, 'w') as f:
            f.write(BUILD_VERSION)
    except Exception:
        pass

# Import services
from services import (
    websocket_manager, set_websocket_database
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ─── MongoDB Connection ───
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise ValueError("MONGO_URL environment variable is required")

client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
    retryWrites=True,
    w='majority',
    maxPoolSize=100,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    waitQueueTimeoutMS=10000,
)

db_name = os.environ.get('DB_NAME')
if not db_name:
    import re
    match = re.search(r'/([^/?]+)\?', mongo_url)
    if not match:
        match = re.search(r'/([^/?]+)$', mongo_url)
    db_name = match.group(1) if match else 'crosscurrent_finance'

db = client[db_name]
logger.info(f"Using database: {db_name}")

# ─── JWT Config ───
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = 'HS256'

# ─── External Service Config ───
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    api_key=os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', '')
)

# ─── APScheduler ───
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
scheduler = AsyncIOScheduler()

# ─── Initialize Shared Deps ───
SUPER_ADMIN_SECRET = os.environ.get('SUPER_ADMIN_SECRET', '')
MASTER_ADMIN_SECRET = os.environ.get('MASTER_ADMIN_SECRET', '')
SUPER_ADMIN_BYPASS = os.environ.get('SUPER_ADMIN_BYPASS', '')

import deps as _deps
_deps.init(db, JWT_SECRET, SUPER_ADMIN_SECRET, MASTER_ADMIN_SECRET, SUPER_ADMIN_BYPASS)

# ─── Create App & Routers ───
app = FastAPI(title="CrossCurrent Finance Center API", redirect_slashes=False)
api_router = APIRouter(prefix="/api")

# ─── Import Route Modules ───
# Core routes (extracted from server.py)
from routes.auth_routes import router as _auth_router
from routes.profit_routes import router as _profit_router
from routes.trade_routes import router as _trade_router
from routes.admin_routes import router as _admin_router
from routes.general_routes import router as _general_router

# Previously extracted routes
from routes.currency import router as _currency_router
from routes.debt import router as _debt_router
from routes.goals import router as _goals_router
from routes.api_center import router as _api_center_router
from routes.bve import router as _bve_router
from routes.settings import router as _settings_router
from routes.habits import router as _habits_router
from routes.affiliate import router as _affiliate_router, admin_affiliate_router as _admin_affiliate_router
from routes.activity_feed import admin_activity_router as _admin_activity_router
from routes.users import router as _users_router
from routes.family import router as _family_router, admin_family_router as _admin_family_router
from routes.rewards import router as _rewards_router
from routes.forum import router as _forum_router
from routes.publitio import router as _publitio_router
from routes.system_health import router as _system_health_router
from routes.onboarding_routes import router as _onboarding_router
from routes.ai_routes import router as _ai_router
from routes.referral_routes import router as _referral_router
from routes.quiz_routes import router as _quiz_router
from routes.ai_assistant_routes import router as _ai_assistant_router

# ─── Register Routers ───
api_router.include_router(_auth_router)
api_router.include_router(_users_router)
api_router.include_router(_profit_router)
api_router.include_router(_trade_router)
api_router.include_router(_admin_router)
api_router.include_router(_general_router)
api_router.include_router(_habits_router)
api_router.include_router(_affiliate_router)
api_router.include_router(_admin_affiliate_router)
api_router.include_router(_admin_activity_router)
api_router.include_router(_debt_router)
api_router.include_router(_goals_router)
api_router.include_router(_currency_router)
api_router.include_router(_settings_router)
api_router.include_router(_api_center_router)
api_router.include_router(_bve_router)
api_router.include_router(_family_router)
api_router.include_router(_admin_family_router)
api_router.include_router(_rewards_router)
api_router.include_router(_forum_router)
api_router.include_router(_publitio_router)
api_router.include_router(_system_health_router)
api_router.include_router(_onboarding_router)
api_router.include_router(_ai_router)
api_router.include_router(_referral_router)
api_router.include_router(_quiz_router)
api_router.include_router(_ai_assistant_router)

app.include_router(api_router)

# ─── Latency Tracking Middleware ───
from starlette.middleware.base import BaseHTTPMiddleware
import time as _time

class LatencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = _time.time()
        response = await call_next(request)
        latency_ms = (_time.time() - start) * 1000
        path = request.url.path
        try:
            from routes.system_health import record_latency
            if '/api/auth/' in path:
                record_latency('auth', latency_ms)
            elif '/api/profit/' in path:
                record_latency('profit', latency_ms)
            elif '/api/trade/' in path:
                record_latency('trade', latency_ms)
            elif '/api/admin/' in path:
                record_latency('admin', latency_ms)
            elif '/api/forum/' in path:
                record_latency('forum', latency_ms)
            else:
                record_latency('general', latency_ms)
        except Exception:
            pass
        return response

app.add_middleware(LatencyMiddleware)

# ─── CORS Middleware ───
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket Endpoints ───

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
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
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id, role)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(websocket, user_id, role)


@app.websocket("/api/ws/{user_id}")
async def api_websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint (via /api/ route for ingress)"""
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
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id, role)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(websocket, user_id, role)


# ─── Startup & Shutdown ───

@app.on_event("startup")
async def startup_db():
    import asyncio
    from helpers import check_missed_trades

    max_retries = 5
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            await client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB (attempt {attempt + 1})")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts: {e}")
                raise

    # Create indexes
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.deposits.create_index("user_id")
        await db.deposits.create_index([("user_id", 1), ("created_at", -1)])
        await db.trade_logs.create_index("user_id")
        await db.trade_logs.create_index([("user_id", 1), ("created_at", -1)])
        await db.trade_logs.create_index("signal_id")
        await db.trading_signals.create_index("is_active")
        await db.trading_signals.create_index("id")
        await db.debts.create_index("user_id")
        await db.goals.create_index("user_id")
        await db.notifications.create_index("recipient_id")
        await db.notifications.create_index([("recipient_id", 1), ("timestamp", -1)])
        await db.global_holidays.create_index("date", unique=True)
        await db.trading_products.create_index("id")
        await db.licenses.create_index([("user_id", 1), ("is_active", 1)])
        await db.rewards_stats.create_index("user_id", unique=True)
        await db.rewards_leaderboard.create_index([("month", 1), ("rank", 1)])
        await db.rewards_leaderboard.create_index([("user_id", 1), ("month", 1)], unique=True)
        await db.rewards_point_logs.create_index([("user_id", 1), ("created_at", -1)])
        await db.rewards_promotions.create_index("is_active")
        await db.users.create_index("referral_code", sparse=True)
        await db.referral_events.create_index([("user_id", 1), ("created_at", -1)])
        logger.info("Database indexes created")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")

    # Seed rewards promotion rules
    try:
        existing = await db.rewards_promotions.count_documents({})
        if existing == 0:
            from datetime import timezone as tz
            now = datetime.now(tz.utc)
            await db.rewards_promotions.insert_many([
                {
                    "id": "promo_continuous_base",
                    "name": "Base Continuous Rewards",
                    "type": "continuous",
                    "start_date": "2020-01-01T00:00:00+00:00",
                    "end_date": "2099-12-31T23:59:59+00:00",
                    "multiplier": 1.0,
                    "is_active": True,
                    "rules_json": {
                        "signup_verify": 25, "join_community": 5, "first_trade": 25,
                        "first_daily_win": 10, "help_chat": 5, "qualified_referral": 150,
                        "deposit": 50, "withdrawal": 5, "streak_5_day": 50,
                        "milestone_10_trade": 125, "milestone_20_trade_streak": 20,
                    },
                    "created_at": now.isoformat(),
                },
                {
                    "id": "promo_hot_summer",
                    "name": "Hot Summer Night's Dream - March 2026",
                    "type": "seasonal",
                    "start_date": "2026-03-01T00:00:00+00:00",
                    "end_date": "2026-03-31T23:59:59+00:00",
                    "multiplier": 2.0,
                    "is_active": True,
                    "rules_json": {
                        "deposit": True, "first_trade": True, "qualified_referral": True,
                    },
                    "created_at": now.isoformat(),
                },
            ])
            logger.info("Seeded rewards promotion rules")
    except Exception as e:
        logger.warning(f"Rewards seed warning: {e}")

    # Seed badge definitions
    try:
        from utils.rewards_engine import seed_default_badges
        await seed_default_badges(db)
        await db.rewards_badge_definitions.create_index("id", unique=True)
        await db.rewards_user_badges.create_index([("user_id", 1), ("badge_id", 1)], unique=True)
        logger.info("Badge definitions seeded")
    except Exception as e:
        logger.warning(f"Badge seed warning: {e}")

    # Initialize WebSocket service
    set_websocket_database(db)
    logger.info("WebSocket service initialized with database")

    # Start missed trade scheduler
    try:
        scheduler.add_job(
            check_missed_trades,
            CronTrigger(hour=23, minute=0),
            id="missed_trade_check",
            replace_existing=True
        )
        
        # Auto batch sync to rewards platform every 4 hours
        async def auto_batch_sync():
            try:
                from services.rewards_sync_service import batch_sync_all_users
                summary = await batch_sync_all_users(db)
                logger.info(f"Auto batch sync completed: {summary.get('success', 0)} synced, {summary.get('failed', 0)} failed")
            except Exception as e:
                logger.warning(f"Auto batch sync failed: {e}")
        
        scheduler.add_job(
            auto_batch_sync,
            IntervalTrigger(hours=4),
            id="rewards_auto_sync",
            replace_existing=True
        )

        # Mid-day streak sync (12:00 UTC)
        scheduler.add_job(
            auto_batch_sync,
            CronTrigger(hour=12, minute=0),
            id="midday_streak_sync",
            replace_existing=True
        )

        # End-of-day streak sync (23:30 UTC)
        scheduler.add_job(
            auto_batch_sync,
            CronTrigger(hour=23, minute=30),
            id="eod_streak_sync",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Scheduler started for missed trade notifications, rewards auto-sync (every 4h), and streak sync (mid-day + end-of-day)")
    except Exception as e:
        logger.warning(f"Scheduler startup warning: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()

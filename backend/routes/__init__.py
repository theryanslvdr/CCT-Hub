"""Backend route modules."""

# Core routes (extracted from server.py)
from routes.auth_routes import router as auth_router
from routes.profit_routes import router as profit_router
from routes.trade_routes import router as trade_router
from routes.admin_routes import router as admin_router
from routes.general_routes import router as general_router

# Previously extracted routes
from routes.currency import router as currency_router
from routes.debt import router as debt_router
from routes.goals import router as goals_router
from routes.api_center import router as api_center_router
from routes.bve import router as bve_router
from routes.settings import router as settings_router
from routes.habits import router as habits_router
from routes.affiliate import router as affiliate_router, admin_affiliate_router
from routes.activity_feed import admin_activity_router
from routes.users import router as users_router
from routes.family import router as family_router, admin_family_router
from routes.rewards import router as rewards_router
from routes.forum import router as forum_router
from routes.publitio import router as publitio_router

__all__ = [
    "auth_router",
    "profit_router", 
    "trade_router",
    "admin_router",
    "general_router",
    "currency_router",
    "debt_router",
    "goals_router",
    "api_center_router",
    "bve_router",
    "settings_router",
    "habits_router",
    "affiliate_router",
    "admin_affiliate_router",
    "admin_activity_router",
    "users_router",
    "family_router",
    "admin_family_router",
    "rewards_router",
    "forum_router",
    "publitio_router",
]

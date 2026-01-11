"""Backend Routes Package

This package contains modular route definitions for the FastAPI application.
Each module handles a specific domain of the API.

Structure:
- auth.py: Authentication routes (register, login, password management)
- admin.py: Admin management routes (members, licenses, analytics)
- trade.py: Trading routes (signals, trade logs)
- profit.py: Financial routes (deposits, withdrawals, debts, goals)
- settings.py: Platform settings routes

Migration Status:
- Routes are currently defined in server.py
- This package shows the target structure for modular routes
- To complete migration:
  1. Create a database module (db.py) with connection and collections
  2. Move helper functions to utils/
  3. Implement routes in each module
  4. Update server.py to import and include routers

Example usage in server.py:
```python
from routes import auth, admin, trade, profit, settings

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(trade.router, prefix="/api")
app.include_router(profit.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
```
"""

from .auth import router as auth_router
from .admin import router as admin_router
from .trade import router as trade_router
from .profit import router as profit_router
from .settings import router as settings_router

__all__ = [
    "auth_router",
    "admin_router", 
    "trade_router",
    "profit_router",
    "settings_router"
]

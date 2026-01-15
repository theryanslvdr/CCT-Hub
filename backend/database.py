"""
Database connection and collections module.
Provides a centralized database connection for all routes.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

# Database configuration
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "crosscurrent_finance")

# Global database client and instance
_client: Optional[AsyncIOMotorClient] = None
_db = None


async def get_database():
    """Get the database instance. Creates connection if not exists."""
    global _client, _db
    
    if _db is None:
        _client = AsyncIOMotorClient(MONGO_URL)
        _db = _client[DB_NAME]
    
    return _db


async def close_database():
    """Close the database connection."""
    global _client, _db
    
    if _client is not None:
        _client.close()
        _client = None
        _db = None


class Database:
    """
    Database wrapper class that provides access to collections.
    Use this in route modules for consistent database access.
    
    Example usage:
        from database import db
        
        async def some_route():
            users = await db.users.find({}).to_list(100)
    """
    
    def __init__(self):
        self._db = None
    
    async def connect(self):
        """Connect to the database."""
        self._db = await get_database()
        return self._db
    
    async def disconnect(self):
        """Disconnect from the database."""
        await close_database()
        self._db = None
    
    @property
    def client(self):
        """Get the Motor client."""
        global _client
        return _client
    
    @property
    def users(self):
        """Users collection."""
        return self._db.users if self._db else None
    
    @property
    def deposits(self):
        """Deposits collection."""
        return self._db.deposits if self._db else None
    
    @property
    def trade_logs(self):
        """Trade logs collection."""
        return self._db.trade_logs if self._db else None
    
    @property
    def signals(self):
        """Trading signals collection."""
        return self._db.signals if self._db else None
    
    @property
    def licenses(self):
        """Licenses collection."""
        return self._db.licenses if self._db else None
    
    @property
    def license_invites(self):
        """License invites collection."""
        return self._db.license_invites if self._db else None
    
    @property
    def licensee_transactions(self):
        """Licensee transactions collection."""
        return self._db.licensee_transactions if self._db else None
    
    @property
    def commissions(self):
        """Commissions collection."""
        return self._db.commissions if self._db else None
    
    @property
    def debts(self):
        """Debts collection."""
        return self._db.debts if self._db else None
    
    @property
    def goals(self):
        """Goals collection."""
        return self._db.goals if self._db else None
    
    @property
    def notifications(self):
        """Notifications collection."""
        return self._db.notifications if self._db else None
    
    @property
    def settings(self):
        """Platform settings collection."""
        return self._db.settings if self._db else None
    
    @property
    def announcements(self):
        """Announcements collection."""
        return self._db.announcements if self._db else None
    
    @property
    def trade_change_requests(self):
        """Trade change requests collection."""
        return self._db.trade_change_requests if self._db else None
    
    @property
    def signals_archive(self):
        """Archived signals collection."""
        return self._db.signals_archive if self._db else None
    
    @property
    def trades_archive(self):
        """Archived trades collection."""
        return self._db.trades_archive if self._db else None
    
    @property
    def bve_signals(self):
        """BVE signals collection."""
        return self._db.bve_signals if self._db else None
    
    @property
    def bve_sessions(self):
        """BVE sessions collection."""
        return self._db.bve_sessions if self._db else None
    
    @property
    def bve_trade_logs(self):
        """BVE trade logs collection."""
        return self._db.bve_trade_logs if self._db else None


# Create a global database instance
db = Database()

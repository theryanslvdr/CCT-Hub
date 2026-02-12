"""
Shared dependencies for all route modules.
Import from here instead of server.py for cross-module usage.
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import bcrypt
import os
from datetime import datetime, timezone, timedelta

# These are set by server.py at startup via init()
db = None
JWT_SECRET = None
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

ROLE_HIERARCHY = {
    'member': 1,
    'basic_admin': 2,
    'super_admin': 3,
    'master_admin': 4,
}

SUPER_ADMIN_SECRET = ''
MASTER_ADMIN_SECRET = ''
SUPER_ADMIN_BYPASS = ''


def init(database, jwt_secret, super_admin_secret='', master_admin_secret='', super_admin_bypass=''):
    """Called once from server.py to inject shared state."""
    global db, JWT_SECRET, SUPER_ADMIN_SECRET, MASTER_ADMIN_SECRET, SUPER_ADMIN_BYPASS
    db = database
    JWT_SECRET = jwt_secret
    SUPER_ADMIN_SECRET = super_admin_secret
    MASTER_ADMIN_SECRET = master_admin_secret
    SUPER_ADMIN_BYPASS = super_admin_bypass


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
    admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
    if user.get("role") not in admin_roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_admin(user: dict = Depends(get_current_user)):
    admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
    if user.get("role") not in admin_roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_super_admin(user: dict = Depends(get_current_user)):
    if user.get("role") not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user


async def require_master_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "master_admin":
        raise HTTPException(status_code=403, detail="Master admin access required")
    return user


async def require_super_or_master_admin(user: dict = Depends(get_current_user)):
    if user.get("role") not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Super admin or master admin access required")
    return user

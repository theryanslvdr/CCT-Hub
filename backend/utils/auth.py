"""Authentication utility functions"""
import os
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

# JWT Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 1440))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    'member': 1,        # Normal member - modular dashboard access
    'basic_admin': 2,   # Can manage members, signals, assist with resets
    'super_admin': 3,   # Full access except hidden features
    'master_admin': 4,  # Full access including hidden features
}

# Secret codes for admin registration
SUPER_ADMIN_SECRET = os.environ.get('SUPER_ADMIN_SECRET', 'CROSSCURRENT2024')
MASTER_ADMIN_SECRET = os.environ.get('MASTER_ADMIN_SECRET', 'CrossCurrentGODSEYE')
SUPER_ADMIN_BYPASS = os.environ.get('SUPER_ADMIN_BYPASS', 'SUPER_ADMIN_BYPASS')


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials"
        )


def get_role_level(role: str) -> int:
    """Get the hierarchy level for a role"""
    return ROLE_HIERARCHY.get(role, 1)


def check_role_permission(user_role: str, required_role: str) -> bool:
    """Check if user has sufficient role permissions"""
    return get_role_level(user_role) >= get_role_level(required_role)


def get_role_from_secret_code(secret_code: Optional[str]) -> Optional[str]:
    """Determine admin role from secret code"""
    if secret_code == MASTER_ADMIN_SECRET:
        return 'master_admin'
    elif secret_code == SUPER_ADMIN_SECRET:
        return 'super_admin'
    return None


def is_admin_role(role: str) -> bool:
    """Check if the role is any type of admin"""
    return role in ['basic_admin', 'super_admin', 'master_admin']


def is_master_admin(role: str) -> bool:
    """Check if the role is master admin"""
    return role == 'master_admin'


def is_super_admin_or_above(role: str) -> bool:
    """Check if the role is super admin or master admin"""
    return role in ['super_admin', 'master_admin']

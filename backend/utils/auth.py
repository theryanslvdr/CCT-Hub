import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone

JWT_SECRET = os.environ.get("JWT_SECRET", "crosscurrent-finance-secret-key-2024")
JWT_ALGORITHM = "HS256"
SUPER_ADMIN_SECRET = os.environ.get("SUPER_ADMIN_SECRET", "CROSSCURRENT_SUPER_ADMIN_2024")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

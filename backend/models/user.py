"""User-related Pydantic models"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


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
    allowed_dashboards: Optional[List[str]] = None
    license_type: Optional[str] = None
    trading_start_date: Optional[str] = None
    trading_type: Optional[str] = None
    referral_code: Optional[str] = None
    referred_by: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    lot_size: Optional[float] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class VerifyPasswordRequest(BaseModel):
    password: str


class HeartbeatVerifyRequest(BaseModel):
    email: str


class SetPasswordRequest(BaseModel):
    email: str
    password: str


class SecretUpgradeRequest(BaseModel):
    user_id: str
    new_role: str
    secret_code: str


class RoleUpgrade(BaseModel):
    user_id: str
    new_role: str  # basic_admin, admin, super_admin
    secret_code: Optional[str] = None


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    lot_size: Optional[float] = None
    allowed_dashboards: Optional[List[str]] = None  # For super admin to assign dashboards
    role: Optional[str] = None  # For master admin to change roles
    email: Optional[str] = None  # For master admin to change email


class TempPasswordSet(BaseModel):
    temp_password: str

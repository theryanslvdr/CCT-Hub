from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class RoleUpgrade(BaseModel):
    user_id: str
    new_role: str  # basic_admin, admin, super_admin
    secret_code: Optional[str] = None

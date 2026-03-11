"""Authentication routes - extracted from server.py"""
import uuid
import os
import httpx
import logging
import requests
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

import deps
from models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from helpers import (
    create_admin_notification, create_user_notification, verify_heartbeat_user,
    verify_heartbeat_user_exists, send_push_notification
)
from services import websocket_manager

try:
    from services.rewards_sync_service import sync_user_to_rewards_platform
except ImportError:
    async def sync_user_to_rewards_platform(*a, **kw): pass

logger = logging.getLogger("server")

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Request Models ───

class VerifyPasswordRequest(BaseModel):
    password: str

class ForceChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class HeartbeatVerifyRequest(BaseModel):
    email: EmailStr

class SetPasswordRequest(BaseModel):
    email: EmailStr
    password: str
    secret_code: Optional[str] = None

class SecretUpgradeRequest(BaseModel):
    secret_code: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    # Check if email exists
    existing = await deps.db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Verify Heartbeat membership and active status
    heartbeat_email = data.heartbeat_email or data.email
    heartbeat_result = await verify_heartbeat_user(heartbeat_email)
    
    if not heartbeat_result.get("exists"):
        raise HTTPException(
            status_code=403, 
            detail="You must be a Heartbeat community member to register. Please join the community first."
        )
    
    if not heartbeat_result.get("is_active"):
        reason = heartbeat_result.get("reason", "Account is not active")
        raise HTTPException(
            status_code=403,
            detail=f"Your Heartbeat account is deactivated. {reason}. Please contact support to reactivate your account."
        )
    
    # Determine role based on secret code
    role = "member"  # Default to normal member
    if data.secret_code:
        if data.secret_code == deps.MASTER_ADMIN_SECRET:
            role = "master_admin"
        elif data.secret_code == deps.SUPER_ADMIN_SECRET:
            role = "super_admin"
    
    # Default dashboards for normal members
    default_dashboards = ["dashboard", "profit_tracker", "trade_monitor", "profile"]
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email.lower(),
        "password": deps.hash_password(data.password),
        "full_name": data.full_name,
        "heartbeat_email": heartbeat_email.lower(),
        "role": role,
        "profile_picture": None,
        "lot_size": 0.01,
        "timezone": "UTC",
        "allowed_dashboards": default_dashboards if role == "member" else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.users.insert_one(user)
    
    # Send notification to all admins about new registration
    await create_admin_notification(
        notification_type="new_user",
        title="New User Registered",
        message=f"{data.full_name} has joined the platform",
        user_id=user_id,
        user_name=data.full_name,
        metadata={"email": data.email.lower(), "role": role}
    )
    
    # Send notification to all members about new member (community notification)
    await create_member_notification(
        notification_type="new_member",
        title="New Member Joined",
        message=f"Welcome {data.full_name} to the community!",
        triggered_by_id=user_id,
        triggered_by_name=data.full_name,
        metadata={"email": data.email.lower()}
    )
    
    # Send email notification to admins
    try:
        from services.email_service import send_registration_notification_to_admins
        await send_registration_notification_to_admins(data.full_name, data.email)
    except Exception as e:
        print(f"Failed to send email notification: {e}")
    
    # Auto-sync new user to rewards platform
    try:
        from services.rewards_sync_service import sync_user_to_rewards
        await sync_user_to_rewards(deps.db, user)
        logger.info(f"Auto-synced new user {data.email} to rewards platform")
    except Exception as e:
        logger.warning(f"Rewards sync failed for new user {data.email}: {e}")
    
    token = deps.create_token(user_id, data.email, role)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=data.email,
            full_name=data.full_name,
            role=role,
            created_at=datetime.fromisoformat(user["created_at"]),
            allowed_dashboards=user.get("allowed_dashboards"),
            license_type=user.get("license_type")
        )
    )


@router.post("/login")
async def login(data: UserLogin):
    user = await deps.db.users.find_one({"email": data.email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not deps.verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is deactivated locally
    if user.get("is_deactivated"):
        raise HTTPException(
            status_code=403, 
            detail="Your account has been deactivated. Please contact your inviter to reactivate your account."
        )
    
    # Skip Heartbeat verification for admins and licensees
    admin_roles = ["basic_admin", "admin", "super_admin", "master_admin"]
    is_licensee = user.get("license_type") is not None
    
    # For licensees, check if their license is still active
    if is_licensee:
        active_license = await deps.db.licenses.find_one({
            "user_id": user["id"], 
            "is_active": True
        }, {"_id": 0})
        
        if not active_license:
            # License has been revoked or deleted
            raise HTTPException(
                status_code=403, 
                detail="Your license has been revoked or expired. Please contact the administrator to renew your license."
            )
    elif user.get("role") not in admin_roles:
        # Non-admin, non-licensee - check Heartbeat membership AND active status
        heartbeat_email = user.get("heartbeat_email", user["email"])
        heartbeat_result = await verify_heartbeat_user(heartbeat_email)
        
        if not heartbeat_result.get("exists"):
            raise HTTPException(
                status_code=403, 
                detail="Your Heartbeat membership could not be verified. Please ensure you're still a community member."
            )
        
        if not heartbeat_result.get("is_active"):
            reason = heartbeat_result.get("reason", "Account is not active")
            raise HTTPException(
                status_code=403,
                detail=f"Your Heartbeat account has been deactivated. {reason}. Please contact support to regain access."
            )
    
    token = deps.create_token(user["id"], user["email"], user["role"])
    
    response_data = {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "created_at": user["created_at"] if isinstance(user["created_at"], str) else user["created_at"].isoformat(),
            "profile_picture": user.get("profile_picture"),
            "lot_size": user.get("lot_size"),
            "timezone": user.get("timezone", "UTC"),
            "allowed_dashboards": user.get("allowed_dashboards"),
            "license_type": user.get("license_type"),
            "referred_by": user.get("referred_by"),
        },
    }
    
    if user.get("must_change_password"):
        response_data["must_change_password"] = True
    
    return response_data


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(deps.get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"],
        profile_picture=user.get("profile_picture"),
        lot_size=user.get("lot_size"),
        timezone=user.get("timezone", "UTC"),
        allowed_dashboards=user.get("allowed_dashboards"),
        license_type=user.get("license_type"),
        trading_start_date=user.get("trading_start_date"),
        trading_type=user.get("trading_type"),
        referral_code=user.get("referral_code"),
        referred_by=user.get("referred_by"),
    )


@router.post("/verify-password")
async def verify_user_password(data: VerifyPasswordRequest, user: dict = Depends(deps.get_current_user)):
    """Verify the current user's password"""
    db_user = await deps.db.users.find_one({"id": user["id"]})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_valid = deps.verify_password(data.password, db_user["password"])
    return {"valid": is_valid}


@router.post("/force-change-password")
async def force_change_password(data: ForceChangePasswordRequest, user: dict = Depends(deps.get_current_user)):
    """Change password for a user who was assigned a temporary password"""
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    new_hash = deps.hash_password(data.new_password)
    await deps.db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password": new_hash, "must_change_password": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Password changed successfully"}


@router.post("/verify-heartbeat")
async def verify_heartbeat_membership(data: HeartbeatVerifyRequest):
    """Verify if email is a Heartbeat member and return user info if exists"""
    email = data.email.lower().strip()
    
    # Get Heartbeat API key from settings, fallback to environment variable
    settings = await deps.db.platform_settings.find_one({}, {"_id": 0})
    heartbeat_api_key = settings.get("heartbeat_api_key") if settings else None
    
    # Fallback to environment variable if not in settings
    if not heartbeat_api_key:
        heartbeat_api_key = os.environ.get("HEARTBEAT_API_KEY")
    
    if not heartbeat_api_key:
        raise HTTPException(status_code=500, detail="Heartbeat integration not configured. Please add your Heartbeat API key in Admin Settings > Integrations.")
    
    # Verify with Heartbeat using the query parameter format
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.heartbeat.chat/v0/users",
                headers={"Authorization": f"Bearer {heartbeat_api_key}"},
                params={"email": email},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Handle both list and dict responses
                users = []
                if isinstance(data, list):
                    users = data
                else:
                    users = data.get("users", data.get("data", []))
                
                # Find the user with matching email
                heartbeat_user = None
                if isinstance(users, list):
                    for u in users:
                        if isinstance(u, dict) and u.get("email", "").lower() == email.lower():
                            heartbeat_user = u
                            break
                
                if heartbeat_user:
                    heartbeat_user_id = heartbeat_user.get("id")
                    
                    # Check for deactivation status
                    status = heartbeat_user.get("status", "").lower() if heartbeat_user.get("status") else ""
                    is_active = heartbeat_user.get("is_active", heartbeat_user.get("active", True))
                    is_suspended = heartbeat_user.get("suspended", heartbeat_user.get("is_suspended", False))
                    is_banned = heartbeat_user.get("banned", heartbeat_user.get("is_banned", False))
                    
                    is_deactivated = (
                        status in ["deactivated", "suspended", "banned", "deleted", "inactive", "disabled"] or
                        is_suspended or is_banned or is_active == False
                    )
                    
                    if is_deactivated:
                        return {
                            "verified": False,
                            "is_deactivated": True,
                            "user": None,
                            "message": "Your Heartbeat account has been deactivated. Please contact support to regain access."
                        }
                    
                    # Check if user already exists in our DB
                    existing_user = await deps.db.users.find_one({"email": email}, {"_id": 0, "id": 1, "full_name": 1, "password": 1})
                    
                    return {
                        "verified": True,
                        "is_deactivated": False,
                        "user": {
                            "email": email,
                            "full_name": heartbeat_user.get("name", email.split('@')[0]),
                            "heartbeat_id": heartbeat_user_id,
                            "has_password": existing_user is not None and existing_user.get("password") is not None
                        }
                    }
            
            return {"verified": False, "is_deactivated": False, "user": None}
    except Exception as e:
        print(f"Heartbeat verification error: {e}")
        return {"verified": False, "is_deactivated": False, "user": None}


@router.post("/set-password")
async def set_password_for_member(data: SetPasswordRequest):
    """Set password for a verified Heartbeat member"""
    email = data.email.lower().strip()
    password = data.password  # Store password before any overwrites
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Verify Heartbeat membership first - check settings then fallback to env
    settings = await deps.db.platform_settings.find_one({}, {"_id": 0})
    heartbeat_api_key = settings.get("heartbeat_api_key") if settings else None
    
    # Fallback to environment variable if not in settings
    if not heartbeat_api_key:
        heartbeat_api_key = os.environ.get("HEARTBEAT_API_KEY")
    
    if not heartbeat_api_key:
        raise HTTPException(status_code=500, detail="Heartbeat integration not configured. Please add your Heartbeat API key in Admin Settings > Integrations.")
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.heartbeat.chat/v0/users",
                headers={"Authorization": f"Bearer {heartbeat_api_key}"},
                params={"email": email},
                timeout=10.0
            )
            
            if response.status_code == 200:
                hb_response = response.json()
                # Handle both list and dict responses
                users = []
                if isinstance(hb_response, list):
                    users = hb_response
                else:
                    users = hb_response.get("users", hb_response.get("data", []))
                
                # Find the user with matching email
                heartbeat_user = None
                if isinstance(users, list):
                    for u in users:
                        if isinstance(u, dict) and u.get("email", "").lower() == email.lower():
                            heartbeat_user = u
                            break
                
                if not heartbeat_user:
                    raise HTTPException(status_code=400, detail="Email not verified with Heartbeat")
                
                heartbeat_user_id = heartbeat_user.get("id")
                full_name = heartbeat_user.get("name", email.split('@')[0])
            else:
                raise HTTPException(status_code=400, detail="Failed to verify Heartbeat membership")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Heartbeat verification error: {e}")
        raise HTTPException(status_code=400, detail="Failed to verify Heartbeat membership")
    
    # Hash password
    hashed_password = deps.hash_password(password)
    
    # Check if user exists
    existing_user = await deps.db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        # Update existing user's password
        await deps.db.users.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )
        return {"message": "Password updated successfully"}
    else:
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = {
            "id": user_id,
            "email": email,
            "password": hashed_password,
            "full_name": full_name,
            "role": "member",
            "heartbeat_user_id": heartbeat_user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_suspended": False,
            "lot_size": 0.01,
            "timezone": "Asia/Manila",
            "allowed_dashboards": ["dashboard", "profit_tracker", "trade_monitor", "habits", "affiliate", "profile"]
        }
        await deps.db.users.insert_one(new_user)
        return {"message": "Account created successfully"}


@router.post("/secret-upgrade")
async def secret_upgrade(data: SecretUpgradeRequest, user: dict = Depends(deps.get_current_user)):
    """Secret endpoint to upgrade user role with bypass code (triggered by 10x Settings click)"""
    
    # Only allow upgrade to super_admin
    if data.new_role != "super_admin":
        raise HTTPException(status_code=400, detail="Invalid upgrade request")
    
    # Verify bypass code
    if data.secret_code != deps.SUPER_ADMIN_BYPASS:
        raise HTTPException(status_code=403, detail="Invalid secret code")
    
    # User can only upgrade themselves
    if data.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="Can only upgrade yourself")
    
    # Don't downgrade master_admin
    if user["role"] == "master_admin":
        raise HTTPException(status_code=400, detail="Master admin cannot be downgraded")
    
    # Upgrade the user
    await deps.db.users.update_one(
        {"id": user["id"]},
        {"$set": {"role": "super_admin", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Successfully upgraded to Super Admin"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Request a password reset token for the given email."""
    user = await deps.db.users.find_one({"email": data.email.strip().lower()}, {"_id": 0})
    if not user:
        # Return success even if email not found (security best practice)
        return {"message": "If that email exists, a reset link has been sent."}
    
    reset_token = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    
    await deps.db.password_resets.insert_one({
        "user_id": user["id"],
        "email": user["email"],
        "token": reset_token,
        "expires_at": expires_at,
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send password reset email via Emailit
    try:
        from services.email_service import send_email, get_password_reset_email
        
        # Build reset link using the frontend URL
        frontend_url = os.environ.get("FRONTEND_URL", "")
        if not frontend_url:
            # Try to get from request headers or use known URL
            settings = await deps.db.platform_settings.find_one({}, {"_id": 0})
            frontend_url = (settings or {}).get("frontend_url", "https://crosscur.rent")
        
        reset_link = f"{frontend_url}/login?reset_token={reset_token}"
        email_content = get_password_reset_email(reset_link, user.get("full_name", ""))
        
        result = await send_email(
            db=deps.db,
            to_email=user["email"],
            subject=email_content["subject"],
            html_content=email_content["html"],
            text_content=email_content["text"],
            template_type="password_reset",
            metadata={"user_id": user["id"]}
        )
        
        if result.get("success"):
            logger.info(f"Password reset email sent to {user['email']}")
        else:
            logger.warning(f"Failed to send reset email: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
    
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Reset password using a valid reset token."""
    reset_record = await deps.db.password_resets.find_one(
        {"token": data.token, "used": False},
        {"_id": 0}
    )
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    if datetime.fromisoformat(reset_record["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    hashed = deps.hash_password(data.new_password)
    await deps.db.users.update_one(
        {"id": reset_record["user_id"]},
        {"$set": {
            "password": hashed,
            "must_change_password": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await deps.db.password_resets.update_one(
        {"token": data.token},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Password has been reset successfully"}


@router.get("/license-invite/{code}")
async def validate_license_invite(code: str):
    """Validate a license invite code (public endpoint for registration page)"""
    invite = await deps.db.license_invites.find_one({"code": code}, {"_id": 0})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if invite.get("is_revoked"):
        raise HTTPException(status_code=400, detail="This invite has been revoked")
    
    # Check expiry
    if invite.get("valid_until"):
        valid_until = datetime.fromisoformat(invite["valid_until"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > valid_until:
            raise HTTPException(status_code=400, detail="This invite has expired")
    
    # Check uses
    if invite.get("uses_count", 0) >= invite.get("max_uses", 1):
        raise HTTPException(status_code=400, detail="This invite has reached its maximum number of uses")
    
    return {
        "valid": True,
        "license_type": invite["license_type"],
        "starting_amount": invite["starting_amount"],
        "invitee_name": invite.get("invitee_name"),
        "invitee_email": invite.get("invitee_email"),
        "valid_until": invite.get("valid_until"),
        "notes": invite.get("notes")
    }


@router.post("/register-with-license")
async def register_with_license(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    invite_code: str = Form(...)
):
    """Register a new user with a license invite code"""
    # Validate invite
    invite = await deps.db.license_invites.find_one({"code": invite_code}, {"_id": 0})
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if invite.get("is_revoked"):
        raise HTTPException(status_code=400, detail="This invite has been revoked")
    
    if invite.get("valid_until"):
        valid_until = datetime.fromisoformat(invite["valid_until"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > valid_until:
            raise HTTPException(status_code=400, detail="This invite has expired")
    
    if invite.get("uses_count", 0) >= invite.get("max_uses", 1):
        raise HTTPException(status_code=400, detail="This invite has reached its maximum number of uses")
    
    # Check if email already exists
    existing = await deps.db.users.find_one({"email": email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    new_user = {
        "id": user_id,
        "email": email.lower(),
        "password": hashed_password.decode('utf-8'),
        "full_name": full_name,
        "role": "member",
        "allowed_dashboards": ["dashboard", "profit_tracker", "trade_monitor", "habits", "affiliate", "profile"],
        "timezone": "Asia/Manila",
        "lot_size": 0.01,
        "is_verified": False,
        "is_suspended": False,
        "license_invite_code": invite_code,
        "license_type": invite["license_type"],
        "has_seen_welcome": False,  # Track if licensee has seen welcome screen
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await deps.db.users.insert_one(new_user)
    
    # Determine effective start date - use invite's effective_start_date or today
    effective_start_date = invite.get("effective_start_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Create the actual license
    license_id = str(uuid.uuid4())
    license_doc = {
        "id": license_id,
        "user_id": user_id,
        "license_type": invite["license_type"],
        "starting_amount": invite["starting_amount"],
        "current_amount": invite["starting_amount"],  # Initialize current_amount
        "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "effective_start_date": effective_start_date,  # When trading projections start
        "notes": f"Created via invite: {invite_code}",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": invite.get("created_by", "system")
    }
    
    await deps.db.licenses.insert_one(license_doc)
    
    # Increment invite uses count
    await deps.db.license_invites.update_one(
        {"code": invite_code},
        {"$inc": {"uses_count": 1}}
    )
    
    # Generate token
    token = deps.create_token(user_id, email.lower(), "member")
    
    # Remove password and _id from response
    del new_user["password"]
    if "_id" in new_user:
        del new_user["_id"]
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user,
        "license": {
            "type": invite["license_type"],
            "starting_amount": invite["starting_amount"]
        }
    }

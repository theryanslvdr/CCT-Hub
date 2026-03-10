"""Onboarding Checklist & Invite System Routes.
7-step onboarding flow that gates platform access until complete.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, List
import logging

import deps
from deps import get_current_user

logger = logging.getLogger("server")

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

ONBOARDING_STEPS = [
    {
        "step": 1,
        "key": "heartbeat_registered",
        "title": "Register in Heartbeat",
        "description": "Create your Heartbeat account — this validates your email for all platforms.",
        "external_url": None,
        "auto_verified": False,
    },
    {
        "step": 2,
        "key": "merin_registered",
        "title": "Register in Merin",
        "description": "Sign up on Merin Global Trading using your inviter's referral code. Save your own referral code.",
        "external_url_template": "https://www.meringlobaltrading.com/#/pages/login/regist?code={inviter_code}&lang=en_US",
        "auto_verified": False,
    },
    {
        "step": 3,
        "key": "hub_registered",
        "title": "Register in the Hub",
        "description": "Create your CrossCurrent Hub account (validated by Heartbeat).",
        "external_url": None,
        "auto_verified": True,
    },
    {
        "step": 4,
        "key": "exchange_verified",
        "title": "Register & Verify Exchange Account",
        "description": "Create your OKX or Coins.ph account and complete full verification.",
        "external_url": None,
        "auto_verified": False,
    },
    {
        "step": 5,
        "key": "tutorials_completed",
        "title": "Complete Tutorials",
        "description": "Go through the Depositing, Withdrawal, and Trading tutorials in Heartbeat.",
        "external_url": None,
        "auto_verified": False,
    },
    {
        "step": 6,
        "key": "live_trade_scheduled",
        "title": "Schedule a Live Trade",
        "description": "Schedule your first live trade session with the team.",
        "external_url": None,
        "auto_verified": False,
    },
    {
        "step": 7,
        "key": "rewards_onboarded",
        "title": "Rewards Platform Onboarding",
        "description": "Login to the Rewards platform to auto-create your account and complete the tutorial.",
        "external_url": None,
        "auto_verified": False,
    },
]


class StepUpdate(BaseModel):
    step_key: str
    completed: bool = True
    merin_referral_code: Optional[str] = None


class MerinCodeUpdate(BaseModel):
    merin_referral_code: str


@router.get("/checklist")
async def get_onboarding_checklist(user: dict = Depends(get_current_user)):
    """Get the user's onboarding checklist with completion status."""
    db = deps.db

    checklist = await db.onboarding_checklists.find_one(
        {"user_id": user["id"]}, {"_id": 0}
    )
    if not checklist:
        checklist = {
            "user_id": user["id"],
            "completed_steps": ["hub_registered"],
            "all_completed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.onboarding_checklists.insert_one(checklist)
        checklist.pop("_id", None)

    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "merin_referral_code": 1, "invited_by": 1, "referral_code": 1})
    inviter_code = None
    if user_doc and user_doc.get("invited_by"):
        inviter = await db.users.find_one({"id": user_doc["invited_by"]}, {"_id": 0, "merin_referral_code": 1, "referral_code": 1})
        if inviter:
            inviter_code = inviter.get("merin_referral_code") or inviter.get("referral_code")

    steps = []
    for s in ONBOARDING_STEPS:
        step = {**s}
        step["completed"] = s["key"] in checklist.get("completed_steps", [])
        if s["key"] == "merin_registered" and inviter_code:
            step["external_url"] = s["external_url_template"].format(inviter_code=inviter_code)
        step.pop("external_url_template", None)
        steps.append(step)

    return {
        "steps": steps,
        "completed_count": len(checklist.get("completed_steps", [])),
        "total_count": len(ONBOARDING_STEPS),
        "all_completed": checklist.get("all_completed", False),
        "merin_referral_code": user_doc.get("merin_referral_code") or user_doc.get("referral_code") if user_doc else None,
    }


@router.put("/checklist/step")
async def update_checklist_step(data: StepUpdate, user: dict = Depends(get_current_user)):
    """Mark a step as complete/incomplete."""
    db = deps.db

    valid_keys = [s["key"] for s in ONBOARDING_STEPS]
    if data.step_key not in valid_keys:
        raise HTTPException(status_code=400, detail="Invalid step key")

    checklist = await db.onboarding_checklists.find_one({"user_id": user["id"]}, {"_id": 0})
    if not checklist:
        checklist = {
            "user_id": user["id"],
            "completed_steps": ["hub_registered"],
            "all_completed": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    completed = set(checklist.get("completed_steps", []))
    if data.completed:
        completed.add(data.step_key)
    else:
        completed.discard(data.step_key)
    completed.add("hub_registered")

    if data.merin_referral_code and data.step_key == "merin_registered":
        code = data.merin_referral_code.strip().upper()
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"merin_referral_code": code}}
        )

    all_done = all(s["key"] in completed for s in ONBOARDING_STEPS)

    await db.onboarding_checklists.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "completed_steps": list(completed),
            "all_completed": all_done,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    if all_done:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"onboarding_completed": True}}
        )

    return {
        "completed_steps": list(completed),
        "all_completed": all_done,
        "completed_count": len(completed),
        "total_count": len(ONBOARDING_STEPS),
    }


@router.put("/merin-code")
async def update_merin_code(data: MerinCodeUpdate, user: dict = Depends(get_current_user)):
    """Update the user's Merin referral code."""
    db = deps.db
    code = data.merin_referral_code.strip().upper()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"merin_referral_code": code}}
    )
    return {"merin_referral_code": code}


@router.get("/invite-link")
async def get_invite_link(user: dict = Depends(get_current_user)):
    """Generate the Merin invite link with the user's referral code."""
    db = deps.db
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "merin_referral_code": 1, "referral_code": 1, "full_name": 1})

    code = user_doc.get("merin_referral_code") or user_doc.get("referral_code")
    if not code:
        raise HTTPException(status_code=400, detail="Please set your Merin referral code first")

    return {
        "merin_link": f"https://www.meringlobaltrading.com/#/pages/login/regist?code={code}&lang=en_US",
        "referral_code": code,
        "member_name": user_doc.get("full_name", ""),
    }


# ── Cross-Platform API (for external onboarding site) ────────

@router.get("/status/{user_id}")
async def get_onboarding_status_external(user_id: str):
    """Public endpoint for external onboarding site to check user status."""
    db = deps.db
    checklist = await db.onboarding_checklists.find_one(
        {"user_id": user_id}, {"_id": 0}
    )
    if not checklist:
        return {"found": False, "all_completed": False, "completed_steps": []}

    return {
        "found": True,
        "all_completed": checklist.get("all_completed", False),
        "completed_steps": checklist.get("completed_steps", []),
        "completed_count": len(checklist.get("completed_steps", [])),
        "total_count": len(ONBOARDING_STEPS),
    }


@router.post("/complete-step-external")
async def complete_step_external(data: dict):
    """External endpoint for onboarding site to mark steps as complete.
    Requires user_email and step_key."""
    db = deps.db
    email = data.get("email")
    step_key = data.get("step_key")

    if not email or not step_key:
        raise HTTPException(status_code=400, detail="email and step_key required")

    valid_keys = [s["key"] for s in ONBOARDING_STEPS]
    if step_key not in valid_keys:
        raise HTTPException(status_code=400, detail="Invalid step key")

    user = await db.users.find_one({"email": email}, {"_id": 0, "id": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    checklist = await db.onboarding_checklists.find_one({"user_id": user["id"]}, {"_id": 0})
    completed = set(checklist.get("completed_steps", [])) if checklist else {"hub_registered"}
    completed.add(step_key)

    all_done = all(s["key"] in completed for s in ONBOARDING_STEPS)

    await db.onboarding_checklists.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "completed_steps": list(completed),
            "all_completed": all_done,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    if all_done:
        await db.users.update_one({"id": user["id"]}, {"$set": {"onboarding_completed": True}})

    return {"completed_steps": list(completed), "all_completed": all_done}

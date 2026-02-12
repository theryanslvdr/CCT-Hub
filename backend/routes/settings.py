"""Platform settings routes."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import cloudinary
import cloudinary.uploader

from deps import db, require_admin

router = APIRouter(prefix="/settings", tags=["Settings"])


class PlatformSettings(BaseModel):
    platform_name: str = "CrossCurrent"
    tagline: str = "Finance Center"
    site_title: str = "CrossCurrent Finance Center"
    site_description: str = "Trading profit management platform"
    favicon_url: Optional[str] = None
    logo_url: Optional[str] = None
    og_image_url: Optional[str] = None
    primary_color: str = "#3B82F6"
    accent_color: str = "#06B6D4"
    hide_emergent_badge: bool = False


@router.get("/platform")
async def get_platform_settings():
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    if not settings:
        settings = PlatformSettings().model_dump()
    return settings


@router.put("/platform")
async def update_platform_settings(data: PlatformSettings, user: dict = Depends(require_admin)):
    await db.platform_settings.update_one(
        {},
        {"$set": data.model_dump()},
        upsert=True,
    )
    return {"message": "Settings updated"}


@router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="crosscurrent/branding",
            public_id="logo",
            overwrite=True,
        )
        url = result.get("secure_url")
        await db.platform_settings.update_one(
            {},
            {"$set": {"logo_url": url}},
            upsert=True,
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload-favicon")
async def upload_favicon(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="crosscurrent/branding",
            public_id="favicon",
            overwrite=True,
        )
        url = result.get("secure_url")
        await db.platform_settings.update_one(
            {},
            {"$set": {"favicon_url": url}},
            upsert=True,
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/email-templates")
async def get_email_templates(user: dict = Depends(require_admin)):
    templates = await db.email_templates.find({}, {"_id": 0}).to_list(100)
    return templates


@router.put("/email-templates/{template_id}")
async def update_email_template(template_id: str, data: dict, user: dict = Depends(require_admin)):
    await db.email_templates.update_one(
        {"id": template_id},
        {"$set": data},
        upsert=True,
    )
    return {"message": "Template updated"}

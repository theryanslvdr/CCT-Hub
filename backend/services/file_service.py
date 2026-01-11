"""File upload service using Cloudinary"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


async def get_cloudinary_config(db) -> Optional[Dict[str, str]]:
    """Get Cloudinary configuration from platform settings or environment"""
    settings = await db.platform_settings.find_one({}, {"_id": 0})
    
    cloud_name = settings.get("cloudinary_cloud_name") if settings else None
    api_key = settings.get("cloudinary_api_key") if settings else None
    api_secret = settings.get("cloudinary_api_secret") if settings else None
    
    # Fallback to environment variables
    if not cloud_name:
        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
    if not api_key:
        api_key = os.environ.get("CLOUDINARY_API_KEY")
    if not api_secret:
        api_secret = os.environ.get("CLOUDINARY_API_SECRET")
    
    if all([cloud_name, api_key, api_secret]):
        return {
            "cloud_name": cloud_name,
            "api_key": api_key,
            "api_secret": api_secret
        }
    
    return None


def configure_cloudinary(config: Dict[str, str]):
    """Configure cloudinary with credentials"""
    cloudinary.config(
        cloud_name=config["cloud_name"],
        api_key=config["api_key"],
        api_secret=config["api_secret"],
        secure=True
    )


async def upload_file(
    db,
    file_content: bytes,
    filename: str,
    content_type: str,
    folder: str = "uploads",
    user_id: Optional[str] = None,
    file_type: str = "general"
) -> Dict[str, Any]:
    """
    Upload a file to Cloudinary
    
    Args:
        db: MongoDB database instance
        file_content: File content as bytes
        filename: Original filename
        content_type: MIME type of the file
        folder: Cloudinary folder to store the file
        user_id: ID of the user uploading the file
        file_type: Type of file (profile_picture, deposit_screenshot, etc.)
    
    Returns:
        Dict with upload result including URL and public_id
    """
    config = await get_cloudinary_config(db)
    
    if not config:
        logger.warning("Cloudinary not configured")
        return {"success": False, "error": "File upload service not configured"}
    
    configure_cloudinary(config)
    
    try:
        # Generate unique public_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        public_id = f"{file_type}_{timestamp}_{unique_id}"
        
        # Determine resource type
        if content_type.startswith("image/"):
            resource_type = "image"
        elif content_type.startswith("video/"):
            resource_type = "video"
        else:
            resource_type = "raw"
        
        # Convert to base64 data URI
        b64_content = base64.b64encode(file_content).decode("utf-8")
        data_uri = f"data:{content_type};base64,{b64_content}"
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            data_uri,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=True,
            timeout=60
        )
        
        logger.info(f"File uploaded successfully: {result.get('public_id')}")
        
        # Store file reference in MongoDB
        file_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "filename": filename,
            "content_type": content_type,
            "file_type": file_type,
            "cloudinary_public_id": result.get("public_id"),
            "cloudinary_url": result.get("secure_url"),
            "cloudinary_resource_type": result.get("resource_type"),
            "file_size": result.get("bytes"),
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.file_uploads.insert_one(file_record)
        
        return {
            "success": True,
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "resource_type": result.get("resource_type"),
            "file_size": result.get("bytes"),
            "format": result.get("format")
        }
    
    except Exception as e:
        logger.error(f"Cloudinary upload error: {str(e)}")
        return {"success": False, "error": str(e)}


async def delete_file(db, public_id: str, resource_type: str = "image") -> Dict[str, Any]:
    """
    Delete a file from Cloudinary
    
    Args:
        db: MongoDB database instance
        public_id: Cloudinary public ID of the file
        resource_type: Type of resource (image, video, raw)
    
    Returns:
        Dict with deletion result
    """
    config = await get_cloudinary_config(db)
    
    if not config:
        logger.warning("Cloudinary not configured")
        return {"success": False, "error": "File upload service not configured"}
    
    configure_cloudinary(config)
    
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        
        if result.get("result") == "ok":
            # Remove from MongoDB
            await db.file_uploads.delete_one({"cloudinary_public_id": public_id})
            logger.info(f"File deleted successfully: {public_id}")
            return {"success": True, "message": "File deleted successfully"}
        else:
            return {"success": False, "error": "File not found or could not be deleted"}
    
    except Exception as e:
        logger.error(f"Cloudinary delete error: {str(e)}")
        return {"success": False, "error": str(e)}


async def get_user_files(db, user_id: str, file_type: Optional[str] = None) -> list:
    """
    Get all files uploaded by a user
    
    Args:
        db: MongoDB database instance
        user_id: ID of the user
        file_type: Optional filter by file type
    
    Returns:
        List of file records
    """
    query = {"user_id": user_id}
    if file_type:
        query["file_type"] = file_type
    
    files = await db.file_uploads.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return files


async def upload_profile_picture(db, user_id: str, file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
    """Upload a profile picture for a user"""
    result = await upload_file(
        db=db,
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        folder="profile_pictures",
        user_id=user_id,
        file_type="profile_picture"
    )
    
    if result.get("success"):
        # Update user's profile picture URL
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"profile_picture": result.get("url")}}
        )
    
    return result


async def upload_deposit_screenshot(db, user_id: str, transaction_id: str, file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
    """Upload a deposit screenshot for a transaction"""
    result = await upload_file(
        db=db,
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        folder="deposit_screenshots",
        user_id=user_id,
        file_type="deposit_screenshot"
    )
    
    if result.get("success"):
        # Update transaction with screenshot URL
        await db.licensee_transactions.update_one(
            {"id": transaction_id},
            {"$set": {"screenshot_url": result.get("url")}}
        )
    
    return result

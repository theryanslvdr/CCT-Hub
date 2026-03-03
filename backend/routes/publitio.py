"""Publitio image upload routes for forum and other media."""
import os
import hashlib
import time
import random
import httpx
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

import deps

router = APIRouter(prefix="/publitio", tags=["Publitio"])

# Config from environment or DB settings
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


async def get_publitio_creds():
    """Get Publitio credentials from DB settings (fallback to env)."""
    db = deps.db
    settings = await db.settings.find_one({"_id": "global"}, {"_id": 0})
    if settings:
        api_key = settings.get("publitio_api_key", "")
        api_secret = settings.get("publitio_api_secret", "")
        if api_key and api_secret:
            return api_key, api_secret
    # Fallback to env
    api_key = os.environ.get("PUBLITIO_API_KEY", "")
    api_secret = os.environ.get("PUBLITIO_API_SECRET", "")
    return api_key, api_secret


def generate_signature(api_secret: str, timestamp: int, nonce: str) -> str:
    """Generate Publitio API signature using SHA-1."""
    signature_string = f"{timestamp}{nonce}{api_secret}"
    return hashlib.sha1(signature_string.encode()).hexdigest()


def validate_file(file: UploadFile, file_bytes: bytes):
    """Validate uploaded file meets constraints."""
    # Check size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(file_bytes)} bytes exceeds maximum of {MAX_FILE_SIZE} bytes (2MB)"
        )
    
    # Check extension
    if file.filename:
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File extension '.{ext}' is not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"MIME type '{file.content_type}' is not allowed. Only images are supported."
        )


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Form(default="general"),
    user: dict = Depends(deps.get_current_user),
):
    """
    Upload an image to Publitio.
    
    Args:
        file: The image file (max 2MB, jpg/png/gif/webp)
        folder: Folder path in Publitio (e.g., 'forum/posts', 'forum/comments')
    
    Returns:
        Upload result with URL and metadata
    """
    api_key, api_secret = await get_publitio_creds()
    
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=503,
            detail="Publitio integration not configured. Please add API keys in Platform Settings."
        )
    
    # Read and validate file
    file_bytes = await file.read()
    validate_file(file, file_bytes)
    
    # Generate auth params
    timestamp = int(time.time())
    nonce = str(random.randint(10000000, 99999999))
    signature = generate_signature(api_secret, timestamp, nonce)
    
    # Prepare upload
    form_data = {
        'api_key': api_key,
        'api_timestamp': str(timestamp),
        'api_nonce': nonce,
        'api_signature': signature,
        'folder': folder,
        'title': file.filename or f"upload_{timestamp}",
    }
    
    files = {
        'file': (file.filename, file_bytes, file.content_type)
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.publit.io/v1/files/create",
                data=form_data,
                files=files
            )
            
            result = response.json()
            
            if not result.get('success'):
                error_msg = result.get('error', {}).get('message', 'Upload failed')
                raise HTTPException(status_code=400, detail=f"Publitio error: {error_msg}")
            
            return {
                "success": True,
                "id": result.get('id'),
                "public_id": result.get('public_id'),
                "url": result.get('url_preview'),
                "url_download": result.get('url_download'),
                "url_thumbnail": result.get('url_thumbnail'),
                "title": result.get('title'),
                "folder": folder,
                "size": result.get('size'),
                "width": result.get('width'),
                "height": result.get('height'),
                "extension": result.get('extension'),
                "uploaded_by": user["id"],
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upload timed out. Please try again.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")


@router.get("/folders")
async def list_folders(
    user: dict = Depends(deps.get_current_user),
):
    """List available Publitio folders."""
    api_key, api_secret = await get_publitio_creds()
    
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=503,
            detail="Publitio integration not configured."
        )
    
    timestamp = int(time.time())
    nonce = str(random.randint(10000000, 99999999))
    signature = generate_signature(api_secret, timestamp, nonce)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.publit.io/v1/folders/list",
                params={
                    'api_key': api_key,
                    'api_timestamp': str(timestamp),
                    'api_nonce': nonce,
                    'api_signature': signature,
                }
            )
            
            result = response.json()
            
            if not result.get('success'):
                return {"success": False, "folders": []}
            
            return {
                "success": True,
                "folders": result.get('folders', []),
                "total": result.get('folders_total', 0),
            }
            
    except Exception:
        return {"success": False, "folders": []}


@router.post("/folder/create")
async def create_folder(
    name: str,
    parent_folder: Optional[str] = None,
    user: dict = Depends(deps.get_current_user),
):
    """Create a new folder in Publitio."""
    # Check admin
    if user.get("role") not in ("master_admin", "super_admin", "basic_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    api_key, api_secret = await get_publitio_creds()
    
    if not api_key or not api_secret:
        raise HTTPException(status_code=503, detail="Publitio not configured")
    
    timestamp = int(time.time())
    nonce = str(random.randint(10000000, 99999999))
    signature = generate_signature(api_secret, timestamp, nonce)
    
    params = {
        'api_key': api_key,
        'api_timestamp': str(timestamp),
        'api_nonce': nonce,
        'api_signature': signature,
        'name': name,
    }
    if parent_folder:
        params['folder'] = parent_folder
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.publit.io/v1/folders/create",
                data=params
            )
            
            result = response.json()
            
            if not result.get('success'):
                error_msg = result.get('error', {}).get('message', 'Failed')
                raise HTTPException(status_code=400, detail=error_msg)
            
            return {
                "success": True,
                "id": result.get('id'),
                "name": result.get('name'),
            }
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")


@router.get("/test")
async def test_connection(
    user: dict = Depends(deps.get_current_user),
):
    """Test Publitio API connection."""
    api_key, api_secret = await get_publitio_creds()
    
    if not api_key or not api_secret:
        return {
            "success": False,
            "configured": False,
            "message": "Publitio API keys not configured"
        }
    
    timestamp = int(time.time())
    nonce = str(random.randint(10000000, 99999999))
    signature = generate_signature(api_secret, timestamp, nonce)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.publit.io/v1/files/list",
                params={
                    'api_key': api_key,
                    'api_timestamp': str(timestamp),
                    'api_nonce': nonce,
                    'api_signature': signature,
                    'limit': 1,
                }
            )
            
            result = response.json()
            
            if result.get('success'):
                return {
                    "success": True,
                    "configured": True,
                    "message": "Connected to Publitio successfully"
                }
            else:
                return {
                    "success": False,
                    "configured": True,
                    "message": result.get('error', {}).get('message', 'Auth failed')
                }
                
    except Exception as e:
        return {
            "success": False,
            "configured": True,
            "message": f"Connection error: {str(e)}"
        }


@router.delete("/file/{file_id}")
async def delete_file(
    file_id: str,
    user: dict = Depends(deps.get_current_user),
):
    """Delete a file from Publitio (admin only)."""
    if user.get("role") not in ("master_admin", "super_admin", "basic_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    api_key, api_secret = await get_publitio_creds()
    
    if not api_key or not api_secret:
        raise HTTPException(status_code=503, detail="Publitio not configured")
    
    timestamp = int(time.time())
    nonce = str(random.randint(10000000, 99999999))
    signature = generate_signature(api_secret, timestamp, nonce)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"https://api.publit.io/v1/files/delete/{file_id}",
                params={
                    'api_key': api_key,
                    'api_timestamp': str(timestamp),
                    'api_nonce': nonce,
                    'api_signature': signature,
                }
            )
            
            result = response.json()
            
            if result.get('success'):
                return {"success": True, "message": "File deleted"}
            else:
                raise HTTPException(status_code=400, detail="Failed to delete file")
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")

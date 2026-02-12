"""API Center routes for external integrations."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid
import httpx

from deps import db, get_current_user, require_admin

router = APIRouter(prefix="/api-center", tags=["API Center"])


class APIConnectionCreate(BaseModel):
    name: str
    endpoint_url: str
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    is_active: bool = True


class APIConnectionResponse(BaseModel):
    id: str
    name: str
    endpoint_url: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]


@router.post("/connections", response_model=APIConnectionResponse)
async def create_api_connection(data: APIConnectionCreate, user: dict = Depends(require_admin)):
    conn_id = str(uuid.uuid4())
    connection = {
        "id": conn_id,
        "name": data.name,
        "endpoint_url": data.endpoint_url,
        "api_key": data.api_key,
        "headers": data.headers or {},
        "is_active": data.is_active,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": None,
    }
    await db.api_connections.insert_one(connection)
    return APIConnectionResponse(**{**connection, "created_at": datetime.fromisoformat(connection["created_at"])})


@router.get("/connections", response_model=List[APIConnectionResponse])
async def get_api_connections(user: dict = Depends(require_admin)):
    connections = await db.api_connections.find({}, {"_id": 0, "api_key": 0}).to_list(100)
    return [
        APIConnectionResponse(
            **{
                **c,
                "created_at": datetime.fromisoformat(c["created_at"])
                if isinstance(c["created_at"], str)
                else c["created_at"],
                "last_used": datetime.fromisoformat(c["last_used"]) if c.get("last_used") else None,
            }
        )
        for c in connections
    ]


@router.post("/connections/{conn_id}/send")
async def send_to_connection(conn_id: str, payload: Dict[str, Any], user: dict = Depends(get_current_user)):
    connection = await db.api_connections.find_one({"id": conn_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    if not connection.get("is_active"):
        raise HTTPException(status_code=400, detail="Connection is not active")

    try:
        headers = connection.get("headers", {})
        if connection.get("api_key"):
            headers["Authorization"] = f"Bearer {connection['api_key']}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                connection["endpoint_url"],
                json=payload,
                headers=headers,
                timeout=30.0,
            )

            await db.api_connections.update_one(
                {"id": conn_id},
                {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}},
            )

            return {
                "status_code": response.status_code,
                "response": response.json()
                if response.headers.get("content-type", "").startswith("application/json")
                else response.text,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@router.post("/receive")
async def receive_webhook(payload: Dict[str, Any]):
    """Endpoint to receive data from external apps"""
    webhook_id = str(uuid.uuid4())
    webhook_log = {
        "id": webhook_id,
        "payload": payload,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "processed": False,
    }
    await db.webhook_logs.insert_one(webhook_log)

    action = payload.get("action")
    if action == "update_signal":
        signal_data = payload.get("data", {})
        if signal_data:
            await db.trading_signals.update_many({}, {"$set": {"is_active": False}})
            signal_id = str(uuid.uuid4())
            signal = {
                "id": signal_id,
                "product": signal_data.get("product", "MOIL10"),
                "trade_time": signal_data.get("trade_time", "00:00"),
                "direction": signal_data.get("direction", "BUY"),
                "notes": signal_data.get("notes"),
                "is_active": True,
                "created_by": "webhook",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.trading_signals.insert_one(signal)

    return {"received": True, "webhook_id": webhook_id}


@router.delete("/connections/{conn_id}")
async def delete_api_connection(conn_id: str, user: dict = Depends(require_admin)):
    result = await db.api_connections.delete_one({"id": conn_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"message": "Connection deleted"}

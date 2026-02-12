"""
BVE (Beta Virtual Environment) routes - extracted from server.py
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

import deps
from deps import get_current_user

router = APIRouter(prefix="/bve", tags=["Beta Virtual Environment"])


# ==================== MODELS ====================

class BVESessionCreate(BaseModel):
    pass

class BVESessionExit(BaseModel):
    session_id: str

class BVERewind(BaseModel):
    session_id: str

class BVESignalCreate(BaseModel):
    product: str = "MOIL10"
    direction: str = "BUY"
    trade_time: str
    trade_timezone: str = "Asia/Manila"
    profit_multiplier: float = 15


# ==================== HELPERS ====================

async def require_bve_admin(user: dict = Depends(get_current_user)):
    """Require super admin or master admin role for BVE access"""
    if user["role"] not in ["super_admin", "master_admin"]:
        raise HTTPException(status_code=403, detail="Beta Virtual Environment requires Super Admin or Master Admin access")
    return user


# ==================== ROUTES ====================

@router.post("/enter")
async def enter_bve(user: dict = Depends(require_bve_admin)):
    """Enter the Beta Virtual Environment - creates a snapshot and session"""
    db = deps.db
    session_id = str(uuid.uuid4())
    
    active_signal = await db.trading_signals.find_one({"is_active": True}, {"_id": 0})
    user_trade_logs = await db.trade_logs.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    user_deposits = await db.deposits.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    user_profile = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0})
    
    snapshot = {
        "id": session_id,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_data": {
            "active_signal": active_signal,
            "trade_logs": user_trade_logs,
            "deposits": user_deposits,
            "user_profile": user_profile
        }
    }
    
    await db.bve_sessions.insert_one(snapshot)
    
    if active_signal:
        bve_signal = {**active_signal, "bve_session_id": session_id}
        await db.bve_trading_signals.delete_many({"bve_session_id": session_id})
        await db.bve_trading_signals.insert_one(bve_signal)
    
    await db.bve_trade_logs.delete_many({"bve_session_id": session_id})
    for log in user_trade_logs:
        bve_log = {**log, "bve_session_id": session_id}
        await db.bve_trade_logs.insert_one(bve_log)
    
    await db.bve_deposits.delete_many({"bve_session_id": session_id})
    for dep in user_deposits:
        bve_dep = {**dep, "bve_session_id": session_id}
        await db.bve_deposits.insert_one(bve_dep)
    
    return {
        "session_id": session_id,
        "message": "Entered Beta Virtual Environment",
        "snapshot": {
            "signals_count": 1 if active_signal else 0,
            "trade_logs_count": len(user_trade_logs),
            "deposits_count": len(user_deposits)
        }
    }

@router.post("/exit")
async def exit_bve(data: BVESessionExit, user: dict = Depends(require_bve_admin)):
    """Exit the Beta Virtual Environment - cleans up BVE data"""
    db = deps.db
    session_id = data.session_id
    
    await db.bve_trading_signals.delete_many({"bve_session_id": session_id})
    await db.bve_trade_logs.delete_many({"bve_session_id": session_id})
    await db.bve_deposits.delete_many({"bve_session_id": session_id})
    
    await db.bve_sessions.update_one(
        {"id": session_id},
        {"$set": {"ended_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Exited Beta Virtual Environment", "session_id": session_id}

@router.post("/rewind")
async def rewind_bve(data: BVERewind, user: dict = Depends(require_bve_admin)):
    """Rewind BVE to the initial snapshot state"""
    db = deps.db
    session_id = data.session_id
    
    session = await db.bve_sessions.find_one({"id": session_id, "user_id": user["id"]})
    if not session:
        raise HTTPException(status_code=404, detail="BVE session not found")
    
    snapshot_data = session.get("snapshot_data", {})
    
    await db.bve_trading_signals.delete_many({"bve_session_id": session_id})
    await db.bve_trade_logs.delete_many({"bve_session_id": session_id})
    await db.bve_deposits.delete_many({"bve_session_id": session_id})
    
    active_signal = snapshot_data.get("active_signal")
    if active_signal:
        bve_signal = {**active_signal, "bve_session_id": session_id}
        await db.bve_trading_signals.insert_one(bve_signal)
    
    for log in snapshot_data.get("trade_logs", []):
        bve_log = {**log, "bve_session_id": session_id}
        await db.bve_trade_logs.insert_one(bve_log)
    
    for dep in snapshot_data.get("deposits", []):
        bve_dep = {**dep, "bve_session_id": session_id}
        await db.bve_deposits.insert_one(bve_dep)
    
    return {
        "message": "BVE state rewound to entry point",
        "session_id": session_id,
        "restored": {
            "signals": 1 if active_signal else 0,
            "trade_logs": len(snapshot_data.get("trade_logs", [])),
            "deposits": len(snapshot_data.get("deposits", []))
        }
    }

@router.get("/signals")
async def get_bve_signals(user: dict = Depends(require_bve_admin)):
    """Get signals in BVE mode"""
    db = deps.db
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    signals = await db.bve_trading_signals.find(
        {"bve_session_id": session["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return signals

@router.post("/signals")
async def create_bve_signal(data: BVESignalCreate, user: dict = Depends(require_bve_admin)):
    """Create a new signal in BVE mode (does not affect real data)"""
    db = deps.db
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    await db.bve_trading_signals.update_many(
        {"bve_session_id": session["id"], "is_active": True},
        {"$set": {"is_active": False, "status": "completed"}}
    )
    
    signal = {
        "id": str(uuid.uuid4()),
        "bve_session_id": session["id"],
        "product": data.product,
        "direction": data.direction,
        "trade_time": data.trade_time,
        "trade_timezone": data.trade_timezone,
        "profit_multiplier": data.profit_multiplier,
        "is_active": True,
        "is_simulated": True,
        "status": "active",
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bve_trading_signals.insert_one(signal)
    
    return {"message": "BVE signal created", "signal": {k: v for k, v in signal.items() if k != "_id"}}

@router.put("/signals/{signal_id}")
async def update_bve_signal(signal_id: str, data: dict, user: dict = Depends(require_bve_admin)):
    """Update a BVE signal (deactivate, change direction, etc.)"""
    db = deps.db
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    signal = await db.bve_trading_signals.find_one(
        {"id": signal_id, "bve_session_id": session["id"]}, {"_id": 0}
    )
    if not signal:
        raise HTTPException(status_code=404, detail="BVE signal not found")
    
    update_data = {}
    for field in ["trade_time", "trade_timezone", "direction", "profit_points", "notes"]:
        if data.get(field) is not None:
            update_data[field] = data[field]
    
    if data.get("is_active") is not None:
        if data["is_active"]:
            await db.bve_trading_signals.update_many(
                {"bve_session_id": session["id"], "id": {"$ne": signal_id}},
                {"$set": {"is_active": False}}
            )
        update_data["is_active"] = data["is_active"]
    
    if update_data:
        await db.bve_trading_signals.update_one(
            {"id": signal_id, "bve_session_id": session["id"]},
            {"$set": update_data}
        )
    
    updated = await db.bve_trading_signals.find_one(
        {"id": signal_id, "bve_session_id": session["id"]}, {"_id": 0}
    )
    return {"message": "BVE signal updated", "signal": updated}

@router.get("/active-signal")
async def get_bve_active_signal(user: dict = Depends(require_bve_admin)):
    """Get active signal in BVE mode"""
    db = deps.db
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        return {"signal": None}
    
    signal = await db.bve_trading_signals.find_one(
        {"bve_session_id": session["id"], "is_active": True}, {"_id": 0}
    )
    
    return {"signal": signal}

@router.post("/trade/log")
async def log_bve_trade(data: dict, user: dict = Depends(require_bve_admin)):
    """Log a trade in BVE mode (does not affect real data)"""
    db = deps.db
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    bve_deposits = await db.bve_deposits.find(
        {"bve_session_id": session["id"]}, {"_id": 0}
    ).to_list(1000)
    
    bve_trade_logs = await db.bve_trade_logs.find(
        {"bve_session_id": session["id"]}, {"_id": 0}
    ).to_list(1000)
    
    total_deposits = sum(d.get("amount", 0) for d in bve_deposits if d.get("amount", 0) > 0)
    total_profit = sum(t.get("actual_profit", 0) for t in bve_trade_logs)
    account_value = total_deposits + total_profit
    
    lot_size = account_value / 980 if account_value > 0 else 0
    projected_profit = lot_size * 15
    actual_profit = data.get("actual_profit", 0)
    profit_difference = actual_profit - projected_profit
    
    trade_log = {
        "id": str(uuid.uuid4()),
        "bve_session_id": session["id"],
        "user_id": user["id"],
        "lot_size": data.get("lot_size") or lot_size,
        "direction": data.get("direction", "BUY"),
        "actual_profit": actual_profit,
        "projected_profit": projected_profit,
        "profit_difference": profit_difference,
        "performance": "above" if profit_difference > 0 else "below" if profit_difference < 0 else "target",
        "notes": data.get("notes"),
        "is_simulated": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bve_trade_logs.insert_one(trade_log)
    
    return {k: v for k, v in trade_log.items() if k != "_id"}

@router.get("/summary")
async def get_bve_summary(user: dict = Depends(require_bve_admin)):
    """Get profit summary in BVE mode"""
    db = deps.db
    session = await db.bve_sessions.find_one(
        {"user_id": user["id"], "ended_at": {"$exists": False}},
        sort=[("created_at", -1)]
    )
    if not session:
        raise HTTPException(status_code=400, detail="No active BVE session")
    
    bve_deposits = await db.bve_deposits.find(
        {"bve_session_id": session["id"]}, {"_id": 0}
    ).to_list(1000)
    
    bve_trade_logs = await db.bve_trade_logs.find(
        {"bve_session_id": session["id"]}, {"_id": 0}
    ).to_list(1000)
    
    total_deposits = sum(d.get("amount", 0) for d in bve_deposits if d.get("amount", 0) > 0)
    total_profit = sum(t.get("actual_profit", 0) for t in bve_trade_logs)
    account_value = total_deposits + total_profit
    lot_size = account_value / 980 if account_value > 0 else 0
    
    return {
        "account_value": account_value,
        "total_deposits": total_deposits,
        "total_profit": total_profit,
        "current_lot_size": lot_size,
        "is_bve": True
    }

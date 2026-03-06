"""System Health & Deployment Metrics - Master Admin only"""
import os
import time
import psutil
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends

import deps

logger = logging.getLogger("server")

router = APIRouter(prefix="/admin/system-health", tags=["System Health"])

# Track server start time
_SERVER_START_TIME = time.time()

# Track request latencies per route group
_route_latencies = {
    "auth": [],
    "profit": [],
    "trade": [],
    "admin": [],
    "forum": [],
    "general": [],
}
_MAX_LATENCY_SAMPLES = 200


def record_latency(route_group: str, latency_ms: float):
    """Record a latency sample for a route group."""
    if route_group in _route_latencies:
        samples = _route_latencies[route_group]
        samples.append(latency_ms)
        if len(samples) > _MAX_LATENCY_SAMPLES:
            _route_latencies[route_group] = samples[-_MAX_LATENCY_SAMPLES:]


@router.get("")
async def get_system_health(user: dict = Depends(deps.require_master_admin)):
    """Comprehensive system health dashboard - Master Admin only."""
    db = deps.db
    health = {}

    # 1. Uptime
    uptime_seconds = time.time() - _SERVER_START_TIME
    days, remainder = divmod(int(uptime_seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    health["uptime"] = {
        "seconds": round(uptime_seconds),
        "formatted": f"{days}d {hours}h {minutes}m {secs}s",
        "started_at": datetime.fromtimestamp(_SERVER_START_TIME, tz=timezone.utc).isoformat(),
    }

    # 2. System resources
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_percent = psutil.cpu_percent(interval=0.1)
        process = psutil.Process()
        proc_mem = process.memory_info()

        health["system"] = {
            "cpu_percent": round(cpu_percent, 1),
            "memory": {
                "total_gb": round(mem.total / (1024 ** 3), 2),
                "used_gb": round(mem.used / (1024 ** 3), 2),
                "available_gb": round(mem.available / (1024 ** 3), 2),
                "percent": mem.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "free_gb": round(disk.free / (1024 ** 3), 2),
                "percent": round(disk.percent, 1),
            },
            "process": {
                "rss_mb": round(proc_mem.rss / (1024 ** 2), 1),
                "vms_mb": round(proc_mem.vms / (1024 ** 2), 1),
                "threads": process.num_threads(),
            },
        }
    except Exception as e:
        logger.warning(f"Failed to get system resources: {e}")
        health["system"] = {"error": str(e)}

    # 3. Database health
    try:
        start = time.time()
        await db.command("ping")
        ping_ms = round((time.time() - start) * 1000, 1)

        # Collection stats
        collections = await db.list_collection_names()
        col_stats = {}
        for col_name in ["users", "deposits", "trade_logs", "trading_signals", "licenses", "posts", "comments"]:
            if col_name in collections:
                count = await db[col_name].estimated_document_count()
                col_stats[col_name] = count

        # DB server info
        server_info = await db.command("serverStatus")
        connections = server_info.get("connections", {})

        health["database"] = {
            "status": "healthy",
            "ping_ms": ping_ms,
            "collections_count": len(collections),
            "document_counts": col_stats,
            "connections": {
                "current": connections.get("current", 0),
                "available": connections.get("available", 0),
                "total_created": connections.get("totalCreated", 0),
            },
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health["database"] = {"status": "unhealthy", "error": str(e)}

    # 4. WebSocket connections
    try:
        from services import websocket_manager
        ws_info = {
            "total_connections": sum(
                len(conns) for conns in websocket_manager.active_connections.values()
            ) if hasattr(websocket_manager, "active_connections") else 0,
            "unique_users": len(
                websocket_manager.active_connections
            ) if hasattr(websocket_manager, "active_connections") else 0,
            "admin_connections": len(
                websocket_manager.admin_connections
            ) if hasattr(websocket_manager, "admin_connections") else 0,
        }
        health["websockets"] = ws_info
    except Exception as e:
        health["websockets"] = {"error": str(e)}

    # 5. Route latencies
    latency_summary = {}
    for group, samples in _route_latencies.items():
        if samples:
            sorted_s = sorted(samples)
            n = len(sorted_s)
            latency_summary[group] = {
                "samples": n,
                "avg_ms": round(sum(sorted_s) / n, 1),
                "p50_ms": round(sorted_s[n // 2], 1),
                "p95_ms": round(sorted_s[int(n * 0.95)], 1) if n >= 20 else None,
                "p99_ms": round(sorted_s[int(n * 0.99)], 1) if n >= 100 else None,
                "max_ms": round(sorted_s[-1], 1),
            }
        else:
            latency_summary[group] = {"samples": 0, "avg_ms": 0}
    health["route_latencies"] = latency_summary

    # 6. Error rates (from recent logs - check last N errors)
    try:
        recent_errors = await db.error_logs.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(20).to_list(20)
        health["recent_errors"] = {
            "count": len(recent_errors),
            "errors": recent_errors[:5],
        }
    except Exception:
        health["recent_errors"] = {"count": 0, "errors": []}

    # 7. Active users (last 24h)
    try:
        from datetime import timedelta
        day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        active_24h = await db.users.count_documents(
            {"last_login": {"$gte": day_ago.isoformat()}}
        )
        total_users = await db.users.estimated_document_count()
        active_members = await db.users.count_documents({"role": "member", "is_active": True})
        health["users"] = {
            "total": total_users,
            "active_members": active_members,
            "active_24h": active_24h,
        }
    except Exception as e:
        health["users"] = {"error": str(e)}

    # 8. External service status
    services_status = {}
    # Check Emailit
    emailit_key = os.environ.get("EMAILIT_API_KEY", "")
    services_status["emailit"] = "configured" if emailit_key else "not_configured"
    # Check Heartbeat
    hb_key = os.environ.get("HEARTBEAT_API_KEY", "")
    services_status["heartbeat"] = "configured" if hb_key else "not_configured"
    # Check Cloudinary
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    services_status["cloudinary"] = "configured" if cloud_name else "not_configured"
    # Check VAPID
    vapid_key = os.environ.get("VAPID_PRIVATE_KEY", "")
    services_status["push_notifications"] = "configured" if vapid_key else "not_configured"
    health["external_services"] = services_status

    # 9. Build info
    try:
        with open("/app/.build_version", "r") as f:
            build_version = f.read().strip()
    except FileNotFoundError:
        build_version = "unknown"
    health["build"] = {
        "version": build_version,
        "environment": os.environ.get("NODE_ENV", "production"),
    }

    return health


@router.get("/db-ping")
async def db_ping(user: dict = Depends(deps.require_master_admin)):
    """Quick DB latency check."""
    start = time.time()
    await deps.db.command("ping")
    ping_ms = round((time.time() - start) * 1000, 1)
    return {"ping_ms": ping_ms, "status": "ok"}

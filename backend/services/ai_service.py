"""Shared AI service — handles all OpenRouter LLM calls with caching and credit efficiency."""
import os
import httpx
import logging
import hashlib
import json
from datetime import datetime, timezone, timedelta

import deps

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"

# Token limits per feature type (keeps costs low)
TOKEN_LIMITS = {
    "trade_coach": 200,
    "financial_summary": 350,
    "balance_forecast": 250,
    "post_summarizer": 250,
    "signal_insights": 250,
    "trade_journal": 350,
    "goal_advisor": 200,
    "anomaly_alert": 200,
    "answer_suggestion": 200,
    "member_risk": 200,
    "daily_report": 400,
    "smart_notification": 100,
    "commission_optimizer": 200,
    "milestone_motivation": 150,
    "duplicate_check": 100,
    "habit_tasks": 300,
}

# Cache durations per feature (seconds)
CACHE_TTL = {
    "trade_coach": 3600,          # 1 hour (per trade)
    "financial_summary": 86400,    # 24 hours
    "balance_forecast": 43200,     # 12 hours
    "post_summarizer": 7200,       # 2 hours
    "signal_insights": 3600,       # 1 hour (per signal)
    "trade_journal": 86400,        # 24 hours
    "goal_advisor": 43200,         # 12 hours
    "anomaly_alert": 86400,        # 24 hours
    "answer_suggestion": 1800,     # 30 min
    "member_risk": 86400,          # 24 hours
    "daily_report": 86400,         # 24 hours
    "smart_notification": 3600,    # 1 hour
    "commission_optimizer": 86400, # 24 hours
    "milestone_motivation": 86400, # 24 hours
    "habit_tasks": 86400,          # 24 hours
}


def _cache_key(feature: str, user_id: str, extra: str = "") -> str:
    raw = f"{feature}:{user_id}:{extra}"
    return hashlib.md5(raw.encode()).hexdigest()


async def get_cached(feature: str, user_id: str, extra: str = ""):
    """Check DB cache for an AI response."""
    db = deps.db
    key = _cache_key(feature, user_id, extra)
    ttl = CACHE_TTL.get(feature, 3600)
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=ttl)).isoformat()

    cached = await db.ai_cache.find_one(
        {"cache_key": key, "created_at": {"$gte": cutoff}},
        {"_id": 0, "response": 1},
    )
    return cached["response"] if cached else None


async def set_cache(feature: str, user_id: str, response: str, extra: str = ""):
    """Store AI response in DB cache."""
    db = deps.db
    key = _cache_key(feature, user_id, extra)
    await db.ai_cache.update_one(
        {"cache_key": key},
        {"$set": {
            "cache_key": key,
            "feature": feature,
            "user_id": user_id,
            "response": response,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    feature: str,
    user_id: str = "",
    cache_extra: str = "",
    temperature: float = 0.3,
    skip_cache: bool = False,
):
    """Central LLM call with caching and error handling.
    Returns the AI text response or None on failure.
    """
    # Check cache first
    if not skip_cache:
        cached = await get_cached(feature, user_id, cache_extra)
        if cached:
            return cached

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set")
        return None

    max_tokens = TOKEN_LIMITS.get(feature, 200)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()

            # Cache the response
            if not skip_cache:
                await set_cache(feature, user_id, text, cache_extra)

            return text

    except Exception as e:
        logger.warning(f"OpenRouter call failed for {feature}: {e}")
        return None

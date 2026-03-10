"""AI-powered feature endpoints — Trade Coach, Financial Summary, Balance Forecast, Post Summarizer."""
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional

import deps
from deps import get_current_user
from services.ai_service import call_llm

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Features"])


# ─── AI Trade Coach ───

@router.get("/trade-coach/{trade_id}")
async def get_trade_coach(trade_id: str, user: dict = Depends(get_current_user)):
    """Get AI coaching feedback for a specific trade."""
    db = deps.db

    trade = await db.trade_logs.find_one(
        {"id": trade_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Get recent trade history for context (last 10 trades)
    recent = await db.trade_logs.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)

    recent_summary = []
    for t in recent:
        recent_summary.append(
            f"{t.get('created_at','')[:10]}: {t.get('direction','?')} "
            f"profit=${t.get('actual_profit',0):.2f} vs projected=${t.get('projected_profit',0):.2f} "
            f"({t.get('performance','?')})"
        )

    # Get streak
    streak_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "streak": 1})
    streak = streak_doc.get("streak", 0) if streak_doc else 0

    system = (
        "You are a trading coach for a copy-trading platform. Give brief, actionable feedback. "
        "Be encouraging but honest. Focus on patterns and discipline. "
        "Keep response under 3 short paragraphs. Use plain language."
    )

    prompt = (
        f"Trade result: {trade.get('direction','')} signal, "
        f"lot size {trade.get('lot_size',0):.2f}, "
        f"projected ${trade.get('projected_profit',0):.2f}, "
        f"actual ${trade.get('actual_profit',0):.2f}, "
        f"performance: {trade.get('performance','')}.\n"
        f"Current streak: {streak} days.\n"
        f"Recent 10 trades:\n" + "\n".join(recent_summary) + "\n\n"
        "Give coaching feedback on this trade and any patterns you notice."
    )

    result = await call_llm(system, prompt, "trade_coach", user["id"], trade_id)
    if not result:
        return {"coaching": "Unable to generate coaching feedback right now. Try again later.", "cached": False}

    return {"coaching": result, "trade_id": trade_id, "cached": True}


# ─── AI Financial Summary ───

@router.get("/financial-summary")
async def get_financial_summary(
    period: str = Query("weekly", regex="^(weekly|monthly)$"),
    user: dict = Depends(get_current_user),
):
    """Generate an AI-powered financial summary for the user."""
    db = deps.db

    if period == "weekly":
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    else:
        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    # Gather data
    trades = await db.trade_logs.find(
        {"user_id": user["id"], "created_at": {"$gte": since}}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    deposits = await db.deposits.find(
        {"user_id": user["id"], "type": "deposit", "created_at": {"$gte": since}}, {"_id": 0, "amount": 1, "created_at": 1}
    ).to_list(50)

    withdrawals = await db.deposits.find(
        {"user_id": user["id"], "type": "withdrawal", "created_at": {"$gte": since}}, {"_id": 0, "amount": 1, "created_at": 1}
    ).to_list(50)

    commissions = await db.commissions.find(
        {"user_id": user["id"], "created_at": {"$gte": since}}, {"_id": 0, "amount": 1, "skip_deposit": 1}
    ).to_list(50)

    # Compute stats
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    total_projected = sum(t.get("projected_profit", 0) for t in trades)
    trade_count = len(trades)
    exceeded = sum(1 for t in trades if t.get("performance") == "exceeded")
    below = sum(1 for t in trades if t.get("performance") == "below")
    perfect = sum(1 for t in trades if t.get("performance") == "perfect")
    total_deposits = sum(d.get("amount", 0) for d in deposits)
    total_withdrawals = sum(abs(w.get("amount", 0)) for w in withdrawals)
    total_commissions = sum(c.get("amount", 0) for c in commissions if not c.get("skip_deposit"))
    avg_profit = total_profit / trade_count if trade_count else 0

    cache_extra = f"{period}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    system = (
        "You are a financial analyst for a trading platform. Write a clear, friendly summary "
        "of the member's financial activity. Highlight wins, areas for improvement, and trends. "
        "Keep it concise — 4-5 short bullet points max. Use $ amounts."
    )

    prompt = (
        f"Period: Last {'7 days' if period == 'weekly' else '30 days'}\n"
        f"Trades: {trade_count} (exceeded: {exceeded}, perfect: {perfect}, below: {below})\n"
        f"Total profit: ${total_profit:.2f} (projected: ${total_projected:.2f})\n"
        f"Avg profit/trade: ${avg_profit:.2f}\n"
        f"Deposits: ${total_deposits:.2f}, Withdrawals: ${total_withdrawals:.2f}\n"
        f"Commissions earned: ${total_commissions:.2f}\n\n"
        f"Summarize this member's financial performance."
    )

    result = await call_llm(system, prompt, "financial_summary", user["id"], cache_extra)
    if not result:
        return {"summary": "Unable to generate summary right now.", "period": period, "stats": {}}

    return {
        "summary": result,
        "period": period,
        "stats": {
            "trade_count": trade_count,
            "total_profit": round(total_profit, 2),
            "exceeded": exceeded,
            "below": below,
            "perfect": perfect,
            "deposits": round(total_deposits, 2),
            "withdrawals": round(total_withdrawals, 2),
            "commissions": round(total_commissions, 2),
        },
    }


# ─── AI Balance Forecast ───

@router.get("/balance-forecast")
async def get_balance_forecast(user: dict = Depends(get_current_user)):
    """AI-powered balance projection for 7/30/90 days."""
    db = deps.db

    # Get current account value
    from utils.calculations import calculate_account_value
    account_value = await calculate_account_value(db, user["id"], user)

    # Get last 30 trades for trend analysis
    trades = await db.trade_logs.find(
        {"user_id": user["id"]}, {"_id": 0, "actual_profit": 1, "created_at": 1, "lot_size": 1}
    ).sort("created_at", -1).limit(30).to_list(30)

    # Get commissions from last 30 days
    since_30d = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    commissions = await db.commissions.find(
        {"user_id": user["id"], "created_at": {"$gte": since_30d}, "skip_deposit": {"$ne": True}},
        {"_id": 0, "amount": 1},
    ).to_list(50)

    avg_daily_profit = sum(t.get("actual_profit", 0) for t in trades) / max(len(trades), 1)
    avg_daily_commission = sum(c.get("amount", 0) for c in commissions) / 30
    trade_days = len(trades)

    cache_extra = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    system = (
        "You are a financial forecasting assistant. Based on trading history, project future balance. "
        "Be realistic — mention risks and assumptions. Keep response to 3-4 sentences plus the 3 projections. "
        "Format projections as: 7-day: $X | 30-day: $X | 90-day: $X"
    )

    prompt = (
        f"Current balance: ${account_value:.2f}\n"
        f"Last {trade_days} trades avg profit: ${avg_daily_profit:.2f}/trade\n"
        f"Avg daily commission: ${avg_daily_commission:.2f}\n"
        f"Trading frequency: ~{trade_days} trades in recent period\n\n"
        f"Project the balance for 7, 30, and 90 days assuming similar performance. "
        f"Account for compounding (lot size grows with balance)."
    )

    result = await call_llm(system, prompt, "balance_forecast", user["id"], cache_extra)
    if not result:
        # Simple math fallback
        daily_gain = avg_daily_profit + avg_daily_commission
        return {
            "forecast": f"Based on your average daily gain of ${daily_gain:.2f}, your projected balance:\n"
                        f"7-day: ${account_value + daily_gain * 7:.2f} | "
                        f"30-day: ${account_value + daily_gain * 30:.2f} | "
                        f"90-day: ${account_value + daily_gain * 90:.2f}",
            "current_balance": round(account_value, 2),
            "ai_powered": False,
        }

    return {
        "forecast": result,
        "current_balance": round(account_value, 2),
        "avg_daily_profit": round(avg_daily_profit, 2),
        "avg_daily_commission": round(avg_daily_commission, 2),
        "ai_powered": True,
    }


# ─── AI Post Summarizer ───

@router.get("/forum-summary/{post_id}")
async def get_forum_summary(post_id: str, user: dict = Depends(get_current_user)):
    """Generate a TL;DR summary for a long forum thread."""
    db = deps.db

    post = await db.forum_posts.find_one({"id": post_id}, {"_id": 0, "title": 1, "content": 1, "id": 1})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = await db.forum_comments.find(
        {"post_id": post_id}, {"_id": 0, "content": 1, "author_name": 1, "score": 1}
    ).sort("created_at", 1).to_list(50)

    if len(comments) < 3:
        return {"summary": None, "reason": "Thread too short for summary", "comment_count": len(comments)}

    # Build thread text (truncate long comments)
    thread = f"Title: {post.get('title','')}\nOP: {post.get('content','')[:300]}\n\n"
    for i, c in enumerate(comments[:30]):
        thread += f"Comment {i+1} ({c.get('author_name','Anon')}, score:{c.get('score',0)}): {c.get('content','')[:200]}\n"

    system = (
        "You are a forum thread summarizer. Write a concise TL;DR (3-4 bullet points max). "
        "Highlight: the question asked, key solutions proposed, and the consensus/best answer if any. "
        "Be factual, not opinionated."
    )

    result = await call_llm(system, thread, "post_summarizer", user["id"], post_id)
    if not result:
        return {"summary": None, "reason": "Unable to generate summary", "comment_count": len(comments)}

    return {"summary": result, "post_id": post_id, "comment_count": len(comments), "ai_powered": True}

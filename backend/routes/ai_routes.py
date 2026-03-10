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


# ─── Phase 2: AI Signal Insights ───

@router.get("/signal-insights/{signal_id}")
async def get_signal_insights(signal_id: str, user: dict = Depends(get_current_user)):
    """Get AI-generated market context and insights for a trading signal."""
    db = deps.db

    signal = await db.trading_signals.find_one({"id": signal_id}, {"_id": 0})
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Get recent signal history for context
    recent_signals = await db.trading_signals.find(
        {}, {"_id": 0, "direction": 1, "product": 1, "profit_points": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)

    # Get member performance on this product
    product_trades = await db.trade_logs.find(
        {"user_id": user["id"], "signal_id": {"$exists": True}},
        {"_id": 0, "direction": 1, "actual_profit": 1, "performance": 1, "lot_size": 1}
    ).sort("created_at", -1).limit(20).to_list(20)

    signal_history = "\n".join(
        f"  {s.get('created_at','')[:10]} {s.get('direction','')} {s.get('product','')} pts:{s.get('profit_points','')}"
        for s in recent_signals
    )

    perf_summary = ""
    if product_trades:
        avg_profit = sum(t.get("actual_profit", 0) for t in product_trades) / len(product_trades)
        exceeded = sum(1 for t in product_trades if t.get("performance") == "exceeded")
        perf_summary = (
            f"Your last {len(product_trades)} trades: avg profit ${avg_profit:.2f}, "
            f"{exceeded}/{len(product_trades)} exceeded target."
        )

    system = (
        "You are a trading signal analyst. When a new signal drops, explain what to watch for. "
        "Be concise (3-4 bullet points), practical, and confidence-boosting without being reckless. "
        "Mention key considerations: timing, lot sizing, exit strategy."
    )

    prompt = (
        f"New signal: {signal.get('direction','')} on {signal.get('product','')}\n"
        f"Trade time: {signal.get('trade_time','')} {signal.get('trade_timezone','')}\n"
        f"Profit multiplier: {signal.get('profit_points','')}\n"
        f"Notes from admin: {signal.get('notes','None')}\n\n"
        f"Recent signal history:\n{signal_history}\n\n"
        f"{perf_summary}\n\n"
        f"Give the member practical insights for this signal."
    )

    result = await call_llm(system, prompt, "signal_insights", user["id"], signal_id)
    if not result:
        return {"insights": None, "signal_id": signal_id}

    return {"insights": result, "signal_id": signal_id, "ai_powered": True}


# ─── Phase 2: AI Trade Journal ───

@router.get("/trade-journal")
async def get_trade_journal(
    period: str = Query("daily", regex="^(daily|weekly)$"),
    user: dict = Depends(get_current_user),
):
    """AI-generated trade journal summarizing patterns, streaks, and discipline."""
    db = deps.db

    if period == "daily":
        since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    else:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    trades = await db.trade_logs.find(
        {"user_id": user["id"], "created_at": {"$gte": since}}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)

    if not trades:
        return {"journal": "No trades found for this period.", "period": period, "trade_count": 0}

    # Build trade details
    trade_lines = []
    for t in trades:
        trade_lines.append(
            f"{t.get('created_at','')[:16]}: {t.get('direction','')} "
            f"lot:{t.get('lot_size',0):.2f} "
            f"projected:${t.get('projected_profit',0):.2f} "
            f"actual:${t.get('actual_profit',0):.2f} "
            f"({t.get('performance','')})"
        )

    # Get streak
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "streak": 1})
    streak = user_doc.get("streak", 0) if user_doc else 0

    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    exceeded = sum(1 for t in trades if t.get("performance") == "exceeded")
    below = sum(1 for t in trades if t.get("performance") == "below")
    buy_trades = [t for t in trades if t.get("direction") == "BUY"]
    sell_trades = [t for t in trades if t.get("direction") == "SELL"]
    buy_profit = sum(t.get("actual_profit", 0) for t in buy_trades)
    sell_profit = sum(t.get("actual_profit", 0) for t in sell_trades)

    cache_extra = f"{period}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    system = (
        "You are a trading journal AI. Write a reflective journal entry about the trader's recent performance. "
        "Analyze patterns: BUY vs SELL performance, consistency, discipline, and emotional indicators. "
        "Be insightful and supportive. Format with clear sections. Keep to 4-5 key observations."
    )

    prompt = (
        f"Period: {'Today' if period == 'daily' else 'This Week'}\n"
        f"Trades ({len(trades)}):\n" + "\n".join(trade_lines) + "\n\n"
        f"Stats: Total profit: ${total_profit:.2f}, Exceeded: {exceeded}, Below: {below}\n"
        f"BUY trades: {len(buy_trades)} (${buy_profit:.2f}), SELL trades: {len(sell_trades)} (${sell_profit:.2f})\n"
        f"Current streak: {streak} days\n\n"
        f"Write a trade journal entry with patterns, observations, and one actionable tip."
    )

    result = await call_llm(system, prompt, "trade_journal", user["id"], cache_extra)
    if not result:
        return {"journal": None, "period": period, "trade_count": len(trades)}

    return {
        "journal": result,
        "period": period,
        "trade_count": len(trades),
        "stats": {
            "total_profit": round(total_profit, 2),
            "exceeded": exceeded,
            "below": below,
            "buy_profit": round(buy_profit, 2),
            "sell_profit": round(sell_profit, 2),
            "streak": streak,
        },
        "ai_powered": True,
    }


# ─── Phase 2: AI Goal Advisor ───

@router.get("/goal-advisor/{goal_id}")
async def get_goal_advisor(goal_id: str, user: dict = Depends(get_current_user)):
    """AI evaluates if a goal is realistic based on current performance."""
    db = deps.db

    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Get recent trade performance
    trades = await db.trade_logs.find(
        {"user_id": user["id"]}, {"_id": 0, "actual_profit": 1, "created_at": 1}
    ).sort("created_at", -1).limit(30).to_list(30)

    # Get account value
    from utils.calculations import calculate_account_value
    account_value = await calculate_account_value(db, user["id"], user)

    remaining = goal["target_amount"] - goal["current_amount"]
    progress = (goal["current_amount"] / goal["target_amount"] * 100) if goal["target_amount"] > 0 else 0

    avg_daily_profit = sum(t.get("actual_profit", 0) for t in trades) / max(len(trades), 1) if trades else 0

    # Calculate days to goal at current pace
    days_to_goal = remaining / avg_daily_profit if avg_daily_profit > 0 else float("inf")

    target_date_str = "No deadline set"
    days_left = None
    if goal.get("target_date"):
        try:
            td = datetime.fromisoformat(goal["target_date"])
            days_left = (td - datetime.now(timezone.utc)).days
            target_date_str = f"{days_left} days left (deadline: {td.strftime('%Y-%m-%d')})"
        except (ValueError, TypeError):
            pass

    system = (
        "You are a financial goal advisor. Evaluate whether the goal is realistic. "
        "Consider pace, deadline, and account trajectory. Give honest, practical advice. "
        "If ahead of schedule, celebrate. If behind, suggest adjustments (not guilt). "
        "Keep response to 3-4 concise points."
    )

    prompt = (
        f"Goal: {goal.get('name','')}\n"
        f"Target: ${goal['target_amount']:.2f}, Current: ${goal['current_amount']:.2f} ({progress:.1f}%)\n"
        f"Remaining: ${remaining:.2f}\n"
        f"Timeline: {target_date_str}\n"
        f"Account value: ${account_value:.2f}\n"
        f"Avg profit/trade: ${avg_daily_profit:.2f} (last {len(trades)} trades)\n"
        f"Days to goal at current pace: {days_to_goal:.0f}\n\n"
        f"Is this goal realistic? What adjustments should the member consider?"
    )

    result = await call_llm(system, prompt, "goal_advisor", user["id"], goal_id)
    if not result:
        return {"advice": None, "goal_id": goal_id}

    return {
        "advice": result,
        "goal_id": goal_id,
        "progress": round(progress, 1),
        "days_to_goal": round(days_to_goal) if days_to_goal != float("inf") else None,
        "days_left": days_left,
        "ai_powered": True,
    }


# ─── Phase 2: AI Anomaly Alert ───

@router.get("/anomaly-check")
async def check_anomalies(user: dict = Depends(get_current_user)):
    """Detect unusual trading patterns and provide proactive advice."""
    db = deps.db

    # Get last 30 trades
    trades = await db.trade_logs.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(30).to_list(30)

    if len(trades) < 5:
        return {"anomalies": None, "reason": "Not enough trade history for analysis", "trade_count": len(trades)}

    # Compute pattern metrics
    recent_5 = trades[:5]
    older_25 = trades[5:]

    recent_profit = sum(t.get("actual_profit", 0) for t in recent_5) / len(recent_5)
    older_profit = sum(t.get("actual_profit", 0) for t in older_25) / max(len(older_25), 1)

    recent_below = sum(1 for t in recent_5 if t.get("performance") == "below")

    # Check for missed trades (gaps in trading days)
    trade_dates = sorted(set(t.get("created_at", "")[:10] for t in trades if t.get("created_at")))
    gaps = 0
    for i in range(1, len(trade_dates)):
        try:
            d1 = datetime.fromisoformat(trade_dates[i - 1])
            d2 = datetime.fromisoformat(trade_dates[i])
            if (d2 - d1).days > 3:
                gaps += 1
        except (ValueError, TypeError):
            pass

    # Get streak
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "streak": 1})
    streak = user_doc.get("streak", 0) if user_doc else 0

    # Detect flags
    flags = []
    if recent_profit < older_profit * 0.5 and older_profit > 0:
        flags.append(f"Profit dropped: recent avg ${recent_profit:.2f} vs older avg ${older_profit:.2f}")
    if recent_below >= 3:
        flags.append(f"3+ below-target trades in last 5 ({recent_below}/5)")
    if gaps >= 2:
        flags.append(f"{gaps} extended gaps (3+ days) in trading schedule")
    if streak == 0 and len(trades) > 10:
        flags.append("Streak broken — currently at 0 days")

    if not flags:
        return {
            "anomalies": None,
            "status": "healthy",
            "message": "No concerning patterns detected. Keep up the good work!",
            "trade_count": len(trades),
        }

    cache_extra = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    system = (
        "You are a trading performance monitor. You've detected concerning patterns. "
        "Be empathetic, not alarming. Give 2-3 actionable suggestions. "
        "Frame issues as opportunities for improvement. Keep it brief."
    )

    prompt = (
        "Detected patterns:\n" + "\n".join(f"- {f}" for f in flags) + "\n\n"
        f"Last 5 trades avg profit: ${recent_profit:.2f}\n"
        f"Previous trades avg profit: ${older_profit:.2f}\n"
        f"Current streak: {streak} days\n"
        f"Below target: {recent_below}/5 recent trades\n\n"
        f"Provide supportive feedback and actionable advice."
    )

    result = await call_llm(system, prompt, "anomaly_alert", user["id"], cache_extra)

    return {
        "anomalies": result,
        "flags": flags,
        "status": "warning",
        "stats": {
            "recent_avg_profit": round(recent_profit, 2),
            "older_avg_profit": round(older_profit, 2),
            "recent_below": recent_below,
            "streak": streak,
            "gaps": gaps,
        },
        "ai_powered": True,
    }

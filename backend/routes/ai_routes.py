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

    # Get streak (computed dynamically)
    from utils.streak import compute_trading_streak
    streak = await compute_trading_streak(db, user["id"])

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

    # Get streak (computed dynamically from trade history)
    from utils.streak import compute_trading_streak
    streak = await compute_trading_streak(db, user["id"])

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

    # Get streak (computed dynamically)
    from utils.streak import compute_trading_streak
    streak = await compute_trading_streak(db, user["id"])
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


# ═══════ Phase 3: Community, Admin & Notifications ═══════


# ─── AI Answer Suggestions ───

@router.get("/answer-suggestion/{post_id}")
async def get_answer_suggestion(post_id: str, user: dict = Depends(get_current_user)):
    """Suggest answers from solved posts for the current forum thread."""
    db = deps.db

    post = await db.forum_posts.find_one({"id": post_id}, {"_id": 0, "title": 1, "content": 1})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Find solved posts with best answers
    solved = await db.forum_posts.find(
        {"status": "closed", "best_answer_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "id": 1, "title": 1, "content": 1, "best_answer_id": 1},
    ).sort("created_at", -1).limit(15).to_list(15)

    if not solved:
        return {"suggestion": None, "reason": "No solved posts to reference"}

    # Get best answer content for each solved post
    refs = []
    for sp in solved:
        ba = await db.forum_comments.find_one(
            {"id": sp["best_answer_id"]}, {"_id": 0, "content": 1}
        )
        if ba:
            refs.append(f"Q: {sp['title'][:80]}\nA: {ba['content'][:200]}")

    if not refs:
        return {"suggestion": None, "reason": "No best answers found"}

    system = (
        "You are a forum assistant. Based on solved Q&As, suggest a helpful answer for the current question. "
        "If no solved post is relevant, say so. Keep the suggestion concise and directly applicable. "
        "Do NOT make up information — only reference what's in the solved posts."
    )

    prompt = (
        f"Current question:\nTitle: {post['title']}\nContent: {post.get('content','')[:300]}\n\n"
        f"Solved Q&As for reference:\n" + "\n---\n".join(refs[:8]) + "\n\n"
        "Suggest an answer based on the solved posts. If none are relevant, say 'No similar solved questions found.'"
    )

    result = await call_llm(system, prompt, "answer_suggestion", user["id"], post_id)
    if not result:
        return {"suggestion": None, "reason": "Unable to generate suggestion"}

    return {"suggestion": result, "post_id": post_id, "ai_powered": True}


# ─── AI Member Risk Scoring (Admin only) ───

@router.get("/member-risk/{user_id}")
async def get_member_risk(user_id: str, user: dict = Depends(get_current_user)):
    """Admin-only: AI flags members showing concerning patterns with a risk score."""
    if user.get("role") not in ("master_admin", "super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    db = deps.db
    member = await db.users.find_one({"id": user_id}, {"_id": 0, "id": 1, "full_name": 1, "email": 1, "streak": 1, "role": 1, "created_at": 1})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get trade history
    trades = await db.trade_logs.find(
        {"user_id": user_id}, {"_id": 0, "actual_profit": 1, "performance": 1, "created_at": 1}
    ).sort("created_at", -1).limit(30).to_list(30)

    # Get recent activity
    last_trade_date = trades[0].get("created_at", "")[:10] if trades else "Never"
    total_profit = sum(t.get("actual_profit", 0) for t in trades)
    below_count = sum(1 for t in trades if t.get("performance") == "below")
    streak = member.get("streak", 0)

    # Check deposits
    deposits = await db.deposits.find(
        {"user_id": user_id, "type": "deposit"}, {"_id": 0, "amount": 1}
    ).sort("created_at", -1).limit(5).to_list(5)

    system = (
        "You are a member risk analyst for a trading platform admin. Score the member's risk level (Low/Medium/High) "
        "and explain in 2-3 bullet points. Focus on: inactivity, performance decline, missed trades. "
        "Be objective and data-driven. End with one recommended admin action."
    )

    prompt = (
        f"Member: {member.get('full_name', member.get('email','?'))}\n"
        f"Role: {member.get('role','member')}, Joined: {member.get('created_at','?')[:10]}\n"
        f"Last trade: {last_trade_date}, Current streak: {streak}\n"
        f"Last {len(trades)} trades: total profit ${total_profit:.2f}, below target: {below_count}\n"
        f"Recent deposits: {len(deposits)}\n\n"
        f"Assess this member's risk level and recommend action."
    )

    result = await call_llm(system, prompt, "member_risk", user["id"], user_id)
    if not result:
        return {"risk_assessment": None, "member_id": user_id}

    return {
        "risk_assessment": result,
        "member_id": user_id,
        "member_name": member.get("full_name") or member.get("email"),
        "stats": {
            "streak": streak,
            "last_trade": last_trade_date,
            "total_profit": round(total_profit, 2),
            "below_count": below_count,
            "trade_count": len(trades),
        },
        "ai_powered": True,
    }


# ─── AI Daily Trade Report (Admin only) ───

@router.get("/daily-report")
async def get_daily_report(user: dict = Depends(get_current_user)):
    """Admin-only: Auto-generated daily summary of all member trading activity."""
    if user.get("role") not in ("master_admin", "super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    db = deps.db
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    since = f"{today}T00:00:00"

    # Today's trades across all members
    all_trades = await db.trade_logs.find(
        {"created_at": {"$gte": since}}, {"_id": 0}
    ).to_list(200)

    # Today's signals
    signals = await db.trading_signals.find(
        {"created_at": {"$gte": since}}, {"_id": 0, "direction": 1, "product": 1, "profit_points": 1}
    ).to_list(10)

    # Active members count
    active_members = len(set(t.get("user_id") for t in all_trades))
    total_members = await db.users.count_documents({"role": {"$in": ["member", "licensee"]}})

    # Performance breakdown
    total_profit = sum(t.get("actual_profit", 0) for t in all_trades)
    exceeded = sum(1 for t in all_trades if t.get("performance") == "exceeded")
    below = sum(1 for t in all_trades if t.get("performance") == "below")
    perfect = sum(1 for t in all_trades if t.get("performance") == "perfect")

    # New deposits today
    new_deposits = await db.deposits.count_documents(
        {"type": "deposit", "created_at": {"$gte": since}}
    )

    cache_extra = f"daily_{today}"

    system = (
        "You are a trading platform daily report generator for admins. Write a concise executive summary. "
        "Include: trading activity overview, member participation, performance highlights, outliers, "
        "and one action item. Keep it under 5 bullet points. Use data."
    )

    prompt = (
        f"Date: {today}\n"
        f"Signals issued: {len(signals)}\n"
        f"Total trades: {len(all_trades)} by {active_members}/{total_members} members\n"
        f"Total profit: ${total_profit:.2f}\n"
        f"Performance: {exceeded} exceeded, {perfect} perfect, {below} below\n"
        f"New deposits: {new_deposits}\n\n"
        f"Generate the daily trading report."
    )

    result = await call_llm(system, prompt, "daily_report", user["id"], cache_extra)
    if not result:
        return {"report": None, "date": today}

    return {
        "report": result,
        "date": today,
        "stats": {
            "trade_count": len(all_trades),
            "active_members": active_members,
            "total_members": total_members,
            "total_profit": round(total_profit, 2),
            "exceeded": exceeded,
            "below": below,
            "perfect": perfect,
            "signals": len(signals),
            "deposits": new_deposits,
        },
        "ai_powered": True,
    }


# ─── AI Smart Notifications ───

class SmartNotifRequest(BaseModel):
    event_type: str  # e.g. "trade_logged", "streak_milestone", "deposit_received"
    context: dict = {}


@router.post("/smart-notification")
async def generate_smart_notification(body: SmartNotifRequest, user: dict = Depends(get_current_user)):
    """Generate a personalized notification message based on member context."""
    db = deps.db

    # Get user context
    user_doc = await db.users.find_one(
        {"id": user["id"]}, {"_id": 0, "full_name": 1, "streak": 1}
    )
    name = (user_doc or {}).get("full_name", "Member")
    streak = (user_doc or {}).get("streak", 0)

    system = (
        "Generate a short, personalized notification message (1-2 sentences max). "
        "Be warm, encouraging, and specific. Use the member's name."
    )

    prompt = (
        f"Member: {name}, Streak: {streak} days\n"
        f"Event: {body.event_type}\n"
        f"Context: {str(body.context)[:200]}\n\n"
        f"Generate a personalized notification message."
    )

    cache_extra = f"{body.event_type}_{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H')}"
    result = await call_llm(system, prompt, "smart_notification", user["id"], cache_extra)

    return {"message": result or f"Great job, {name}!", "event_type": body.event_type, "ai_powered": result is not None}


# ─── AI Commission Optimizer ───

@router.get("/commission-insights")
async def get_commission_insights(user: dict = Depends(get_current_user)):
    """Analyze referral commission patterns and suggest optimization strategies."""
    db = deps.db

    commissions = await db.commissions.find(
        {"user_id": user["id"], "skip_deposit": {"$ne": True}},
        {"_id": 0, "amount": 1, "traders_count": 1, "commission_date": 1, "created_at": 1},
    ).sort("created_at", -1).limit(30).to_list(30)

    if not commissions:
        return {"insights": None, "reason": "No commission history found"}

    total = sum(c.get("amount", 0) for c in commissions)
    avg = total / len(commissions)
    total_traders = sum(c.get("traders_count", 0) for c in commissions)

    # Analyze day-of-week patterns
    day_totals = {}
    for c in commissions:
        date_str = c.get("commission_date") or c.get("created_at", "")[:10]
        try:
            day = datetime.fromisoformat(date_str).strftime("%A")
            day_totals[day] = day_totals.get(day, 0) + c.get("amount", 0)
        except (ValueError, TypeError):
            pass

    best_day = max(day_totals, key=day_totals.get) if day_totals else "Unknown"

    cache_extra = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    system = (
        "You are a referral commission analyst. Analyze the pattern and suggest optimization. "
        "Be specific: mention best performing days, trends, and one actionable tip. "
        "Keep it to 3-4 concise points."
    )

    prompt = (
        f"Commission history (last {len(commissions)} entries):\n"
        f"Total earned: ${total:.2f}, Average per entry: ${avg:.2f}\n"
        f"Total referral traders: {total_traders}\n"
        f"Best day of week: {best_day} (${day_totals.get(best_day, 0):.2f})\n"
        f"Day breakdown: {', '.join(f'{d}: ${v:.2f}' for d, v in sorted(day_totals.items(), key=lambda x: -x[1]))}\n\n"
        f"Analyze patterns and suggest how to optimize referral commissions."
    )

    result = await call_llm(system, prompt, "commission_optimizer", user["id"], cache_extra)
    if not result:
        return {"insights": None, "reason": "Unable to generate insights"}

    return {
        "insights": result,
        "stats": {
            "total_earned": round(total, 2),
            "avg_per_entry": round(avg, 2),
            "total_traders": total_traders,
            "best_day": best_day,
            "entries_analyzed": len(commissions),
        },
        "ai_powered": True,
    }


# ─── AI Milestone Motivation ───

@router.get("/milestone/{goal_id}")
async def get_milestone_motivation(goal_id: str, user: dict = Depends(get_current_user)):
    """Generate personalized encouragement at goal milestones (25/50/75/100%)."""
    db = deps.db

    goal = await db.goals.find_one({"id": goal_id, "user_id": user["id"]}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    progress = (goal["current_amount"] / goal["target_amount"] * 100) if goal["target_amount"] > 0 else 0

    # Determine milestone bracket
    if progress >= 100:
        milestone = "completed"
    elif progress >= 75:
        milestone = "75%"
    elif progress >= 50:
        milestone = "50%"
    elif progress >= 25:
        milestone = "25%"
    else:
        milestone = "started"

    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "full_name": 1, "streak": 1})
    name = (user_doc or {}).get("full_name", "Member")

    system = (
        "You are a motivational coach celebrating a financial milestone. "
        "Write a short, personalized message (2-3 sentences). Be genuine, not generic. "
        "Reference the specific goal and progress. End with encouragement for the next step."
    )

    prompt = (
        f"Member: {name}\n"
        f"Goal: {goal.get('name','')}\n"
        f"Target: ${goal['target_amount']:.2f}\n"
        f"Current: ${goal['current_amount']:.2f} ({progress:.1f}%)\n"
        f"Milestone: {milestone}\n\n"
        f"Generate a personalized milestone celebration message."
    )

    cache_extra = f"{goal_id}_{milestone}"
    result = await call_llm(system, prompt, "milestone_motivation", user["id"], cache_extra)
    if not result:
        return {"motivation": None, "milestone": milestone}

    return {
        "motivation": result,
        "milestone": milestone,
        "progress": round(progress, 1),
        "goal_name": goal.get("name"),
        "ai_powered": True,
    }

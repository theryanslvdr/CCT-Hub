# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Financial tracking and community platform for CrossCurrent trading group. Features include profit tracking, trade monitoring, community forums, admin management, rewards, and real-time notifications.

## Core Requirements
1. **Profit Tracker** - Track deposits, withdrawals, commissions, daily projections, lot sizes, balance audit trails
2. **Trade Monitor** - Log trades, view signals, track streak, manage products/holidays
3. **Admin Panel** - Member management, transaction correction, license management, analytics, email templates
4. **Community Forum** - Posts, comments, categories, pinning, @mentions, merge, duplicate safeguard, solution validation
5. **Rewards System** - Points, badges, leaderboard, promotions
6. **Real-time Notifications** - WebSocket-based notifications for trades, forum activity, deposits
7. **BVE (Backtesting Virtual Environment)** - Isolated backtesting environment with separate data collections

## User Personas
- **Master Admin**: Full control — can merge posts, manage members, manage licenses
- **Super Admin / Admin**: Can manage members, merge forum posts
- **Member**: Trade logging, profit tracking, forum participation, rewards
- **Licensee**: View-only profit tracking with manager-traded status

## Architecture
### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py              (slim entry point, CORS, WebSocket, startup)
├── deps.py                (shared auth, DB access, JWT)
├── helpers.py             (notification, push, calculation helpers)
├── database.py            (Database connection class)
├── routes/
│   ├── auth_routes.py     (login, register, password reset, heartbeat)
│   ├── profit_routes.py   (deposits, withdrawals, daily-balances, onboarding, commissions)
│   ├── trade_routes.py    (trade logging, streak, signals, products)
│   ├── admin_routes.py    (members, licenses, analytics, transactions, email)
│   ├── general_routes.py  (notifications, uploads, health, version)
│   ├── forum.py           (posts, comments, categories, pinning, mentions, merge, validation, sidebar)
│   ├── rewards.py         (points, badges, leaderboard, promotions)
│   ├── bve.py             (BVE sessions, rewind, trade history, isolated trade delete)
│   ├── family.py, settings.py, currency.py, etc.
│   └── __init__.py
├── models/                (Pydantic models)
├── services/              (email, websocket, file upload, reports)
└── utils/                 (calculations, trading_days, rewards_engine)
```

### Frontend (React + ShadcnUI)
```
/app/frontend/src/
├── pages/
│   ├── ProfitTrackerPage.jsx   (main profit dashboard)
│   ├── TradeMonitorPage.jsx     (trade monitoring with BVE-aware data loading)
│   ├── ForumListPage.jsx        (forum listing with duplicate safeguard)
│   ├── ForumPostPage.jsx        (post view with sidebar, merge dialog)
│   └── admin/                   (admin pages)
├── components/
│   ├── profit/ DailyProjectionDialog.jsx
│   ├── BalanceAuditTrail.jsx
│   └── MyTransactionEdit.jsx
├── utils/
│   └── profitCalculations.js    (extracted pure functions)
├── contexts/
│   ├── BVEContext.jsx
│   └── WebSocketProvider.jsx
└── lib/
    └── api.js                   (API client with all endpoints)
```

## Key DB Collections
- `users` - User accounts with roles
- `deposits` - Financial transactions (deposits, withdrawals, profits)
- `commissions` - Commission records (with skip_deposit flag)
- `trade_logs` - Production individual trade records
- `trading_signals` - Admin-created trade signals
- `bve_sessions`, `bve_trade_logs`, `bve_deposits`, `bve_trading_signals` - BVE-isolated data
- `forum_posts`, `forum_comments` - Forum data
- `forum_merge_logs` - Audit trail for merged posts
- `rewards_stats`, `rewards_leaderboard`, `rewards_point_logs` - Rewards system
- `admin_notifications`, `user_notifications` - Notification system

## 3rd Party Integrations
- **Emailit** - Password reset and notification emails
- **Heartbeat** - Community member verification
- **CoinGecko** - Currency conversion rates
- **Cloudinary** - Image uploads
- **Publitio** - Forum image hosting
- **Rewards Platform (rewards.crosscur.rent)** - External rewards API with auto-sync
- **OpenRouter** - AI-powered semantic duplicate detection for forum (gpt-4o-mini)

## What's Been Implemented
- [x] Profit tracking (deposits, withdrawals, commissions, projections)
- [x] Trade monitoring (signals, streak, products, holidays)
- [x] Admin panel (members, licenses, transactions, analytics)
- [x] Community forum (CRUD, categories, pinning, @mentions)
- [x] Rewards system (points, badges, leaderboard)
- [x] Real-time notifications (WebSocket)
- [x] Balance audit trail
- [x] Member self-edit transactions
- [x] Admin transaction correction/deletion
- [x] Trade history streak fix (non-trading days handling)
- [x] Backend refactoring - server.py decomposed
- [x] Frontend refactoring - ProfitTrackerPage utilities extracted
- [x] Commission backfill with skip_deposit option (kept subtly for future use)
- [x] Clear Cache & Reload button
- [x] Auto batch sync every 4 hours
- [x] BVE data isolation fix (P0) — trade history and reset in BVE mode never touch production
- [x] Forum: Merge duplicate posts (master_admin + super_admin only, 8pts to source OP)
- [x] Forum: Duplicate post safeguard (pre-submission title+content similarity check)
- [x] Forum: Post details sidebar (contributors, awards, post date, solution validation)
- [x] Forum: Enhanced similar search (both title AND content)
- [x] Forum: "Solution still valid" button with timestamp
- [x] Commission Records: Type column distinguishing Balance vs Historical (skip_deposit)
- [x] OpenRouter AI-powered semantic duplicate detection for forum posts
- [x] Exit Trade function verified (all flows tested, performance calculation confirmed)
- [x] AI Trade Coach — Post-trade personalized coaching feedback per trade
- [x] AI Financial Summary — Weekly/monthly AI-powered profit analysis
- [x] AI Balance Forecast — 7/30/90 day balance projection
- [x] AI Post Summarizer — TL;DR for forum threads with 3+ comments
- [x] AI Service Layer — Shared backend module with DB caching, token limits, credit-efficient batching

## Prioritized Backlog

### P0 (Critical)
- None currently

### P1 (High)
- [ ] Publitio: Needs user to re-enter API keys in Platform Settings

### P2 (Medium)
- [ ] profitCalculations.js refactoring (currently fragile, overly complex)
- [ ] Backend Pydantic model audit across all routes
- [ ] Further ProfitTrackerPage.jsx decomposition
- [ ] Performance optimization (caching, pagination improvements)

### Future
- [ ] UI Refresh (major overhaul — awaiting user direction)

## AI Integration Roadmap

### Phase 1 — DONE
- [x] AI Trade Coach
- [x] AI Financial Summary (weekly/monthly)
- [x] AI Balance Forecast (7/30/90 day)
- [x] AI Post Summarizer
- [x] AI Duplicate Detection

### Phase 2 — Trading Intelligence — DONE
- [x] AI Signal Insights — Market context when signals drop
- [x] AI Trade Journal — Auto-generated daily/weekly trade summary
- [x] AI Goal Advisor — Evaluates goal realism
- [x] AI Anomaly Alert — Detects concerning performance patterns

### Phase 3 — Community, Admin & Notifications — DONE
- [x] AI Answer Suggestions — Suggests answers from solved posts
- [x] AI Member Risk Scoring — Admin risk flags
- [x] AI Daily Trade Report — Auto admin summary
- [x] AI Smart Notifications — Personalized alerts
- [x] AI Commission Optimizer — Referral commission insights
- [x] AI Milestone Motivation — Goal encouragement

### Phase 4 — Habit Tracker: Social Media Growth Engine
- [ ] AI-generated daily social media task sets
- [ ] Gradual difficulty progression
- [ ] Progressive unlocks as streaks build

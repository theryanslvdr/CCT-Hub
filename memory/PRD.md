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

## Referral & Rewards Expansion (March 2026)

### Phase 1 — Referral System Backend & Onboarding — DONE
- [x] Referral code management (set, validate, check uniqueness)
- [x] External rewards platform validation (best-effort via rewards.crosscur.rent)
- [x] Referred-by tracking (inviter code linking)
- [x] Mandatory onboarding modal for non-admin users
- [x] UserResponse model updated with referral_code, referred_by fields
- [x] Admin override for setting/changing referral codes
- [x] Referral events logging (code_set, referred_by_set)

### Phase 2 — Admin Referral Tree Visualization — DONE
- [x] Admin endpoint returns full referral tree data structure
- [x] Interactive collapsible tree view
- [x] D3 visual graph (react-d3-tree) with drag/zoom
- [x] Flat table view with search/pagination
- [x] Stats cards (Total Users, With Code, Referred, Onboarded %)
- [x] Sidebar nav item for super/master admin

### Phase 3 — Habit Rewards — DONE
- [x] Streak-based reward points (5/10/20/35/50/70/100 pts scaling with 7 tiers)
- [x] Auto-award on habit completion and social task all-done
- [x] Daily dedup prevents double-awarding
- [x] Manual habit-reward endpoint available

### Social Media Growth Engine Expansion — DONE (March 2026)
- [x] Expanded from 4 to 7 levels: Getting Started, Active Engager, Content Creator, Thought Leader, Brand Ambassador, Growth Hacker, Community Leader
- [x] Dynamic task counts: L1-3 = 3 tasks/day, L4-5 = 4 tasks/day, L6-7 = 5 tasks/day
- [x] Task types: engage, create, invite, collaborate, lead
- [x] Referral-aware AI prompts (includes user's referral code in task generation)
- [x] 7-level roadmap visualization (Seed → Sprout → Bloom → Crown → Star → Rocket → Diamond)
- [x] Reward point scaling: 5/10/20/35/50/70/100 per streak tier

### profitCalculations.js Refactoring — DONE (March 2026)
- [x] Split 620-line monolith into 3 focused modules:
  - formatters.js: Currency & number formatting
  - tradingDays.js: Business day, holiday, trading day checks
  - projections.js: Balance projection calculations
- [x] Barrel re-export file preserves all existing import paths

## Prioritized Backlog

### P0 (Critical)
- None currently

### P1 (High)
- [ ] Publitio: Needs user to re-enter API keys in Platform Settings

### P2 (Medium)
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

### Phase 4 — Habit Tracker: Social Media Growth Engine — DONE
- [x] AI-generated daily social media task sets (3 tasks/day)
- [x] 4-level progression system (Getting Started → Active Engager → Content Creator → Thought Leader)
- [x] Task completion tracking with all_done detection
- [x] Level roadmap visualization (Seed → Sprout → Bloom → Crown)
- [x] Platform-specific tasks (Instagram, Twitter, YouTube, LinkedIn, TikTok)
- [x] Streak-based level progression with next-level indicator

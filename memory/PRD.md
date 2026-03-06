# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Financial tracking and community platform for CrossCurrent trading group. Features include profit tracking, trade monitoring, community forums, admin management, rewards, and real-time notifications.

## Core Requirements
1. **Profit Tracker** - Track deposits, withdrawals, commissions, daily projections, lot sizes, balance audit trails
2. **Trade Monitor** - Log trades, view signals, track streak, manage products/holidays
3. **Admin Panel** - Member management, transaction correction, license management, analytics, email templates
4. **Community Forum** - Posts, comments, categories, pinning, @mentions, CRUD operations
5. **Rewards System** - Points, badges, leaderboard, promotions
6. **Real-time Notifications** - WebSocket-based notifications for trades, forum activity, deposits

## User Personas
- **Master Admin**: Full control over all features, member management, license management
- **Super Admin / Admin**: Can manage members and transactions
- **Member**: Trade logging, profit tracking, forum participation, rewards
- **Licensee**: View-only profit tracking with manager-traded status

## Architecture
### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py              (352 lines - slim entry point, CORS, WebSocket, startup)
├── deps.py                (shared auth, DB access, JWT)
├── helpers.py             (notification, push, calculation helpers)
├── database.py            (Database connection class)
├── routes/
│   ├── auth_routes.py     (705 lines - login, register, password reset, heartbeat)
│   ├── profit_routes.py   (2241 lines - deposits, withdrawals, daily-balances, onboarding)
│   ├── trade_routes.py    (1246 lines - trade logging, streak, signals, products)
│   ├── admin_routes.py    (4510 lines - members, licenses, analytics, transactions, email)
│   ├── general_routes.py  (472 lines - notifications, uploads, health, version)
│   ├── forum.py           (862 lines - posts, comments, categories, pinning, mentions)
│   ├── rewards.py         (1907 lines - points, badges, leaderboard, promotions)
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
│   ├── ProfitTrackerPage.jsx   (4450 lines - main profit dashboard)
│   ├── TradeMonitorPage.jsx     (trade monitoring)
│   ├── ForumListPage.jsx        (forum listing)
│   ├── ForumPostPage.jsx        (single post view)
│   └── admin/                   (admin pages)
├── components/
│   ├── profit/
│   │   └── DailyProjectionDialog.jsx (416 lines - extracted dialog)
│   ├── BalanceAuditTrail.jsx
│   └── MyTransactionEdit.jsx
├── utils/
│   └── profitCalculations.js    (612 lines - extracted pure functions)
└── contexts/
    └── WebSocketProvider.jsx
```

## Key DB Collections
- `users` - User accounts with roles
- `deposits` - Financial transactions (deposits, withdrawals, profits)
- `trade_logs` - Individual trade records
- `trading_signals` - Admin-created trade signals
- `licenses` - Licensee management
- `posts`, `comments` - Forum data
- `rewards_stats`, `rewards_leaderboard` - Rewards system
- `admin_notifications`, `user_notifications` - Notification system

## 3rd Party Integrations
- **Emailit** - Password reset and notification emails
- **Heartbeat** - Community member verification
- **CoinGecko** - Currency conversion rates
- **Cloudinary** - Image uploads
- **Publitio** - Forum image hosting
- **Rewards Platform** - External rewards API

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
- [x] **Backend refactoring** - server.py decomposed from 10,302 to 352 lines
- [x] **Frontend refactoring** - ProfitTrackerPage utilities and DailyProjectionDialog extracted

## P2 Backlog
- [ ] Further ProfitTrackerPage.jsx decomposition (ProjectionVision, StatsCards, TransactionDialogs)
- [ ] E2E test suite with pytest
- [ ] Performance optimization (caching, pagination improvements)

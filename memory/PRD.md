# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
A multi-phase financial trading dashboard platform with admin-configurable features:
- Trading signal blocking, "New Version" banner
- Admin-configurable notice banners and promotion pop-ups with analytics
- Full-featured habit tracker with streaks and signal gating
- Affiliate center with admin-managed resources and Chatbase embed
- Interactive habit gate flow with screenshot uploads
- Live admin activity feed and push notifications for habit completions
- PWA push notification support

## Core Architecture
- **Backend:** FastAPI (Python) on port 8001
- **Frontend:** React on port 3000  
- **Database:** MongoDB (crosscurrent_finance)
- **Auth:** JWT-based, admin roles: master_admin, super_admin, basic_admin

## Key Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`
- Login returns `access_token` field

## What's Implemented (All features complete)
1. **Phase 1:** Trading Signal Blocking + "New Version" Banner
2. **Phase 2:** Admin-configurable Banners, Popups + Analytics
3. **Phase 3:** Habit Tracker with Streaks + Signal Gate
4. **Phase 4:** Affiliate Center + Chatbase placeholder
5. **Interactive Habit Gate** on TradeMonitorPage
6. **Live Activity Feed** on Admin Dashboard
7. **PWA Push Notifications** (fixed VAPID key bug)
8. **Admin Habit Notifications** (push on member habit completion)

## Backend Route Architecture (Post-Refactoring)
```
/app/backend/
├── server.py          (8705 lines - main server, still contains auth/profit/trade/admin routers)
├── deps.py            (Auth functions, JWT handling)
├── helpers.py         (Push notification helpers: send_push_to_admins, send_push_notification, send_push_to_all_members)
├── database.py        (MongoDB connection singleton)
├── models/
│   ├── user.py        (UserCreate, UserResponse, TokenResponse, etc.)
│   ├── trade.py       (Trade models)
│   ├── common.py      (Deposit, Debt models)
│   └── settings.py    (Settings models)
└── routes/
    ├── habits.py      ✅ EXTRACTED (habits + admin habit management)
    ├── affiliate.py   ✅ EXTRACTED (affiliate resources + chatbase config)
    ├── activity_feed.py ✅ EXTRACTED (admin activity feed)
    ├── users.py       ✅ EXTRACTED (notification prefs, push subscriptions, profile, password)
    ├── settings.py    ✅ (previously extracted)
    ├── currency.py    ✅ (previously extracted)
    ├── debt.py        ✅ (previously extracted)
    ├── goals.py       ✅ (previously extracted)
    ├── api_center.py  ✅ (previously extracted)
    └── bve.py         ✅ (previously extracted)
```

## Frontend Component Architecture (Post-Refactoring)
```
/app/frontend/src/pages/admin/
├── AdminSettingsPage.jsx    (2713 lines - reduced from 3131)
└── settings/
    ├── HabitManagerCard.jsx      ✅ EXTRACTED (~130 lines)
    ├── AffiliateManagerCard.jsx  ✅ EXTRACTED (~155 lines)
    └── BannerAnalyticsCard.jsx   ✅ EXTRACTED (~60 lines)
```

## Bug Fixes Applied
- **P0:** PWA Push Notification fix (VAPID key in .env was concatenated)
- **P1:** Admin reset protection (recurring regression - admins can no longer self-reset)
- **LOW:** Broken image in Activity Feed (onError handler + length check)
- **CRITICAL:** Members couldn't see Habit Tracker or Affiliate Center (allowed_dashboards missing 'habits'/'affiliate'). Fixed: updated all DB records, registration defaults, and sidebar filtering
- **CRITICAL:** Soft-gate habit tracker not showing during admin simulation (signal block check now works for simulated member views)

## Mocked Integrations
- **Cloudinary:** File uploads stored locally in `/app/backend/uploads/`
- **Chatbase:** Placeholder iframe in Affiliate Center

## 3rd Party Integrations
- **pywebpush:** VAPID-encrypted web push notifications
- **Heartbeat API:** User verification for registration

## Remaining P2 Refactoring Backlog
1. Extract `auth_router` from server.py → `routes/auth.py`
2. Extract `trade_router` from server.py → `routes/trade.py`
3. Extract `profit_router` from server.py → `routes/profit.py`
4. Extract `admin_router` from server.py → `routes/admin.py`
5. Refactor `ProfitTrackerPage.jsx` (5235 lines) - address prop-drilling
6. Further break down `AdminSettingsPage.jsx` tab contents

## Future / Nice-to-Have
- Replace local file uploads with Cloudinary
- Chatbase bot embed (production integration)

## Test Reports
- iteration_106: P0 notification fix verified
- iteration_107: Full regression after refactoring (17/17 backend, all frontend ✅)

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
- Licensee management (Extended & Honorary) with profit tracking

## Core Architecture
- **Backend:** FastAPI (Python) on port 8001
- **Frontend:** React on port 3000  
- **Database:** MongoDB (crosscurrent_finance)
- **Auth:** JWT-based, admin roles: master_admin, super_admin, basic_admin

## Key Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`
- Login returns `access_token` field

## What's Implemented
1. **Phase 1:** Trading Signal Blocking + "New Version" Banner
2. **Phase 2:** Admin-configurable Banners, Popups + Analytics
3. **Phase 3:** Habit Tracker with Streaks + Signal Gate
4. **Phase 4:** Affiliate Center + Chatbase placeholder
5. **Interactive Habit Gate** on TradeMonitorPage
6. **Live Activity Feed** on Admin Dashboard
7. **PWA Push Notifications** (fixed VAPID key bug)
8. **Admin Habit Notifications** (push on member habit completion)
9. **Honorary Licensee Profit Tracker** - Dynamic account value calculation with quarterly compounding

## Recent Bug Fixes (Feb 17, 2026)
- **P0: Honorary Licensee Profit Tracker** - Fixed 3 critical bugs:
  - Manager Traded column: Fixed by filtering out `did_not_trade` entries from master admin trade queries
  - Account value sync: Fixed by implementing `calculate_honorary_licensee_value()` for dynamic calculation
  - Profit stuck at $0: Fixed by calculating profit from dynamic account_value instead of stale `current_amount`
- **P1: Admin Habits 404**: Admin habit CRUD endpoints confirmed working in preview (POST/GET/DELETE /api/admin/habits)

## Pending/Upcoming Tasks
### P0 - Immediate
- **Family Account Feature**: Design & implement family accounts for Honorary Licensees (plan required before coding)

### P1 - High Priority
- **Failed to Save Habit (Live Site)**: Recurring 404 on user's live site. Endpoints work in preview. Need user's network logs to debug production-specific issue.

### P2 - Backlog
- Backend Refactoring: Extract remaining routers (auth, trade, admin) from server.py
- Frontend Refactoring: Break down AdminSettingsPage.jsx and ProfitTrackerPage.jsx
- Cloudinary integration for file uploads
- Chatbase integration placeholder

## Key Technical Details
- Honorary licensee account_value is dynamically calculated using quarterly compounding via `calculate_honorary_licensee_value()` in `/app/backend/utils/calculations.py`
- All master admin trade queries now filter out `did_not_trade` entries with `{"did_not_trade": {"$ne": True}}`
- Licensee daily projection endpoint now returns field names consistent with simulation endpoint (start_value, lot_size, daily_profit)

## Backend Route Architecture
```
/app/backend/
├── server.py          (Main server - auth/profit/trade/admin routers)
├── utils/calculations.py (Financial calculations including calculate_honorary_licensee_value)
├── deps.py            (Auth functions, JWT handling)
├── helpers.py         (Push notification helpers)
├── database.py        (MongoDB connection singleton)
└── routes/
    ├── habits.py      (habits + user habit operations)
    ├── affiliate.py   (affiliate resources)
    ├── activity_feed.py (admin activity feed)
    ├── users.py       (notification prefs, profile)
    ├── settings.py    (platform settings)
    ├── admin.py       (admin operations)
    └── ...other extracted routers
```

## 3rd Party Integrations
- **pywebpush:** VAPID-encrypted web push notifications
- **Chatbase:** Placeholder iframe (not integrated)
- **Cloudinary:** Placeholder (not integrated)

## Mocked Features
- Cloudinary file upload integration
- Chatbase integration in Affiliate Center

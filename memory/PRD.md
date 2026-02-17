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
- Licensee management (Extended, Honorary, Honorary FA) with profit tracking
- Family Account feature for Honorary FA licensees

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
10. **Family Account Feature (Honorary FA)** - Complete CRUD + projections + withdrawal flow

## Recent Implementation (Feb 17, 2026)

### Profit Tracker Bug Fixes (P0)
- Fixed Manager Traded column by filtering `did_not_trade` entries
- Fixed account value sync with dynamic `calculate_honorary_licensee_value()`
- Fixed profit stuck at $0 — now calculated from dynamic account_value

### Family Account Feature (P0) — NEW
**Backend:**
- New license type: `honorary_fa` (Family Account variant)
- New `/app/backend/routes/family.py` with full CRUD endpoints
- Family members stored in `family_members` collection
- Each family member has independent profit tracking (quarterly compounding)
- 3-stage withdrawal flow: family → parent approval → admin approval
- Push notifications at each withdrawal stage
- Max 5 family members per licensee

**Frontend:**
- New `FamilyAccountsPage.jsx` with member cards, detail view, withdrawal management
- Route `/family-accounts` registered in App.js
- Sidebar navigation shows "Family Accounts" only for honorary_fa licensees
- AdminLicensesPage updated with honorary_fa option in create/change forms

**API Endpoints:**
- `POST /api/admin/family/members/{user_id}` — Admin adds family member
- `GET /api/admin/family/members/{user_id}` — Admin lists family members
- `GET /api/admin/family/members/{user_id}/{member_id}/projections` — Admin views projections
- `GET/POST/PUT/DELETE /api/family/members` — Licensee CRUD
- `GET /api/family/members/{id}/projections` — Licensee views member projections
- `POST /api/family/members/{id}/withdraw` — Withdrawal request
- `PUT /api/family/withdrawals/{id}/approve` — Parent approves
- `GET/PUT /api/admin/family/withdrawals` — Admin manages withdrawals

## Pending/Upcoming Tasks
### P1 - High Priority
- **Failed to Save Habit (Live Site)**: 404 on user's live site. Works in preview. Deployment issue.

### P2 - Backlog
- Backend Refactoring: Extract remaining routers from server.py
- Frontend Refactoring: AdminSettingsPage.jsx, ProfitTrackerPage.jsx
- Cloudinary integration for file uploads
- Chatbase integration placeholder

## Key DB Collections
- `users` — license_type field: "extended", "honorary", "honorary_fa"
- `licenses` — active license documents
- `family_members` — {id, parent_user_id, parent_license_id, name, relationship, email, starting_amount, effective_start_date, is_active}
- `family_withdrawals` — {id, family_member_id, parent_user_id, amount, status, created_at, parent_approved_at, admin_approved_at}
- `trade_logs` — master admin trade logs (did_not_trade entries filtered)
- `licensee_trade_overrides` — manual overrides for traded/not-traded days

## 3rd Party Integrations
- **pywebpush:** VAPID-encrypted web push notifications

## Mocked Features
- Cloudinary file upload integration
- Chatbase integration in Affiliate Center

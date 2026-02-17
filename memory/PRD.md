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

## What's Implemented
1. Phase 1-4: Signal blocking, banners, popups, habits, affiliate
2. Interactive Habit Gate, Live Activity Feed, PWA Push Notifications
3. Honorary Licensee Profit Tracker - Dynamic quarterly compounding
4. **Family Account Feature** - Complete CRUD, projections, withdrawal flow
5. **1:1 Simulation** - Admin can simulate Honorary FA view with Family Accounts
6. **Licensee Nav Restrictions** - Habits & Affiliate hidden from ALL licensees

## Recent Changes (Feb 17, 2026)

### Profit Tracker Bug Fixes
- Filtered `did_not_trade` entries from all master admin trade queries
- Dynamic `calculate_honorary_licensee_value()` for account value
- Fixed profit stuck at $0

### Family Account Feature
- New `honorary_fa` license type with family member CRUD (max 5)
- Independent profit tracking per family member (quarterly compounding)
- 3-stage withdrawal: family → parent approval → admin approval
- Push notifications at each withdrawal stage
- Admin simulation shows 1:1 licensee view with family data

### Simulation & Navigation
- "Honorary FA (Family) View" in Simulate View dropdown
- Sidebar correctly shows only: Dashboard, Profit Tracker, Deposit/Withdrawal, Family Accounts
- Habits & Affiliate hidden from all licensees (both direct & simulated)
- Admin sidebar retains Habits & Affiliate (non-licensee view)

## Pending Tasks
### P1
- Failed to Save Habit (Live Site) - 404 in production, works in preview

### P2 - Backlog
- Backend refactoring (extract auth/trade/admin routers from server.py)
- Frontend refactoring (AdminSettingsPage.jsx, ProfitTrackerPage.jsx)
- Cloudinary integration, Chatbase integration

## Key Collections
- `family_members`: {id, parent_user_id, parent_license_id, name, relationship, email, starting_amount, effective_start_date, is_active}
- `family_withdrawals`: {id, family_member_id, parent_user_id, amount, status, created_at, parent_approved_at, admin_approved_at}

## Mocked Features
- Cloudinary file upload, Chatbase integration

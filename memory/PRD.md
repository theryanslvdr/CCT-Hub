# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
A multi-phase financial trading dashboard platform with admin-configurable features including licensee management, family accounts, and profit tracking with quarterly compounding.

## Core Architecture
- **Backend:** FastAPI (Python) on port 8001
- **Frontend:** React on port 3000  
- **Database:** MongoDB (crosscurrent_finance)
- **Auth:** JWT-based, admin roles: master_admin, super_admin, basic_admin
- Master Admin: `iam@ryansalvador.com` / `admin123`

## What's Implemented
1. Phase 1-4: Signal blocking, banners, popups, habits, affiliate
2. Interactive Habit Gate, Live Activity Feed, PWA Push Notifications
3. Honorary Licensee Profit Tracker - Dynamic quarterly compounding
4. Family Account Feature - CRUD, projections, 3-stage withdrawal flow
5. 1:1 Admin Simulation for Honorary FA licensees
6. Licensee Nav Restrictions - Habits & Affiliate hidden from ALL licensees
7. **Admin Reset: Starting Balance & Trade Start Date** for both licensees and family members

## Recent Changes (Feb 17, 2026)

### Profit Tracker Bug Fixes
- Filtered `did_not_trade` entries from master admin trade queries
- Dynamic `calculate_honorary_licensee_value()` for account value
- Fixed profit stuck at $0

### Family Account Feature
- `honorary_fa` license type with family member CRUD (max 5)
- Independent profit tracking per family member
- 3-stage withdrawal: family → parent → admin approval
- Admin simulation shows 1:1 licensee view

### Admin Reset Features
- **Reset Starting Balance**: `POST /api/admin/licenses/{id}/reset-balance` — Projections recalculate with new base
- **Set Trade Start Date**: `PUT /api/admin/licenses/{id}/effective-start-date` — Projections compound from new date
- **Family Member Reset**: `PUT /api/admin/family/members/{userId}/{memberId}/reset` — Reset starting_amount and/or effective_start_date
- All resets are immediately reflected in dynamic projections (no stale data)

## Key API Endpoints
### License Management
- `POST /api/admin/licenses/{id}/reset-balance` — Reset starting balance
- `PUT /api/admin/licenses/{id}/effective-start-date` — Set trade start date
- `POST /api/admin/licenses/{id}/change-type` — Convert license type
- `GET /api/admin/licenses/{id}/projections` — View projections

### Family Accounts
- `POST/GET /api/family/members` — Licensee CRUD
- `GET /api/family/members/{id}/projections` — Member projections
- `POST /api/family/members/{id}/withdraw` — Withdrawal request
- `PUT /api/family/withdrawals/{id}/approve` — Parent approves
- `GET/POST /api/admin/family/members/{userId}` — Admin CRUD
- `PUT /api/admin/family/members/{userId}/{memberId}/reset` — Admin reset
- `GET/PUT /api/admin/family/withdrawals` — Admin manages withdrawals

## Pending Tasks
### P1
- Failed to Save Habit (Live Site) — 404 in production, works in preview. Needs redeployment.
- **Live site needs deployment of latest code** — Family accounts, reset features, and other new endpoints will not work until redeployed.

### P2 - Backlog
- Backend refactoring (extract auth/trade/admin routers from server.py)
- Frontend refactoring (AdminSettingsPage.jsx, ProfitTrackerPage.jsx)
- Cloudinary/Chatbase integrations

## Mocked Features
- Cloudinary file upload, Chatbase integration

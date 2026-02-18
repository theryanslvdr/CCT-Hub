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
7. Admin Reset: Starting Balance & Trade Start Date for both licensees and family members
8. **Admin Temp Password with Forced Reset** - Admin sets temp password, user sees force-change dialog on login
9. **P0 Fix: Profit Tracker Data Consistency** - All endpoints (direct login + admin simulation) now return dynamically calculated values for honorary licensees

## Recent Changes (Feb 18, 2026)

### P0 Bug Fix: Profit Tracker Data Discrepancy
- **Root Cause:** `/api/profit/licensee/welcome-info` was returning stale `license.current_amount` instead of dynamically calculated value
- **Fix:** Applied `calculate_honorary_licensee_value()` to welcome-info endpoint
- **Verified:** Direct login and admin simulation now show identical account values ($6,530 for Rizza Miles)
- All 4 endpoints now consistent: `/api/profit/summary`, `/api/profit/licensee/welcome-info`, `/api/admin/members/{id}`, `/api/admin/members/{id}/simulate`

### Admin Temp Password Feature
- `POST /api/admin/members/{user_id}/set-temp-password` - Sets temp password + `must_change_password` flag
- `POST /api/auth/force-change-password` - User changes password after temp password login
- Login endpoint returns `must_change_password: true` when applicable
- Frontend shows forced password change dialog (non-dismissible) before redirect
- Rizza Miles current password: `rizza123`

## Key API Endpoints
### License Management
- `POST /api/admin/licenses/{id}/reset-balance` - Reset starting balance
- `PUT /api/admin/licenses/{id}/effective-start-date` - Set trade start date
- `POST /api/admin/licenses/{id}/change-type` - Convert license type
- `GET /api/admin/licenses/{id}/projections` - View projections

### Family Accounts
- `POST/GET /api/family/members` - Licensee CRUD
- `GET /api/family/members/{id}/projections` - Member projections
- `POST /api/family/members/{id}/withdraw` - Withdrawal request
- `PUT /api/family/withdrawals/{id}/approve` - Parent approves
- `GET/POST /api/admin/family/members/{userId}` - Admin CRUD
- `PUT /api/admin/family/members/{userId}/{memberId}/reset` - Admin reset

### Auth
- `POST /api/admin/members/{user_id}/set-temp-password` - Admin sets temp password
- `POST /api/auth/force-change-password` - User changes temp password

## Pending Tasks
### P1
- Live site needs deployment of latest code - Family accounts, reset features, temp password, and P0 fix will not work until redeployed
- Failed to Save Habit (Live Site) - 404 in production, works in preview. Needs redeployment.

### P2 - Backlog
- Backend refactoring (extract auth/trade/admin routers from server.py)
- Frontend refactoring (AdminSettingsPage.jsx, ProfitTrackerPage.jsx)
- Cloudinary/Chatbase integrations

## Mocked Features
- Cloudinary file upload, Chatbase integration

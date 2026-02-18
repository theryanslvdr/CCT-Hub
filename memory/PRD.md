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
8. Admin Temp Password with Forced Reset on first login
9. **P0 Fix: Profit Tracker Data Consistency** - ALL endpoints return dynamically calculated values
10. **Simulation Bug Fix** - `/api/admin/licenses` now computes dynamic values for honorary licensees (was returning stale `current_amount`)
11. **Licensee Dashboard Redesign** - Year-by-year growth projections (1yr, 2yr, 3yr, 5yr) replace Trade Performance; Family Member Stats replace Recent Trades
12. **Admin Add Family Member on Behalf** - Master admin can add family members for licensees from the Licenses page

## Key API Endpoints
### License Management
- `GET /api/admin/licenses` - Returns all licenses with dynamically calculated values
- `POST /api/admin/licenses/{id}/reset-balance` - Reset starting balance
- `PUT /api/admin/licenses/{id}/effective-start-date` - Set trade start date
- `POST /api/admin/licenses/{id}/change-type` - Convert license type

### Family Accounts
- `POST/GET /api/family/members` - Licensee CRUD
- `POST /api/admin/family/members/{userId}` - Admin adds member on behalf of licensee
- `GET /api/family/members/{id}/projections` - Member projections
- `POST /api/family/members/{id}/withdraw` - Withdrawal request

### Profit & Projections
- `GET /api/profit/summary` - Dynamic financial summary
- `GET /api/profit/licensee/year-projections` - 1yr, 2yr, 3yr, 5yr growth projections
- `GET /api/profit/licensee/welcome-info` - Dynamic current_balance for honorary
- `GET /api/profit/licensee/daily-projection` - Daily trade projections

### Auth
- `POST /api/admin/members/{user_id}/set-temp-password` - Admin sets temp password
- `POST /api/auth/force-change-password` - User changes temp password

## Pending Tasks
### P1
- Live site needs redeployment - all new features (family accounts, temp password, P0 fix, dashboard redesign, simulation fix) require redeployment
- "Failed to Save Habit" on live site - resolved by redeployment

### P2 - Backlog
- Backend refactoring (extract remaining routers from server.py)
- Frontend refactoring (AdminSettingsPage.jsx, ProfitTrackerPage.jsx)
- Cloudinary/Chatbase integrations

## Mocked Features
- Cloudinary file upload, Chatbase integration

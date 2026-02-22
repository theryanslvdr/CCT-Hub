# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
A financial tracking platform for the CrossCurrent trading community. Supports admin-managed honorary licensees, extended licensees, family accounts, and direct traders. Key feature: dynamic account value calculation for honorary licensees based on master admin trading performance.

## Core Architecture
- **Frontend:** React (Vite) with Shadcn/UI, TailwindCSS
- **Backend:** FastAPI with Motor (async MongoDB)
- **Database:** MongoDB

## User Roles
- **Master Admin** (iam@ryansalvador.com): Full control, manages all members/licensees
- **Super Admin / Admin**: Limited admin capabilities
- **Member**: Regular trader with profit tracking
- **Licensee (Honorary/Honorary FA/Extended)**: Managed accounts whose value grows based on master admin trades

## What's Been Implemented

### Core Features (Complete)
- User authentication with JWT tokens
- Admin dashboard with member management
- Trade logging and profit tracking (Projection Vision)
- Deposit/Withdrawal management
- Currency conversion (USDT/PHP/EUR/GBP)
- Signal management (active trade signals)
- License management (create, edit, deactivate, change type)
- Maintenance mode with master admin override
- BVE (Beta Virtual Environment) mode
- Year-by-year growth projections for licensees
- Admin-initiated password reset (temp password, force change)
- User-initiated "Forgot Password" flow (token-based)

### Family Account System (Complete - Feb 22, 2026)
- Family members (up to 5) for Honorary FA licensees
- **Deposit date** required when adding member → effective trading starts NEXT TRADING DAY after deposit
- Family member growth computed SAME as parent licensee (based on master admin trades, quarterly compounding)
- Family member projections show full history from effective start date with manager traded flags
- Family member balance is SEPARATE money from licensee
- Dashboard "Overall Account Growth" card shows: Your Account + Family Total + Combined Value + Combined Profit
- Admin can add family members on behalf of licensees
- Family member withdrawal flow (parent approval → admin approval)

### Bug Fixes Completed (Feb 22, 2026)
1. **P0: Stale Data Discrepancy** - All endpoints use dynamic `calculate_honorary_licensee_value` consistently
2. **P0: Incorrect $0 Total Profit** - Profit = `account_value - starting_amount` for licensees
3. **P0: Total Trades = 0** - Now counts master admin trade days since licensee's effective start date
4. **P1: Incomplete Projection History** - Frontend uses `effectiveStartDate` from license data for past months
5. **P1: Dashboard Stuck Loading** - Added `projectionError` state with error UI and retry
6. **P1: Forgot Password** - Full backend + frontend flow implemented
7. **P2: License Conversion Preservation** - Honorary ↔ Honorary FA is in-place update
8. **Dashboard: Growth Projections blank** - Fixed: admin simulation uses `user_id` param; direct login works correctly
9. **Dashboard: Family Members blank** - Fixed: key was `members` instead of `family_members`
10. **Dashboard: Performance Overview/Recent Trades visible** - Hidden when viewing licensee dashboard (including admin simulation)

## Mocked Features
- Cloudinary file upload, Chatbase integration

## Prioritized Backlog

### P2 - Improvements
- Backend refactoring: Extract remaining routers from server.py
- Frontend refactoring: AdminSettingsPage.jsx, ProfitTrackerPage.jsx
- Email integration for password reset tokens (currently token returned in API response)

### P3 - Future
- Cloudinary integration for file uploads
- Chatbase integration for chat support

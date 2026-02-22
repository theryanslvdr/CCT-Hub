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

### Family Account System (Complete)
- Family members (up to 5) for Honorary FA licensees
- **Deposit date** required → trading starts NEXT TRADING DAY after deposit
- Family member growth computed same as parent licensee (master admin trades, quarterly compounding)
- Family member projections show full history from effective start date
- Dashboard "Overall Account Growth" card: Your Account + Family Total + Combined Value + Combined Profit
- Admin can add/remove family members on behalf of licensees (via admin endpoints)
- Admin simulation mode correctly uses admin API endpoints for family operations
- Family member withdrawal flow (parent approval → admin approval)

### Robustness: License Check (Critical Fix)
- ALL family endpoints use `verify_honorary_fa_license()` helper that queries `licenses` collection directly
- Never relies on `user.license_type` field (unreliable in production)
- Same pattern applied to all financial data endpoints

### Bug Fixes Completed
1. Stale Data Discrepancy - All endpoints use dynamic calculation
2. Incorrect $0 Total Profit - Profit = account_value - starting_amount
3. Total Trades = 0 for licensees - Now counts master admin trade days
4. Incomplete Projection History - Frontend uses effectiveStartDate from license data
5. Dashboard Stuck Loading - Error state with retry button
6. Forgot Password - Full backend + frontend flow
7. License Conversion Preservation - Honorary ↔ Honorary FA in-place update
8. Dashboard Growth Projections blank - Admin simulation uses user_id param
9. Dashboard Family Members blank - Fixed key mismatch (members → family_members)
10. Performance Overview/Recent Trades hidden for licensee dashboard
11. Family member "Not Found" on add - Robust license check via licenses collection
12. Admin simulation family member add - Frontend uses admin endpoints when simulating

## Mocked Features
- Cloudinary file upload, Chatbase integration

## Prioritized Backlog

### P2 - Improvements
- Backend refactoring: Extract remaining routers from server.py
- Frontend refactoring: AdminSettingsPage.jsx, ProfitTrackerPage.jsx
- Email integration for password reset tokens

### P3 - Future
- Cloudinary integration for file uploads
- Chatbase integration for chat support

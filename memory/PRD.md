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
- Family Account system (Honorary FA licensees)
- Admin-initiated password reset (temp password, force change)
- License management (create, edit, deactivate, change type)
- Maintenance mode with master admin override
- BVE (Beta Virtual Environment) mode
- Year-by-year growth projections for licensees
- Admin "Add Family Member" on behalf of licensee

### Bug Fixes Completed (Feb 22, 2026)
1. **P0: Stale Data Discrepancy** - Fixed: All endpoints now use dynamic `calculate_honorary_licensee_value` consistently. Dashboard, Profit Tracker, and Sidebar all show correct dynamic values for licensees.
2. **P0: Incorrect $0 Total Profit** - Fixed: `get_user_financial_summary` now correctly calculates profit as `account_value - starting_amount` for licensees.
3. **P0: Total Trades shows 0 for licensees** - Fixed: Now counts master admin trade days since licensee's effective start date.
4. **P1: Incomplete Projection History** - Fixed: Frontend `generateMonthlyProjection` now uses `effectiveStartDate` from license data to show past months even without personal trades.
5. **P1: Dashboard Stuck Loading Projections** - Fixed: Added `projectionError` state with error UI and retry button.
6. **P1: Forgot Password** - Implemented: Backend endpoints (`POST /api/auth/forgot-password`, `POST /api/auth/reset-password`) + Frontend UI on login page.
7. **P2: License Conversion Data Preservation** - Fixed: Honorary ↔ Honorary FA conversion is now in-place update (preserves license ID, starting_amount, effective_start_date, all financial data).
8. **P2: Admin Add Family Member** - Verified working.

## Mocked Features
- Cloudinary file upload, Chatbase integration

## Prioritized Backlog

### P1 - Next Up
- (None currently - all critical bugs resolved)

### P2 - Improvements
- Backend refactoring: Extract remaining routers from server.py
- Frontend refactoring: AdminSettingsPage.jsx, ProfitTrackerPage.jsx
- Email integration for password reset tokens (currently token returned in API response)

### P3 - Future
- Cloudinary integration for file uploads
- Chatbase integration for chat support

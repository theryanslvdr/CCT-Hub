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

## Core Financial Formula
```
Quarterly Fixed Daily Profit = round((Account Value at Quarter Start / 980) * 15, 2)
```
- Daily profit is FIXED for the entire calendar quarter (Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec)
- Recalculated at each new quarter start using the accumulated account value
- Trading days = weekdays excluding US market holidays (~250/year)
- US Market Holidays: New Year's, MLK Day, Presidents' Day, Good Friday, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, Christmas
- Weekend-to-weekday observance: Sat holidays → preceding Fri, Sun holidays → following Mon

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
- Admin-initiated password reset (temp password, force change)
- User-initiated "Forgot Password" flow (token-based)

### Growth Projection System (Complete - Feb 22, 2026)
- **Year Projections**: 1, 2, 3, 5 year projections with quarterly compounding
- **Daily Projections**: Day-by-day breakdown showing past (actual trades) and future (projected)
- **Holiday-aware**: US market holidays excluded from trading days
- **Quarter breakdown**: Each projection shows per-quarter detail (trading days, daily profit, start/end values)
- **Correct formula**: `round((balance/980)*15, 2)` — no intermediate lot_size rounding
- **Trading days utility**: `/app/backend/utils/trading_days.py` handles holidays, Easter calc, observed dates

### Family Account System (Complete)
- Family members (up to 5) for Honorary FA licensees
- Deposit date required: trading starts NEXT TRADING DAY after deposit
- Family member growth computed same as parent licensee
- Family member projections use same formula with holiday exclusion
- Dashboard "Overall Account Growth" card
- Admin can add/edit/remove family members via admin endpoints
- Admin simulation mode uses correct admin API endpoints for ALL operations
- Family member withdrawal flow (parent approval -> admin approval)

### Robustness: License Check (Critical Fix)
- ALL family endpoints use `verify_honorary_fa_license()` from licenses collection
- Never relies on `user.license_type` field (unreliable in production)

## Key API Endpoints

### Projections
- `GET /api/profit/licensee/year-projections` - Year 1/2/3/5 projections with quarter breakdown
- `GET /api/profit/licensee/daily-projection` - Daily entries (past: actual, future: projected)

### Family & Auth
- `POST /api/auth/forgot-password` - Generate reset token
- `POST /api/auth/reset-password` - Reset password with token
- `GET/POST /api/family/members` - Licensee family management
- `GET/POST/PUT/DELETE /api/admin/family/members/{user_id}[/{member_id}]` - Admin family management

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

## Test Credentials
- Master Admin: iam@ryansalvador.com / admin123
- Licensee (Honorary FA): rizza.miles@gmail.com / rizza123
- Rizza's user ID: 19ccb9d7-139f-4918-a662-ad72483010b1

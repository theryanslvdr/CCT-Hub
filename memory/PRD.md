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
- Daily profit is FIXED for the entire calendar quarter
- Recalculated at each new quarter start using the accumulated account value
- Trading days = weekdays excluding US market holidays (~250/year)

## What's Been Implemented

### Core Features (Complete)
- User authentication with JWT tokens
- Admin dashboard with member management
- Trade logging and profit tracking
- Deposit/Withdrawal management
- License management, Maintenance mode, BVE mode
- Password reset (admin-initiated + user-initiated "Forgot Password")

### Growth Projection System (Complete - Updated Feb 24, 2026)
- Year Projections: 1, 2, 3, 5 year with quarterly compounding
- **DUAL PROJECTION VIEW (Option C - Feb 24, 2026):**
  1. **License Year End**: Balance at end of license Year 1/2/3/5 from `effective_start_date` using `starting_amount`
  2. **Forward Projections**: Balance after 1/2/3/5 years from TODAY using current `account_value`
- Daily Projections: past (actual trades) + future (projected)
- Holiday-aware (US market holidays excluded)
- Trading days utility: `/app/backend/utils/trading_days.py`
- **Quarterly Compounding Fix**: Frontend `generateMonthlyProjection` now uses fixed daily profit per quarter (not daily recalculation)

### Family Account System (Complete)
- Family members (up to 5) for Honorary FA licensees
- Admin can add/edit/remove family members via admin endpoints
- Dashboard combined account overview

### Rewards & Points System (Complete - Feb 23, 2026)

**Points System:**
- Single currency: POINTS (100 pts = 1 USDT)
- Continuous base points: signup(25), first_trade(25), deposit(50/50 USDT pro-rated), withdrawal(5/15 USDT), referral(150), streaks, milestones
- Seasonal promotions: multiplier-based PromotionRule (DB-managed)
- Level system: Newbie -> Trader -> Investor -> Connector -> Trade Novice -> Amateur -> Seasoned -> Pro -> Elite

**Stable API Endpoints (DO NOT change URLs or field names):**
1. `GET /api/rewards/summary?user_id={ID}` — Public, returns lifetime_points, monthly_points, level, estimated_usdt, min_redeem_points, is_redeemable
2. `GET /api/rewards/leaderboard?user_id={ID}` — Public, returns current_rank, distance_to_next, next_user_name, suggested_message
3. `POST /api/rewards/redeem` — Protected (X-INTERNAL-API-KEY), deducts points
4. `POST /api/rewards/credit` — Protected (X-INTERNAL-API-KEY), adds points

**Event Hooks (all protected with X-INTERNAL-API-KEY):**
- `POST /api/rewards/events/trade` — Process trade, streaks, milestones
- `POST /api/rewards/events/deposit` — Process deposit points
- `POST /api/rewards/events/withdrawal` — Process withdrawal points
- `POST /api/rewards/events/signup` — Sign-up & verify (25 pts)
- `POST /api/rewards/events/referral-qualified` — Qualified referral (150 pts)
- `POST /api/rewards/events/community` — Community actions (join, daily win, help chat)

**Admin System Check:**
- `POST /api/rewards/system-check` — Admin JWT auth, runs 10-step health check
- Frontend page at `/admin/system-check` with one-click validation

**Frontend:**
- Prominent Rewards card on main dashboard (points, USDT, level, monthly rank, CTA)
- Dedicated `/my-rewards` page with full points view, level badge, rank, and history table
- "Open Rewards & Store" CTA → `https://rewards.crosscur.rent/?user_id={USER_ID}`
- "My Rewards" sidebar link for all members
- System Check admin page in sidebar

**Admin Rewards Tools (Feb 23, 2026):**
- `/admin/rewards` page with User Rewards Lookup (search by email/user_id)
- Simulate Points tool: test_trade, test_deposit, test_referral, manual_bonus
- Full points history table for looked-up user
- All simulated actions tagged as "Admin Test" in history
- "Rewards Admin" sidebar link for admins

**New API Endpoints:**
- `GET /api/rewards/history` — JWT auth, returns points transaction log (members see own, admins see any)
- `GET /api/rewards/admin/lookup` — Admin JWT, search by email/user_id, returns full profile + history
- `POST /api/rewards/admin/simulate` — Admin JWT, simulate test_trade/deposit/referral/manual_bonus

**Configuration:**
- `REWARDS_INTERNAL_API_KEY` in backend .env
- Seeded promotion rules: 1 continuous (base), 1 seasonal (March 2026 2x multiplier)

**Collections:** rewards_stats, rewards_leaderboard, rewards_promotions, rewards_redemptions, rewards_point_logs

## Mocked Features
- Cloudinary file upload, Chatbase integration

### Regression Tests (Feb 23, 2026)
- **Created:** `/app/backend/tests/test_projection_regression.py` (21 tests)
  - 10 unit tests for trading_days.py (holidays, trading day checks, quarterly growth)
  - 3 unit tests for calculations.py (lot size, projected profit, performance)
  - 8 API integration tests (year projections, daily projections, summary consistency, admin access)
- **Purpose:** Prevent recurring honorary licensee projection breakage (has broken 4+ times)
- **Status:** All 21 tests PASSING
- **One-click repair:** `POST /api/admin/licensee-health-check` — validates all licensees, auto-fixes missing start dates

### Rewards System Phase 1 & 2 Enhancements (Feb 25, 2026) - COMPLETE
**Phase 1 - Points History (MyRewardsPage):**
- Points Balance card with USDT estimate, Level card with progress bar
- Monthly Rank card with distance to next position
- Streak tracking (Current Streak, Best Streak)
- Points History table with Date, Type, Source, Points, Balance
- Time Period filters (All Time, 7 Days, 30 Days, 90 Days, Custom)
- Activity Type filters, CSV Export, Pagination
- **Test Status:** 100% passed (iteration_128)

**Phase 2 - Leaderboard (LeaderboardPage):**
- New page at `/leaderboard` with podium display for top 3
- Period toggle between Monthly and All Time
- Full rankings table with Rank, User, Level, Points, Change columns
- User rank card showing position and distance to next rank
- Sidebar link visible for all non-licensee members
- Backend endpoint: `GET /api/rewards/leaderboard/full?period=monthly|alltime&limit=N`
- **Test Status:** 100% passed (iteration_128)

**Bug Fix:** Added 'leaderboard' to sidebar `alwaysInclude` list so all members can see it (not just admins)

### Recurring Bug Mitigations (Feb 23-25, 2026)
- **ROOT CAUSE FOUND (FINAL)**: Multiple compounding issues:
  1. Case-sensitive `license_type` matching (all 20+ locations) — fixed with `_is_honorary()` helper
  2. **`get_member_details` endpoint** (used by admin simulation) had NO try/except around honorary calculation + no float() casts on MongoDB values → crashed silently, returned $0 profit
  3. MongoDB `Decimal128`/string type values not cast to `float` → arithmetic errors
  4. MongoDB regex queries case-sensitive → `$options: "i"` added
  5. **Year Projection Calculation Bug (Feb 24)**: Was calculating projections from current balance only, user expected to see License Year End values from effective start date
  6. **FRONTEND BACKEND URL MISMATCH (Feb 25)**: Production frontend was calling OLD backend URL (`finance-hub-452.emergent.host`) instead of production backend (`hub.crosscur.rent`). Fixed `REACT_APP_BACKEND_URL` to point to custom domain.
- **Fixes applied**:
  - `_is_honorary()` case-insensitive helper in `calculations.py` used in ALL locations
  - `get_member_details`: try/except around calculation with fallback, float() on ALL numeric fields
  - `get_user_financial_summary`: float() casts on all license values
  - `year-projections`: Now returns BOTH projection types (license_year_projections + projections)
  - Frontend quarterly compounding: `generateMonthlyProjection` fixed to use quarterly fixed daily profit
  - Frontend auto-retry (2x) + guard against simulation without selected member
  - Rewards card hidden for licensees
  - **One-click repair**: `POST /api/admin/licensee-health-check`
  - **Frontend BACKEND_URL**: Fixed to `https://hub.crosscur.rent`

### Admin Diagnostic & Sync Tool (Feb 25, 2026) - UPDATED
**Location:** Platform Settings → Diagnostics tab (Master Admin only)
**Purpose:** Comprehensive safeguard tool for master admin to diagnose and fix licensee calculation issues

**Features:**
1. **Sync Status Banner** - Shows last sync date and next recommended sync (every 7 days)
2. **Batch Sync All** - Recalculates ALL honorary licensees in one click
3. **Health Check** - Quick scan to identify licensees with calculation issues
4. **Individual Diagnostic** - Enter email to see step-by-step diagnostic for a specific licensee
5. **Force Sync** - Manually recalculate and update a single licensee's value

**Endpoints:**
- `GET /api/diagnostic/licensee/{email}` - Public diagnostic (no auth needed)
- `POST /api/admin/licensee/{user_id}/force-sync` - Force recalculation for one user
- `POST /api/admin/licensee/batch-sync-all` - Batch sync all licensees
- `POST /api/admin/licensee-health-check` - Run health check on all licensees

**Scheduling:**
- System tracks last sync date in localStorage
- Recommends sync every 7 days
- Shows warning banner when sync is overdue (red) or never done (amber)

### Year Projection Dual View (Feb 24, 2026)
**Bug Report:** Year 1 showed $44,943 instead of expected ~$12,414 
**Root Cause:** Projections only calculated from current balance, not from starting amount at effective start date
**Fix (Option C):** Show BOTH types of projections
- **Backend**: `/api/profit/licensee/year-projections` now returns:
  - `projections` array: Forward from TODAY's current_value
  - `license_year_projections` array: From effective_start_date using starting_amount
- **Frontend Dashboard**: Two rows in Growth Projections card
  - Cyan: License Year End (from start date)
  - Blue: Forward Projections (from today's balance)
- **Test file**: `/app/backend/tests/test_iteration_127_projection_fix.py`

## Prioritized Backlog

### P1 - Upcoming (Rewards Phases 3 & 4)
- **Phase 3: Gamification & Engagement** - Badge/achievement system (login streaks, points milestones), notifications for new rewards
- **Phase 4: Admin Tools Enhancement** - Overhaul `/admin/rewards` with filtering, manual point adjustment with audit trail, comprehensive transaction history

### P2 - Improvements
- Backend refactoring: Extract remaining routers from server.py
- Frontend refactoring: AdminSettingsPage.jsx, ProfitTrackerPage.jsx
- Email integration for password reset tokens
- Admin UI for PromotionRule management

### P3 - Future
- Cloudinary integration, Chatbase integration
- Rewards store UI (handled by rewards.crosscur.rent)

## Test Credentials
- Master Admin: iam@ryansalvador.com / admin123
- Licensee (Honorary FA): rizza.miles@gmail.com / rizza123
- Internal API Key: _CXCB2Y-ObBIZqqaCzmjEJU1zwe7DMHr8C-tzoef9h0

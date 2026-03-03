# CrossCurrent Hub - Changelog

## Mar 3, 2026

### Streak Freeze Feature
- Added streak freeze purchase system: Trade Streak Freeze (200 pts) and Habit Streak Freeze (150 pts)
- Backend: `GET /api/rewards/streak-freezes`, `POST /api/rewards/streak-freezes/purchase`
- Frontend: StreakFreezeSection on My Rewards page with quantity selector and buy buttons
- Trade streak and habit streak calculations updated to check for active freezes
- Created `/app/prompts_for_rewards_platform_streak_freeze.md` for Rewards Platform integration

## Feb 18, 2026 (Session 2)

### Simulation Dialog/Banner Stale Value Fix
- **Root Cause:** `GET /api/admin/licenses` returned raw `license.current_amount` from DB (stale) for honorary licensees
- **Fix:** Added `calculate_honorary_licensee_value()` call for honorary/honorary_fa in the licenses endpoint
- **Result:** Simulation dialog now shows $6,530 (dynamic) instead of $798.57 (stale)
- Sidebar.jsx simulation data now picks up correct values from backend

### Licensee Dashboard Redesign
- Replaced "Trade Performance" chart with **Year-by-Year Growth Projections** (1yr, 2yr, 3yr, 5yr)
- Replaced "Recent Trades" with **Family Account Members** stats table
- Added `GET /api/profit/licensee/year-projections` backend endpoint
- Projections use same quarterly compounding: LOT = Balance/980, Daily = LOT×15, recalculated each quarter
- Family members table shows name, relationship, starting amount, current value, profit, status

### Admin Add Family Member on Behalf
- Added Users icon button on honorary_fa license rows in Admin Licenses page
- Opens dialog for admin to enter member name, relationship, starting amount
- Uses existing `POST /api/admin/family/members/{userId}` backend endpoint

## Feb 18, 2026 (Session 1)

### P0 Fix: Profit Tracker Data Consistency for Direct Licensee Login
- Fixed `/api/profit/licensee/welcome-info` to use `calculate_honorary_licensee_value()`
- All 4 key endpoints return identical dynamically calculated values
- Backend test: 10/10 passed (iteration_114)

### Admin Temp Password with Forced Reset on First Login
- Modified login endpoint to return `must_change_password` flag
- Added `POST /api/auth/force-change-password` endpoint
- Frontend: force change password dialog before dashboard redirect

## Feb 17, 2026
### Family Account Feature (End-to-End)
- Created `honorary_fa` license type with family member CRUD
- Built all APIs for admin conversion, member management, withdrawal approvals

### Admin Reset Functionality
- Reset starting balance, trade start date, and family member reset endpoints

### Profit Tracker Logic Refactor (Partial)
- Dynamic `calculate_honorary_licensee_value()` with quarterly compounding

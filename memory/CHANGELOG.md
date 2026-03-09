# CrossCurrent Hub - Changelog

### Critical Fix: Commission as Display-Only (Balance Decoupled)
- **Root cause:** Commissions were factored into the balance calculation at 3 points in `profitCalculations.js`:
  1. Starting balance subtracted commissions → artificially lowered all "Balance Before" values
  2. Today's effective balance subtracted commission
  3. Running balance added commission to next day's calculation
- **User's use case:** People enter a lump-sum total commission (not daily values). Including this in balance math distorted all projections.
- **Fix:** Removed commission from all 3 balance calculation points. Commission is now purely display-only in the projection table:
  - Shows in the Commission column per day
  - Shows in the Total Commission summary card
  - Does NOT affect Balance Before, Lot Size, Target Profit, or P/L Diff
  - New commissions still create deposits (affecting account value through the deposit pathway)
  - "Historical correction only" checkbox available for backfilling past commissions without creating deposits
- **Files modified:** `frontend/src/utils/profitCalculations.js`, `frontend/src/pages/ProfitTrackerPage.jsx`
- **Test report:** `/app/test_reports/iteration_150.json` (7/7 backend, 7/7 frontend passed)

### Feature: Commission Backfill (skip_deposit)
- Added `skip_deposit: bool = False` field to `CommissionCreate` model
- When `true`, commission is recorded but NO deposit is created (account balance unaffected)
- Frontend "Adjust Commission" dialog now has a "Display only (don't add to balance)" checkbox
- **Use case:** Backfilling historical commissions that were lost due to the save bug, without double-counting in account value
- **Files modified:** `backend/routes/profit_routes.py`, `frontend/src/pages/ProfitTrackerPage.jsx`

### Bug Fix: Failed to Log Trade (P0)
- **Root cause:** `TradeLogCreate` Pydantic model was missing the `commission` field. The `log_trade` route accessed `data.commission` at lines 60 and 88, causing `AttributeError` in Pydantic v2.
- **Fix:** Added `commission: float = 0` to `TradeLogCreate` and `TradeLogResponse` models.
- **Files modified:** `backend/models/trade.py`

### Bug Fix: Failed to Create Signal (P0)
- **Root cause:** A duplicate `TradingSignalCreate` class at line 132 in `admin_routes.py` shadowed the proper model from `models/trade.py`. The duplicate was missing `profit_points`, `is_official`, `send_email`, and `profit_multiplier` fields, causing `AttributeError` on signal creation.
- **Fix:** 
  1. Removed the duplicate class from `admin_routes.py`
  2. Added `TradingSignalCreate` to the import from `models/trade.py`
  3. Added `is_official`, `send_email`, `trade_date`, `profit_multiplier` fields to `TradingSignalCreate` model
  4. Added `is_official` to `TradingSignalResponse` model
  5. Fixed push notification body to fall back to `profit_points` when `profit_multiplier` is None
- **Files modified:** `backend/routes/admin_routes.py`, `backend/models/trade.py`

### Critical Fix: Commission Balance Formula
- **Formula:** Next Trade Day Balance Before = Last Trade Day Balance Before + Actual Profit + Commission
- **Implementation:** Two commission fields in tradeLogs:
  - `commission`: All commissions (for display in Commission column)
  - `balance_commission`: Only real commissions (skip_deposit=false, for balance calculations)
- Balance calculations in `profitCalculations.js` use `balance_commission`:
  - Starting balance subtracts balance_commission
  - Today's effective balance subtracts balance_commission
  - Running balance adds balance_commission for next day
- Commission deposits (`is_commission: true`) filtered from `transactionsByDate` to prevent double-counting
- Historical corrections (`skip_deposit: true`) only show in display, don't affect balance
- `skip_deposit` flag saved on commission record in DB for correct historical tracking
- **Files modified:** `frontend/src/utils/profitCalculations.js`, `frontend/src/pages/ProfitTrackerPage.jsx`, `backend/routes/profit_routes.py`
- **Test report:** `/app/test_reports/iteration_151.json` (9/9 backend, 7/7 frontend passed)

### Bug Fix: Publitio Image Upload (P1)
- **Root cause:** `get_publitio_creds()` in `publitio.py` was reading from `db.settings` (non-existent collection with `_id: "global"`) instead of `db.platform_settings` (the actual settings collection). Credentials could never be found.
- **Fix:** Changed to read from `db.platform_settings.find_one({})`
- **Note:** User's Publitio API keys are currently empty in the database. User needs to re-enter them in Platform Settings → API Keys.
- **Files modified:** `backend/routes/publitio.py`

## 2026-03-07 - Commission Save Bug + Batch Sync Fix + Platform Settings Black Screen Fix

### Bug Fix: Commission Save Endpoint (P0 - CRITICAL)
- **Root cause:** `CommissionCreate` Pydantic model was missing `traders_count` and `commission_date` fields. When the frontend posted commission data with these fields, Pydantic rejected them causing a 500 Internal Server Error. No commissions could be saved.
- **Fix:** Added `traders_count: int = 1` and `commission_date: Optional[str] = None` to the `CommissionCreate` model in `profit_routes.py`
- **Files modified:** `backend/routes/profit_routes.py`

### Bug Fix: Batch Sync to Rewards Platform (P1)
- **Root cause:** `DiagnosticsTab.jsx` called `rewardsAPI.batchSync()` which did NOT exist in the API module. The correct method is `rewardsAPI.adminSyncAllUsers()`.
- **Fix:** Changed the call to use the correct API method with proper response handling.
- **Files modified:** `frontend/src/pages/admin/settings/DiagnosticsTab.jsx`

### Feature: Auto Batch Sync Every 4 Hours
- Added APScheduler `IntervalTrigger(hours=4)` job in `server.py` startup that calls `batch_sync_all_users()` automatically
- **Files modified:** `backend/server.py`

### Bug Fix: Platform Settings Black Screen (P0)
- **Root cause:** `AdminSettingsPage.jsx` had a dead `useEffect` (lines 354-364) that called `setLastSyncDate()` and `setNextSyncRecommended()` — but these state setters were NEVER declared. When `localStorage.getItem('lastLicenseeSyncDate')` returned a value (after any batch sync), calling these undefined functions threw a ReferenceError, crashing the component → black screen. First load after cache purge worked because localStorage was cleared.
- **Fix:** Removed the dead useEffect. The `DiagnosticsTab.jsx` already has its own properly declared state for sync dates.
- **Files modified:** `frontend/src/pages/admin/AdminSettingsPage.jsx`
- **Test report:** `/app/test_reports/iteration_148.json` (6/6 backend, 7/7 frontend passed)

## 2026-03-07 - Commission Display Fix + Cache Purge Button

### Bug Fix: Commissions Missing from Daily Projection Table
- **Root cause:** Three-part issue:
  1. Standalone commissions on weekends/holidays were not being shifted to the nearest trading day during merge, causing them to be lost in the daily projection (which only shows trading days)
  2. Total Commission summary card in daily projection only counted `completed` status days, excluding commissions on `missed` days
  3. Commission column for `missed` status days showed "Add" instead of the actual commission value
- **Fix:**
  1. Added holiday-aware date shifting during commission merge in `loadData()` — weekends and global holidays shift to previous trading day
  2. Loaded global holidays within `loadData()` Promise.all to make them available during merge
  3. Removed `.filter(day => day.status === 'completed')` from Total Commission summary card
  4. Updated commission column for missed-status days to show actual value with cyan styling when commission exists
- **Result:** Daily projection Total Commission ($917.48 for Jan 2026) now matches monthly table exactly. Commission values like +$904.48 on Fri Jan 16 correctly aggregate shifted weekend/holiday commissions.
- **Files modified:** `ProfitTrackerPage.jsx` (commission merge logic), `DailyProjectionDialog.jsx` (summary card + column rendering)
- **Test report:** `/app/test_reports/iteration_147.json` (7/7 features passed)

### Feature: Clear Cache & Reload Button
- Added "Clear Cache & Reload" button (amber colored) to user profile dropdown in sidebar
- Functionality: Unregisters service workers, clears browser caches, clears localStorage/sessionStorage (preserves auth token), then force reloads
- Available in both expanded and collapsed sidebar views
- **File modified:** `Sidebar.jsx`

## 2026-03-07 - Bug Fixes + Transaction Correction Guide + ProfitTrackerPage Refactoring

### Bug Fix: Signal Deactivation (500 Error)
- **Root cause:** `TradingSignalUpdate` model in `models/trade.py` was missing the `is_official` field, causing `AttributeError` when the backend tried to access it during signal updates
- **Fix:** Added `is_official: Optional[bool] = None` to the `TradingSignalUpdate` Pydantic model
- Signal deactivation/reactivation now works correctly

### Bug Fix: Exit Trade Button Not Appearing
- **Root cause:** `getTradeWindowInfo()` in `TradeMonitorPage.jsx` had a 30-minute post-trade window. If the user visited the page more than 30 minutes after trade time, the Exit Trade button wouldn't show
- **Fix:** Extended the post-trade window from 30 minutes to 8 hours, ensuring the Exit Trade button is accessible for the full trading session

### Bug Fix: Missing resetNewBalance State (Found by Testing Agent)
- **Root cause:** During AdminActionsPanel extraction, the `resetNewBalance` state variable was referenced as a prop but never defined in ProfitTrackerPage
- **Fix:** Added `const [resetNewBalance, setResetNewBalance] = useState('')` to ProfitTrackerPage

### Bug Fix: Commissions Missing from Monthly Profit Table
- **Root cause:** Standalone commissions (from "Adjust Commission") were stored in a separate `commissions` collection but never merged into `tradeLogs`. The monthly table also had no Commission column.
- **Fix:**
  1. Added commission merge logic in `loadData()` — standalone commissions are now merged into `tradeLogs` by date
  2. Added `totalCommission` calculation in `generateMonthlyProjection()`
  3. Added Commission column to Monthly Table view, showing per-month commission totals

### Documentation: Transaction Correction Guide with Screenshots
- Created `/app/memory/transaction_correction_guide.md` with step-by-step instructions for both members and admins
- 3 screenshots saved to `/app/frontend/public/guide-images/` (member transactions, admin transactions, admin correction dialog)

### In-App Help Overlays
- Added help icon (?) next to "My Recent Transactions" title — shows 3-step editing walkthrough + rules (48h window, last 2 editable, one edit per tx)
- Added help icon (?) next to "Transaction History" title on Admin Transactions page — shows 3-step correction process + audit trail note

### ProfitTrackerPage.jsx Refactoring (P1)
- Extracted `StatsCards` component → `/app/frontend/src/components/profit/StatsCards.jsx` (~170 lines)
- Extracted `AdminActionsPanel` component → `/app/frontend/src/components/profit/AdminActionsPanel.jsx` (~120 lines)
- File reduced from 4,451 → 4,184 lines (~6% reduction, 267 lines extracted)
- Test report: `/app/test_reports/iteration_146.json` (100% pass rate)

## 2026-03-06 - Comprehensive Pytest Suite Complete

### Backend Pytest Suite (P0 - Launch Readiness)
- **135 total tests**, all passing across 9 test files
- Test files created:
  - `test_auth_suite.py` (10 tests) — login, /me, verify-password, forgot-password, auth edge cases
  - `test_profit_suite.py` (19 tests) — summary, deposits, withdrawals, commissions, daily-balances, VSD, sync-validation, onboarding, balance-override
  - `test_trade_suite.py` (12 tests) — logs, history, streak, signals, daily-summary, missed-trade, holidays, products
  - `test_admin_suite.py` (24 tests) — members CRUD, transactions, signals, analytics (6 endpoints), licenses, notifications
  - `test_general_suite.py` (9 tests) — health, version, notifications, WS status, system-health, db-ping
  - `test_forum_suite.py` (6 tests) — posts CRUD, comments, pagination
  - `test_rewards_suite.py` (11 tests) — summary, leaderboard, badges, earning-actions, history, admin endpoints
  - `test_misc_suite.py` (17 tests) — settings, currency, debt, goals, habits, users, family, activity-feed, affiliate
  - `test_refactored_routes.py` (27 tests) — existing regression suite
- Shared `conftest.py` with session-scoped fixtures for auth token and admin user
- Test report: `/app/test_reports/iteration_145.json`

### Bug Fix
- Fixed `POST /api/auth/verify-password` returning 500 — missing `bcrypt` import in `auth_routes.py`, now uses `deps.verify_password()`

## 2026-03-06 - Major Refactoring Release

### Backend Refactoring
- **server.py**: Reduced from 10,302 lines to 352 lines (97% reduction)
- Extracted routes into 5 modular files:
  - `routes/auth_routes.py` (705 lines) - Authentication endpoints
  - `routes/profit_routes.py` (2,241 lines) - Profit/financial endpoints
  - `routes/trade_routes.py` (1,246 lines) - Trade monitoring endpoints
  - `routes/admin_routes.py` (4,510 lines) - Admin management endpoints
  - `routes/general_routes.py` (472 lines) - General API endpoints
- Updated `helpers.py` with all shared functions (notifications, calculations, scheduler tasks)
- Updated `routes/__init__.py` with new module registry
- Removed old route stubs (auth.py, profit.py, trade.py, admin.py)
- All 27 backend endpoints verified working (100% pass rate)

### Frontend Refactoring
- **ProfitTrackerPage.jsx**: Reduced from 5,452 lines to 4,450 lines (18% reduction)
- Extracted pure utility functions to `utils/profitCalculations.js` (612 lines)
  - Formatting: truncateTo2Decimals, formatFullCurrency, formatLargeNumber, formatCompact, maskAmount
  - Trading: isTradingDay, isHoliday, addBusinessDays
  - Projections: generateProjectionData, generateDailyProjectionForMonth, generateMonthlyProjection, groupMonthsByYear
- Extracted `components/profit/DailyProjectionDialog.jsx` (416 lines)
  - Monthly projection table with trade status, P/L diff, commission tracking
  - Manager traded toggle for licensees
  - Holiday handling

### Testing
- Full regression test passed (27/27 backend, all frontend pages verified)
- Test report: `/app/test_reports/iteration_144.json`

## 2026-03-05 - Feature Batch Release

### Completed Features
- Fixed critical balance calculation bug (double-counting in server.py)
- Forum enhancements (CRUD, categories, pinning, @mentions)
- Admin transaction correction/deletion UI
- Member self-edit widget for recent transactions (48-hour window, last 2 transactions)
- Trade history streak calculation fix (non-trading days)
- Balance Audit Trail modal
- Real-time notification enhancements (forum replies, mentions)
- Admin Transactions page: Profits filter, user search
- Documentation: instructionals_admin.md, instructionals_members.md

# CrossCurrent Hub - Changelog

## 2026-03-07 - Bug Fixes + Transaction Correction Guide

### Bug Fix: Signal Deactivation (500 Error)
- **Root cause:** `TradingSignalUpdate` model in `models/trade.py` was missing the `is_official` field, causing `AttributeError` when the backend tried to access it during signal updates
- **Fix:** Added `is_official: Optional[bool] = None` to the `TradingSignalUpdate` Pydantic model
- Signal deactivation/reactivation now works correctly

### Bug Fix: Exit Trade Button Not Appearing
- **Root cause:** `getTradeWindowInfo()` in `TradeMonitorPage.jsx` had a 30-minute post-trade window. If the user visited the page more than 30 minutes after trade time, the Exit Trade button wouldn't show
- **Fix:** Extended the post-trade window from 30 minutes to 8 hours, ensuring the Exit Trade button is accessible for the full trading session

### Documentation: Transaction Correction Guide
- Created `/app/memory/transaction_correction_guide.md` with step-by-step instructions for both members and admins

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

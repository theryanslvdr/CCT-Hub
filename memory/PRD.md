# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification
- **Integrations**: Cloudinary, Emailit, ExchangeRate-API, APScheduler, CoinGecko (USDT rates)

## Completed Work

### Session 54 (2026-01-19) - Commission Tracking System ✅

#### Commission Tracking Feature Implementation ✅
- **Commission Column in Daily Projection**: Added "Commission" column to the Daily Projection table in ProfitTrackerPage
- **Commission Input in Trade Monitor**: Added commission input field when entering actual profit after a trade
- **Commission Input in Onboarding Wizard**: Added total commission input at the final step (Step 5) for experienced traders
- **Balance Formula Updated**: `Next Day's Balance = Today's Balance + Today's Profit + Today's Commission`

#### Backend Changes ✅
- **Models Updated**: `TradeLogCreate`, `TradeLogUpdate`, `OnboardingTradeEntry`, `OnboardingData` include `commission` field
- **API Endpoints Updated**:
  - `POST /api/trade/log` - Accepts and stores `commission` field (defaults to 0)
  - `POST /api/trade/log-missed-trade` - Accepts `commission` field
  - `POST /api/profit/complete-onboarding` - Accepts `total_commission` field
  - `GET /api/trade/history` - Returns `commission` field with default 0 for backward compatibility
- **Calculations Updated** (`utils/calculations.py`):
  - `calculate_account_value()` includes commission in balance calculation
  - `get_user_financial_summary()` returns `total_commission` field

#### Frontend Changes ✅
- **TradeMonitorPage.jsx**:
  - Added `commissionValue` state
  - Added commission input field in actual profit dialog
  - Updated `submitActualProfit` to send commission to backend
- **OnboardingWizard.jsx**:
  - Added `totalCommission` state
  - Added commission input card at final step (Step 5)
  - Updated `handleSubmit` to include `total_commission` in API call
  - Updated `handleRestart` to clear commission state
- **ProfitTrackerPage.jsx**:
  - Updated `generateDailyProjectionForMonth` to extract commission from trade logs
  - Updated balance calculation: `runningBalance += actualProfit + commission`
  - Added Commission column to table header and body

#### P1: Data Consistency Verification ✅
- Verified Reset Tracker correctly deletes deposits and trade_logs
- Verified Complete Onboarding creates trade_logs with correct formulas:
  - `lot_size = balance / 980`
  - `projected_profit = lot_size * 15`
- Verified Daily Projection uses stored trade_log values for completed trades
- Fixed `/api/trade/history` endpoint to return commission field with default 0

#### P1: Frontend Refactoring (Started) ✅
- Created `/app/frontend/src/components/onboarding/` directory with extracted components:
  - `StepUserType.jsx` - Step 1: User type selection (new/experienced)
  - `StepNewTraderBalance.jsx` - Step 2: Starting balance for new traders
  - `StepExperiencedStart.jsx` - Step 2: Start date and balance for experienced traders
  - `index.js` - Export file with shared helper functions
- Created `/app/frontend/src/lib/profitTrackerUtils.js` with shared calculation functions:
  - `truncateTo2Decimals`, `formatLargeNumber`, `formatMoney`
  - `calculateLotSize`, `calculateProjectedProfit`, `calculateExitValue`
  - `isTradingDay`, `isHoliday`, `addBusinessDays`
  - `generateDailyProjectionForMonth` - Core projection calculation

#### Testing ✅
- **Iteration 53**: 15/15 backend tests passed (commission tracking)
- **Iteration 54**: 18/20 backend tests passed (data consistency - 2 minor issues fixed)

### Session 53 (2026-01-17) - Onboarding Wizard, Streaks, Daily Projection Fixes

#### Onboarding Wizard Enhancements ✅
- **Balance as Source of Truth**: Users now enter account balance per day instead of LOT
- **LOT Size is Derived**: Balance ÷ 980 = LOT (read-only display)
- **Commission Removed**: Daily commission calculation removed; commission is totaled at end
- **Disclaimer Added**: "The goal is to catch up to your current account value with granular daily trade estimates. Commissions are totaled at the end."
- **Compact Design**: Reduced padding, cleaner layout
- **Data Sync**: Onboarding now sends `balance`, `product`, `direction` per trade entry

#### Streak Calculation Fix ✅
- **Before**: Used hardcoded HOLIDAYS list
- **After**: Uses global holidays from database (`global_holidays` collection)
- **Holidays Don't Break Streak**: Holidays are treated like weekends - skipped in streak calculation
- **Backend**: `/api/trade/streak` now fetches global holidays dynamically

#### Daily Projection Table Improvements ✅
- **December Data for Existing Users**: Now shows past months (Year History) if user has trade data
- **Global Holidays Integration**: `isTradingDay()` now uses dynamic holidays from backend
- **Remaining Days Count Fixed**: Only counts days WITHOUT actual profit recorded

#### Known Issue (Partial Fix)
- **Trade History vs Daily Projection Mismatch**: Historical trades imported via onboarding may have different LOT/projected values than Daily Projection recalculation. This is because:
  - Daily Projection recalculates LOT based on running balance + deposits/withdrawals
  - Trade History shows stored values from when trade was logged
  - For NEW trades, the backend recalculates LOT from authoritative account_value
  - For HISTORICAL/ONBOARDING trades, values depend on what was entered during onboarding

### Session 52 (2026-01-17) - Admin Settings Redesign & Global Trading Settings ✅

#### Major Refactoring: Admin Settings Page ✅
- **Before**: Tab-based layout
- **After**: Sidebar navigation layout for improved organization
- **Sidebar Tabs**: SEO & Meta, Branding, UI Settings, API Keys, Links, Emails, Maintenance
- **Files Modified**: `/app/frontend/src/pages/admin/AdminSettingsPage.jsx`
- **Testing**: 13/13 backend tests passed, all frontend verified

#### Feature: Global Trading Settings (Master Admin Only) ✅
- **Location**: Admin Settings > Global Trading (sidebar)
- **Access**: Master Admin ONLY (role-based visibility)
- **Components**:
  1. **Trading Products Management**:
     - Add/remove/toggle products
     - Default products: MOIL10, XAUUSD, EURUSD, GBPUSD, USDJPY
     - Endpoints: `POST/PUT/DELETE /api/admin/trading-products`
  2. **Global Holidays Management**:
     - Calendar picker with tree icons for holidays
     - Scheduled holidays list with delete buttons
     - Existing endpoints: `POST/DELETE /api/admin/global-holidays`

#### OnboardingWizard Integration ✅
- **Products**: Fetches from `/api/trade/trading-products` (user endpoint)
- **Holidays**: Fetches from `/api/trade/global-holidays` (user endpoint)
- **Behavior**: Combines backend global holidays with static holidays to exclude from trading days

#### New API Endpoints ✅
- `GET /api/admin/trading-products` - List products (admin)
- `POST /api/admin/trading-products?name=PRODUCT` - Add product
- `PUT /api/admin/trading-products/{id}?is_active=bool` - Toggle product
- `DELETE /api/admin/trading-products/{id}` - Remove product
- `GET /api/trade/trading-products` - List active products (all users)

### Session 51 (2026-01-17) - Data Integrity Fixes + New Features ✅

#### P0 Bug Fix: Incorrect Lot Size Logged in Trade History ✅
- **Issue**: Dashboard showed correct lot_size (19.32), but Trade History logged incorrect value (20.67)
- **Root Cause**: Frontend (`TradeMonitorPage.jsx`) was sending a `lot_size` calculated from a stale `profitSummary.account_value` to the backend
- **Fix**: 
  1. Backend `POST /api/trade/log` now IGNORES frontend's `lot_size` parameter
  2. Backend recalculates `lot_size` from authoritative `account_value` using `calculate_lot_size()` function
  3. Frontend no longer sends `lot_size` for regular trades (BVE mode still sends it for simulation)
- **Formula**: `lot_size = account_value / 980`
- **Testing**: All backend tests passed - verified server ignores wrong/stale lot_size values

#### P1 Bug Fix: Daily Projection "Balance Before" Synchronization ✅
- **Issue**: Daily Projection table's "Balance Before" for current day didn't match live dashboard `account_value`
- **Fix**: `generateDailyProjectionForMonth` now uses live account_value for today's row

#### Feature: Undo Trade Button ✅
- **Location**: ONLY in Onboarding Wizard (Step 5 - Enter Trade Profits)
- **Purpose**: Undo accidental "I Missed This Trade" clicks during onboarding
- **UI**: Red "Undo" button replaces "I Missed This Trade" when day is marked as missed
- **Behavior**: Clears the missed entry, allowing user to re-enter
- **Testing**: All tests passed

#### Feature: Product and Direction Selection in Onboarding ✅
- **Location**: Onboarding Wizard Step 5 (Enter Trade Profits)
- **Products**: MOIL10, XAUUSD, EURUSD, GBPUSD, USDJPY
- **Directions**: BUY, SELL
- **UI**: Two dropdown selects for each trade entry

#### Feature: Global Holidays (Admin Settings) ✅
- **Location**: Admin Settings > Holidays tab
- **Access**: Super Admin AND Master Admin can manage
- **UI**: 
  - Calendar date picker - click to toggle holiday status
  - Selected dates show **tree icon** (🌲) instead of number
  - Scheduled holidays list with delete buttons
- **Endpoints**: 
  - `GET /api/admin/global-holidays` - List all global holidays (admin)
  - `POST /api/admin/global-holidays?date=YYYY-MM-DD&reason=...` - Add
  - `DELETE /api/admin/global-holidays/{date}` - Remove
  - `GET /api/trade/global-holidays` - List for all users (read-only)
- **Collection**: `global_holidays`

#### Daily Projection Holiday Display ✅
- Global holidays show as special **"HOLIDAY"** row:
  - Date column shows tree icon (🌲) + date
  - All other columns merge into centered "🌲 HOLIDAY 🌲"
  - Row has emerald/green highlight

#### NOTE: Personal Holidays REMOVED from Onboarding
- Tree icon / holiday button is NO LONGER in Onboarding Wizard
- Holidays are now managed globally by admins only from Settings

#### Feature: Official Trading Signal Toggle ✅
- **Backend**: Added `is_official` field to `TradingSignalCreate`, `TradingSignalUpdate`, `TradingSignalResponse` models
- **Endpoints**: `POST /api/admin/signals` and `PUT /api/admin/signals/{id}` accept `is_official` parameter
- **UI**: "Official Trading Signal" toggle in create/edit signal dialogs
- **Badge**: "OFFICIAL" badge shown on active signal when `is_official=true`

### Session 50 (2026-01-16) - Lot Size Calculation Synchronization Fix ✅

#### Bug Fix: Account Value & LOT Size Calculation ✅
- **Issue**: Discrepancy between Trade History (20.67), Daily Projection (19.12), and Dashboard (19.32) LOT sizes
- **Root Cause**:
  1. `calculate_account_value` was using separate deposit/withdrawal logic, but withdrawals already have NEGATIVE amounts in DB
  2. `DepositResponse` model was missing `is_withdrawal` and `type` fields
  3. `/profit/withdrawals` endpoint wasn't returning records with negative amounts (only `is_withdrawal: True`)
- **Fix**:
  1. Simplified `calculate_account_value`: `net_deposits = sum(all_deposit_amounts) + total_profit` (negative amounts ARE withdrawals)
  2. Added `is_withdrawal` and `type` fields to `DepositResponse` model
  3. Updated `/profit/withdrawals` to use `$or: [is_withdrawal: True, amount: {$lt: 0}]`
- **Files Modified**: 
  - `utils/calculations.py` (calculate_account_value, get_user_financial_summary)
  - `server.py` (DepositResponse model, withdrawals endpoint)

#### Clarification: Expected LOT Size Differences ✅
After fixing, the system now correctly shows:
- **Dashboard LOT (19.32)**: Based on CURRENT account value ($18,941.87)
- **Daily Projection LOT (19.12)**: Based on "Balance Before" each day's trade ($18,738.19)
- **Trade History LOT (stored values)**: Historical values from when trades were logged

**This is EXPECTED BEHAVIOR** - different views show different points in time:
- Dashboard = NOW
- Daily Projection = START of each trading day
- Trade History = WHEN the trade was made

### Session 49 (2026-01-16) - Lot Size & Streak Calculation Fixes ✅

#### Bug Fix 1: Daily Projection Wrong Lot Sizes ✅
- **Issue**: Trade History and Daily Projection Table displayed wrong Lot Sizes, causing incorrect P/L Diff and Performance Data
- **Root Cause**: 
  1. Daily Projection was using stored lot_size from trade logs instead of recalculating based on running balance
  2. Starting balance calculation didn't account for deposits/withdrawals
  3. Withdrawal amounts were being double-negated (withdrawals already have negative amounts in DB)
- **Fix**:
  1. Refactored `generateDailyProjectionForMonth()` to ALWAYS recalculate lot size: `truncateTo2Decimals(runningBalance / 980)`
  2. Added proper transaction tracking by date with deposits/withdrawals
  3. Fixed withdrawal handling - just add the amount directly (already negative)
  4. Calculate starting balance by subtracting month's profit AND transactions from current balance
- **Files Modified**: `ProfitTrackerPage.jsx` (lines 98-220)

#### Bug Fix 2: Streak Counting Holidays ✅
- **Issue**: Streaks counted holidays as trading days (should skip them)
- **Fix**: Added HOLIDAYS set in backend with:
  - Christmas (Dec 25)
  - Boxing Day (Dec 26)
  - New Year's Eve (Dec 31)
  - New Year's Day (Jan 1)
  - Jan 2 (New Year Holiday)
- **Files Modified**: 
  - `server.py` (lines 1338-1427: HOLIDAYS set, is_trading_day(), get_previous_trading_day())
  - `ProfitTrackerPage.jsx` (lines 77-111: isHoliday function)
  - `OnboardingWizard.jsx` (lines 26-48: HOLIDAYS Set for trading days)

### Session 48 (2026-01-16) - Notification Engine & Reset Flow Fix ✅

#### Bug Fix 1: Notification Engine "Connection Lost" ✅
- **Issue**: WebSocket showed "Connection lost" and reconnect didn't work, no past notifications
- **Root Cause**: 
  1. Token wasn't exposed in AuthContext value
  2. WebSocket path `/ws/` wasn't routed through ingress (only `/api/` is routed)
  3. Notifications weren't persisted to database
- **Fix**:
  1. Added `token` to AuthContext value export
  2. Added `/api/ws/{user_id}` WebSocket endpoint for ingress routing
  3. Added notification persistence to MongoDB via `set_database()` in websocket_service
  4. Added CRUD endpoints: `GET /api/notifications`, `POST /api/notifications/mark-read`, `DELETE /api/notifications`
  5. Updated WebSocketContext to fetch past notifications on connect
- **Files Modified**: 
  - `server.py` (lines 5380-5460: notification endpoints, 5338-5408: dual WebSocket endpoints)
  - `services/websocket_service.py` (notification persistence with set_database)
  - `contexts/WebSocketContext.jsx` (API calls, /api/ws/ path)
  - `contexts/AuthContext.jsx` (token in value)

#### Feature: Reset Tracker → Onboarding Wizard Flow ✅
- **Change**: Simplified reset dialog to skip "new balance" step
- **New Flow**: Warning → Password Verification → Onboarding Wizard opens
- **Files Modified**: `ProfitTrackerPage.jsx` (handleResetConfirm, handleResetWithPassword)

#### Feature: Onboarding Wizard Text Update ✅
- **Change**: Renamed "I'm New to Merin" to "New Trader / Start Fresh"
- **Dynamic Description**: Shows "Start over with a clean slate" during reset flow
- **Files Modified**: `OnboardingWizard.jsx` (line 387)

### Session 47 (2026-01-15) - Timer Fix, Streak Fix & Onboarding Wizard ✅

#### Bug Fix 1: Timer Stalling at 8 Seconds ✅
- **Issue**: 30-second countdown stalled around 8 seconds. Clicking "Refresh" showed "no active countdown to restart"
- **Root Cause**: Countdown interval used a closure variable `targetTimeMs` that became stale when browser throttled the interval
- **Fix**: Refactored countdown to read target time from localStorage on EVERY tick:
  - `updateCountdown()` now reads from `localStorage.getItem('trade_check_in')` each tick
  - Uses 500ms interval for more frequent updates
  - `restartCountdown()` can now recreate check-in data from signal if localStorage is missing
- **Files Modified**: `TradeMonitorPage.jsx` (lines 663-738, 755-845)

#### Bug Fix 2: Streak Calculation - Count Trading Days, Not Profits ✅
- **Issue**: Streak was counting consecutive trades with positive profit. User wants ANY consecutive trading days
- **Fix**: Refactored `/api/trade/streak` to count consecutive trading days regardless of profit/loss:
  - Uses date comparison to check for consecutive days
  - Skips weekends (Saturday=5, Sunday=6)
  - Returns `streak_type: "trading"` instead of `"winning"`
- **Files Modified**: `server.py` (lines 1338-1399)

#### Feature 1: Comprehensive Onboarding Wizard ✅
- **Created**: `/app/frontend/src/components/OnboardingWizard.jsx`
- **Triggers**: Opens for new users (no deposits) or after reset
- **Flow for New Traders (2 steps)**:
  1. Select "I'm New to Merin"
  2. Enter starting balance → Complete
- **Flow for Experienced Traders (5 steps)**:
  1. Select "I'm Experienced"
  2. Select start date (min: December 1, 2025, weekdays only)
  3. Enter starting balance
  4. Add deposits/withdrawals (accepts deposits from Nov 24, 2025)
  5. Enter actual profits for each trading day (with "I Missed This Trade" option)
- **Features**:
  - Save & Continue Later (progress saved to localStorage)
  - Remembers user type (new/experienced) after reset
  - Shows running balance, lot size, and projected profit for each trade day
  - Creates deposits and trade logs in backend on completion
- **Backend Endpoints Added**:
  - `POST /api/profit/complete-onboarding` - Processes onboarding data
  - `GET /api/profit/onboarding-status` - Returns onboarding completion status
- **Files Modified**: `server.py` (lines 4633-4808), `ProfitTrackerPage.jsx`, `api.js`

### Session 46 (2026-01-15) - 6 Bug Fixes ✅

#### Feature 1: Adjust Trade Dialog (Renamed from Enter AP) ✅
- **Issue**: Past trade adjustments didn't account for deposits/withdrawals on that day
- **Solution**: Enhanced dialog with full adjustment options:
  - **Deposit/Withdrawal Selection**: "Did you deposit or withdraw on this day?" dropdown
    - "No, just enter profit"
    - "Yes, I made a deposit"
    - "Yes, I made a withdrawal"
  - **Amount Input**: When deposit/withdrawal selected, shows input for the amount
  - **Adjusted Balance**: Optional field to manually correct the balance before trade
  - **Actual Profit**: Input for the actual profit made
  - **Adjustment Summary**: Shows all adjustments being made
- **Logic**: If deposit/withdrawal selected, records it first, then logs the trade with correct balance
- **Files Modified**: `ProfitTrackerPage.jsx`

#### Feature 2: Timer Stall Fix ✅
- **Issue**: Trade countdown timer stopped/stalled every 2 minutes
- **Root Cause**: Browser throttles setInterval in background tabs
- **Fixes Applied**:
  1. Reduced interval to 500ms (from 1000ms) for more frequent updates
  2. Added `visibilitychange` event listener to force update when tab becomes visible
  3. Auto-refresh countdown in stall detection (instead of just showing warning)
  4. Countdown now recalculates from localStorage target time each tick
- **Files Modified**: `TradeMonitorPage.jsx`

### Session 44 (2026-01-15) - Daily Projection History Fix ✅

#### Feature: Keep Past Trade Dates in Daily Projection
- **Issue**: When a new day came, previous day's trade data disappeared from Daily Projection
- **Fix**: Updated `generateDailyProjectionForMonth` to always start from first day of month
- **Changes**:
  - Removed filter that hid past dates for current month
  - Added "missed" status for past days without trades
  - Added visual indicators: ✓ checkmark for completed trades, dimmed styling for missed days
  - Running balance now calculated correctly from month start
- **Result**: Users can now see full trade history for the month including:
  - Past dates with completed trades (green highlight, ✓ badge)
  - Past dates with missed trades ("Enter AP" button available)
  - Today's date (blue highlight, "TODAY" badge)
  - Future dates
- **Files Modified**: `ProfitTrackerPage.jsx` (lines 98-195, 630-665, 2120-2195)

### Session 43 (2026-01-15) - Delete Licensee Feature ✅

#### Feature: Delete License from Admin Panel
- **UI**: Added trash icon button in Actions column of Active Licenses table
- **Confirmation Dialog**: Shows warning message and license details before deletion
- **Backend**: Uses existing `DELETE /api/admin/licenses/{license_id}` endpoint
- **Behavior**: 
  - Removes license from system
  - User account preserved (can be re-licensed later)
  - Only Master Admin can delete licenses
- **Files Modified**: `AdminLicensesPage.jsx` (lines 71-75, 326-346, 773-786, 1674-1745)

### Session 42 (2026-01-15) - Licensee Calculation & Synchronization Fixes ✅

#### Issue 1: Remove Ability for Honorary Member to Set Starting Value ✅
- **Fix**: Frontend now hides "Starting Amount" input for honorary licensees
- **Logic**: Honorary licensees start with $0, use standard calculations (deposits + profits - withdrawals)
- **Files Modified**: `AdminLicensesPage.jsx` (lines 922-946, 110-151)

#### Issue 2: Synchronize Dashboard/Profit Tracker/Deposit-Withdrawal Pages ✅
- **Fix**: LicenseeAccountPage now uses `profitAPI.getSummary` as single source of truth
- **Ensures**: All three pages show the same `account_value`
- **Files Modified**: `LicenseeAccountPage.jsx` (lines 79-99)

#### Issue 3: Notice for Licensees When License is Revoked ✅
- **Fix**: Login endpoint checks for active license when user has `license_type`
- **Response**: Returns 403 with message "Your license has been revoked or expired. Please contact the administrator to renew your license."
- **Files Modified**: `server.py` (lines 645-661)

#### Issue 4: Extended Licensee Lot Size Should Be Fixed Per Quarter ✅
- **Bug**: Lot size was growing daily instead of being fixed per quarter
- **Fix**: Updated `calculate_extended_license_projections` to:
  - Calculate `quarter_lot_size` once per quarter (starting_amount / 980)
  - Calculate `quarter_daily_profit` once per quarter (lot_size × 15)
  - Both values stay FIXED for entire quarter, only recalculate on first trading day of new quarter
- **Verified**: Tested with actual data showing 6 quarters with fixed values
- **Files Modified**: `server.py` (lines 2949-3003), `ProfitTrackerPage.jsx` (lines 619-658)

### Session 41 (2026-01-15) - Licensee Authentication & Daily Projection Enhancements ✅

#### Feature 1: Licensees Bypass Heartbeat Membership ✅
- **Issue**: Licensees registering via invite link couldn't login - "not a heartbeat member" error
- **Fix**: Updated login endpoint to check `license_type` and skip Heartbeat verification for licensees
- **Code**: `server.py` lines 643-653 - Added `is_licensee = user.get("license_type") is not None`
- **Files Modified**: `server.py`

#### Feature 2: Extended Licensee Profit Calculation Clarification ✅
- **Status**: Already correctly implemented
- **Logic**: Quarterly compounding - daily profit stays same within quarter, recalculates on first trading day of each new quarter
- **Function**: `calculate_extended_license_projections()` in `server.py` (lines 2949-2994)

#### Feature 3: Extended Licensee Daily Projection UI ✅
- **Changes**:
  - Removed "Actual Profit" column for extended licensees
  - Removed "P/L Diff" column for extended licensees
  - Added "Profit Credited" column showing:
    - ✓ (green checkmark) when Master Admin traded that day
    - ✗ (red X) when Master Admin did not trade
- **Files Modified**: `ProfitTrackerPage.jsx`

#### Feature 4: Master Admin Trades API ✅
- **New Endpoint**: `GET /api/profit/master-admin-trades`
- **Purpose**: Returns master admin's trading status by date for extended licensees
- **Access**: Licensees only (returns 403 for non-licensees)
- **Response**: `{ trading_dates: { "2026-01-15": { traded: true, actual_profit: 285.57 } } }`
- **Files Modified**: `server.py`, `api.js`

### Session 40 (2026-01-15) - Backend Refactoring ✅

#### Task 1: Data Integrity Check (status: None) ✅
- **Status**: Verified - No deposits with `status: None` found
- **Details**: Checked licensee_transactions collection - all 9 transactions have valid status fields

#### Task 2: Unified Account Value Calculation ✅
- **Implementation**: Created utility functions in `/app/backend/utils/calculations.py`
- **New Functions**:
  - `calculate_account_value(db, user_id, user, include_licensee_check)` - Unified account value calculation
  - `get_user_financial_summary(db, user_id, user)` - Comprehensive financial summary
- **Refactored Endpoints**:
  - `GET /api/profit/summary` - Now uses `get_user_financial_summary()`
  - `POST /api/profit/simulate-withdrawal` - Now uses `calculate_account_value()`
- **Benefits**: 
  - Single source of truth for account value calculation
  - Consistent handling of licensees vs regular users
  - Easier maintenance and testing
- **Files Modified**: `utils/calculations.py`, `utils/__init__.py`, `server.py`

#### Task 3: Database Module for Route Migration ✅
- **Created**: `/app/backend/database.py`
- **Features**:
  - Centralized database connection
  - `Database` class with property accessors for all collections
  - Ready for future route migration from monolithic `server.py`
- **Status**: Module created but not yet integrated (preparation for future migration)

#### Server.py Size Reduction
- **Before**: 6130 lines
- **After**: 6096 lines
- **Note**: Major reduction will come when routes are migrated to `/routes/` directory

### Session 39 (2026-01-15) - Licensee Management Enhancements ✅

#### Feature 1: Licensees Cannot Set Starting Balance ✅
- **Status**: Already implemented correctly
- **Details**: Starting balance can only be set by admin via license invite creation or reset-balance endpoint. No endpoint exists for licensees to set their own balance.
- **Files**: All balance-setting endpoints are admin-protected in `server.py`

#### Feature 2: Master Admin Can Edit Licensee Profiles ✅
- **Implementation**: Added "Edit Profile" dialog to `AdminLicensesPage.jsx`
- **Features**:
  - UserCog icon button in Actions column
  - Dialog with Full Name and Timezone fields
  - Uses `PUT /api/admin/members/{user_id}` endpoint
- **Backend**: Updated `GET /api/admin/licenses` to return `user_timezone` field
- **Files Modified**: `AdminLicensesPage.jsx`, `api.js`, `server.py`

#### Feature 3: License Balance Syncs Across All Pages ✅
- **Implementation**: Updated profit-related endpoints to check for licensees
- **Changes**:
  - `GET /api/profit/summary` returns `license.current_amount` for licensees
  - `POST /api/profit/simulate-withdrawal` uses license balance for licensees
  - `POST /api/admin/licenses/{id}/reset-balance` updates both `license.current_amount` and `user.account_value`
  - Team analytics uses license balance for licensee account values
- **Files Modified**: `server.py` (lines 1017-1042, 1044-1070, 2363-2370)

### Session 38 (2026-01-15) - Bug Fixes ✅

#### Bug Fix 1: Countdown Timer Stops Under a Minute ✅
- **Issue**: Countdown timer would sometimes stop counting, especially under a minute
- **Fix**: Added stall detection and manual refresh capability
- **Implementation**:
  - `lastCountdownUpdateRef` tracks when countdown was last updated
  - `countdownStalled` state turns true if no update in 3 seconds
  - Amber warning appears with "Countdown may have stalled" message
  - "Refresh Timer" button available to manually restart countdown
  - `restartCountdown` function clears interval and starts fresh from localStorage
- **Files Modified**: `TradeMonitorPage.jsx`

#### Bug Fix 2 & 3: BVE Signal Editing Issues ✅
- **Issue 2**: When editing a signal from BVE, it said "signal not found"
- **Issue 3**: When in BVE mode editing an active signal activated outside BVE, it affected actual signal
- **Root Cause**: `handleSaveEdit` in AdminSignalsPage always called production endpoint `/admin/signals/{id}` regardless of BVE mode
- **Fix**: Updated `handleSaveEdit` to check `isInBVE` and use `bveAPI.updateSignal` when in BVE mode
- **Files Modified**: `AdminSignalsPage.jsx`

### Session 37 (2026-01-15) - Trade History Actions & Onboarding Fix ✅

#### Trade History Role-Based Actions ✅
- **Feature**: Added "Actions" column to Trade History table in Trade Monitor
- **Master Admin**: Sees "Reset" button to delete trades (with confirmation dialog)
- **Other Users**: See "Request Change" button to submit change requests to admin
- **Endpoints Used**:
  - `DELETE /api/trade/reset/{trade_id}` - Master admin only, deletes trade and creates audit trail
  - `POST /api/trade/request-change` - Any user, creates pending change request
- **UI Components**: Reset button (red), Request Change button (amber) with loading states
- **Request Change Dialog**: Shows trade details and textarea for reason
- **Files Modified**: `TradeMonitorPage.jsx`, `api.js`

#### Onboarding Tour Persistence Fix ✅
- **Issue**: Tour could not be dismissed by clicking the overlay background
- **Fix**: Updated overlay to call `handleSkip` on click, properly saving state to localStorage
- **Key**: `crosscurrent_tour_completed` in localStorage prevents tour from reappearing
- **Files Modified**: `OnboardingTour.jsx`

### Session 35 (2026-01-13) - Security Fix & Trade Flow Improvements ✅

#### P0: Security Fix - Report Generation Endpoint ✅
- **Issue**: Report generation endpoints (`/api/profit/report/*`) were accessible to any authenticated user
- **Fix**: Moved endpoints to admin-protected routes (`/api/admin/analytics/report/*`)
- **Endpoints Changed**:
  - `GET /api/profit/report/image` → `GET /api/admin/analytics/report/image`
  - `GET /api/profit/report/base64` → `GET /api/admin/analytics/report/base64`
- **Additional**: Added `user_id` parameter for admins to generate reports for specific users
- **Files Modified**: `server.py`, `api.js`, `AdminAnalyticsPage.jsx`

#### Bug Fix: BVE Trade Notification Flood ✅
- **Issue**: When trade time was reached in BVE mode, push notifications were flooding and the alarm wouldn't stop
- **Root Cause**: The interval firing toast notifications multiple times before `clearInterval` took effect
- **Fix**: Added `tradeNotifiedRef` to track if notification has been shown, preventing duplicates
- **Files Modified**: `TradeMonitorPage.jsx`

#### Trade Flow Improvements ✅
- **Issue**: Trade flow was confusing - "End Trade" button unclear, alarm didn't stop properly
- **New Flow**:
  1. Alarm rings → Button shows "Trade Entered" 
  2. Click "Trade Entered" → Alarm stops, button changes to "Exit Trade"
  3. Click "Exit Trade" → Shows actual profit input form
- **Files Modified**: `TradeMonitorPage.jsx`

#### Missed Trade Popup Enhancement ✅
- **Feature 1**: Auto-show popup when trade window passes via backend API check (`/api/trade/missed-trade-status`)
- **Feature 2**: Auto-show popup when signal is marked completed and user hasn't traded
- **Feature 3**: "Enter AP" button in Daily Projection Table for missed trades
  - Shows in Profit Tracker → Month card → Daily Projection dialog
  - Allows users to retroactively log actual profit for missed trades
  - Calculates and displays P/L difference
  - Updates the trade log with `is_retroactive: true` flag
  - **Fixed**: After submission, button hides and values update correctly
  - **Fixed**: User removed from Missed Trade list in Team Analytics
- **Feature 4**: Daily Projection now uses latest account value for current month
  - Ensures newly logged trades are immediately reflected
- **New Endpoints**:
  - `GET /api/trade/missed-trade-status` - Check if user should see missed trade popup
  - `POST /api/trade/log-missed-trade` - Log a trade retroactively
- **Bug Fixes**:
  - Fixed timezone handling in trade dates (now always includes +00:00)
  - Fixed missing `signal_id` field in retroactive trades
  - Fixed `profit_difference` calculation in retroactive trades
- **Files Modified**: `server.py`, `api.js`, `TradeMonitorPage.jsx`, `ProfitTrackerPage.jsx`

#### Manual Deposit Override Feature ✅
- **Status**: USER VERIFICATION PENDING
- **Feature**: Text link "Wrong Calculations? Enter your total deposit manually" in Simulate Deposit dialog
- **Allows**: Users to bypass automatic fee calculations and enter exact deposit amounts
- **Files**: `ProfitTrackerPage.jsx`

### Session 34 (2026-01-12) - P1 & P2 Features ✅

#### P1: Off-Canvas Notification Panel ✅
- Created `NotificationSheet.jsx` component using Shadcn Sheet
- Slides in from right side with full notification list
- Shows connection status with "Live updates active" or "Disconnected"
- Reconnect button available when disconnected

#### P1: WebSocket Offline Indicator ✅
- Added prominent "Connection lost" banner with WifiOff icon
- Red pulsing indicator on notification bell when disconnected
- Reconnect button to manually reconnect WebSocket

#### P1: Automated Missed Trade Email ✅
- Added APScheduler for background tasks
- `check_missed_trades()` runs at 11 PM UTC daily
- Sends email to members who didn't log a trade that day
- Uses customizable "missed_trade" email template
- Logs all sent emails to `email_history` collection

#### P1: Email Template Testing ✅
- Added "Test" button to Email Template editor
- Dialog with recipient email and variable value inputs
- Live preview showing variables replaced with test values
- Sends test email with "[TEST]" prefix in subject

#### P2: Top Performers Feature ✅
- Backend: `GET /api/admin/top-performers` endpoint
- Supports `exclude_non_traders` parameter (default true)
- Filters to traders who traded in last 30 days
- Returns ranked list with total_profit, total_trades, avg_profit_per_trade
- Frontend: Top Performers card on Admin Analytics page
- "Active traders only" checkbox to toggle filter

#### P2: Image-Based Performance Report ✅
- Created `/app/backend/services/report_generator.py` using PIL/Pillow
- Dark-themed 800x600 PNG with account stats, profit, trades, win rate
- `GET /api/profit/report/image` - Downloads PNG file
- `GET /api/profit/report/base64` - Returns base64 for preview
- Frontend: "Generate Report" button and dialog on ProfitTrackerPage
- Supports Daily, Weekly, Monthly periods

#### P2: BVE Signal Update ✅
- Added `PUT /api/bve/signals/{id}` endpoint
- Allows deactivating/updating BVE signals
- Fixed "Deactivate" button not working in BVE mode

#### Bug Fixes ✅
- Fixed toast notification persistence issue
- Fixed notification flood when trade alarm triggers

### Session 33 (2026-01-12) - BVE Bug Fixes ✅

#### Bug Fix 1: BVE Signal Not Appearing on Dashboard/Trade Monitor ✅
- **Root Cause**: `loadData` function used stale closure for `isInBVE` state
- **Fix**: Wrapped `loadData` in `useCallback` with `isInBVE` as dependency
- **Files Modified**: `TradeMonitorPage.jsx`, `DashboardPage.jsx`

#### Bug Fix 2: Mute Button Not Stopping Active Alarm ✅
- **Root Cause**: Audio continued playing after `soundEnabled` was set to false
- **Fix**: Added `useEffect` to immediately stop audio when `soundEnabled` becomes false
- **File Modified**: `TradeMonitorPage.jsx`

#### Bug Fix 3: Projection Value Mismatch ✅
- **Root Cause**: Inconsistent use of `truncateTo2Decimals` for exit value calculation
- **Fix**: Applied `truncateTo2Decimals` to `exitValue` calculation (LOT × profitMultiplier)
- **File Modified**: `TradeMonitorPage.jsx`

### Session 31 Part 3 (2026-01-12) - BVE & Trade Persistence ✅

#### Feature 1: Trade Check-in State Persistence ✅
- Trade check-in state now persists across navigation
- Stored in localStorage with key `trade_check_in`
- Contains: targetTime, signalId, signalInfo, checkedInAt
- Automatically restores countdown on page return
- Clears on trade completion or manual stop

#### Feature 2: Beta Virtual Environment (BVE) ✅
A sandboxed environment for Super/Master Admins to test without affecting real data.

**Backend:**
- `POST /api/bve/enter` - Creates BVE session, snapshots current data
- `GET /api/bve/signals` - Get signals in BVE mode
- `POST /api/bve/signals` - Create signal in BVE (isolated)
- `POST /api/bve/rewind` - Restore to entry snapshot
- `POST /api/bve/exit` - Exit BVE, cleanup data

**Frontend:**
- **BVE Button** in header for Super/Master Admin (flask icon)
- **BVE Active Badge** shows when in BVE mode
- **Rewind Button** - Restores to entry point
- **Exit Button** - Exits BVE mode
- **Purple Banner** on Admin Signals page when in BVE
- **Title Change** - "BVE Trading Signals" instead of "Trading Signals"

**Data Collections:**
- `bve_sessions` - Stores session snapshots
- `bve_trading_signals` - Isolated signals
- `bve_trade_logs` - Isolated trade logs
- `bve_deposits` - Isolated deposits

### Session 31 Part 2 - Bug Fixes & Email History ✅
- Fixed Deactivate Signal button (missing API method)
- Fixed Daily Projection accuracy (uses stored LOT/Projected values)
- Added Email History frontend in Admin Settings

### Session 31 Part 1 - Major Feature Batch ✅
- Fee restructuring ($1 Binance fee moved to deposit)
- Commission system (Simulate Commission + Commission Records)
- Monthly table simplification (removed Daily Profit & LOT columns)
- Dream Daily Profit calculator
- Quick signal deactivation
- Merin iframe refresh button
- Admin role dropdown fix
- Trade time restrictions (20 min before trade)
- Floating countdown popup

## Pending Tasks

### P0 - Critical (NONE REMAINING)
- ~~Security vulnerability in report generation endpoint~~ ✅ FIXED

### P1 - High Priority
- **Profit Tracker Calculation Discrepancy**: User reported balance calculations don't match live data
- **User-configurable announcement display**: Allow users to hide/show global announcements
- **Backend Route Migration**: server.py → /routes/ directory

### P2 - Medium Priority
- **Admin Daily Email Recap**: Scheduled daily summary to admins
- Frontend Refactoring: Break down large admin components
- Mobile responsiveness improvements

## Key API Endpoints

### Performance Reports (Admin Protected)
- `GET /api/admin/analytics/report/image` - Download PNG report (Admin only)
- `GET /api/admin/analytics/report/base64` - Get base64 report for preview (Admin only)

### BVE (Beta Virtual Environment)
- `POST /api/bve/enter` - Enter BVE, create session
- `GET /api/bve/signals` - Get BVE signals
- `POST /api/bve/signals` - Create BVE signal
- `GET /api/bve/active-signal` - Get active BVE signal
- `POST /api/bve/trade/log` - Log trade in BVE
- `GET /api/bve/summary` - Get BVE profit summary
- `POST /api/bve/rewind` - Rewind to entry snapshot
- `POST /api/bve/exit` - Exit BVE, cleanup

### Other Key Endpoints
- `POST /api/profit/commission` - Record commission
- `GET /api/settings/email-history` - Email logs
- `PUT /api/admin/signals/{id}` - Update/deactivate signal

## Test Credentials
- Master Admin: iam@ryansalvador.com / admin123

## Tech Stack
- Backend: FastAPI, Motor (async MongoDB), PyJWT, Pydantic
- Frontend: React, React Router, Axios, TailwindCSS, Shadcn/UI, Recharts
- State: React Context (AuthContext, WebSocketContext, TradeCountdownContext, BVEContext)

## Critical Business Logic

### Trade Check-in Persistence
```javascript
// Stored in localStorage
{
  targetTime: "2026-01-12T14:00:00.000Z",
  signalId: "signal-uuid",
  signalInfo: { product: "MOIL10", direction: "BUY" },
  checkedInAt: "2026-01-12T13:40:00.000Z"
}
```
- Restores countdown on page return
- Valid for 30 minutes after trade time
- Clears on trade completion

### BVE Data Isolation
- All BVE data stored in separate collections (bve_*)
- bve_session_id links data to session
- Rewind deletes current BVE data and restores from snapshot
- Exit cleans up all BVE collections for session

### Daily Projection Calculation
For **completed trades**: Uses stored `lot_size` and `projected_profit` from trade logs
For **pending trades**: Calculated as `balance / 980` and `lot_size * 15`

# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification
- **Integrations**: Cloudinary, Emailit, ExchangeRate-API, APScheduler

## Completed Work

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

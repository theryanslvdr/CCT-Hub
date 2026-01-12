# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification
- **Integrations**: Cloudinary, Emailit, ExchangeRate-API

## Completed Work

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

### P0 - High Priority
- Email Template Testing with Variables Preview
- Automated "Missed Trade" Email System (scheduler)

### P1 - Medium Priority
- WebSocket "Offline" Icon indicator
- Off-Canvas Notification Panel (slide-out style)
- Backend Route Migration (server.py → /routes/)

### P2 - Lower Priority
- Exclude Non-Traders from Top Performers
- Generate Image Recap Report (16:9 landscape)
- Admin Email Recap Summary

## Key API Endpoints

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

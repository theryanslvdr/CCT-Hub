# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification
- **Integrations**: Cloudinary, Emailit, ExchangeRate-API

## Completed Work

### Session 31 Part 2 (2026-01-12) - Bug Fixes & Email History ✅

#### Bug Fix 1: Deactivate Signal Button ✅
- **Issue:** Deactivate button on active signals wasn't working
- **Root Cause:** Missing `adminAPI.updateSignal` method in api.js
- **Fix:** Added `updateSignal: (id, data) => api.put(/admin/signals/${id}, data)` to adminAPI

#### Bug Fix 2: Daily Projection Accuracy ✅ (CRITICAL)
- **Issue:** After recording a trade, the LOT size and Projected Profit were changing
- **User Example:** LOT was 15.28, Projected was 229.20, but after trade they showed 15.52 and changed values
- **Root Cause:** Frontend was recalculating LOT and Projected values from current balance instead of using stored values
- **Fix:** Modified `generateDailyProjectionForMonth` to use stored `lot_size` and `projected_profit` from trade logs for completed trades
- **Result:** LOT (15.28) and Target Profit ($229.20) now remain fixed after trade is recorded

#### Feature: Email History Frontend ✅
- Added `/settings/email-history` GET endpoint (admin only)
- Added `/settings/email-history` DELETE endpoint (master admin only)
- Added Email History card to Admin Settings → Emails tab
- Shows: Status (with colored badges), Recipient, Subject, Type, Sent At
- Includes pagination for large email histories
- Clear History button for Master Admin

### Session 31 Part 1 - Major Feature Batch ✅

#### Fee Restructuring ✅
- Moved $1 Binance fee from Withdrawal to Deposit

#### Commission System ✅
- "Simulate Commission" button + Commission Records popup

#### Monthly Table Simplification ✅
- Removed "Daily Profit" and "Lot Size" columns

#### Navigation Improvements ✅
- "Trade Now" → /trade-monitor, "I'm Ready to Trade" button text

#### Dream Daily Profit Calculator ✅
- Replaced "Exit Value Calculator" with new profit goal calculator

#### Quick Signal Actions ✅
- "Deactivate" button on active signal card

#### Merin Iframe Refresh ✅
- Added refresh icon button

#### Admin Role Dropdown Fix ✅
- Removed "Admin", kept Basic Admin, Super Admin, Master Admin

#### Trade Time Restrictions ✅
- Button locked until 20 min before trade time

#### Floating Trade Countdown ✅
- Popup when navigating away during trade (with beeping)

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
- POST /api/profit/commission - Record referral commission
- GET /api/profit/commissions - Get user's commission history
- GET /api/admin/members/{id}/deposits - Get member deposits (admin)
- GET /api/admin/members/{id}/withdrawals - Get member withdrawals (admin)
- GET /api/settings/email-history - Get email logs (admin)
- DELETE /api/settings/email-history - Clear email logs (master admin)
- PUT /api/admin/signals/{id} - Update signal (admin)

## Test Credentials
- Master Admin: iam@ryansalvador.com / admin123

## Tech Stack
- Backend: FastAPI, Motor (async MongoDB), PyJWT, Pydantic
- Frontend: React, React Router, Axios, TailwindCSS, Shadcn/UI, Recharts
- State: React Context (AuthContext, WebSocketContext, TradeCountdownContext)

## Critical Business Logic

### Daily Projection Calculation
For **completed trades**, the system now uses STORED values from trade logs:
- `lot_size` - Locked at trade time (e.g., 15.28)
- `projected_profit` - Locked at trade time (e.g., 229.20)
- These values DO NOT change after the trade is recorded

For **pending/future trades**, values are calculated dynamically:
- `lot_size = running_balance / 980`
- `projected_profit = lot_size * 15`

### Fee Structure
- **Deposit:** 1% fee + $1 Binance fee
- **Withdrawal:** 3% Merin fee only (no Binance fee)

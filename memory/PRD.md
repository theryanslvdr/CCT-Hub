# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification
- **Integrations**: Cloudinary, Emailit, ExchangeRate-API

## Completed Work

### Session 31 (2026-01-12) - Major Feature Batch ✅

#### 1. Fee Restructuring ✅
- Moved $1 Binance fee from Withdrawal to Deposit
- Deposit now shows: Binance USDT, 1% fee, $1 Binance fee, Receive Amount
- Withdrawal only shows: Gross, 3% Merin fee, Net Amount

#### 2. Commission System ✅
- Added "Simulate Commission" button in Profit Tracker
- Commission dialog with USDT Amount and Traders Count fields
- New "Commission Records" button to view history
- Backend API endpoints: POST /api/profit/commission, GET /api/profit/commissions

#### 3. Monthly Table Simplification ✅
- Removed "Daily Profit" and "Lot Size" columns from monthly table
- Now shows only: Month, Trading Days, Final Balance, Actions

#### 4. Navigation Improvements ✅
- "Trade Now" in daily projection navigates to /trade-monitor (not /trade)
- "Enter the Trade Now!" renamed to "I'm Ready to Trade"

#### 5. Dream Daily Profit Calculator ✅
- Replaced "Exit Value Calculator" with "Dream Daily Profit"
- Shows: Target daily profit → Required balance → Amount to add
- Formula: Balance = (Target ÷ 15) × 980

#### 6. Quick Signal Actions ✅
- Added "Deactivate" button on active signal card
- One-click signal deactivation for admins

#### 7. Merin Iframe Refresh ✅
- Added refresh icon button in Merin Trading Platform section
- Reloads iframe on click

#### 8. Admin Role Dropdown Fix ✅
- Removed plain "Admin" option from role upgrade dropdown
- Options now: Basic Admin, Super Admin, Master Admin

#### 9. Daily Projection Balance Bug Fix ✅
- Fixed: balanceBefore now shows balance BEFORE today's profit, not after
- Account value adjustment for current month's trade logs

#### 10. Post-Trade Navigation ✅
- Added "View Daily Projection" button in celebration popup
- "Forward to Profit Tracker" now redirects to profit tracker

#### 11. Live Registration Notifications ✅
- WebSocket notification to all admins when new user registers
- Email notification sent to all admin users

#### 12. Simulation Accuracy Fix ✅
- Fixed: Master Admin simulation now fetches complete member data
- Trade logs, deposits, withdrawals all fetched for simulated member
- New API endpoints: GET /api/admin/members/{id}/deposits, GET /api/admin/members/{id}/withdrawals

#### 13. Trade Time Restrictions ✅
- "I'm Ready to Trade" button disabled until 20 minutes before trade time
- Shows countdown: "Trading window opens in: X minutes"
- Helpful text explaining the 20-minute window

#### 14. Floating Trade Countdown ✅
- Created TradeCountdownContext for global countdown state
- When checked in and navigating away, floating popup appears
- Shows countdown with "Go to Trade Monitor" button
- Beeping sound in last 30 seconds (5-second burst)

### Session 30 (2026-01-11) - Maintenance & Mobile ✅
- Maintenance Tab with mode toggle and custom message
- Announcements System (Info/Warning/Success types)
- Maintenance Landing Page with hidden admin override
- Mobile-Friendly Notices on complex pages

### Session 29 - P2 Tasks ✅
- Debt Management Tooltips
- Shared Admin Components
- Backend Route Structure
- Additional Email Templates

### Session 28 - P1 Features ✅
- Backend Services Package
- WebSocket real-time notifications
- File upload endpoints

### Session 27 - P0 Features ✅
- Dashboard tabs for members
- API key security modal
- Persistent footer
- Login customization

## Pending Tasks

### P0 - High Priority
- Email Template Testing with Variables Preview
- Automated "Missed Trade" Email System
- Email History Frontend Table

### P1 - Medium Priority
- WebSocket "Offline" Icon indicator
- Announcement Display Options (more control)
- Off-Canvas Notification Panel (slide-out style)
- Backend Route Migration (server.py → /routes/)

### P2 - Lower Priority
- Exclude Non-Traders from Top Performers
- Generate Image Recap Report (16:9 landscape)
- Admin Email Recap Summary
- Frontend Component Refactoring

## Key API Endpoints
- POST /api/profit/commission - Record referral commission
- GET /api/profit/commissions - Get user's commission history
- GET /api/admin/members/{id}/deposits - Get member deposits (admin)
- GET /api/admin/members/{id}/withdrawals - Get member withdrawals (admin)
- POST /api/settings/test-emailit - Test Emailit API key
- POST /api/settings/test-heartbeat - Test Heartbeat API key
- WS /ws/{client_id} - WebSocket connection

## Test Credentials
- Master Admin: iam@ryansalvador.com / admin123

## Tech Stack
- Backend: FastAPI, Motor (async MongoDB), PyJWT, Pydantic
- Frontend: React, React Router, Axios, TailwindCSS, Shadcn/UI, Recharts
- State: React Context (AuthContext, WebSocketContext, TradeCountdownContext)

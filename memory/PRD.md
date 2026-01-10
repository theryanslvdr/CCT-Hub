# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard. Features include JWT authentication with Heartbeat verification, role-based access (User/Admin/Super Admin), and API Center for external app communication.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification gatekeeper
- **Integrations**: Cloudinary (file uploads), Emailit (emails), ExchangeRate-API (currency conversion)

## User Personas
1. **Traders** - Track profits, monitor trades, manage debts, plan financial goals
2. **Admins** - Manage trading signals, members, platform settings
3. **Super Admins** - Full platform control including role management

## Core Requirements (Static)
- [x] Heartbeat community verification for registration
- [x] LOT Size Calculator (LOT × 15 = Exit Value)
- [x] Withdrawal fees: 3% Merin + $1 Binance, 1-2 business days processing
- [x] Live currency conversion (USDT-USD-Local currencies)
- [x] Trading signals in Philippine/Taiwan/Singapore timezone (GMT+8)

## P1 Features Completed (2026-01-10)

### Member Management Enhancements
- ✅ Search members by name/email
- ✅ Filter by role (user/admin/super_admin)
- ✅ Filter by status (active/suspended)
- ✅ Pagination with page controls
- ✅ View member details with Profile/Statistics/Activity tabs
- ✅ Edit member profile (name, timezone, LOT size)
- ✅ Suspend/unsuspend members
- ✅ Set temporary password
- ✅ Upgrade/downgrade roles

### Trading Signals Improvements
- ✅ Custom profit_points multiplier (default: 15)
- ✅ Edit existing signals
- ✅ Simulate signals (Super Admin only, marked as [SIMULATED])
- ✅ Toggle signal active/inactive
- ✅ Notes field for additional context

### Profit Tracker Features
- ✅ Initial balance setup dialog (limited to 2 decimals)
- ✅ **Deposit/Withdrawal Records**: Hidden behind buttons, aligned right
- ✅ Multi-step deposit/withdrawal simulation with fee calculations
- ✅ **Projection Vision** card with Year dropdown (1-5 years)
- ✅ **Monthly Table accordion**: 
  - Grouped by "Current Period" and Year 1-5
  - Shows Trading Days count, Final Balance, LOT Size, Daily Profit
  - **Daily View button** for each month
- ✅ **Daily Projection Popup**:
  - Shows only weekdays (excludes weekends and holidays)
  - For current month: shows remaining days from today
  - Columns: Date, Balance Before, LOT Size, Target Profit, **Actual Profit**
  - Actual Profit status: `-` (future) | `Pending Trade` (past, no trade) | `Trade Now` (today + signal) | Value (completed)
  - Trade Now button links to Trade Monitor
- ✅ **Large number formatting**: $X.XX Million, Billion, Trillion
- ✅ **LOT Size**: All displays truncated to 2 decimal places
- ✅ **Total Deposits card**: Currency dropdown inside (USD, PHP, EUR, GBP)
- ✅ **Trading Signal Banner**: Shows today's signal with Trade Now → Merin
- ✅ **Multi-step Reset Tracker** with password verification

## Bug Fixes Completed (2026-01-10)
- ✅ **PROB-1**: Fixed login persistence - Users now stay logged in after page refresh (AuthContext localStorage fix)
- ✅ **DM-1**: Fixed "Add Debt" functionality - POST /api/debt now works correctly
- ✅ **PPL-1**: Fixed "Add Goal" functionality - POST /api/goals now works correctly
- ✅ Fixed /api/trade/active-signal backward compatibility for missing profit_points field

## What's Been Implemented (2026-01-10)

### Backend
- ✅ User authentication with JWT and Heartbeat verification
- ✅ Role-based access control (User/Admin/Super Admin)
- ✅ Profile settings with timezone and LOT size
- ✅ Profit Tracker APIs (deposits, summary, exit calculation, withdrawal simulation)
- ✅ Trade Monitor APIs (trade logging, active signals, daily summary, forward to profit)
- ✅ Debt Management APIs (CRUD, payments, repayment planning)
- ✅ Profit Planner/Goals APIs (CRUD, contributions, goal planning)
- ✅ Admin APIs (trading signals with timezone, member management, role upgrades)
- ✅ API Center (external connections, webhook receiver)
- ✅ Platform Settings APIs (SEO, branding, UI customization)
- ✅ Currency conversion API

### Frontend
- ✅ Dark professional UI design
- ✅ Onboarding Tour (9 steps explaining all features)
- ✅ Login/Register with Heartbeat notice
- ✅ Profile Settings (timezone, LOT size)
- ✅ Dashboard with KPIs, performance chart, live rates
- ✅ Profit Tracker with deposit management, withdrawal simulation
- ✅ Trade Monitor with:
  - **Active Signal Card** (redesigned from Admin Signals page, shows date, simulated tag)
  - **LOT Size Card** (fetched from Profit Tracker: Balance ÷ 980)
  - **Projected Exit Value Card** (LOT × multiplier, replaces LOT Calculator)
  - **Exit Value Calculator Popup** (custom LOT input)
  - **Your Time Card** - Philippine Time prominent, user local time underneath
  - **Timezone Conversion** in signal card (shows user's local trade time)
  - Check-in → Countdown with **5-second beep alert** → "Enter the Trade Now!" button
  - Enter actual profit → **Celebration Popup** with performance message
  - Forward profit to Profit Tracker button
  - **Trade History Table** with pagination (Date, Product, Direction, LOT Size, Time Set, Time Entered (editable), Projected, Actual, P/L Diff)
  - **Streak Indicator** (fire icon with count at top right of Trade History)
- ✅ **Today's Summary** (simplified): Only Actual Total + P/L Difference + Encouragement message
- ✅ Debt Management with repayment planning
- ✅ Profit Planner with goal creation and progress tracking
- ✅ Admin: Trading Signals with timezone selection (Asia/Manila, Asia/Singapore, Asia/Taipei)
- ✅ Admin: Member management with role upgrades
- ✅ Admin: API Center for external connections
- ✅ Admin: Platform Settings (SEO, branding, colors)

## Key Trading Flow
1. Admin posts daily signal (product, time, direction, timezone, multiplier)
2. Trader sees signal with **LOT Size Card** (from Profit Tracker) and **Projected Exit Value**
3. **Your Time card** shows Philippine time prominently (local time underneath)
4. Trader clicks "**Enter the Trade Now!**" → countdown starts
5. Last **5 seconds**: beep countdown alert
6. At trade time: "ENTER THE TRADE NOW!" alert shows → Trader clicks "End Trade"
7. Trader enters actual profit amount
8. **Celebration Popup** shows with performance message (exceeded/perfect/below)
9. Trader clicks "Forward to Profit Tracker" button

## Prioritized Backlog
### P0 (Critical) - ✅ DONE
- [x] Core authentication flow
- [x] Profit tracking and calculations
- [x] Trade monitoring with exit alerts
- [x] Profile settings with timezone
- [x] Login persistence bug (PROB-1) - FIXED
- [x] Add Debt bug (DM-1) - FIXED
- [x] Add Goal bug (PPL-1) - FIXED

### P0 (Critical) - Trade Monitor Enhancements ✅ DONE (2026-01-10)
- [x] LOT Size card fetches from Profit Tracker (Balance ÷ 980)
- [x] Projected Exit Value card (LOT × multiplier) replaces LOT Calculator
- [x] Exit Value Calculator popup with custom LOT input
- [x] Philippine Time prioritized in Your Time card
- [x] User local time shown smaller underneath
- [x] Profit multiplier (×15) visible next to trading signal
- [x] User local time visible next to trading signal in banner
- [x] "Enter the Trade Now!" button (changed from "Exit Now!")
- [x] 5-second countdown beep before trade time
- [x] Celebration popup after entering actual profit
- [x] Today's Summary simplified: only Actual Total + P/L Difference + Encouragement

### P1 (High) - ✅ COMPLETED (2026-01-10)
- [x] Member Management enhancements (search, filters, pagination, view details with tabs, edit profile, suspend/unsuspend, set temp password)
- [x] Trading Signals management improvements (profit_points multiplier, edit signals, simulate signals for super admin)
- [x] Profit Tracker feature additions (reset tracker, initial balance setup dialog)
- [x] Profile page password reset (already implemented)
- [ ] Branding settings (logo, favicon, site title) - partially implemented
- [ ] Email notifications for trade signals (Emailit configured)

### P2 (Medium)
- [ ] Interactive onboarding tour
- [ ] Tooltips for Debt Management
- [ ] Alarm music selection for Trade Monitor
- [ ] Integration with Merin Trading Platform chart
- [ ] Heartbeat API user sync
- [ ] Advanced analytics and reporting
- [ ] Export data functionality

## Test Account
- Email: admin@crosscurrent.com
- Password: admin123
- Role: Super Admin

## Super Admin Secret Code
CROSSCURRENT2024

## API Keys Configured
- Heartbeat: hb:579ef3a8e97533a0461dd93c23ceb6fb531817e4ae65b8b669
- Emailit: em_8CTRD13gKPSo8dnC6xzYT93DA1tiiPBm
- Cloudinary: crosscurrent / 387887783889587 / 97bu1ngM6OYE6VKGRId9Fh9802E

# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard. Features include JWT authentication with Heartbeat verification, role-based access, and API Center for external app communication.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification gatekeeper
- **Integrations**: Cloudinary (file uploads), Emailit (emails), ExchangeRate-API (currency conversion), Merin Trading Platform (embedded iframe)

## User Personas & Role Hierarchy (2026-01-11)
1. **Normal Member** (role: `member`) - Modular dashboard access assigned by Super Admin
   - Default dashboards: Dashboard, Profit Tracker, Trade Monitor, Profile
2. **Basic Admin** (role: `basic_admin`) - Manage members, trading signals, assist with resets
3. **Super Admin** (role: `super_admin`) - Full access except hidden/upcoming features
   - Secret code for registration: `CROSSCURRENT2024`
4. **Master Admin** (role: `master_admin`) - Full access including hidden features + simulate member view
   - Secret code for registration: `CrossCurrentGODSEYE`
   - Current Master Admin: iam@ryansalvador.com

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
- ✅ **Interactive Onboarding Tour** (8 steps with progress bar, navigation, page highlighting)
- ✅ Login/Register with Heartbeat notice
- ✅ Profile Settings (timezone, LOT size)
- ✅ Dashboard with KPIs, performance chart, live rates
- ✅ Profit Tracker with deposit management, withdrawal simulation
- ✅ Trade Monitor with:
  - **Split Screen Layout** - Trade controls on left, Merin iframe on right
  - **Merin Trading Platform** - Embedded in mobile aspect ratio for seamless trading
  - **Active Signal Card** (redesigned with date, simulated tag with Flask icon)
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
- ✅ Debt Management with repayment planning (**HIDDEN - Master Admin only**)
- ✅ Profit Planner with goal creation and progress tracking (**HIDDEN - Master Admin only**)
- ✅ Admin: Trading Signals with timezone selection (Asia/Manila, Asia/Singapore, Asia/Taipei)
  - **Signal History** with pagination (10 per page)
  - **Monthly Archive** with accordion view (signals organized by month)
  - Archive Current Month button to clear history
- ✅ Admin: Member management with role upgrades and allowed_dashboards assignment
  - **Account Value column** (visible to Super/Master Admin only)
  - **Simulate Member** feature (view member's real account data)
  - **Edit Member** without LOT size field
  - **Pagination** for members list
- ✅ Admin: API Center for external connections
- ✅ Admin: Platform Settings (SEO, branding, colors)
- ✅ **Sidebar Updates (2026-01-11)**:
  - "Simulate Member View" button (Master Admin only)
  - "HIDDEN FEATURES" section with Crown icon (Master Admin only)
  - Role label with Crown icon for Master Admin

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

### P0 (Critical) - Trade Monitor V2 Enhancements ✅ DONE (2026-01-10)
- [x] Active Signal card redesigned from Admin Signals page (Radio icon, date, no edit)
- [x] Fixed timezone conversion (shows user local time correctly)
- [x] SIMULATED signals show Flask icon tag instead of [SIMULATED] text in notes
- [x] Trade History table with pagination (all 9 columns)
- [x] Time Entered column is editable (pencil icon, save/cancel)
- [x] Streak indicator with fire icon at top right of Trade History

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

## Completed Work (2026-01-11 Session - Latest)

### Sidebar Menu Improvements ✅
1. **Removed "Main Menu"** label
2. **Hidden Features** - Crown icon moved to right side
3. **Renamed** "Administration" → "Admin Section"
4. **Renamed** "Analytics" → "Team Analytics"
5. **Minimal spacing** - Reduced padding and margins for cleaner look

### Header Improvements ✅
1. **Removed notification bell icon** (wasn't functional)
2. **Added secret Super Admin upgrade feature**:
   - Click Settings icon 10 times within 3 seconds
   - Dialog prompts for secret code: `SUPER_ADMIN_BYPASS`
   - Upgrades user to Super Admin role
   - Only works for non-admin users (admins redirected to Settings page)

### P0 Bug Fix - Member Simulation Feature ✅ COMPLETE
**Issue 1**: Simulation didn't show member's Total Deposits  
**Issue 2**: Analytics didn't include admin account values  
**Issue 3**: No way to view individual member stats  
**Issue 4**: No date filtering for performance graphs  

**Solutions Implemented**:
1. **Total Deposits Fix**: Added `getSimulatedTotalDeposits()` and `getSimulatedTotalProfit()` to AuthContext. Updated ProfitTrackerPage to use `effectiveTotalDeposits` and `effectiveTotalProfit`.

2. **Admin in Analytics**: Modified `/admin/analytics/team` endpoint to include ALL user roles (members + admins) in team statistics. Team Account Value now shows $14.6K (admin + users).

3. **Member Dropdown**: Added "All Members" dropdown to Analytics page header. Clicking a member opens detailed stats dialog showing Account Value, LOT Size, Total Profit, Total Deposits, Recent Trades.

4. **Date Range Picker**: Added From/To date pickers with Apply button to Performance Overview section. Backend supports `start_date` and `end_date` query parameters.

**Testing Results** (iteration_14.json):
- Backend: 100% pass rate (8/8 tests)
- Frontend: 100% all critical flows working
- All four improvements verified working

### Analytics Dashboard Features ✅ COMPLETE
- Team KPIs (includes all user roles)
- Performance graphs with date filtering
- Member dropdown with stats dialog
- Missed Trade notification system
- Top Performers leaderboard (shows role badges)
- Archive Old Trades button
- Recent Team Trades with pagination

## Current Test Accounts
- **Master Admin**: iam@ryansalvador.com / admin123 (role: master_admin, account_value: $14,521.62)
- **Test User**: test_user_092113@example.com (role: user, account_value: $100, has: Honorary License)

## Completed Work (2026-01-11 Session 2 - Latest)

### P0 - Settings Page Overhaul ✅ COMPLETE
- **Tabbed Interface**: Reorganized AdminSettingsPage into 4 tabs:
  1. **SEO & Meta** - Site Title, Description, OG Image URL
  2. **Branding** - Logo upload, Favicon upload, Hide Emergent Badge toggle
  3. **UI Customization** - Primary/Accent color pickers with preview
  4. **Integrations** - API key fields for Emailit, Cloudinary (3 fields), Heartbeat
- All fields with proper labels, descriptions, and external links
- Eye toggle icons for showing/hiding sensitive API keys

### P0 - Sidebar Restructure ✅ COMPLETE
- **Moved to Profile Popover**: "Platform Settings" and "API Center" links
- **Admin Section Anchored**: Members, Trading Signals, Team Analytics, Transactions at bottom of sidebar (above user profile)
- **Clean Layout**: Profile popover now includes: Profile Settings, Platform Settings, API Center, Log Out

### P0 - Custom License System ✅ COMPLETE
**License Types**:
1. **Extended Licensee** - Complex quarterly profit calculation
   - Formula: Daily Profit = (Account Value / 980) × 15
   - Fixed for entire quarter, recalculated at quarter start based on ending balance
   - Trading calendar skips weekends and US holidays (NYSE schedule)
   - Badge: "EXT" (purple)

2. **Honorary Licensee** - Standard profit calculations
   - Funds are **EXCLUDED** from team analytics totals
   - Badge: "HON" (amber)
   - `honorary_excluded_count` returned in team analytics

**Backend Endpoints** (Master Admin only):
- `GET /api/admin/licenses` - List all licenses with current calculated amounts
- `POST /api/admin/licenses` - Assign new license
- `DELETE /api/admin/licenses/{id}` - Remove license

**Frontend Implementation**:
- License badge (EXT/HON) next to member names in Members table
- Award icon button for license management (Master Admin only)
- License dialog shows: License type, Starting Amount, Current Amount, Start Date, Status, Notes
- "Remove License" button in manage dialog
- License count in Members page stats cards

**Team Analytics Updates**:
- `is_honorary` flag returned for each member
- `honorary_excluded_count` in response
- Honorary licensee funds excluded from `total_account_value` and `total_profit`

### Testing Results (iteration_15.json)
- Backend: 100% pass rate (13/13 tests)
- Frontend: 100% all critical flows working
- All features verified working

## Files Modified This Session
- `/app/frontend/src/pages/admin/AdminSettingsPage.jsx` - Complete rewrite with tabs
- `/app/frontend/src/components/layout/Sidebar.jsx` - Restructured with profile popover
- `/app/frontend/src/pages/admin/AdminMembersPage.jsx` - Added license management UI
- `/app/frontend/src/lib/api.js` - Fixed duplicate profitAPI export
- `/app/backend/server.py` - Team analytics honorary exclusion, license datetime fix
- `/app/tests/test_iteration_15.py` - New comprehensive test file

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
- ✅ Initial balance setup dialog for first-time users
- ✅ Reset tracker functionality (clears all deposits and trade logs)
- ✅ Improved deposit history visualization

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
  - LOT Calculator (LOT × 15 formula)
  - World Timer (user's timezone from profile)
  - Check-in → Countdown → Exit Alert → End Trade button
  - Enter actual exit value → Celebration/Encouragement
  - Forward profit to Profit Tracker button
- ✅ Today's Summary in Trade Monitor
- ✅ Debt Management with repayment planning
- ✅ Profit Planner with goal creation and progress tracking
- ✅ Admin: Trading Signals with timezone selection (Asia/Manila, Asia/Singapore, Asia/Taipei)
- ✅ Admin: Member management with role upgrades
- ✅ Admin: API Center for external connections
- ✅ Admin: Platform Settings (SEO, branding, colors)

## Key Trading Flow
1. Admin posts daily signal (product, time, direction, timezone)
2. Trader checks Trade Monitor, sets LOT size
3. LOT Calculator shows exit value (LOT × 15)
4. Trader clicks "Check In" → countdown starts
5. At trade time: Exit Alert shows → Trader clicks "End Trade"
6. Trader enters actual exit value
7. App shows celebration/encouragement based on performance
8. Trader can forward profit to Profit Tracker

## Prioritized Backlog
### P0 (Critical) - ✅ DONE
- [x] Core authentication flow
- [x] Profit tracking and calculations
- [x] Trade monitoring with exit alerts
- [x] Profile settings with timezone
- [x] Login persistence bug (PROB-1) - FIXED
- [x] Add Debt bug (DM-1) - FIXED
- [x] Add Goal bug (PPL-1) - FIXED

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

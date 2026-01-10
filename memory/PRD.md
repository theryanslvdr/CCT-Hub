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
- [ ] Heartbeat community verification for registration
- [ ] LOT Size Calculator (LOT × 15 = Exit Value)
- [ ] Withdrawal fees: 3% Merin + $1 Binance, 1-2 business days processing
- [ ] Live currency conversion (USDT-USD-Local currencies)

## What's Been Implemented (2026-01-10)
### Backend
- ✅ User authentication with JWT and Heartbeat verification
- ✅ Role-based access control (User/Admin/Super Admin)
- ✅ Profit Tracker APIs (deposits, summary, exit calculation, withdrawal simulation)
- ✅ Trade Monitor APIs (trade logging, active signals, daily summary)
- ✅ Debt Management APIs (CRUD, payments, repayment planning)
- ✅ Profit Planner/Goals APIs (CRUD, contributions, goal planning)
- ✅ Admin APIs (trading signals, member management, role upgrades)
- ✅ API Center (external connections, webhook receiver)
- ✅ Platform Settings APIs (SEO, branding, UI customization)
- ✅ Currency conversion API
- ✅ Cloudinary file upload integration

### Frontend
- ✅ Dark professional UI design
- ✅ Login/Register with Heartbeat notice
- ✅ Dashboard with KPIs, performance chart, live rates
- ✅ Profit Tracker with deposit management, withdrawal simulation
- ✅ Trade Monitor with LOT Calculator, World Timer, Check-in flow
- ✅ Debt Management with repayment planning
- ✅ Profit Planner with goal creation and progress tracking
- ✅ Admin: Trading Signals management
- ✅ Admin: Member management with role upgrades
- ✅ Admin: API Center for external connections
- ✅ Admin: Platform Settings (SEO, branding, colors)

## Prioritized Backlog
### P0 (Critical)
- [x] Core authentication flow
- [x] Profit tracking and calculations
- [x] Trade monitoring with exit alerts

### P1 (High)
- [ ] Email notifications for trade signals
- [ ] Sound alarm for exit alerts (implemented but needs audio file)
- [ ] Real-time WebSocket updates for signals

### P2 (Medium)
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

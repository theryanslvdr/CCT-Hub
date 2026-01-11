# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard. Features include JWT authentication with Heartbeat verification, role-based access, and API Center for external app communication.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification gatekeeper
- **Integrations**: Cloudinary (file uploads), Emailit (emails), ExchangeRate-API (currency conversion)

## User Personas & Role Hierarchy
1. **Normal Member** (role: `member`) - Modular dashboard with tabs
2. **Basic Admin** (role: `basic_admin`) - Manage members, signals
3. **Super Admin** (role: `super_admin`) - Full access except hidden features
4. **Master Admin** (role: `master_admin`) - Full access including hidden features
5. **Extended/Honorary Licensee** - Special member types

## Completed Work

### Session 29 (2026-01-11) - P2 Complete ✅

#### 1. Debt Management Tooltips ✅
- Added `TooltipProvider` wrapper to DebtManagementPage
- Created `InfoTooltip` component with HelpCircle icon
- Added tooltips to all 4 overview cards:
  - **Total Debt**: "The sum of all remaining balances..."
  - **Monthly Commitment**: "Total of all minimum payments due..."
  - **Account Balance**: "Your current trading account balance..."
  - **Status**: Context-aware based on can_cover_this_month
- Added tooltips to Add Debt form fields:
  - Debt Name, Total Amount, Minimum Payment, Due Day, Interest Rate

#### 2. Shared Admin Components ✅
Created `/app/frontend/src/components/admin/SharedComponents.jsx`:
- `StatsCard` - Displays metric with icon
- `SearchFilterBar` - Search input with filters
- `Pagination` - Page navigation controls
- `RoleBadge` - Role display with icon
- `LicenseBadge` - License type badge
- `StatusBadge` - Transaction/status badge
- `LoadingSpinner` - Loading indicator
- `EmptyState` - No data placeholder
- `ActionButtons` - Action button group

#### 3. Backend Route Structure ✅
Created modular route files in `/app/backend/routes/`:
- `auth.py` - Authentication routes structure
- `admin.py` - Admin management routes structure
- `trade.py` - Trading routes structure
- `profit.py` - Financial routes structure
- `settings.py` - Settings routes structure
- `__init__.py` - Package exports with migration docs

#### 4. Additional Email Templates ✅
Added 4 new templates to `/app/backend/services/email_service.py`:
- `get_welcome_email()` - New user welcome with feature list
- `get_transaction_update_email()` - Transaction status updates
- `get_missed_trade_email()` - Missed trade notifications
- `get_weekly_summary_email()` - Weekly performance summary

### Session 28 - P1 Complete ✅
- Backend Services Package (email, file, websocket)
- WebSocket real-time notifications
- File upload endpoints
- Email test endpoint

### Session 27 - P0 Complete ✅
- Dashboard tabs for members
- API key security modal
- Persistent footer
- Login customization
- Production URL setting
- CrossCurrent branding

## Backend Structure

### Models (`/app/backend/models/`)
```
models/
├── __init__.py - Exports all models
├── user.py - User, Auth, Profile models
├── trade.py - Trade, Signal models
├── common.py - Deposit, Debt, Goal, Notification models
├── license.py - License, Invite, Transaction models
└── settings.py - Platform, Email template models
```

### Utils (`/app/backend/utils/`)
```
utils/
├── __init__.py - Exports all utilities
├── auth.py - Password, JWT, role functions
└── calculations.py - LOT, profit, fee calculations
```

### Services (`/app/backend/services/`)
```
services/
├── __init__.py - Exports all services
├── email_service.py - Emailit + 8 templates
├── file_service.py - Cloudinary uploads
└── websocket_service.py - Real-time notifications
```

### Routes (`/app/backend/routes/`)
```
routes/
├── __init__.py - Package with migration docs
├── auth.py - Auth routes structure
├── admin.py - Admin routes structure
├── trade.py - Trade routes structure
├── profit.py - Financial routes structure
└── settings.py - Settings routes structure
```

## Frontend Structure

### Admin Components (`/app/frontend/src/components/admin/`)
```
admin/
└── SharedComponents.jsx - 9 reusable components
```

## API Endpoints Summary

### Core APIs
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register
- `GET /api/profit/summary` - Profit summary
- `GET /api/trade/logs` - Trade history
- `GET /api/debt` - Get debts
- `GET /api/debt/plan` - Debt repayment plan

### Admin APIs
- `GET /api/admin/members` - Member list
- `GET /api/admin/notifications` - Notifications
- `GET /api/admin/licenses` - License management

### Integration APIs
- `POST /api/email/test` - Test email service
- `POST /api/upload/profile-picture` - Upload profile pic
- `GET /api/ws/status` - WebSocket stats
- `WS /ws/{user_id}` - Real-time notifications

## Test Credentials
- **Master Admin**: iam@ryansalvador.com / admin123
- **Regular Member**: jaspersalvador9413@gmail.com / test123

## Testing Summary
- **Iteration 29**: 13/13 backend tests passed (100%)
- **Iteration 28**: 16/16 backend tests passed (100%)
- **Iteration 27**: All P0 features tested (100%)

## Future Tasks
- [ ] Implement actual route migration from server.py
- [ ] Add Alarm Music Selection for Trade Monitor
- [ ] Break down AdminMembersPage.jsx into smaller components
- [ ] Break down AdminLicensesPage.jsx into smaller components

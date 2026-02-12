# CrossCurrent Finance Center - PRD

## Original Problem Statement
Build a Finance Center for CrossCurrent traders with Profit Tracker, Trade Monitor, Debt Management, Profit Planner, and Admin Dashboard.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Auth**: JWT with Heartbeat API verification
- **Integrations**: Cloudinary, Emailit, ExchangeRate-API, APScheduler, CoinGecko (USDT rates)

## Completed Work

### Session 80 (2026-02-12) - Trade Monitor Layout Redesign + Export Debug Data

#### UI: Trade Monitor 2-Column Layout Redesign
- Restructured page layout to 2-column grid (`lg:grid-cols-[1fr_340px]`)
- **Left column**: Active Signal Card, LOT Size/Calculator/Projected Exit (3-column row), Trade Control
- **Right sidebar (desktop)**: Multiplier panel (flex-1, tall), Dream button + Rocket icon, Sound toggle
- Multiplier and Sound toggle remain inline on mobile (hidden sidebar with `lg:hidden`)
- LOT Size + Calculator icon + Projected Exit now in a 3-part row matching the user-provided screenshot
- Your Time, Today's Summary, Merin iframe remain in 3-column grid below
- Trade History remains full width at bottom
- **Testing**: Iteration 92 -- 100% pass rate (8/8 features verified)

#### FEATURE: Export Debug Data
- New backend endpoint: `GET /api/admin/export-debug-data/{user_id}`
- Downloads comprehensive JSON file with: user profile, all trades, deposits, withdrawals, reset trades, balance overrides, commissions
- Export button added to Admin Members page alongside Run Diagnostic button
- **Testing**: Verified working via curl and testing agent

### Session 79 (2026-02-12) - Trade Monitor Layout Redesign (Previous)

#### UI: Trade Monitor 3-Column Layout
- Moved Merin iframe from full-height right sidebar into a 3-column grid alongside "Your Time" and "Today's Summary" (all equal height)
- Trade History card is now full-width below the 3-column grid
- Mobile: Merin panel hidden, mobile button still available
- **Testing**: Iteration 91 -- 100% pass, all 10 features verified

### Session 78 (2026-02-12) - Data Health Badge + Refactoring

#### ENHANCEMENT: Data Health Score Badge
- Compact amber pill inline with "Projection Vision" card title
- Clicking opens Pre-Sync Wizard; auto-refreshes after syncing

#### REFACTORING: Backend Route Extraction
- Created `/app/backend/deps.py`: Shared dependencies module
- Extracted `/app/backend/routers/currency.py`, `debt.py`, `goals.py`, `api_center.py`
- server.py: 9486 -> 9026 lines

#### REFACTORING: Frontend Component Extraction
- Extracted TransactionRecords.jsx, PreSyncWizard.jsx, DataHealthBadge.jsx, SimulateActions.jsx
- ProfitTrackerPage.jsx: 5294 -> 4800 lines

### Session 77 (2026-02-12) - Pre-Sync Validation Wizard
- Multi-step wizard for data integrity before balance sync

### Session 76 (2026-02-12) - Balance Override Feature
- Balance override/Merin sync functionality

### Session 75 (2026-02-11) - Critical Bug Fixes & Account Diagnostic Tool

## Known Issues
- **Run Diagnostic (production)**: 404 in user's production environment - infrastructure issue, not code. Provide curl command for user to debug their own environment.
- **Cloudinary**: File upload is placeholder/mocked.

## Prioritized Backlog

### P0 - In Progress
- Continue refactoring server.py (~9000 lines -> extract more routers: settings, bve, profit, admin)
- Continue refactoring ProfitTrackerPage.jsx (~4800 lines -> extract ProjectionVision, dialogs)

### P1 - Upcoming
- Progressive Web App (PWA) capabilities
- Actual Cloudinary file upload implementation

### P2 - Future
- Performance optimization
- Additional admin tools

## Key API Endpoints
- `POST /api/admin/run-diagnostic/{user_id}` - Live diagnostic summary
- `GET /api/admin/export-debug-data/{user_id}` - Full JSON export for offline analysis
- `GET /api/profit/validate-sync-readiness` - Pre-Sync Wizard backend
- `POST /api/profit/balance-override` - Manual balance override

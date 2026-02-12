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

#### UI: Trade Monitor Complete Layout Redesign
- Redesigned page into priority-based 2-column layout (`lg:grid-cols-[1fr_380px]`)
- **Left column** (priority order): Active Signal (top), LOT Size + Projected Exit (side-by-side), Your Time + Today's Summary (side-by-side)
- **Right column**: Merin Trading iframe (tall, spans full height of left content)
- **Bottom (full width)**: Trade Control, Trade History
- Sound toggle removed entirely per user request
- **Testing**: Iteration 93 -- 100% pass rate (9/9 features verified)

#### FEATURE: Full PWA Implementation
- Created `manifest.json` with app name "The CrossCurrent Hub", dark theme (#09090b), standalone display mode, 4 icon sizes
- Created `sw.js` service worker with stale-while-revalidate for static assets, network-first for navigation, API bypass
- Created `offline.html` branded offline fallback page
- Generated PWA icons: 16px, 32px, 192px, 512px, apple-touch-icon (180px)
- Added PWA meta tags to `index.html` (apple-mobile-web-app-capable, theme-color, etc.)
- Created `PWAInstallBanner` component with custom "Add to Home Screen" prompt
- Registered service worker in `App.js`
- Page title updated to "The CrossCurrent Hub"
- **Testing**: Iteration 94 -- 100% pass rate (30/30 backend + all frontend verified)

#### REFACTORING: Backend Route Extraction (Continued)
- Extracted BVE routes to `/app/backend/routes/bve.py` (338 lines)
- Extracted Settings routes to `/app/backend/routes/settings.py` (413 lines) — includes platform settings, email templates, integration tests, email history
- server.py: 9066 -> 8360 lines (706 lines removed)
- All routes tested and verified working via curl
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
- Continue refactoring server.py (~8360 lines -> extract more routers: profit, admin, trade, auth)
- Continue refactoring ProfitTrackerPage.jsx (~5200 lines -> deeply coupled dialogs make extraction complex)

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

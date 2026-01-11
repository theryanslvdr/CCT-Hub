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
5. **Extended Licensee** (special member) - Custom quarterly profit calculation
6. **Honorary Licensee** (special member) - Standard calculations, excluded from team analytics

## Core Requirements (Static)
- [x] Heartbeat community verification for registration
- [x] LOT Size Calculator (LOT × 15 = Exit Value)
- [x] Withdrawal fees: 3% Merin + $1 Binance, 1-2 business days processing
- [x] Live currency conversion (USDT-USD-Local currencies)
- [x] Trading signals in Philippine/Taiwan/Singapore timezone (GMT+8)

## Completed Work - Session 27 (2026-01-11)

### P0 - 6 New Features ✅ ALL COMPLETE (100% Pass Rate)

1. **Dashboard Tabs for Members** ✅
   - Regular members (role: member/user) see 4 tabs: Overview, Profit, Trades, Charts
   - Admins do NOT see tabs (original layout preserved)
   - Each tab has unique content:
     - Overview: Performance chart + Your Stats
     - Profit: Profit Summary + Performance Metrics
     - Trades: Full trade history table
     - Charts: Profit Trend + Projected vs Actual bar chart

2. **API Key Security Check Modal** ✅
   - Master Admin sees "Missing API Keys" modal on login
   - Checks for: Heartbeat, Emailit, Cloudinary (all 3 keys)
   - Modal shows: List of missing integrations with descriptions
   - Options: "Remind Me Later" or "Configure Now" → redirects to Settings

3. **Persistent Footer with Custom Links** ✅
   - Footer appears at bottom of ALL pages
   - Shows: Copyright text + Custom links + Made with Emergent badge
   - Admin can customize via Settings > Links tab:
     - Footer Copyright text
     - Footer Links (add/remove with label and URL)

4. **Login Page Customization** ✅
   - Admin can customize via Settings > UI tab:
     - Login Title (e.g., "Welcome to CrossCurrent")
     - Login Tagline (e.g., "Your Trading Finance Hub")
     - Login Notice Message
   - Live preview in settings
   - Login page fetches and displays these settings

5. **Production Site URL Setting** ✅
   - Admin can set via Settings > Branding tab
   - Description: "All test/preview links will be replaced with this URL in emails and exports"
   - Stored in platform_settings collection

6. **Login Card Text Fix** ✅
   - All references to "Heartbeat" in community context changed to "CrossCurrent"
   - Login page says "Only CrossCurrent community members can access this platform."
   - Error messages say "CrossCurrent Traders"
   - Note: Internal Heartbeat API references remain (referring to the API itself)

### Files Modified
- `/app/frontend/src/pages/DashboardPage.jsx` - Added tabs for members
- `/app/frontend/src/components/layout/DashboardLayout.jsx` - Footer integration + API key modal
- `/app/frontend/src/components/layout/Footer.jsx` - Footer component (already existed)
- `/app/frontend/src/pages/LoginPage.jsx` - Uses customizable settings (already had CrossCurrent text)
- `/app/frontend/src/pages/admin/AdminSettingsPage.jsx` - Login settings + Footer settings (already had these)
- `/app/backend/server.py` - PlatformSettings model (already had all fields)

### Testing Results (iteration_27.json)
- Backend: 100% pass rate (10 tests)
- Frontend: 100% pass rate (all UI tests)
- All 6 features verified working

## P1 Tasks - READY TO START

### Backend Refactoring (IN PROGRESS)
Directory structure created, code migration pending:
- `/app/backend/models/` - Pydantic models (files created, empty)
- `/app/backend/routes/` - FastAPI routers (files created, empty)
- `/app/backend/utils/` - Utility functions (files created, empty)

**Next Steps:**
1. Move Pydantic models from server.py to `/app/backend/models/`
2. Move routes from server.py to `/app/backend/routes/`
3. Move utility functions to `/app/backend/utils/`
4. Update server.py to import from new modules

### Frontend Refactoring
- Break down `AdminMembersPage.jsx` into smaller components
- Break down `AdminLicensesPage.jsx` into smaller components

## Future/Backlog (P2)

- [ ] Implement WebSockets for real-time notifications
- [ ] Add Tooltips to Debt Management page
- [ ] Add Alarm Music Selection to Trade Monitor
- [ ] Fully activate and test Emailit integration for sending emails
- [ ] Fully activate and test Cloudinary integration for file storage

## Test Credentials
- **Master Admin**: iam@ryansalvador.com / admin123
- **Regular Member**: jaspersalvador9413@gmail.com / test123

## API Keys Configured
- Heartbeat: hb:579ef3a8e97533a0461dd93c23ceb6fb531817e4ae65b8b669
- Emailit: em_8CTRD13gKPSo8dnC6xzYT93DA1tiiPBm
- Cloudinary: crosscurrent / 387887783889587 / 97bu1ngM6OYE6VKGRId9Fh9802E

## Key Technical Concepts
- **Backend:** FastAPI, Motor (async MongoDB), PyJWT, Pydantic.
- **Frontend:** React, React Router, Axios, TailwindCSS, Shadcn/UI, Recharts.
- **State Management:** React Context API (`AuthContext` for user/simulation state) and component-level state.
- **File Uploads:** Required for licensee deposit workflow. Uses `UploadFile` from FastAPI.

## Database Schema (key collections)
- **platform_settings:** Extended to include `login_title`, `login_tagline`, `login_notice`, `platform_name`, `production_site_url`, `footer_copyright`, and `footer_links`.
- **users:** `account_value` is synced with `licenses.current_amount` for licensees.
- **licenses:** `current_amount` is the source of truth for a licensee's balance.

## Previous Sessions Summary

### Session 26 (Previous)
- Master Admin role promotion without secret code
- LOT Size calculation fix in member details
- Licensee onboarding tour (5 steps)
- Dashboard "Your Stats" card replacement

### Session 25 (Previous)
- Licensee account value sync
- Licensees removed from Member Management
- Login card styling fix

### Sessions 21-24
- Multiple bug fixes for:
  - Heartbeat API verification
  - License type in user response
  - Trade Monitor hidden for licensees
  - Profit Tracker buttons hidden for licensees
  - Password setting flow
  - Licensee simulation dialog
  - Balance logic for deposits/withdrawals

# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Financial trading dashboard ("The CrossCurrent Hub") for the Merin Trading Platform. Full-stack app with React frontend, FastAPI backend, and MongoDB.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001, routes prefixed /api)
- **Database**: MongoDB
- **PWA**: Dynamic manifest via `/api/settings/manifest.json` + service-worker.js
- **Push Notifications**: Web Push API with VAPID keys + pywebpush
- **Production URL**: https://hub.crosscur.rent/

## Credentials
- Master Admin: iam@ryansalvador.com / admin123

## What's Been Implemented (Feb 12, 2026)

### Mobile Bug Fixes (User Lysha)
1. DNT error "Failed: [object Object]" - Fixed param mismatch (trade_date -> date)
2. Adjust button in wizard exits dialog - Redirected to existing Enter AP dialog
3. Balance unchanged after onboarding - Mobile wizard sent `trade_history` instead of `trade_entries`
4. Can't select Missed Trade after typing - Added Clear button, fixed disabled condition
5. Negative trade results blocked - Removed `< 0` validation
6. Mobile Balance Sync Wizard - Full-screen overlay matching Simulate style
7. NaN in Adjust Trade dialog - Added fallback calculations

### Mobile UI Fixes (Trade Monitor)
1. Desktop notice hidden behind header - Removed from mobile view
2. LOT Size/Projected Exit cards - Icons inline on mobile, Dream button inside card
3. Merin iframe - "Open Merin" button hides when iframe displayed, iframe fills viewport height

### Notification System
1. **Notification Preferences** in Profile: Trading Signal, 10/5-min Pre-Trade, Missed Trade (members) + Member Trade Submitted, Missed Trade, Profit Reports, Daily Summary (admins)
2. **Web Push Notifications**: VAPID keys, subscribe/unsubscribe, push toggle in Profile
3. **Pre-trade push scheduling**: 10min and 5min reminders via APScheduler
4. Auto-push when new trading signal published + force-notify button

### Daily Trade Summary
1. Admin page `/admin/daily-summary` - who traded/missed/DNT with profits/commissions
2. Notifications page links to daily summary for trade-related notifications
3. "Notify All Members" button on Active Signal card (master admin)

### PWA Enhancements
1. Dynamic `manifest.json` via `/api/settings/manifest.json`
2. PWA App Icon upload in Admin > Branding settings
3. Device-detecting install instructions dialog
4. "Install App" in sidebar menu
5. Service worker with push notification handlers

### Backend Refactoring (Partial)
1. Created `/app/backend/helpers.py` for shared helper functions
2. `settings.py` and `bve.py` previously extracted from server.py

## Key API Endpoints
- `GET/PUT /api/users/notification-preferences`
- `GET /api/users/vapid-public-key`
- `POST/DELETE /api/users/push-subscribe`
- `GET /api/admin/daily-trade-summary`
- `POST /api/admin/signals/force-notify`
- `POST /api/admin/push-notify-all`
- `GET /api/settings/manifest.json`
- `POST /api/settings/upload-pwa-icon`
- `POST /api/trade/did-not-trade?date=YYYY-MM-DD`

## Remaining Backlog

### P1 (High)
- Continue backend refactoring (server.py still ~8600 lines)
- User verification of all features in production

### P2 (Medium)
- Frontend refactoring of ProfitTrackerPage.jsx (consider Zustand)
- Cloudinary file upload implementation

## Known Issues
- "Run Diagnostic" fails in production (infrastructure, not code)
- Cloudinary integration is placeholder

## 3rd Party Integrations
Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush

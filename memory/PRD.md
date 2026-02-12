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

## What's Been Implemented

### Session Feb 12, 2026 (Current)

**Mobile Bug Fixes (User Lysha):**
1. DNT button error - Fixed param mismatch (trade_date -> date)
2. Adjust button in wizard - Redirected to existing Enter AP dialog
3. Balance not updating after onboarding - Mobile wizard sent `trade_history` instead of `trade_entries`
4. Missed Trade button disabled - Added Clear button, fixed condition
5. Negative trade results - Removed validation blocking negative values
6. Mobile Balance Sync Wizard - Full-screen overlay matching Simulate style

**Mobile UI Fixes (Trade Monitor):**
1. Desktop notice removed from mobile view (was hidden behind header)
2. LOT Size card: Large icon hidden on mobile, inline icon added
3. Projected Exit card: Dream button now inline inside card, not floating outside
4. Merin iframe: "Open Merin" button hides when iframe is displayed, iframe height dynamic

**Notification System:**
1. Notification Preferences in Profile: Trading Signal, 10/5-min Pre-Trade, Missed Trade (members) + Member Trade Submitted, Missed Trade, Profit Reports, Daily Summary (admins)
2. Web Push Notifications: VAPID keys, subscribe/unsubscribe endpoints, push toggle in Profile
3. Push notifications sent automatically when new trading signal is published
4. Push notifications sent when admin force-notifies from signal card

**Daily Trade Summary:**
1. Admin page at `/admin/daily-summary` showing traded/missed/DNT members with profits
2. Notifications page links to daily summary for trade-related notifications
3. Force Notify button on Active Signal card (master admin only)

**PWA Enhancements:**
1. Dynamic manifest.json via `/api/settings/manifest.json` (supports custom icons)
2. PWA App Icon upload in Admin > Branding settings
3. Device-detecting install instructions dialog
4. "Install App" menu item in sidebar
5. Service worker updated with push notification handlers

### Previous Sessions (Completed)
- Dashboard layout redesign, Data Export feature
- Backend refactoring (settings.py, bve.py extracted)
- Pre-Sync Validation Wizard, Data Health Score

## Prioritized Backlog

### P1 (High)
- Continue backend refactoring (extract trade, profit, admin routes from server.py ~8600 lines)
- User verification of all implemented features

### P2 (Medium)
- Frontend refactoring of ProfitTrackerPage.jsx (consider Zustand)
- Cloudinary file upload implementation (currently placeholder)
- Pre-trade countdown push notifications (10min/5min before scheduled trade)

## Known Issues
- "Run Diagnostic" feature fails in production (infrastructure issue, not code)
- Cloudinary integration is still a placeholder

## Key API Endpoints
- `GET/PUT /api/users/notification-preferences`
- `GET /api/users/vapid-public-key`
- `POST/DELETE /api/users/push-subscribe`
- `GET /api/admin/daily-trade-summary`
- `POST /api/admin/signals/force-notify`
- `POST /api/admin/push-notify-all`
- `GET /api/settings/manifest.json`
- `POST /api/settings/upload-pwa-icon`

## 3rd Party Integrations
- Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush

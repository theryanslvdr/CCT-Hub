# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Financial trading dashboard ("The CrossCurrent Hub") for the Merin Trading Platform. Full-stack app with React frontend, FastAPI backend, and MongoDB.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001, routes prefixed /api)
- **Database**: MongoDB
- **PWA**: manifest.json + service-worker.js
- **Production URL**: https://hub.crosscur.rent/

## Credentials
- Master Admin: iam@ryansalvador.com / admin123

## What's Been Implemented

### Session Feb 12, 2026 (Current)

**Mobile Bug Fixes:**
1. DNT button error - Fixed param mismatch (trade_date -> date)
2. Adjust button in wizard - Redirected to existing Enter AP dialog
3. Balance not updating after onboarding - Mobile wizard sent `trade_history` instead of `trade_entries`
4. Missed Trade button disabled - Added Clear button, fixed condition
5. Negative trade results - Removed validation blocking negative values
6. Mobile Balance Sync Wizard - Full-screen overlay matching Simulate style
7. NaN display in Adjust Trade - Added fallback calculations

**Notification Preferences System:**
1. Backend endpoints: GET/PUT `/api/users/notification-preferences`
2. Profile page: Notification Preferences card with toggle switches
3. Member notifications: Trading Signal, 10-min/5-min Pre-Trade, Missed Trade Report
4. Admin notifications: Member Trade Submitted, Member Missed Trade, Profit Reports, Daily Summary

**Daily Trade Summary:**
1. Backend endpoint: GET `/api/admin/daily-trade-summary?date=YYYY-MM-DD`
2. New admin page: `/admin/daily-summary` with stats, traded/missed/DNT member lists
3. Notifications page links to daily summary for trade-related notifications

**Force Notify Members:**
1. Backend endpoint: POST `/api/admin/signals/force-notify`
2. "Notify All Members" button on Active Signal card (master admin only)

**PWA Install Instructions:**
1. Device-detecting instructions dialog
2. "Install App" menu item in sidebar profile dropdown
3. Instructions for Windows, Mac, Android, iOS

### Previous Sessions (Completed)
- Dashboard layout redesign, Data Export feature
- Backend refactoring (settings.py, bve.py extracted)
- Full PWA implementation, Pre-Sync Validation Wizard, Data Health Score

## Prioritized Backlog

### P1 (High)
- Continue backend refactoring (extract trade, profit, admin routes from server.py)
- Provide curl command for "Run Diagnostic" production debugging
- User verification of all implemented features

### P2 (Medium)
- Frontend refactoring of ProfitTrackerPage.jsx (consider Zustand)
- Cloudinary file upload implementation (currently placeholder)
- Push notification delivery mechanism (Web Push API)

## Known Issues
- "Run Diagnostic" feature fails in production (infrastructure issue)
- Cloudinary integration is still a placeholder

## Key API Endpoints
- `GET/PUT /api/users/notification-preferences` - Notification settings
- `GET /api/admin/daily-trade-summary` - Daily trade overview
- `POST /api/admin/signals/force-notify` - Force email signal to members
- `POST /api/admin/export-debug-data/{user_id}` - Debug data export

## 3rd Party Integrations
- Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new

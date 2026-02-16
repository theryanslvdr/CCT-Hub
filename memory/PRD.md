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

### Phase 1 Features (Feb 2026)

#### Trading Signal Blocking
- `GET /api/trade/signal-block-status` - checks if member is blocked (7+ days unreported profit data)
- `POST /api/admin/members/{user_id}/unblock-signal` - admin manual override (N days)
- Admins are never blocked
- Auto-unblocks when user submits profit tracker data
- Frontend: Signal-blocked-card overlay on TradeMonitorPage with "Go to Profit Tracker" CTA
- Frontend: Unblock button in AdminMembersPage member details (Actions tab)

#### Version Banner ("New Version Deployed")
- `GET /api/version` - returns `build_version` UUID (changes on every server restart/deploy)
- Frontend: `VersionBanner` component checks version every 60 seconds
- Shows persistent banner with "Refresh Now" button when version mismatch detected
- Stores cached version in localStorage for comparison

### Previously Implemented
- Mobile bug fixes (onboarding, balance sync, profit tracker)
- PWA install instructions & dynamic manifest
- Notification system (preferences, web push, pre-trade reminders)
- Daily trade summary page
- PWA icon customization
- Production hotfix for PWA endpoints
- Mobile UI fixes (Trade Monitor)

## Key API Endpoints
- `GET /api/version` - Build version check (no auth)
- `GET /api/trade/signal-block-status` - Signal block status (auth)
- `POST /api/admin/members/{user_id}/unblock-signal` - Admin unblock (admin auth)
- `GET/PUT /api/users/notification-preferences`
- `GET /api/settings/manifest.json`
- `POST /api/trade/did-not-trade`

## Upcoming Tasks

### Phase 2: Banners & Popups (P1)
- Customizable sticky notice banner (admin-configurable, dismissible)
- Promotion pop-up (presets, images, text, buttons, admin-managed)

### Phase 3: Habit Tracker (P2)
- "Soft gate" - completing one daily task unlocks trading signal
- Admin interface to manage/add habits
- Pre-written invite task as default

### Phase 4: Affiliate Center (P3)
- Resource hub: conversation starters, story templates, marketing materials
- FAQ section
- Chatbase chatbot embed ("ConSim")

## Backlog
- Backend refactoring of `server.py` (incremental approach, ~8600+ lines)
- Frontend refactoring of ProfitTrackerPage.jsx (state management needed)
- Cloudinary file upload implementation (placeholder)

## Known Issues
- "Run Diagnostic" fails in production (infrastructure)
- Cloudinary integration is placeholder
- Reset Tracker admin account flow (user verification pending)

## 3rd Party Integrations
Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush, Chatbase (Planned)

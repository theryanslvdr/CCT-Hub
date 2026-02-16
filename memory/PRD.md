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

### Phase 2 Features (Feb 2026) - Banners & Popups

#### Notice Banner
- Admin Settings > Banners & Popups tab
- Customizable text, background color, text color, optional link
- Page-specific targeting via checkboxes (Dashboard, Profit Tracker, Trade Monitor, Profit Planner, Debt Manager, Profile, Notifications)
- Dismissible per session (sessionStorage)
- Live preview in admin settings
- Endpoints: `GET /api/settings/notice-banner` (public)

#### Promotion Pop-up
- 3 preset styles: Announcement (blue), Promo (amber), Feature Update (emerald)
- Title, body text, image URL, CTA button with custom URL
- Frequency control: once per session, once per day, every page load
- Endpoints: `GET /api/settings/promotion-popup` (public)

### Phase 1 Features (Feb 2026) - Signal Blocking & Version Banner

#### Trading Signal Blocking
- `GET /api/trade/signal-block-status` - checks if member blocked (7+ days unreported)
- `POST /api/admin/members/{user_id}/unblock-signal` - admin manual override
- Frontend: Signal-blocked-card overlay on TradeMonitorPage
- Frontend: Unblock button in AdminMembersPage member details

#### Version Banner
- `GET /api/version` - returns build_version UUID (changes on restart/deploy)
- Frontend: `VersionBanner` component checks every 60 seconds
- Shows "Refresh Now" banner on version mismatch

### Previously Implemented
- Mobile bug fixes, PWA install flow, web push notifications
- Notification system, daily trade summary
- PWA icon customization, production hotfixes
- Mobile UI fixes

## Key API Endpoints
- `GET /api/version` - Build version (no auth)
- `GET /api/trade/signal-block-status` - Signal block (auth)
- `POST /api/admin/members/{user_id}/unblock-signal` - Admin unblock
- `GET /api/settings/notice-banner` - Notice banner config (no auth)
- `GET /api/settings/promotion-popup` - Popup config (no auth)
- `PUT /api/settings/platform` - Save all settings (admin)

## Upcoming Tasks

### Phase 3: Habit Tracker (P2)
- "Soft gate" - completing one daily task unlocks trading signal
- Admin interface to manage/add habits
- Pre-written invite task as default

### Phase 4: Affiliate Center (P3)
- Resource hub: conversation starters, story templates, marketing materials
- FAQ section
- Chatbase chatbot embed ("ConSim")

## Backlog
- Backend refactoring of `server.py` (incremental, ~8600+ lines)
- Frontend refactoring of ProfitTrackerPage.jsx
- Cloudinary file upload implementation (placeholder)

## Known Issues
- Cloudinary integration is placeholder
- Reset Tracker admin flow (user verification pending)

## 3rd Party Integrations
Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush, Chatbase (Planned)

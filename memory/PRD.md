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

### Banner Analytics Enhancement (Feb 2026)
- `POST /api/settings/banner-analytics/track` - tracks impressions/dismissals (no auth)
- `GET /api/settings/banner-analytics` - admin dashboard with views, dismissals, dismiss rate, days active
- Integrated tracking into NoticeBanner and PromotionPopup components
- BannerAnalyticsCard in admin Banners & Popups tab

### Phase 3: Habit Tracker - Soft Gate (Feb 2026)
- **Member-facing**: `/habits` page with daily task list, completion toggle, gate status badge
- **Admin**: Habit management in Admin Settings > Habits tab (CRUD)
- **3 action types**: send_invite (with copy message), link_click, generic
- **Gate mechanism**: Gate habits block trading signal until at least one is completed daily
- **Signal integration**: signal-block-status API returns `habit_gate_locked` field
- **TradeMonitorPage**: Shows habit-specific blocked message with "Go to Daily Habits" CTA
- **Sidebar**: "Daily Habits" nav item with CheckSquare icon
- **Default seeded habit**: "Send 1 invite today" (send_invite type, gate enabled)

### Phase 2: Banners & Popups (Feb 2026)
- Notice Banner: Admin-configurable sticky bar with page targeting, colors, link, dismiss
- Promotion Popup: 3 presets (Announcement/Promo/Feature Update), image, CTA, frequency control
- Admin UI: Banners & Popups tab in Admin Settings

### Phase 1: Signal Blocking & Version Banner (Feb 2026)
- Signal blocking: Auto-block after 7+ days unreported profit data, admin manual unblock
- Version banner: Detects new deployments via build_version UUID, forces refresh

### Previously Implemented
- Mobile bug fixes, PWA install flow, web push notifications
- Notification system, daily trade summary, PWA icon customization
- Production hotfixes, mobile UI fixes

## Key API Endpoints
- `GET /api/version` - Build version (no auth)
- `GET /api/trade/signal-block-status` - Signal block + habit gate (auth)
- `POST /api/admin/members/{user_id}/unblock-signal` - Admin unblock
- `GET /api/settings/notice-banner` - Banner config (no auth)
- `GET /api/settings/promotion-popup` - Popup config (no auth)
- `POST /api/settings/banner-analytics/track` - Track events (no auth)
- `GET /api/settings/banner-analytics` - Analytics (admin)
- `GET /api/habits/` - Member habits + gate status (auth)
- `POST /api/habits/{id}/complete` - Complete habit (auth)
- `POST /api/habits/{id}/uncomplete` - Undo habit (auth)
- `GET/POST/PUT/DELETE /api/admin/habits` - Admin habit CRUD

## Upcoming Tasks

### Phase 4: Affiliate Center (P1)
- Resource hub: conversation starters, story templates, marketing materials
- FAQ section
- Chatbase chatbot embed ("ConSim")

## Backlog
- Backend refactoring of `server.py` (incremental, ~8900+ lines)
- Frontend refactoring of ProfitTrackerPage.jsx
- Cloudinary file upload implementation (placeholder)

## 3rd Party Integrations
Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush, Chatbase (Planned)

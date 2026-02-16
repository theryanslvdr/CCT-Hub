# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Financial trading dashboard ("The CrossCurrent Hub") for the Merin Trading Platform. Full-stack app with React frontend, FastAPI backend, and MongoDB.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001, routes prefixed /api)
- **PWA**: Dynamic manifest + service worker
- **Push Notifications**: Web Push API with VAPID keys + pywebpush

## Credentials
- Master Admin: iam@ryansalvador.com / admin123

## All 4 Phases Complete + Enhancements

### Phase 1: Signal Blocking & Version Banner
- Auto-block signal after 7+ unreported days, admin manual unblock
- Version banner: detects deployments via build_version UUID

### Phase 2: Banners & Popups
- Notice Banner: page-targeted, customizable colors, link, dismissible
- Promotion Popup: 3 presets, image, CTA, frequency control
- Banner Analytics: impressions, dismissals, dismiss rate tracking

### Phase 3: Habit Tracker (Soft Gate)
- Daily tasks, 3 action types (send_invite, link_click, generic)
- Gate habits block signal until completed
- **Interactive Gate Overlay** on Trade Monitor: "On it!" → screenshot upload → "Task Done" → signal revealed
- Habit Streaks: current/longest streak, total days badges
- Admin CRUD via Settings > Habits tab

### Phase 4: Affiliate Center
- Resource hub at /affiliate with 4 categories (all users can access)
- Copy-to-clipboard on all resources
- Chatbase chatbot embed (ConSim)
- **Admin inline "Add Resource"** + delete buttons on each tab

### Member Activity Feed (Enhancement)
- Live feed on Admin Dashboard, polls every 8 seconds
- Shows habit completions (with screenshot thumbnails) and trade logs
- Green pulsing "Listening" indicator, pulse animation on new items
- `GET /api/admin/activity-feed?since=&limit=` with polling support
- Resolves user names from DB for trade logs with missing names

## Key API Endpoints
- Signal: `GET /api/trade/signal-block-status`, `POST /api/admin/members/{id}/unblock-signal`
- Banners: `GET /api/settings/notice-banner`, `GET /api/settings/promotion-popup`, `POST /api/settings/banner-analytics/track`
- Habits: `GET /api/habits/`, `GET /api/habits/streak`, `POST /api/habits/{id}/complete`, `POST /api/habits/upload-screenshot`
- Affiliate: `GET /api/affiliate-resources`, `GET /api/affiliate-chatbase-public`
- Activity: `GET /api/admin/activity-feed`
- Version: `GET /api/version`

## Backlog
- Backend refactoring of `server.py` (~9500+ lines)
- Frontend refactoring of ProfitTrackerPage.jsx
- Cloudinary file upload (placeholder)

## 3rd Party Integrations
Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush, Chatbase (configurable)

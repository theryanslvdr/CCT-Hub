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
- Habit Streaks: current streak, longest streak, total days badges
- Admin CRUD via Settings > Habits tab
- **Interactive Gate Overlay on Trade Monitor**: "On it!" → screenshot upload (optional) → "Task Done" → signal revealed

### Phase 4: Affiliate Center
- Resource hub at /affiliate with 4 categories (all users can see)
- Copy-to-clipboard on all resources
- Chatbase chatbot embed (ConSim) configurable by admin
- **Admin inline "Add Resource"** button on each tab + delete per resource
- Admin full CRUD via Settings > Affiliate tab

### Enhancements
- Habit Streaks (flame/trophy/calendar badges)
- Banner Analytics (views, dismissals, dismiss rate)
- Screenshot upload for habit completion proof (POST /api/habits/upload-screenshot)

## Key API Endpoints
- `GET /api/version`, `GET /api/trade/signal-block-status`
- `GET /api/settings/notice-banner`, `GET /api/settings/promotion-popup`
- `POST /api/settings/banner-analytics/track`, `GET /api/settings/banner-analytics`
- `GET /api/habits/`, `GET /api/habits/streak`
- `POST /api/habits/{id}/complete`, `POST /api/habits/upload-screenshot`
- `GET /api/affiliate-resources`, `GET /api/affiliate-chatbase-public`
- Admin: `/api/admin/habits`, `/api/admin/affiliate-resources`, `/api/admin/affiliate-chatbase`

## Backlog
- Backend refactoring of `server.py` (incremental, ~9400+ lines)
- Frontend refactoring of ProfitTrackerPage.jsx
- Cloudinary file upload implementation (placeholder)

## 3rd Party Integrations
Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush, Chatbase (configurable)

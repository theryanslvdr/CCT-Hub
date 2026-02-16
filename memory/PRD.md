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

## All 4 Phases Complete

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

### Phase 4: Affiliate Center
- Resource hub at /affiliate with 4 categories
- Conversation Starters, Story Templates, Marketing Materials, FAQs
- Copy-to-clipboard on all resources
- Chatbase chatbot embed (ConSim) configurable by admin
- Admin CRUD via Settings > Affiliate tab

## Key API Endpoints
- `GET /api/version` - Build version
- `GET /api/trade/signal-block-status` - Signal block + habit gate
- `GET /api/settings/notice-banner` - Banner config
- `GET /api/settings/promotion-popup` - Popup config
- `POST /api/settings/banner-analytics/track` - Track events
- `GET /api/settings/banner-analytics` - Analytics
- `GET /api/habits/` - Habits + streak
- `GET /api/habits/streak` - Streak data
- `GET /api/affiliate-resources` - Grouped resources
- `GET /api/affiliate-chatbase-public` - Chatbase config

## Backlog
- Backend refactoring of `server.py` (incremental, ~9200+ lines)
- Frontend refactoring of ProfitTrackerPage.jsx
- Cloudinary file upload implementation (placeholder)

## 3rd Party Integrations
Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new, pywebpush, Chatbase (configurable via admin)

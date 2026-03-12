# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Full-stack trading community platform with admin/member management, habits tracking, referral system, profit tracking, store, and forum features. The platform requires comprehensive UI/UX overhaul, admin tools, AI integrations, and codebase refactoring.

## Core Architecture
- **Frontend:** React (port 3000) with Shadcn/UI, Tailwind CSS, dark theme
- **Backend:** FastAPI (port 8001) with MongoDB
- **3rd Party:** OpenRouter AI, Publitio (image hosting), Heartbeat (verification), TidyCal (booking embed)

## Test Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`

## What's Been Implemented

### P0 Bug Fixes (DONE)
- Fixed Profit Tracker "Failed to log trade" error
- Fixed streak synchronization between dashboard and Rewards Platform
- Fixed referral tree not populating + improved UI
- Fixed member count discrepancy on admin dashboard
- Fixed Share Performance streak showing 0

### P1 Features (DONE)
- Auto streak sync (twice-daily via APScheduler)
- Referral tree D3 visualization
- Suspended member isolation in admin
- Forum "Solved" tab

### P2 Features (DONE)
- Day-of-week specific habits with mandatory screenshot proofs
- Fraud warning system + weekly check
- Smart Registration Security layer
- AI-powered forum post merging
- Admin Dashboard stat card overhaul
- AI Visual Review for Screenshots with RyAI analysis labels
- AI Recommendations for Team Leaders

### UI/UX Overhaul (DONE - 2026-03-11)
- Collapsible Nav Categories (Core, Growth, Rewards, Community, Tools, Admin)
- Hub Store (renamed from Store, includes Streak Freezes)
- Leaderboard Modal in My Rewards
- Invite & Earn in My Team page
- Dashboard Quick Actions
- Notification Badge Counters
- AI Assistant to Forum Posting
- Find a Member in Admin Dashboard
- Enhanced Performance View
- Admin Cleanup RyAI Labels

### TidyCal Booking Integration (DONE - 2026-03-12)
- Admin Settings > API Keys tab: TidyCal Booking card with embed URL input + live preview
- New `/booking` page: Renders TidyCal calendar in iframe, shows empty state when not configured
- "Book a Call" nav item added under Community category in sidebar and mobile menu
- Public `GET /api/settings/booking-embed` endpoint serves the embed URL
- Backend `tidycal_embed_url` field added to PlatformSettings model

### Weekly Team Performance Report (DONE - 2026-03-12)
- New `GET /api/referrals/my-team/weekly-report` endpoint aggregating team trades
- Report shows: Total Trades, Total Profit, Win Rate, Active Traders
- Week-over-week comparison with trend indicators
- Top Performer highlight
- Per-member breakdown table
- Rendered on Team Page between stat cards and AI Recommendations

### Mobile Readiness (DONE - 2026-03-12)
- Fixed sidebar-to-content margin mismatch (md breakpoint alignment)
- Mobile menu updated with Book a Call, My Team, Hub Store nav items
- All pages use responsive grid classes
- Mobile bottom nav, hamburger menu, slide-out drawer all functional

### Backend Refactoring (DONE - 2026-03-11)
- Extracted `admin_cleanup_routes.py` from `admin_routes.py`
- Extracted `admin_members_routes.py` from `admin_routes.py`
- Extracted `AdjustTradeDialog.jsx` from ProfitTrackerPage
- `referred_by` data normalization

## Prioritized Backlog

### P2 (Future)
- Store enhancements (expand item catalog beyond immunity credits)
- Further ProfitTrackerPage.jsx refactoring (~3900 lines)
- ProfitTrackerPage mobile overlay extraction

### P3 (Backlog)
- Additional admin_routes.py extraction (signals, analytics sections)
- Performance optimization (caching, pagination)
- Refactor `referred_by` field usage for consistency

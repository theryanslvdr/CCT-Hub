# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Full-stack trading community platform with admin/member management, habits tracking, referral system, profit tracking, store, and forum features. The user requested comprehensive bug fixes, feature development (stricter habits, smart registration, AI forum merging, team invitations), and significant codebase refactoring.

## Core Architecture
- **Frontend:** React (port 3000) with Shadcn/UI components, dark theme
- **Backend:** FastAPI (port 8001) with MongoDB
- **3rd Party:** OpenRouter AI, Publitio (image hosting), Heartbeat (verification)

## Test Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`

## What's Been Implemented

### P0 Bug Fixes (DONE)
- Fixed Profit Tracker "Failed to log trade" error
- Fixed streak synchronization between dashboard and Rewards Platform
- Fixed referral tree not populating + improved UI readability
- Fixed member count discrepancy on admin dashboard

### P1 Features (DONE)
- Auto streak sync (twice-daily via APScheduler)
- Referral tree D3 visualization fix
- Suspended member isolation in admin
- Forum "Solved" tab

### P2 Features (DONE)
- Day-of-week specific habits with mandatory screenshot proofs
- Fraud warning system + weekly check
- "My Team" page for team leaders
- Smart Registration Security layer
- Admin Cleanup Hub (integrated in dashboard)
- AI-powered forum post merging
- Store for Signal Gate Immunity Credits
- Admin Dashboard stat card overhaul
- **AI Visual Review for Screenshots** — pending proofs with AI badges on Admin Cleanup page (2026-03-11)
- **AI Recommendations for Team Leaders** — AI Insights button on Team page with per-member suggestions (2026-03-11)

### Refactoring (DONE - 2026-03-11)
- Extracted `admin_cleanup_routes.py` from `admin_routes.py`
- Extracted `admin_members_routes.py` from `admin_routes.py` (~730 lines moved)
- Extracted `ProjectionVision.jsx` from ProfitTrackerPage (~226 lines)
- Extracted `AdjustTradeDialog.jsx` from ProfitTrackerPage (~183 lines)
- ProfitTrackerPage reduced from 4319 → 3954 lines
- admin_routes.py reduced from 4631 → 3800 lines
- Text search index on forum `posts` collection
- `referred_by` data normalization startup task

## Prioritized Backlog

### P2 (Future)
- Store enhancements (expand item catalog)
- Normalize `referred_by` usage across codebase
- Performance optimization (caching, pagination)

### P3 (Backlog)
- Further ProfitTrackerPage refactoring (mobile overlays extraction)
- Additional admin_routes.py extraction (signals, analytics sections)

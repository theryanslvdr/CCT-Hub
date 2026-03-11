# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Full-stack trading community platform with admin/member management, habits tracking, referral system, profit tracking, store, and forum features. The platform requires comprehensive UI/UX overhaul, admin tools, AI integrations, and codebase refactoring.

## Core Architecture
- **Frontend:** React (port 3000) with Shadcn/UI, Tailwind CSS, dark theme
- **Backend:** FastAPI (port 8001) with MongoDB
- **3rd Party:** OpenRouter AI, Publitio (image hosting), Heartbeat (verification)

## Test Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`

## What's Been Implemented

### P0 Bug Fixes (DONE)
- Fixed Profit Tracker "Failed to log trade" error
- Fixed streak synchronization between dashboard and Rewards Platform
- Fixed referral tree not populating + improved UI
- Fixed member count discrepancy on admin dashboard
- **Fixed Share Performance streak showing 0** (was hardcoded, now uses rewardsSummary.current_streak)

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
- **Collapsible Nav Categories** — Core, Growth, Rewards, Community, Tools, Admin — only one expanded at a time
- **Hub Store** — Renamed from "Store", now includes Signal Gate Immunity items AND Streak Freezes (moved from My Rewards)
- **Rewards Category** — New nav category containing My Rewards + Hub Store
- **Leaderboard Modal** — Moved from standalone page to button/modal in My Rewards
- **Invite & Earn in My Team** — Invite link card at top of Team page with copy button + referral stats
- **Dashboard Quick Actions** — Track Profits, Manage Team, Hub Store, Community Help buttons
- **Notification Badge Counters** — Admin nav badge shows pending items count
- **AI Assistant → Forum Posting** — When AI can't answer, "Ask the Community Instead" button pre-fills a forum post
- **Find a Member (Admin)** — Search function moved from Affiliate Center to Admin Dashboard
- **Enhanced Performance View** — Total Profit, LOT Size, Daily Target, Total Trades, Win Rate, Streak, Perf Rate
- **Admin Cleanup RyAI Labels** — AI-flagged proofs show "RyAI: Suspicious" or "RyAI: Looks legitimate" with Sparkles icon

### Backend Refactoring (DONE - 2026-03-11)
- Extracted `admin_cleanup_routes.py` from `admin_routes.py`
- Extracted `admin_members_routes.py` from `admin_routes.py` (~730 lines, 15+ endpoints)
- Extracted `ProjectionVision.jsx` and `AdjustTradeDialog.jsx` from ProfitTrackerPage
- ProfitTrackerPage reduced from 4319 → 3954 lines
- admin_routes.py reduced from 4631 → 3800 lines
- `referred_by` data normalization (startup task + consistent $or queries)

## Prioritized Backlog

### P2 (Future)
- Store enhancements (expand item catalog beyond immunity credits)
- Further ProfitTrackerPage mobile overlay extraction

### P3 (Backlog)
- Additional admin_routes.py extraction (signals, analytics sections)
- Performance optimization (caching, pagination)

# CrossCurrent Hub — Product Requirements Document

## Original Problem Statement
Build a comprehensive financial tracking and community platform for CrossCurrent's trading community.

## Core Architecture
- **Frontend:** React 19 + Tailwind CSS + ShadcnUI
- **Backend:** FastAPI (Python) + APScheduler
- **Database:** MongoDB
- **AI:** OpenRouter API (gpt-4o-mini)
- **File Storage:** Publitio

## Implemented Features (All Verified — Iteration 186)

### Foundation (Complete)
- JWT Auth, Dashboard, Profit Tracker, Trade Monitor, Admin Panel
- WebSocket Notifications, Forum, Family Accounts, Licensee Management
- Rewards & Leaderboard, Referral System, Quiz System, Habit Tracker
- Premium Dark Theme, AI Knowledge Assistant, 7-Step Onboarding Gate

### P0 Bug Fixes (2026-03-11)
- Profit Tracker crash (model field mismatch)
- Streak sync (wrong DB field names)
- Referral tree (merin_referral_code mapping)
- Member count (use response.total)

### P1 Features (2026-03-11)
- Auto Streak Sync (CronTrigger mid-day + end-of-day)
- Referral Tree off-white background (Tree + Visual views)
- Suspended Members Isolation (stat cards, excluded from default list)
- Forum Solved Tab (Open/Solved/All tabs)

### P2 Features (2026-03-11)
- **Habits Overhaul:** Day-of-week habits, screenshot proof required, admin management
- **Fraud Warning System:** Admin reject → warning → popup → acknowledge → 7-day countdown → auto-suspend
- **Team System:** My Team page with member activity, stats, danger status
- **Smart Registration Security:** Auto-flag suspicious signups, admin approval queue
- **Admin Cleanup Page:** One-stop hub (Pending Proofs, Fraud Warnings, In Danger, Auto-Suspended, Pending Registrations)
- **AI Forum Merging:** OpenRouter-powered content blending with fallback concatenation
- **Dashboard Integration:** Cleanup alerts embedded in Admin Dashboard

## Remaining Backlog

### P2 — Remaining
- Signal Gate Immunity Credits (purchasable bypass)
- AI Visual Review for screenshots (automatic flagging)

### P3 — Long-term
- Refactor ProfitTrackerPage.jsx (~4300 lines) and admin_routes.py (~4700 lines)
- Performance optimization (caching, pagination)

## Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`

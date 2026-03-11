# CrossCurrent Hub — Product Requirements Document

## Original Problem Statement
Build a comprehensive financial tracking and community platform for CrossCurrent's trading community. The platform manages trade profit tracking, commission calculations, member management, and community engagement.

## Core Architecture
- **Frontend:** React 19 + Tailwind CSS + ShadcnUI
- **Backend:** FastAPI (Python) + APScheduler
- **Database:** MongoDB
- **AI:** OpenRouter API (gpt-4o-mini)
- **File Storage:** Publitio

## What's Been Implemented

### Foundation Features (Complete)
- User auth (JWT), Dashboard, Profit Tracker, Trade Monitor, Admin panel
- Notifications (WebSocket), Forum, Family accounts, Licensee management
- Rewards, Referral system, Quiz system, Habit tracker

### UI Refresh & AI Assistant (Complete)
- Premium Dark Theme, AI Knowledge Assistant, Forum Enhancement, Rewards Polish

### Onboarding & Invite System (Complete)
- 7-Step Onboarding Gate, Merin Referral Code, Affiliate Center, Login Redesign

### P0 Bug Fixes (2026-03-11)
- Profit Tracker crash, Streak sync, Referral tree, Member count mismatch

### P1 Features (2026-03-11)
- Auto Streak Sync (mid-day + end-of-day CronTrigger)
- Referral Tree Readability (off-white background on both Tree + Visual views)
- Suspended Members Isolation (new stat cards, excluded from default list)
- Forum Solved Tab (Open/Solved/All tabs, default Open, search across all)

### P2 Features — Habits Overhaul Phase 1 (2026-03-11)
- Day-of-week habits (admin configurable, `day_of_week` field)
- Screenshot proof required (`requires_screenshot` enforced backend + frontend upload UI)

### P2 Features — Fraud Warning System (2026-03-11)
- Admin rejects habit proof → creates `fraud_warning` in DB
- Member sees `FraudWarningPopup` on next page load
- Member acknowledges → 7-day countdown starts
- Weekly scheduler (Sunday 23:00 UTC) checks expired countdowns → auto-suspend if new rejections
- `fraud_warnings` collection tracks: user_id, fraud_count, acknowledged, countdown_end, resolution

### P2 Features — Team System (2026-03-11)
- `GET /api/referrals/my-team` — team leader views their referred members
- Activity data: recent trades, habits today, last trade date, fraud warnings
- Status classification: active, inactive, danger, suspended
- Stats: total, active, in_danger, new_this_week
- Frontend `TeamPage.jsx` with stat cards and member list, sidebar link "My Team"

### P2 Features — Smart Registration Security (2026-03-11)
- Auto-flag on registration: same email domain as suspended, same inviter as suspended, similar name
- `registration_flagged`, `registration_flags`, `registration_approved` fields on user document
- Admin notification on flagged registrations
- `GET /api/admin/pending-registrations` — admin review queue
- `POST /api/admin/approve-registration/{id}` and `reject-registration/{id}`

### P2 Features — Admin Cleanup Page (2026-03-11)
- `GET /api/admin/cleanup-overview` — one-stop hub returning all admin review metrics
- Frontend `AdminCleanupPage.jsx` with 5 stat cards + expandable sections
- Sections: Pending Proofs, Fraud Warnings, In Danger Members, Auto-Suspended, Pending Registrations
- Approve/Reject actions for flagged registrations

## Prioritized Backlog

### Remaining P2 Items
- **AI Forum Merging:** AI rewrites/blends merged content into Master Post, credits original submitter
- **Signal Gate Immunity Credits:** Purchasable credits from store to bypass gate
- **AI Visual Review:** Flag suspicious screenshots automatically (needs AI integration)

### P3 — Long-term
- AI for Debt Management
- Gamified Leaderboards
- Performance optimization (caching, pagination)
- Refactor ProfitTrackerPage.jsx (~4300 lines) and admin_routes.py (~4700 lines)

## Key Endpoints
- `GET /api/habits/my-warnings` — user's fraud warnings
- `POST /api/habits/acknowledge-warning/{id}` — acknowledge warning
- `GET /api/referrals/my-team` — team leader's team data
- `GET /api/admin/pending-registrations` — flagged signups
- `GET /api/admin/cleanup-overview` — admin cleanup hub
- `GET /api/admin/members/stats/overview` — member stat cards

## Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`

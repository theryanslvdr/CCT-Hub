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
- User authentication (JWT), Dashboard, Profit Tracker, Trade Monitor, Admin panel
- Notifications (WebSocket + in-app), Forum, Family accounts, Licensee management
- Rewards & leaderboard, Referral system, Quiz system, Habit tracker

### UI Refresh & AI Assistant (Complete)
- Premium Dark Theme, AI Knowledge Assistant, Forum Enhancement, Rewards Polish

### Onboarding & Invite System (Complete)
- 7-Step Onboarding Gate, Merin Referral Code, Affiliate Center, Login Redesign, ErrorBoundary

### P0 Bug Fixes (2026-03-11)
- Profit Tracker crash (OnboardingData model mismatch)
- Streak sync (wrong field names in rewards.py)
- Referral tree (merin_referral_code mapping)
- Member count (use response.total)

### P1 Features (2026-03-11)
- **Auto Streak Sync:** Mid-day (12:00 UTC) + end-of-day (23:30 UTC) CronTrigger jobs
- **Referral Tree Readability:** Off-white background (#f5f5f0) with dark text on both Tree and Visual views
- **Suspended Members Isolation:** Excluded from default list, new stat cards (Active, Team Leaders, Suspended, In Danger), new `/admin/members/stats/overview` endpoint
- **Admin Referral Edit:** Verified admin can edit Merin code and inviter
- **Forum Solved Tab:** Open/Solved/All tabs using ShadcnUI Tabs, default to Open, search across all statuses

### P2 Features — Habits Overhaul Phase 1 (2026-03-11)
- **Day-of-Week Habits:** Admin can set habits for specific days (e.g., Monday Story Day). `day_of_week` field on habit model. User-facing endpoint filters habits to only show today's.
- **Screenshot Proof Required:** `requires_screenshot` field on habits. Backend returns 400 if screenshot missing. Frontend shows file upload UI.
- **Admin Habit Management:** Updated HabitManagerCard with day selector dropdown and screenshot toggle. Badges show day-of-week and screenshot status.

## Prioritized Backlog

### P2 — In Progress: Habits Overhaul Phase 2
- Admin spot checks on random completions (endpoints exist, need UI polish)
- Fraudulent screenshot flow: warning popup, member acknowledgment, countdown timer, auto-suspend if behavior continues
- Signal Gate Immunity Credits (purchasable from store)
- AI visual review for suspicious screenshots (needs AI integration)

### P2 — Team System
- Inviters = Team Leaders (auto from referral tree)
- Team pages: members, activity, balances (leader-only view)
- Invite Pipeline: track each member's invites, flag leeches
- AI recommendations with "In Danger" status
- Team stats dashboard

### P2 — Smart Registration Security
- Auto-flag suspicious registrations (same email domain as suspended, similar names, matching codes)
- Admin approval queue for flagged registrations
- Notification to admin on triggers

### P2 — AI Forum Merging
- AI rewrites/blends merged content into Master Post
- Credits original submitter, merged post removed from main list

### P2 — Admin Cleanup Page
- Central review page for: flagged screenshots, danger status members, auto-suspended members, pending registration approvals

## Key Database Collections
- `users`, `trade_logs`, `signals`, `forum_posts`, `habits`, `habit_completions`
- `quizzes`, `rewards`, `rewards_stats` (current_streak_days, best_streak_days)
- `ai_assistants`, `ai_sessions`, `ai_messages`, `ai_knowledge`
- `onboarding_checklists`, `platform_settings`

## Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`

## Tech Stack
React 19, FastAPI, MongoDB, Tailwind CSS, ShadcnUI, OpenRouter API, APScheduler, react-d3-tree

# CrossCurrent Hub — Product Requirements Document

## Original Problem Statement
Build a comprehensive financial tracking and community platform for CrossCurrent's trading community. The platform manages trade profit tracking, commission calculations, member management, and community engagement.

## Core Architecture
- **Frontend:** React 19 + Tailwind CSS + ShadcnUI
- **Backend:** FastAPI (Python) 
- **Database:** MongoDB
- **AI:** OpenRouter API (gpt-4o-mini)
- **File Storage:** Publitio

## What's Been Implemented

### Phase: Foundation Features (Complete)
- User authentication (JWT-based)
- Dashboard with profit tracking, KPIs, performance charts
- Profit Tracker with detailed trade logging
- Trade Monitor with live signals
- Admin panel (Members, Signals, Analytics, Transactions)
- Notification system (WebSocket + in-app)
- Forum with posts, replies, upvotes
- Family accounts system
- Licensee management
- Rewards & leaderboard system
- Referral system with admin tree visualization

### Phase: Community & Growth (Complete)
- Quiz system (AI-generated, admin-managed, user-facing)
- Habit tracker with proof-of-completion
- Markdown rendering for AI content
- Quiz editing with AI verification
- Bonus points for correct quiz answers
- New badges for habit/quiz achievements

### Phase: UI Refresh & AI Assistant (2026-03-10)
- Premium Dark Theme Redesign (COMPLETE)
- AI Knowledge Assistant (COMPLETE)
- Forum Enhancement (COMPLETE)
- Habit Tracker Enhancement (COMPLETE)
- Rewards Page Polish (COMPLETE)
- Dark Theme Refinements (COMPLETE)

### Onboarding & Invite System (COMPLETE)
- 7-Step Onboarding Gate
- Merin Referral Code
- Cross-Platform API
- Admin Gate Toggle
- Referral Tracking Page
- Referral Milestone Rewards
- Referral Leaderboard
- Admin Stats

### Black Screen Bug Fix & Affiliate Center (COMPLETE)
- Error Boundary added
- InviterModal fixed
- Affiliate Center with invite link, member lookup
- Admin Inviter Management
- Login Page Redesign

### P0 Bug Fixes (2026-03-11)
- **Profit Tracker "New Trader" crash (FIXED):** OnboardingData Pydantic model updated to accept frontend fields (user_type, start_date, trade_entries, total_commission) with proper optional defaults. Was returning 422 due to field name mismatch.
- **Streak not syncing to Rewards (FIXED):** rewards.py summary endpoint was reading `current_streak` and `best_streak` but DB stores them as `current_streak_days` and `best_streak_days`. Fixed to read correct field names with fallback.
- **Referral tree not populating (FIXED):** Tree-building code now maps both `referral_code` and `merin_referral_code` to users, and also resolves `referred_by_user_id` for direct ID lookups. Referral counting in tracking/my-code endpoints also updated.
- **Member count discrepancy (FIXED):** Admin Dashboard was counting `members.length` (capped at page limit=20) instead of using `response.total`. Fixed to use `membersRes.data.total`.
- Tested: iteration 182 — 100% pass (13/13 backend, all frontend).

## Prioritized Backlog

### P1 — Upcoming Tasks
- **Verify/Confirm Admin Editing:** Confirm master admin can edit member's Merin referral code and inviter
- **Isolate Suspended Members:** Replace Admins card with Suspended card, add Suspended tab, exclude from active count
- **Separate Solved Forum Posts:** New 'Solved' tab, move solved posts there, keep searchable

### P2 — Future Features
- **Habits Overhaul:** Day-of-week habits (Mon Story Day, etc.) admin-configurable, screenshot proof required, AI visual review, admin spot checks, fraudulent screenshot flow with warnings/suspension, Signal Gate Immunity Credits
- **Team System:** Inviters = Team Leaders (auto from referral tree), team pages with members/activity/balances, invite pipeline, AI recommendations with "In Danger" status, team stats dashboard
- **Smart Registration Security:** Auto-flag suspicious registrations (same email domain as suspended, similar names, matching codes), admin approval queue, notifications
- **AI Forum Merging:** AI rewrites/blends merged content into Master Post, credits original submitter
- **Admin Cleanup Page:** Central review page for flagged screenshots, danger status members, auto-suspended members, pending registration approvals

### P3 — Long-term
- AI for Debt Management
- Gamified Leaderboards
- Performance optimization (caching, pagination)
- Refactor ProfitTrackerPage.jsx (~4300 lines) and admin_routes.py (~4500 lines)

## Key Database Collections
- `users`, `trade_logs`, `signals`, `forum_posts`, `habits`, `quizzes`, `rewards`
- `ai_assistants`, `ai_sessions`, `ai_messages`, `ai_knowledge`, `ai_unanswered`, `ai_interactions`
- `onboarding_checklists`, `platform_settings`
- `rewards_stats` (stores `current_streak_days`, `best_streak_days`)

## Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`
- API: OpenRouter key in `backend/.env`

## Tech Stack
React 19, FastAPI, MongoDB, Tailwind CSS, ShadcnUI, OpenRouter API, react-d3-tree, react-markdown, @tailwindcss/typography

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

### Foundation Features (Complete)
- User authentication (JWT-based), Dashboard, Profit Tracker, Trade Monitor
- Admin panel (Members, Signals, Analytics, Transactions)
- Notification system (WebSocket + in-app), Forum, Family accounts, Licensee management
- Rewards & leaderboard, Referral system with admin tree, Quiz system, Habit tracker

### UI Refresh & AI Assistant (Complete)
- Premium Dark Theme, AI Knowledge Assistant, Forum Enhancement, Rewards Polish

### Onboarding & Invite System (Complete)
- 7-Step Onboarding Gate, Merin Referral Code, Affiliate Center, Login Redesign

### P0 Bug Fixes (2026-03-11)
- **Profit Tracker crash:** Fixed OnboardingData model field mismatches
- **Streak sync:** Fixed rewards.py reading wrong field names (current_streak_days/best_streak_days)
- **Referral tree not populating:** Fixed tree mapping to include both referral_code and merin_referral_code
- **Member count mismatch:** Fixed AdminDashboard to use response.total

### P1 Features — Session 2 (2026-03-11)
- **Auto Streak Sync:** Added mid-day (12:00 UTC) and end-of-day (23:30 UTC) scheduled sync jobs
- **Referral Tree Readability:** Changed tree background to off-white (#f5f5f0) with dark text for readability
- **Suspended Members Isolation:**
  - Suspended users excluded from default member list
  - New stat cards: Total Active Members (incl. Team Leaders), Team Leaders, Suspended Users, In Danger
  - New endpoint: GET /api/admin/members/stats/overview
  - In Danger = active members with trades but none in 7+ days

## Prioritized Backlog

### P1 — Remaining Tasks
- **Verify/Confirm Admin Editing:** Confirm master admin can edit member's Merin referral code and inviter
- **Separate Solved Forum Posts:** New 'Solved' tab, move solved posts there, keep searchable

### P2 — Future Features
- **Habits Overhaul:** Day-of-week habits (Mon Story Day, etc.) admin-configurable, screenshot proof required, AI visual review, admin spot checks, fraudulent screenshot flow with warnings/suspension, Signal Gate Immunity Credits
- **Team System:** Inviters = Team Leaders (auto from referral tree), team pages with members/activity/balances, invite pipeline, AI recommendations with "In Danger" status, team stats dashboard
- **Smart Registration Security:** Auto-flag suspicious registrations, admin approval queue, notifications
- **AI Forum Merging:** AI rewrites/blends merged content into Master Post, credits original submitter
- **Admin Cleanup Page:** Central review page for flagged screenshots, danger status members, auto-suspended members, pending registration approvals

## Key Database Collections
- `users`, `trade_logs`, `signals`, `forum_posts`, `habits`, `quizzes`, `rewards`
- `ai_assistants`, `ai_sessions`, `ai_messages`, `ai_knowledge`, `ai_unanswered`, `ai_interactions`
- `onboarding_checklists`, `platform_settings`, `rewards_stats`

## Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`

## Tech Stack
React 19, FastAPI, MongoDB, Tailwind CSS, ShadcnUI, OpenRouter API, react-d3-tree, react-markdown

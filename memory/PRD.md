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
- **Premium Dark Theme Redesign (COMPLETE):**
  - Upgraded from basic color swap to full premium fintech aesthetic
  - Global component overhaul: Card, Dialog, Input, Tabs, Badge shadcn components updated with dark gradient bases
  - CSS utilities: glass-card, glass-card-elevated, kpi-card (with accent variants), star-bg, btn-primary, btn-secondary, input-dark
  - Login: Particle star background (#050505), premium glass-morphic card with ambient glow
  - Dashboard: KPI cards with colored left accent glow bars, 3xl stat numbers, icon glow effects
  - Sidebar: Gradient background (#0c0c0c → #080808), refined section labels, orange glow active states
  - Header: Transparent bg with 20px backdrop blur
  - Admin Dashboard: Premium StatCard + QuickAction components
  - Forum: Refined post cards with gradient backgrounds, pill category filters
  - AI Assistant: Premium sidebar/chat backgrounds
  - Main background: #070707 (nearly black) for depth
  - All dialogs: Dark gradient backgrounds with premium shadow
  - Borders: Switched from white/[0.08] to subtle white/[0.04]-[0.06]
  
- **AI Knowledge Assistant (COMPLETE):**
  - Two AI personalities: RyAI (Technical/Safeguard) and zxAI (Knowledge/Encouragement)
  - Multi-turn conversation with session persistence
  - Admin-trainable knowledge base
  - Active learning from interactions
  - Escalation system: AI flags questions it can't answer for admin review
  - Admin answers are automatically added to knowledge base
  - Admin config: personality, system prompt, greeting, model selection
  - Analytics dashboard: sessions, messages, escalation rate
  - Backend: `/api/ai-assistant/*` routes
  - Frontend: `/ai-assistant` (user), `/admin/ai-training` (admin)

- **Forum Enhancement (COMPLETE):**
  - Community info sidebar with gradient banner, stats, Top Contributors
  - Category pills (All, General, Trading, Technical, Announcements)
  - Posts + sidebar layout for desktop

- **Habit Tracker Enhancement (COMPLETE):**
  - Streak badges with gradient glow effects
  - Current Streak, Best Streak, Total Days cards

- **Rewards Page Polish (COMPLETE):**
  - Points Balance, Level, Rank cards with gradient icons and glow
  - Level progress bar with points-to-next-level
  - Streak & Activity Stats grid (4 items)

- **Dark Theme Refinements (COMPLETE):**
  - All zinc backgrounds → true dark (#0a0a0a, #111111, #1a1a1a)
  - Chart grid strokes refined (subtle rgba)
  - Chart tooltips updated (dark glass-morphism)
  - Notification panel with date grouping

## Prioritized Backlog

### P0 — Core Changes (2026-03-10, Session 2)
- **Fix Persistent Popup (DONE):** PromotionPopup CTA now closes dialog before navigating (uses react-router for internal URLs)
- **Onboarding Tour Persistence (DONE):** Tour completion saved to backend DB via /api/users/complete-tour, checked on load via /api/users/tour-status
- **Adaptive AI Assistant (DONE):** Merged RyAI/zxAI into single unified chat. Backend auto-detects intent and routes to correct persona (technical → RyAI, encouragement → zxAI). Persona indicated per message.
- **Admin Sidebar Simplified (DONE):** Replaced accordion with single "Admin Dashboard" button. AdminDashboardPage reorganized into 4 categories: Management, Analytics & Tools, AI & Platform, System.
- **Admin Toggle for Adaptive AI (DONE — 2026-03-10, Session 3):** Added `adaptive_ai_enabled` setting to platform_settings. Toggle in Admin Settings > Security tab. When disabled, all chat requests fall back to RyAI (no adaptive persona routing). Tested: iteration_169 — 100% pass.

### Bug Fixes (2026-03-10, Session 3)
- **Family Member Projections Fix (DONE):** Fixed broken import `from server import get_quarter` → `from utils.trading_days import get_quarter` in family.py. FA Licensee family projections now load correctly.
- **Daily Projection Table Fix (DONE):** Added missing `get_quarter` import to profit_routes.py and admin_routes.py. Licensee daily projection endpoint no longer crashes with NameError. Also fixed undefined `get_first_trading_day_of_quarter` function.
- **Dashboard Licensee Label Fix (DONE):** Changed "Actual vs Projected / Below target" to "Account Growth / +X% since inception" for licensees in DashboardPage.jsx. No more misleading "Below target" label.
- **AI Training Model Dropdown (DONE):** Dynamic model selector pulling 346+ models from OpenRouter API with searchable dropdown. Backend endpoint: `/api/ai-assistant/models` (1h cache).
- **Habits Pagination (DONE):** Added pagination (10 items/page) with prev/next and page number buttons to HabitManagerCard.jsx.
- **Anomaly Detection Streak Fix (DONE):** Created shared `utils/streak.py` utility. Anomaly check, trade journal, and trade coach now compute streak from trade_logs instead of non-existent `users.streak` field.
- **AI Trade Journal Truncation Fix (DONE):** Increased `max_tokens` from 350 to 800 in ai_service.py. Journals now complete fully.
- **Timezone DST Fix (DONE):** Replaced hardcoded timezone offsets with dynamic `Intl.DateTimeFormat` API in TradeMonitorPage.jsx. Now correctly handles DST transitions.
- **Notification Consolidation (DONE):** Rewrote NotificationPanel with Unread/Read/All tabs, type-based consolidation (e.g., "Member1, Member2 and 32 more submitted trades"), and action buttons per notification type.
- Tested: iterations 170-173.

### Onboarding & Invite System (2026-03-10, Session 4)
- **7-Step Onboarding Gate (DONE):** New `/api/onboarding/*` routes. Blocks platform access until all steps complete (Heartbeat, Merin, Hub, Exchange, Tutorials, Live Trade, Rewards). Admin always bypasses.
- **Merin Referral Code (DONE):** Members store their Merin code in profile. Invite link auto-generates: `https://www.meringlobaltrading.com/#/pages/login/regist?code={CODE}&lang=en_US`
- **Cross-Platform API (DONE):** Public endpoints for external onboarding site: `GET /api/onboarding/status/{user_id}`, `POST /api/onboarding/complete-step-external`
- **Admin Gate Toggle (DONE):** `onboarding_gate_enabled` setting in Admin Settings > Security tab.

### Referral Tracking & Milestone Rewards (2026-03-10, Session 4)
- **Referral Tracking Page (DONE):** New `/referral-tracking` page ("Invite & Earn") with invite link, stats, milestones, leaderboard, and referral list.
- **Referral Milestone Rewards (DONE):** Points awarded at 3 (100pts), 5 (200pts), 10 (500pts), 25 (1000pts), 50 (2500pts) referrals. New badges: `referral_25` (Network Builder), `referral_50` (Community Architect).
- **Referral Leaderboard (DONE):** Ranked by referral count with badge display.
- **Admin Stats (DONE):** `/api/referrals/admin/stats` returns total_members, code_adoption_rate, referral_rate, top_referrers.
- Tested: iteration 174 — 100% pass.

### P1 — Feature Enhancements (ALL COMPLETE — iteration_165)
- Share Trade Card: Dashboard "Share" button → opens rich card dialog with copy/download (DONE)
- Daily Profit Summary: AI-consolidated notification on dashboard for today's trades (DONE)
- Admin Dashboard: Dedicated admin home page with stats (DONE — previous session)
- Public Member Profile: View any member's profile from Admin Members page or /member/:id (DONE)
- Transaction Stepper: Step-progress indicators in deposit/withdrawal dialogs (DONE)
- AI Smart Prompts: Popular questions shown in AI Assistant from active learning data (DONE)

### P2 — Upcoming
- Smoother onboarding (pre-fill referral from website) — Partially done via onboarding gate system
- External onboarding wizard site (prompt provided to user for separate Emergent deployment)

### Invite Someone Feature (2026-03-10, Session 5)
- **Onboarding Invite Link (DONE):** Backend returns `onboarding_invite_link` (`https://crosscur.rent/onboarding?merin_code={CODE}`) in `/api/referrals/tracking`. Default Merin code is `BDVMAF` when no code is provided on the onboarding site.
- **Affiliate Center Invite Card (DONE):** Prominent "Invite Someone" card at top of Affiliate Center page with copy-to-clipboard, view referral stats link, and direct Merin signup link.
- **Sidebar Profile Link (DONE):** "Affiliate Center" link added to profile dropdown in sidebar (both expanded and collapsed modes) for quick access.
- **Referral Tracking Update (DONE):** Updated Invite & Earn page to display the onboarding invite link instead of the direct Merin registration link, with direct Merin link shown below as secondary.
- **Member Lookup (DONE):** "Find a Member" card in Affiliate Center — search by name/email, results show name + masked email + Merin code with copy button. Backend: `GET /api/referrals/lookup-members?q={query}`. Only returns members who have a Merin code set.
- Tested: iterations 176-177 — 100% pass.

### P3 — Future Features
- AI for Debt Management
- Gamified Leaderboards
- Performance optimization (caching, pagination)
- Refactor ProfitTrackerPage.jsx (~4300 lines) and TradeMonitorPage.jsx (~2600 lines)

## Key Database Collections
- `users`, `trade_logs`, `signals`, `forum_posts`, `habits`, `quizzes`, `rewards`
- `ai_assistants` — AI bot configs (RyAI, zxAI)
- `ai_sessions` — Chat sessions per user
- `ai_messages` — Individual chat messages
- `ai_knowledge` — Admin-curated training data
- `ai_unanswered` — Escalated questions pending admin answer
- `ai_interactions` — Active learning interaction log
- `onboarding_checklists` — Per-user 7-step onboarding progress
- `platform_settings` — Admin toggles (adaptive_ai_enabled, onboarding_gate_enabled, etc.)

## Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`
- API: OpenRouter key in `backend/.env`

## Tech Stack
React 19, FastAPI, MongoDB, Tailwind CSS, ShadcnUI, OpenRouter API, react-d3-tree, react-markdown, @tailwindcss/typography

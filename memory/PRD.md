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
- **Daily Projection Table Fix (DONE):** Added missing `get_quarter` import to profit_routes.py helpers import. Licensee daily projection endpoint no longer crashes.
- **Dashboard Licensee Label Fix (DONE):** Changed "Actual vs Projected / Below target" to "Account Growth / +X% since inception" for licensees in DashboardPage.jsx. No more misleading "Below target" label.
- **AI Training Model Dropdown (DONE):** Replaced text input with Select dropdown for AI model selection in AITrainingPage.jsx. 10 model options (OpenAI, Anthropic, Google, Meta, Mistral).
- **Habits Pagination (DONE):** Added pagination (10 items/page) with prev/next and page number buttons to HabitManagerCard.jsx.
- Tested: iteration_170 — 100% pass (all 5 fixes verified).

### P1 — Feature Enhancements (ALL COMPLETE — iteration_165)
- Share Trade Card: Dashboard "Share" button → opens rich card dialog with copy/download (DONE)
- Daily Profit Summary: AI-consolidated notification on dashboard for today's trades (DONE)
- Admin Dashboard: Dedicated admin home page with stats (DONE — previous session)
- Public Member Profile: View any member's profile from Admin Members page or /member/:id (DONE)
- Transaction Stepper: Step-progress indicators in deposit/withdrawal dialogs (DONE)
- AI Smart Prompts: Popular questions shown in AI Assistant from active learning data (DONE)

### P2 — Upcoming
- Smoother onboarding (pre-fill referral from website)

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

## Credentials
- Master Admin: `iam@ryansalvador.com` / `admin123`
- API: OpenRouter key in `backend/.env`

## Tech Stack
React 19, FastAPI, MongoDB, Tailwind CSS, ShadcnUI, OpenRouter API, react-d3-tree, react-markdown, @tailwindcss/typography

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

### Phase: UI Refresh & AI Assistant (In Progress — 2026-03-10)
- **Orange Theme Migration (COMPLETE):**
  - Changed primary color from blue (#3B82F6) to orange (#F97316) across entire app
  - Updated 63+ JSX/JS files, CSS variables, utility classes
  - Login page redesigned: glass-morphism card, dot-pattern background, orange CTA
  - Sidebar: orange active states, amber gradient avatars
  - Mobile bottom nav: orange accents
  - All modals, buttons, form inputs updated to orange theme
  
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

## Prioritized Backlog

### P0 — Remaining UI Refresh Phases
- Phase 2: Profit Tracker & Financial Modals (stat cards, deposit/withdrawal modals, share trade card)
- Phase 3: Trade Monitor & Notifications (dense stats table, signal cards, notification panel)
- Phase 4: Admin Dashboard Overhaul (separate admin dashboard, analytics, member detail modal, settings)
- Phase 5: Community & Growth UI (forum refresh, habit tracker progress, quiz polish)
- Phase 6: Profiles & Polish (public member profile, licensee dashboard, final responsive pass)

### P1 — Feature Enhancements
- Share Trade/Projection as rich shareable card
- AI-consolidated profit notifications  
- Separate Admin Dashboard home page
- Public member profile view
- Step-progress indicators for deposits/withdrawals
- Smart prompt suggestions on AI Assistant (learn from popular user questions via active learning data)

### P2 — Future Features
- AI for Debt Management
- Smoother onboarding (pre-fill referral from website)
- Performance optimization (caching, pagination)

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

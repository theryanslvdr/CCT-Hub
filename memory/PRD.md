# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
A financial tracking platform for the CrossCurrent trading community. Supports admin-managed honorary licensees, extended licensees, family accounts, and direct traders. Key feature: dynamic account value calculation for honorary licensees based on master admin trading performance.

## Core Architecture
- **Frontend:** React (Vite) with Shadcn/UI, TailwindCSS
- **Backend:** FastAPI with Motor (async MongoDB)
- **Database:** MongoDB

## User Roles
- **Master Admin** (iam@ryansalvador.com): Full control, manages all members/licensees. Has access to ALL features including System Check, Platform Settings, API Center, and Licenses.
- **Super Admin**: Full admin capabilities EXCEPT System Check, Platform Settings, API Center, and Licenses. Can see Members, Trading Signals, Team Analytics, Transactions, and Rewards Admin.
- **Basic Admin**: Basic admin capabilities (Members, Trading Signals, Team Analytics only)
- **Member**: Regular trader with profit tracking
- **Licensee (Honorary/Honorary FA/Extended)**: Managed accounts whose value grows based on master admin trades

## Core Financial Formula
```
Quarterly Fixed Daily Profit = truncate_lot_size(Account Value at Quarter Start) * 15
LOT Size = math.trunc(Account Value / 980 * 100) / 100  (truncation, NOT rounding)
```
- LOT size uses truncation (floor to 2 decimals) to match frontend behavior
- Daily profit is FIXED for the entire calendar quarter
- Recalculated at each new quarter start using the accumulated account value
- Trading days = weekdays excluding US market holidays (~250/year)

## What's Been Implemented

### Core Features (Complete)
- User authentication with JWT tokens
- Admin dashboard with member management
- Trade logging and profit tracking
- Deposit/Withdrawal management
- License management, Maintenance mode, BVE mode
- Password reset (admin-initiated + user-initiated "Forgot Password")

### Growth Projection System (Complete - Updated Feb 24, 2026)
- Year Projections: 1, 2, 3, 5 year with quarterly compounding
- **DUAL PROJECTION VIEW (Option C - Feb 24, 2026):**
  1. **License Year End**: Balance at end of license Year 1/2/3/5 from `effective_start_date` using `starting_amount`
  2. **Forward Projections**: Balance after 1/2/3/5 years from TODAY using current `account_value`
- Daily Projections: past (actual trades) + future (projected)
- Holiday-aware (US market holidays excluded)
- Trading days utility: `/app/backend/utils/trading_days.py`
- **Quarterly Compounding Fix**: Frontend `generateMonthlyProjection` now uses fixed daily profit per quarter (not daily recalculation)

### Family Account System (Complete)
- Family members (up to 5) for Honorary FA licensees
- Admin can add/edit/remove family members via admin endpoints
- Dashboard combined account overview

### Rewards & Points System (Complete - Feb 23, 2026)

**Points System:**
- Single currency: POINTS (100 pts = 1 USDT)
- Continuous base points: signup(25), first_trade(25), deposit(50/50 USDT pro-rated), withdrawal(5/15 USDT), referral(150), streaks, milestones
- Seasonal promotions: multiplier-based PromotionRule (DB-managed)
- Level system: Newbie -> Trader -> Investor -> Connector -> Trade Novice -> Amateur -> Seasoned -> Pro -> Elite

**Stable API Endpoints (DO NOT change URLs or field names):**
1. `GET /api/rewards/summary?user_id={ID}` — Public, returns lifetime_points, monthly_points, level, estimated_usdt, min_redeem_points, is_redeemable
2. `GET /api/rewards/leaderboard?user_id={ID}` — Public, returns current_rank, distance_to_next, next_user_name, suggested_message
3. `POST /api/rewards/redeem` — Protected (X-INTERNAL-API-KEY), deducts points
4. `POST /api/rewards/credit` — Protected (X-INTERNAL-API-KEY), adds points

**Event Hooks (all protected with X-INTERNAL-API-KEY):**
- `POST /api/rewards/events/trade` — Process trade, streaks, milestones
- `POST /api/rewards/events/deposit` — Process deposit points
- `POST /api/rewards/events/withdrawal` — Process withdrawal points
- `POST /api/rewards/events/signup` — Sign-up & verify (25 pts)
- `POST /api/rewards/events/referral-qualified` — Qualified referral (150 pts)
- `POST /api/rewards/events/community` — Community actions (join, daily win, help chat)

**Admin System Check:**
- `POST /api/rewards/system-check` — Admin JWT auth, runs 10-step health check
- Frontend page at `/admin/system-check` with one-click validation

**Frontend:**
- Prominent Rewards card on main dashboard (points, USDT, level, monthly rank, CTA)
- Dedicated `/my-rewards` page with full points view, level badge, rank, and history table
- "Open Rewards & Store" CTA → `https://rewards.crosscur.rent/?user_id={USER_ID}`
- "My Rewards" sidebar link for all members
- System Check admin page in sidebar

**Admin Rewards Tools (Feb 23, 2026):**
- `/admin/rewards` page with User Rewards Lookup (search by email/user_id)
- Simulate Points tool: test_trade, test_deposit, test_referral, manual_bonus
- Full points history table for looked-up user
- All simulated actions tagged as "Admin Test" in history
- "Rewards Admin" sidebar link for admins

**New API Endpoints:**
- `GET /api/rewards/history` — JWT auth, returns points transaction log (members see own, admins see any)
- `GET /api/rewards/admin/lookup` — Admin JWT, search by email/user_id, returns full profile + history
- `POST /api/rewards/admin/simulate` — Admin JWT, simulate test_trade/deposit/referral/manual_bonus

**Configuration:**
- `REWARDS_INTERNAL_API_KEY` in backend .env
- Seeded promotion rules: 1 continuous (base), 1 seasonal (March 2026 2x multiplier)

**Collections:** rewards_stats, rewards_leaderboard, rewards_promotions, rewards_redemptions, rewards_point_logs

## Mocked Features
- Cloudinary file upload, Chatbase integration

### Regression Tests (Feb 23, 2026)
- **Created:** `/app/backend/tests/test_projection_regression.py` (21 tests)
  - 10 unit tests for trading_days.py (holidays, trading day checks, quarterly growth)
  - 3 unit tests for calculations.py (lot size, projected profit, performance)
  - 8 API integration tests (year projections, daily projections, summary consistency, admin access)
- **Purpose:** Prevent recurring honorary licensee projection breakage (has broken 4+ times)
- **Status:** All 21 tests PASSING
- **One-click repair:** `POST /api/admin/licensee-health-check` — validates all licensees, auto-fixes missing start dates

### Rewards Full List Dialog + Permission Changes (Feb 25, 2026) - COMPLETE
**Rewards Full List Dialog:**
- "See Full List" link on top-right of Badges & Achievements card
- Opens dialog with 11 earning actions table (Action, Category, Points, USDT Value)
- Achievement Badges section with 14 badges showing earned/locked status
- "1 Point = $0.01 USDT" conversion note

**Super Admin Permission Restriction:**
- Super admin sees: Members, Trading Signals, Team Analytics, Transactions, Rewards Admin
- Super admin does NOT see: System Check, Platform Settings, API Center, Licenses
- Master admin retains full access to all features
- **Test Status:** 100% passed (iteration_132)

### Rewards Platform User Sync (Feb 25, 2026) - COMPLETE
**Admin Batch Sync:**
- "Sync All Users" button in Platform Settings > Diagnostics
- Pushes all hub users to `rewards.crosscur.rent` via external API (POST /external/users)
- Sync status dashboard: Hub Users, Synced, Rewards Platform count, Last Sync timestamp

**Auto-Sync Hooks:**
- New user registration → auto-pushed to rewards platform
- Password change → synced to rewards platform  
- Profile update → synced to rewards platform

**JWT SSO Auto-Login (VERIFIED WORKING):**
- Hub generates JWT → redirects to `rewards.crosscur.rent/login?token=xxx`
- Rewards platform verifies JWT via `POST /api/auth/sso` using `HUB_JWT_SECRET`
- Auto-creates/matches user, sets admin flags, logs in, redirects to dashboard
- Confirmed: Ryan Salvador auto-logged in as Super Admin on rewards platform
- **Test Status:** 100% passed (iteration_131 + manual SSO verification)

### Badge Toasts, Email Reset, Rewards Store API (Feb 25, 2026) - COMPLETE

### Bug Fixes & Enhancements (Mar 3, 2026) - COMPLETE

### Streak Freeze Feature (Mar 3, 2026) - COMPLETE

### Retroactive Badge Awards & Bug Fixes (Mar 3, 2026) - COMPLETE

### Earning Actions System (Mar 3, 2026) - COMPLETE
**Earning Actions with Retroactive Point Awards:**
- `GET /api/rewards/earning-actions` — returns status of all 8 earning actions per user (awarded, claimable, one-time, category)
- `POST /api/rewards/claim/{action_id}` — manual claim endpoint (only for `join_community`)
- Retroactive scan now also awards missed points: signup_verify (on first trade), first_trade, first_daily_win, streak_5_day (per 5 days), milestone_10_trade, deposits, referrals
- Double-claim prevention: already-claimed actions return 400 error
- Non-claimable actions (first_trade, etc.) return 400 if manually claimed

**Actions:**
| Action | Points | Auto/Manual | One-time |
|--------|--------|------------|----------|
| Sign Up & Verify | 25 | Auto (on first trade) | Yes |
| Join Community | 5 | Manual (Claim button) | Yes |
| First Trade | 25 | Auto | Yes |
| First Daily Win | 10 | Auto (profitable trade) | Yes |
| 5-Day Streak | 50 | Auto (repeatable) | No |
| 10 Trades Milestone | 125 | Auto | Yes |
| Qualified Referral | 150 | Auto (per referral) | No |
| Deposit Bonus | 50/$50 | Auto | No |
| Help Chat | ON HOLD | Future community forum | - |

**Frontend:**
- EarningActionsSection component on My Rewards page
- Progress bar (X/8 completed), unclaimed at top with Claim button, completed below with Done badge
- Repeatable actions show "xN" count
- **Test Status:** 100% passed (iteration_136, 7/7 backend + frontend)
**Retroactive Badge System:**
- `POST /api/rewards/retroactive-scan` — scans user's actual hub records (trades, streaks, deposits, referrals) and awards earned badges
- `POST /api/rewards/retroactive-scan-all` — master admin endpoint to scan ALL users
- `_compute_real_stats()` utility computes: lifetime_trades, distinct_trade_days, best_streak_days, current_streak_days, lifetime_deposit_usdt, qualified_referrals
- Badge definitions expanded from 14 to 30: First Trade, Getting Started, Quarter Century, 50 Trades Club, Century Trader, Trading Veteran, Trading Legend, Streak Starter (3), Streak Master 7/14/30, Streak Champion (50), Streak Legend (100), Points Rookie (100), 500/1K/5K/10K milestones, First Referral, Referral Champion/Pro/Legend, First Deposit ($100), Deposit Hero ($500), High Roller ($1K), Whale ($5K), 10/30/50/100 Days Active
- BadgesSection auto-runs retroactive scan on mount to award all earned badges
- **Test Status:** 100% passed (iteration_135, 12/12 backend)

**Daily Projection Fix (Dec trades not showing):**
- Fixed `has_trade` in daily-balances: changed from `actual_profit is not None and actual_profit != 0` to `date_key in trades_by_date`
- Zero-profit trades (break-even) now correctly show as having a trade

**Trade History Streak Display:**
- Streak indicator always visible in Trade History header (not gated by streak > 0)
- Added "Day #" column to trade history table showing global trade day number for each trade
- Backend `get_trade_history` returns `trade_day_number` per trade and `total_trade_days` count
**Backend:**
- `GET /api/rewards/streak-freezes` — returns user's freeze inventory, costs, available points, usage history
- `POST /api/rewards/streak-freezes/purchase` — purchases streak freezes (trade=200pts, habit=150pts), validates balance, deducts points
- `use_streak_freeze()` / `check_freeze_for_date()` utility functions for automatic freeze consumption
- Trade streak calculation (`get_trade_streak`) updated to check for freezes on missed days
- Habit streak calculation (`_calc_habit_streak`) updated to check for freezes on missed days
- New MongoDB collections: `streak_freezes` (inventory), `streak_freeze_usage` (consumption log)

**Frontend:**
- StreakFreezeSection component on My Rewards page
- Two cards: Trade Streak Freeze (blue, 200pts) and Habit Streak Freeze (orange, 150pts)
- Quantity selector (1-10), Buy button with total cost, insufficient points warning
- Recent usage history display

**Rewards Platform Prompt:**
- Complete integration prompt created at `/app/prompts_for_rewards_platform_streak_freeze.md`
- Includes API specs, data models, UI guidelines, and testing instructions for the external Rewards Platform
- **Test Status:** 100% passed (iteration_134, 8/8 backend + frontend)

**Habit Proof Upload Fix:**
- Changed `POST /api/habits/{id}/complete` to accept `screenshot_url` in request body (HabitCompleteRequest model) instead of query parameter
- Fixes "Failed to complete task" error caused by base64 data URLs exceeding URL length limits
- Backend maintains backward compatibility (supports both body and query param)

**LOT Size Truncation Fix (Joy Sison's $0.30 bug):**
- Changed ALL backend lot_size calculations from `round(x/980, 2)` to `math.trunc(x/980*100)/100`
- Backend now uses truncation (floor) matching frontend `truncateTo2Decimals()` behavior
- Example: $16.13 / 980 = 0.01646... → truncated to 0.01 (was rounded to 0.02)
- Fixed in: `server.py` (truncate_lot_size helper + ~15 inline occurrences), `utils/calculations.py`

**Trade Monitor Target vs Projected Exit Consistency:**
- TARGET in Trade Control section now uses `exitValue` (frontend real-time calculation) instead of `dailySummary.total_projected` (backend stored value)
- Both Projected Exit card and TARGET now show the same value

**Streak Holiday Awareness Fix:**
- Streak calculation (`_calc_habit_streak`) now skips weekends and US market holidays
- Uses `get_holidays_for_range()` from `utils/trading_days.py`
- Presidents' Day (Feb 16, 2026) no longer breaks streaks

**Dashboard Account Value Hide/Reveal Toggle:**
- Eye icon toggle next to currency KPI cards (Account Value, Total Profit)
- When hidden: values show `****`, comparison metrics hidden
- Persists in `localStorage('hideAccountValues')`
- Icon switches between Eye (visible) and EyeOff (hidden)

**Super Admin Simulation Fix:**
- Master Admin's "Simulate View → Super Admin" now correctly shows admin sidebar items
- MobileMenu updated: added Rewards Admin, removed Platform Settings from super admin items
- Profile dropdown respects simulation role (hides Platform Settings, API Center, Licenses during super admin simulation)
- **Test Status:** 100% passed (iteration_133, 11/11 backend tests)
**Badge Notification Toasts:**
- `POST /api/rewards/badges/check` runs on MyRewardsPage load, returns newly_awarded list
- Celebratory toast shown for each newly earned badge during session
- **Test Status:** 100% passed (iteration_130)

**Email Password Reset (Emailit Integration):**
- `POST /api/auth/forgot-password` now sends email with reset link via Emailit (no longer returns token in response)
- Email template with branded design, reset button, 1-hour expiry warning
- Frontend: "Send Reset Link" flow with email sent confirmation, URL param `?reset_token=xxx` auto-opens dialog
- **Test Status:** 100% passed (iteration_130)

**Rewards Store API (Cross-Site Auth):**
- `POST /api/rewards/store-token` - Generates signed JWT (HS256, 10min expiry, aud=crosscurrent-store)
- `POST /api/rewards/store-verify?token=xxx` - Store calls this to verify user and get profile (requires internal API key)
- `POST /api/rewards/store-deduct?user_id=x&points=N` - Store calls this to deduct points on redemption
- Frontend: "Open Rewards & Store" button generates token and opens `rewards.crosscur.rent/store?token=xxx`
- **Test Status:** 100% passed (iteration_130)

### Rewards System Phase 3 & 4 (Feb 25, 2026) - COMPLETE
**Phase 3 - Badges & Achievements:**
- 14 default badge definitions: First Trade, Streak Master (7/14/30), Points Milestone (500/1K/5K/10K), Referral Champion (3/5/10), Deposit Hero, 50 Trades Club, Century Trader
- Stored in `rewards_badge_definitions` collection (admin customizable names/descriptions)
- Auto-awarded via `check_and_award_badges()` after trade/deposit/referral events
- Earned badges stored in `rewards_user_badges` collection
- Frontend: Badges & Achievements section on MyRewardsPage (earned with glow vs locked with lock icon)
- Endpoints: `GET /api/rewards/badges`, `GET /api/rewards/badges/user` (JWT), `POST /api/rewards/badges/check`
- **Test Status:** 100% passed (iteration_129)

**Phase 4 - Admin Tools Enhancement:**
- User search autocomplete: `GET /api/rewards/admin/search-users?q=name` with dropdown matches
- Manual point adjustment with audit trail: `POST /api/rewards/admin/adjust-points` (Credit/Deduct with reason)
- Transaction history with filters (All, Earned, Spent, Admin Actions) and pagination
- Badge Management tab: Edit names/descriptions, enable/disable badges (`PUT /api/rewards/admin/badges/{id}`)
- **Test Status:** 100% passed (iteration_129)

**Bug Fixes:**
- Rewards Store button now uses `email` parameter instead of `user_id` (external platform compatibility)
- User lookup replaced with name-based autocomplete dropdown search

### Rewards System Phase 1 & 2 Enhancements (Feb 25, 2026) - COMPLETE
**Phase 1 - Points History (MyRewardsPage):**
- Points Balance card with USDT estimate, Level card with progress bar
- Monthly Rank card with distance to next position
- Streak tracking (Current Streak, Best Streak)
- Points History table with Date, Type, Source, Points, Balance
- Time Period filters (All Time, 7 Days, 30 Days, 90 Days, Custom)
- Activity Type filters, CSV Export, Pagination
- **Test Status:** 100% passed (iteration_128)

**Phase 2 - Leaderboard (LeaderboardPage):**
- New page at `/leaderboard` with podium display for top 3
- Period toggle between Monthly and All Time
- Full rankings table with Rank, User, Level, Points, Change columns
- User rank card showing position and distance to next rank
- Sidebar link visible for all non-licensee members
- Backend endpoint: `GET /api/rewards/leaderboard/full?period=monthly|alltime&limit=N`
- **Test Status:** 100% passed (iteration_128)

**Bug Fix:** Added 'leaderboard' to sidebar `alwaysInclude` list so all members can see it (not just admins)

### Recurring Bug Mitigations (Feb 23-25, 2026)
- **ROOT CAUSE FOUND (FINAL)**: Multiple compounding issues:
  1. Case-sensitive `license_type` matching (all 20+ locations) — fixed with `_is_honorary()` helper
  2. **`get_member_details` endpoint** (used by admin simulation) had NO try/except around honorary calculation + no float() casts on MongoDB values → crashed silently, returned $0 profit
  3. MongoDB `Decimal128`/string type values not cast to `float` → arithmetic errors
  4. MongoDB regex queries case-sensitive → `$options: "i"` added
  5. **Year Projection Calculation Bug (Feb 24)**: Was calculating projections from current balance only, user expected to see License Year End values from effective start date
  6. **FRONTEND BACKEND URL MISMATCH (Feb 25)**: Production frontend was calling OLD backend URL (`finance-hub-452.emergent.host`) instead of production backend (`hub.crosscur.rent`). Fixed `REACT_APP_BACKEND_URL` to point to custom domain.
- **Fixes applied**:
  - `_is_honorary()` case-insensitive helper in `calculations.py` used in ALL locations
  - `get_member_details`: try/except around calculation with fallback, float() on ALL numeric fields
  - `get_user_financial_summary`: float() casts on all license values
  - `year-projections`: Now returns BOTH projection types (license_year_projections + projections)
  - Frontend quarterly compounding: `generateMonthlyProjection` fixed to use quarterly fixed daily profit
  - Frontend auto-retry (2x) + guard against simulation without selected member
  - Rewards card hidden for licensees
  - **One-click repair**: `POST /api/admin/licensee-health-check`
  - **Frontend BACKEND_URL**: Fixed to `https://hub.crosscur.rent`

### Admin Diagnostic & Sync Tool (Feb 25, 2026) - UPDATED
**Location:** Platform Settings → Diagnostics tab (Master Admin only)
**Purpose:** Comprehensive safeguard tool for master admin to diagnose and fix licensee calculation issues

**Features:**
1. **Sync Status Banner** - Shows last sync date and next recommended sync (every 7 days)
2. **Batch Sync All** - Recalculates ALL honorary licensees in one click
3. **Health Check** - Quick scan to identify licensees with calculation issues
4. **Individual Diagnostic** - Enter email to see step-by-step diagnostic for a specific licensee
5. **Force Sync** - Manually recalculate and update a single licensee's value

**Endpoints:**
- `GET /api/diagnostic/licensee/{email}` - Public diagnostic (no auth needed)
- `POST /api/admin/licensee/{user_id}/force-sync` - Force recalculation for one user
- `POST /api/admin/licensee/batch-sync-all` - Batch sync all licensees
- `POST /api/admin/licensee-health-check` - Run health check on all licensees

**Scheduling:**
- System tracks last sync date in localStorage
- Recommends sync every 7 days
- Shows warning banner when sync is overdue (red) or never done (amber)

### Year Projection Dual View (Feb 24, 2026)
**Bug Report:** Year 1 showed $44,943 instead of expected ~$12,414 
**Root Cause:** Projections only calculated from current balance, not from starting amount at effective start date
**Fix (Option C):** Show BOTH types of projections
- **Backend**: `/api/profit/licensee/year-projections` now returns:
  - `projections` array: Forward from TODAY's current_value
  - `license_year_projections` array: From effective_start_date using starting_amount
- **Frontend Dashboard**: Two rows in Growth Projections card
  - Cyan: License Year End (from start date)
  - Blue: Forward Projections (from today's balance)
- **Test file**: `/app/backend/tests/test_iteration_127_projection_fix.py`

## Prioritized Backlog

### P0 - Community Forum (COMPLETE - Mar 3, 2026)
**Backend (`/app/backend/routes/forum.py`):**
- `GET /api/forum/posts` — List posts with filters (status, tag, search), pagination
- `POST /api/forum/posts` — Create new post (title, content, tags)
- `GET /api/forum/posts/{id}` — Get post with all comments, increments views
- `POST /api/forum/posts/{id}/comments` — Add comment (blocked on closed posts)
- `PUT /api/forum/posts/{id}/best-answer/{comment_id}` — Mark best answer (OP or admin)
- `PUT /api/forum/posts/{id}/close` — Close post, award points (Best Answer: 50pts, Active Collaborators: 15pts each)
- `DELETE /api/forum/posts/{id}` — Delete post and comments (OP or admin)
- `GET /api/forum/stats` — Forum-wide stats and top contributors

**Frontend:**
- `ForumListPage.jsx` at `/forum` — Stats bar, search, filters (All/Open/Solved), top contributors, post cards with pagination
- `ForumPostPage.jsx` at `/forum/:postId` — Post thread, comments, reply box, mark best answer, close dialog with collaborator selection
- Sidebar & MobileMenu — "Community Forum" nav item with MessageSquare icon

**Collections:** `forum_posts`, `forum_comments`
**Points:** forum_best_answer (50pts), forum_active_collaborator (15pts)
**Test Status:** 100% passed (iteration_137, 15/15 backend + frontend)

### Forum Enhancements (Mar 3, 2026) - COMPLETE
**Upvote/Downvote System:**
- `POST /api/forum/comments/{id}/vote` — Cast vote (up/down), toggle off, or switch
- `GET /api/forum/comments/{id}/voters` — List voters with names (not anonymous)
- Votes stored in `forum_votes` collection with voter_name, comment_author_id
- Comments enriched with: upvotes, downvotes, score, up_voters, down_voters, my_vote
- Cannot vote on own comment (400 error)
- Frontend: ThumbsUp/ThumbsDown buttons, expandable voter list per comment

**Live Similar Posts Search (AJAX):**
- `GET /api/forum/search-similar?q=...` — Returns matching posts (3+ chars, word-based regex)
- Frontend: SimilarPostsSuggestion in New Post dialog, 400ms debounce, clickable results with status badges
- Helps users find existing answers before creating duplicates

**Top Contributors with Reputation:**
- Stats endpoint returns reputation scores: 10*best_answers + upvotes_received + 0.5*comments_count
- Frontend: TopContributorsCard with rank, name, best answers, upvotes, comments, reputation score
- Top 10 contributors displayed

**Collections:** `forum_votes` (new)
**Test Status:** 100% passed (iteration_138, 17/17 backend + frontend)

### Forum Image Uploads with Publitio (Mar 3, 2026) - COMPLETE
**Image Upload Feature:**
- Forum posts and comments can now include images (up to 4 per post/comment)
- 2MB file size limit per image
- Supported formats: JPG, PNG, GIF, WebP
- Images stored via Publitio CDN with folder organization (`forum/posts/`, `forum/comments/`)
- Frontend component: `ForumImageUpload.jsx` with preview, drag-drop, progress indicator

**Backend Endpoints:**
- `POST /api/publitio/upload` — Upload image with folder categorization
- `GET /api/publitio/test` — Test Publitio connection status
- `GET /api/publitio/folders` — List Publitio folders
- `POST /api/publitio/folder/create` — Create new folder (admin only)
- `DELETE /api/publitio/file/{id}` — Delete uploaded file (admin only)

**Forum API Updates:**
- `POST /api/forum/posts` — Now accepts `images: string[]` array
- `POST /api/forum/posts/{id}/comments` — Now accepts `images: string[]` array
- Posts and comments return images array in responses

**Admin Settings Integration:**
- Publitio card added to Platform Settings > API Keys tab
- API Key and API Secret input fields with visibility toggle
- "Test Connection" button to verify credentials
- Setup instructions with links to publit.io
- Credentials stored in platform settings DB

**Files:**
- `/app/backend/routes/publitio.py` — Publitio API routes
- `/app/frontend/src/components/ForumImageUpload.jsx` — Upload component
- `/app/frontend/src/pages/ForumListPage.jsx` — New Post dialog updated
- `/app/frontend/src/pages/ForumPostPage.jsx` — Comment section + ImageGallery
- `/app/frontend/src/pages/admin/AdminSettingsPage.jsx` — Publitio settings card

**Test Status:** 100% passed (iteration_140, 11/11 backend + all frontend features verified)

### Profit Tracker Hide/Show Amounts Toggle (Mar 3, 2026) - COMPLETE
**Feature:**
- Per-card eye icon toggle for each summary card (Account Value, Deposits, Total Profit, LOT Size, Account Growth)
- Clicking the eye icon on each card individually hides/shows that specific value
- Values masked with "••••••" when hidden
- Each card can be independently controlled

**Implementation:**
- `hiddenCards` state object in ProfitTrackerPage.jsx
- `toggleCardVisibility(cardKey)` function for per-card control
- Individual `data-testid` for each toggle: `toggle-account-value`, `toggle-deposits`, `toggle-profit`, `toggle-lot-size`, `toggle-growth`

**Test Status:** Verified working via screenshot

### Critical Bug Fix: Withdrawals Not Included in Balance Calculations (Mar 3, 2026) - FIXED
**Issue:**
- User reported incorrect Balance Before values in Monthly Table
- Account value showed ~$37,607 when actual balance was ~$31,000
- Root cause: Withdrawals stored in `db.withdrawals` collection were NOT being included in balance calculations

**Fixed Files:**
- `/app/backend/utils/calculations.py` — `get_user_financial_summary()` and `calculate_account_value()` now query and subtract from `db.withdrawals` collection
- `/app/backend/server.py` — `/api/profit/daily-balances` endpoint now includes withdrawals in balance calculations

**Impact:**
- Account value calculations now correctly subtract withdrawals
- Monthly Table "Balance Before" values now accurate
- Trade Monitor LOT Size calculations now correct
- Withdrawal preview now shows correct remaining balance

### P1 - Upcoming
- Rewards Admin Dashboard UI (Backend complete, frontend pending)

### P2 - Improvements
- Frontend refactoring: AdminSettingsPage.jsx split (**DONE** - Mar 3, 2026: 3368→1900 lines, extracted EmailsTab, TradingTab, DiagnosticsTab)
- Frontend refactoring: ProfitTrackerPage.jsx split (5280 lines — deferred, tightly coupled dialogs)
- Backend refactoring: Extract remaining routers from server.py (9840 lines — deferred, high risk)

### P3 - Future
- Cloudinary integration (deprecated in favor of Publitio)
- Chatbase integration
- Rewards store UI (handled by rewards.crosscur.rent)
- Admin UI for PromotionRule management

## Test Credentials
- Master Admin: iam@ryansalvador.com / admin123
- Licensee (Honorary FA): rizza.miles@gmail.com / rizza123
- Internal API Key: _CXCB2Y-ObBIZqqaCzmjEJU1zwe7DMHr8C-tzoef9h0

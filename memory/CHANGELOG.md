# CrossCurrent Hub - Changelog

## Mar 3, 2026 (Session 3)

### Forum Image Uploads with Publitio Integration
- Added image upload capability to forum posts and comments
- 2MB file size limit, supports JPG/PNG/GIF/WebP
- New backend routes: `/api/publitio/upload`, `/api/publitio/test`, `/api/publitio/folders`
- Frontend component: `ForumImageUpload.jsx` with preview, progress indicator
- Admin Settings: Publitio card in API Keys tab with setup instructions
- Images stored via Publitio CDN in organized folders (forum/posts/, forum/comments/)
- Forum posts/comments now accept and display `images[]` array

### Profit Tracker Per-Card Hide/Show Toggle
- Moved hide/show toggle INSIDE each summary card for individual control
- Each card (Account Value, Deposits, Total Profit, LOT Size, Account Growth) has its own eye icon
- Users can hide/show specific values independently
- `hiddenCards` state object tracks visibility per card

### CRITICAL BUG FIX: Withdrawals Not Included in Balance Calculations
- **Issue:** User reported Balance Before values were ~$6,000 too high
- **Root Cause:** Withdrawals stored in `db.withdrawals` collection were not being queried
- **Fixed:** `get_user_financial_summary()`, `calculate_account_value()`, and `/api/profit/daily-balances` now include withdrawals
- **Impact:** Account values, Monthly Table, Trade Monitor LOT sizes all now correct

**Test Status:** 100% passed (iteration_140) + additional visual verification

## Mar 3, 2026 (Session 2)

### Community Forum Feature
- Built full-stack ticketing-style forum: create posts, comment, mark best answer, close with point awards
- Backend: 8 endpoints in `routes/forum.py` (CRUD posts, comments, best answer, close, stats, delete)
- Frontend: ForumListPage (stats, search, filters, pagination), ForumPostPage (thread view, close dialog, collaborator selection)
- Points system: Best Answer = 50 pts, Active Collaborator = 15 pts each
- Sidebar + MobileMenu: "Community Forum" link with MessageSquare icon
- New collections: `forum_posts`, `forum_comments`

### Forum Enhancements: Voting, Similar Search, Reputation
- **Upvote/Downvote**: ThumbsUp/ThumbsDown on comments, toggle/switch, voter names visible (non-anonymous), self-vote blocked
- **Similar Posts AJAX**: Live search in New Post dialog (3+ chars, 400ms debounce), shows existing posts with status badges
- **Top Contributors**: Reputation scoring (10x best answers + upvotes + 0.5x comments), ranked leaderboard on forum page
- New collection: `forum_votes`
- New endpoints: `POST /api/forum/comments/{id}/vote`, `GET /api/forum/comments/{id}/voters`, `GET /api/forum/search-similar`

### Real-time WebSocket Forum Updates
- Backend: `broadcast_forum_event` in `websocket_service.py` — broadcasts `forum_new_comment`, `forum_vote`, `forum_post_closed` events
- Frontend: `WebSocketContext` exposes `lastForumEvent` state; `ForumPostPage` auto-refreshes when matching event arrives
- No toasts for forum events — just silent UI refresh

### Frontend Refactoring: AdminSettingsPage
- Reduced from 3368 to 1900 lines (43% reduction)
- Extracted `EmailsTab.jsx` — self-contained email template editor + email history
- Extracted `TradingTab.jsx` — self-contained products management + global holidays calendar
- Extracted `DiagnosticsTab.jsx` — self-contained system diagnostics, batch sync, health check, rewards sync, scan all members

### Scan All Members Button
- Verified "Scan All Members" retroactive rewards scan button on Admin Settings > Diagnostics tab
- Backend endpoint `/api/rewards/retroactive-scan-all` working (scanned 15 users)

## Mar 3, 2026

### Streak Freeze Feature
- Added streak freeze purchase system: Trade Streak Freeze (200 pts) and Habit Streak Freeze (150 pts)
- Backend: `GET /api/rewards/streak-freezes`, `POST /api/rewards/streak-freezes/purchase`
- Frontend: StreakFreezeSection on My Rewards page with quantity selector and buy buttons
- Trade streak and habit streak calculations updated to check for active freezes
- Created `/app/prompts_for_rewards_platform_streak_freeze.md` for Rewards Platform integration

## Feb 18, 2026 (Session 2)

### Simulation Dialog/Banner Stale Value Fix
- **Root Cause:** `GET /api/admin/licenses` returned raw `license.current_amount` from DB (stale) for honorary licensees
- **Fix:** Added `calculate_honorary_licensee_value()` call for honorary/honorary_fa in the licenses endpoint
- **Result:** Simulation dialog now shows $6,530 (dynamic) instead of $798.57 (stale)
- Sidebar.jsx simulation data now picks up correct values from backend

### Licensee Dashboard Redesign
- Replaced "Trade Performance" chart with **Year-by-Year Growth Projections** (1yr, 2yr, 3yr, 5yr)
- Replaced "Recent Trades" with **Family Account Members** stats table
- Added `GET /api/profit/licensee/year-projections` backend endpoint
- Projections use same quarterly compounding: LOT = Balance/980, Daily = LOT×15, recalculated each quarter
- Family members table shows name, relationship, starting amount, current value, profit, status

### Admin Add Family Member on Behalf
- Added Users icon button on honorary_fa license rows in Admin Licenses page
- Opens dialog for admin to enter member name, relationship, starting amount
- Uses existing `POST /api/admin/family/members/{userId}` backend endpoint

## Feb 18, 2026 (Session 1)

### P0 Fix: Profit Tracker Data Consistency for Direct Licensee Login
- Fixed `/api/profit/licensee/welcome-info` to use `calculate_honorary_licensee_value()`
- All 4 key endpoints return identical dynamically calculated values
- Backend test: 10/10 passed (iteration_114)

### Admin Temp Password with Forced Reset on First Login
- Modified login endpoint to return `must_change_password` flag
- Added `POST /api/auth/force-change-password` endpoint
- Frontend: force change password dialog before dashboard redirect

## Feb 17, 2026
### Family Account Feature (End-to-End)
- Created `honorary_fa` license type with family member CRUD
- Built all APIs for admin conversion, member management, withdrawal approvals

### Admin Reset Functionality
- Reset starting balance, trade start date, and family member reset endpoints

### Profit Tracker Logic Refactor (Partial)
- Dynamic `calculate_honorary_licensee_value()` with quarterly compounding

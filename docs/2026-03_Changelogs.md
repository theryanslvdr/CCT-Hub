# CrossCurrent Hub - Complete Changelog
**Development History: January 2026 - March 2026**

---

## Table of Contents
- [March 2026](#march-2026)
- [February 2026](#february-2026)
- [January 2026](#january-2026)
- [Version Summary](#version-summary)

---

## March 2026

### March 3, 2026 - Forum Images & Balance Fix

#### Major: Forum Image Upload System
Complete image upload integration for community forum.

**Features:**
- Upload images to forum posts and comments
- Up to 4 images per post/comment
- 2MB file size limit per image
- Supported formats: JPG, PNG, GIF, WebP
- Image preview before posting
- Lightbox gallery for viewing images
- Publitio CDN integration for storage

**Files Added/Modified:**
- `backend/routes/publitio.py` - New file for Publitio API
- `frontend/src/components/ForumImageUpload.jsx` - Upload component
- `frontend/src/pages/ForumListPage.jsx` - Post creation with images
- `frontend/src/pages/ForumPostPage.jsx` - Comment images, gallery

**Minor Changes:**
- Added `images[]` field to forum post/comment models
- Added Publitio setup instructions to Platform Settings
- Test connection button for Publitio credentials

---

#### Major: Per-Card Hide/Show Toggle (Profit Tracker)
Individual privacy controls for each summary card.

**Features:**
- Eye icon on each card: Account Value, Deposits, Profit, LOT Size, Growth
- Independent toggle per card
- Values masked with "••••••" when hidden
- State persists during session

**Files Modified:**
- `frontend/src/pages/ProfitTrackerPage.jsx`

**Minor Changes:**
- Changed from global toggle to `hiddenCards` state object
- Added `toggleCardVisibility(cardKey)` function
- Individual `data-testid` for each toggle button

---

#### Major: Balance Calculation Bug Fixes
Critical fixes for account value and Monthly Table calculations.

**Root Cause:**
Withdrawals stored in `db.withdrawals` collection were not being included in balance calculations.

**Fixes Applied:**
- `backend/utils/calculations.py`:
  - `get_user_financial_summary()` now queries `db.withdrawals`
  - `calculate_account_value()` now includes withdrawals
- `backend/server.py`:
  - `/api/profit/daily-balances` includes withdrawals
  - `/api/profit/withdrawals` returns from correct collection
  - Added `/api/profit/debug-transactions` for troubleshooting

**Minor Changes:**
- Added debug info to daily-balances response
- Fixed BUILD_VERSION to persist (prevent false "new version" banners)
- Fixed Platform Settings null value warnings

---

### March 2, 2026 - Forum Enhancements

#### Major: Community Forum Feature
Complete ticketing-style forum for community Q&A.

**Features:**
- Create posts with title, description, tags
- Comment on posts with replies
- Upvote/downvote system with voter visibility
- Best Answer marking with point rewards
- Active Collaborator selection
- Post status: Open, Solved, Closed
- Similar posts search during creation
- Top Contributors leaderboard
- Real-time WebSocket updates

**Backend Endpoints:**
- `POST /api/forum/posts` - Create post
- `GET /api/forum/posts` - List posts with pagination
- `GET /api/forum/posts/{id}` - Get post with comments
- `POST /api/forum/posts/{id}/comments` - Add comment
- `PUT /api/forum/posts/{id}/best-answer/{comment_id}` - Mark best answer
- `PUT /api/forum/posts/{id}/close` - Close post
- `DELETE /api/forum/posts/{id}` - Delete post
- `POST /api/forum/comments/{id}/vote` - Vote on comment
- `GET /api/forum/comments/{id}/voters` - Get voter list
- `GET /api/forum/search-similar` - Similar post search
- `GET /api/forum/stats` - Forum statistics

**Files Added:**
- `backend/routes/forum.py`
- `frontend/src/pages/ForumListPage.jsx`
- `frontend/src/pages/ForumPostPage.jsx`

**Minor Changes:**
- Added forum link to sidebar navigation
- WebSocket events for real-time comment/vote updates
- Points integration (50pts best answer, 15pts collaborator)

---

#### Major: Admin Settings Refactoring
Split monolithic settings page into smaller components.

**Changes:**
- Reduced `AdminSettingsPage.jsx` from 3368 to ~1900 lines
- Extracted components:
  - `EmailsTab.jsx`
  - `TradingHolidaysTab.jsx`
  - `DiagnosticsTab.jsx`

**Minor Changes:**
- Improved code maintainability
- Consistent component patterns
- Better error handling per tab

---

### March 1, 2026 - Rewards Admin Dashboard

#### Major: Rewards Admin Feature
Bird's eye view for managing member rewards.

**Features:**
- Overview tab with key statistics
- User lookup by email/ID
- Points management (credit/deduct with audit trail)
- Badge management (edit, enable/disable)
- Simulate points for testing
- Full audit trail of transactions
- CSV export functionality

**Backend Endpoints:**
- `GET /api/rewards/admin/overview`
- `GET /api/rewards/admin/members`
- `GET /api/rewards/admin/audit-trail`
- `POST /api/rewards/admin/credit-points`
- `POST /api/rewards/admin/deduct-points`
- `POST /api/rewards/admin/award-badge`
- `POST /api/rewards/admin/revoke-badge`
- `GET /api/rewards/admin/export/members`
- `GET /api/rewards/admin/export/audit`

**Files Added/Modified:**
- `backend/routes/rewards.py` - Admin endpoints
- `frontend/src/pages/admin/RewardsAdminPage.jsx`

---

## February 2026

### February 27, 2026 - Streak Freezes & Badge System

#### Major: Streak Freeze System
Purchase protection against losing streaks.

**Features:**
- Trade Streak Freeze: 200 points
- Habit Streak Freeze: 150 points
- Buy 1-10 at a time
- Auto-apply on missed days
- Usage history tracking

**Minor Changes:**
- Added freeze inventory to rewards stats
- Freeze purchase modal
- History view in My Rewards

---

#### Major: Badge Achievement System
30 badges with automatic awarding.

**Badge Categories:**
- Trading: First Trade, 50/100/500/1000 trades
- Streaks: 3/7/14/30/50/100 day streaks
- Points: 100/500/1K/5K/10K milestones
- Referrals: 1/5/10/25 referrals
- Deposits: $100/$500/$1K/$5K deposits
- Activity: 10/30/50/100 days active

**Minor Changes:**
- Badge display in My Rewards
- Badge tooltips with descriptions
- Progress indicators for unlocked badges

---

### February 20, 2026 - Licensee System

#### Major: Honorary License System
Managed accounts growing with master admin trades.

**Features:**
- License types: Honorary, Honorary FA, Extended
- Quarterly compounding formula
- Year-by-year growth projections
- Family account support (up to 5 members)
- Admin management console

**Backend:**
- License model and CRUD operations
- Projection calculation engine
- Batch sync functionality
- Family member management

**Frontend:**
- Licensee-specific dashboard
- Growth projection charts
- Family member table

**Minor Changes:**
- `_is_honorary()` helper function
- `calculate_honorary_licensee_value()` with quarterly compounding
- Trading days calculation excluding weekends/holidays

---

### February 15, 2026 - Rewards Platform Integration

#### Major: External Rewards Platform
Integration with rewards.crosscur.rent.

**Features:**
- User sync to external platform
- Points balance sync
- "Open Rewards & Store" button
- Redemption flow

**Minor Changes:**
- API key management
- Auto-sync on profile updates
- Sync status in diagnostics

---

### February 10, 2026 - Leaderboard System

#### Major: Monthly/All-Time Leaderboards
Compete with other members.

**Features:**
- Monthly rankings
- All-time rankings
- Top 3 podium display
- Your position highlight
- Up/down movement indicators

**Minor Changes:**
- Rank calculation caching
- Performance optimizations
- Real-time updates

---

### February 5, 2026 - My Rewards Page

#### Major: Complete Rewards Tracking
Full rewards center for members.

**Features:**
- Points balance display
- Level progression
- Monthly rank
- Earning actions (8 total)
- Points history with filters
- CSV export

**Minor Changes:**
- Currency conversion (100pts = 1 USDT)
- Pagination for history
- Filter by time range

---

## January 2026

### January 28, 2026 - Trade Monitor

#### Major: Real-Time Trade Execution
Execute and track trades.

**Features:**
- Daily trade summary
- Entry/Exit input
- Active trades panel
- Trade history table
- Streak tracking
- WebSocket real-time updates

**Minor Changes:**
- Day # column (global trade day number)
- Commission tracking
- Trade adjustment for past trades

---

### January 20, 2026 - Profit Tracker

#### Major: Profit Projection System
Comprehensive profit tracking and projections.

**Features:**
- Summary cards (Account Value, Deposits, Profit, LOT)
- Projection Vision section
- Monthly Table with day-by-day breakdown
- Today's Trading Signal
- Balance sync with Merin

**Formula Implementation:**
```
LOT Size = truncate(Account Value / 980, 2 decimals)
Daily Target = LOT Size × 15
```

**Minor Changes:**
- Currency conversion selector
- Export to CSV
- Reset tracker functionality

---

### January 15, 2026 - Dashboard

#### Major: Main Dashboard
Central hub for financial overview.

**Features:**
- Account Value card
- Total Profit card
- Performance messages
- Rewards preview
- Quick actions

**Minor Changes:**
- Currency selector
- Hide/show toggle (original global)
- Recent activity timeline

---

### January 10, 2026 - Authentication System

#### Major: User Authentication
Complete auth flow with role-based access.

**Features:**
- Login/Logout
- Password reset (email + admin)
- Role system (Member, Basic/Super/Master Admin)
- Session management

**Minor Changes:**
- Remember me functionality
- Forced password change
- 1-hour reset token expiry

---

### January 5, 2026 - Foundation

#### Major: Platform Foundation
Initial platform setup and infrastructure.

**Technology Stack:**
- Frontend: React (Vite), Shadcn/UI, TailwindCSS
- Backend: FastAPI, Motor (async MongoDB)
- Database: MongoDB
- Real-time: WebSocket

**Initial Features:**
- Project structure
- Database models
- API routing
- Basic UI components

---

## Version Summary

| Version | Date | Major Features |
|---------|------|----------------|
| 1.0.0 | Jan 5 | Platform foundation |
| 1.1.0 | Jan 10 | Authentication system |
| 1.2.0 | Jan 15 | Dashboard |
| 1.3.0 | Jan 20 | Profit Tracker |
| 1.4.0 | Jan 28 | Trade Monitor |
| 1.5.0 | Feb 5 | My Rewards page |
| 1.6.0 | Feb 10 | Leaderboard system |
| 1.7.0 | Feb 15 | Rewards platform integration |
| 1.8.0 | Feb 20 | Licensee system |
| 1.9.0 | Feb 27 | Streak freezes & badges |
| 2.0.0 | Mar 1 | Rewards Admin dashboard |
| 2.1.0 | Mar 2 | Community Forum |
| 2.2.0 | Mar 3 | Forum images, per-card toggles, balance fixes |

---

## Upcoming Features (Roadmap)

### P1 - High Priority
- Rewards Admin Dashboard UI completion
- Balance calculation audit system

### P2 - Medium Priority
- Server.py route extraction refactoring
- Additional forum features

### P3 - Future
- Chatbase integration
- PromotionRule admin UI
- Mobile app

---

*Changelog maintained by development team*
*Last Updated: March 2026*

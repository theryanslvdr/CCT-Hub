# CrossCurrent Hub - Complete Feature Documentation

## Table of Contents
1. [Overview](#overview)
2. [User Roles & Permissions](#user-roles--permissions)
3. [Dashboard](#dashboard)
4. [Profit Tracker](#profit-tracker)
5. [Trade Monitor](#trade-monitor)
6. [My Rewards](#my-rewards)
7. [Leaderboard](#leaderboard)
8. [Community Forum](#community-forum)
9. [Daily Habits](#daily-habits)
10. [Affiliate Center](#affiliate-center)
11. [Admin Features](#admin-features)
12. [License Management](#license-management)
13. [Family Accounts](#family-accounts)

---

## Overview

CrossCurrent Hub is a comprehensive financial tracking platform designed for the CrossCurrent trading community. It provides tools for tracking profits, managing deposits/withdrawals, earning rewards, and community engagement.

**Core Technology Stack:**
- Frontend: React (Vite) with Shadcn/UI, TailwindCSS
- Backend: FastAPI with Motor (async MongoDB)
- Database: MongoDB
- Real-time: WebSocket connections for live updates

---

## User Roles & Permissions

### Master Admin
- **Full platform control** - Access to ALL features
- Manages all members, licensees, and settings
- Access to: System Check, Platform Settings, API Center, Licenses, Rewards Admin
- Can simulate viewing the platform as other user roles
- Email: iam@ryansalvador.com

### Super Admin
- Full admin capabilities **EXCEPT**:
  - System Check
  - Platform Settings  
  - API Center
  - Licenses
- Can view: Members, Trading Signals, Team Analytics, Transactions, Rewards Admin

### Basic Admin
- Limited admin capabilities
- Can view: Members, Trading Signals, Team Analytics only

### Member
- Regular trader with profit tracking
- Access to: Dashboard, Profit Tracker, Trade Monitor, My Rewards, Leaderboard, Community Forum, Daily Habits, Affiliate Center, Profile

### Licensee (Honorary/Honorary FA/Extended)
- Managed accounts whose value grows based on master admin trades
- Simplified dashboard with year-by-year growth projections
- No manual trading capabilities

---

## Dashboard

The main hub for viewing your financial overview at a glance.

### Features:
- **Account Value Card** - Shows current account balance with hide/reveal toggle
- **Total Profit Card** - Cumulative profit earned
- **Currency Conversion** - View amounts in USD, PHP, EUR, GBP
- **Performance Message** - Contextual message based on your trading performance
- **Quick Actions** - Access Trade Monitor, view recent activity

### For Licensees:
- Year-by-Year Growth Projections (1yr, 2yr, 3yr, 5yr)
- Family Account Members table (for Honorary FA accounts)
- Simplified view without trading controls

### Key Components:
- Rewards card showing points balance, level, and rank
- Recent activity timeline
- Growth projection charts

---

## Profit Tracker

Comprehensive profit tracking with projections and historical analysis.

### Summary Cards:
| Card | Description |
|------|-------------|
| Account Value | Current account balance with "Sync" button to verify with Merin |
| Deposits | Total deposits in selected currency |
| Total Profit | Cumulative actual profit from trades |
| LOT Size | Current trading lot size (Balance ÷ 980) |

**Privacy Feature:** Each card has an eye icon toggle to individually hide/show values with "••••••" masking.

### Projection Vision Section:
- **Summary Tab**: Current balance, LOT size, daily profit projection, formula display
- **Monthly Table Tab**: Day-by-day breakdown showing:
  - Date
  - Balance Before (account value at start of day)
  - LOT Size (calculated lot for that balance)
  - Target Profit (LOT × 15)
  - Actual Profit (recorded if trade occurred)
  - Commission earned
  - Status indicator

### Features:
- **Today's Trading Signal** - Shows current signal (e.g., "MOIL10 SELL at 15:00")
- **Trade Now Button** - Quick access to execute trades
- **Access Records** - View historical trade data
- **Reset Tracker** - Reset tracking from a specific date
- **Simulate Actions** - Test different scenarios

### Formula:
```
LOT Size = truncate(Account Value / 980, 2 decimals)
Daily Profit Target = LOT Size × 15
```
*Note: Uses truncation (floor), not rounding*

---

## Trade Monitor

Real-time trade execution and monitoring interface.

### Key Sections:

#### Daily Trade Summary
- Today's projected profit
- Completed trades count
- Commission earned
- Win rate percentage

#### Trade Control
- **ENTRY** - Entry price input
- **EXIT** - Exit price input  
- **TARGET** - Calculated target based on LOT size
- Balance and LOT size display
- Quick trade execution buttons

#### Active Trades Panel
- Currently open positions
- Real-time P&L updates
- Close trade functionality

#### Trade History
- Complete history of executed trades
- Streak indicator (consecutive profitable days)
- "Day #" column showing global trade day number
- Filtering by date range
- Export functionality

### Features:
- WebSocket-powered real-time updates
- One-click trade submission
- Trade adjustment for past entries
- Commission tracking

---

## My Rewards

Complete rewards tracking and earning center.

### Overview Cards:
| Card | Description |
|------|-------------|
| Points Balance | Total points with USDT equivalent (~$0.01/point) |
| Level | Current level with progress to next (Newbie → Trade Novice → ... → Elite) |
| Monthly Rank | Your position on the monthly leaderboard |

### Streak Tracking:
- **Current Streak** - Consecutive trading days
- **Best Streak** - Your longest streak ever
- Holiday-aware (weekends and US market holidays don't break streaks)

### Earning Actions (8 Total):
| Action | Points | Type |
|--------|--------|------|
| Sign Up & Verify | 25 | Auto (on first trade) |
| Join Community | 5 | Manual Claim |
| First Trade | 25 | Auto |
| First Daily Win | 10 | Auto |
| 5-Day Streak | 50 | Auto (repeatable) |
| 10 Trades Milestone | 125 | Auto |
| Qualified Referral | 150 | Auto (per referral) |
| Deposit Bonus | 50 per $50 | Auto |

### Streak Freezes:
Purchase protection against losing your streak:
- **Trade Streak Freeze**: 200 points (protects trading streak)
- **Habit Streak Freeze**: 150 points (protects habit streak)
- Buy 1-10 at a time
- View usage history

### Badges & Achievements:
30 badges available including:
- **Trading Badges**: First Trade, 50 Trades Club, Century Trader, Trading Veteran, Trading Legend
- **Streak Badges**: Streak Starter (3), Streak Master (7/14/30), Streak Champion (50), Streak Legend (100)
- **Points Badges**: Points Rookie (100), 500/1K/5K/10K milestones
- **Referral Badges**: First Referral, Referral Champion/Pro/Legend
- **Deposit Badges**: First Deposit, Deposit Hero, High Roller, Whale
- **Activity Badges**: 10/30/50/100 Days Active

### Points History:
- Full transaction log with Date, Type, Source, Points, Balance
- Filters: All Time, 7 Days, 30 Days, 90 Days, Custom
- Activity type filters
- CSV export
- Pagination

### Rewards Store:
Click "Open Rewards & Store" to visit rewards.crosscur.rent where you can:
- Browse available rewards
- Redeem points for prizes
- View exclusive offers

---

## Leaderboard

Compete with other members for top positions.

### Views:
- **Monthly** - Rankings for current month
- **All Time** - Lifetime rankings

### Display:
- **Podium** - Top 3 members with special display
- **Full Rankings Table**:
  - Rank position
  - User name
  - Level badge
  - Points earned
  - Change indicator (up/down arrows)

### Your Position:
- Highlighted card showing your rank
- Distance to next position
- Personalized encouragement message

---

## Community Forum

Knowledge-sharing platform for the trading community.

### Forum Statistics:
- Total Posts
- Open Questions
- Solved Questions
- Total Comments

### Top Contributors:
- Ranked by reputation score
- Formula: `10 × best_answers + upvotes_received + 0.5 × comments_count`

### Creating Posts:
1. Click "New Post" button
2. Enter title and detailed description
3. Add tags (comma-separated)
4. **Attach Images** (optional):
   - Up to 4 images per post
   - Max 2MB per image
   - Supported: JPG, PNG, GIF, WebP
5. Similar Posts search helps find existing answers

### Post Features:
- **Status Badges**: Open (blue), Solved (green), Best Answer (gold)
- **Tags**: Categorize posts for easy discovery
- **View Count**: Track post popularity
- **Comment Count**: See engagement level

### Commenting:
- Add replies to help others
- Attach images to comments
- **Upvote/Downvote** system:
  - See who voted (non-anonymous)
  - Cannot vote on your own comments
  - Voter names displayed on hover

### Solving Posts:
1. Original poster or admin marks "Best Answer"
2. Select active collaborators for bonus points
3. Close post to prevent further comments
4. **Points Awarded**:
   - Best Answer: 50 points
   - Active Collaborator: 15 points each

### Real-time Updates:
- WebSocket integration
- Automatic refresh when new comments or votes arrive

---

## Daily Habits

Track and maintain positive daily habits.

### Features:
- Create custom habits to track
- Daily check-off system
- Streak tracking (holiday-aware)
- Photo/screenshot upload for proof
- Progress visualization

### Habit Completion:
1. View today's habits
2. Mark as complete
3. Optionally upload proof screenshot
4. Build your streak!

### Streak Protection:
- Purchase Habit Streak Freezes (150 points)
- Automatically applied on missed days

---

## Affiliate Center

Grow your network and earn rewards.

### Features:
- Unique referral link generation
- Track referred members
- Monitor referral status
- View commission earnings
- Qualified Referral: 150 points when referee completes first trade

---

## Admin Features

### Member Management
- View all members with search and filters
- Role management (Member, Basic Admin, Super Admin)
- Account status (Active/Inactive)
- Quick actions: View profile, Reset password, Edit, Delete

### Trading Signals
- Set daily trading signals (e.g., "MOIL10 SELL at 15:00")
- Signal history and scheduling

### Team Analytics
- Platform-wide statistics
- User engagement metrics
- Trading performance overview

### Transactions
- View all deposits and withdrawals
- Approve/reject withdrawal requests
- Transaction history with filters

### Rewards Admin
- **User Lookup**: Search by email or user ID
- **Points Management**: Credit/deduct points with audit trail
- **Badge Management**: Edit badge names, descriptions, enable/disable
- **Simulate Points**: Test point awards (tagged as "Admin Test")

### System Check (Master Admin Only)
- 10-step health check for rewards system
- Validates API endpoints
- Checks database connections
- Badge definition verification

### Platform Settings (Master Admin Only)

#### General Tab:
- Site title and description
- Logo and favicon upload
- OG image for social sharing

#### Branding Tab:
- Primary and accent colors
- Custom CSS injection

#### API Keys Tab:
- **Emailit**: Password reset emails
- **Cloudinary**: Image uploads (legacy)
- **Heartbeat**: User verification
- **Publitio**: Forum image hosting
- Test connection buttons for each

#### Login Tab:
- Custom login page title and tagline
- Login notice message
- Registration link customization

#### Footer Tab:
- Custom footer links
- Copyright text

#### Maintenance Tab:
- Enable/disable maintenance mode
- Custom maintenance message

#### Diagnostics Tab:
- Licensee batch sync
- Health check tools
- Individual user diagnostics
- Rewards platform sync
- "Scan All Members" for retroactive badge awards

### API Center (Master Admin Only)
- View and manage API keys
- Integration documentation
- Rate limit monitoring

---

## License Management

### License Types:

#### Honorary License
- Value grows based on master admin trading performance
- Quarterly compounding: LOT = Balance/980, Daily = LOT × 15
- No manual trading required

#### Honorary FA (Family Account)
- Same as Honorary, plus up to 5 family members
- Combined account overview
- Individual member tracking

#### Extended License
- Fixed amount that doesn't compound
- Simple value tracking

### Admin Functions:
- Create new licenses
- Set effective start date
- Define starting amount
- Add family members (for FA)
- Force recalculation/sync
- Convert between license types

### Licensee View:
- Simplified dashboard
- Year-by-year growth projections showing:
  - License Year End (from start date)
  - Forward Projections (from current balance)
- Family member table (if FA)

---

## Family Accounts

For Honorary FA licensees, manage family member investments.

### Features:
- Add up to 5 family members
- Track individual starting amounts
- View current values and profit
- Withdrawal management per member

### Admin Management:
- Add members on behalf of licensee
- Edit member details
- Reset member values
- Remove family members

### Family Member Card:
- Name and relationship
- Starting amount
- Current value
- Profit earned
- Status indicator

---

## Additional Features

### Password Reset
- **Admin-Initiated**: Admin can set temporary password with forced reset on first login
- **User-Initiated**: "Forgot Password" sends email with reset link (via Emailit)
- 1-hour token expiry
- Branded email template

### Notifications
- In-app notification center
- Toast notifications for:
  - New badges earned
  - Trade completions
  - System alerts

### Mobile Support
- Responsive design for all screen sizes
- Mobile navigation menu
- Touch-friendly interactions

### BVE Mode
- Balance Verification Engine
- Special mode for balance synchronization
- Admin-controlled toggle

### Simulation Mode
- Admin can simulate viewing as other roles
- Test features without affecting real data
- "Simulate View" dropdown in sidebar

---

## Technical Notes

### Financial Formula
```
Quarterly Fixed Daily Profit = truncate_lot_size(Account Value at Quarter Start) × 15
LOT Size = math.trunc(Account Value / 980 × 100) / 100
```
- Uses **truncation** (floor to 2 decimals), NOT rounding
- Daily profit is FIXED for entire calendar quarter
- Recalculated at each new quarter start
- Trading days = weekdays excluding US market holidays (~250/year)

### Rewards Points System
- Single currency: POINTS
- Conversion: 100 points = 1 USDT
- Minimum redemption: 500 points ($5 USDT)

### WebSocket Events
- Real-time trade updates
- Forum notifications
- System alerts

---

*Last Updated: March 2026*

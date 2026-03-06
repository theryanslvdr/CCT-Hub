# CrossCurrent Hub - Admin Features Guide
**Last Updated: March 2026**

---

## Table of Contents
1. [Admin Dashboard Overview](#admin-dashboard-overview)
2. [Member Management](#member-management)
3. [Trading Signals](#trading-signals)
4. [Team Analytics](#team-analytics)
5. [Transactions Management](#transactions-management)
6. [Rewards Admin](#rewards-admin)
7. [System Check](#system-check)
8. [Platform Settings](#platform-settings)
9. [API Center](#api-center)
10. [License Management](#license-management)
11. [Diagnostics & Troubleshooting](#diagnostics--troubleshooting)

---

## Admin Dashboard Overview

### Access Levels by Role

| Feature | Master Admin | Super Admin | Basic Admin |
|---------|--------------|-------------|-------------|
| Members | ✅ | ✅ | ✅ |
| Trading Signals | ✅ | ✅ | ✅ |
| Team Analytics | ✅ | ✅ | ✅ |
| Transactions | ✅ | ✅ | ❌ |
| Rewards Admin | ✅ | ✅ | ❌ |
| System Check | ✅ | ❌ | ❌ |
| Platform Settings | ✅ | ❌ | ❌ |
| API Center | ✅ | ❌ | ❌ |
| Licenses | ✅ | ❌ | ❌ |

### Simulation Mode
Master Admin can simulate viewing the platform as other roles:
1. Click "Simulate View" dropdown in sidebar
2. Select a user to simulate
3. Platform displays as that user would see it
4. Yellow banner indicates simulation mode
5. Click "Exit Simulation" to return to admin view

---

## Member Management

**Location:** Admin Section → Members

### Overview Statistics
- **Total Members** - All registered users
- **Members** - Regular member count
- **Admins** - Admin user count
- **Licensed Users** - Users with active licenses

### Member Table Columns
| Column | Description |
|--------|-------------|
| Member | Name with avatar |
| Email | User's email address |
| Role | Member/Basic Admin/Super Admin/Master Admin |
| Account Value | Current account balance |
| Status | Active/Inactive |
| Joined | Registration date |
| Actions | View, Edit, Reset Password, Delete |

### Search & Filters
- **Search** - By name or email
- **Role Filter** - All Roles, Member, Basic Admin, Super Admin
- **Status Filter** - All Status, Active, Inactive
- **Sort Order** - Default, Name A-Z, Name Z-A, Newest, Oldest

### Member Actions

#### View Member (Eye Icon)
Opens detailed member profile showing:
- Account information
- Trade history
- Deposit/withdrawal history
- Points and badges

#### Edit Member (Pencil Icon)
Modify:
- Full name
- Email address
- Role assignment
- Account status

#### Reset Password (Key Icon)
Two options:
1. **Set Temporary Password** - User must change on first login
2. **Send Reset Link** - Email with password reset link (1-hour expiry)

#### Delete Member (Trash Icon)
- Permanently removes user
- Confirmation required
- Cannot delete Master Admin

### Creating New Members
1. Click "Add Member" button
2. Fill in required fields:
   - Full Name
   - Email Address
   - Temporary Password
   - Role Selection
3. Toggle "Force password change on first login" (recommended)
4. Click "Create Member"

---

## Trading Signals

**Location:** Admin Section → Trading Signals

### Daily Signal Management
Set the daily trading signal for all members:

#### Signal Components
- **Product Code** - Trading pair (e.g., MOIL10, XAUUSD)
- **Direction** - BUY or SELL
- **Time** - Signal time in Asia/Manila timezone
- **Notes** - Optional signal notes

### Signal History
- View past signals
- Track signal performance
- Export signal data

### Daily Trade Summary
**Location:** Admin Section → Trading Signals → Daily Summary

View aggregated trading performance:
- Total trades executed
- Win/loss ratio
- Total profit/loss
- Commission earned
- Member participation rate

---

## Team Analytics

**Location:** Admin Section → Team Analytics

### Platform Statistics
- Total account value across all members
- Total deposits received
- Total withdrawals processed
- Total profit generated
- Active user count

### Charts & Visualizations
- Daily trading volume
- Weekly/monthly trends
- User growth over time
- Profit distribution

### Performance Metrics
- Average trade size
- Win rate percentage
- Most active members
- Top performers

---

## Transactions Management

**Location:** Admin Section → Transactions

### Transaction Types
- **Deposits** - Member fund additions
- **Withdrawals** - Member fund removals
- **Trades** - Trading activity
- **Adjustments** - Admin corrections

### Deposit Management

#### Pending Deposits
- Review deposit requests
- Verify payment proof
- Approve or reject
- Add admin notes

#### Approved Deposits
- Full deposit history
- Search by member
- Filter by date range
- Export to CSV

### Withdrawal Management

#### Pending Withdrawals
Review and process:
1. Member name and email
2. Withdrawal amount
3. Wallet address
4. Request date
5. Current balance

#### Actions:
- **Approve** - Confirm withdrawal, deduct from balance
- **Reject** - Decline with reason
- **Hold** - Temporarily pause processing

#### Completed Withdrawals
- Transaction history
- Processing timestamps
- Admin who approved

### Transaction Filters
- Date range selector
- Transaction type
- Status (Pending/Approved/Rejected)
- Member search
- Amount range

---

## Rewards Admin

**Location:** Admin Section → Rewards Admin

### User Lookup
Search for any member by:
- Email address
- User ID
- Name

#### Lookup Results Show:
- Points balance
- Current level
- Monthly rank
- Lifetime points earned
- Complete points history

### Points Management

#### Credit Points
1. Search for user
2. Click "Credit Points"
3. Enter amount
4. Select reason:
   - Manual Bonus
   - Promotion Credit
   - Error Correction
   - Other (specify)
5. Add note (required)
6. Confirm credit

#### Deduct Points
1. Search for user
2. Click "Deduct Points"
3. Enter amount
4. Select reason:
   - Refund
   - Error Correction
   - Policy Violation
   - Other (specify)
5. Add note (required)
6. Confirm deduction

All adjustments create audit trail entries.

### Simulate Points
Test point awards without affecting real data:
- **test_trade** - Simulate trade completion
- **test_deposit** - Simulate deposit bonus
- **test_referral** - Simulate qualified referral
- **manual_bonus** - Test manual credit

All simulated actions tagged as "Admin Test" in history.

### Badge Management
Edit badge definitions:
- Change display name
- Update description
- Enable/disable badges
- Modify point thresholds

### Transaction History
View all point transactions with filters:
- All transactions
- Earned (positive)
- Spent (negative)
- Admin Actions only

---

## System Check

**Location:** Admin Section → System Check
**Access:** Master Admin Only

### 10-Step Health Check
Validates entire rewards system:

| Step | Check | Description |
|------|-------|-------------|
| 1 | Database Connection | MongoDB connectivity |
| 2 | Collections Exist | Required collections present |
| 3 | Badge Definitions | All 30 badges defined |
| 4 | Promotion Rules | Active promotions configured |
| 5 | API Endpoints | All reward endpoints responding |
| 6 | Point Calculations | Math verification |
| 7 | Streak System | Streak tracking functional |
| 8 | Leaderboard | Rankings generating correctly |
| 9 | External APIs | Rewards platform connection |
| 10 | WebSocket | Real-time updates working |

### Running System Check
1. Navigate to System Check page
2. Click "Run Full Check"
3. Wait for all 10 steps to complete
4. Review results (Pass/Fail for each)
5. Address any failures

### Troubleshooting Failed Checks
Each failed check provides:
- Error message
- Suggested fix
- Documentation link

---

## Platform Settings

**Location:** Admin Section → Platform Settings
**Access:** Master Admin Only

### General Tab
| Setting | Description |
|---------|-------------|
| Site Title | Browser tab title |
| Site Description | SEO description |
| OG Image URL | Social sharing image |

### Branding Tab
| Setting | Description |
|---------|-------------|
| Logo URL | Header logo image |
| Favicon URL | Browser favicon |
| Primary Color | Main brand color (hex) |
| Accent Color | Secondary color (hex) |
| Custom CSS | Additional styling |

### API Keys Tab

#### Emailit (Password Reset Emails)
- API Key input
- Test Connection button
- Used for: Password reset, notifications

#### Heartbeat (User Verification)
- API Key input
- Test Connection button
- Used for: Member verification

#### Publitio (Forum Images)
- API Key input
- API Secret input
- Test Connection button
- Used for: Forum image uploads
- **Setup Instructions:**
  1. Visit publit.io
  2. Create free account
  3. Navigate to Dashboard → Settings → API
  4. Copy API Key and Secret
  5. Paste in Platform Settings

### Login Tab
| Setting | Description |
|---------|-------------|
| Login Title | Custom login page heading |
| Login Tagline | Subtitle text |
| Login Notice | Warning/info message |
| Custom Registration Link | External registration URL |

### Footer Tab
- Add custom footer links (Label + URL)
- Drag to reorder
- Delete unwanted links
- Copyright text customization

### Maintenance Tab
| Setting | Description |
|---------|-------------|
| Maintenance Mode | Enable/disable |
| Maintenance Message | Displayed to users |

When enabled:
- All non-admin users see maintenance page
- Admins can still access platform
- Custom message displayed

### Diagnostics Tab
See [Diagnostics & Troubleshooting](#diagnostics--troubleshooting)

---

## API Center

**Location:** Admin Section → API Center
**Access:** Master Admin Only

### Available APIs

#### Rewards API
Endpoints for external integration:
- `GET /api/rewards/summary` - User points summary
- `GET /api/rewards/leaderboard` - Rankings
- `POST /api/rewards/redeem` - Point redemption
- `POST /api/rewards/credit` - Add points

#### Authentication
- Internal API Key required
- Header: `X-INTERNAL-API-KEY`

### API Documentation
- Endpoint descriptions
- Request/response formats
- Example code snippets
- Rate limit information

### API Keys
- View current internal API key
- Regenerate key (invalidates old)
- Usage statistics

---

## License Management

**Location:** Admin Section → Licenses
**Access:** Master Admin Only

### License Types

#### Honorary License
- Passive investment account
- Value grows with master admin trades
- Quarterly compounding formula
- No manual trading

#### Honorary FA (Family Account)
- Same as Honorary
- Supports up to 5 family members
- Combined account view
- Individual member tracking

#### Extended License
- Fixed value license
- No compounding
- Simple tracking

### Creating a License

1. Click "Add License"
2. Select member (search by name/email)
3. Choose license type
4. Set starting amount
5. Set effective start date
6. Click "Create License"

### License Table
| Column | Description |
|--------|-------------|
| User | License holder name |
| Type | Honorary/Honorary FA/Extended |
| Starting Amount | Initial investment |
| Current Value | Calculated current value |
| Effective Date | When license started |
| Status | Active/Inactive |
| Actions | Edit, Sync, Family (FA only) |

### License Actions

#### Edit License
- Change starting amount
- Update effective date
- Modify license type

#### Force Sync
Recalculate current value:
1. Click sync icon
2. Confirms recalculation
3. Updates displayed value

#### Manage Family (FA Only)
Click users icon to:
- View family members
- Add new member (name, relationship, amount)
- Edit existing members
- Remove members

### Batch Operations
- **Batch Sync All** - Recalculate all honorary licensees
- **Health Check** - Identify calculation issues
- **Export** - Download license data as CSV

---

## Diagnostics & Troubleshooting

**Location:** Platform Settings → Diagnostics Tab
**Access:** Master Admin Only

### Sync Status Banner
Shows:
- Last sync date
- Days since last sync
- Recommendation (sync every 7 days)
- Warning if overdue (red) or never done (amber)

### Available Tools

#### 1. Batch Sync All Licensees
Recalculates ALL honorary licensee values:
1. Click "Batch Sync All"
2. Wait for processing
3. Review success/failure count
4. Check individual failures

#### 2. Health Check
Quick scan identifying issues:
- Missing effective dates
- Invalid starting amounts
- Calculation mismatches
- Database inconsistencies

#### 3. Individual Diagnostic
Enter email to see step-by-step diagnostic:
- License details
- Calculation breakdown
- Trade history impact
- Expected vs actual value

#### 4. Force Sync Single User
Manually recalculate one licensee:
1. Enter user email
2. Click "Force Sync"
3. View updated value

### Rewards Platform Sync

#### Sync Status Dashboard
- Hub Users count
- Synced count
- Rewards Platform count
- Last sync timestamp

#### Sync All Users
Push all hub users to rewards.crosscur.rent:
1. Click "Sync All Users"
2. Wait for batch processing
3. Review sync results

#### Auto-Sync Triggers
Automatic sync occurs on:
- New user registration
- Password change
- Profile update

### Scan All Members (Retroactive Badges)
Awards missed badges to all users:
1. Click "Scan All Members"
2. System checks each user's history
3. Awards earned but unawarded badges
4. View scan results

### Common Issues & Solutions

#### Issue: Licensee showing $0 value
**Solution:**
1. Run Individual Diagnostic
2. Check effective_start_date exists
3. Verify starting_amount set
4. Force Sync the user

#### Issue: Points not calculating
**Solution:**
1. Run System Check
2. Verify rewards collections exist
3. Check promotion rules active
4. Review point log for errors

#### Issue: Forum images not uploading
**Solution:**
1. Go to Platform Settings → API Keys
2. Verify Publitio credentials entered
3. Click "Test Connection"
4. Check for error messages

#### Issue: Password reset emails not sending
**Solution:**
1. Verify Emailit API key configured
2. Test connection in Platform Settings
3. Check email service status

---

## Quick Reference

### Keyboard Shortcuts
- `Ctrl/Cmd + K` - Quick search
- `Esc` - Close modal/dialog

### Important URLs
- Platform Settings: `/admin/settings`
- Members: `/admin/members`
- Licenses: `/admin/licenses`
- System Check: `/admin/system-check`
- API Center: `/admin/api-center`

### Emergency Contacts
For critical issues, contact development team with:
- Error screenshots
- Browser console logs
- Steps to reproduce
- User ID affected

---

*Document Version: 1.0*
*Last Updated: March 2026*

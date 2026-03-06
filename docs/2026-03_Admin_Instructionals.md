# CrossCurrent Hub - Admin Instructionals
**Step-by-Step Guides for Administrators**
**Last Updated: March 2026**

---

## Table of Contents
1. [Admin Role Quick Reference](#admin-role-quick-reference)
2. [How to Add a New Member](#how-to-add-a-new-member)
3. [How to Edit a Member's Role or Status](#how-to-edit-a-members-role-or-status)
4. [How to Reset a Member's Password](#how-to-reset-a-members-password)
5. [How to Delete a Member Account](#how-to-delete-a-member-account)
6. [How to Set the Daily Trading Signal](#how-to-set-the-daily-trading-signal)
7. [How to Review & Approve Deposits](#how-to-review--approve-deposits)
8. [How to Process Withdrawal Requests](#how-to-process-withdrawal-requests)
9. [How to Create a New License](#how-to-create-a-new-license)
10. [How to Add Family Members to an Honorary FA License](#how-to-add-family-members-to-an-honorary-fa-license)
11. [How to Force-Sync a Licensee's Value](#how-to-force-sync-a-licensees-value)
12. [How to Run a Batch Sync for All Licensees](#how-to-run-a-batch-sync-for-all-licensees)
13. [How to Diagnose a Licensee Calculation Issue](#how-to-diagnose-a-licensee-calculation-issue)
14. [How to Credit or Deduct Points for a Member](#how-to-credit-or-deduct-points-for-a-member)
15. [How to Look Up a Member's Rewards Profile](#how-to-look-up-a-members-rewards-profile)
16. [How to Simulate Points (Testing)](#how-to-simulate-points-testing)
17. [How to Manage Badges](#how-to-manage-badges)
18. [How to Run a Retroactive Badge Scan](#how-to-run-a-retroactive-badge-scan)
19. [How to Run the System Health Check](#how-to-run-the-system-health-check)
20. [How to Enable Maintenance Mode](#how-to-enable-maintenance-mode)
21. [How to Configure Emailit (Password Reset Emails)](#how-to-configure-emailit-password-reset-emails)
22. [How to Configure Publitio (Forum Image Uploads)](#how-to-configure-publitio-forum-image-uploads)
23. [How to Customize Branding & Login Page](#how-to-customize-branding--login-page)
24. [How to Sync Users to the Rewards Platform](#how-to-sync-users-to-the-rewards-platform)
25. [How to Use Simulation Mode](#how-to-use-simulation-mode)
26. [How to Moderate Forum Posts](#how-to-moderate-forum-posts)
27. [How to Export Data (CSV)](#how-to-export-data-csv)
28. [Weekly Admin Checklist](#weekly-admin-checklist)

---

## Admin Role Quick Reference

Before you begin, know what you can access based on your role:

| Feature | Master Admin | Super Admin | Basic Admin |
|---------|:---:|:---:|:---:|
| Members | Yes | Yes | Yes |
| Trading Signals | Yes | Yes | Yes |
| Team Analytics | Yes | Yes | Yes |
| Transactions | Yes | Yes | No |
| Rewards Admin | Yes | Yes | No |
| System Check | Yes | No | No |
| Platform Settings | Yes | No | No |
| API Center | Yes | No | No |
| Licenses | Yes | No | No |

---

## How to Add a New Member

### When to Do This
When a new trader joins the CrossCurrent community.

### Steps
1. Go to **Admin Section** > **Members**
2. Click the **"Add Member"** button (top right)
3. Fill in the form:
   - **Full Name**: Member's full name
   - **Email Address**: Their email (used for login)
   - **Temporary Password**: Set a starting password
   - **Role**: Select "Member" (default for traders)
4. Toggle ON **"Force password change on first login"** (recommended for security)
5. Click **"Create Member"**

### After Creation
- Share the email and temporary password with the new member securely
- They'll be prompted to set their own password on first login
- The member is automatically synced to the Rewards Platform

---

## How to Edit a Member's Role or Status

### Changing a Role
1. Go to **Admin** > **Members**
2. Search for the member by name or email
3. Click the **pencil icon** (Edit) on their row
4. Change the **Role** dropdown:
   - **Member** — Regular trader
   - **Basic Admin** — Can see Members, Signals, Analytics
   - **Super Admin** — All admin features except Settings, API, Licenses
5. Click **"Save Changes"**

### Deactivating a Member
1. Edit the member (pencil icon)
2. Change **Status** to **"Inactive"**
3. Save changes
4. The member can no longer log in, but their data is preserved

### Reactivating a Member
1. Edit the member
2. Change Status back to **"Active"**
3. Save — they can log in again immediately

---

## How to Reset a Member's Password

You have two options:

### Option A: Set a Temporary Password
1. Go to **Admin** > **Members**
2. Find the member
3. Click the **key icon**
4. Enter a temporary password
5. Enable **"Force change on login"**
6. Click **"Set Password"**
7. Securely share the temporary password with the member

### Option B: Send a Reset Email
1. Go to **Admin** > **Members**
2. Find the member
3. Click the **key icon**
4. Click **"Send Reset Link"**
5. The member receives an email with a reset link (valid for 1 hour)
6. They click the link and set their own new password

**Prerequisite for Option B:** Emailit must be configured in Platform Settings > API Keys.

---

## How to Delete a Member Account

### Warning
This action is **permanent** and removes all of the member's data (trades, deposits, points, badges).

### Steps
1. Go to **Admin** > **Members**
2. Find the member
3. Click the **trash icon**
4. Read the confirmation dialog carefully
5. Click **"Confirm Delete"**

### Restrictions
- You **cannot** delete the Master Admin account
- Consider **deactivating** instead of deleting if you may need the data later

---

## How to Set the Daily Trading Signal

### Steps
1. Go to **Admin Section** > **Trading Signals**
2. Set the signal details:
   - **Product Code**: e.g., MOIL10, XAUUSD
   - **Direction**: BUY or SELL
   - **Time**: Signal execution time (Asia/Manila timezone)
   - **Notes**: Any additional instructions (optional)
3. Click **"Set Signal"** or **"Save"**

### Best Practices
- Set the signal before trading hours
- Include clear product and direction
- All members see this signal on their Dashboard and Profit Tracker

---

## How to Review & Approve Deposits

### Step 1: View Pending Deposits
1. Go to **Admin** > **Transactions**
2. Filter by **"Pending Deposits"**

### Step 2: Review Each Deposit
For each pending deposit, verify:
- Member name and email
- Deposit amount
- Payment proof (if uploaded)
- Payment method used

### Step 3: Take Action
- **Approve**: Click Approve to add funds to member's account
- **Reject**: Click Reject and enter a reason (member will be notified)

### After Approval
- The member's Account Value increases immediately
- Their LOT size and daily target update accordingly
- Deposit bonus points are automatically awarded (50 pts per $50)

---

## How to Process Withdrawal Requests

### Step 1: View Pending Withdrawals
1. Go to **Admin** > **Transactions**
2. Filter by **"Pending Withdrawals"**

### Step 2: Verify Each Request
Check:
- Member has **sufficient balance** for the withdrawal
- **Wallet address** is valid
- No suspicious activity on the account
- Request amount is within allowed limits

### Step 3: Take Action
- **Approve**: Sends the funds and deducts from member's balance
- **Reject**: Declines with a reason (balance is not affected)
- **Hold**: Temporarily pauses processing

### Important
- A withdrawal affects the member's **next trading day's Balance Before**
- Example: If approved on a Monday after the trade, Tuesday's balance will be lower
- The member's LOT size and daily target adjust automatically

---

## How to Create a New License

### When to Do This
When issuing an Honorary, Honorary FA, or Extended license to a member.

### Steps
1. Go to **Admin** > **Licenses**
2. Click **"Add License"**
3. **Search and select** the member
4. Choose the **License Type**:
   - **Honorary** — Passive account, grows with master admin trades, quarterly compounding
   - **Honorary FA** — Same as Honorary + supports up to 5 family members
   - **Extended** — Fixed value, no compounding
5. Enter the **Starting Amount** (initial investment)
6. Set the **Effective Start Date** (when the license begins)
7. Click **"Create"**

### After Creation
- The member's dashboard switches to the licensee view
- Growth projections are calculated automatically
- The member sees their year-by-year projection (1yr, 2yr, 3yr, 5yr)

---

## How to Add Family Members to an Honorary FA License

### Prerequisites
- The license must be of type **Honorary FA**

### Steps
1. Go to **Admin** > **Licenses**
2. Find the Honorary FA license in the table
3. Click the **users icon** (family management)
4. Click **"Add Family Member"**
5. Enter:
   - **Member Name**: Full name of the family member
   - **Relationship**: e.g., Spouse, Child, Parent, Sibling
   - **Starting Amount**: Their portion of the investment
6. Click **"Add"**
7. Repeat for up to 5 family members

### Managing Existing Family Members
- **Edit**: Click the edit icon to change name, relationship, or amount
- **Remove**: Click the trash icon to remove a family member

---

## How to Force-Sync a Licensee's Value

### When to Do This
When a licensee's displayed value doesn't look right or after making changes to their license.

### Option A: From the License Table
1. Go to **Admin** > **Licenses**
2. Find the licensee
3. Click the **sync icon** on their row
4. Confirm the recalculation
5. The value updates based on current trading data

### Option B: From Diagnostics
1. Go to **Platform Settings** > **Diagnostics** tab
2. Enter the licensee's email
3. Click **"Force Sync"**
4. Review the updated value

---

## How to Run a Batch Sync for All Licensees

### When to Do This
- Recommended: **Every 7 days**
- After significant trading activity
- After making bulk changes to licenses

### Steps
1. Go to **Platform Settings** > **Diagnostics** tab
2. Look at the **Sync Status Banner** at the top:
   - Green: Sync is current
   - Amber: Never synced
   - Red: Overdue (7+ days since last sync)
3. Click **"Batch Sync All"**
4. Wait for processing (may take 1-2 minutes depending on license count)
5. Review the results:
   - Total processed
   - Success count
   - Any failures (investigate individually)

---

## How to Diagnose a Licensee Calculation Issue

### When a Licensee Reports Wrong Values

### Step 1: Run Individual Diagnostic
1. Go to **Platform Settings** > **Diagnostics** tab
2. Enter the licensee's **email address**
3. Click **"Run Diagnostic"**

### Step 2: Review the Breakdown
The diagnostic shows:
- License details (type, start date, starting amount)
- Step-by-step calculation trace
- Expected vs. actual value
- Any issues found (missing dates, invalid amounts)

### Step 3: Fix Common Issues
| Issue | Fix |
|-------|-----|
| Missing effective_start_date | Edit the license and set the correct date |
| Missing starting_amount | Edit the license and set the amount |
| Value shows $0 | Force Sync the user |
| Calculation mismatch | Run Batch Sync, then recheck |
| Still wrong after sync | Contact development team with diagnostic output |

### Step 4: Verify
After making changes, Force Sync the user and verify the displayed value matches expectations.

---

## How to Credit or Deduct Points for a Member

### Crediting Points (Adding)
1. Go to **Admin** > **Rewards Admin**
2. Search for the member by email or name
3. Click **"Credit Points"**
4. Enter the **amount** of points to add
5. Select a **reason**:
   - Manual Bonus
   - Promotion Credit
   - Error Correction
   - Other (specify)
6. Add a **note** (required — this creates an audit trail)
7. Click **"Credit"**

### Deducting Points (Removing)
1. Same as above, but click **"Deduct Points"**
2. Enter the amount to remove
3. Select a reason:
   - Refund
   - Error Correction
   - Policy Violation
   - Other (specify)
4. Add a note (required)
5. Click **"Deduct"**

### Audit Trail
All point adjustments are permanently logged with:
- Admin who made the change
- Timestamp
- Amount and reason
- Note text

---

## How to Look Up a Member's Rewards Profile

### Steps
1. Go to **Admin** > **Rewards Admin**
2. Use the **search bar** to find a member:
   - Search by email, name, or user ID
   - Select from the autocomplete dropdown
3. View the member's full rewards profile:
   - **Points Balance** and USDT equivalent
   - **Current Level** and progress
   - **Monthly Rank**
   - **Lifetime Points** earned
   - **Complete Points History** with filters

### Filters for Points History
- **All** — Every transaction
- **Earned** — Points added (trades, deposits, badges)
- **Spent** — Points used (streak freezes, store)
- **Admin Actions** — Manual credits/deductions by admins

---

## How to Simulate Points (Testing)

### When to Do This
When you want to test point awards without affecting real data, or to verify the system is working.

### Steps
1. Go to **Admin** > **Rewards Admin**
2. Find the **Simulate Points** section
3. Choose an action type:
   - **test_trade** — Simulates a trade completion
   - **test_deposit** — Simulates a deposit bonus
   - **test_referral** — Simulates a qualified referral
   - **manual_bonus** — Tests a manual credit
4. Select a target user
5. Click **"Simulate"**

### Important
- All simulated actions are tagged as **"Admin Test"** in the points history
- These DO affect the user's actual point balance
- Use for testing workflows or manually awarding bonus points

---

## How to Manage Badges

### Viewing All Badges
1. Go to **Admin** > **Rewards Admin**
2. Navigate to the **Badge Management** tab
3. See all 30 badge definitions

### Editing a Badge
1. Find the badge you want to modify
2. Click **Edit**
3. You can change:
   - **Display Name** — What members see
   - **Description** — Tooltip/detail text
   - **Enabled/Disabled** — Toggle badge availability
4. Click **Save**

### Disabling a Badge
1. Find the badge
2. Toggle to **Disabled**
3. Save — Members can no longer earn this badge
4. Members who already earned it keep it

---

## How to Run a Retroactive Badge Scan

### When to Do This
- After adding new badge definitions
- When members report missing badges
- As part of a weekly maintenance routine

### Steps
1. Go to **Platform Settings** > **Diagnostics** tab
2. Find the **"Scan All Members"** button
3. Click it
4. Wait for the scan to complete (scans every member's history)
5. Review results:
   - How many users were scanned
   - How many badges were awarded

### What It Does
The scan checks each member's actual records (trades, streaks, deposits, referrals) and awards any badges they've earned but haven't received yet.

---

## How to Run the System Health Check

### Access
**Master Admin only** — Go to **Admin** > **System Check**

### Steps
1. Click **"Run Full Check"**
2. Wait for all 10 steps to complete
3. Each step shows Pass or Fail:

| Step | What It Checks |
|------|----------------|
| 1 | MongoDB database connection |
| 2 | Required collections exist |
| 3 | All 30 badge definitions present |
| 4 | Promotion rules configured |
| 5 | All reward API endpoints responding |
| 6 | Point calculation math is correct |
| 7 | Streak tracking system functional |
| 8 | Leaderboard generating correctly |
| 9 | External rewards platform connection |
| 10 | WebSocket/real-time updates working |

### If a Step Fails
- Read the error message for the specific issue
- Follow the suggested fix provided
- Re-run the check after applying fixes
- If persistent, note the step number and error for the development team

---

## How to Enable Maintenance Mode

### When to Do This
During planned downtime, system updates, or when you need to temporarily block member access.

### Steps
1. Go to **Platform Settings** > **Maintenance** tab
2. Toggle **"Maintenance Mode"** to ON
3. Enter a **Maintenance Message** (what members will see):
   - Example: "We're performing scheduled maintenance. We'll be back shortly!"
4. Click **"Save All Changes"**

### What Happens
- All non-admin users see the maintenance page instead of the app
- Admins can still access and use the platform normally
- The custom message is displayed to blocked users

### Turning It Off
1. Go back to Platform Settings > Maintenance
2. Toggle OFF
3. Save — Members can access the platform immediately

---

## How to Configure Emailit (Password Reset Emails)

### Prerequisites
- An Emailit account (sign up at emailit.com)
- Your Emailit API key

### Steps
1. Go to **Platform Settings** > **API Keys** tab
2. Find the **Emailit** section
3. Paste your **API Key**
4. Click **"Test Connection"** to verify it works
5. Click **"Save All Changes"**

### What This Enables
- Password reset emails sent to members via "Forgot Password"
- Branded email template with reset link
- 1-hour token expiry for security

### Troubleshooting
- If "Test Connection" fails, verify the API key is correct
- Check your Emailit account is active
- Ensure you haven't exceeded rate limits

---

## How to Configure Publitio (Forum Image Uploads)

### Prerequisites
- A Publitio account (sign up at publit.io — free tier available)
- Your API Key and API Secret

### Steps
1. Visit [publit.io](https://publit.io) and create an account
2. Go to **Dashboard** > **Settings** > **API**
3. Copy your **API Key** and **API Secret**
4. In the Hub: Go to **Platform Settings** > **API Keys** tab
5. Find the **Publitio** section
6. Paste the **API Key** and **API Secret**
7. Click **"Test Connection"** to verify
8. Click **"Save All Changes"**

### What This Enables
- Members can upload images when creating forum posts
- Members can attach images to forum comments
- Images are hosted on Publitio CDN for fast delivery
- Up to 4 images per post/comment, 2MB each

### Free Tier Limits
- 500MB storage
- 2GB bandwidth per month

---

## How to Customize Branding & Login Page

### Branding (Colors & Logo)
1. Go to **Platform Settings** > **Branding** tab
2. Set:
   - **Logo URL** — Direct URL to your logo image (PNG/JPG)
   - **Favicon URL** — URL for the browser tab icon
   - **Primary Color** — Main brand color (hex, e.g., #1e40af)
   - **Accent Color** — Secondary color (hex)
   - **Custom CSS** — Any additional styling overrides
3. Click **"Save All Changes"**

### Login Page
1. Go to **Platform Settings** > **Login** tab
2. Customize:
   - **Login Title** — Main heading on the login page
   - **Login Tagline** — Subtitle text
   - **Login Notice** — Warning or info message displayed below the form
   - **Custom Registration Link** — If you use an external registration page
3. Click **"Save All Changes"**

### Footer Links
1. Go to **Platform Settings** > **Footer** tab
2. Add links: Enter a **Label** and **URL** for each
3. Drag to reorder links
4. Delete unwanted links with the trash icon
5. Customize the copyright text
6. Click **"Save All Changes"**

---

## How to Sync Users to the Rewards Platform

### What This Does
Pushes all Hub user accounts to the external Rewards Platform (rewards.crosscur.rent) so members can access the store and redeem points.

### Manual Sync
1. Go to **Platform Settings** > **Diagnostics** tab
2. Find the **Rewards Platform Sync** section
3. Review the sync dashboard:
   - Hub Users count
   - Synced count
   - Rewards Platform count
   - Last sync timestamp
4. Click **"Sync All Users"**
5. Wait for batch processing
6. Review results

### Automatic Sync
The system automatically syncs to the Rewards Platform when:
- A new user registers
- A user changes their password
- A user updates their profile

You don't need to manually sync for these events.

---

## How to Use Simulation Mode

### What It Does
Lets you view the platform exactly as another user would see it, without logging out.

### Steps
1. Look for the **"Simulate View"** dropdown in the sidebar
2. Select a user or role to simulate
3. The platform switches to that user's view
4. A **yellow banner** appears at the top indicating simulation mode

### While Simulating
- You see the sidebar, dashboard, and features as that user would
- You **cannot** make changes that affect the user's data
- Use this to verify what a member or admin sees

### Exiting Simulation
- Click **"Exit Simulation"** in the yellow banner
- You return to your full Master Admin view

---

## How to Moderate Forum Posts

### Deleting Inappropriate Posts
1. Go to **Community Forum**
2. Open the post
3. Click **"Delete Post"** (available to admins)
4. Confirm deletion
5. The post and all its comments are removed

### Closing a Post
1. Open the post
2. Click **"Close Post"**
3. Select best answer if applicable
4. Choose active collaborators
5. Confirm — no new comments can be added

### Marking Best Answer (As Admin)
Even if you didn't create the post, admins can mark a comment as Best Answer:
1. Open the post
2. Find the best comment
3. Click **"Mark as Best Answer"**

---

## How to Export Data (CSV)

### Trade Data
1. Go to **Profit Tracker** > **Monthly Table**
2. Click **"Export"** button
3. CSV file downloads with all trading data

### Transaction Data
1. Go to **Admin** > **Transactions**
2. Set your filters (date range, type, status)
3. Click **"Export CSV"**

### Points Data
1. Go to **Rewards Admin**
2. Look up a user or view all transactions
3. Click **"Export CSV"**

### License Data
1. Go to **Admin** > **Licenses**
2. Click **"Export"**
3. CSV includes all license details and current values

---

## Weekly Admin Checklist

A recommended weekly routine to keep the platform healthy:

### Every Week
- [ ] **Run Batch Sync** for all licensees (Platform Settings > Diagnostics)
- [ ] **Review pending deposits** and process them (Transactions)
- [ ] **Review pending withdrawals** and process them (Transactions)
- [ ] **Check the daily signal** is set for each trading day (Trading Signals)
- [ ] **Review Team Analytics** for unusual activity

### Every Month
- [ ] **Run System Health Check** (System Check page)
- [ ] **Run Retroactive Badge Scan** (Diagnostics > Scan All Members)
- [ ] **Sync all users** to Rewards Platform (Diagnostics)
- [ ] **Review forum** for unanswered or stale posts
- [ ] **Export transaction reports** for record-keeping

### As Needed
- [ ] **Add new members** as traders join
- [ ] **Create/update licenses** for new licensees
- [ ] **Credit/deduct points** for special circumstances
- [ ] **Enable maintenance mode** during updates
- [ ] **Update branding** if logos/colors change

---

*Document Version: 1.0*
*Last Updated: March 2026*
*CrossCurrent Hub Admin Instructionals*

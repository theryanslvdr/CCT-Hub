# CrossCurrent Hub - Admin Testing Guide
## New Features & Enhancements (Since Last Deployment)

> **Login:** `iam@ryansalvador.com` / `admin123`
> **App URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com

---

## 1. Redesigned Sidebar Navigation

**What changed:** The sidebar menu is now organized into collapsible accordion categories instead of a flat list.

**Steps to test:**
1. Log in and look at the left sidebar
2. You'll see these category headers: **CORE**, **GROWTH**, **REWARDS**, **COMMUNITY**, **TOOLS**, **ADMIN**
3. Click any category header to expand/collapse it
4. **CORE** contains: Dashboard, Profit Tracker, Trade Monitor
5. **GROWTH** contains: Daily Habits, Affiliate Center, My Team
6. **COMMUNITY** contains: Community Forum, AI Assistant, **Book a Call** (NEW)
7. **ADMIN** shows a red notification badge with the count of pending items (e.g., pending proofs)
8. The sidebar remembers which category is expanded based on the current page

**Expected result:** Smooth accordion animation, only one or two categories open at a time, clicking a nav item navigates to that page.

---

## 2. TidyCal Booking Embed (NEW)

**What changed:** A new "Book a Call" feature has been added. You can configure a TidyCal booking calendar URL in admin settings, and members will see the embedded calendar.

### 2a. Configure the TidyCal URL
1. Go to **Admin Dashboard** > scroll down > click **Platform Settings**
2. On the Settings page, click **API Keys** in the left sidebar tabs
3. Scroll down past Heartbeat and Publitio sections
4. You'll see the **TidyCal Booking** card
5. Paste your TidyCal booking page URL (e.g., `https://tidycal.com/your-username/your-event`)
6. A live **Preview** of the calendar will appear below the input
7. Click **Save All Changes** at the top

**Direct URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com/admin/settings (then click "API Keys" tab)

### 2b. Verify the Booking Page
1. In the sidebar, expand **COMMUNITY**
2. Click **Book a Call**
3. If a TidyCal URL is configured, you'll see the embedded booking calendar
4. If no URL is configured, you'll see: "Booking calendar not configured yet"

**Direct URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com/booking

---

## 3. Admin Dashboard - Find a Member (NEW)

**What changed:** A quick member search tool has been added directly to the Admin Dashboard.

**Steps to test:**
1. Go to **Admin Dashboard** (expand ADMIN in sidebar > Admin Dashboard)
2. You'll see a **"Find a Member"** search bar below the Action Required section
3. Type a name or email in the search box
4. Results will appear as you type
5. Click a result to go to that member's profile

**Direct URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com/admin/dashboard

---

## 4. Weekly Team Performance Report (NEW)

**What changed:** Team leaders now see a weekly performance report on their My Team page.

**Steps to test:**
1. Go to **My Team** (expand GROWTH in sidebar > My Team)
2. Below the team stat cards (Total Members, Active This Week, etc.), you'll see the **Weekly Performance Report** section
3. It displays:
   - **Total Trades** - with comparison to last week (arrow up/down)
   - **Total Profit** - with week-over-week trend
   - **Win Rate** - percentage with trend
   - **Active Traders** - count out of total members
4. If a team member has traded, a **Top Performer** highlight appears
5. Below that is the **Member Breakdown** table showing each member's trades, win rate, and profit

**Direct URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com/my-team

---

## 5. Hub Store (Renamed)

**What changed:** "Store" has been renamed to "Hub Store" and now includes Streak Freezes (moved from My Rewards).

**Steps to test:**
1. Expand **TOOLS** in the sidebar
2. Click **Hub Store**
3. Verify you see both **Signal Gate Immunity** and **Streak Freeze** items
4. Test purchasing with available points

**Direct URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com/store

---

## 6. AI Assistant to Forum Pipeline

**What changed:** When the AI Assistant can't answer a question, it now offers to create a forum post for the community to help.

**Steps to test:**
1. Go to **AI Assistant** (expand COMMUNITY > AI Assistant)
2. Ask a question the AI might not know (e.g., something very specific about your org)
3. If the AI doesn't have an answer, you'll see a **"Post to Forum"** button
4. Clicking it creates a new forum topic with the question

**Direct URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com/ai-assistant

---

## 7. My Rewards - Leaderboard Modal

**What changed:** The Leaderboard has been moved from a separate page into a modal on the My Rewards page.

**Steps to test:**
1. Go to **My Rewards** (expand REWARDS > My Rewards)
2. Look for the **Leaderboard** button
3. Click it to open the leaderboard modal
4. Verify the leaderboard displays correctly with member rankings

**Direct URL:** https://ui-mobile-overhaul-3.preview.emergentagent.com/my-rewards

---

## 8. Admin Cleanup - RyAI Labels

**What changed:** AI-generated analysis in the Admin Cleanup Hub is now clearly labeled as "RyAI Analysis".

**Steps to test:**
1. Go to **Admin Cleanup** (expand ADMIN > Admin Cleanup)
2. Review any flagged items
3. If AI analysis is present, verify it's labeled with "RyAI Analysis"

---

## 9. Notification Badge on Admin

**What changed:** The ADMIN category in the sidebar now shows a red badge with the count of items needing attention.

**Steps to test:**
1. Look at the sidebar
2. The **ADMIN** category should show a red circle with a number (e.g., pending proofs count)
3. The **Admin Cleanup** sub-item also shows its own badge

---

## 10. Mobile Readiness

**What changed:** The entire app is now mobile-responsive.

**Steps to test:**
1. Open the app on a mobile device or resize your browser to mobile width (~375px)
2. Verify the sidebar is hidden and a hamburger menu appears in the header
3. Tap the hamburger to open the full-screen mobile menu
4. Verify the bottom navigation bar shows: Home, Tracker, Trade, Heartbeat, Rewards
5. Navigate through several pages and verify no content overflows or breaks
6. Check the **My Team** page on mobile - the Weekly Report should stack properly
7. Check the **Booking** page on mobile - the calendar embed should be full-width

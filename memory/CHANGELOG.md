# CrossCurrent Hub — Change Log, Social Update & Setup Guide

---

## CHANGE LOG (Feb 2026 Release)

### Phase 1: Signal Blocking & Version Banner
- **Trading Signal Auto-Block** — Members who haven't reported profit tracker data for 7+ days are automatically blocked from viewing the daily signal. Updates their tracker = instant unblock. Admins can manually override via Members page.
- **New Version Banner** — After a deployment, a blue banner appears at the top prompting users to refresh. No more stale app issues.

### Phase 2: Banners & Popups
- **Notice Banner** — Sticky announcement bar. You pick the text, colors, link, and which pages it shows on. Members can dismiss it (comes back next session).
- **Promotion Pop-up** — Modal dialog with 3 styles: Announcement, Promo, Feature Update. Set an image, call-to-action button, and choose frequency (per session / per day / always).
- **Banner Analytics** — See how many members viewed and dismissed each banner. Track engagement over 30 days.

### Phase 3: Habit Tracker (Soft Gate)
- **Daily Habits Page** — Members see a task list at `/habits`. Complete one gate task = signal unlocked for the day.
- **3 Task Types** — "Send Invite" (with copy-paste message), "Visit Link", or a generic checkbox.
- **Habit Streaks** — Current streak, best streak, and total days displayed with flame/trophy/calendar badges.
- **Admin Management** — Create, edit, activate/deactivate habits from Settings > Habits.

### Phase 4: Affiliate Center
- **Resource Hub** — `/affiliate` page with 4 tabs: Conversation Starters, Story Templates, Marketing Materials, FAQs.
- **Copy to Clipboard** — One click to copy any script or template.
- **ConSim Chatbot** — Embed a Chatbase chatbot so members can practice invitation conversations. Admin toggles it on and sets the bot ID.
- **Admin Management** — Full resource CRUD + Chatbase config in Settings > Affiliate.

---

## SOCIAL MEDIA UPDATE

> **CrossCurrent Hub just got a major upgrade.**
>
> Here's what's new:
>
> **Signal Accountability** — If you haven't updated your profit tracker in a week, your daily signal is paused until you catch up. Stay on track = stay in the game.
>
> **Daily Habits** — Complete one quick task each day (like sharing an invite) to unlock your signal. Build streaks and watch your consistency grow.
>
> **Affiliate Center** — Ready-to-use conversation starters, story templates, and FAQs to help you invite new members. Plus a conversation simulator (ConSim) to practice your pitch.
>
> **Smart Banners & Popups** — Important announcements now show exactly where they need to. No more missing updates.
>
> Log in and check it out.

---

## SETUP & TESTING INSTRUCTIONS

### For the Admin (You)

**1. Habit Tracker Setup**
- Go to **Admin Settings > Habits** tab
- A default habit ("Send 1 invite today") is already seeded
- To add more: click **Add Habit**, fill in title, pick action type, toggle "Gate" on if it should block the signal
- Action types:
  - **Send Invite** — Shows a pre-written message members can copy
  - **Visit Link** — Shows a link members should open
  - **Generic** — Simple checkbox task

**2. Notice Banner Setup**
- Go to **Admin Settings > Banners & Popups** tab
- Toggle **Enable Notice Banner** on
- Type your message, pick colors, optionally add a link
- Check the pages where it should appear (Dashboard, Trade Monitor, etc.)
- Hit **Save** at the top of the page
- Test: open the app in a new incognito window to see it as a member would

**3. Promotion Pop-up Setup**
- Same tab, scroll to **Promotion Pop-up**
- Toggle on, pick a preset (Announcement / Promo / Feature Update)
- Fill in title, body, optional image URL, and CTA button
- Set frequency: once per session, once per day, or always
- Save. Open an incognito window to test.

**4. Affiliate Center Setup**
- Go to **Admin Settings > Affiliate** tab
- Click **Add Resource** to create conversation starters, FAQs, etc.
- Pick a category, write the content, set sort order
- To enable ConSim: toggle **Enable ConSim**, paste your **Chatbase Bot ID**, and save
- Members will see the Affiliate Center in their sidebar

**5. Signal Blocking — Nothing to configure**
- It's automatic. Members with 7+ days of unreported data get blocked.
- To manually unblock someone: go to **Admin > Members**, open their profile, click **Unblock Signal** (lasts 7 days).

### Testing Checklist

| Feature | How to Test |
|---|---|
| Signal Blocking | Create a test member account. Don't log any trades for 7+ days. Check if signal is blocked on Trade Monitor. |
| Version Banner | The banner appears after a new deployment (server restart). You'll see it next time you deploy. |
| Notice Banner | Enable it in admin settings. Open the app — see the banner on selected pages. Dismiss it. Refresh — should stay dismissed. Open a new session — should reappear. |
| Promotion Pop-up | Enable it. Open a new incognito tab and log in — popup should appear. Close it. Refresh — should not reappear (if frequency = once per session). |
| Banner Analytics | After enabling banners, check the analytics card at the bottom of the Banners & Popups tab. Shows views and dismiss rates. |
| Daily Habits | Log in as a member. Go to `/habits`. Complete a task. Check that the gate status changes to "Signal Unlocked". Go to Trade Monitor — signal should now be visible. |
| Habit Streaks | Complete habits on consecutive days. Return to `/habits` — streak counter should increment. |
| Affiliate Center | Go to `/affiliate`. Browse tabs. Click copy on a resource. Check ConSim tab (if Chatbase is configured). |

### Quick API Test (curl)

```bash
# Get your token
API=https://hub.crosscur.rent
TOKEN=$(curl -s -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"iam@ryansalvador.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Test signal block status
curl -s "$API/api/trade/signal-block-status" -H "Authorization: Bearer $TOKEN"

# Test habits
curl -s "$API/api/habits/" -H "Authorization: Bearer $TOKEN"

# Test affiliate resources
curl -s "$API/api/affiliate-resources" -H "Authorization: Bearer $TOKEN"

# Test version
curl -s "$API/api/version"

# Test banner config
curl -s "$API/api/settings/notice-banner"
```

# CrossCurrent Hub — What's New (March 9–10, 2026)

Here's everything that was built, fixed, and improved over the past two days. Each section includes what it does and how to use it.

---

## 1. Login Page Redesign

**What changed:** The login screen now uses a modern split-panel layout — form on the left, decorative visual on the right. Clean, minimal, and consistent with the dark theme across the entire platform.

**How it looks:**
- Desktop: Two-column layout with orange accent orb on the right
- Mobile: Single column, form only

---

## 2. "Who Invited You?" Modal

**What it does:** Every non-admin member now sees a one-time prompt on each session asking them to confirm who invited them. This ensures the referral tree is accurate.

**How it works:**
1. Log in as any member (non-admin)
2. The "Who invited you?" modal appears automatically
3. If you already have an inviter linked, you'll see their name — click **Confirm** to keep them
4. To change: type a name or email in the search box → select the correct person → click **Confirm Inviter**
5. The modal won't appear again until the next browser session (refresh/reopen)

**For admins:** You can change any member's inviter from the Admin Members page (see #8 below).

---

## 3. Invite Someone (Onboarding Invite Link)

**What it does:** Members can now generate a shareable link that takes new joiners directly to the onboarding site with the inviter's Merin code pre-filled.

**How to use it:**
1. Go to **Affiliate Center** (sidebar → Growth → Affiliate Center, or click your profile → Affiliate Center)
2. The **"Invite Someone"** card is at the top of the page
3. Your unique onboarding link is displayed: `https://crosscur.rent/onboarding?merin_code=YOUR_CODE`
4. Click **Copy** to copy the link to your clipboard
5. Share with your prospect — when they open it, the Merin step will have your code pre-filled

**Note:** You need a Merin referral code set in your Profile for this to work. If you don't have one, the card will prompt you to set it up.

---

## 4. Member Lookup

**What it does:** Search for any member by name or email to find their Merin referral code.

**How to use it:**
1. Go to **Affiliate Center**
2. Scroll to the **"Find a Member"** card
3. Type a name or email in the search box
4. Results appear instantly showing: **Name** · **masked email** · **Merin Code**
5. Click the code to copy it to your clipboard

---

## 5. Referral Tracking & Milestone Rewards

**What it does:** A full gamified referral system. Track your referrals, earn points at milestones, and compete on the leaderboard.

**How to use it:**
1. Go to **Invite & Earn** (sidebar → Growth → Invite & Earn)
2. See your invite link (now the onboarding link), copy and share it
3. Track how many people you've referred and their onboarding status
4. **Milestones** — earn points automatically:
   - 3 referrals → 100 points
   - 5 referrals → 200 points
   - 10 referrals → 500 points
   - 25 referrals → 1,000 points + "Network Builder" badge
   - 50 referrals → 2,500 points + "Community Architect" badge
5. Go to **Leaderboard** (sidebar → Growth → Leaderboard) to see rankings

---

## 6. Sidebar — Affiliate Center Quick Link

**What changed:** "Affiliate Center" is now accessible from the profile dropdown at the bottom-left of the sidebar (both expanded and collapsed modes). One click to get there.

---

## 7. Adaptive AI Assistant

**What it does:** The AI assistant now automatically detects whether you're asking a technical question or seeking motivation, and responds with the right persona — no manual switching needed.

**How to use it:**
1. Go to **AI Assistant** (sidebar)
2. Just chat naturally. Ask a technical trading question and you'll get RyAI's analytical response. Ask for encouragement and zxAI will respond warmly.
3. Each message shows which persona responded

**Admin control:**
1. Go to **Platform Settings** → Security tab
2. Toggle **Adaptive AI** on/off. When off, all responses use the default RyAI persona.

---

## 8. Admin — Edit Member's Inviter

**What it does:** Admins can now view and change who invited any member, directly from the member management page.

**How to use it:**
1. Go to **Admin Dashboard** → **Members**
2. Click the eye icon to view a member
3. The **"Inviter"** field shows who referred them (or "Not set")
4. Click **Edit Profile**
5. Scroll to the **"Inviter (Who Referred Them)"** field
6. Search by name or email, select the correct inviter → **Save**
7. To clear an inviter, click **Clear** → Save

---

## 9. Admin — Edit Member's Merin Referral Code

**What it does:** Master admins can now manually set or change a member's Merin referral code.

**How to use it:**
1. Go to **Admin Dashboard** → **Members**
2. Click the eye icon to view a member → **Edit Profile**
3. Find the **Merin Referral Code** field
4. Enter the code (auto-uppercased) → **Save**

---

## 10. Dynamic AI Model Selector

**What it does:** The AI Training page now lets admins choose from 346+ AI models via a live, searchable dropdown — pulled directly from OpenRouter.

**How to use it:**
1. Go to **Admin Dashboard** → AI & Platform → **AI Training**
2. In the model configuration section, click the model dropdown
3. Search by name (e.g., "gpt-4", "claude", "llama")
4. Select a model → Save

---

## 11. 7-Step Onboarding Gate

**What it does:** New members are blocked from accessing the platform until they complete all 7 onboarding steps. This ensures everyone is fully set up before they start trading.

**Steps:** Heartbeat → Merin → Hub → Exchange → Tutorials → Live Trade → Rewards

**Admin control:**
1. Go to **Platform Settings** → Security tab
2. Toggle **Onboarding Gate** on/off

**For the external onboarding site:** API endpoints are live:
- `GET /api/onboarding/status/{user_id}` — check a user's progress
- `POST /api/onboarding/complete-step-external` — mark a step complete

---

## 12. Notification Consolidation

**What changed:** Notifications are now grouped by type. Instead of 34 individual "Member X submitted a trade" notifications, you see: **"Member1, Member2 and 32 more submitted trades"**

**Tabs:** Unread · Read · All — with action buttons per notification type.

---

## 13. Mobile Menu Sync

**What changed:** The mobile navigation menu now matches the desktop sidebar exactly — same items, same order, same sections.

---

## 14. Merged Forum Post Tagging

**What it does:** When an admin merges a forum post into another, the merged post now shows a tag indicating it was merged, with a link to the original post.

---

## Bug Fixes

| Bug | Fix |
|-----|-----|
| **Black screen after login** | `InviterModal.jsx` was missing a `useEffect` import, crashing React for all non-admin members. Fixed + added global Error Boundary. |
| **Daily projections showing $0** | Missing `get_quarter` import in admin_routes.py and profit_routes.py. Fixed. |
| **Trading streak wrong count** | Streak was reading from a non-existent `users.streak` field. Now computed from actual `trade_logs`. |
| **Timezone DST errors** | Hardcoded timezone offsets replaced with dynamic `Intl.DateTimeFormat` API. |
| **AI journal cut off mid-sentence** | Increased `max_tokens` from 350 to 800 in ai_service.py. |
| **Family member projections crash** | Broken import `from server import get_quarter` → fixed to `from utils.trading_days import get_quarter`. |
| **Licensee "Below target" label** | Changed to "Account Growth / +X% since inception" on the dashboard. |

---

## Error Boundary (Safety Net)

**What it does:** If anything in the app ever crashes again, instead of a black screen, users now see a friendly "Something went wrong" screen with a **Reload App** button that clears state and redirects to login.

---

*All features have been tested across iterations 165–179 with 100% pass rates.*

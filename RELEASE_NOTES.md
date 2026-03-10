# CrossCurrent Hub — What's New (March 9–10, 2026)

Here's everything that was built, fixed, and improved over the past two days. Each section includes what it does, how to use it, and a screenshot for reference.

---

## 1. Login Page Redesign

**What changed:** The login screen now uses a modern split-panel layout — clean form on the left, decorative orange accent on the right. Dark, minimal, and consistent with the platform theme.

- Desktop: Two-column layout with abstract orange orb
- Mobile: Single column, form only — right panel is hidden

![Login Page](https://dark-theme-overhaul-4.preview.emergentagent.com/screenshots/01_login.png)

---

## 2. Dashboard

Your home base. All KPIs, trading stats, and quick actions at a glance.

![Dashboard](https://dark-theme-overhaul-4.preview.emergentagent.com/screenshots/02_dashboard.png)

---

## 3. Invite Someone + Member Lookup (Affiliate Center)

**What it does:** Members can now generate a shareable invite link and look up any member's Merin code.

**How to use it:**
1. Navigate to **Affiliate Center** (sidebar → Growth → Affiliate Center, or profile dropdown → Affiliate Center)
2. **Invite Someone** card (top) — your unique onboarding link is displayed:
   `https://crosscur.rent/onboarding?merin_code=YOUR_CODE`
   Click **Copy** and share with your prospect.
3. **Find a Member** card — type a name or email, instantly see:
   **Name** · **Masked email** · **Merin Code** (click to copy)

> **Note:** You need a Merin referral code set in your Profile for the invite link to work.

![Affiliate Center](https://dark-theme-overhaul-4.preview.emergentagent.com/screenshots/03_affiliate_center.png)

---

## 4. Referral Tracking & Milestone Rewards (Invite & Earn)

**What it does:** Track your referrals, earn points at milestones, and compete on the leaderboard.

**How to use it:**
1. Go to **Invite & Earn** (sidebar → Growth → Invite & Earn)
2. Your onboarding invite link is at the top — copy and share it
3. See your referral count and each person's onboarding status
4. **Milestones** are earned automatically:

| Referrals | Reward |
|-----------|--------|
| 3 | 100 points |
| 5 | 200 points |
| 10 | 500 points |
| 25 | 1,000 points + "Network Builder" badge |
| 50 | 2,500 points + "Community Architect" badge |

5. Check the **Leaderboard** (sidebar → Growth → Leaderboard) for rankings

![Referral Tracking](https://dark-theme-overhaul-4.preview.emergentagent.com/screenshots/04_referral_tracking.png)

---

## 5. "Who Invited You?" Modal

**What it does:** Every non-admin member is prompted once per session to confirm who invited them. This keeps the referral tree accurate.

**How it works:**
1. Log in as a member (non-admin)
2. The "Who invited you?" modal appears automatically
3. **Already have an inviter?** You'll see their name — click **Confirm** to keep them
4. **Need to change?** Type a name or email in the search → select the correct person → **Confirm Inviter**
5. Won't appear again until the next browser session

> Admins never see this modal.

---

## 6. Adaptive AI Assistant

**What it does:** The AI assistant now auto-detects your intent — technical question gets RyAI (analytical), motivational question gets zxAI (encouraging). No manual switching.

**How to use it:**
1. Go to **AI Assistant** (sidebar)
2. Chat naturally — the AI picks the right persona per message
3. Each response shows which persona is speaking

**Admin control:** Platform Settings → Security → toggle **Adaptive AI** on/off

![AI Assistant](https://dark-theme-overhaul-4.preview.emergentagent.com/screenshots/05_ai_assistant.png)

---

## 7. Dynamic AI Model Selector (Admin)

**What it does:** Choose from 346+ AI models via a live searchable dropdown, pulled directly from OpenRouter.

**How to use it:**
1. Go to **Admin Dashboard** → AI & Platform → **AI Training**
2. Click the model dropdown, search by name (e.g., "gpt-4", "claude", "llama")
3. Select a model → Save

---

## 8. Admin — Manage Member Inviter & Merin Code

**What it does:** Admins can view and edit any member's inviter and Merin referral code.

**How to use it:**
1. Go to **Admin Dashboard** → **Members**
2. Click the eye icon to view a member's profile
3. See the **Inviter** field (or "Not set")
4. Click **Edit Profile** to:
   - **Set/change inviter:** Search by name or email → select → Save
   - **Clear inviter:** Click Clear → Save
   - **Set Merin Code:** Type the code (auto-uppercased) → Save

![Admin Members](https://dark-theme-overhaul-4.preview.emergentagent.com/screenshots/06_admin_members.png)

---

## 9. Sidebar — Affiliate Center Quick Access

**What changed:** "Affiliate Center" is now in the profile dropdown (bottom-left of sidebar). One click to get there — available in both expanded and collapsed sidebar modes.

---

## 10. 7-Step Onboarding Gate

**What it does:** New members must complete all 7 onboarding steps before accessing the platform.

**Steps:** Heartbeat → Merin → Hub → Exchange → Tutorials → Live Trade → Rewards

**Admin control:** Platform Settings → Security → toggle **Onboarding Gate** on/off

**External API endpoints (for the onboarding site):**
- `GET /api/onboarding/status/{user_id}` — check progress
- `POST /api/onboarding/complete-step-external` — mark a step complete

---

## 11. Notification Consolidation

**What changed:** Similar notifications are now grouped. Instead of 34 separate "Member X submitted a trade" notifications, you see:

> **"Member1, Member2 and 32 more submitted trades"**

Tabs: **Unread** · **Read** · **All** — with action buttons per type.

---

## 12. Mobile Menu Sync

**What changed:** The mobile nav menu now matches the desktop sidebar exactly — same items, same order, same sections.

---

## 13. Merged Forum Post Tagging

**What it does:** Merged forum posts now show a tag with a link to the original post for context.

---

## 14. Error Boundary (Safety Net)

**What it does:** If anything in the app crashes, users now see a friendly recovery screen instead of a black/blank page.

- "Something went wrong" message
- **Reload App** button that clears state and redirects to login

---

## Bug Fixes

| Bug | Fix |
|-----|-----|
| **Black screen after login** | `InviterModal.jsx` crashed React (missing import). Fixed + added global Error Boundary. |
| **Daily projections showing $0** | Missing helper import. Fixed. |
| **Trading streak wrong** | Was reading non-existent field. Now computed from actual trade logs. |
| **Timezone DST errors** | Hardcoded offsets → dynamic `Intl.DateTimeFormat` API. |
| **AI journal cut off** | Increased `max_tokens` from 350 → 800. |
| **Family member projections crash** | Broken import path. Fixed. |
| **Licensee "Below target" label** | Changed to "Account Growth / +X% since inception". |

---

*All features tested across iterations 165–179 with 100% pass rates.*

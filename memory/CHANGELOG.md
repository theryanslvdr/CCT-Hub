# CrossCurrent Hub - Changelog

## 2026-03-09 - Forum Features & BVE Bug Fix

### Bug Fixes
- **BVE "Reset to Entry Point" data loss (P0)**: Fixed critical bug where trade operations in BVE mode could affect production data. Added `/api/bve/trade/history` and `/api/bve/trade/{id}` endpoints. Frontend now routes through BVE-specific endpoints when `isInBVE` is true.

### New Features
- **Forum: Merge Posts**: Master Admin and Super Admin can merge duplicate posts. Comments from source are moved to target. Source OP gets 8 pts; all contributors retain full points. Merge history logged to `forum_merge_logs`.
- **Forum: Duplicate Post Safeguard**: Pre-submission check searches by both title AND content. Shows warning with similar posts before allowing submission. User can view existing post or confirm their question is different.
- **Forum: Post Details Sidebar**: Right sidebar on post view showing:
  - Post info (date, views, comments)
  - Contributors list
  - Awards received
  - "Solution still valid" button (for closed posts with best answer)
- **Forum: Enhanced Similar Search**: `/api/forum/search-similar` now searches both title and content (was title-only).

### Testing
- 15/15 backend tests passed (iteration 152)
- 100% frontend verification
- BVE data isolation confirmed

### Commission & AI Features (same day)
- **Commission Records**: Added "Type" column - "Balance" (green) for normal commissions, "Historical" (amber) for `skip_deposit=true`
- **OpenRouter Integration**: AI-powered semantic duplicate detection at `POST /api/forum/ai-check-duplicate`. Uses gpt-4o-mini via OpenRouter. Falls back to regex if unavailable.
- **Exit Trade Verification**: Full regression test passed - trade logging, performance calculation, commission storage, trade history all working correctly.

### Testing (AI & Commissions)
- 18/18 backend tests passed (iteration 153)
- 100% frontend verification
- OpenRouter AI integration confirmed working (ai_powered=true)

### Phase 1 AI Features (same day)
- **AI Trade Coach**: Personalized coaching under each trade in Trade History (brain icon button)
- **AI Financial Summary**: Weekly/Monthly analysis card on Profit Tracker with toggle
- **AI Balance Forecast**: 7/30/90 day projection card on Profit Tracker
- **AI Post Summarizer**: TL;DR button on forum posts with 3+ comments
- **AI Service Layer**: Shared `/app/backend/services/ai_service.py` with MongoDB caching, per-feature token limits, and TTLs

### Testing (Phase 1 AI)
- 15/15 backend tests passed (iteration 154)
- 100% frontend verification
- All 4 AI endpoints confirmed working with OpenRouter + caching

## 2026-03-10 — Phase 2: Trading Intelligence AI

### New Features
- **AI Signal Insights**: Market context & tips inside Active Signal card (Zap icon button)
- **AI Trade Journal**: Daily/Weekly reflective journal on Trade Monitor with BUY/SELL analysis, streak tracking
- **AI Goal Advisor**: Per-goal realism assessment on Profit Planner with days-to-goal projection
- **AI Anomaly Alert**: Detects trading gaps, streak breaks, profit drops — shows flags with supportive advice

### Testing
- 19/20 backend tests passed, 1 skipped (no active signal) (iteration 155)
- Phase 1 regression: all 4 features still working
- 100% frontend verification

## 2026-03-10 — Phase 3: Community, Admin & Notifications AI

### New Features
- **AI Answer Suggestions**: "AI Suggest Answer" button in forum comment area, references solved Q&As
- **AI Member Risk Scoring**: "AI Risk" button in admin member details dialog, shows risk level + flags
- **AI Daily Trade Report**: Card at top of Admin Analytics, generates executive summary with stats
- **AI Smart Notifications**: Personalized notification messages based on member context
- **AI Commission Optimizer**: Card in Profit Tracker alongside Financial Summary and Balance Forecast
- **AI Milestone Motivation**: Celebration button on goal cards at 25/50/75/100% milestones

### Testing
- 28/28 backend tests passed (iteration 156)
- Phase 1+2 regression: all features passing
- 100% frontend verification

## 2026-03-06 - Commission & Stability Fixes

### Bug Fixes
- Fixed daily projection commissions aggregation
- Fixed commission save endpoint (model mismatch)
- Fixed Platform Settings black screen
- Fixed batch sync to rewards platform
- Fixed Publitio credential reading
- Fixed "Failed to create signal" error
- Fixed "Failed to log trade" error

### New Features
- Clear Cache & Reload button in sidebar
- Auto batch sync every 4 hours (APScheduler)
- Commission backfill with skip_deposit option

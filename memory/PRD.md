# CrossCurrent Hub - Product Requirements Document

## Original Problem Statement
Financial trading dashboard ("The CrossCurrent Hub") for the Merin Trading Platform. Full-stack app with React frontend, FastAPI backend, and MongoDB. Features include profit tracking, trade monitoring, balance sync, admin panel, PWA support, and more.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn/UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001, routes prefixed /api)
- **Database**: MongoDB
- **PWA**: manifest.json + service-worker.js

## Key Files
- `/app/backend/server.py` (~8400 lines) - Main backend, needs continued refactoring
- `/app/frontend/src/pages/ProfitTrackerPage.jsx` (~5200 lines) - Main profit tracker
- `/app/frontend/src/components/OnboardingWizardMobile.jsx` - Mobile onboarding
- `/app/frontend/src/components/OnboardingWizard.jsx` - Desktop onboarding
- `/app/frontend/src/components/PreSyncWizard.jsx` - Balance sync wizard (desktop + mobile)
- `/app/frontend/src/lib/pwa.jsx` - PWA install + instructions
- `/app/frontend/src/components/layout/Sidebar.jsx` - Navigation sidebar

## Credentials
- Master Admin: iam@ryansalvador.com / admin123

## What's Been Implemented

### Session Feb 12, 2026 - Mobile Bug Fixes + PWA Instructions
1. **Bug Fix: DNT button error** - Fixed param mismatch (trade_date -> date) in did-not-trade API calls
2. **Bug Fix: Adjust button in wizard** - Redirected to existing Enter AP dialog (was using undeclared state)
3. **Bug Fix: Balance not updating after onboarding** - Mobile wizard sent `trade_history` instead of `trade_entries` to backend
4. **Bug Fix: Missed Trade button disabled** - Added Clear button, changed condition to allow re-selection
5. **Bug Fix: Negative trade results** - Removed validation blocking negative actual profit values
6. **Feature: Mobile Balance Sync Wizard** - Full-screen overlay matching Simulate functions style
7. **Feature: PWA Install Instructions** - Device-detecting instructions dialog accessible from sidebar
8. **Bug Fix: NaN display in Adjust Trade** - Added fallback calculations for wizard-sourced trade adjustments

### Previous Sessions (Completed)
- Dashboard layout redesign (TradeMonitorPage.jsx)
- Data Export feature (admin panel)
- Backend refactoring (settings.py, bve.py extracted from server.py)
- Full PWA implementation ("The CrossCurrent Hub")
- Pre-Sync Validation Wizard
- Data Health Score badge

## Prioritized Backlog

### P0 (Critical)
- None currently

### P1 (High)
- Push notification support with user preference settings
- Continue backend refactoring (extract trade, profit, admin routes from server.py)
- Provide curl command for "Run Diagnostic" production debugging

### P2 (Medium)
- Frontend refactoring of ProfitTrackerPage.jsx (consider Zustand for state management)
- Cloudinary file upload implementation (currently placeholder)

### Known Issues
- "Run Diagnostic" feature fails in production (infrastructure issue, not code)
- Cloudinary integration is still a placeholder

## 3rd Party Integrations
- Heartbeat, Emailit, APScheduler, Cloudinary (Placeholder), CoinGecko, react-quill-new
